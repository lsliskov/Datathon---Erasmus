import unittest

from prepare_data import (
    load_application_results,
    load_funding_results,
    load_institutions,
    build_outputs,
    match_project,
    normalize_text,
    parse_eur,
    parse_percent,
    summarize_applications,
)


class PrepareDataTests(unittest.TestCase):
    def test_normalizes_accents_and_school_abbreviations(self):
        self.assertEqual(
            normalize_text("OŠ  Ivana  Kukuljevića"),
            normalize_text("Osnovna škola Ivana Kukuljevića"),
        )

    def test_parses_croatian_amount_and_percentage(self):
        self.assertEqual(str(parse_eur("48.405,00 EUR")), "48405.00")
        self.assertEqual(str(parse_percent("73,2%")), "73.2")

    def test_matches_only_unique_exact_name_and_city(self):
        project = {
            "record_id": "project::row-2",
            "project_id": "project",
            "beneficiary_name": "OŠ Primjer",
            "city": "Zagreb",
        }
        institutions = [
            {
                "institution_id": "school-1",
                "normalized_name": normalize_text("Osnovna škola Primjer"),
                "normalized_city": normalize_text("Zagreb"),
            }
        ]
        result = match_project(project, institutions)
        self.assertEqual(result["match_status"], "matched_exact_name_and_city")
        self.assertEqual(result["institution_id"], "school-1")

    def test_marks_duplicate_exact_matches_ambiguous(self):
        project = {
            "record_id": "project::row-2",
            "project_id": "project",
            "beneficiary_name": "Škola Primjer",
            "city": "Zagreb",
        }
        institutions = [
            {
                "institution_id": "school-1",
                "normalized_name": normalize_text("Škola Primjer"),
                "normalized_city": normalize_text("Zagreb"),
            },
            {
                "institution_id": "school-2",
                "normalized_name": normalize_text("Škola Primjer"),
                "normalized_city": normalize_text("Zagreb"),
            },
        ]
        result = match_project(project, institutions)
        self.assertEqual(result["match_status"], "ambiguous_exact_name_and_city")
        self.assertIsNone(result["institution_id"])

    def test_does_not_match_same_name_in_a_different_city(self):
        project = {
            "record_id": "project::row-2",
            "project_id": "project",
            "beneficiary_name": "Škola Primjer",
            "city": "Split",
        }
        institutions = [
            {
                "institution_id": "school-1",
                "normalized_name": normalize_text("Škola Primjer"),
                "normalized_city": normalize_text("Zagreb"),
            }
        ]
        result = match_project(project, institutions)
        self.assertEqual(result["match_status"], "location_mismatch")
        self.assertIsNone(result["institution_id"])

    def test_application_summary_uses_only_annual_rows(self):
        summary = summarize_applications(load_application_results())
        self.assertEqual(
            [row["year"] for row in summary],
            [2021, 2022, 2023, 2024, 2025, 2026],
        )
        self.assertEqual(
            [(row["applications"], row["contracted"]) for row in summary],
            [
                (545, 306),
                (758, 410),
                (1111, 520),
                (1322, 575),
                (1261, 642),
                (1252, 640),
            ],
        )

    def test_funding_results_do_not_repeat_all_years_as_2026(self):
        results = load_funding_results()
        totals = [
            row for row in results
            if row["sector"] == "Ukupno" and row["measure"] == "Ugovoreno"
        ]
        self.assertEqual([row["year"] for row in totals], [2021, 2022, 2023, 2024, 2025, 2026])

    def test_quality_report_exposes_source_count_discrepancy(self):
        outputs = build_outputs()
        reconciliation = {
            row["year"]: row
            for row in outputs["data_quality"]["source_reconciliation"]
        }
        self.assertEqual(reconciliation[2025]["project_count_difference"], -1)
        self.assertEqual(reconciliation[2026]["project_count_difference"], 0)

    def test_registry_county_conflicts_are_not_silently_assigned(self):
        institutions, _ = load_institutions()
        for institution in institutions:
            if len(institution["county_candidates"]) > 1:
                self.assertEqual(institution["county"], "")


if __name__ == "__main__":
    unittest.main()
