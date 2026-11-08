import json
from io import BytesIO
from pathlib import Path
import unittest

from openpyxl import load_workbook

from app_helpers import (
    filter_application_years,
    compare_similar_institutions,
    dataset_export_frame,
    excel_bytes,
    project_export_frame,
    summarize_institution_types,
    summarize_regional_coverage,
)
from prepare_data import build_outputs
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).with_name("streamlit_app.py")


class StreamlitAppTests(unittest.TestCase):
    def test_all_pages_render_without_exceptions(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        self.assertEqual(len(app.exception), 0)

        pages = [
            "Regije",
            "Korisnici",
            "Koncentracija",
            "Podaci i metodologija",
            "Sažetak",
        ]
        minimum_downloads = {
            "Regije": 2,
            "Korisnici": 4,
            "Koncentracija": 1,
            "Podaci i metodologija": 5,
        }
        for page in pages:
            app.segmented_control[0].set_value(page)
            app.run(timeout=60)
            self.assertEqual(
                len(app.exception),
                0,
                f"Page {page!r} raised: {[item.message for item in app.exception]}",
            )
            for chart in app.get("plotly_chart"):
                config = json.loads(chart.proto.config)
                self.assertIs(
                    config["scrollZoom"],
                    False,
                    f"Scroll zoom should be disabled on {page!r}",
                )
            for download in app.get("download_button"):
                self.assertTrue(
                    download.proto.url.endswith(".xlsx"),
                    f"Download on {page!r} should be an XLSX file",
                )
            self.assertGreaterEqual(
                len(app.get("download_button")),
                minimum_downloads.get(page, 0),
                f"Expected XLSX exports beside the useful tables on {page!r}",
            )

    def test_empty_project_filters_render_empty_states(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.sidebar.multiselect[0].set_value([])
        app.sidebar.pills[0].set_value([])
        app.segmented_control[0].set_value("Koncentracija")
        app.run(timeout=60)
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(
            any("Nema projekata" in item.value for item in app.caption)
        )

    def test_concentration_can_be_limited_to_linked_education_institutions(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.segmented_control[0].set_value("Koncentracija")
        app.run(timeout=60)
        app.radio[0].set_value("Samo pouzdano povezane obrazovne ustanove")
        app.run(timeout=60)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("top 10" in item.label.casefold() for item in app.metric))

    def test_application_year_filter_is_independent_from_project_years(self):
        results = [
            {"year": 2021, "applications": 100},
            {"year": 2025, "applications": 250},
        ]
        self.assertEqual(
            filter_application_years(results, [2021]),
            [{"year": 2021, "applications": 100}],
        )

    def test_project_export_keeps_euro_amount_numeric(self):
        frame = project_export_frame(
            [
                {
                    "year": 2025,
                    "sector": "Odgoj",
                    "beneficiary_name": "Škola",
                    "city": "Zagreb",
                    "key_action": "KA1",
                    "activity_type": "KA121",
                    "project_id": "2025-1-HR01",
                    "grant_amount_eur": 1234.5,
                    "source_updated_at": None,
                }
            ]
        )
        self.assertEqual(frame["Odobreno (EUR)"].iloc[0], 1234.5)
        self.assertEqual(str(frame["Odobreno (EUR)"].dtype), "float64")

    def test_table_export_is_xlsx_and_keeps_amount_numeric(self):
        frame = project_export_frame(
            [
                {
                    "year": 2025,
                    "sector": "Odgoj",
                    "beneficiary_name": "Škola",
                    "city": "Zagreb",
                    "key_action": "KA1",
                    "activity_type": "KA121",
                    "project_id": "2025-1-HR01",
                    "grant_amount_eur": 1234.5,
                    "source_updated_at": None,
                }
            ]
        )
        workbook = load_workbook(BytesIO(excel_bytes(frame, "Projekti")))
        sheet = workbook["Projekti"]

        self.assertEqual(sheet["H1"].value, "Odobreno (EUR)")
        self.assertEqual(sheet["H2"].value, 1234.5)

    def test_prepared_dataset_export_flattens_columns_and_preserves_nested_values(self):
        frame = dataset_export_frame(
            [
                {
                    "year": 2025,
                    "grant_amount": 1234.5,
                    "metadata": {"source": "CKAN"},
                    "activities": ["KA1", "KA2"],
                }
            ]
        )
        workbook = load_workbook(BytesIO(excel_bytes(frame, "Podaci")))
        sheet = workbook["Podaci"]
        columns = {
            sheet.cell(row=1, column=column).value: column
            for column in range(1, sheet.max_column + 1)
        }

        self.assertEqual(sheet.cell(row=2, column=columns["year"]).value, 2025)
        self.assertEqual(
            sheet.cell(row=2, column=columns["grant_amount"]).value, 1234.5
        )
        self.assertEqual(
            sheet.cell(row=2, column=columns["metadata.source"]).value, "CKAN"
        )
        self.assertEqual(
            sheet.cell(row=2, column=columns["activities"]).value, '["KA1", "KA2"]'
        )

    def test_overview_year_axes_are_horizontal(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        charts = app.get("plotly_chart")

        self.assertEqual(len(charts), 3)
        for chart in charts:
            figure = json.loads(chart.proto.spec)
            self.assertEqual(figure["layout"]["xaxis"].get("tickangle", 0), 0)

    def test_methodology_page_includes_project_list_and_summary_table(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.segmented_control[0].set_value("Podaci i metodologija")
        app.run(timeout=60)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Popis projekata" in item.value for item in app.subheader))
        self.assertEqual(len(app.get("bar_chart")), 0)

    def test_concentration_slider_updates_the_top_share_metric(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.segmented_control[0].set_value("Koncentracija")
        app.run(timeout=60)
        app.slider[0].set_value(4)
        app.run(timeout=60)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any(item.label == "Udio top 4" for item in app.metric))

    def test_region_page_renders_local_county_map(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.segmented_control[0].set_value("Regije")
        app.run(timeout=60)
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(
            any("nije stopa prijava" in item.value for item in app.caption)
        )

    def test_region_page_keeps_registry_context_when_project_filters_are_empty(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.segmented_control[0].set_value("Regije")
        app.sidebar.multiselect[0].set_value([])
        app.run(timeout=60)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(
            any(
                "Karta i dalje prikazuje ustanove u registru" in item.value
                for item in app.warning
            )
        )

    def test_long_category_charts_have_full_name_hover_tooltips(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.segmented_control[0].set_value("Koncentracija")
        app.run(timeout=60)
        charts = app.get("plotly_chart")

        self.assertGreaterEqual(len(charts), 1)
        chart_spec = json.loads(charts[0].proto.spec)
        trace = chart_spec["data"][0]
        self.assertIn("%{y}", trace["hovertemplate"])
        self.assertIn("Odobreno", trace["hovertemplate"])
        self.assertTrue(any(" — " in label for label in trace["y"]))

    def test_institution_type_charts_include_complete_category_labels(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.segmented_control[0].set_value("Korisnici")
        app.run(timeout=60)
        charts = app.get("plotly_chart")

        self.assertGreaterEqual(len(charts), 2)
        for chart in charts[:2]:
            trace = json.loads(chart.proto.spec)["data"][0]
            self.assertIn("%{y}", trace["hovertemplate"])
            self.assertIn("Visoko obrazovanje", trace["y"])

    def test_institution_type_summary_reconciles_registered_and_matched_records(self):
        outputs = build_outputs()
        institutions_by_id = {
            row["institution_id"]: row for row in outputs["institutions"]
        }
        matches_by_record = {
            row["record_id"]: row
            for row in outputs["project_institution_matches"]
        }
        summary = summarize_institution_types(
            outputs["projects"],
            matches_by_record,
            institutions_by_id,
            outputs["institutions"],
        )

        self.assertEqual(
            sum(row["Ustanove u registru"] for row in summary),
            outputs["dashboard_summary"]["institution_count"],
        )
        self.assertEqual(
            sum(row["Projektni zapisi"] for row in summary),
            outputs["dashboard_summary"]["linked_project_count"],
        )
        matched_project_ids = {
            row["project_id"]
            for row in outputs["project_institution_matches"]
            if row["institution_id"]
        }
        self.assertEqual(
            sum(row["Jedinstveni projektni brojevi"] for row in summary),
            len(matched_project_ids),
        )
        self.assertIn(
            "Osnovna škola",
            {row["Vrsta ustanove"] for row in summary},
        )
        self.assertIn(
            "Visoko obrazovanje",
            {row["Vrsta ustanove"] for row in summary},
        )
        self.assertIn(
            "Predškolska ustanova",
            {row["Vrsta ustanove"] for row in summary},
        )

    def test_regional_coverage_uses_registry_counts_as_denominator(self):
        outputs = build_outputs()
        institutions_by_id = {
            row["institution_id"]: row for row in outputs["institutions"]
        }
        matches_by_record = {
            row["record_id"]: row
            for row in outputs["project_institution_matches"]
        }
        summary = summarize_regional_coverage(
            outputs["projects"],
            matches_by_record,
            institutions_by_id,
            outputs["institutions"],
        )
        county = next(
            row for row in summary if row["Županija"] == "Grad Zagreb županija"
        )

        self.assertGreater(county["Registrirane školske ustanove"], 0)
        self.assertGreater(county["Registrirana visoka učilišta"], 0)
        self.assertGreater(county["Registrirani dječji vrtići"], 0)
        self.assertGreater(county["Ustanove s povezanim projektom"], 0)
        self.assertLessEqual(
            county["Ustanove s povezanim projektom"],
            county["Registrirane obrazovne ustanove"],
        )
        self.assertEqual(
            sum(row["Projektni zapisi"] for row in summary),
            sum(row["project_count"] for row in outputs["regional_summary"]),
        )

    def test_similar_institutions_use_transparent_profile_features(self):
        institutions = {
            f"institution-{index}": {
                "institution_id": f"institution-{index}",
                "name": f"Škola {index}",
                "city": "Zagreb",
                "institution_types": ["Osnovna škola"],
                "registry_kinds": ["school"],
            }
            for index in range(5)
        }
        projects = []
        matches = {}
        project_profiles = {
            0: [
                ("2024-A", 2024, "KA121", 100.0),
                ("2025-B", 2025, "KA122", 200.0),
            ],
            1: [
                ("2024-A", 2024, "KA121", 100.0),
                ("2025-B", 2025, "KA122", 200.0),
            ],
            2: [("2024-C", 2024, "KA121", 50.0)],
            3: [
                ("2023-D", 2023, "KA121", 100.0),
                ("2024-E", 2024, "KA122", 200.0),
                ("2025-F", 2025, "KA120", 200.0),
            ],
            4: [
                ("2025-G", 2025, "KA122", 150.0),
                ("2026-H", 2026, "KA121", 200.0),
            ],
        }
        for institution_index, records in project_profiles.items():
            for project_index, (project_id, year, activity, amount) in enumerate(
                records
            ):
                record_id = f"record-{institution_index}-{project_index}"
                projects.append(
                    {
                        "record_id": record_id,
                        "project_id": project_id,
                        "year": year,
                        "activity_type": activity,
                        "key_action": "KA1",
                        "grant_amount_eur": amount,
                    }
                )
                matches[record_id] = {
                    "institution_id": f"institution-{institution_index}"
                }

        comparison = compare_similar_institutions(
            projects,
            matches,
            institutions,
            "institution-0",
        )

        self.assertEqual(comparison["comparable_institution_count"], 4)
        self.assertEqual(comparison["peers"][0]["institution_id"], "institution-1")
        self.assertEqual(comparison["peers"][0]["similarity_percent"], 100)
        self.assertEqual(len(comparison["selected"]["project_ids"]), 2)

    def test_similar_institutions_wait_for_enough_comparable_peers(self):
        institutions = {
            "selected": {
                "name": "Odabrana škola",
                "city": "Zagreb",
                "institution_types": ["Osnovna škola"],
                "registry_kinds": ["school"],
            },
            "peer": {
                "name": "Druga škola",
                "city": "Split",
                "institution_types": ["Osnovna škola"],
                "registry_kinds": ["school"],
            },
        }
        projects = [
            {
                "record_id": institution_id,
                "project_id": institution_id,
                "year": 2025,
                "activity_type": "KA121",
                "key_action": "KA1",
                "grant_amount_eur": 100.0,
            }
            for institution_id in institutions
        ]
        matches = {
            institution_id: {"institution_id": institution_id}
            for institution_id in institutions
        }

        comparison = compare_similar_institutions(
            projects,
            matches,
            institutions,
            "selected",
        )

        self.assertEqual(comparison["comparable_institution_count"], 1)
        self.assertEqual(comparison["peers"], [])

    def test_institution_page_explains_the_similar_profile_comparison(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.segmented_control[0].set_value("Korisnici")
        app.run(timeout=60)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(
            any("Pametna usporedba sličnih ustanova" in item.value for item in app.subheader)
        )
        self.assertTrue(
            any("Usporedili smo je s" in item.value for item in app.markdown)
        )


if __name__ == "__main__":
    unittest.main()
