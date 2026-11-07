from pathlib import Path
import unittest

from app_helpers import filter_application_years, project_export_frame
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).with_name("streamlit_app.py")


class StreamlitAppTests(unittest.TestCase):
    def test_all_pages_render_without_exceptions(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        self.assertEqual(len(app.exception), 0)

        pages = [
            "Regije",
            "Korisnici i ustanove",
            "Koncentracija financiranja",
            "Projekti",
            "Kvaliteta podataka",
            "Pregled",
        ]
        for page in pages:
            app.sidebar.selectbox[0].set_value(page)
            app.run(timeout=60)
            self.assertEqual(
                len(app.exception),
                0,
                f"Page {page!r} raised: {[item.message for item in app.exception]}",
            )

    def test_empty_project_filters_render_empty_states(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.sidebar.multiselect[0].set_value([])
        app.sidebar.multiselect[1].set_value([])
        app.sidebar.selectbox[0].set_value("Koncentracija financiranja")
        app.run(timeout=60)
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(
            any("Nema projekata" in item.value for item in app.info)
        )

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

    def test_region_page_renders_local_county_map(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
        app.sidebar.selectbox[0].set_value("Regije")
        app.run(timeout=60)
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Siva područja bez ispune" in item.value for item in app.caption))


if __name__ == "__main__":
    unittest.main()
