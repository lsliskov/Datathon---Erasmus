import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "processed"

PROJECTS_FILE = "tablica_7_popis-financiranih-projekata-programa-erasmus_2021_2027.csv"
PROJECT_FIELDS = {
    "year": "Natječajna godina",
    "sector": "Područje",
    "deadline": "Rok",
    "key_action": "Ključna aktivnost",
    "activity_type": "Tip aktivnosti",
    "project_id": "Projektni broj",
    "beneficiary_name": "Naziv korisnika",
    "address": "Adresa korisnika",
    "city": "Mjesto",
    "postal_code": "Poštanski broj",
    "grant_amount": "Iznos odobrenih bespovratnih sredstava",
    "source_updated_at": "Posljednje ažuriranje podataka",
}

SCHOOL_SOURCES = (
    ("data (1).csv", "school"),
    ("data.csv", "school"),
)
HIGHER_EDUCATION_SOURCE = ("data (2).csv", "higher_education")

FINANCIAL_SECTORS = (
    ("Odgoj i opće obrazovanje", 3),
    ("Strukovno obrazovanje i osposobljavanje", 4),
    ("Visoko obrazovanje", 5),
    ("Obrazovanje odraslih", 6),
    ("Mladi", 7),
    ("Sport", 8),
    ("Ukupno", 9),
)

APPLICATION_SECTORS = (
    ("Odgoj i opće obrazovanje", 4),
    ("Strukovno obrazovanje i osposobljavanje", 5),
    ("Visoko obrazovanje", 6),
    ("Obrazovanje odraslih", 7),
    ("Mladi", 8),
    ("Sport", 9),
    ("Ukupno", 10),
)


def normalize_text(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()
    value = re.sub(r"\b(o s|os)\b", "osnovna skola", value)
    value = re.sub(r"\b(s s|ss)\b", "srednja skola", value)
    value = re.sub(r"\b(d v|dv)\b", "djecji vrtic", value)
    return re.sub(r"\s+", " ", value)


def parse_eur(value):
    value = str(value or "").strip().replace("EUR", "").replace("€", "").strip()
    if not value:
        return None
    try:
        return Decimal(value.replace(".", "").replace(",", "."))
    except InvalidOperation as error:
        raise ValueError(f"Invalid EUR amount: {value!r}") from error


def parse_percent(value):
    value = str(value or "").strip().replace("%", "").replace(",", ".")
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"Invalid percentage: {value!r}") from error


def _year(value):
    match = re.fullmatch(r"\s*(\d{4})\.?\s*", str(value or ""))
    return int(match.group(1)) if match else None


def _header_key(value):
    return normalize_text(value)


def _read_dict_rows(filename, delimiter=","):
    path = BASE_DIR / filename
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError(f"{filename} has no header row")
        for line_number, row in enumerate(reader, start=2):
            yield line_number, {_header_key(key): (value or "").strip() for key, value in row.items() if key}


def _value(row, *names):
    for name in names:
        value = row.get(_header_key(name), "")
        if value:
            return value
    return ""


def _read_matrix(filename, delimiter=";"):
    with (BASE_DIR / filename).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.reader(source, delimiter=delimiter))


def _amount_number(value):
    return float(value.quantize(Decimal("0.01"))) if value is not None else None


def _stable_id(prefix, parts):
    key = "\x1f".join(str(part or "") for part in parts)
    return f"{prefix}-{hashlib.sha1(key.encode('utf-8')).hexdigest()[:12]}"


