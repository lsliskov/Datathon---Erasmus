# Erasmus+ Explorer RH

Erasmus+ Explorer RH omogućuje pregled financiranih projekata, korisnika i regionalne
zastupljenosti te analizu koncentracije financiranja. Projekt sadrži pripremu podataka
i Streamlit MVP sučelje; izlazne JSON/CSV datoteke ostaju dostupne za integraciju s
drugim sučeljem.

## Pokretanje aplikacije

Iz korijena projekta:

```powershell
python -m pip install -r .\requirements.txt
python .\2021-2027\prepare_data.py
python -m streamlit run .\2021-2027\streamlit_app.py
```

Aplikacija sadrži pregled programa, regionalnu analizu, pretraživanje korisnika i
ustanova, koncentraciju financiranja, filtrirani popis projekata te prikaz kvalitete
i ograničenja podataka.

## Priprema podataka

Za ponovno generiranje pripremljenih podataka:

```powershell
python .\2021-2027\prepare_data.py
```

Skripta koristi samo Python standardnu biblioteku. Rezultati se zapisuju u
`2021-2027/processed/`. Za pokretanje aplikacije potrebni su paketi iz
`requirements.txt`. Za provjeru pripreme i osnovnih pravila povezivanja:

```powershell
python -m unittest discover -s .\2021-2027 -p "test_*.py"
```

## Izlazne datoteke

- `projects.json` / `projects.csv` — jedan zapis po retku izvornog popisa; iznos je
  numerički `grant_amount_eur`, godina je broj, a `record_id` jedinstveno identificira
  redak čak i kad se projektni broj ponavlja.
- `beneficiaries.json` — profil po normaliziranom nazivu korisnika i mjestu, s brojem
  projekata, ukupnim iznosom, godinama, sektorima i vezama na zapise projekata.
- `institutions.json` — ustanove iz školskih i visokih registara. Zrcalni zapisi spajaju
  se samo kad se podudaraju normalizirani naziv, mjesto, adresa i poštanski broj;
  sačuvane su reference na izvorne retke.
- `project_institution_matches.json` / `.csv` — rezultat povezivanja svakog projekta
  s registrom i mogući kandidati.
- `regional_summary.json` — županijski zbrojevi za projekte sigurno povezane sa školskim
  registrom.
- `funding_results.json` — financijski rezultati po godini, mjeri i sektoru iz tablice 8.
- `application_results.json` — prijave, ugovoreni projekti i stope prolaznosti po godini,
  ključnoj aktivnosti i sektoru iz tablice 9.
- `dashboard_summary.json` — sažeti pokazatelji za početni prikaz.
- `data_quality.json` — provjere, duplikati i ograničenja podataka.

U `data_quality.json` nalazi se i godišnja usporedba broja projekata i financiranja
iz popisa projekata s agregatnim tablicama prijava i financija. Razlike su upozorenja
za pregled, ne automatski razlog za uklanjanje zapisa.

## Što prikazuje sučelje

- **Pregled** — ključni pokazatelji, projekti po godini, sredstva po sektoru te
  agregatni broj prijava i ugovorenih projekata.
- **Regije** — županijski prikaz samo za projekte sigurno povezane sa školskim registrom.
- **Korisnici i ustanove** — pretraživi profili korisnika iz popisa projekata, s
  odvojenim prikazom sigurnih veza na registre.
- **Koncentracija financiranja** — udio vodećih korisnika i broj ponovljenih korisnika.
- **Projekti** — pretraživ i filtriran popis s preuzimanjem CSV-a.
- **Kvaliteta podataka** — metodologija povezivanja, usporedba izvora i upozorenja,
  uz preuzimanje pripremljenih skupova u JSON-u.

Filtri godina i sektora projekata u bočnoj traci odnose se na popis projekata
(2024.–2026.). Agregati prijava imaju zaseban filtar godina (2021.–2026.) i nisu
filtrirani prema sektoru projekata. CSV izvoz projekata čuva iznose kao numeričke
vrijednosti, ne kao formatirani tekst.

## Pravila povezivanja i ograničenja

Nazivi se normaliziraju uklanjanjem dijakritika, ujednačavanjem razmaka i interpunkcije
te proširenjem čestih kratica `OŠ`, `SŠ` i `DV`. Automatsko povezivanje radi se samo ako
su naziv i mjesto jedinstveno podudarni nakon normalizacije. Nejasna podudaranja i
razlike u mjestu ostaju označene za provjeru; nema automatskog fuzzy povezivanja.

Popis financiranih projekata sadrži korisnike iz više sektora, dok registri pokrivaju
samo škole i visoka učilišta. Zato su županijski rezultati namjerno označeni kao
djelomični i ne predstavljaju potpunu regionalnu raspodjelu svih Erasmus+ projekata.
Podaci u izvornim tablicama imaju različite datume ažuriranja pa se mogu razlikovati
njihovi godišnji zbrojevi. Skripta čuva sve retke iz popisa projekata, uključujući
ponovljene projektne brojeve, i prijavljuje ih u `data_quality.json` umjesto da ih
tiho uklanja.

Županijska karta koristi lokalni GeoJSON iz
[`2021-2027/geo/croatia-counties.geojson`](./2021-2027/geo/croatia-counties.geojson).
Granice su izvedene iz Natural Earth admin-1 podataka (public domain); GeoJSON je
preuzet iz repozitorija [croatia-travel-map](https://github.com/GeneralSting/croatia-travel-map)
na commit-u `48be7e000d9b305b85b562e566a9c6a055a46e34`. Karta se učitava lokalno i
ne traži vanjske kartografske pločice. Prazna županija znači da nema pouzdano povezane
školske ustanove u obuhvaćenim projektima, a ne da ondje nema Erasmus+ projekata.