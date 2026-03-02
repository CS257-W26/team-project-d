"""Unit tests for ProductionCode.db."""

from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from ProductionCode import db


class TestDbConfig(unittest.TestCase):
    """Tests for connection-string building and config parsing."""

    def test_get_db_url_prefers_environment_variable(self) -> None:
        """If DATABASE_URL is set, it should be returned verbatim."""
        os.environ["DATABASE_URL"] = "postgresql://example"
        try:
            self.assertEqual("postgresql://example", db.get_db_url())
        finally:
            os.environ.pop("DATABASE_URL", None)

    def test_get_db_url_supports_multiple_variable_names(self) -> None:
        """Config can use DATABASE/USER/PASSWORD/HOST/PORT variable names."""
        fake_cfg = types.ModuleType("ProductionCode.psql_config")
        fake_cfg.DATABASE = "team_db"
        fake_cfg.USER = "alice"
        fake_cfg.PASSWORD = "secret"
        fake_cfg.HOST = "stearns.mathcs.carleton.edu"
        fake_cfg.PORT = 5432

        with patch.dict(sys.modules, {"ProductionCode.psql_config": fake_cfg}):
            self.assertEqual(
                "postgresql://alice:secret@stearns.mathcs.carleton.edu:5432/team_db",
                db.get_db_url(),
            )

    def test_get_db_url_missing_values_raises(self) -> None:
        """Missing required values in psql_config should raise a helpful error."""
        fake_cfg = types.ModuleType("ProductionCode.psql_config")
        fake_cfg.DATABASE = "team_db"
        fake_cfg.USER = "alice"
        fake_cfg.HOST = "stearns.mathcs.carleton.edu"

        with patch.dict(sys.modules, {"ProductionCode.psql_config": fake_cfg}):
            with self.assertRaises(RuntimeError) as ctx:
                _ = db.get_db_url()

        self.assertIn("missing required values", str(ctx.exception).lower())

    def test_get_db_url_defaults_invalid_port_to_5432(self) -> None:
        """Invalid PORT values should fall back to PostgreSQL's default port."""
        fake_cfg = types.ModuleType("ProductionCode.psql_config")
        fake_cfg.DATABASE = "team_db"
        fake_cfg.USER = "alice"
        fake_cfg.PASSWORD = "secret"
        fake_cfg.HOST = "localhost"
        fake_cfg.PORT = "not-a-number"

        with patch.dict(sys.modules, {"ProductionCode.psql_config": fake_cfg}):
            self.assertEqual(
                "postgresql://alice:secret@localhost:5432/team_db",
                db.get_db_url(),
            )

    def test_get_db_url_missing_config_module_raises_runtime_error(self) -> None:
        """Missing psql_config should raise a clear RuntimeError."""
        with patch("ProductionCode.db._import", side_effect=ModuleNotFoundError):
            with self.assertRaises(RuntimeError) as ctx:
                db.get_db_url()

        self.assertIn("Missing ProductionCode/psql_config.py", str(ctx.exception))

    def test_get_db_calls_records_database(self) -> None:
        """get_db() should construct a records.Database instance with the URL."""
        fake_records = types.SimpleNamespace(Database=MagicMock())

        with patch.dict(sys.modules, {"records": fake_records}):
            with patch("ProductionCode.db.get_db_url", return_value="postgresql://u:p@h:5432/d"):
                _ = db.get_db()

        fake_records.Database.assert_called_once_with("postgresql://u:p@h:5432/d")

    def test_get_db_wraps_connection_errors(self) -> None:
        """get_db() should wrap low-level connection failures in RuntimeError."""
        fake_records = types.SimpleNamespace(Database=MagicMock(side_effect=Exception("boom")))

        with patch("ProductionCode.db._import", return_value=fake_records):
            with patch("ProductionCode.db.get_db_url", return_value="postgresql://u:p@h:5432/d"):
                with self.assertRaises(RuntimeError) as ctx:
                    db.get_db()

        self.assertIn("Failed to connect to database", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