def load_projects():
    projects = []
    for row_number, row in _read_dict_rows(PROJECTS_FILE, delimiter=";"):
        project = {
            "record_id": "",
            "source_row": row_number,
            "year": _year(_value(row, PROJECT_FIELDS["year"])),
            "sector": _value(row, PROJECT_FIELDS["sector"]),
            "deadline": _value(row, PROJECT_FIELDS["deadline"]),
            "key_action": _value(row, PROJECT_FIELDS["key_action"]),
            "activity_type": _value(row, PROJECT_FIELDS["activity_type"]),
            "project_id": _value(row, PROJECT_FIELDS["project_id"]),
            "beneficiary_name": _value(row, PROJECT_FIELDS["beneficiary_name"]),
            "address": _value(row, PROJECT_FIELDS["address"]),
            "city": _value(row, PROJECT_FIELDS["city"]),
            "postal_code": _value(row, PROJECT_FIELDS["postal_code"]),
            "grant_amount_eur": _amount_number(
                parse_eur(_value(row, PROJECT_FIELDS["grant_amount"]))
            ),
            "source_updated_at": _value(row, PROJECT_FIELDS["source_updated_at"]) or None,
        }
        missing = [
            field
            for field in ("year", "sector", "project_id", "beneficiary_name", "grant_amount_eur")
            if project[field] in (None, "")
        ]
        if missing:
            raise ValueError(
                f"{PROJECTS_FILE} row {row_number} is missing required values: "
                f"{', '.join(missing)}"
            )
        project["record_id"] = f"{project['project_id']}::row-{row_number}"
        project["beneficiary_key"] = _stable_id(
            "recipient",
            (normalize_text(project["beneficiary_name"]), normalize_text(project["city"])),
        )
        projects.append(project)
    return projects


def load_institutions():
    records = []
    sources = list(SCHOOL_SOURCES) + [HIGHER_EDUCATION_SOURCE]
    for filename, registry_kind in sources:
        for row_number, row in _read_dict_rows(filename):
            if registry_kind == "school":
                name = _value(row, "Naziv")
                city = _value(row, "Mjesto")
                address = _value(row, "Adresa")
                postal_code = _value(row, "PoštanskiBroj", "Poštanski broj")
                county = _value(row, "Županija", "Župnija")
                institution_type = _value(row, "TipUstanove")
                registry_code = _value(row, "Šifra")
            else:
                name = _value(row, "NazivUstanove")
                city = _value(row, "Mjesto")
                address = _value(row, "Adresa")
                postal_code = ""
                county = ""
                institution_type = _value(row, "VrstaUstanove")
                registry_code = _value(row, "mbu")
            if not name:
                raise ValueError(f"{filename} row {row_number} has no institution name")
            records.append(
                {
                    "name": name,
                    "normalized_name": normalize_text(name),
                    "city": city,
                    "normalized_city": normalize_text(city),
                    "address": address,
                    "postal_code": postal_code,
                    "county": county,
                    "institution_type": institution_type,
                    "registry_kind": registry_kind,
                    "registry_code": registry_code,
                    "source_file": filename,
                    "source_row": row_number,
                }
            )

    grouped = {}
    for record in records:
        identity = (
            record["normalized_name"],
            record["normalized_city"],
            normalize_text(record["address"]),
            record["postal_code"],
        )
        institution = grouped.get(identity)
        if institution is None:
            institution = {
                "institution_id": _stable_id("institution", identity),
                "name": record["name"],
                "city": record["city"],
                "address": record["address"],
                "postal_code": record["postal_code"],
                "county": "",
                "county_candidates": [],
                "institution_types": [],
                "registry_kinds": [],
                "source_records": [],
                "normalized_name": record["normalized_name"],
                "normalized_city": record["normalized_city"],
            }
            grouped[identity] = institution
        for field, value in (
            ("institution_types", record["institution_type"]),
            ("registry_kinds", record["registry_kind"]),
            ("county_candidates", record["county"]),
        ):
            if value and value not in institution[field]:
                institution[field].append(value)
        institution["source_records"].append(
            {
                "file": record["source_file"],
                "row": record["source_row"],
                "registry_code": record["registry_code"] or None,
            }
        )
    institutions = list(grouped.values())
    for institution in institutions:
        if len(institution["county_candidates"]) == 1:
            institution["county"] = institution["county_candidates"][0]
    return institutions, len(records)


