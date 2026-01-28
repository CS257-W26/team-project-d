"""
Unit and acceptance tests for the command-line interface
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from command_line import main
from ProductionCode.co2 import (
    latest_year as co2_latest_year,
    load_co2_rows,
    top_emitters,
    value_for_entity_year as co2_value_for_entity_year,
)
from ProductionCode.entity_utils import match_entity_name, normalize_entity_name
from ProductionCode.forest_change import (
    count_entities_for_year,
    is_country_row,
    latest_year as forest_latest_year,
    latest_year_for_entity as forest_latest_year_for_entity,
    load_forest_change_rows,
    rank_entities as forest_rank_entities,
    rank_for_entity as forest_rank_for_entity,
    value_for_entity_year as forest_value_for_entity_year,
)
from ProductionCode.io_utils import read_csv_records
from ProductionCode.numbers import format_number

DATA_DIR = Path(__file__).resolve().parents[1] / "Data"


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    """run the CLI with argv and return"""
    out = StringIO()
    err = StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        exit_code = main(argv)
    return exit_code, out.getvalue().strip(), err.getvalue().strip()


class TestEntityNormalization(unittest.TestCase):
    """tests for forgiving entity-name normalization and matching"""

    def test_normalize_entity_name_basic(self) -> None:
        """normalize common inputs into stable keys"""
        self.assertEqual(normalize_entity_name("Brazil"), "brazil")
        self.assertEqual(normalize_entity_name("  Brazil  "), "brazil")
        self.assertEqual(normalize_entity_name("United States"), "unitedstates")

    def test_match_entity_name_suggests_close_matches(self) -> None:
        """unknown names should raise an error"""
        with self.assertRaises(ValueError) as ctx:
            match_entity_name("Brazl", ["Brazil", "Canada"])
        self.assertIn("Did you mean", str(ctx.exception))


class TestForestChangeQueries(unittest.TestCase):
    """unit tests for forest-change query functions"""

    @classmethod
    def setUpClass(cls) -> None:
        """load forest-change rows once for the whole test class"""
        cls.rows = load_forest_change_rows(DATA_DIR)

    def test_latest_year_for_entity_matches_max_in_rows(self) -> None:
        """latest_year_for_entity should match the max year in the raw rows"""
        expected = max(r.year for r in self.rows if r.entity == "Brazil")
        actual = forest_latest_year_for_entity(self.rows, "Brazil")
        self.assertEqual(actual, expected)

    def test_value_for_entity_year_explicit_year(self) -> None:
        """value lookup should return the requested year when provided"""
        entity, year, value = forest_value_for_entity_year(
            rows=self.rows,
            entity_query="Brazil",
            year=2020,
            only_countries=True,
        )
        self.assertEqual(entity, "Brazil")
        self.assertEqual(year, 2020)
        self.assertAlmostEqual(value, -2628412.5, places=1)

    def test_value_for_entity_year_default_latest_year(self) -> None:
        """value lookup should default to the latest year for that entity"""
        entity, year, value = forest_value_for_entity_year(
            rows=self.rows,
            entity_query="Brazil",
            year=None,
            only_countries=True,
        )
        expected_year = max(r.year for r in self.rows if r.entity == "Brazil")
        self.assertEqual(entity, "Brazil")
        self.assertEqual(year, expected_year)
        self.assertIsInstance(value, float)

    def test_rank_entities_invalid_order_raises(self) -> None:
        """rank_entities should reject invalid order values"""
        with self.assertRaises(ValueError):
            forest_rank_entities(
                rows=self.rows,
                year=2020,
                order="not-a-real-order",
                top_n=5,
                only_countries=True,
            )

    def test_rank_for_entity_loss_order(self) -> None:
        """brazil should be ranked for loss order in 2020"""
        entity, year, rank, value = forest_rank_for_entity(
            rows=self.rows,
            entity_query="Brazil",
            year=2020,
            order="loss",
            only_countries=True,
        )
        self.assertEqual(entity, "Brazil")
        self.assertEqual(year, 2020)
        self.assertEqual(rank, 1)
        self.assertAlmostEqual(value, -2628412.5, places=1)

    def test_rank_entities_top_n(self) -> None:
        """ranking should return top_n results in the correct order"""
        ranked = forest_rank_entities(
            rows=self.rows,
            year=2020,
            order="loss",
            top_n=2,
            only_countries=True,
        )
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0][0], "Brazil")
        self.assertAlmostEqual(ranked[0][1], -2628412.5, places=1)

    def test_latest_year_only_countries_filter(self) -> None:
        """latest_year should respect the only_countries filter"""
        year_all = forest_latest_year(self.rows, only_countries=False)
        year_countries = forest_latest_year(self.rows, only_countries=True)
        self.assertGreaterEqual(year_all, year_countries)


class TestCo2Queries(unittest.TestCase):
    """unit tests for co2 per-capita queries"""

    @classmethod
    def setUpClass(cls) -> None:
        """load co2 rows once for the whole test class"""
        cls.rows = load_co2_rows(DATA_DIR)
        cls.country_entities = set()
        for row in load_forest_change_rows(DATA_DIR):
            if is_country_row(row):
                cls.country_entities.add(row.entity)

    def test_co2_value_for_entity_year(self) -> None:
        """co2 value lookup should return the right number for a year"""
        entity, year, value = co2_value_for_entity_year(
            rows=self.rows,
            entity_query="Canada",
            year=2020,
            only_countries=False,
            country_entities=None,
        )
        self.assertEqual(entity, "Canada")
        self.assertEqual(year, 2020)
        self.assertAlmostEqual(value, 13.732821, places=3)

    def test_co2_latest_year_with_country_filter(self) -> None:
        """latest_year should work with only_countries=True"""
        year = co2_latest_year(
            self.rows,
            only_countries=True,
            country_entities=self.country_entities,
        )
        self.assertIsInstance(year, int)

    def test_top_emitters(self) -> None:
        """top emitters should return a sorted list of results"""
        ranked = top_emitters(
            rows=self.rows,
            year=2020,
            top_n=2,
            only_countries=False,
            country_entities=None,
        )
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0][0], "Qatar")
        self.assertAlmostEqual(ranked[0][1], 36.145443, places=3)

    def test_top_emitters_missing_year_raises(self) -> None:
        """requesting a year with no data should raise ValueError"""
        with self.assertRaises(ValueError):
            top_emitters(
                rows=self.rows,
                year=1600,
                top_n=2,
                only_countries=False,
                country_entities=None,
            )


class TestNumbers(unittest.TestCase):
    """unit tests for number formatting"""

    def test_format_number_integer_and_decimal(self) -> None:
        """format_number should format integers without decimals and decimals with rounding"""
        self.assertEqual(format_number(1000.0), "1,000")
        self.assertEqual(format_number(12.3456, decimals=2), "12.35")


class TestIoUtils(unittest.TestCase):
    """unit tests for CSV reading helpers"""

    def test_read_csv_records_missing_file_raises(self) -> None:
        """missing files should raise FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            read_csv_records(Path("/definitely/not/a/real/file.csv"))

    def test_read_csv_records_no_header_raises(self) -> None:
        """csv files without a header row should raise ValueError"""
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "no_header.csv"
            csv_path.write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_csv_records(csv_path)


