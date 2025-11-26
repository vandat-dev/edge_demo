import asyncio
import io
import logging
import os
from datetime import datetime
from typing import Iterable, Tuple

import grpc
import numpy as np
import pydicom
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image

from frame_pb2 import FrameRequest
from frame_pb2_grpc import FrameServiceStub

GRPC_TARGET = os.getenv("GRPC_TARGET", "localhost:50051")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Service A] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Service A - DICOM uploader")


def load_dicom_from_bytes(data: bytes) -> Tuple[dict, np.ndarray]:
    """Đọc file DICOM từ bytes."""
    try:
        ds = pydicom.dcmread(io.BytesIO(data), force=True)
    except Exception as e:
        raise ValueError(f"Lỗi khi đọc file DICOM: {e}") from e

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

    try:
        arr = ds.pixel_array
    except Exception as e:
        raise ValueError(f"Lỗi khi truy cập pixel_array: {e}") from e
    return patient_info, arr


def frame_to_png_bytes(frame: np.ndarray) -> bytes:
    """Chuẩn hóa frame (có thể 16-bit) thành ảnh PNG bytes."""
    if frame.ndim == 3 and frame.shape[-1] in (3, 4):
        image = Image.fromarray(frame)
    else:
        normalized = normalize_to_uint8(frame)
        image = Image.fromarray(normalized).convert("L")
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP")
    return buffer.getvalue()


def normalize_to_uint8(frame: np.ndarray) -> np.ndarray:
    frame = frame.astype(np.float32)
    min_v = frame.min()
    max_v = frame.max()
    if max_v - min_v == 0:
        return np.zeros_like(frame, dtype=np.uint8)
    scaled = (frame - min_v) / (max_v - min_v) * 255.0
    return scaled.astype(np.uint8)




def send_frames(frames: np.ndarray, target: str):
    if frames.size == 0:
        raise ValueError("Không có frame để gửi.")

    with grpc.insecure_channel(target) as channel:
        stub = FrameServiceStub(channel)
        for idx, frame in enumerate(frames):
            data = frame_to_png_bytes(frame)

            logger.info("Chuẩn bị gửi frame #%s", idx)
            print()
            try:
                start_time = datetime.now()
                stub.SendFrame(FrameRequest(data=data))
                print(datetime.now() - start_time)


            except Exception as e:
                logger.error(f"Lỗi gửi frame #{idx}: {e}")
        
        logger.info("Đã gửi xong %d frame tới %s", frames.shape[0], target)
        return {"ok": True, "message": "Frames sent"}


@app.post("/upload")
async def upload_dicom(
    file: UploadFile = File(...),
    target: str | None = None,
):
    """Nhận file DICOM, chuyển thành frames và stream sang Service B."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File rỗng.")

    try:
        patient, frames = load_dicom_from_bytes(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    loop = asyncio.get_running_loop()
    chosen_target = "localhost:50051"
    try:
        ack = await loop.run_in_executor(None, send_frames, frames, chosen_target)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return JSONResponse(
        {
            "frames": int(frames.shape[0]) if frames.size else 0,
            "patient": patient,
            "ack": ack,
            "target": chosen_target,
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok", "target": GRPC_TARGET}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8700, reload=True)
