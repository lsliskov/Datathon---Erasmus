import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from app_helpers import (
    filter_application_years,
    compare_similar_institutions,
    institution_category,
    project_export_frame,
    summarize_institution_types,
    summarize_regional_coverage,
)


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
    "study_program_summary.json",
    "funding_results.json",
    "application_results.json",
    "dashboard_summary.json",
    "data_quality.json",
    "study_programs.json",
    "study_program_summary.json",
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


def horizontal_bar_figure(
    frame, category_column, value_column, value_label, value_format, suffix=""
):
    figure = px.bar(
        frame,
        x=value_column,
        y=category_column,
        orientation="h",
        category_orders={
            category_column: frame.sort_values(value_column)[category_column].tolist()
        },
        labels={category_column: "", value_column: value_label},
    )
    figure.update_traces(
        hovertemplate=(
            f"<b>%{{y}}</b><br>{value_label}: "
            f"%{{x:{value_format}}}{suffix}<extra></extra>"
        ),
        cliponaxis=False,
    )
    figure.update_layout(
        height=max(360, 46 * len(frame) + 100),
        margin={"l": 260, "r": 30, "t": 25, "b": 55},
        yaxis={"automargin": True, "title": None},
        xaxis={"title": value_label},
        hoverlabel={"align": "left"},
    )
    return figure


def render_page_context(text):
    st.markdown(text)


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
    render_page_context(
        "Ova stranica povezuje tri pogleda na program: koliko je projekata "
        "financirano, kako se odobrena sredstva razlikuju među sektorima te "
        "koliko je prijava završilo ugovaranjem. Prva dva prikaza temelje se "
        "na pojedinačnim projektima za 2024.–2026.; bočni filtri za godine i "
        "sektore mijenjaju te rezultate i ostale projektne stranice. Prijave "
        "i ugovoreni projekti dolaze iz zasebnog godišnjeg agregata za "
        "2021.–2026. i imaju vlastiti filtar godina."
    )

    linked_project_count = sum(
        bool(matches_by_record[project["record_id"]]["institution_id"])
        for project in projects
    )
    total_grants = sum(project["grant_amount_eur"] for project in projects)
    recipients = aggregate_recipients(projects)
    with st.container(horizontal=True):
        st.metric(
            "Projektni zapisi",
            f"{len(projects):,}".replace(",", "."),
            border=True,
        )
        st.metric(
            "Korisnici projektnog popisa",
            f"{len(recipients):,}".replace(",", "."),
            border=True,
        )
        st.metric(
            "Odobreno (odabrani projekti)",
            euro(total_grants),
            border=True,
        )
        st.metric(
            "Pouzdano povezani zapisi",
            f"{linked_project_count:,}".replace(",", "."),
            border=True,
        )
    st.caption(
        "„Korisnik” je ovdje jedinstvena kombinacija naziva i mjesta, a ne "
        "provjereni broj pravnih osoba. Povezani zapisi su oni za koje je "
        "pronađena sigurna veza s dostupnim registrom obrazovnih ustanova."
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
        st.caption(
            "Svaki stupac broji retke financiranih projekata iz odabranih "
            "godina i sektora. Više zapisa može imati isti projektni broj."
        )
        yearly_frame = pd.DataFrame(
            [
                {"Godina": year, "Broj projekata": values["project_count"]}
                for year, values in sorted(yearly.items())
            ]
        )
        if not yearly_frame.empty:
            st.bar_chart(
                yearly_frame,
                x="Godina",
                y="Broj projekata",
                alt="Broj financiranih projektnih zapisa po godini",
            )
    with right:
        st.subheader("Odobrena sredstva po sektoru")
        st.caption(
            "Ovdje je zbrojen odobreni iznos iz istih filtriranih projektnih "
            "redaka; usporedite visinu sredstava, a ne broj ustanova."
        )
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
                alt="Odobrena sredstva po sektoru",
            )

    st.subheader("Prijave i ugovoreni projekti")
    st.caption(
        "Ovaj grafikon uspoređuje ukupan broj zaprimljenih prijava s brojem "
        "ugovorenih projekata po godini. Razlika pokazuje koliko prijava nije "
        "završilo ugovaranjem, ali nije prikaz uspjeha pojedine ustanove."
    )
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
        st.bar_chart(
            application_frame,
            alt="Broj Erasmus+ prijava i ugovorenih projekata po godini",
        )
        st.caption(
            "Agregatni podaci iz tablice 9 uključuju sve sektore i nisu ograničeni "
            "filtrom sektora u bočnoj traci."
        )
    else:
        st.caption("Za odabrane godine nema agregatnih podataka o prijavama.")

    duplicate_count = len(data["data_quality"]["duplicate_project_ids"])
    if duplicate_count:
        st.warning(
            f"Izvor sadrži {duplicate_count} ponovljeni projektni broj uz različite "
            "korisnike. Redci su sačuvani; pojedinosti su na stranici Kvaliteta podataka."
        )


