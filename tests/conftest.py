"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture()
def tmp_db(tmp_path: Path):
    """Create a temporary SQLite database with the app schema."""
    db_path = tmp_path / "test.db"

    # Patch paths so the app uses our temp directory
    with (
        patch("app.paths.DB_PATH", db_path),
        patch("app.paths.DATA_DIR", tmp_path),
        patch("app.paths.MAPS_DIR", tmp_path / "maps"),
        patch("app.paths.PHOTOS_DIR", tmp_path / "photos"),
        patch("app.paths.PROJECT_ROOT", tmp_path),
    ):
        from app.database import initialize_db

        initialize_db()
        yield db_path
