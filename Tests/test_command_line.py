"""
Unit tests for command-line interface.
"""

from __future__ import annotations

import contextlib
import io
import unittest
from unittest.mock import MagicMock, patch

import command_line
from typing import List, Tuple


class TestCommandLine(unittest.TestCase):
    """clu tests for argument parsing + formatting"""
    def run_cli(self, argv: List[str]) -> Tuple[int, str, str]:
        """run the cli and capture (exit_code, stdout, stderr)"""
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = command_line.main(argv)

        return exit_code, stdout.getvalue(), stderr.getvalue()

    @patch("command_line.ClimateRepository")
    @patch("command_line.get_db")
    def test_deforestation_single_value(self, mock_get_db, mock_repo_class) -> None:
        """--deforestation country should call forest_value_for_entity_year"""
        mock_get_db.return_value = MagicMock()
        repo = mock_repo_class.return_value
        repo.forest_value_for_entity_year.return_value = ("Brazil", 2020, -2628412.5)

        code, out, err = self.run_cli(["--deforestation", "Brazil", "--year", "2020"])

        self.assertEqual(0, code)
        self.assertEqual("", err)
        self.assertIn("Annual change in forest area for Brazil in 2020", out)
        self.assertIn("-2,628,412.50 ha", out)

        repo.forest_value_for_entity_year.assert_called_once_with(
            entity_query="Brazil",
            year=2020,
            only_countries=True,
        )

    @patch("command_line.ClimateRepository")
    @patch("command_line.get_db")
    def test_deforestation_list(self, mock_get_db, mock_repo_class) -> None:
        """--deforestation (no country) should call forest_rank_entities"""
        mock_get_db.return_value = MagicMock()
        repo = mock_repo_class.return_value
        repo.forest_rank_entities.return_value = [
            ("Brazil", -10.0),
            ("Indonesia", -5.0),
            ("Canada", 2.0),
        ]

        code, out, err = self.run_cli(["--deforestation", "--year", "2021", "--top", "3"])

        self.assertEqual(0, code)
        self.assertEqual("", err)
        self.assertIn("Top 3 entities", out)
        self.assertIn("1. Brazil:", out)

        repo.forest_rank_entities.assert_called_once_with(
            year=2021,
            order="loss",
            top_n=3,
            only_countries=True,
        )

    @patch("command_line.ClimateRepository")
    @patch("command_line.get_db")
    def test_co2_single_value(self, mock_get_db, mock_repo_class) -> None:
        """--co2 country should call co2_value_for_entity_year"""

        mock_get_db.return_value = MagicMock()
        repo = mock_repo_class.return_value
        repo.co2_value_for_entity_year.return_value = ("Canada", 2021, 14.25)

        code, out, err = self.run_cli(["--co2", "Canada", "--year", "2021"])

        self.assertEqual(0, code)
        self.assertEqual("", err)
        self.assertIn("Annual CO₂ emissions (per capita) for Canada in 2021", out)
        self.assertIn("t/person", out)

        repo.co2_value_for_entity_year.assert_called_once_with(
            entity_query="Canada",
            year=2021,
            only_countries=True,
        )

    @patch("command_line.ClimateRepository")
    @patch("command_line.get_db")
    def test_co2_list(self, mock_get_db, mock_repo_class) -> None:
        """--co2 (no country) should call co2_top_emitters"""

        mock_get_db.return_value = MagicMock()
        repo = mock_repo_class.return_value
        repo.co2_top_emitters.return_value = [("Qatar", 40.0), ("Canada", 14.25)]

        code, out, err = self.run_cli(["--co2", "--year", "2021", "--top", "2"])

        self.assertEqual(0, code)
        self.assertEqual("", err)
        self.assertIn("Top 2 entities", out)
        self.assertIn("1. Qatar:", out)

        repo.co2_top_emitters.assert_called_once_with(
            year=2021,
            top_n=2,
            only_countries=True,
        )

    @patch("command_line.ClimateRepository")
    @patch("command_line.get_db")
    def test_ranking_single_value(self, mock_get_db, mock_repo_class) -> None:
        """--ranking country should call forest_rank_for_entity + count"""

        mock_get_db.return_value = MagicMock()
        repo = mock_repo_class.return_value
        repo.forest_rank_for_entity.return_value = ("Brazil", 2020, 1, -2628412.5)
        repo.forest_count_entities_for_year.return_value = 200

        code, out, err = self.run_cli([
            "--ranking",
            "Brazil",
            "--year",
            "2020",
            "--order",
            "loss",
        ])

        self.assertEqual(0, code)
        self.assertEqual("", err)
        self.assertIn("Brazil rank in 2020", out)
        self.assertIn("1 of 200", out)

        repo.forest_rank_for_entity.assert_called_once_with(
            entity_query="Brazil",
            year=2020,
            order="loss",
            only_countries=True,
        )
        repo.forest_count_entities_for_year.assert_called_once_with(
            year=2020,
            only_countries=True,
        )

    @patch("command_line.ClimateRepository")
    @patch("command_line.get_db")
    def test_ranking_list(self, mock_get_db, mock_repo_class) -> None:
        """--ranking (no country) should call forest_rank_entities"""

        mock_get_db.return_value = MagicMock()
        repo = mock_repo_class.return_value
        repo.forest_rank_entities.return_value = [("Brazil", -10.0), ("Canada", 2.0)]

        code, out, err = self.run_cli(["--ranking", "--year", "2021", "--top", "2"])

        self.assertEqual(0, code)
        self.assertEqual("", err)
        self.assertIn("Forest change ranking for 2021", out)
        self.assertIn("1. Brazil:", out)

        repo.forest_rank_entities.assert_called_once_with(
            year=2021,
            order="loss",
            top_n=2,
            only_countries=True,
        )

    @patch("command_line.ClimateRepository")
    @patch("command_line.get_db")
    def test_include_aggregates_changes_only_countries(self, mock_get_db, mock_repo_class) -> None:
        """--include-aggregates should flip only_countries=False"""

        mock_get_db.return_value = MagicMock()
        repo = mock_repo_class.return_value
        repo.forest_value_for_entity_year.return_value = ("World", 2021, -123.0)

        code, out, err = self.run_cli([
            "--deforestation",
            "World",
            "--year",
            "2021",
            "--include-aggregates",
        ])

        self.assertEqual(0, code)
        self.assertEqual("", err)
        self.assertIn("World", out)

        repo.forest_value_for_entity_year.assert_called_once_with(
            entity_query="World",
            year=2021,
            only_countries=False,
        )

    @patch("command_line.ClimateRepository")
    @patch("command_line.get_db")
    def test_unknown_entity_returns_error(self, mock_get_db, mock_repo_class) -> None:
        """repository ValueError should become exit code 2 + helpful stderr"""

        mock_get_db.return_value = MagicMock()
        repo = mock_repo_class.return_value
        repo.co2_value_for_entity_year.side_effect = ValueError("Unknown entity name.")

        code, _out, err = self.run_cli(["--co2", "Atlantis", "--year", "2021"])

        self.assertEqual(2, code)
        self.assertIn("Error:", err)
        self.assertIn("Unknown entity", err)


if __name__ == "__main__":
    unittest.main()
