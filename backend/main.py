import os
import shutil
import tempfile
import uuid
import warnings
import asyncio
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import converter_core
from security import (
    validate_file_safety,
    save_file_with_size_limit,
    delete_file_safely,
    MAX_FILE_SIZE_BYTES
)

warnings.filterwarnings("ignore", category=UserWarning, module="fitz")

# Rate Limiter: track client IP
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Hardened Document & Image Engine", version="2.5.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: Restricted to local frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

TEMP_DIR = os.path.join(tempfile.gettempdir(), "universal_converter_jobs")
os.makedirs(TEMP_DIR, exist_ok=True)


# --- Automatic Cleanup Loop ---
@app.on_event("startup")
async def start_periodic_cleanup():
    """Background sweeper: purges orphaned files older than 30 minutes."""
    async def cleanup_loop():
        while True:
            await asyncio.sleep(600)  # Check every 10 minutes
            now = time.time()
            try:
                for fname in os.listdir(TEMP_DIR):
                    fpath = os.path.join(TEMP_DIR, fname)
                    if os.path.isfile(fpath) and os.path.getmtime(fpath) < (now - 1800):
                        delete_file_safely(fpath)
            except Exception:
                pass

    asyncio.create_task(cleanup_loop())


# --- Endpoints ---

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "universal-document-engine"}


@app.post("/api/convert/office-to-pdf")
@limiter.limit("10/minute")
async def office_to_pdf_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    safe_name = await validate_file_safety(file, ["docx", "xlsx", "pptx"])
    ext = os.path.splitext(safe_name)[1].lower().replace(".", "")

    job_id = str(uuid.uuid4())
    in_file = os.path.join(TEMP_DIR, f"{job_id}_{safe_name}")
    out_file = os.path.join(TEMP_DIR, f"{job_id}_converted.pdf")

    await save_file_with_size_limit(file, in_file)

    try:
        # 60s execution timeout protects against hung Office processes
        await asyncio.wait_for(
            asyncio.to_thread(converter_core.convert_office_document, in_file, out_file, ext),
            timeout=60.0
        )
        background_tasks.add_task(delete_file_safely, in_file)
        background_tasks.add_task(delete_file_safely, out_file)
        return FileResponse(out_file, filename=f"{os.path.splitext(safe_name)[0]}.pdf", media_type="application/pdf")
    except asyncio.TimeoutError:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=504, detail="Conversion timed out (limit: 60s).")
    except Exception as e:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/convert/pdf-to-office")
@limiter.limit("10/minute")
async def pdf_to_office_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_format: str = Form(...)
):
    safe_name = await validate_file_safety(file, ["pdf"])
    target = target_format.lower().replace(".", "")
    if target not in ["docx", "xlsx", "pptx"]:
        raise HTTPException(status_code=400, detail="Target format must be docx, xlsx, or pptx")

    job_id = str(uuid.uuid4())
    in_file = os.path.join(TEMP_DIR, f"{job_id}_{safe_name}")
    out_file = os.path.join(TEMP_DIR, f"{job_id}_converted.{target}")

    await save_file_with_size_limit(file, in_file)

    try:
        if target == "docx":
            await asyncio.wait_for(asyncio.to_thread(converter_core.pdf_to_word, in_file, out_file), timeout=60.0)
            media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif target == "xlsx":
            await asyncio.wait_for(asyncio.to_thread(converter_core.pdf_to_excel, in_file, out_file), timeout=60.0)
            media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif target == "pptx":
            await asyncio.wait_for(asyncio.to_thread(converter_core.pdf_to_powerpoint, in_file, out_file), timeout=60.0)
            media = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        background_tasks.add_task(delete_file_safely, in_file)
        background_tasks.add_task(delete_file_safely, out_file)
        return FileResponse(out_file, filename=f"{os.path.splitext(safe_name)[0]}.{target}", media_type=media)
    except asyncio.TimeoutError:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=504, detail="Conversion timed out.")
    except Exception as e:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pdf/compress")
