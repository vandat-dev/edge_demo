import asyncio
import base64
import logging
from contextlib import asynccontextmanager
from typing import Set

import grpc
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from frame_pb2 import Ack
from frame_pb2_grpc import FrameStreamerServicer, add_FrameStreamerServicer_to_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Service B] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

connected_clients: Set[WebSocket] = set()
clients_lock = asyncio.Lock()
grpc_server = None


async def register_client(websocket: WebSocket):
    await websocket.accept()
    async with clients_lock:
        connected_clients.add(websocket)
    logger.info("WebSocket client connected, total=%d", len(connected_clients))


async def unregister_client(websocket: WebSocket):
    async with clients_lock:
        connected_clients.discard(websocket)
    logger.info("WebSocket client disconnected, total=%d", len(connected_clients))


async def broadcast(payload):
    if not connected_clients:
        return
    dead_clients = []
    for ws in list(connected_clients):
        try:
            await ws.send_json(payload)
        except Exception:
            dead_clients.append(ws)
    for ws in dead_clients:
        await unregister_client(ws)


def encode_frame(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


class FrameStreamerService(FrameStreamerServicer):
    async def SendFrames(self, request_iterator, context):
        async for chunk in request_iterator:
            logger.info("Nhận frame #%s từ Service A", chunk.index)
            payload = {
                "index": chunk.index,
                "image": encode_frame(chunk.data),
            }
            await broadcast(payload)
            logger.info("Đã broadcast frame #%s tới %d client", chunk.index, len(connected_clients))
        return Ack(ok=True, message="Frames forwarded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global grpc_server
    grpc_server = grpc.aio.server()
    add_FrameStreamerServicer_to_server(FrameStreamerService(), grpc_server)
    grpc_server.add_insecure_port("[::]:50051")
    await grpc_server.start()
    logger.info("gRPC server lắng nghe tại 0.0.0.0:50051")
    try:
        yield
    finally:
        await grpc_server.stop(0)


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
            await websocket.receive_text()
    except WebSocketDisconnect:
        await unregister_client(websocket)
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
        await unregister_client(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8800, reload=True)
