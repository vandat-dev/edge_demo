import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from kafka import KafkaConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Service B] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = "localhost:9096"
TOPIC = "test"

connected_clients: Set[WebSocket] = set()
clients_lock = asyncio.Lock()

# ---------------------------
# WebSocket
# ---------------------------

async def register_client(websocket: WebSocket):
    await websocket.accept()
    async with clients_lock:
        connected_clients.add(websocket)
    logger.info("Client connected, total=%d", len(connected_clients))


async def unregister_client(websocket: WebSocket):
    async with clients_lock:
        connected_clients.discard(websocket)
    logger.info("Client disconnected, total=%d", len(connected_clients))


async def broadcast(data: bytes):
    if not connected_clients:
        return

    dead = []
    for ws in list(connected_clients):
        try:
            await ws.send_bytes(data)
        except Exception:
            dead.append(ws)

    for ws in dead:
        await unregister_client(ws)


# ---------------------------
# Kafka Consumer Background Task
# ---------------------------

async def kafka_worker():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda v: v,
    )

    logger.info("Kafka consumer đang lắng nghe tại %s", KAFKA_BOOTSTRAP)

    loop = asyncio.get_running_loop()

    while True:
        msg_pack = consumer.poll(timeout_ms=200)

        for tp, messages in msg_pack.items():
            for msg in messages:
                data = msg.value
                await broadcast(data)

        await asyncio.sleep(0)


# ---------------------------
# FastAPI + lifespan
# ---------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(kafka_worker())
    yield
    task.cancel()


app = FastAPI(title="Service B - Kafka relay + WebSocket", lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "message": "Kafka Consumer đang chạy",
        "kafka": KAFKA_BOOTSTRAP,
        "ws": "/ws",
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await register_client(websocket)

    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        await unregister_client(websocket)


if __name__ == "__main__":
    uvicorn.run("consumer_server_kafka.consumer:app", host="0.0.0.0", port=8800)
