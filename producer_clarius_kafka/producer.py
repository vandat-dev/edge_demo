import asyncio
import io
import logging
import os
from datetime import datetime
from typing import Tuple

import numpy as np
import pydicom
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image
from kafka import KafkaProducer
import json

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9096")
TOPIC = "test"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Service A] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Service A - DICOM uploader")


# ---------------------------
# Utils
# ---------------------------

def load_dicom_from_bytes(data: bytes) -> Tuple[dict, np.ndarray]:
    ds = pydicom.dcmread(io.BytesIO(data), force=True)
    arr = ds.pixel_array

    patient_info = {
        "name": str(ds.get("PatientName", "")),
        "id": str(ds.get("PatientID", "")),
        "sex": str(ds.get("PatientSex", "")),
        "birth_date": str(ds.get("PatientBirthDate", "")),
        "age": str(ds.get("PatientAge", "")),
        "study_date": str(ds.get("StudyDate", "")),
        "institution": str(ds.get("InstitutionName", "")),
        "modality": str(ds.get("Modality", "")),
    }
    return patient_info, arr


def normalize_to_uint8(frame: np.ndarray) -> np.ndarray:
    frame = frame.astype(np.float32)
    min_v, max_v = frame.min(), frame.max()
    if max_v - min_v == 0:
        return np.zeros_like(frame, dtype=np.uint8)
    scaled = (frame - min_v) / (max_v - min_v) * 255.0
    return scaled.astype(np.uint8)


def frame_to_png_bytes(frame: np.ndarray) -> bytes:
    if frame.ndim == 3 and frame.shape[-1] in (3, 4):
        image = Image.fromarray(frame)
    else:
        normalized = normalize_to_uint8(frame)
        image = Image.fromarray(normalized).convert("L")
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP")
    return buffer.getvalue()


# ---------------------------
# Kafka Producer
# ---------------------------

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: v,   # gửi raw bytes
)


def send_frames_via_kafka(frames: np.ndarray):
    if frames.size == 0:
        raise ValueError("Không có frame để gửi.")

    for idx, frame in enumerate(frames):
        data = frame_to_png_bytes(frame)
        start = datetime.now()

        producer.send(TOPIC, value=data)
        producer.flush()

        print("Frame", idx, "took:", datetime.now() - start)

    return {"ok": True, "message": f"Đã gửi {len(frames)} frame qua Kafka"}


# ---------------------------
# API Upload
# ---------------------------

@app.post("/upload")
async def upload_dicom(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File rỗng.")

    try:
        patient, frames = load_dicom_from_bytes(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    loop = asyncio.get_running_loop()
    ack = await loop.run_in_executor(None, send_frames_via_kafka, frames)

    return JSONResponse(
        {
            "frames": int(frames.shape[0]),
            "patient": patient,
            "ack": ack,
            "kafka": KAFKA_BOOTSTRAP,
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok", "kafka": KAFKA_BOOTSTRAP}


if __name__ == "__main__":
    uvicorn.run("producer_clarius_kafka.producer:app", host="0.0.0.0", port=8700)
