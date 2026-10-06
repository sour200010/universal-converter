import os
import re
import magic
from fastapi import HTTPException, UploadFile

# Hard cap: 50 MB per file to prevent memory/disk exhaustion
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

ALLOWED_MIME_SIGNATURES = {
    "pdf": ["application/pdf"],
    "jpeg": ["image/jpeg"],
    "jpg": ["image/jpeg"],
    "png": ["image/png"],
    "webp": ["image/webp"],
    "docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream"
    ],
    "pptx": [
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/octet-stream"
    ],
    "xlsx": [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/octet-stream"
    ]
}


def sanitize_filename(filename: str) -> str:
    """
    Strips directory traversal payloads (../../) and dangerous characters.
    """
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", clean_name)
    if not clean_name or clean_name.startswith("."):
        clean_name = f"safe_file_{clean_name}"
    return clean_name


def delete_file_safely(file_path: str):
    """Safely deletes temporary files with error suppression."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


async def validate_file_safety(file: UploadFile, expected_extensions: list[str]) -> str:
    """
    Validates file extension, inspects binary magic bytes, and blocks disguised payloads.
    """
    safe_name = sanitize_filename(file.filename)
    ext = os.path.splitext(safe_name)[1].lower().replace(".", "")

    if ext not in expected_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '.{ext}'. Allowed: {', '.join(expected_extensions)}"
        )

    # Read the first 2KB to inspect true binary signature
    header_bytes = await file.read(2048)
    if not header_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # PDF header signature check
    if ext == "pdf" and not header_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="File signature mismatch: file is not a valid PDF document."
        )

    # Magic byte inspection for images and archives
    try:
        detected_mime = magic.from_buffer(header_bytes, mime=True)
        valid_mimes = ALLOWED_MIME_SIGNATURES.get(ext, [])
        if valid_mimes and not any(detected_mime.startswith(vm) for vm in valid_mimes):
            # If magic library returns generic octet-stream, permit only if extension matches standard zip containers
            if detected_mime not in ["application/octet-stream", "application/zip"] or ext not in ["docx", "xlsx", "pptx"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Security alert: File content ({detected_mime}) does not match '.{ext}'."
                )
    except HTTPException:
        raise
    except Exception:
        pass  # Fallback if magic signature cannot parse non-standard subheaders

    # Reset stream pointer back to beginning so downstream writes work
    await file.seek(0)
    return safe_name


async def save_file_with_size_limit(file: UploadFile, destination: str):
    """
    Streams file in 1MB chunks and cancels immediately if size exceeds 50MB.
    Prevents RAM overload and disk-filling DoS attacks.
    """
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1MB chunk

    with open(destination, "wb") as buffer:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > MAX_FILE_SIZE_BYTES:
                buffer.close()
                delete_file_safely(destination)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
                )
            buffer.write(chunk)