def match_project(project, institutions, institutions_by_name=None):
    if institutions_by_name is None:
        institutions_by_name = defaultdict(list)
        for institution in institutions:
            institutions_by_name[institution["normalized_name"]].append(institution)
    name_candidates = institutions_by_name.get(
        normalize_text(project["beneficiary_name"]), []
    )
    city = normalize_text(project["city"])
    city_candidates = [item for item in name_candidates if item["normalized_city"] == city]

    if len(city_candidates) == 1:
        status = "matched_exact_name_and_city"
        matched_id = city_candidates[0]["institution_id"]
        candidates = city_candidates
    elif len(city_candidates) > 1:
        status = "ambiguous_exact_name_and_city"
        matched_id = None
        candidates = city_candidates
    elif name_candidates:
        status = "location_mismatch"
        matched_id = None
        candidates = name_candidates
    else:
        status = "unmatched"
        matched_id = None
        candidates = []

    return {
        "record_id": project["record_id"],
        "project_id": project["project_id"],
        "beneficiary_name": project["beneficiary_name"],
        "city": project["city"],
        "match_status": status,
        "institution_id": matched_id,
        "candidate_institution_ids": [item["institution_id"] for item in candidates],
        "candidate_count": len(candidates),
    }


def load_funding_results():
    rows = _read_matrix(
        "tablica_8_pregled-financijskih-rezultata-programa-erasmus-2021_2027.csv"
    )
    results = []
    year = None
    for row in rows[4:]:
        if len(row) < 10:
            continue
        year_cell = row[0].replace("\n", "").strip()
        if year_cell:
            year = _year(year_cell)
        measure = row[2].strip()
        if year is None or year < 2021 or year > 2026 or not measure:
            continue
        is_percentage = measure.startswith("%")
        for sector, column in FINANCIAL_SECTORS:
            raw_value = row[column].strip()
            value = parse_percent(raw_value) if is_percentage else parse_eur(raw_value)
            results.append(
                {
                    "year": year,
                    "measure": measure,
                    "sector": sector,
                    "unit": "percent" if is_percentage else "EUR",
                    "value": float(value) if value is not None else None,
                }
            )
    return results


def load_application_results():
    rows = _read_matrix(
        "tablica_9_broj-erasmus-zaprimljenih-i-odobrenih-projekata-2021_2027.csv"
    )
    if len(rows) < 4:
        raise ValueError("Applications source is missing its header row")
    results = []
    year = None
    key_action = None
    for row in rows[3:]:
        if len(row) < 11:
            continue
        year_cell = row[0].strip()
        if year_cell:
            year = _year(year_cell)
        if row[2].strip():
            key_action = row[2].strip()
        metric = row[3].strip()
        if year is None or year < 2021 or year > 2026 or not key_action or not metric:
            continue
        is_percentage = metric.startswith("%")
        for sector, column in APPLICATION_SECTORS:
            raw_value = row[column].strip()
            if not raw_value:
                value = None
            elif is_percentage:
                value = parse_percent(raw_value)
            else:
                value = int(raw_value)
            results.append(
                {
                    "year": year,
                    "key_action": key_action,
                    "metric": metric,
                    "sector": sector,
                    "unit": "percent" if is_percentage else "projects",
                    "value": (
                        float(value) if is_percentage else int(value)
                    ) if value is not None else None,
                }
            )
    return results


def summarize_applications(results):
    totals = defaultdict(dict)
    for result in results:
        if result["sector"] == "Ukupno" and result["metric"] in ("Prijave", "Ugovoreni"):
            key = (result["year"], result["metric"])
            totals[key]["value"] = totals[key].get("value", 0) + (result["value"] or 0)
    summary = []
    years = sorted({year for year, _ in totals})
    for year in years:
        applications = totals.get((year, "Prijave"), {}).get("value", 0)
        contracted = totals.get((year, "Ugovoreni"), {}).get("value", 0)
        summary.append(
            {
                "year": year,
                "applications": applications,
                "contracted": contracted,
                "success_rate_percent": (
                    round(contracted / applications * 100, 2) if applications else None
                ),
            }
        )
    return summary


