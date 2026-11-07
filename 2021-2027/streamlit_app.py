import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from app_helpers import filter_application_years, project_export_frame


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "processed"
COUNTY_GEOJSON_PATH = APP_DIR / "geo" / "croatia-counties.geojson"
COUNTY_GEO_ID = {
    "Bjelovarsko-bilogorska županija": "bjelovar-bilogora",
    "Brodsko-posavska županija": "brod-posavina",
    "Dubrovačko-neretvanska županija": "dubrovnik-neretva",
    "Grad Zagreb županija": "zagreb-city",
    "Istarska županija": "istria",
    "Karlovačka županija": "karlovac",
    "Koprivničko-križevačka županija": "koprivnica-krizevci",
    "Krapinsko-zagorska županija": "krapina-zagorje",
    "Ličko-senjska županija": "lika-senj",
    "Međimurska županija": "medimurje",
    "Osječko-baranjska županija": "osijek-baranja",
    "Požeško-slavonska županija": "pozega-slavonia",
    "Primorsko-goranska županija": "primorje-gorski-kotar",
    "Sisačko-moslavačka županija": "sisak-moslavina",
    "Splitsko-dalmatinska županija": "split-dalmatia",
    "Varaždinska županija": "varazdin",
    "Virovitičko-podravska županija": "virovitica-podravina",
    "Vukovarsko-srijemska županija": "vukovar-srijem",
    "Zadarska županija": "zadar",
    "Zagrebačka županija": "zagreb-county",
    "Šibensko-kninska županija": "sibenik-knin",
}
DATA_FILES = (
    "projects.json",
    "institutions.json",
    "project_institution_matches.json",
    "beneficiaries.json",
    "regional_summary.json",
    "funding_results.json",
    "application_results.json",
    "dashboard_summary.json",
    "data_quality.json",
)

st.set_page_config(
    page_title="Erasmus+ Explorer RH",
    page_icon=":material/explore:",
    layout="wide",
)


@st.cache_data(ttl="15m", max_entries=2)
def load_processed_data(file_fingerprint):
    del file_fingerprint
    result = {}
    for filename in DATA_FILES:
        with (DATA_DIR / filename).open(encoding="utf-8") as source:
            result[filename.removesuffix(".json")] = json.load(source)
    return result


@st.cache_data(ttl="1d", max_entries=1)
def load_county_geojson(file_fingerprint):
    del file_fingerprint
    with COUNTY_GEOJSON_PATH.open(encoding="utf-8") as source:
        return json.load(source)


def euro(value):
    if value is None:
        return "—"
    return f"{value:,.2f} €".replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")


def percent(value):
    return "—" if value is None else f"{value:.2f} %".replace(".", ",")


def format_table(frame, amount_columns=()):
    frame = frame.copy()
    for column in amount_columns:
        if column in frame:
            frame[column] = frame[column].map(euro)
    return frame


def filter_projects(projects, selected_years, selected_sectors):
    return [
        project
        for project in projects
        if project["year"] in selected_years and project["sector"] in selected_sectors
    ]


def aggregate_recipients(projects):
    grouped = defaultdict(
        lambda: {
            "beneficiary_key": "",
            "beneficiary_name": "",
            "city": "",
            "project_count": 0,
            "grant_amount_eur": 0.0,
        }
    )
    for project in projects:
        row = grouped[project["beneficiary_key"]]
        row["beneficiary_key"] = project["beneficiary_key"]
        row["beneficiary_name"] = project["beneficiary_name"]
        row["city"] = project["city"]
        row["project_count"] += 1
        row["grant_amount_eur"] += project["grant_amount_eur"]
    return sorted(
        grouped.values(),
        key=lambda item: (-item["grant_amount_eur"], item["beneficiary_name"]),
    )


