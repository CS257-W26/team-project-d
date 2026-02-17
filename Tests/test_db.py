"""
Unit tests for ProductionCode.db.
"""

from __future__ import annotations

import sys
from pathlib import Path
import os
import types
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import ProductionCode
from ProductionCode import db


class TestDbConfig(unittest.TestCase):
    """tests for connection-string building and config parsing"""
    def test_get_db_url_prefers_environment_variable(self) -> None:
        os.environ["DATABASE_URL"] = "postgresql://example"
        try:
            self.assertEqual("postgresql://example", db.get_db_url())
        finally:
            os.environ.pop("DATABASE_URL", None)

    def test_load_psql_config_supports_multiple_variable_names(self) -> None:
        fake = types.SimpleNamespace(
            DATABASE="team_db",
            USER="alice",
            PASSWORD="secret",
            HOST="stearns.mathcs.carleton.edu",
            PORT=5432,
        )

        with patch.object(ProductionCode, "psql_config", fake, create=True):
            cfg = db._load_psql_config()

        self.assertEqual("team_db", cfg.database)
        self.assertEqual("alice", cfg.user)
        self.assertEqual("secret", cfg.password)
        self.assertEqual("stearns.mathcs.carleton.edu", cfg.host)
        self.assertEqual(5432, cfg.port)

    def test_load_psql_config_missing_values_raises(self) -> None:
        fake = types.SimpleNamespace(
            DATABASE="team_db",
            USER="alice",
            HOST="stearns.mathcs.carleton.edu",
        )

        with patch.object(ProductionCode, "psql_config", fake, create=True):
            with self.assertRaises(RuntimeError) as ctx:
                _ = db._load_psql_config()

        self.assertIn("missing required values", str(ctx.exception).lower())

    def test_get_db_calls_records_database(self) -> None:
        """get_db should call records.Database(db_url)"""
        fake_records = types.SimpleNamespace(Database=MagicMock())

        with patch.dict("sys.modules", {"records": fake_records}):
            with patch("ProductionCode.db.get_db_url", return_value="postgresql://u:p@h:5432/d"):
                _ = db.get_db()

        fake_records.Database.assert_called_once_with("postgresql://u:p@h:5432/d")


if __name__ == "__main__":
    unittest.main()