def _sum_eur(values):
    return _amount_number(sum((Decimal(str(value)) for value in values), Decimal("0")))


def build_outputs():
    projects = load_projects()
    institutions, registry_row_count = load_institutions()
    institutions_by_name = defaultdict(list)
    for institution in institutions:
        institutions_by_name[institution["normalized_name"]].append(institution)
    matches = [
        match_project(project, institutions, institutions_by_name)
        for project in projects
    ]
    institution_by_id = {item["institution_id"]: item for item in institutions}

    projects_by_recipient = defaultdict(list)
    matches_by_record = {item["record_id"]: item for item in matches}
    for project in projects:
        projects_by_recipient[project["beneficiary_key"]].append(project)

    beneficiaries = []
    for beneficiary_key, records in projects_by_recipient.items():
        record_matches = [matches_by_record[item["record_id"]] for item in records]
        linked_ids = {
            item["institution_id"] for item in record_matches if item["institution_id"]
        }
        beneficiaries.append(
            {
                "beneficiary_id": beneficiary_key,
                "name": records[0]["beneficiary_name"],
                "city": records[0]["city"],
                "project_count": len(records),
                "total_grant_eur": _sum_eur(item["grant_amount_eur"] for item in records),
                "years": sorted({item["year"] for item in records}),
                "sectors": sorted({item["sector"] for item in records}),
                "project_record_ids": [item["record_id"] for item in records],
                "matched_project_count": sum(
                    item["match_status"] == "matched_exact_name_and_city"
                    for item in record_matches
                ),
                "institution_ids": sorted(linked_ids),
            }
        )

    status_counts = Counter(item["match_status"] for item in matches)
    regional = defaultdict(lambda: {"project_count": 0, "total_grant_eur": Decimal("0"), "beneficiaries": set()})
    for project, match in zip(projects, matches):
        if not match["institution_id"]:
            continue
        institution = institution_by_id[match["institution_id"]]
        if not institution["county"]:
            continue
        bucket = regional[institution["county"]]
        bucket["project_count"] += 1
        bucket["total_grant_eur"] += Decimal(str(project["grant_amount_eur"]))
        bucket["beneficiaries"].add(project["beneficiary_key"])
    regional_summary = [
        {
            "county": county,
            "project_count": values["project_count"],
            "beneficiary_count": len(values["beneficiaries"]),
            "total_grant_eur": _amount_number(values["total_grant_eur"]),
        }
        for county, values in sorted(regional.items())
    ]

    projects_by_year = defaultdict(list)
    projects_by_sector = defaultdict(list)
    for project in projects:
        projects_by_year[project["year"]].append(project)
        projects_by_sector[project["sector"]].append(project)

    id_records = defaultdict(list)
    for project in projects:
        id_records[project["project_id"]].append(project)
    duplicate_project_ids = [
        {
            "project_id": project_id,
            "record_ids": [item["record_id"] for item in records],
            "beneficiaries": sorted({item["beneficiary_name"] for item in records}),
        }
        for project_id, records in sorted(id_records.items())
        if len(records) > 1
    ]
    conflicting_registry_counties = [
        {
            "institution_id": institution["institution_id"],
            "name": institution["name"],
            "county_candidates": institution["county_candidates"],
        }
        for institution in institutions
        if len(institution["county_candidates"]) > 1
    ]

    funding_results = load_funding_results()
    application_results = load_application_results()
    applications_by_year = summarize_applications(application_results)
    funding_totals_by_year = {
        result["year"]: result["value"]
        for result in funding_results
        if result["sector"] == "Ukupno" and result["measure"] == "Ugovoreno"
    }
    application_totals_by_year = {
        result["year"]: result["contracted"] for result in applications_by_year
    }
    source_reconciliation = []
    for year, year_projects in sorted(projects_by_year.items()):
        project_funding = _sum_eur(
            project["grant_amount_eur"] for project in year_projects
        )
        official_funding = funding_totals_by_year.get(year)
        official_project_count = application_totals_by_year.get(year)
        source_reconciliation.append(
            {
                "year": year,
                "project_list_count": len(year_projects),
                "applications_table_contracted_count": official_project_count,
                "project_count_difference": (
                    len(year_projects) - official_project_count
                    if official_project_count is not None
                    else None
                ),
                "project_list_grants_eur": project_funding,
                "funding_table_contracted_eur": official_funding,
                "grant_difference_eur": (
                    round(project_funding - official_funding, 2)
                    if official_funding is not None
                    else None
                ),
            }
        )
    data_quality = {
        "project_records": len(projects),
        "unique_project_ids": len(id_records),
        "duplicate_project_ids": duplicate_project_ids,
        "missing_source_update_date_count": sum(
            not project["source_updated_at"] for project in projects
        ),
        "project_source_update_dates": sorted(
            {project["source_updated_at"] for project in projects if project["source_updated_at"]}
        ),
        "registry_source_rows": registry_row_count,
        "deduplicated_institutions": len(institutions),
        "school_registry_missing_counties": sum(
            "school" in institution["registry_kinds"] and not institution["county"]
            for institution in institutions
        ),
        "conflicting_registry_counties": conflicting_registry_counties,
        "project_match_status_counts": dict(sorted(status_counts.items())),
        "project_matches_are_exact_name_and_city_only": True,
        "regional_summary_scope": (
            "Only projects matched by unique exact normalized beneficiary name and city "
            "to a school registry record with a county. This is not a complete regional "
            "distribution of all Erasmus+ projects."
        ),
        "source_reconciliation": source_reconciliation,
        "project_list_year_coverage": sorted(projects_by_year),
        "source_dates_may_differ": True,
    }
    dashboard_summary = {
        "project_count": len(projects),
        "unique_project_id_count": len(id_records),
        "beneficiary_count": len(beneficiaries),
        "institution_count": len(institutions),
        "total_grant_eur": _sum_eur(item["grant_amount_eur"] for item in projects),
        "exactly_matched_project_count": status_counts["matched_exact_name_and_city"],
        "projects_by_year": [
            {
                "year": year,
                "project_count": len(items),
                "total_grant_eur": _sum_eur(item["grant_amount_eur"] for item in items),
            }
            for year, items in sorted(projects_by_year.items())
        ],
        "projects_by_sector": [
            {
                "sector": sector,
                "project_count": len(items),
                "total_grant_eur": _sum_eur(item["grant_amount_eur"] for item in items),
            }
            for sector, items in sorted(projects_by_sector.items())
        ],
        "applications_by_year": applications_by_year,
        "regional_summary_scope": data_quality["regional_summary_scope"],
    }

    return {
        "projects": projects,
        "institutions": institutions,
        "project_institution_matches": matches,
        "beneficiaries": beneficiaries,
        "regional_summary": regional_summary,
        "funding_results": funding_results,
        "application_results": application_results,
        "dashboard_summary": dashboard_summary,
        "data_quality": data_quality,
    }


def _write_json(path, data):
    with path.open("w", encoding="utf-8", newline="\n") as destination:
        json.dump(data, destination, ensure_ascii=False, indent=2)
        destination.write("\n")


def _write_csv(path, rows):
    if not rows:
        raise ValueError(f"Refusing to write an empty CSV: {path.name}")
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    outputs = build_outputs()
    OUTPUT_DIR.mkdir(exist_ok=True)
    for name, data in outputs.items():
        _write_json(OUTPUT_DIR / f"{name}.json", data)
    _write_csv(OUTPUT_DIR / "projects.csv", outputs["projects"])
    _write_csv(
        OUTPUT_DIR / "project_institution_matches.csv",
        outputs["project_institution_matches"],
    )
    print(
        f"Prepared {len(outputs['projects'])} project rows and "
        f"{len(outputs['institutions'])} institutions in {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