@limiter.limit("10/minute")
async def compress_pdf_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    compression_level: str = Form("recommended")
):
    safe_name = await validate_file_safety(file, ["pdf"])
    job_id = str(uuid.uuid4())
    in_file = os.path.join(TEMP_DIR, f"{job_id}_{safe_name}")
    out_file = os.path.join(TEMP_DIR, f"{job_id}_compressed.pdf")

    await save_file_with_size_limit(file, in_file)

    try:
        await asyncio.wait_for(
            asyncio.to_thread(converter_core.compress_pdf, in_file, out_file, compression_level),
            timeout=60.0
        )
        background_tasks.add_task(delete_file_safely, in_file)
        background_tasks.add_task(delete_file_safely, out_file)
        return FileResponse(out_file, filename=f"compressed_{safe_name}", media_type="application/pdf")
    except asyncio.TimeoutError:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=504, detail="PDF compression timed out.")
    except Exception as e:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/image/to-pdf")
@limiter.limit("10/minute")
async def image_to_pdf_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    safe_name = await validate_file_safety(file, ["jpg", "jpeg", "png", "webp"])
    job_id = str(uuid.uuid4())
    in_file = os.path.join(TEMP_DIR, f"{job_id}_{safe_name}")
    out_file = os.path.join(TEMP_DIR, f"{job_id}_output.pdf")

    await save_file_with_size_limit(file, in_file)

    try:
        await asyncio.wait_for(asyncio.to_thread(converter_core.image_to_pdf, in_file, out_file), timeout=30.0)
        background_tasks.add_task(delete_file_safely, in_file)
        background_tasks.add_task(delete_file_safely, out_file)
        return FileResponse(out_file, filename=f"{os.path.splitext(safe_name)[0]}.pdf", media_type="application/pdf")
    except asyncio.TimeoutError:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=504, detail="Image conversion timed out.")
    except Exception as e:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/image/resize-compress")
@limiter.limit("15/minute")
async def image_resize_compress_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    width: float = Form(None),
    height: float = Form(None),
    unit: str = Form("Pixels (px)"),
    target_dpi: int = Form(72),
    export_format: str = Form("JPEG"),
    target_kb: int = Form(0),
    quality: int = Form(80)
):
    safe_name = await validate_file_safety(file, ["jpg", "jpeg", "png", "webp"])
    job_id = str(uuid.uuid4())
    in_file = os.path.join(TEMP_DIR, f"{job_id}_{safe_name}")
    ext = export_format.lower()
    out_file = os.path.join(TEMP_DIR, f"{job_id}_processed.{ext}")

    await save_file_with_size_limit(file, in_file)

    try:
        await asyncio.wait_for(
            asyncio.to_thread(
                converter_core.resize_and_compress_image,
                in_file, out_file, width, height, unit, target_dpi, export_format, target_kb, quality
            ),
            timeout=30.0
        )
        background_tasks.add_task(delete_file_safely, in_file)
        background_tasks.add_task(delete_file_safely, out_file)
        return FileResponse(out_file, filename=f"processed_{os.path.splitext(safe_name)[0]}.{ext}", media_type=f"image/{ext}")
    except asyncio.TimeoutError:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=504, detail="Image processing timed out.")
    except Exception as e:
        delete_file_safely(in_file)
        delete_file_safely(out_file)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/purge/{job_id}")
async def purge_job_files(job_id: str):
    """
    Explicit wipe endpoint allowing the client to instantly purge 
    files associated with a job ID before the sweeper runs.
    """
    # Sanitize job_id to prevent directory traversal
    clean_job_id = os.path.basename(job_id).replace("..", "")
    purged_count = 0

    try:
        for fname in os.listdir(TEMP_DIR):
            if fname.startswith(clean_job_id):
                fpath = os.path.join(TEMP_DIR, fname)
                delete_file_safely(fpath)
                purged_count += 1
        return {"status": "purged", "job_id": clean_job_id, "deleted_files": purged_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))