"""Tests for app.database — CRUD operations with a temporary SQLite database."""

from __future__ import annotations

from unittest.mock import patch


class TestDatabaseInit:
    """Tests for initialize_db() and schema creation."""

    def test_tables_created(self, tmp_db):
        """All expected tables exist after initialization."""
        import sqlite3

        conn = sqlite3.connect(tmp_db)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()

        expected = {
            "admins",
            "floors",
            "locations",
            "game_sessions",
            "game_session_rounds",
        }
        assert expected.issubset(tables)

    def test_default_admins_seeded(self, tmp_db):
        """Default admin accounts are present after init."""
        import sqlite3

        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
        conn.close()
        assert count >= 1


class TestGameResults:
    """Tests for save_game_result() and get_results()."""

    def test_save_and_retrieve(self, tmp_db):
        """Saved game session appears in results."""
        with (
            patch("app.paths.DB_PATH", tmp_db),
            patch("app.paths.PROJECT_ROOT", tmp_db.parent),
        ):
            from app.database import get_results, save_game_result

            rounds = [
                {
                    "location_title": "Коридор 2 этаж",
                    "image_path": "data/photos/test.jpg",
                    "answer_x": 100,
                    "answer_y": 200,
                    "answer_floor": 2,
                    "guessed_x": 110,
                    "guessed_y": 190,
                    "guessed_floor": 2,
                    "distance_meters": 1.41,
                    "points": 5,
                },
            ]
            session_id = save_game_result(score=5, rounds=rounds, max_score=5)
            assert session_id > 0

            results = get_results(limit=10)
            assert len(results) >= 1
            assert results[0]["score"] == 5

    def test_multiple_sessions_ordered(self, tmp_db):
        """Results are returned in reverse chronological order."""
        with (
            patch("app.paths.DB_PATH", tmp_db),
            patch("app.paths.PROJECT_ROOT", tmp_db.parent),
        ):
            from app.database import get_results, save_game_result

            round_data = {
                "answer_x": 0,
                "answer_y": 0,
                "answer_floor": 1,
                "guessed_x": 0,
                "guessed_y": 0,
                "guessed_floor": 1,
                "distance_meters": 0,
                "points": 5,
            }
            save_game_result(score=10, rounds=[round_data])
            save_game_result(score=20, rounds=[round_data])

            results = get_results(limit=10)
            # The most recent session (score=20) should come first
            assert results[0]["score"] == 20
