import re
from pathlib import Path


def safe_stem(filename: str) -> str:
    name = filename.replace("\\", "/").split("/")[-1]
    stem = Path(name).stem
    stem = re.sub(r"[^A-Za-z0-9._ -]", "_", stem).strip(" ._")[:80]
    return stem or "converted"


def download_name(filename: str, suffix: str, extension: str) -> str:
    return f"{safe_stem(filename)}{suffix}.{extension}"
