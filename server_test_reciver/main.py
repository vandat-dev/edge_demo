import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Set

import grpc
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

import frame_pb2, frame_pb2_grpc


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Service B] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

connected_clients: Set[WebSocket] = set()
clients_lock = asyncio.Lock()
grpc_server = None


# ===========================================
# WEBSOCKET
# ===========================================

async def register_client(websocket: WebSocket):
    await websocket.accept()
    async with clients_lock:
        connected_clients.add(websocket)
    logger.info("WebSocket client connected, total=%d", len(connected_clients))


async def unregister_client(websocket: WebSocket):
    async with clients_lock:
        connected_clients.discard(websocket)
    logger.info("WebSocket client disconnected, total=%d", len(connected_clients))


async def broadcast(data: bytes):
    if not connected_clients:
        return

    dead_clients = []
    for ws in list(connected_clients):
        try:
            await ws.send_bytes(data)
        except Exception:
            dead_clients.append(ws)

    for ws in dead_clients:
        await unregister_client(ws)


# ===========================================
# gRPC SERVICER
# ===========================================

class FrameServicer(frame_pb2_grpc.FrameServiceServicer):
    async def SendFrame(self, request: frame_pb2.FrameRequest, context):
        logger.info("Nhận frame từ Service A - size=%d bytes", len(request.data))
        await broadcast(request.data)
        return frame_pb2.FrameResponse()


# ===========================================
# FASTAPI LIFESPAN - START gRPC SERVER
# ===========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global grpc_server

    grpc_server = grpc.aio.server()

    # ĐÚNG TÊN SERVICER
    frame_pb2_grpc.add_FrameServiceServicer_to_server(FrameServicer(), grpc_server)

    grpc_server.add_insecure_port("[::]:50051")
    await grpc_server.start()
    logger.info("gRPC server lắng nghe tại 0.0.0.0:50051")

    try:
        yield
    finally:
        await grpc_server.stop(0)
        logger.info("gRPC server stopped")


# ===========================================
# FASTAPI APP
# ===========================================

app = FastAPI(
    title="Service B - gRPC relay + WebSocket",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "message": "Service B đang chạy",
        "websocket": "/ws",
        "grpc_port": 50051,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await register_client(websocket)

    try:
        while True:
            # nhận mọi frame (ping/pong/text/binary) để giữ kết nối ổn định
            await websocket.receive()
    except WebSocketDisconnect:
        await unregister_client(websocket)
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
        await unregister_client(websocket)

# ===========================================
# MAIN ENTRY
# ===========================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8800, reload=True)
