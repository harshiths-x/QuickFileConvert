import asyncio
import json
import logging
import multiprocessing
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pypdf import PdfReader
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.config import settings
from app.services.processor import process
from app.utils.cleanup import remove_directory, remove_expired
from app.utils.file_validation import EXTENSIONS, validate_file
from app.utils.filename import download_name

logger = logging.getLogger("quickfileconvert")
rate_state: dict[str, deque[float]] = defaultdict(deque)
conversion_slots = asyncio.Semaphore(2)


def _worker(tool: str, source: str, target: str, options: dict, queue) -> None:
    try:
        process(tool, Path(source), Path(target), options)
        queue.put(None)
    except ValueError as exc:
        queue.put(str(exc))
    except Exception:
        logger.exception("Conversion failed for tool %s", tool)
        queue.put("Conversion could not be completed. The file may be invalid or corrupted.")


def _run_worker(tool: str, source: Path, target: Path, options: dict) -> None:
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    worker = context.Process(target=_worker, args=(tool, str(source), str(target), options, queue))
    worker.start()
    worker.join(settings.conversion_timeout)
    if worker.is_alive():
        worker.terminate()
        worker.join(5)
        if worker.is_alive():
            worker.kill()
            worker.join()
        raise ValueError("The conversion took too long.")
    if worker.exitcode != 0:
        raise ValueError("Conversion could not be completed.")
    message = queue.get(timeout=2)
    if message:
        raise ValueError(message)


async def _janitor() -> None:
    while True:
        await asyncio.sleep(5)
        await asyncio.to_thread(remove_expired, settings.storage_root, settings.temp_file_ttl)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    remove_expired(settings.storage_root, settings.temp_file_ttl)
    task = asyncio.create_task(_janitor())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="QuickFileConvert API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.method == "POST" and request.url.path.startswith("/api/"):
        client = request.client.host if request.client else "unknown"
        # Trust the direct connection only; forwarding headers can be spoofed without a trusted proxy.
        now = time.monotonic()
        bucket = rate_state[client]
        while bucket and bucket[0] < now - settings.rate_limit_window:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_requests:
            return JSONResponse({"detail": "Too many requests. Please try again later."}, status_code=429)
        bucket.append(now)
    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok"}


async def _save_upload(upload: UploadFile, path: Path) -> None:
    size = 0
    with path.open("wb") as file:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > min(settings.max_upload_size, 50 * 1024 * 1024):
                raise HTTPException(413, "File exceeds the 50 MB limit.")
            file.write(chunk)
    if size == 0:
        raise HTTPException(400, "Choose a non-empty file.")


async def _assert_single_file(request: Request) -> None:
    form = await request.form()
    uploads = [value for _, value in form.multi_items() if isinstance(value, StarletteUploadFile)]
    if len(uploads) != 1:
        raise HTTPException(400, "Choose one file at a time.")


async def _convert(tool: str, file: UploadFile, options: str) -> dict:
    if tool not in EXTENSIONS:
        raise HTTPException(404, "Tool not found.")
    try:
        parsed = json.loads(options)
        if not isinstance(parsed, dict):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(400, "Invalid tool options.")
    token = uuid.uuid4().hex
    directory = settings.storage_root / token
    directory.mkdir(parents=True, exist_ok=False)
    extension = Path(file.filename or "").suffix.lower()
    source = directory / f"input{extension}"
    output_extension = EXTENSIONS[tool][1]
    target = directory / f"output{output_extension}"
    try:
        async with asyncio.timeout(settings.conversion_timeout):
            await _save_upload(file, source)
        validate_file(source, file.filename or "", tool)
        async with conversion_slots:
            await asyncio.to_thread(_run_worker, tool, source, target, parsed)
        if not target.is_file() or target.stat().st_size == 0:
            raise ValueError("Conversion could not be completed.")
        suffix = {"split": "-split", "rotate": "-rotated", "extract": "-extracted", "reorder": "-reordered"}.get(tool, "")
        filename = download_name(file.filename or "converted", suffix, output_extension.lstrip("."))
        metadata = {"filename": filename, "mime_type": EXTENSIONS[tool][2], "size": target.stat().st_size}
        (directory / "result.json").write_text(json.dumps(metadata), encoding="utf-8")
        source.unlink(missing_ok=True)
        # TTL starts when the result becomes available, not when upload begins.
        directory.touch()
        return {"download_id": token, **metadata}
    except HTTPException:
        remove_directory(directory)
        raise
    except TimeoutError as exc:
        remove_directory(directory)
        raise HTTPException(408, "The upload took too long.") from exc
    except ValueError as exc:
        remove_directory(directory)
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        logger.exception("Request failed for tool %s", tool)
        remove_directory(directory)
        raise HTTPException(500, "Conversion could not be completed.") from exc
    finally:
        await file.close()


@app.post("/api/convert/{tool}")
async def convert(tool: str, request: Request, file: UploadFile = File(...), options: str = Form("{}")):
    if tool in {"split", "rotate", "extract", "reorder"}:
        raise HTTPException(404, "Tool not found.")
    await _assert_single_file(request)
    return await _convert(tool, file, options)


@app.post("/api/pdf/{tool}")
async def pdf_tool(tool: str, request: Request, file: UploadFile = File(...), options: str = Form("{}")):
    if tool == "inspect":
        await _assert_single_file(request)
        return await inspect_pdf(file)
    if tool not in {"split", "rotate", "extract", "reorder"}:
        raise HTTPException(404, "Tool not found.")
    await _assert_single_file(request)
    return await _convert(tool, file, options)


async def inspect_pdf(file: UploadFile = File(...)):
    directory = settings.storage_root / uuid.uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    source = directory / "input.pdf"
    try:
        await _save_upload(file, source)
        validate_file(source, file.filename or "", "split")
        reader = PdfReader(str(source))
        if reader.is_encrypted:
            raise ValueError("Password-protected PDFs are not supported.")
        return {"page_count": len(reader.pages)}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, "The uploaded file appears to be invalid or corrupted.") from exc
    finally:
        remove_directory(directory)
        await file.close()


@app.get("/api/download/{token}")
async def download(token: str):
    if len(token) != 32 or any(character not in "0123456789abcdef" for character in token):
        raise HTTPException(404, "The temporary download has expired.")
    directory = settings.storage_root / token
    metadata_file = directory / "result.json"
    if not metadata_file.is_file() or time.time() - directory.stat().st_mtime > settings.temp_file_ttl:
        remove_directory(directory)
        raise HTTPException(404, "The temporary download has expired.")
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    extension = Path(metadata["filename"]).suffix
    output = directory / f"output{extension}"
    if not output.is_file():
        raise HTTPException(404, "The temporary download has expired.")
    return FileResponse(output, media_type=metadata["mime_type"], filename=metadata["filename"])
