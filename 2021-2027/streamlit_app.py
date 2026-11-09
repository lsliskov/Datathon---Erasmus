import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from app_helpers import (
    filter_application_years,
    compare_similar_institutions,
    dataframe_height,
    dataset_export_frame,
    excel_bytes,
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
PLOTLY_CONFIG = {"displayModeBar": False, "scrollZoom": False}
EXCEL_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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


def download_excel(frame, file_name, sheet_name, key):
    st.download_button(
        "Preuzmi",
        data=excel_bytes(frame, sheet_name),
        file_name=file_name,
        mime=EXCEL_MIME_TYPE,
        key=key,
    )


def horizontal_bar_figure(
    frame,
    category_column,
    value_column,
    value_label,
    value_format,
    suffix="",
    height=None,
    left_margin=260,
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
        height=height or max(360, 46 * len(frame) + 100),
        margin={"l": left_margin, "r": 30, "t": 25, "b": 55},
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
        "Istražite financirane projekte, organizacije i regionalnu zastupljenost "
        "na temelju dostupnih podataka za Hrvatsku."
    )
    render_page_context(
        "Ovdje možete vidjeti koliko je projekata financirano, koliko je "
        "sredstava odobreno i koliko je prijava ugovoreno."
    )

    linked_project_count = sum(
        bool(matches_by_record[project["record_id"]]["institution_id"])
        for project in projects
    )
    total_grants = sum(project["grant_amount_eur"] for project in projects)
    recipients = aggregate_recipients(projects)
    with st.container(horizontal=True):
        st.metric(
            "Projekti",
            f"{len(projects):,}".replace(",", "."),
            border=True,
        )
        st.metric(
            "Organizacije uz projekte",
            f"{len(recipients):,}".replace(",", "."),
            border=True,
        )
        st.metric(
            "Odobreno (odabrani projekti)",
            euro(total_grants),
            border=True,
        )
        st.metric(
            "Projekti povezani s ustanovom iz registra",
            f"{linked_project_count:,}".replace(",", "."),
            border=True,
        )
    st.caption(
        "Organizacija uz projekt je naziv organizacije naveden u izvornom popisu. "
        "Kod povezanih projekata taj se naziv i mjesto mogu sigurno povezati s "
        "ustanovom iz dostupnog registra."
    )

    yearly = defaultdict(lambda: {"project_count": 0, "grant_amount_eur": 0.0})
    sector_totals = defaultdict(lambda: {"project_count": 0, "grant_amount_eur": 0.0})
    for project in projects:
        yearly[project["year"]]["project_count"] += 1
        yearly[project["year"]]["grant_amount_eur"] += project["grant_amount_eur"]
        sector_totals[project["sector"]]["project_count"] += 1
        sector_totals[project["sector"]]["grant_amount_eur"] += project["grant_amount_eur"]
    project_years_label = ", ".join(
        str(year) for year in sorted(yearly)
    ) or "nema odabrane godine"

    left, right = st.columns([1, 2])
    with left:
        st.subheader("Projekti po godini")
        st.caption(
            f"Odabrane godine: {project_years_label} — prema popisu financiranih projekata."
        )
        yearly_frame = pd.DataFrame(
            [
                {"Godina": year, "Broj projekata": values["project_count"]}
                for year, values in sorted(yearly.items())
            ]
        )
        if not yearly_frame.empty:
            figure = px.bar(yearly_frame, x="Godina", y="Broj projekata")
            figure.update_xaxes(tickangle=0)
            figure.update_layout(height=360)
            st.plotly_chart(
                figure,
                width="stretch",
                config=PLOTLY_CONFIG,
                alt="Broj financiranih projektnih zapisa po godini",
            )
    with right:
        st.subheader("Odobrena sredstva po sektoru")
        st.caption(
            f"Odabrane godine: {project_years_label} — prema popisu financiranih projekata."
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
            st.plotly_chart(
                horizontal_bar_figure(
                    sector_frame,
                    "Sektor",
                    "Odobreno (EUR)",
                    "Odobreno",
                    ",.2f",
                    " €",
                    height=360,
                    left_margin=320,
                ),
                width="stretch",
                config=PLOTLY_CONFIG,
                alt="Odobrena sredstva po sektoru",
            )

    st.divider()
    st.subheader("Prijave i ugovoreni projekti")
    st.caption(
        "Razdoblje: 2021.–2026. — prema godišnjim agregatima prijava. "
        "Ovaj grafikon uspoređuje ukupan broj zaprimljenih prijava s brojem "
        "ugovorenih projekata po godini i obuhvaća sve sektore."
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
        )
        figure = px.bar(
            application_frame,
            x="Godina",
            y=["Prijave", "Ugovoreni"],
            barmode="group",
        )
        figure.update_xaxes(tickangle=0)
        figure.update_layout(height=420)
        st.plotly_chart(
            figure,
            width="stretch",
            config=PLOTLY_CONFIG,
            alt="Broj Erasmus+ prijava i ugovorenih projekata po godini",
        )
    else:
        st.caption("Za odabrane godine nema agregatnih podataka o prijavama.")

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
        "Broj projekata i iznosi uključuju organizacije čiji se naziv i mjesto "
        "mogu sigurno povezati sa školom, dječjim vrtićem "
        "i visoka učilišta s poznatom županijom. Mjesto organizacije uz projekt iz "
        "izvornog popisa može se razlikovati od mjesta ustanove u registru; "
        "mjesto provedbe aktivnosti nije navedeno u dostupnim podacima. "
        "Broj registriranih ustanova služi kao usporedna osnova, a podaci o "
        "projektima mijenjaju se prema odabranim godinama i sektorima."
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
        "Projekti": "Projekti",
        "Različiti projektni brojevi": "Različiti projektni brojevi",
        "Registrirane školske ustanove": "Registrirane školske ustanove",
        "Registrirana visoka učilišta": "Registrirana visoka učilišta",
        "Registrirani dječji vrtići": "Registrirani dječji vrtići",
        "Registrirane obrazovne ustanove": "Registrirane obrazovne ustanove",
        "Ustanove s projektom u registru": "Ustanove s projektom u registru",
        "Udio ustanova s projektom (%)": "Udio ustanova s projektom (%)",
        "Odobreno (EUR)": "Odobreno (EUR)",
    }
    selected_metric_label = st.selectbox(
        "Pokazatelj na karti",
        list(metric_options),
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
                "Ustanove s projektom u registru": values.get(
                    "Ustanove s povezanim projektom", 0
                ),
                "Udio ustanova s projektom (%)": values.get(
                    "Udio ustanova s povezanim projektom (%)", 0
                ),
                "Organizacije uz projekte": values.get("Korisnici", 0),
                "Projekti": values.get("Projektni zapisi", 0),
                "Različiti projektni brojevi": values.get(
                    "Jedinstveni projektni brojevi", 0
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
            "Ustanove s projektom u registru": ":,.0f",
            "Udio ustanova s projektom (%)": ":,.2f",
            "Projekti": ":,.0f",
            "Različiti projektni brojevi": ":,.0f",
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
        config=PLOTLY_CONFIG,
        alt=f"Karta hrvatskih županija: {selected_metric}",
    )
    st.caption(
        "Karta obuhvaća samo projekte čije se organizacije mogu sigurno povezati "
        "sa školama, vrtićima "
        "i visokim učilištima. Prazna ili svjetlija županija ne pokazuje nužno da ondje "
        "nema projekata: dio organizacija i ustanova nije moguće povezati s "
        "trenutačno dostupnim registrima. Udio ustanova s projektom računa se "
        "kao broj ustanova iz registra s barem jednim povezanim projektom "
        "podijeljen s ukupnim brojem ustanova iste skupine u registru — posebno "
        "za škole, vrtiće i visoka učilišta. To nije stopa prijava niti mjera "
        "dostupnosti programa. Granice su lokalno pripremljene iz podataka "
        "Natural Earth."
    )
    county_rows.sort(
        key=lambda row: row["Projekti"] or 0,
        reverse=True,
    )
    county_frame = pd.DataFrame(county_rows)
    county_frame = county_frame.drop(columns=["county_id"])
    county_frame = county_frame.drop(columns=["Udio ustanova s projektom (%)"])
    county_frame = county_frame.rename(
        columns={"Različiti projektni brojevi": "Broj različitih projekata"}
    )
    st.caption(
        "Tablica ispod karte daje točne vrijednosti za svaku županiju. "
        "„Registrirane obrazovne ustanove” čine usporednu osnovu, a "
        "„ustanove s projektom u registru” broje ustanove koje su pronađene "
        "u odgovarajućem registru i povezane s barem jednim projektom. "
        "„Organizacije uz projekte” su nazivi iz izvornog popisa i mogu "
        "uključivati udruge; zato ta dva broja nisu ista."
    )
    st.dataframe(
        format_table(county_frame, ("Odobreno (EUR)",)),
        hide_index=True,
        alt="Regionalni pokazatelji i obuhvat školskih ustanova po županiji",
    )
    download_excel(
        county_frame,
        "erasmus_regionalni_pokazatelji.xlsx",
        "Regionalni pokazatelji",
        "download_regional_summary",
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
                    "Organizacija uz projekt": row["beneficiary_name"],
                    "Mjesto organizacije (izvor)": row["city"],
                    "Mjesto ustanove (registar)": (
                        institutions_by_id[row["institution_id"]]["city"]
                    ),
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
            "Svaki redak prikazuje projekt koji je sigurno povezan s ustanovom "
            "u odabranoj županiji. „Mjesto organizacije (izvor)” dolazi "
            "iz projektnog popisa, a „Mjesto ustanove (registar)” iz registra. "
            "Mjesto provedbe aktivnosti nije navedeno u dostupnim podacima."
        )
        st.dataframe(
            format_table(details, ("Odobreno (EUR)",)),
            hide_index=True,
            alt="Popis projekata pouzdano povezanih sa školskim, predškolskim i visokoškolskim registrom",
        )
        download_excel(
            details,
            "erasmus_povezani_projekti_zupanije.xlsx",
            "Povezani projekti",
            "download_county_projects",
        )


def render_beneficiaries(projects, matches_by_record, institutions_by_id, institutions):
    st.title("Organizacije i ustanove")
    render_page_context(
        "Usporedite sudjelovanje po vrstama obrazovnih ustanova, pronađite "
        "organizaciju ili usporedite ustanovu s drugima sličnog profila. Prikazi "
        "prate odabrane godine i sektore."
    )
    st.caption(
        "Obrazovni registri obuhvaćaju osnovne i srednje škole, kombinirane "
        "škole, dječje vrtiće te visoka učilišta. Udruge i druge organizacije "
        "iz popisa projekata nisu nužno u tim registrima."
    )
    st.subheader("Usporedba ustanova prema vrsti")
    st.caption(
        "Grafikoni i tablica ispod odnose se na jednu skupinu ustanova u svakom "
        "retku, primjerice osnovne škole, srednje škole, dječje vrtiće ili "
        "visoka učilišta. Postotak pokazuje koliko je ustanova iz te konkretne "
        "skupine u registru imalo barem jedan povezani projekt."
    )
    type_summary = summarize_institution_types(
        projects, matches_by_record, institutions_by_id, institutions
    )
    registered_count = sum(row["Ustanove u registru"] for row in type_summary)
    linked_records = sum(row["Projektni zapisi"] for row in type_summary)
    with st.container(horizontal=True):
        st.metric("Ustanove u obrazovnim registrima", registered_count, border=True)
        st.metric("Projekti povezani s ustanovom iz registra", linked_records, border=True)
        st.metric(
            "Udio projektnih redaka povezanih s ustanovom iz registra",
            percent(linked_records / len(projects) * 100 if projects else None),
            border=True,
        )
    type_frame = pd.DataFrame(type_summary)
    if not type_frame.empty:
        type_frame = type_frame[
            [
                "Vrsta ustanove",
                "Odobreno (EUR)",
                "Ustanove s povezanim projektom",
                "Udio ustanova s povezanim projektom (%)",
                "Projektni zapisi",
                "Jedinstveni projektni brojevi",
                "Korisnici",
                "Ustanove u registru",
            ]
        ]
        type_frame = type_frame.rename(
            columns={
                "Ustanove s povezanim projektom": "Ustanove s projektom",
                "Udio ustanova s povezanim projektom (%)": (
                    "Udio ustanova s projektom (%)"
                ),
                "Projektni zapisi": "Projekti",
                "Jedinstveni projektni brojevi": "Različiti projektni brojevi",
                "Korisnici": "Organizacije uz projekte",
            }
        )
    if not type_frame.empty:
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                horizontal_bar_figure(
                    type_frame,
                    "Vrsta ustanove",
                    "Ustanove s projektom",
                    "Ustanove s projektom",
                    ",.0f",
                ),
                width="stretch",
                config=PLOTLY_CONFIG,
                alt="Broj ustanova s projektom po vrsti obrazovne ustanove",
            )
            st.caption(
                "Ovaj grafikon broji koliko je ustanova iz svake skupine imalo barem "
                    "jedan projekt koji smo mogli povezati s registrom."
            )
        with right:
            st.plotly_chart(
                horizontal_bar_figure(
                    type_frame,
                    "Vrsta ustanove",
                    "Udio ustanova s projektom (%)",
                    "Udio ustanova s projektom",
                    ",.2f",
                    " %",
                ),
                width="stretch",
                config=PLOTLY_CONFIG,
                alt="Udio ustanova s projektom među zapisima registra po vrsti",
            )
            st.caption(
                "Ovdje se broj ustanova s projektom uspoređuje sa svim ustanovama "
                "iste skupine u registru. Zato se vidi obuhvat svake skupine, "
                "ne samo njezina apsolutna veličina."
            )
        st.caption(
            "Tablica spaja oba pogleda: broj ustanova i projekata, "
            "ukupno odobrena sredstva te udio u registru. Kombinirane vrste "
            "škola prikazane su kao zasebna skupina kako se ne bi brojile dvaput."
        )
        st.dataframe(
            format_table(type_frame, ("Odobreno (EUR)",)),
            hide_index=True,
            column_config={
                "Udio ustanova s projektom (%)": (
                    st.column_config.NumberColumn(
                            "Udio ustanova s projektom (%)",
                        format="%.2f %%",
                    )
                )
            },
            alt="Projekti, sredstva i obuhvat registra po vrsti ustanove",
        )
        download_excel(
            type_frame,
            "erasmus_vrste_ustanova.xlsx",
            "Vrste ustanova",
            "download_institution_types",
        )
    else:
        st.caption("Nema obrazovnih ustanova u registrima za odabrane filtre.")

    st.subheader("Pretraživanje organizacija i profili")
    recipients = aggregate_recipients(projects)
    if not recipients:
        st.caption("Nema organizacija za odabrane filtre.")
        return

    query = st.text_input(
        "Pretražite naziv organizacije ili mjesto",
    )
    st.caption(
        "Upišite dio naziva ili mjesta. Primjerice „suma”, „Split” ili "
        "„gimnazija”. Popis ispod sadrži samo organizacije "
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
        st.caption("Nema organizacija koje odgovaraju pretrazi.")
        return

    labels = {
        f"{row['beneficiary_name']} — {row['city']} ({row['project_count']} projekta)": row
        for row in options
    }
    selected_label = st.selectbox(
        "Odaberite organizaciju",
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
        "Ovi pokazatelji opisuju projekte odabrane organizacije ili ustanove "
        "u trenutačnom filtru. Isti naziv i mjesto grupiraju se zajedno."
    )

    linked_institution_ids = {
        matches_by_record[row["record_id"]]["institution_id"]
        for row in beneficiary_projects
        if matches_by_record[row["record_id"]]["institution_id"]
    }
    if linked_institution_ids:
        st.subheader("Ustanova pronađena u registru")
        st.caption(
            "Ovo je ustanova iz javnog registra koju smo prema nazivu, mjestu "
            "ili adresi mogli sigurno povezati s odabranom organizacijom iz "
            "projektnog popisa."
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
            alt="Ustanova povezana s odabranom organizacijom",
        )
        download_excel(
            pd.DataFrame(linked_records),
            "erasmus_povezani_registri_korisnika.xlsx",
            "Povezani registri",
            "download_beneficiary_matches",
        )
    else:
        st.caption(
            "Za organizaciju nije pronađena jedna sigurna veza s trenutno "
            "korištenim registrima."
        )

    st.subheader("Projekti odabrane organizacije")
    st.caption(
        "U tablici su svi projekti odabrane organizacije u trenutačnom "
        "filtru; isti projektni broj može se pojaviti u više redaka."
    )
    project_rows = [
        {
            "Godina": row["year"],
            "Sektor": row["sector"],
            "Ključna aktivnost": row["key_action"],
            "Tip aktivnosti": row["activity_type"],
            "Projektni broj": row["project_id"],
            "Odobreno (EUR)": row["grant_amount_eur"],
            "Mjesto organizacije": row["city"],
        }
        for row in beneficiary_projects
    ]
    beneficiary_project_frame = pd.DataFrame(project_rows)
    st.dataframe(
        format_table(beneficiary_project_frame, ("Odobreno (EUR)",)),
        hide_index=True,
        alt="Financirani projekti odabrane organizacije",
    )
    download_excel(
        beneficiary_project_frame,
        "erasmus_projekti_korisnika.xlsx",
        "Projekti organizacije",
        "download_beneficiary_projects",
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
            "organizacije i pomaže vidjeti kada je sudjelovala."
        )
        figure = px.bar(yearly_frame, x="Godina", y="Odobreno (EUR)")
        figure.update_xaxes(tickangle=0)
        figure.update_layout(height=360)
        st.plotly_chart(
            figure,
            width="stretch",
            config=PLOTLY_CONFIG,
            alt="Odobrena sredstva odabrane organizacije po godini",
        )


    st.divider()
    st.subheader("Usporedba sličnih ustanova")
    st.markdown(
        "Odaberite ustanovu s barem jednim projektom koji smo mogli povezati "
        "s registrom. "
        "Pronalazimo do pet sličnih ustanova **iste vrste**, uspoređujući "
        "broj različitih projektnih brojeva, aktivnosti, godine sudjelovanja "
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
    st.caption(
        "Možete upisati samo dio naziva ili mjesta, primjerice "
        "„gimnazija”, „Split” ili „Zagreb”."
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
        else:
            selected_profile = comparison["selected"]
            peers = comparison["peers"]
            st.markdown(
                f"**{selected_profile['name']}** ({selected_profile['city']}) "
                f"ima **{len(selected_profile['project_ids'])}** različitih "
                "projektnih brojeva u odabranim podacima. Broj drugih ustanova "
                "iste vrste s projektom za usporedbu: "
                f"**{comparison['comparable_institution_count']}**."
            )
            if peers:
                average_peer_projects = sum(
                    len(peer["project_ids"]) for peer in peers
                ) / len(peers)
                average_peer_projects_text = f"{average_peer_projects:.1f}".replace(
                    ".", ","
                )
                st.caption(
                    f"Prikazujemo do pet najsličnijih ustanova. One imaju prosječno "
                    f"{average_peer_projects_text} različitih projektnih brojeva."
                )
                peer_rows = [
                    {
                        "Ustanova": peer["name"],
                        "Mjesto": peer["city"],
                        "Sličnost profila (%)": peer["similarity_percent"],
                        "Različiti projektni brojevi": len(peer["project_ids"]),
                        "Odobreno (EUR)": peer["grant_amount_eur"],
                        "Aktivnosti": ", ".join(sorted(peer["activities"])),
                        "Godine sudjelovanja": ", ".join(
                            str(year) for year in sorted(peer["years"])
                        ),
                    }
                    for peer in peers
                ]
                st.caption(
                    "Postotak sličnosti nije ocjena uspješnosti. Sve četiri značajke "
                    "imaju jednaku težinu: uspoređujemo koliko su broj projekata i "
                    "iznos blizu vrijednostima u skupini te koliko se aktivnosti i "
                    "godine sudjelovanja preklapaju."
                )
                peer_frame = pd.DataFrame(peer_rows)
                st.dataframe(
                    format_table(peer_frame, ("Odobreno (EUR)",)),
                    hide_index=True,
                    column_config={
                        "Sličnost profila (%)": st.column_config.NumberColumn(
                            "Sličnost profila (%)",
                            format="%.1f %%"
                        )
                    },
                    alt="Do pet ustanova istog tipa s najsličnijim Erasmus+ profilom",
                )
                download_excel(
                    peer_frame,
                    "erasmus_slicne_ustanove.xlsx",
                    "Slicne ustanove",
                    "download_similar_institutions",
                )
            else:
                st.caption(
                    "U odabranim godinama i sektorima nema drugih ustanova iste "
                    "vrste s povezanim projektom za usporedbu."
                )

    st.divider()


def render_concentration(projects, matches_by_record, institutions_by_id):
    st.title("Financiranje")
    render_page_context(
        "Ova stranica pokazuje koliki dio ukupnih odobrenih sredstava pripada "
        "organizacijama i ustanovama s najvećim iznosima te koliko ih ima više "
        "od jednog projekta."
    )
    scope = st.radio(
        "Koga želite uključiti?",
        [
            "Sve organizacije i ustanove iz popisa projekata",
            "Samo ustanove koje smo pronašli u obrazovnim registrima",
        ],
        horizontal=True,
    )
    st.caption(
        "Prva opcija uključuje sve organizacije navedene u popisu projekata, "
        "uključujući udruge. Druga uključuje samo škole, vrtiće i visoka učilišta "
        "koje smo mogli sigurno povezati s javnim registrom."
    )
    if scope == "Samo ustanove koje smo pronašli u obrazovnim registrima":
        projects = [
            project
            for project in projects
            if matches_by_record[project["record_id"]]["institution_id"]
            in institutions_by_id
        ]
    st.caption(
        "Iznosi i broj projekata odnose se na odabrane godine i sektore. "
        "Udio ukupnog financiranja vodećih organizacija pokazuje koliki dio "
        "svih odobrenih sredstava iz odabranog popisa pripada odabranom vrhu. "
        "Naziv i mjesto grupiraju se "
        "zajedno."
    )
    recipients = aggregate_recipients(projects)
    if not recipients:
        st.caption("Nema projekata za odabrane filtre.")
        return

    total_funding = sum(row["grant_amount_eur"] for row in recipients)
    repeat_recipients = sum(row["project_count"] > 1 for row in recipients)
    top_count = st.slider(
        "Broj vodećih organizacija",
        min_value=1,
        max_value=min(20, len(recipients)),
        value=min(10, len(recipients)),
    )
    top_amount = sum(row["grant_amount_eur"] for row in recipients[:top_count])
    with st.container(horizontal=True):
        st.metric("Organizacije", len(recipients), border=True)
        st.metric("S 2+ projekata", repeat_recipients, border=True)
        st.metric(
            "Ukupno odobreno",
            euro(total_funding),
            border=True,
        )
        st.metric(
            f"Udio ukupnog financiranja vodećih {top_count} organizacija",
            percent(top_amount / total_funding * 100 if total_funding else None),
            border=True,
        )
    st.caption(
        f"Odabrani broj {top_count} određuje i udio financiranja i popis vodećih "
        "organizacija u grafikonu i tablici. Organizacija s 2+ projekata ima najmanje "
        "dva retka u popisu."
    )
    top_frame = pd.DataFrame(
        [
            {
                "Organizacija": f"{row['beneficiary_name']} — {row['city']}",
                "Odobreno (EUR)": row["grant_amount_eur"],
            }
            for row in recipients[:top_count]
        ]
    )
    st.subheader(f"Vodećih {top_count} organizacija prema odobrenim sredstvima")
    st.plotly_chart(
        horizontal_bar_figure(
            top_frame,
            "Organizacija",
            "Odobreno (EUR)",
            "Odobreno",
            ",.2f",
            " €",
            height=620,
            left_margin=300,
        ),
        width="stretch",
        config=PLOTLY_CONFIG,
        alt=f"Vodećih {top_count} organizacija prema odobrenim sredstvima",
    )
    st.caption(
        "Dulji stupac prikazuje veći zbroj odobrenih sredstava za organizaciju u "
        "odabranim godinama i sektorima. Naziv uključuje mjesto kako bi se "
        "razlikovali korisnici sličnih imena."
    )

    table = pd.DataFrame(
        [
            {
                "Organizacija": row["beneficiary_name"],
                "Mjesto organizacije": row["city"],
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
        height=dataframe_height(len(table)),
        hide_index=True,
        column_config={
            "Udio (%)": st.column_config.NumberColumn("Udio (%)", format="%.2f %%")
        },
        alt="Udio vodećih organizacija u financiranju",
    )
    download_excel(
        table,
        "erasmus_koncentracija_financiranja.xlsx",
        "Vodeci korisnici",
        "download_funding_concentration",
    )
    st.caption(
        "Tablica uz iznos prikazuje broj projekata i postotni udio svake "
        "organizacije u ukupnom odabranom financiranju."
    )


def render_projects(projects, nested=False):
    if nested:
        st.subheader("Popis projekata")
    else:
        st.title("Popis projekata")
    render_page_context(
        "Svaki redak predstavlja zapis iz popisa financiranih projekata, a ne "
        "nužno jedinstven projektni broj. Godine i sektori u bočnoj traci "
        "primjenjuju se prije pretrage. Preuzimanje sadrži upravo trenutno "
        "prikazane retke."
    )
    query = st.text_input(
        "Pretražite organizaciju, mjesto ili projektni broj",
    )
    st.caption(
        "Pretraga nalazi upisani tekst u nazivu organizacije, mjestu ili "
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
    st.dataframe(
        format_table(export_frame, ("Odobreno (EUR)",)),
        hide_index=True,
        alt="Filtrirani popis projekata s odobrenim sredstvima",
    )
    download_excel(
        export_frame,
        "erasmus_projekti.xlsx",
        "Projekti",
        "download_filtered_projects",
    )


def render_data_quality(data, filtered_projects):
    st.title("Podaci i metodologija")
    render_page_context(
        "Ova stranica objašnjava odakle dolaze brojke i koliko su veze među "
        "izvorima pouzdane. Na dnu se nalazi pretraživ popis projekata koji "
        "prati odabrane godine i sektore."
    )
    quality = data["data_quality"]

    st.subheader("Opseg podataka")
    st.caption(
        "Projektni redak i projektni broj nisu isto: isti broj može se pojaviti "
        "u više redaka, primjerice uz različite organizacije. Broj registarskih "
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
        f"Za **{quality['missing_source_update_date_count']}** redaka u izvornom "
        "popisu nije naveden datum zadnjeg ažuriranja. Za ostale su navedeni "
        "datumi, primjerice: "
        f"{', '.join(quality['project_source_update_dates'])}."
    )

    st.subheader("Povezivanje s registrima")
    st.caption(
        "Tablica pokazuje koliko je redaka iz popisa bilo moguće povezati s "
        "nekom ustanovom iz trenutačno dostupnih registara. Udruge i druge "
        "organizacije ne moraju imati odgovarajući javni registar u korištenim "
        "izvorima."
    )
    matched_count = sum(
        bool(item["institution_id"])
        for item in data["project_institution_matches"]
    )
    match_frame = pd.DataFrame(
        [
            {"Status povezivanja": "Povezano s ustanovom", "Projekata": matched_count},
            {
                "Status povezivanja": "Nije povezano s ustanovom",
                "Projekata": (
                    len(data["project_institution_matches"]) - matched_count
                ),
            },
        ]
    )
    st.dataframe(
        match_frame,
        hide_index=True,
        alt="Broj projekata povezanih i nepovezanih s ustanovom",
    )
    download_excel(
        match_frame,
        "erasmus_status_povezivanja.xlsx",
        "Status povezivanja",
        "download_match_summary",
    )
    st.caption(
        "Veze se temelje na jedinstvenim podudaranjima naziva, mjesta i adrese; "
        "tri talijanska/dvojezična zapisa škola u Rovinju ostaju nepovezana. "
        "Mjesto u projektnom popisu je mjesto navedeno uz organizaciju ili "
        "ustanovu, a ne nužno mjesto provedbe aktivnosti."
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
    st.write(
        f"Županiju je moguće jednoznačno dodijeliti za "
        f"**{higher_education_coverage['with_county']} od "
        f"{higher_education_coverage['total']}** visokih učilišta. "
        "To omogućuje uključivanje visokih učilišta u regionalnu usporedbu."
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
        download_excel(
            conflict_frame,
            "erasmus_proturjecne_zupanije.xlsx",
            "Proturjecne zupanije",
            "download_county_conflicts",
        )
        st.caption(
            "Ovi zapisi imaju više mogućih županija; nijedna nije odabrana "
            "automatski pa se ustanove ne koriste u regionalnom izračunu."
        )

    st.subheader("Usporedba izvora")
    st.caption(
        "Uspoređujemo broj i financijski zbroj u popisu projekata "
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
    download_excel(
        reconciliation,
        "erasmus_usporedba_izvora.xlsx",
        "Usporedba izvora",
        "download_source_reconciliation",
    )
    st.caption(
        "Za 2025. razlika od jednog projekta nije posljedica ponovljenog "
        "projektnog broja: ponovljeni broj postoji u projektnom popisu 2024. "
        "i tamo označava dvije organizacije uz isti projekt. Razlika za 2025. može "
        "proizaći iz različitog datuma ažuriranja ili načina zbrajanja izvora. "
        "Izvorne tablice nisu umjetno usklađivane."
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
                    "Povezivanje organizacija iz Erasmus+ projekata s dječjim vrtićima "
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
        "uživo."
    )

    duplicates = quality["duplicate_project_ids"]
    st.subheader("Projekt s više organizacija")
    st.caption(
        "Ovdje je prikazan projektni broj koji se u izvornom popisu pojavljuje "
        "uz dvije različite organizacije. To nije greška ni duplikat za brisanje: "
        "isti projekt može uključivati više organizacija, pa se oba retka zadržavaju."
    )
    if duplicates:
        duplicate_frame = pd.DataFrame(
            [
                {
                    "Projektni broj": item["project_id"],
                    "Organizacije u izvornim redcima": ", ".join(item["beneficiaries"]),
                    "ID-jevi redaka": ", ".join(item["record_ids"]),
                }
                for item in duplicates
            ]
        )
        st.warning(
            "Projektni broj je isti, ali se korisnici razlikuju. Zato se projekt "
            "u popisu prikazuje u dva retka, a analiza jasno razlikuje broj redaka "
            "od broja različitih projektnih brojeva."
        )
        st.dataframe(
            duplicate_frame,
            hide_index=True,
            alt="Ponovljeni projektni brojevi i pripadajući korisnici",
        )
        download_excel(
            duplicate_frame,
            "erasmus_projekt_s_vise_organizacija.xlsx",
            "Projekt s više organizacija",
            "download_duplicate_projects",
        )
    else:
        st.success("Nema ponovljenih projektnih brojeva.")

    render_projects(filtered_projects, nested=True)

    st.subheader("Preuzimanje podataka za daljnju obradu")
    st.caption(
        "Na kraju stranice možete preuzeti obrađene skupove podataka u Excelu. "
        "Ugniježđene vrijednosti prikazane su kao JSON tekst u ćelijama."
    )
    dataset_options = {
        "Projekti": "projects",
        "Organizacije": "beneficiaries",
        "Ustanove": "institutions",
        "Povezivanje projekata i ustanova": "project_institution_matches",
        "Regionalni sažetak": "regional_summary",
        "Financije po godini i sektoru": "funding_results",
        "Prijave i ugovaranja": "application_results",
        "Sažeti pokazatelji": "dashboard_summary",
    }
    selection = st.selectbox(
        "Skup podataka",
        list(dataset_options),
    )
    export_frame = dataset_export_frame(data[dataset_options[selection]])
    download_excel(
        export_frame,
        f"{dataset_options[selection]}.xlsx",
        "Podaci",
        "download_prepared_dataset",
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

page = st.segmented_control(
    "Odaberite prikaz",
    [
        "Sažetak",
        "Regije",
        "Organizacije i ustanove",
        "Financiranje",
        "Podaci i metodologija",
    ],
    default="Sažetak",
    required=True,
    label_visibility="collapsed",
    width="stretch",
    wrap=True,
    key="main_navigation",
)

with st.sidebar:
    st.divider()
    st.subheader("Filtri projekata")
    st.caption(
        "Odabrane godine i sektori primjenjuju se na projektne prikaze i popis."
    )
    selected_years = st.multiselect(
        "Godine projekata",
        project_years,
        default=project_years,
        key="selected_years",
    )
    sector_labels = {
        "Odgoj i opće obrazovanje": "Opće obrazovanje",
        "Strukovno obrazovanje i osposobljavanje": "Strukovno obrazovanje",
    }
    selected_sectors = st.pills(
        "Sektori projekata",
        sectors,
        format_func=lambda sector: sector_labels.get(sector, sector),
        default=sectors,
        selection_mode="multi",
        key="selected_sectors",
        wrap=True,
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

filtered_projects = filter_projects(projects, selected_years, selected_sectors or [])

if page == "Sažetak":
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
elif page == "Organizacije i ustanove":
    render_beneficiaries(
        filtered_projects,
        matches_by_record,
        institutions_by_id,
        data["institutions"],
    )
elif page == "Financiranje":
    render_concentration(
        filtered_projects,
        matches_by_record,
        institutions_by_id,
    )
else:
    render_data_quality(data, filtered_projects)
