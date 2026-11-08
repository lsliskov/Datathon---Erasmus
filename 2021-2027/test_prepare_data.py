import unittest

from prepare_data import (
    CURATED_ADDRESS_MATCHES,
    USER_CONFIRMED_SCHOOL_MATCHES,
    USER_CONFIRMED_UNMATCHED_PROJECT_ROWS,
    load_application_results,
    load_funding_results,
    load_institutions,
    build_outputs,
    load_study_programs,
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

    def test_matches_unique_name_even_when_registry_city_differs(self):
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
        self.assertEqual(
            result["match_status"],
            "matched_unique_name_location_differs",
        )
        self.assertEqual(result["institution_id"], "school-1")

    def test_matches_exact_registry_name_when_city_is_appended_to_beneficiary(self):
        project = {
            "record_id": "project::row-30",
            "project_id": "project",
            "source_row": 30,
            "beneficiary_name": "III. gimnazija Zagreb",
            "city": "Zagreb",
            "address": "Kušlanova 52",
        }
        institutions = [
            {
                "institution_id": "gimnazija-iii",
                "normalized_name": normalize_text("III. gimnazija"),
                "normalized_city": normalize_text("Zagreb"),
                "address": "KUŠLANOVA 52",
            },
            {
                "institution_id": "os-kuslan",
                "normalized_name": normalize_text("Osnovna škola Dragutina Kušlana"),
                "normalized_city": normalize_text("Zagreb"),
                "address": "KUŠLANOVA 52",
            },
        ]
        result = match_project(project, institutions)
        self.assertEqual(
            result["match_status"], "matched_exact_name_and_city_suffix"
        )
        self.assertEqual(result["institution_id"], "gimnazija-iii")

    def test_matches_shortened_name_by_unique_exact_address(self):
        project = {
            "record_id": "project::row-2",
            "project_id": "project",
            "beneficiary_name": "Tehnička škola",
            "address": "Eugena Kumičića 55",
            "city": "Slavonski Brod",
        }
        institutions = [
            {
                "institution_id": "school-sb",
                "normalized_name": normalize_text(
                    "Tehnička škola, Slavonski Brod"
                ),
                "normalized_city": normalize_text("Slavonski Brod"),
                "address": "EUGENA KUMIČIĆA 55",
            },
            {
                "institution_id": "school-po",
                "normalized_name": normalize_text("Tehnička škola"),
                "normalized_city": normalize_text("Požega"),
                "address": "Ratarnička 1",
            },
        ]
        result = match_project(project, institutions)
        self.assertEqual(
            result["match_status"],
            "matched_unique_address_and_city",
        )
        self.assertEqual(result["institution_id"], "school-sb")

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

    def test_higher_education_counties_use_unique_school_registry_city(self):
        institutions, _ = load_institutions()
        higher_education = [
            institution
            for institution in institutions
            if "higher_education" in institution["registry_kinds"]
        ]

        self.assertEqual(len(higher_education), 133)
        self.assertTrue(all(institution["county"] for institution in higher_education))
        self.assertTrue(
            all(
                "school_registry_city_lookup"
                in institution["county_assignment_methods"]
                for institution in higher_education
            )
        )

    def test_kindergarten_registry_is_included_and_projects_are_linked(self):
        outputs = build_outputs()
        kindergartens = [
            institution
            for institution in outputs["institutions"]
            if "kindergarten" in institution["registry_kinds"]
        ]
        self.assertEqual(len(kindergartens), 885)
        self.assertTrue(all(institution["county"] for institution in kindergartens))

        project = next(
            project
            for project in outputs["projects"]
            if project["source_row"] == 8
        )
        match = next(
            match
            for match in outputs["project_institution_matches"]
            if match["record_id"] == project["record_id"]
        )
        institution = next(
            institution
            for institution in kindergartens
            if institution["institution_id"] == match["institution_id"]
        )
        self.assertEqual(match["match_status"], "matched_exact_name_and_city")
        self.assertIn("Vladimir Nazor", institution["name"])

        nursery_project = next(
            project
            for project in outputs["projects"]
            if project["source_row"] == 181
        )
        nursery_match = next(
            match
            for match in outputs["project_institution_matches"]
            if match["record_id"] == nursery_project["record_id"]
        )
        nursery = next(
            institution
            for institution in kindergartens
            if institution["institution_id"] == nursery_match["institution_id"]
        )
        self.assertEqual(
            nursery_match["match_status"],
            "matched_unique_address_location_differs",
        )
        self.assertEqual(nursery["city"], "Pojatno")

    def test_shortened_technical_school_name_resolves_to_slavonski_brod(self):
        outputs = build_outputs()
        self.assertFalse(
            any(
                match["match_status"] == "location_mismatch"
                for match in outputs["project_institution_matches"]
            )
        )
        project = next(
            project
            for project in outputs["projects"]
            if project["source_row"] == 201
        )
        match = next(
            match
            for match in outputs["project_institution_matches"]
            if match["record_id"] == project["record_id"]
        )
        institution = next(
            institution
            for institution in outputs["institutions"]
            if institution["institution_id"] == match["institution_id"]
        )
        self.assertEqual(
            match["match_status"],
            "matched_unique_address_and_city",
        )
        self.assertIn("slavonski brod", institution["name"].casefold())
        self.assertEqual(institution["city"], "Slavonski Brod")

    def test_user_confirmed_primary_school_matches_and_rovinj_exceptions(self):
        outputs = build_outputs()
        projects = {
            project["source_row"]: project for project in outputs["projects"]
        }
        matches = {
            match["record_id"]: match
            for match in outputs["project_institution_matches"]
        }
        institutions = {
            institution["institution_id"]: institution
            for institution in outputs["institutions"]
        }

        confirmed_rows = set(USER_CONFIRMED_SCHOOL_MATCHES)
        self.assertEqual(len(confirmed_rows), 45)
        for source_row, registry_row in USER_CONFIRMED_SCHOOL_MATCHES.items():
            project = projects[source_row]
            match = matches[project["record_id"]]
            institution = institutions[match["institution_id"]]
            registry_record = next(
                record
                for record in institution["source_records"]
                if record["file"] == "data (1).csv"
                and record["row"] == registry_row
            )
            self.assertTrue(registry_record)
            self.assertEqual(
                match["match_status"], "matched_user_confirmed_school"
            )

        self.assertEqual(USER_CONFIRMED_UNMATCHED_PROJECT_ROWS, {74, 734, 742})
        for source_row in USER_CONFIRMED_UNMATCHED_PROJECT_ROWS:
            project = projects[source_row]
            self.assertEqual(
                matches[project["record_id"]]["match_status"], "unmatched"
            )

        for source_row, registry_row in ((30, 255), (633, 255)):
            project = projects[source_row]
            match = matches[project["record_id"]]
            institution = institutions[match["institution_id"]]
            self.assertEqual(match["match_status"], "matched_exact_name_and_city_suffix")
            self.assertTrue(
                any(
                    record["file"] == "data.csv"
                    and record["row"] == registry_row
                    for record in institution["source_records"]
                )
            )

        for source_row, registry_row in ((82, 268), (125, 97), (159, 511)):
            project = projects[source_row]
            match = matches[project["record_id"]]
            institution = institutions[match["institution_id"]]
            self.assertTrue(
                any(
                    record["file"] == "data (4).csv"
                    and record["row"] == registry_row
                    for record in institution["source_records"]
                )
            )

        self.assertEqual(len(CURATED_ADDRESS_MATCHES), 9)
        for source_row, (
            registry_file,
            registry_row,
        ) in CURATED_ADDRESS_MATCHES.items():
            project = projects[source_row]
            match = matches[project["record_id"]]
            institution = institutions[match["institution_id"]]
            self.assertEqual(
                match["match_status"], "matched_unique_address_and_city"
            )
            self.assertTrue(
                any(
                    record["file"] == registry_file
                    and record["row"] == registry_row
                    for record in institution["source_records"]
                )
            )

        unmatched = [
            match
            for match in outputs["project_institution_matches"]
            if match["match_status"] == "unmatched"
        ]
        self.assertEqual(len(unmatched), 693)

    def test_study_programs_link_to_provider_and_county(self):
        outputs = build_outputs()
        programs = outputs["study_programs"]
        matched = [
            program
            for program in programs
            if program["match_status"] == "matched_exact_name_and_city"
        ]
        unmatched = [
            program
            for program in programs
            if program["match_status"] == "unmatched"
        ]

        self.assertEqual(len(programs), 1727)
        self.assertEqual(len(matched), 1709)
        self.assertEqual(len(unmatched), 18)
        self.assertTrue(all(program["institution_id"] for program in matched))
        self.assertTrue(all(program["county"] for program in matched))
        self.assertEqual(
            sum(row["Zapisi studijskih programa"] for row in outputs["study_program_summary"]),
            len(matched),
        )


if __name__ == "__main__":
    unittest.main()
