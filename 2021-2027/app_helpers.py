import json
from io import BytesIO

import pandas as pd


def filter_application_years(results, selected_years):
    return [row for row in results if row["year"] in selected_years]


def institution_category(institution):
    if "higher_education" in institution["registry_kinds"]:
        return "Visoko obrazovanje"

    type_text = " ".join(institution["institution_types"]).casefold()
    categories = {
        "Predškolska ustanova": "predškolska",
        "Osnovna škola": "osnovna škola",
        "Srednja škola": "srednja škola",
        "Umjetnička škola": "umjetnička škola",
        "Posebna ustanova": "posebna ustanova",
        "Obrazovanje odraslih": "obrazovanje odraslih",
    }
    matches = [
        category for category, label in categories.items() if label in type_text
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return "Kombinirani tipovi ustanova"
    return "Ostale školske ustanove"


def summarize_institution_types(
    projects, matches_by_record, institutions_by_id, institutions
):
    summary = {}
    for institution in institutions:
        if not {"school", "kindergarten", "higher_education"}.intersection(
            institution["registry_kinds"]
        ):
            continue
        category = institution_category(institution)
        bucket = summary.setdefault(
            category,
            {
                "category": category,
                "registered_institution_ids": set(),
                "matched_institution_ids": set(),
                "beneficiary_keys": set(),
                "project_record_count": 0,
                "project_ids": set(),
                "total_grant_eur": 0.0,
            },
        )
        bucket["registered_institution_ids"].add(institution["institution_id"])

    for project in projects:
        match = matches_by_record[project["record_id"]]
        institution_id = match["institution_id"]
        if (
            not institution_id
        ):
            continue
        institution = institutions_by_id[institution_id]
        category = institution_category(institution)
        bucket = summary[category]
        bucket["matched_institution_ids"].add(institution_id)
        bucket["beneficiary_keys"].add(project["beneficiary_key"])
        bucket["project_record_count"] += 1
        bucket["project_ids"].add(project["project_id"])
        bucket["total_grant_eur"] += project["grant_amount_eur"]

    rows = []
    for bucket in summary.values():
        registered_count = len(bucket["registered_institution_ids"])
        matched_count = len(bucket["matched_institution_ids"])
        rows.append(
            {
                "Vrsta ustanove": bucket["category"],
                "Ustanove u registru": registered_count,
                "Ustanove s povezanim projektom": matched_count,
                "Udio ustanova s povezanim projektom (%)": (
                    round(matched_count / registered_count * 100, 2)
                    if registered_count
                    else None
                ),
                "Korisnici": len(bucket["beneficiary_keys"]),
                "Projektni zapisi": bucket["project_record_count"],
                "Jedinstveni projektni brojevi": len(bucket["project_ids"]),
                "Odobreno (EUR)": round(bucket["total_grant_eur"], 2),
            }
        )
    return sorted(rows, key=lambda row: row["Vrsta ustanove"])


def summarize_regional_coverage(
    projects, matches_by_record, institutions_by_id, institutions
):
    registered_by_county = {}
    for institution in institutions:
        if not {"school", "kindergarten", "higher_education"}.intersection(
            institution["registry_kinds"]
        ) or not institution["county"]:
            continue
        county_summary = registered_by_county.setdefault(
            institution["county"],
            {
                "all": set(),
                "school": set(),
                "kindergarten": set(),
                "higher_education": set(),
            },
        )
        county_summary["all"].add(institution["institution_id"])
        for registry_kind in ("school", "kindergarten", "higher_education"):
            if registry_kind in institution["registry_kinds"]:
                county_summary[registry_kind].add(institution["institution_id"])

    projects_by_county = {}
    for project in projects:
        match = matches_by_record[project["record_id"]]
        institution_id = match["institution_id"]
        if (
            not institution_id
        ):
            continue
        institution = institutions_by_id[institution_id]
        if not {"school", "kindergarten", "higher_education"}.intersection(
            institution["registry_kinds"]
        ) or not institution["county"]:
            continue
        bucket = projects_by_county.setdefault(
            institution["county"],
            {
                "institution_ids": set(),
                "beneficiary_keys": set(),
                "project_records": 0,
                "project_ids": set(),
                "total_grant_eur": 0.0,
            },
        )
        bucket["institution_ids"].add(institution_id)
        bucket["beneficiary_keys"].add(project["beneficiary_key"])
        bucket["project_records"] += 1
        bucket["project_ids"].add(project["project_id"])
        bucket["total_grant_eur"] += project["grant_amount_eur"]

    rows = []
    for county, county_institutions in registered_by_county.items():
        matched = projects_by_county.get(county, {})
        registered_count = len(county_institutions["all"])
        matched_count = len(matched.get("institution_ids", set()))
        rows.append(
            {
                "Županija": county,
                "Registrirane školske ustanove": len(
                    county_institutions["school"]
                ),
                "Registrirana visoka učilišta": len(
                    county_institutions["higher_education"]
                ),
                "Registrirani dječji vrtići": len(
                    county_institutions["kindergarten"]
                ),
                "Registrirane obrazovne ustanove": registered_count,
                "Ustanove s povezanim projektom": matched_count,
                "Udio ustanova s povezanim projektom (%)": (
                    round(matched_count / registered_count * 100, 2)
                    if registered_count
                    else None
                ),
                "Korisnici": len(matched.get("beneficiary_keys", set())),
                "Projektni zapisi": matched.get("project_records", 0),
                "Jedinstveni projektni brojevi": len(
                    matched.get("project_ids", set())
                ),
                "Odobreno (EUR)": round(matched.get("total_grant_eur", 0.0), 2),
            }
        )
    return sorted(rows, key=lambda row: row["Županija"])


def compare_similar_institutions(
    projects,
    matches_by_record,
    institutions_by_id,
    selected_institution_id,
    limit=5,
    minimum_comparable_institutions=4,
):
    profiles = {}
    for project in projects:
        institution_id = matches_by_record[project["record_id"]]["institution_id"]
        if not institution_id or institution_id not in institutions_by_id:
            continue
        institution = institutions_by_id[institution_id]
        profile = profiles.setdefault(
            institution_id,
            {
                "institution_id": institution_id,
                "name": institution["name"],
                "city": institution["city"],
                "category": institution_category(institution),
                "project_ids": set(),
                "years": set(),
                "activities": set(),
                "grant_amount_eur": 0.0,
            },
        )
        profile["project_ids"].add(project["project_id"])
        profile["years"].add(project["year"])
        activity = project["activity_type"] or project["key_action"]
        if activity:
            profile["activities"].add(activity)
        profile["grant_amount_eur"] += project["grant_amount_eur"]

    selected = profiles.get(selected_institution_id)
    if selected is None:
        return None

    candidates = [
        profile
        for institution_id, profile in profiles.items()
        if institution_id != selected_institution_id
        and profile["category"] == selected["category"]
    ]
    result = {
        "selected": selected,
        "comparable_institution_count": len(candidates),
        "peers": [],
    }
    if len(candidates) < minimum_comparable_institutions:
        return result

    cohort = [selected, *candidates]
    project_counts = [len(profile["project_ids"]) for profile in cohort]
    grant_amounts = [profile["grant_amount_eur"] for profile in cohort]
    project_range = max(project_counts) - min(project_counts)
    grant_range = max(grant_amounts) - min(grant_amounts)

    def numeric_similarity(left, right, value_range):
        if value_range == 0:
            return 1.0 if left == right else 0.0
        return 1 - abs(left - right) / value_range

    def set_similarity(left, right):
        union = left | right
        return len(left & right) / len(union) if union else 1.0

    for candidate in candidates:
        similarities = (
            numeric_similarity(
                len(selected["project_ids"]),
                len(candidate["project_ids"]),
                project_range,
            ),
            set_similarity(selected["activities"], candidate["activities"]),
            set_similarity(selected["years"], candidate["years"]),
            numeric_similarity(
                selected["grant_amount_eur"],
                candidate["grant_amount_eur"],
                grant_range,
            ),
        )
        result["peers"].append(
            {
                **candidate,
                "similarity_percent": round(sum(similarities) / len(similarities) * 100, 1),
            }
        )

    result["peers"].sort(
        key=lambda profile: (
            -profile["similarity_percent"],
            profile["name"].casefold(),
            profile["city"].casefold(),
            profile["institution_id"],
        )
    )
    result["peers"] = result["peers"][:limit]
    return result


def project_export_frame(projects):
    return pd.DataFrame(
        [
            {
                "Godina": row["year"],
                "Sektor": row["sector"],
                "Korisnik": row["beneficiary_name"],
                "Mjesto korisnika (izvor)": row["city"],
                "Ključna aktivnost": row["key_action"],
                "Tip aktivnosti": row["activity_type"],
                "Projektni broj": row["project_id"],
                "Odobreno (EUR)": row["grant_amount_eur"],
                "Ažurirano": row["source_updated_at"],
            }
            for row in projects
        ]
    )


def dataset_export_frame(dataset):
    if isinstance(dataset, dict):
        frame = pd.json_normalize([dataset], sep=".")
    elif isinstance(dataset, list) and all(isinstance(row, dict) for row in dataset):
        frame = pd.json_normalize(dataset, sep=".")
    elif isinstance(dataset, list):
        frame = pd.DataFrame({"value": dataset})
    else:
        frame = pd.DataFrame({"value": [dataset]})

    for column in frame.columns:
        if frame[column].map(lambda value: isinstance(value, (dict, list))).any():
            frame[column] = frame[column].map(
                lambda value: json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else value
            )
    return frame


def excel_bytes(frame, sheet_name):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()
