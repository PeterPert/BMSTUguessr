from __future__ import annotations

import shutil
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MAPS_DIR = DATA_DIR / "maps"
PHOTOS_DIR = DATA_DIR / "photos"
DB_PATH = DATA_DIR / "baumanka.db"

VALID_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
MAP_SIZE = (1100, 700)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_path(stored_path: str | Path) -> Path:
    path = Path(stored_path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def to_project_relative(path: str | Path) -> str:
    path = Path(path).resolve()
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_inside_project(path: str | Path) -> bool:
    try:
        Path(path).resolve().relative_to(PROJECT_ROOT)
        return True
    except ValueError:
        return False


def copy_image_to_storage(source: str | Path, target_dir: Path, prefix: str) -> str:
    ensure_dirs()
    src = Path(source)
    suffix = src.suffix.lower()
    if suffix not in VALID_IMAGE_SUFFIXES:
        raise ValueError("Неподдерживаемый формат изображения")

    if src.exists() and is_inside_project(src):
        return to_project_relative(src)

    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4().hex[:10]}{suffix}"
    dst = target_dir / filename
    shutil.copy2(src, dst)
    return to_project_relative(dst)