def render_overview(data, projects, matches_by_record):
    st.title("Erasmus+ Explorer RH")
    st.caption(
        "Istražite financirane projekte, korisnike i regionalnu zastupljenost "
        "na temelju dostupnih podataka za Hrvatsku."
    )

    exactly_matched = sum(
        matches_by_record[project["record_id"]]["match_status"]
        == "matched_exact_name_and_city"
        for project in projects
    )
    total_grants = sum(project["grant_amount_eur"] for project in projects)
    recipients = aggregate_recipients(projects)
    with st.container(horizontal=True):
        st.metric("Financirani projekti", f"{len(projects):,}".replace(",", "."),
                  border=True)
        st.metric("Korisnici", f"{len(recipients):,}".replace(",", "."),
                  border=True)
        st.metric("Odobrena sredstva", euro(total_grants), border=True)
        st.metric(
            "Pouzdano povezani zapisi",
            f"{exactly_matched:,}".replace(",", "."),
            border=True,
        )

    st.info(
        "Broj projekata i financiranje odnose se na dostupni popis za 2024.–2026. "
        "Podaci za ranije godine dostupni su samo kao agregati prijava i financija."
    )

    yearly = defaultdict(lambda: {"project_count": 0, "grant_amount_eur": 0.0})
    sector_totals = defaultdict(lambda: {"project_count": 0, "grant_amount_eur": 0.0})
    for project in projects:
        yearly[project["year"]]["project_count"] += 1
        yearly[project["year"]]["grant_amount_eur"] += project["grant_amount_eur"]
        sector_totals[project["sector"]]["project_count"] += 1
        sector_totals[project["sector"]]["grant_amount_eur"] += project["grant_amount_eur"]

    left, right = st.columns(2)
    with left:
        st.subheader("Projekti po godini")
        yearly_frame = pd.DataFrame(
            [
                {"Godina": year, "Broj projekata": values["project_count"]}
                for year, values in sorted(yearly.items())
            ]
        )
        if not yearly_frame.empty:
            st.bar_chart(yearly_frame, x="Godina", y="Broj projekata")
    with right:
        st.subheader("Odobrena sredstva po sektoru")
        sector_frame = pd.DataFrame(
            [
                {"Sektor": sector, "Odobreno (EUR)": values["grant_amount_eur"]}
                for sector, values in sorted(
                    sector_totals.items(),
                    key=lambda item: item[1]["grant_amount_eur"],
                    reverse=True,
                )
            ]
        )
        if not sector_frame.empty:
            st.bar_chart(
                sector_frame,
                x="Sektor",
                y="Odobreno (EUR)",
                horizontal=True,
            )

    st.subheader("Prijave i ugovoreni projekti")
    application_rows = filter_application_years(
        data["dashboard_summary"]["applications_by_year"],
        st.session_state["selected_aggregate_years"],
    )
    if application_rows:
        application_frame = pd.DataFrame(
            [
                {
                    "Godina": row["year"],
                    "Prijave": row["applications"],
                    "Ugovoreni": row["contracted"],
                }
                for row in application_rows
            ]
        ).set_index("Godina")
        st.bar_chart(application_frame)
        st.caption(
            "Agregatni podaci iz tablice 9 uključuju sve sektore i nisu ograničeni "
            "filtrom sektora u bočnoj traci."
        )
    else:
        st.info("Za odabrane godine nema agregatnih podataka o prijavama.")

    duplicate_count = len(data["data_quality"]["duplicate_project_ids"])
    if duplicate_count:
        st.warning(
            f"Izvor sadrži {duplicate_count} ponovljeni projektni broj uz različite "
            "korisnike. Redci su sačuvani; pojedinosti su na stranici Kvaliteta podataka."
        )


