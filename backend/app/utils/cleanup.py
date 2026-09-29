import shutil
import time
from pathlib import Path


def remove_directory(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def remove_expired(root: Path, ttl: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - ttl
    for path in root.iterdir():
        if path.is_dir() and path.stat().st_mtime < cutoff:
            remove_directory(path)
