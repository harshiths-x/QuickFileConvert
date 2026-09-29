from pathlib import Path
from zipfile import BadZipFile, ZipFile
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader


EXTENSIONS = {
    "pdf-to-word": (".pdf", ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "word-to-pdf": (".docx", ".pdf", "application/pdf"),
    "pdf-to-txt": (".pdf", ".txt", "text/plain; charset=utf-8"),
    "txt-to-pdf": (".txt", ".pdf", "application/pdf"),
    "docx-to-txt": (".docx", ".txt", "text/plain; charset=utf-8"),
    "jpg-to-png": ((".jpg", ".jpeg"), ".png", "image/png"),
    "png-to-jpg": (".png", ".jpg", "image/jpeg"),
    "image-to-pdf": ((".jpg", ".jpeg", ".png"), ".pdf", "application/pdf"),
    "csv-to-excel": (".csv", ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "excel-to-csv": (".xlsx", ".csv", "text/csv; charset=utf-8"),
    "split": (".pdf", ".pdf", "application/pdf"),
    "rotate": (".pdf", ".pdf", "application/pdf"),
    "extract": (".pdf", ".pdf", "application/pdf"),
    "reorder": (".pdf", ".pdf", "application/pdf"),
}


def validate_file(path: Path, filename: str, tool: str) -> None:
    spec = EXTENSIONS[tool]
    extension = Path(filename.lower()).suffix
    allowed = spec[0] if isinstance(spec[0], tuple) else (spec[0],)
    if extension not in allowed:
        raise ValueError("Unsupported file format for this tool.")
    try:
        if extension == ".pdf":
            with path.open("rb") as file:
                if file.read(5) != b"%PDF-":
                    raise ValueError("The uploaded file appears to be invalid or corrupted.")
            try:
                reader = PdfReader(str(path), strict=False)
                if reader.is_encrypted:
                    raise ValueError("Password-protected PDFs are not supported.")
                if len(reader.pages) == 0:
                    raise ValueError("The PDF has no pages.")
            except ValueError:
                raise
            except Exception as exc:
                raise ValueError("The uploaded file appears to be invalid or corrupted.") from exc
        elif extension in (".png", ".jpg", ".jpeg"):
            with Image.open(path) as image:
                if image.format != ("PNG" if extension == ".png" else "JPEG"):
                    raise ValueError("The file content does not match its extension.")
                if image.width * image.height > 40_000_000:
                    raise ValueError("The image dimensions are too large to process.")
                image.verify()
        elif extension in (".docx", ".xlsx"):
            expected = "word/document.xml" if extension == ".docx" else "xl/workbook.xml"
            with ZipFile(path) as archive:
                names = archive.namelist()
                if expected not in names or len(names) > 10000:
                    raise ValueError("The uploaded file appears to be invalid or corrupted.")
                if sum(item.file_size for item in archive.infolist()) > 500 * 1024 * 1024:
                    raise ValueError("The document expands beyond the allowed size.")
        elif extension in (".txt", ".csv"):
            with path.open("rb") as file:
                sample = file.read(8192)
            if b"\x00" in sample:
                raise ValueError("The uploaded file appears to be invalid or corrupted.")
            sample.decode("utf-8-sig")
    except (BadZipFile, UnidentifiedImageError, UnicodeDecodeError, OSError) as exc:
        raise ValueError("The uploaded file appears to be invalid or corrupted.") from exc