class TestCommandLineAcceptance(unittest.TestCase):
    """acceptance tests for the CLI (mapped to user stories)"""

    def test_cli_deforestation_value(self) -> None:
        """user story 1: deforestation value lookup by country and year"""
        code, out, err = run_cli(
            [
                "--deforestation",
                "Brazil",
                "--year",
                "2020",
                "--data-dir",
                str(DATA_DIR),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Annual change in forest area for Brazil in 2020", out)
        self.assertIn("-2,628,412.50 ha", out)

    def test_cli_deforestation_default_year(self) -> None:
        """user story 1: default year should be the latest year for that country"""
        rows = load_forest_change_rows(DATA_DIR)
        expected_year = max(r.year for r in rows if r.entity == "Brazil")
        expected_value = next(
            r.value_ha for r in rows if r.entity == "Brazil" and r.year == expected_year
        )

        code, out, err = run_cli(["--deforestation", "Brazil", "--data-dir", str(DATA_DIR)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")

        self.assertIn(f"for Brazil in {expected_year}", out)
        self.assertIn(f"{format_number(expected_value)} ha", out)

    def test_cli_co2_value(self) -> None:
        """user story 2: CO₂ value lookup by country and year"""
        code, out, err = run_cli(
            [
                "--co2",
                "Canada",
                "--year",
                "2021",
                "--data-dir",
                str(DATA_DIR),
                "--include-aggregates",
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Annual CO₂ emissions (per capita) for Canada in 2021", out)
        self.assertIn("t/person", out)

    def test_cli_co2_default_year(self) -> None:
        """user story 2: CO₂ default year should be the latest year for that country"""
        rows = load_co2_rows(DATA_DIR)
        expected_year = max(r.year for r in rows if r.entity == "Canada")
        expected_value = next(
            r.value_tonnes_per_capita
            for r in rows
            if r.entity == "Canada" and r.year == expected_year
        )

        code, out, err = run_cli(["--co2", "Canada", "--data-dir", str(DATA_DIR)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")

        self.assertIn(f"for Canada in {expected_year}", out)
        self.assertIn(f"{expected_value:.2f} t/person", out)

    def test_cli_ranking_for_country(self) -> None:
        """user story 3: ranking for a country in a specific year"""
        code, out, err = run_cli(
            ["--ranking", "Brazil", "--year", "2020", "--data-dir", str(DATA_DIR)]
        )
        self.assertEqual(code, 0)
        self.assertEqual(err, "")

        total = count_entities_for_year(
            load_forest_change_rows(DATA_DIR),
            year=2020,
            only_countries=True,
        )
        self.assertIn("Brazil rank in 2020", out)
        self.assertIn(f"1 of {total}", out)
        self.assertIn("-2,628,412.50 ha", out)

    def test_cli_list_outputs(self) -> None:
        """CLI should support list outputs when no country is provided"""
        code, out, err = run_cli(
            ["--deforestation", "--year", "2020", "--top", "3", "--data-dir", str(DATA_DIR)]
        )
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Top 3", out)

        code, out, err = run_cli(
            ["--ranking", "--year", "2020", "--top", "3", "--data-dir", str(DATA_DIR)]
        )
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Forest change ranking for 2020", out)

        code, out, err = run_cli(["--co2", "--top", "3", "--data-dir", str(DATA_DIR)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Top 3", out)

    def test_main_sys_argv_pattern(self) -> None:
        """sys.argv / sys.stdout pattern"""
        original_argv = sys.argv
        original_stdout = sys.stdout
        try:
            sys.argv = [
                "command_line.py",
                "--deforestation",
                "Brazil",
                "--year",
                "2020",
                "--data-dir",
                str(DATA_DIR),
            ]
            sys.stdout = StringIO()
            exit_code = main()
            output = sys.stdout.getvalue().strip()
        finally:
            sys.argv = original_argv
            sys.stdout = original_stdout

        self.assertEqual(exit_code, 0)
        self.assertIn("Brazil in 2020", output)

    def test_cli_error_unknown_country(self) -> None:
        """unknown countries should produce a non-zero exit code and an error message"""
        code, out, err = run_cli(["--deforestation", "NotACountry", "--data-dir", str(DATA_DIR)])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("Error:", err)

    def test_cli_error_missing_data_dir(self) -> None:
        """missing data directory should produce a helpful error"""
        code, out, err = run_cli(["--deforestation", "Brazil", "--data-dir", "/nope"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("CSV file not found", err)
    
