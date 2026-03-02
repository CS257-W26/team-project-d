"""Unit tests for command_line.py."""
# pylint: disable=protected-access

from __future__ import annotations

import io
import unittest
from unittest.mock import MagicMock, patch

import command_line


class TestCommandLine(unittest.TestCase):
    """Tests for the CLI interface."""

    def test_build_parser_and_helper_functions(self) -> None:
        """Parser and small helpers should support the CLI contract."""
        parser = command_line.build_parser()
        args = parser.parse_args(["--co2", "Canada"])
        repo = MagicMock()
        repo.resolve_country.return_value = "United States"

        with patch("sys.stderr", new=io.StringIO()) as stderr:
            error_code = command_line._print_error("boom")

        self.assertEqual(args.co2, "Canada")
        self.assertIsNone(args.year)
        self.assertEqual(
            command_line._resolve_country(repo, "United_States"),
            "United States",
        )
        self.assertEqual(error_code, 2)
        self.assertIn("boom", stderr.getvalue())

    @patch("command_line.get_db")
    @patch("command_line.ClimateRepository")
    def test_deforestation_with_explicit_year(
        self,
        repo_cls: MagicMock,
        _get_db: MagicMock,
    ) -> None:
        """The deforestation lookup should print one formatted value."""
        repo = MagicMock()
        repo.resolve_country.return_value = "United States"
        repo.forest_latest_year_for_country.return_value = 2022
        repo.forest_value.return_value = 1234.0
        repo_cls.return_value = repo

        with patch("builtins.print") as mock_print:
            exit_code = command_line.main(
                ["--deforestation", "United_States", "--year", "2010"]
            )

        self.assertEqual(exit_code, 0)
        repo.resolve_country.assert_called()
        repo.forest_value.assert_called_with("United States", 2010)
        printed = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
        self.assertIn("United States", printed)
        self.assertIn("2010", printed)

    @patch("command_line.get_db")
    @patch("command_line.ClimateRepository")
    def test_co2_defaults_to_latest_year(
        self,
        repo_cls: MagicMock,
        _get_db: MagicMock,
    ) -> None:
        """When year is omitted, the CLI should use the latest year."""
        repo = MagicMock()
        repo.resolve_country.return_value = "Canada"
        repo.co2_latest_year_for_country.return_value = 2020
        repo.co2_value.return_value = 1.5
        repo_cls.return_value = repo

        with patch("builtins.print"):
            exit_code = command_line.main(["--co2", "Canada"])

        self.assertEqual(exit_code, 0)
        repo.co2_latest_year_for_country.assert_called_with("Canada")
        repo.co2_value.assert_called_with("Canada", 2020)

    @patch("command_line.get_db")
    @patch("command_line.ClimateRepository")
    def test_unknown_country_returns_error(
        self,
        repo_cls: MagicMock,
        _get_db: MagicMock,
    ) -> None:
        """Unknown countries should return a non-zero exit code."""
        repo = MagicMock()
        repo.resolve_country.return_value = None
        repo_cls.return_value = repo

        with patch("builtins.print") as mock_print:
            exit_code = command_line.main(["--co2", "Narnia"])

        self.assertEqual(exit_code, 2)
        mock_print.assert_called()


    @patch("command_line.get_db")
    @patch("command_line.ClimateRepository")
    def test_deforestation_unknown_country_returns_error(
        self,
        repo_cls: MagicMock,
        _get_db: MagicMock,
    ) -> None:
        """Unknown countries should fail for the deforestation feature too."""
        repo = MagicMock()
        repo.resolve_country.return_value = None
        repo_cls.return_value = repo

        with patch("builtins.print") as mock_print:
            exit_code = command_line.main(["--deforestation", "Narnia"])

        self.assertEqual(exit_code, 2)
        mock_print.assert_called()

    @patch("command_line.get_db")
    @patch("command_line.ClimateRepository")
    def test_deforestation_missing_value_returns_error(
        self,
        repo_cls: MagicMock,
        _get_db: MagicMock,
    ) -> None:
        """Missing forest data should return an error code."""
        repo = MagicMock()
        repo.resolve_country.return_value = "United States"
        repo.forest_value.return_value = None
        repo_cls.return_value = repo

        with patch("builtins.print") as mock_print:
            exit_code = command_line.main(["--deforestation", "United_States"])

        self.assertEqual(exit_code, 2)
        mock_print.assert_called()

    @patch("command_line.get_db")
    @patch("command_line.ClimateRepository")
    def test_co2_missing_value_returns_error(
        self,
        repo_cls: MagicMock,
        _get_db: MagicMock,
    ) -> None:
        """Missing CO₂ data should return an error code."""
        repo = MagicMock()
        repo.resolve_country.return_value = "Canada"
        repo.co2_latest_year_for_country.return_value = 2020
        repo.co2_value.return_value = None
        repo_cls.return_value = repo

        with patch("builtins.print") as mock_print:
            exit_code = command_line.main(["--co2", "Canada"])

        self.assertEqual(exit_code, 2)
        mock_print.assert_called()
