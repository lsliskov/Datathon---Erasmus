import pandas as pd


def filter_application_years(results, selected_years):
    return [row for row in results if row["year"] in selected_years]


def project_export_frame(projects):
    return pd.DataFrame(
        [
            {
                "Godina": row["year"],
                "Sektor": row["sector"],
                "Korisnik": row["beneficiary_name"],
                "Mjesto": row["city"],
                "Ključna aktivnost": row["key_action"],
                "Tip aktivnosti": row["activity_type"],
                "Projektni broj": row["project_id"],
                "Odobreno (EUR)": row["grant_amount_eur"],
                "Ažurirano": row["source_updated_at"],
            }
            for row in projects
        ]
    )