def render_regions(
    projects,
    matches_by_record,
    institutions_by_id,
    institutions,
    study_program_summary,
    county_geojson,
):
    st.title("Regionalna zastupljenost")
    render_page_context(
        "Broj projekata i iznosi uključuju sigurno povezane škole, dječje vrtiće "
        "i visoka učilišta s poznatom županijom. Mjesto u projektnom popisu je "
        "mjesto korisnika, ne mjesto provedbe aktivnosti; regionalna županija "
        "uzima se iz registra ustanove. Filtri godina i sektora mijenjaju projektne "
        "pokazatelje, ali ne i registarski nazivnik. Studijski programi su zaseban "
        "kontekst ponude obrazovanja, nisu Erasmus+ projekti i ne prate te filtre."
    )

    rows = []
    for project in projects:
        match = matches_by_record[project["record_id"]]
        if not match["institution_id"]:
            continue
        institution = institutions_by_id[match["institution_id"]]
        if not institution["county"]:
            continue
        rows.append(
            {
                **project,
                "county": institution["county"],
                "institution_id": institution["institution_id"],
                "registry_kinds": institution["registry_kinds"],
            }
        )

    if not rows:
        st.warning(
            "Za ove filtre nema pouzdano povezanih projekata obrazovnih ustanova. "
            "Karta i dalje prikazuje ustanove u registru te nulte vrijednosti "
            "povezanih projektnih pokazatelja."
        )

    county_summaries = summarize_regional_coverage(
        projects, matches_by_record, institutions_by_id, institutions
    )
    summaries_by_county = {
        row["Županija"]: row for row in county_summaries
    }
    programs_by_county = {
        row["Županija"]: row for row in study_program_summary
    }

    metric_options = {
        "Projektni zapisi": "Projektni zapisi",
        "Jedinstveni projektni brojevi": "Jedinstveni projektni brojevi",
        "Registrirane školske ustanove": "Registrirane školske ustanove",
        "Registrirana visoka učilišta": "Registrirana visoka učilišta",
        "Registrirani dječji vrtići": "Registrirani dječji vrtići",
        "Registrirane obrazovne ustanove": "Registrirane obrazovne ustanove",
        "Ustanove s povezanim projektom": "Ustanove s povezanim projektom",
        "Udio obrazovnih ustanova s projektom (%)": (
            "Udio obrazovnih ustanova s projektom (%)"
        ),
        "Zapisi studijskih programa": "Zapisi studijskih programa",
        "Odobreno (EUR)": "Odobreno (EUR)",
    }
    selected_metric_label = st.selectbox(
        "Pokazatelj na karti",
        list(metric_options),
    )
    st.caption(
        "Odaberite što želite usporediti po županijama. Tamnija boja znači "
        "veću vrijednost odabranog pokazatelja; prelaskom preko županije "
        "možete vidjeti i ostale vrijednosti. Projektni pokazatelji mijenjaju "
        "se s bočnim filtrima, dok se broj ustanova u registru ne mijenja."
    )
    selected_metric = metric_options[selected_metric_label]
    county_rows = []
    for county, county_id in COUNTY_GEO_ID.items():
        values = summaries_by_county.get(county, {})
        program_values = programs_by_county.get(county, {})
        county_rows.append(
            {
                "Županija": county,
                "county_id": county_id,
                "Registrirane školske ustanove": values.get(
                    "Registrirane školske ustanove", 0
                ),
                "Registrirana visoka učilišta": values.get(
                    "Registrirana visoka učilišta", 0
                ),
                "Registrirani dječji vrtići": values.get(
                    "Registrirani dječji vrtići", 0
                ),
                "Registrirane obrazovne ustanove": values.get(
                    "Registrirane obrazovne ustanove", 0
                ),
                "Ustanove s povezanim projektom": values.get(
                    "Ustanove s povezanim projektom", 0
                ),
                "Udio obrazovnih ustanova s projektom (%)": values.get(
                    "Udio ustanova s povezanim projektom (%)", 0
                ),
                "Korisnici": values.get("Korisnici", 0),
                "Projektni zapisi": values.get("Projektni zapisi", 0),
                "Jedinstveni projektni brojevi": values.get(
                    "Jedinstveni projektni brojevi", 0
                ),
                "Zapisi studijskih programa": program_values.get(
                    "Zapisi studijskih programa", 0
                ),
                "Izvoditelji programa": program_values.get(
                    "Izvoditelji programa", 0
                ),
                "Odobreno (EUR)": values.get("Odobreno (EUR)", 0),
            }
        )
    county_frame = pd.DataFrame(county_rows)
    figure = px.choropleth(
        county_frame,
        geojson=county_geojson,
        locations="county_id",
        featureidkey="properties.county_id",
        color=selected_metric,
        hover_name="Županija",
        hover_data={
            "county_id": False,
            "Registrirane školske ustanove": ":,.0f",
            "Registrirana visoka učilišta": ":,.0f",
            "Registrirani dječji vrtići": ":,.0f",
            "Registrirane obrazovne ustanove": ":,.0f",
            "Ustanove s povezanim projektom": ":,.0f",
            "Udio obrazovnih ustanova s projektom (%)": ":,.2f",
            "Korisnici": ":,.0f",
            "Projektni zapisi": ":,.0f",
            "Jedinstveni projektni brojevi": ":,.0f",
            "Zapisi studijskih programa": ":,.0f",
            "Izvoditelji programa": ":,.0f",
            "Odobreno (EUR)": ":,.2f",
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
    st.plotly_chart(
        figure,
        width="stretch",
        config={"displayModeBar": False},
        alt=f"Karta hrvatskih županija: {selected_metric}",
    )
    st.caption(
        "Karta obuhvaća samo projekte sigurno povezane sa školama, vrtićima "
        "i visokim učilištima. Prazna ili svjetlija županija ne znači da ondje "
        "nema projekata: dio korisnika nije moguće povezati s ovim registrima. "
        "Udio ustanova s projektom nije stopa prijava niti mjera dostupnosti "
        "programa. Granice su lokalno pripremljene iz podataka Natural Earth."
    )
    county_rows.sort(
        key=lambda row: row["Projektni zapisi"] or 0,
        reverse=True,
    )
    county_frame = pd.DataFrame(county_rows)
    county_frame = county_frame.drop(columns=["county_id"])
    st.caption(
        "Tablica ispod karte daje točne vrijednosti za svaku županiju. "
        "„Registrirane obrazovne ustanove” čine usporednu osnovu, a "
        "„ustanove s povezanim projektom” broje samo sigurno uparene ustanove."
    )
    st.caption(
        "Broj studijskih programa zaseban je pokazatelj obrazovne ponude "
        "visokih učilišta; ne predstavlja Erasmus+ projekte i ne mijenja se "
        "s projektnim filtrima."
    )
    st.dataframe(
        format_table(county_frame, ("Odobreno (EUR)",)),
        hide_index=True,
        alt="Regionalni pokazatelji i obuhvat školskih ustanova po županiji",
    )
    st.download_button(
        "Preuzmi regionalne pokazatelje (CSV)",
        data=county_frame.to_csv(index=False).encode("utf-8-sig"),
        file_name="erasmus_regionalni_pokazatelji.csv",
        mime="text/csv",
    )

    if rows:
        selected_county = st.selectbox(
            "Odaberite županiju za pregled projekata",
            ["Sve županije", *[row["Županija"] for row in county_rows]],
        )
        st.caption(
            "Odabir županije filtrira samo popis povezanih projekata ispod "
            "i ne mijenja kartu ni regionalne zbrojeve."
        )
        if selected_county != "Sve županije":
            rows = [row for row in rows if row["county"] == selected_county]

        details = pd.DataFrame(
            [
                {
                    "Županija": row["county"],
                    "Godina": row["year"],
                    "Korisnik": row["beneficiary_name"],
                    "Mjesto korisnika (izvor)": row["city"],
                    "Vrsta ustanove": ", ".join(
                        {
                            "school": "Škola",
                            "kindergarten": "Dječji vrtić",
                            "higher_education": "Visoko učilište",
                        }[kind]
                        for kind in row["registry_kinds"]
                    ),
                    "Sektor": row["sector"],
                    "Projektni broj": row["project_id"],
                    "Odobreno (EUR)": row["grant_amount_eur"],
                }
                for row in rows
            ]
        )
        st.subheader("Povezani projekti")
        st.caption(
            "Svaki redak prikazuje projekt koji je sigurno povezan s registrom "
            "ustanove u odabranoj županiji. Mjesto korisnika dolazi iz projektnog "
            "popisa i može se razlikovati od županije ustanove."
        )
        st.dataframe(
            format_table(details, ("Odobreno (EUR)",)),
            hide_index=True,
            alt="Popis projekata pouzdano povezanih sa školskim, predškolskim i visokoškolskim registrom",
        )


def render_beneficiaries(projects, matches_by_record, institutions_by_id, institutions):
    st.title("Korisnici i vrste ustanova")
    render_page_context(
        "Ovdje možete najprije vidjeti koje vrste obrazovnih ustanova sudjeluju "
        "u odabranim projektima, a zatim potražiti pojedinog korisnika ili "
        "usporediti ustanovu sličnog profila. Usporedba s registrom uključuje "
        "samo sigurno povezane ustanove; nepovezani korisnici nisu nužno "
        "neobrazovne ustanove jer korišteni registri ne obuhvaćaju sve moguće "
        "korisnike. Svi projektni prikazi prate filtre godina i sektora."
    )
    type_summary = summarize_institution_types(
        projects, matches_by_record, institutions_by_id, institutions
    )
    st.subheader("Sudjelovanje prema vrsti ustanove")
    registered_count = sum(row["Ustanove u registru"] for row in type_summary)
    linked_records = sum(row["Projektni zapisi"] for row in type_summary)
    with st.container(horizontal=True):
        st.metric("Ustanove u obrazovnim registrima", registered_count, border=True)
        st.metric("Sigurno povezani projektni zapisi", linked_records, border=True)
        st.metric(
            "Projektni zapisi s vezom na obrazovni registar",
            percent(linked_records / len(projects) * 100 if projects else None),
            border=True,
        )
    st.caption(
        "Broj ustanova u registrima ne mijenja se s projektnim filtrima. "
        "Broj ustanova s projektom i postotak obuhvata mijenjaju se; postotak "
        "je udio u korištenom registru, a ne stopa prijavljivanja ili uspjeha."
    )
    type_frame = pd.DataFrame(type_summary)
    if not type_frame.empty:
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                horizontal_bar_figure(
                    type_frame,
                    "Vrsta ustanove",
                    "Ustanove s povezanim projektom",
                    "Ustanove s projektom",
                    ",.0f",
                ),
                width="stretch",
                config={"displayModeBar": False},
                alt="Broj ustanova s projektom po vrsti obrazovne ustanove",
            )
            st.caption(
                "Ovaj grafikon broji koliko je različitih ustanova svake vrste "
                "imalo barem jedan sigurno povezani projekt."
            )
        with right:
            st.plotly_chart(
                horizontal_bar_figure(
                    type_frame,
                    "Vrsta ustanove",
                    "Udio ustanova s povezanim projektom (%)",
                    "Udio ustanova s projektom",
                    ",.2f",
                    " %",
                ),
                width="stretch",
                config={"displayModeBar": False},
                alt="Udio ustanova s projektom među zapisima registra po vrsti",
            )
            st.caption(
                "Ovdje se isti broj ustanova s projektom uspoređuje s veličinom "
                "odgovarajuće skupine u registru. Zato je udio korisniji od "
                "samog broja kada su vrste ustanova različite veličine."
            )
        st.caption(
            "Tablica spaja oba pogleda: broj ustanova i projektnih zapisa, "
            "ukupno odobrena sredstva te udio u registru. Kombinirane vrste "
            "škola prikazane su kao zasebna skupina kako se ne bi brojile dvaput."
        )
        st.dataframe(
            format_table(type_frame, ("Odobreno (EUR)",)),
            hide_index=True,
            column_config={
                "Udio ustanova s povezanim projektom (%)": (
                    st.column_config.NumberColumn(
                        "Udio ustanova s povezanim projektom (%)",
                        format="%.2f %%",
                    )
                )
            },
            alt="Projekti, sredstva i obuhvat registra po vrsti ustanove",
        )
        st.download_button(
            "Preuzmi pokazatelje po vrsti ustanove (CSV)",
            data=type_frame.to_csv(index=False).encode("utf-8-sig"),
            file_name="erasmus_vrste_ustanova.csv",
            mime="text/csv",
        )
    else:
        st.caption("Nema obrazovnih ustanova u registrima za odabrane filtre.")

    st.divider()
    st.subheader("Pametna usporedba sličnih ustanova")
    st.markdown(
        "Odaberite ustanovu s barem jednim sigurno povezanim projektom. "
        "Pronalazimo do pet sličnih ustanova **iste vrste**, uspoređujući "
        "broj jedinstvenih projektnih brojeva, aktivnosti, godine sudjelovanja "
        "i ukupno odobrena sredstva. Usporedba koristi samo podatke koji "
        "trenutačno prolaze bočne filtre."
    )
    institution_ids = sorted(
        {
            matches_by_record[project["record_id"]]["institution_id"]
            for project in projects
            if matches_by_record[project["record_id"]]["institution_id"]
            in institutions_by_id
        },
        key=lambda institution_id: (
            institutions_by_id[institution_id]["name"].casefold(),
            institutions_by_id[institution_id]["city"].casefold(),
            institution_id,
        ),
    )
    institution_query = st.text_input(
        "Pronađite ustanovu po nazivu ili mjestu",
        key="similar_institution_query",
    )
    normalized_institution_query = institution_query.casefold().strip()
    institution_options = [
        institution_id
        for institution_id in institution_ids
        if normalized_institution_query
        in institutions_by_id[institution_id]["name"].casefold()
        or normalized_institution_query
        in institutions_by_id[institution_id]["city"].casefold()
    ]
    if not institution_options:
        st.caption(
            "Nema ustanova koje odgovaraju pretrazi i imaju sigurno povezane "
            "projekte u trenutačnom odabiru."
        )
    else:
        selected_institution_id = st.selectbox(
            "Odaberite obrazovnu ustanovu",
            institution_options,
            format_func=lambda institution_id: (
                f"{institutions_by_id[institution_id]['name']} — "
                f"{institutions_by_id[institution_id]['city']} "
                f"({institution_category(institutions_by_id[institution_id])})"
            ),
            key="similar_institution_id",
        )
        comparison = compare_similar_institutions(
            projects,
            matches_by_record,
            institutions_by_id,
            selected_institution_id,
        )
        if comparison is None:
            st.caption(
                "Za odabranu ustanovu u trenutačnom skupu nema podataka za usporedbu."
            )
        elif comparison["comparable_institution_count"] < 4:
            st.caption(
                f"Pronađeno je samo {comparison['comparable_institution_count']} "
                "drugih ustanova iste vrste s povezanim projektom. Za smisleniju "
                "usporedbu potrebno je najmanje četiri; pokušajte proširiti filtre "
                "godina ili sektora."
            )
        else:
            selected_profile = comparison["selected"]
            peers = comparison["peers"]
            average_peer_projects = sum(
                len(peer["project_ids"]) for peer in peers
            ) / len(peers)
            average_peer_projects_text = f"{average_peer_projects:.1f}".replace(
                ".", ","
            )
            st.markdown(
                f"**{selected_profile['name']}** ({selected_profile['city']}) "
                f"ima **{len(selected_profile['project_ids'])}** jedinstvenih "
                "projektnih brojeva u odabranim podacima. Usporedili smo je s "
                f"**{comparison['comparable_institution_count']}** drugim "
                "ustanovama iste vrste koje imaju povezane projekte; u tablici "
                f"je do pet najsličnijih. Te ustanove imaju prosječno "
                f"**{average_peer_projects_text}** jedinstvenih projektnih brojeva."
            )
            peer_rows = [
                {
                    "Ustanova": peer["name"],
                    "Mjesto": peer["city"],
                    "Sličnost profila (%)": peer["similarity_percent"],
                    "Jedinstveni projektni brojevi": len(peer["project_ids"]),
                    "Aktivnosti": ", ".join(sorted(peer["activities"])),
                    "Godine sudjelovanja": ", ".join(
                        str(year) for year in sorted(peer["years"])
                    ),
                    "Odobreno (EUR)": peer["grant_amount_eur"],
                }
                for peer in peers
            ]
            st.caption(
                "Postotak sličnosti nije ocjena uspješnosti. Sve četiri značajke "
                "imaju jednaku težinu: uspoređujemo koliko su broj projekata i "
                "iznos blizu vrijednostima u skupini te koliko se aktivnosti i "
                "godine sudjelovanja preklapaju. Zbog malog i nejednakog broja "
                "podataka koristimo ovu jednostavnu usporedbu umjesto strojnog "
                "grupiranja."
            )
            st.dataframe(
                format_table(
                    pd.DataFrame(peer_rows),
                    ("Odobreno (EUR)",),
                ),
                hide_index=True,
                column_config={
                    "Sličnost profila (%)": st.column_config.NumberColumn(
                        "Sličnost profila (%)",
                        format="%.1f %%"
                    )
                },
                alt="Do pet ustanova istog tipa s najsličnijim Erasmus+ profilom",
            )

    st.divider()
    st.subheader("Pretraživanje korisnika i profili")
    recipients = aggregate_recipients(projects)
    if not recipients:
        st.caption("Nema korisnika za odabrane filtre.")
        return

    query = st.text_input(
        "Pretražite naziv korisnika ili mjesto",
    )
    st.caption(
        "Upišite dio naziva ili mjesta. Popis ispod sadrži samo korisnike "
        "u trenutno odabranim godinama i sektorima."
    )
    query_normalized = query.casefold().strip()
    options = [
        row
        for row in recipients
        if query_normalized in row["beneficiary_name"].casefold()
        or query_normalized in row["city"].casefold()
    ]
    if not options:
        st.caption("Nema korisnika koji odgovaraju pretrazi.")
        return

    labels = {
        f"{row['beneficiary_name']} — {row['city']} ({row['project_count']} projekta)": row
        for row in options
    }
    selected_label = st.selectbox(
        "Odaberite korisnika",
        list(labels),
    )
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
    st.caption(
        "Ovi pokazatelji opisuju projekte odabranog korisnika u trenutačnom "
        "filtru. Korisnik je grupiran prema nazivu i mjestu, što nije uvijek "
        "isto što i jedna pravna osoba."
    )

    linked_institution_ids = {
        matches_by_record[row["record_id"]]["institution_id"]
        for row in beneficiary_projects
        if matches_by_record[row["record_id"]]["institution_id"]
    }
    if linked_institution_ids:
        st.subheader("Povezani zapisi u registru")
        st.caption(
            "Ovi registarski zapisi odgovaraju odabranom korisniku prema "
            "primijenjenim pravilima povezivanja. Ako tablice nema, to ne "
            "dokazuje da korisnik nije obrazovna ustanova."
        )
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
        st.dataframe(
            pd.DataFrame(linked_records),
            hide_index=True,
            alt="Povezani zapisi korisnika u obrazovnim registrima",
        )
    else:
        st.caption(
            "Za ovog korisnika nije pronađena jedinstvena podudarnost u dostupnim "
            "registrima. To ne znači da korisnik nije obrazovna ustanova."
        )

    st.subheader("Projekti korisnika")
    st.caption(
        "U tablici su svi projektni zapisi odabranog korisnika u trenutačnom "
        "filtru; isti projektni broj može se pojaviti u više redaka."
    )
    project_rows = [
        {
            "Godina": row["year"],
            "Sektor": row["sector"],
            "Ključna aktivnost": row["key_action"],
            "Tip aktivnosti": row["activity_type"],
            "Projektni broj": row["project_id"],
            "Mjesto korisnika": row["city"],
            "Odobreno (EUR)": row["grant_amount_eur"],
        }
        for row in beneficiary_projects
    ]
    st.dataframe(
        format_table(pd.DataFrame(project_rows), ("Odobreno (EUR)",)),
        hide_index=True,
        alt="Financirani projekti odabranog korisnika",
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
        st.caption(
            "Ovaj grafikon zbraja odobrene iznose po godini za odabranog "
            "korisnika i pomaže vidjeti kada je sudjelovao."
        )
        st.bar_chart(
            yearly_frame,
            x="Godina",
            y="Odobreno (EUR)",
            alt="Odobrena sredstva odabranog korisnika po godini",
        )


def render_concentration(projects, matches_by_record, institutions_by_id):
    st.title("Koncentracija financiranja")
    render_page_context(
        "Ova stranica pokazuje koliki dio ukupnih odobrenih sredstava pripada "
        "korisnicima s najvećim iznosima i koliko se korisnika ponavlja kroz "
        "više projekata. Tako možete procijeniti jesu li sredstva raspoređena "
        "na mnogo korisnika ili se veći dio iznosa slijeva manjem broju njih. "
        "To je opis raspodjele, a ne procjena pravednosti ili dostupnosti programa."
    )
    scope = st.radio(
        "Obuhvat korisnika",
        [
            "Svi korisnici u projektnom popisu",
            "Samo pouzdano povezane obrazovne ustanove",
        ],
        horizontal=True,
    )
    if scope == "Samo pouzdano povezane obrazovne ustanove":
        projects = [
            project
            for project in projects
            if matches_by_record[project["record_id"]]["institution_id"]
            in institutions_by_id
        ]
    st.caption(
        "Udio se računa iz odobrenih iznosa u odabranom obuhvatu, godinama i "
        "sektorima. Korisnik je grupiran prema normaliziranom nazivu i mjestu; "
        "opcija obrazovnih ustanova uključuje samo sigurne veze na dostupne registre."
    )
    recipients = aggregate_recipients(projects)
    if not recipients:
        st.caption("Nema projekata za odabrane filtre.")
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
    st.caption(
        "Pokazatelji top 10 i top 20 računaju udio njihovih sredstava u ukupnom "
        "iznosu odabranog obuhvata. „S 2+ projekata” broji korisnike s najmanje "
        "dva projektna zapisa."
    )

    top_count = st.slider(
        "Broj korisnika na grafikonu",
        min_value=1,
        max_value=min(30, len(recipients)),
        value=min(10, len(recipients)),
    )
    st.caption(
        "Odaberite koliko vodećih korisnika prikazati. Ovaj izbor mijenja "
        "samo grafikon i tablicu; pokazatelji udjela top 10 i top 20 ostaju isti."
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
    st.plotly_chart(
        horizontal_bar_figure(
            top_frame,
            "Korisnik",
            "Odobreno (EUR)",
            "Odobreno",
            ",.2f",
            " €",
        ),
        width="stretch",
        config={"displayModeBar": False},
        alt=f"Vodećih {top_count} korisnika prema odobrenim sredstvima",
    )
    st.caption(
        "Dulji stupac znači veći zbroj odobrenih sredstava za korisnika u "
        "odabranim godinama i sektorima. Naziv uključuje mjesto kako bi se "
        "razlikovali korisnici sličnih imena."
    )

    table = pd.DataFrame(
        [
            {
                "Korisnik": row["beneficiary_name"],
                "Mjesto korisnika": row["city"],
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
        alt="Udio vodećih korisnika u financiranju",
    )
    st.caption(
        "Tablica uz iznos prikazuje broj projektnih zapisa i postotni udio "
        "svakog korisnika u ukupnom odabranom financiranju."
    )


def render_projects(projects):
    st.title("Popis projekata")
    render_page_context(
        "Svaki redak predstavlja zapis iz popisa financiranih projekata, a ne "
        "nužno jedinstven projektni broj. Godine i sektori u bočnoj traci "
        "primjenjuju se prije pretrage. Preuzimanje sadrži upravo trenutno "
        "prikazane retke."
    )
    query = st.text_input(
        "Pretražite korisnika, mjesto ili projektni broj",
    )
    st.caption(
        "Pretraga nalazi upisani tekst u nazivu korisnika, mjestu ili "
        "projektnom broju, bez obzira na velika i mala slova."
    )
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
    st.caption(
        "Svaki redak je zapis iz izvora; ponovljeni projektni brojevi nisu "
        "automatski uklonjeni. CSV preuzima točno ove prikazane retke."
    )
    st.dataframe(
        format_table(export_frame, ("Odobreno (EUR)",)),
        hide_index=True,
        alt="Filtrirani popis projekata s odobrenim sredstvima",
    )
    st.download_button(
        "Preuzmi filtrirane projekte (CSV)",
        data=export_frame.to_csv(index=False).encode("utf-8-sig"),
        file_name="erasmus_projekti.csv",
        mime="text/csv",
    )


def render_data_quality(data):
    st.title("Kvaliteta i metodologija")
    render_page_context(
        "Ova stranica objašnjava odakle dolaze brojke i koliko su veze među "
        "izvorima pouzdane. Najprije je prikazano što sve podaci obuhvaćaju, "
        "zatim kako su projekti povezani s registrima te gdje se izvori "
        "razlikuju. Brojke ovdje opisuju cijeli učitani skup i ne mijenjaju "
        "se bočnim filtrima projekata."
    )
    quality = data["data_quality"]

    st.subheader("Opseg podataka")
    st.caption(
        "Projektni redak i projektni broj nisu isto: isti broj može se pojaviti "
        "u više redaka, primjerice uz različite korisnike. Broj registarskih "
        "ustanova odnosi se na konsolidirane zapise nakon uklanjanja duplikata."
    )
    st.write(
        f"Popis sadrži **{quality['project_records']:,}** projektnih redaka i "
        f"**{quality['unique_project_ids']:,}** jedinstvenih projektnih brojeva. "
        f"Popis pokriva godine: "
        f"{', '.join(map(str, quality['project_list_year_coverage']))}."
    )
    st.write(
        f"Pripremljeno je **{quality['registry_source_rows']:,}** izvornih redaka "
        f"registara, konsolidiranih u **{quality['deduplicated_institutions']:,}** "
        f"zapisa ustanova, uključujući **{quality['kindergarten_registry_count']:,}** "
        "dječjih vrtića."
    )
    st.write(
        f"U popisu nedostaje datum ažuriranja za "
        f"**{quality['missing_source_update_date_count']}** projekata. "
        f"Poznati datumi: {', '.join(quality['project_source_update_dates'])}."
    )

    st.subheader("Povezivanje s registrima")
    st.caption(
        "Grafikon prikazuje rezultat povezivanja svakog projektnog retka s "
        "dostupnim obrazovnim registrima. Uspješna veza znači da je pronađen "
        "jedinstven kandidat prema pravilima ispod; neuspjela veza ne dokazuje "
        "da korisnik nije obrazovna ustanova."
    )
    status_counts = quality["project_match_status_counts"]
    match_frame = pd.DataFrame(
        [
            {"Status": "Jedinstveni naziv i mjesto", "Zapisa": status_counts.get("matched_exact_name_and_city", 0)},
            {"Status": "Točan naziv, mjesto dodano uz naziv", "Zapisa": status_counts.get("matched_exact_name_and_city_suffix", 0)},
            {"Status": "Jedinstveni naziv, mjesto se razlikuje", "Zapisa": status_counts.get("matched_unique_name_location_differs", 0)},
            {"Status": "Skraćeni naziv + jedinstvena adresa i mjesto", "Zapisa": status_counts.get("matched_unique_address_and_city", 0)},
            {"Status": "Jedinstvena adresa, mjesto se razlikuje", "Zapisa": status_counts.get("matched_unique_address_location_differs", 0)},
            {"Status": "Ručno potvrđene veze osnovnih škola", "Zapisa": status_counts.get("matched_user_confirmed_school", 0)},
            {"Status": "Više kandidata / razlika u mjestu", "Zapisa": status_counts.get("location_mismatch", 0) + status_counts.get("ambiguous_exact_name_and_city", 0)},
            {"Status": "Bez kandidata", "Zapisa": status_counts.get("unmatched", 0)},
        ]
    )
    st.bar_chart(
        match_frame,
        x="Status",
        y="Zapisa",
        alt="Broj projektnih zapisa po statusu povezivanja s ustanovama",
    )
    st.caption(
        "Projekt se može povezati jedinstvenim nazivom i kad se mjesto korisnika "
        "razlikuje od mjesta registra, kao i kad je točno ime ustanove navedeno uz "
        "mjesto na kraju naziva korisnika. Za skraćeni naziv traži se i jedinstvena "
        "podudarnost adrese i mjesta. Tri talijanska/dvojezična zapisa škola u Rovinju "
        "ostaju nepovezana. Mjesto u popisu označava korisnika, ne mjesto provedbe "
        "aktivnosti. Nema automatskog fuzzy povezivanja. Visoka učilišta dobivaju "
        "županiju samo kad se njihovo mjesto jednoznačno podudara sa školskim registrom."
    )
    st.write(
        f"Školskih zapisa bez županije: "
        f"**{quality['school_registry_missing_counties']}**. "
        f"Zapisa s proturječnim županijama u izvorima: "
        f"**{len(quality['conflicting_registry_counties'])}**."
    )
    higher_education_coverage = quality[
        "higher_education_registry_county_coverage"
    ]
    program_match_counts = quality["study_program_match_status_counts"]
    st.write(
        f"Županiju je moguće jednoznačno dodijeliti za "
        f"**{higher_education_coverage['with_county']} od "
        f"{higher_education_coverage['total']}** visokih učilišta. "
        f"Od **{quality['study_program_records']}** zapisa studijskih programa, "
        f"**{program_match_counts.get('matched_exact_name_and_city', 0)}** "
        "jedinstveno je povezano s izvođačem i mjestom; "
        f"**{quality['study_program_records_with_unique_institution_and_county']}** "
        "takvih zapisa ima i županiju. "
        f"Preostalih {quality['study_program_records'] - program_match_counts.get('matched_exact_name_and_city', 0)} "
        "nije sigurno povezano s registarskim visokim učilištem."
    )
    st.caption(
        "Studijski programi prikazuju se kao kontekst obrazovne ponude. Njihov "
        "broj nije broj Erasmus+ projekata, financiranje ni mjera sudjelovanja."
    )
    st.caption(
        f"U školskim registrima pronađeno je "
        f"{quality['ambiguous_school_city_county_mappings']} mjesta s više "
        "mogućih županija; takva se mjesta ne koriste za dopunu županija "
        "visokih učilišta."
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
        st.dataframe(
            conflict_frame,
            hide_index=True,
            alt="Ustanove s proturječnim županijama u izvorima",
        )
        st.caption(
            "Ovi zapisi imaju više mogućih županija; nijedna nije odabrana "
            "automatski pa se ustanove ne koriste u regionalnom izračunu."
        )

    st.subheader("Usporedba izvora")
    st.caption(
        "Uspoređujemo broj i financijski zbroj u popisu pojedinačnih projekata "
        "s objavljenim agregatima za iste godine. Razlike mogu nastati zbog "
        "različitog datuma ažuriranja ili načina zbrajanja; podaci se ne "
        "prepravljaju kako bi se umjetno poklopili."
    )
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
        alt="Usklađenje broja projekata i financiranja među izvorima",
    )
    st.caption(
        "Izvorne tablice imaju različite datume ažuriranja. Prikazane razlike su "
        "upozorenja za provjeru, ne automatski razlog za odbacivanje podataka."
    )

    st.subheader("Izvori i ponovljivost")
    st.caption(
        "Tablica navodi javni izvor, izdavača, lokalni naziv datoteke i ulogu "
        "svakog skupa. Aplikacija radi nad lokalnim kopijama, a ne nad živim "
        "podacima s portala."
    )
    source_frame = pd.DataFrame(
        [
            {
                "Skup podataka": "Program Erasmus+ 2021.–2027.",
                "Lokalne datoteke": (
                    "tablica_7_popis-financiranih-projekata…csv; "
                    "tablica_8_pregled-financijskih-rezultata…csv; "
                    "tablica_9_broj-erasmus-zaprimljenih-i-odobrenih…csv"
                ),
                "Izdavač": "Agencija za mobilnost i programe Europske unije",
                "Licencija": "Otvorena dozvola (OD)",
                "Metapodaci izmijenjeni": "9. 10. 2026.",
                "Uloga u analizi": "Projekti, financiranje i agregati prijava.",
                "Kataloški zapis": (
                    "https://data.gov.hr/ckan/hr/dataset/"
                    "program-erasmus-za-razdoblje-od-2021-do-2027-godine"
                ),
            },
            {
                "Skup podataka": "Osnovne škole",
                "Lokalne datoteke": "data (1).csv",
                "Izdavač": "Ministarstvo znanosti, obrazovanja i mladih",
                "Licencija": "Otvorena dozvola (OD)",
                "Metapodaci izmijenjeni": "15. 4. 2026.",
                "Uloga u analizi": "Povezivanje i klasifikacija osnovnih škola.",
                "Kataloški zapis": (
                    "https://data.gov.hr/ckan/hr/dataset/osnovne-skole"
                ),
            },
            {
                "Skup podataka": "Srednje škole",
                "Lokalne datoteke": "data.csv",
                "Izdavač": "Ministarstvo znanosti, obrazovanja i mladih",
                "Licencija": "Otvorena dozvola (OD)",
                "Metapodaci izmijenjeni": "15. 4. 2026.",
                "Uloga u analizi": "Povezivanje i klasifikacija srednjih škola.",
                "Kataloški zapis": (
                    "https://data.gov.hr/ckan/hr/dataset/srednje-skole"
                ),
            },
            {
                "Skup podataka": "Dječji vrtići",
                "Lokalne datoteke": "data (4).csv",
                "Izdavač": "Ministarstvo znanosti, obrazovanja i mladih",
                "Licencija": "Otvorena dozvola (OD)",
                "Metapodaci izmijenjeni": "15. 4. 2026.",
                "Uloga u analizi": (
                    "Povezivanje korisnika Erasmus+ projekata s dječjim vrtićima "
                    "i drugim pravnim osobama koje provode predškolske programe."
                ),
                "Kataloški zapis": (
                    "https://data.gov.hr/ckan/hr/dataset/djecji-vrtici"
                ),
            },
            {
                "Skup podataka": "Ustanove iz sustava visokog obrazovanja",
                "Lokalne datoteke": "data (2).csv",
                "Izdavač": "Ministarstvo znanosti, obrazovanja i mladih",
                "Licencija": "Otvorena dozvola (OD)",
                "Metapodaci izmijenjeni": "15. 4. 2026.",
                "Uloga u analizi": "Povezivanje i klasifikacija visokih učilišta.",
                "Kataloški zapis": (
                    "https://data.gov.hr/ckan/hr/dataset/"
                    "ustanove-iz-sustava-visokog-obrazovanja"
                ),
            },
            {
                "Skup podataka": "Studijski programi visokih učilišta",
                "Lokalne datoteke": "data (3).csv",
                "Izdavač": "Ministarstvo znanosti, obrazovanja i mladih",
                "Licencija": "Otvorena dozvola (OD)",
                "Metapodaci izmijenjeni": "15. 4. 2026.",
                "Uloga u analizi": (
                    "Povezani s visokim učilištima po izvođaču i mjestu; "
                    "broje se kao kontekst ponude studija po županiji."
                ),
                "Kataloški zapis": (
                    "https://data.gov.hr/ckan/dataset/"
                    "studijski-programi-visokih-ucilista"
                ),
            },
        ]
    )
    st.dataframe(
        source_frame,
        hide_index=True,
        column_config={
            "Kataloški zapis": st.column_config.LinkColumn(
                "Kataloški zapis",
                display_text="Otvori skup podataka",
            )
        },
        alt="Izvorni skupovi podataka, njihove lokalne datoteke i namjena",
    )
    st.caption(
        "Metapodaci CKAN-a provjereni su 7. 11. 2026.; prikazani datum je datum "
        "izmjene kataloške kartice, ne nužno datum ažuriranja lokalne datoteke. "
        "Lokalne podatkovne datoteke preuzete su 6. 11. 2026. CKAN navodi "
        "Otvorenu dozvolu RH; provjerite uvjete atribucije prije daljnje "
        "distribucije. Aplikacija koristi lokalne snimke i ne dohvaća podatke "
        "uživo. Studijski programi su kontekstualno povezani s visokim učilištima "
        "po točnom izvođaču i mjestu, a županija se izvodi iz jednoznačnog mjesta."
    )

    duplicates = quality["duplicate_project_ids"]
    st.subheader("Ponovljeni projektni brojevi")
    st.caption(
        "Ovdje su izdvojeni brojevi koji se pojavljuju uz više korisnika. "
        "Zadržani su svi izvorni redci kako se podaci ne bi izgubili bez "
        "potvrde izdavača."
    )
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
        st.dataframe(
            duplicate_frame,
            hide_index=True,
            alt="Ponovljeni projektni brojevi i pripadajući korisnici",
        )
    else:
        st.success("Nema ponovljenih projektnih brojeva.")

    st.subheader("Preuzimanje podataka za daljnju obradu")
    st.caption(
        "Odaberite pripremljeni analitički skup u JSON obliku. To su obrađeni "
        "rezultati za ponovnu uporabu, a ne izvorne CSV datoteke s portala."
    )
    dataset_options = {
        "Projekti (JSON)": "projects",
        "Korisnici (JSON)": "beneficiaries",
        "Ustanove (JSON)": "institutions",
        "Povezivanje projekata i ustanova (JSON)": "project_institution_matches",
        "Regionalni sažetak (JSON)": "regional_summary",
        "Studijski programi i status veze (JSON)": "study_programs",
        "Financije po godini i sektoru (JSON)": "funding_results",
        "Prijave i ugovaranja (JSON)": "application_results",
        "Sažeti pokazatelji (JSON)": "dashboard_summary",
    }
    selection = st.selectbox(
        "Skup podataka",
        list(dataset_options),
    )
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
    st.caption(
        "Odaberite temu analize. Filtri ispod utječu na stranice s projektnim "
        "podacima, a ne na cijelu stranicu kvalitete."
    )
    st.divider()
    st.subheader("Filtri projekata")
    st.caption(
        "Projektni popis sadrži godine 2024.–2026. Odabrane godine i sektori "
        "primjenjuju se na pregled, regije, korisnike, koncentraciju i popis projekata."
    )
    selected_years = st.multiselect(
        "Godine projekata",
        project_years,
        default=project_years,
        key="selected_years",
    )
    selected_sectors = st.multiselect(
        "Sektori projekata",
        sectors,
        default=sectors,
        key="selected_sectors",
    )
    st.caption(
        "Agregat prijava pokriva 2021.–2026. i ima zaseban filtar. "
        "On mijenja samo grafikon prijava i ugovorenih projekata na početnoj stranici."
    )
    st.multiselect(
        "Godine agregata prijava",
        aggregate_years,
        default=aggregate_years,
        key="selected_aggregate_years",
    )
    st.caption(
        "Filtri projekata ne utječu na agregatni grafikon prijava ni na stranicu "
        "kvalitete podataka."
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
        data["institutions"],
        data["study_program_summary"],
        county_geojson,
    )
elif page == "Korisnici i ustanove":
    render_beneficiaries(
        filtered_projects,
        matches_by_record,
        institutions_by_id,
        data["institutions"],
    )
elif page == "Koncentracija financiranja":
    render_concentration(
        filtered_projects,
        matches_by_record,
        institutions_by_id,
    )
elif page == "Projekti":
    render_projects(filtered_projects)
else:
    render_data_quality(data)