def render_regions(projects, matches_by_record, institutions_by_id, county_geojson):
    st.title("Regionalna zastupljenost")
    st.caption(
        "Prikaz uključuje samo projekte povezane sa školskim registrom i županijom. "
        "Ne predstavlja potpunu raspodjelu svih Erasmus+ projekata."
    )

    rows = []
    for project in projects:
        match = matches_by_record[project["record_id"]]
        if match["match_status"] != "matched_exact_name_and_city":
            continue
        institution = institutions_by_id[match["institution_id"]]
        if not institution["county"]:
            continue
        rows.append(
            {
                **project,
                "county": institution["county"],
                "institution_id": institution["institution_id"],
            }
        )

    if not rows:
        st.info("Nema regionalno povezanih projekata za odabrane filtre.")
        return

    by_county = defaultdict(
        lambda: {"project_count": 0, "grant_amount_eur": 0.0, "beneficiaries": set()}
    )
    for row in rows:
        summary = by_county[row["county"]]
        summary["project_count"] += 1
        summary["grant_amount_eur"] += row["grant_amount_eur"]
        summary["beneficiaries"].add(row["beneficiary_key"])

    metric_options = {
        "Broj projekata": "project_count",
        "Broj korisnika": "beneficiary_count",
        "Odobrena sredstva (EUR)": "grant_amount_eur",
    }
    selected_metric = st.selectbox("Pokazatelj na karti", list(metric_options))
    county_rows = []
    for county, county_id in COUNTY_GEO_ID.items():
        values = by_county.get(county)
        county_rows.append(
            {
                "Županija": county,
                "county_id": county_id,
                "Broj projekata": values["project_count"] if values else None,
                "Broj korisnika": len(values["beneficiaries"]) if values else None,
                "Odobrena sredstva (EUR)": (
                    values["grant_amount_eur"] if values else None
                ),
            }
        )
    county_frame = pd.DataFrame(county_rows)
    map_frame = county_frame.dropna(subset=[selected_metric])
    if map_frame.empty:
        st.info("Nema regionalno povezanih podataka za izradu karte.")
        return
    figure = px.choropleth(
        county_frame,
        geojson=county_geojson,
        locations="county_id",
        featureidkey="properties.county_id",
        color=selected_metric,
        hover_name="Županija",
        hover_data={
            "county_id": False,
            "Broj projekata": ":,.0f",
            "Broj korisnika": ":,.0f",
            "Odobrena sredstva (EUR)": ":,.2f",
        },
        color_continuous_scale="Blues",
        labels={selected_metric: selected_metric},
    )
    figure.update_geos(
        fitbounds="locations",
        visible=False,
        projection_type="mercator",
        showland=True,
        landcolor="#F3F6FA",
        showcountries=False,
    )
    figure.update_traces(marker_line_color="white", marker_line_width=0.8)
    figure.update_layout(
        height=620,
        margin={"l": 0, "r": 0, "t": 15, "b": 0},
        coloraxis_colorbar={"title": selected_metric},
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
    st.caption(
        "Siva područja bez ispune označavaju županije bez projekta pouzdano povezanog "
        "s dostupnim školskim registrom, a ne nužno županije bez Erasmus+ projekata. "
        "Granice: Natural Earth (public domain), lokalno pripremljen GeoJSON."
    )
    county_rows.sort(key=lambda row: row["Broj projekata"] or 0, reverse=True)
    county_frame = pd.DataFrame(county_rows)
    county_frame = county_frame.drop(columns=["county_id"])
    st.dataframe(
        format_table(county_frame, ("Odobrena sredstva (EUR)",)),
        hide_index=True,
    )

    selected_county = st.selectbox(
        "Odaberite županiju za pregled projekata",
        ["Sve županije", *[row["Županija"] for row in county_rows]],
    )
    if selected_county != "Sve županije":
        rows = [row for row in rows if row["county"] == selected_county]

    details = pd.DataFrame(
        [
            {
                "Županija": row["county"],
                "Godina": row["year"],
                "Korisnik": row["beneficiary_name"],
                "Mjesto": row["city"],
                "Sektor": row["sector"],
                "Projektni broj": row["project_id"],
                "Odobreno (EUR)": row["grant_amount_eur"],
            }
            for row in rows
        ]
    )
    st.subheader("Povezani projekti")
    st.dataframe(format_table(details, ("Odobreno (EUR)",)), hide_index=True)


def render_beneficiaries(projects, matches_by_record, institutions_by_id):
    st.title("Pretraga korisnika i profili")
    st.caption(
        "Profili se temelje na nazivu korisnika i mjestu iz popisa projekata. "
        "Povezivanje s registrom prikazuje se odvojeno i samo kada je podudaranje sigurno."
    )
    recipients = aggregate_recipients(projects)
    if not recipients:
        st.info("Nema korisnika za odabrane filtre.")
        return

    query = st.text_input("Pretražite naziv korisnika ili mjesto")
    query_normalized = query.casefold().strip()
    options = [
        row
        for row in recipients
        if query_normalized in row["beneficiary_name"].casefold()
        or query_normalized in row["city"].casefold()
    ]
    if not options:
        st.info("Nema korisnika koji odgovaraju pretrazi.")
        return

    labels = {
        f"{row['beneficiary_name']} — {row['city']} ({row['project_count']} projekta)": row
        for row in options
    }
    selected_label = st.selectbox("Odaberite korisnika", list(labels))
    selected = labels[selected_label]
    beneficiary_projects = [
        project
        for project in projects
        if project["beneficiary_key"] == selected["beneficiary_key"]
    ]

    total_grants = sum(row["grant_amount_eur"] for row in beneficiary_projects)
    years = sorted({row["year"] for row in beneficiary_projects})
    with st.container(horizontal=True):
        st.metric("Projekti", len(beneficiary_projects), border=True)
        st.metric("Ukupno odobreno", euro(total_grants), border=True)
        st.metric("Godine sudjelovanja", ", ".join(map(str, years)), border=True)

    linked_institution_ids = {
        matches_by_record[row["record_id"]]["institution_id"]
        for row in beneficiary_projects
        if matches_by_record[row["record_id"]]["institution_id"]
    }
    if linked_institution_ids:
        st.subheader("Povezani zapisi u registru")
        linked_records = [
            {
                "Naziv ustanove": institutions_by_id[item]["name"],
                "Mjesto": institutions_by_id[item]["city"],
                "Županija": institutions_by_id[item]["county"],
                "Vrsta registra": ", ".join(institutions_by_id[item]["registry_kinds"]),
                "ID ustanove": item,
            }
            for item in sorted(linked_institution_ids)
        ]
        st.dataframe(pd.DataFrame(linked_records), hide_index=True)
    else:
        st.info(
            "Za ovog korisnika nije pronađena jedinstvena podudarnost u dostupnim "
            "registrima. To ne znači da korisnik nije obrazovna ustanova."
        )

    st.subheader("Projekti korisnika")
    project_rows = [
        {
            "Godina": row["year"],
            "Sektor": row["sector"],
            "Ključna aktivnost": row["key_action"],
            "Tip aktivnosti": row["activity_type"],
            "Projektni broj": row["project_id"],
            "Mjesto": row["city"],
            "Odobreno (EUR)": row["grant_amount_eur"],
        }
        for row in beneficiary_projects
    ]
    st.dataframe(
        format_table(pd.DataFrame(project_rows), ("Odobreno (EUR)",)),
        hide_index=True,
    )

    yearly = defaultdict(float)
    for row in beneficiary_projects:
        yearly[row["year"]] += row["grant_amount_eur"]
    yearly_frame = pd.DataFrame(
        [
            {"Godina": year, "Odobreno (EUR)": amount}
            for year, amount in sorted(yearly.items())
        ]
    )
    if len(yearly_frame) > 1:
        st.subheader("Financiranje kroz godine")
        st.bar_chart(yearly_frame, x="Godina", y="Odobreno (EUR)")


def render_concentration(projects):
    st.title("Koncentracija financiranja")
    st.caption(
        "Udio se računa na temelju odobrenih iznosa u odabranim projektima i filtrima. "
        "Korisnik je grupiran prema normaliziranom nazivu i mjestu."
    )
    recipients = aggregate_recipients(projects)
    if not recipients:
        st.info("Nema projekata za odabrane filtre.")
        return

    total_funding = sum(row["grant_amount_eur"] for row in recipients)
    top_10_amount = sum(row["grant_amount_eur"] for row in recipients[:10])
    top_20_amount = sum(row["grant_amount_eur"] for row in recipients[:20])
    repeat_recipients = sum(row["project_count"] > 1 for row in recipients)
    with st.container(horizontal=True):
        st.metric("Korisnici", len(recipients), border=True)
        st.metric("S 2+ projekata", repeat_recipients, border=True)
        st.metric(
            "Udio top 10 korisnika",
            percent(top_10_amount / total_funding * 100 if total_funding else None),
            border=True,
        )
        st.metric(
            "Udio top 20 korisnika",
            percent(top_20_amount / total_funding * 100 if total_funding else None),
            border=True,
        )

    top_count = st.slider(
        "Broj korisnika na grafikonu",
        min_value=1,
        max_value=min(30, len(recipients)),
        value=min(10, len(recipients)),
    )
    top_frame = pd.DataFrame(
        [
            {
                "Korisnik": f"{row['beneficiary_name']} — {row['city']}",
                "Odobreno (EUR)": row["grant_amount_eur"],
            }
            for row in recipients[:top_count]
        ]
    )
    st.bar_chart(top_frame, x="Korisnik", y="Odobreno (EUR)", horizontal=True)

    table = pd.DataFrame(
        [
            {
                "Korisnik": row["beneficiary_name"],
                "Mjesto": row["city"],
                "Broj projekata": row["project_count"],
                "Odobreno (EUR)": row["grant_amount_eur"],
                "Udio (%)": (
                    row["grant_amount_eur"] / total_funding * 100
                    if total_funding
                    else 0
                ),
            }
            for row in recipients[:top_count]
        ]
    )
    st.dataframe(
        format_table(table, ("Odobreno (EUR)",)),
        hide_index=True,
        column_config={
            "Udio (%)": st.column_config.NumberColumn("Udio (%)", format="%.2f %%")
        },
    )


def render_projects(projects):
    st.title("Popis projekata")
    st.caption(
        "Filtrirajte, pretražite i preuzmite projektne zapise korištene u analizama."
    )
    query = st.text_input("Pretražite korisnika, mjesto ili projektni broj")
    normalized_query = query.casefold().strip()
    filtered = [
        row
        for row in projects
        if normalized_query in row["beneficiary_name"].casefold()
        or normalized_query in row["city"].casefold()
        or normalized_query in row["project_id"].casefold()
    ]
    export_frame = project_export_frame(filtered)
    st.write(f"Prikazano zapisa: {len(export_frame):,}".replace(",", "."))
    st.dataframe(
        format_table(export_frame, ("Odobreno (EUR)",)),
        hide_index=True,
    )
    st.download_button(
        "Preuzmi filtrirane projekte (CSV)",
        data=export_frame.to_csv(index=False).encode("utf-8-sig"),
        file_name="erasmus_projekti.csv",
        mime="text/csv",
    )


def render_data_quality(data):
    st.title("Kvaliteta i metodologija")
    quality = data["data_quality"]

    st.subheader("Opseg podataka")
    st.write(
        f"Popis sadrži **{quality['project_records']:,}** projektnih redaka i "
        f"**{quality['unique_project_ids']:,}** jedinstvenih projektnih brojeva. "
        f"Popis pokriva godine: "
        f"{', '.join(map(str, quality['project_list_year_coverage']))}."
    )
    st.write(
        f"Pripremljeno je **{quality['registry_source_rows']:,}** izvornih redaka "
        f"registara, konsolidiranih u **{quality['deduplicated_institutions']:,}** "
        "zapisa ustanova."
    )
    st.write(
        f"U popisu nedostaje datum ažuriranja za "
        f"**{quality['missing_source_update_date_count']}** projekata. "
        f"Poznati datumi: {', '.join(quality['project_source_update_dates'])}."
    )

    st.subheader("Povezivanje s registrima")
    status_counts = quality["project_match_status_counts"]
    match_frame = pd.DataFrame(
        [
            {"Status": "Jedinstveni naziv i mjesto", "Zapisa": status_counts.get("matched_exact_name_and_city", 0)},
            {"Status": "Razlika u mjestu", "Zapisa": status_counts.get("location_mismatch", 0)},
            {"Status": "Bez kandidata", "Zapisa": status_counts.get("unmatched", 0)},
            {"Status": "Nejasno podudaranje", "Zapisa": status_counts.get("ambiguous_exact_name_and_city", 0)},
        ]
    )
    st.bar_chart(match_frame, x="Status", y="Zapisa")
    st.caption(
        "Automatsko povezivanje koristi normalizirani naziv i mjesto. Nema automatskog "
        "fuzzy povezivanja. Regionalni sažetak koristi samo sigurno povezane zapise "
        "škola s upisanom županijom."
    )
    st.write(
        f"Školskih zapisa bez županije: "
        f"**{quality['school_registry_missing_counties']}**. "
        f"Zapisa s proturječnim županijama u izvorima: "
        f"**{len(quality['conflicting_registry_counties'])}**."
    )
    if quality["conflicting_registry_counties"]:
        conflict_frame = pd.DataFrame(
            [
                {
                    "Ustanova": row["name"],
                    "Pronađene županije": ", ".join(row["county_candidates"]),
                    "ID ustanove": row["institution_id"],
                }
                for row in quality["conflicting_registry_counties"]
            ]
        )
        st.warning(
            "Proturječne županije nisu automatski odabrane; ti zapisi nisu uključeni "
            "u županijsku kartu."
        )
        st.dataframe(conflict_frame, hide_index=True)

    st.subheader("Usporedba izvora")
    reconciliation = pd.DataFrame(quality["source_reconciliation"])
    reconciliation = reconciliation.rename(
        columns={
            "year": "Godina",
            "project_list_count": "Projekti u popisu",
            "applications_table_contracted_count": "Ugovoreni u agregatu",
            "project_count_difference": "Razlika broja",
            "project_list_grants_eur": "Iznosi popisa (EUR)",
            "funding_table_contracted_eur": "Ugovoreno u agregatu (EUR)",
            "grant_difference_eur": "Razlika iznosa (EUR)",
        }
    )
    st.dataframe(
        format_table(
            reconciliation,
            ("Iznosi popisa (EUR)", "Ugovoreno u agregatu (EUR)", "Razlika iznosa (EUR)"),
        ),
        hide_index=True,
    )
    st.caption(
        "Izvorne tablice imaju različite datume ažuriranja. Prikazane razlike su "
        "upozorenja za provjeru, ne automatski razlog za odbacivanje podataka."
    )

    duplicates = quality["duplicate_project_ids"]
    st.subheader("Ponovljeni projektni brojevi")
    if duplicates:
        duplicate_frame = pd.DataFrame(
            [
                {
                    "Projektni broj": item["project_id"],
                    "Korisnici u izvornim redcima": ", ".join(item["beneficiaries"]),
                    "ID-jevi redaka": ", ".join(item["record_ids"]),
                }
                for item in duplicates
            ]
        )
        st.warning(
            "Ponovljeni brojevi nisu uklonjeni jer se zapisi razlikuju po korisniku. "
            "Provjerite izvor prije zaključivanja o konačnom broju projekata."
        )
        st.dataframe(duplicate_frame, hide_index=True)
    else:
        st.success("Nema ponovljenih projektnih brojeva.")

    st.subheader("Preuzimanje podataka za daljnju obradu")
    dataset_options = {
        "Projekti (JSON)": "projects",
        "Korisnici (JSON)": "beneficiaries",
        "Ustanove (JSON)": "institutions",
        "Povezivanje projekata i ustanova (JSON)": "project_institution_matches",
        "Regionalni sažetak (JSON)": "regional_summary",
        "Financije po godini i sektoru (JSON)": "funding_results",
        "Prijave i ugovaranja (JSON)": "application_results",
        "Sažeti pokazatelji (JSON)": "dashboard_summary",
    }
    selection = st.selectbox("Skup podataka", list(dataset_options))
    payload = json.dumps(
        data[dataset_options[selection]],
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    st.download_button(
        "Preuzmi JSON",
        data=payload,
        file_name=f"{dataset_options[selection]}.json",
        mime="application/json",
    )


missing_files = [filename for filename in DATA_FILES if not (DATA_DIR / filename).is_file()]
if missing_files:
    st.title("Erasmus+ Explorer RH")
    st.error(
        "Nedostaju pripremljene datoteke: "
        + ", ".join(missing_files)
        + ". Najprije pokrenite pripremu podataka."
    )
    st.code("python .\\2021-2027\\prepare_data.py", language="powershell")
    st.stop()

file_fingerprint = tuple(
    (filename, (DATA_DIR / filename).stat().st_mtime_ns, (DATA_DIR / filename).stat().st_size)
    for filename in DATA_FILES
)
data = load_processed_data(file_fingerprint)

projects = data["projects"]
project_years = sorted({project["year"] for project in projects})
aggregate_years = sorted(
    row["year"] for row in data["dashboard_summary"]["applications_by_year"]
)
sectors = sorted({project["sector"] for project in projects})
matches_by_record = {
    item["record_id"]: item for item in data["project_institution_matches"]
}
institutions_by_id = {
    item["institution_id"]: item for item in data["institutions"]
}

with st.sidebar:
    st.title("Erasmus+ Explorer RH")
    page = st.selectbox(
        "Odaberite prikaz",
        [
            "Pregled",
            "Regije",
            "Korisnici i ustanove",
            "Koncentracija financiranja",
            "Projekti",
            "Kvaliteta podataka",
        ],
    )
    st.divider()
    st.subheader("Filtri projekata")
    selected_years = st.multiselect(
        "Godine projekata",
        project_years,
        default=project_years,
        key="selected_years",
    )
    selected_sectors = st.multiselect(
        "Sektori projekata", sectors, default=sectors, key="selected_sectors"
    )
    st.multiselect(
        "Godine agregata prijava",
        aggregate_years,
        default=aggregate_years,
        key="selected_aggregate_years",
    )
    st.caption(
        "Popis projekata dostupan je za 2024.–2026.; agregati prijava za 2021.–2026."
    )
    st.divider()
    st.caption(
        f"{len(projects):,} projektnih redaka · "
        f"{data['dashboard_summary']['institution_count']:,} zapisa ustanova".replace(",", ".")
    )

filtered_projects = filter_projects(projects, selected_years, selected_sectors)

if page == "Pregled":
    render_overview(data, filtered_projects, matches_by_record)
elif page == "Regije":
    if not COUNTY_GEOJSON_PATH.is_file():
        st.error(f"Nedostaje lokalna GeoJSON karta: {COUNTY_GEOJSON_PATH}")
        st.stop()
    geojson_fingerprint = (
        COUNTY_GEOJSON_PATH.stat().st_mtime_ns,
        COUNTY_GEOJSON_PATH.stat().st_size,
    )
    county_geojson = load_county_geojson(geojson_fingerprint)
    render_regions(
        filtered_projects,
        matches_by_record,
        institutions_by_id,
        county_geojson,
    )
elif page == "Korisnici i ustanove":
    render_beneficiaries(filtered_projects, matches_by_record, institutions_by_id)
elif page == "Koncentracija financiranja":
    render_concentration(filtered_projects)
elif page == "Projekti":
    render_projects(filtered_projects)
else:
    render_data_quality(data)
