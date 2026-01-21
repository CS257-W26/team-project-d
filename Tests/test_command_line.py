"""
For testing out command lines
"""
from __future__ import annotations
import unittest

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from command_line import main
from ProductionCode.entity_utils import normalize_entity_name
from ProductionCode.forest_change import (
    load_forest_change_rows,
    is_country_row,
    latest_year_for_entity as forest_latest_year_for_entity,
    rank_for_entity as forest_rank_for_entity,
    rank_entities as forest_rank_entities,
    value_for_entity_year as forest_value_for_entity_year,
)
from ProductionCode.co2 import (
    load_co2_rows,
    value_for_entity_year as co2_value_for_entity_year,
    top_emitters,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "Data"

# run the CLI and capture stdout/stderr
def run_cli(argv: list[str]) -> tuple[int, str, str]:
    out = StringIO()
    err = StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        exit_code = main(argv)
    return exit_code, out.getvalue().strip(), err.getvalue().strip()

# unit tests for entity name normalization/matching
class TestEntityNormalization(unittest.TestCase):
    def test_normalize_entity_name_basic(self) -> None:
        self.assertEqual(normalize_entity_name("Brazil"), "brazil")
        self.assertEqual(normalize_entity_name("  Brazil  "), "brazil")
        self.assertEqual(normalize_entity_name("United States"), "unitedstates")

# unit tests for forest change (deforestation) query functions
class TestForestChangeQueries(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_forest_change_rows(DATA_DIR)

    def test_latest_year_for_entity(self) -> None:
        # brazil has values through the most recent year in the dataset
        self.assertEqual(forest_latest_year_for_entity(self.rows, "Brazil"), 2025)

    def test_value_for_entity_year_explicit_year(self) -> None:
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
        entity, year, value = forest_value_for_entity_year(
            rows=self.rows,
            entity_query="Brazil",
            year=None,
            only_countries=True,
        )
        self.assertEqual(year, 2025)
        self.assertAlmostEqual(value, -3256050.0, places=1)

    def test_rank_for_entity(self) -> None:
        entity, year, rank, value = forest_rank_for_entity(
            rows=self.rows,
            entity_query="Brazil",
            year=2020,
            order="loss",
            only_countries=True,
        )
        self.assertEqual(entity, "Brazil")
        self.assertEqual(year, 2020)
        # Brazil has the most negative net change (largest loss) in 2020, so it should be rank 1
        self.assertEqual(rank, 1)
        self.assertAlmostEqual(value, -2628412.5, places=1)

    def test_rank_entities_top_n(self) -> None:
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
        self.assertEqual(ranked[1][0], "Angola")
        self.assertAlmostEqual(ranked[1][1], -510031.25, places=2)

# unit tests for CO₂ per-capita queries
class TestCo2Queries(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_co2_rows(DATA_DIR)

    def test_co2_value_for_entity_year(self) -> None:
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

    def test_top_emitters(self) -> None:
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
        self.assertEqual(ranked[1][0], "Bahrain")
        self.assertAlmostEqual(ranked[1][1], 25.237510, places=3)


# acceptance tests for the CLI (per user story)
class TestCommandLineAcceptance(unittest.TestCase):

    # user story 1: deforestation value lookup
    def test_cli_deforestation_value(self) -> None:
        code, out, err = run_cli(
            ["--deforestation", "Brazil", "--year", "2020", "--data-dir", str(DATA_DIR)]
        )
        self.assertEqual(code, 0)
        self.assertIn("Annual change in forest area for Brazil in 2020", out)
        self.assertIn("-2,628,412.50 ha", out)
        self.assertEqual(err, "")

    # user story 1: default year should be latest for that country
    def test_cli_deforestation_default_year(self) -> None:
        code, out, err = run_cli(
            ["--deforestation", "Brazil", "--data-dir", str(DATA_DIR)]
        )
        self.assertEqual(code, 0)
        self.assertIn("for Brazil in 2025", out)
        self.assertIn("-3,256,050 ha", out)

    # user story 2: CO2 value lookup
    def test_cli_co2_value(self) -> None:
        code, out, err = run_cli(
            ["--co2", "Canada", "--year", "2021", "--data-dir", str(DATA_DIR), "--include-aggregates"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Annual CO₂ emissions (per capita) for Canada in 2021", out)
        self.assertIn("13.98 t/person", out)

    # user story 3: ranking by forest loss
    def test_cli_ranking_for_country(self) -> None:
        code, out, err = run_cli(
            ["--ranking", "Brazil", "--year", "2020", "--data-dir", str(DATA_DIR)]
        )
        self.assertEqual(code, 0)
        self.assertIn("Brazil rank in 2020", out)
        total = sum(1 for r in load_forest_change_rows(DATA_DIR) if r.year == 2020 and is_country_row(r))
        self.assertIn(f"1 of {total}", out)
        self.assertIn("-2,628,412.50 ha", out)

    # demonstration test
    def test_main_sys_argv_pattern(self) -> None:
        import sys
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
        code, out, err = run_cli(
            ["--deforestation", "NotACountry", "--data-dir", str(DATA_DIR)]
        )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("Error:", err)
