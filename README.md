# Erasmus+ Explorer RH

Erasmus+ Explorer RH omogućuje pregled financiranih projekata, korisnika i regionalne
zastupljenosti te analizu koncentracije financiranja. Projekt sadrži pripremu podataka
i Streamlit MVP sučelje; izlazne JSON/CSV datoteke ostaju dostupne za integraciju s
drugim sučeljem, a tablični prikazi mogu se preuzeti u XLSX formatu.

Dokumentacija projekta, metodologija, pregled natječajnih kriterija i predloženi
tijek trosminutne demonstracije nalaze se u [DATATHON.md](./DATATHON.md).

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

## Snimke zaslona

Početna stranica daje pregled projekata, financiranja i prijava; regionalna karta
zatim prikazuje gdje su sigurno povezane ustanove zastupljene u dostupnim podacima.

![Početni pregled Erasmus+ projekata i financiranja](./docs/screenshots/pregled.png)

Na stranici Regije uz kartu je tablica s brojčanim vrijednostima po županijama,
a gumb **Preuzmi** sprema trenutačni regionalni sažetak u Excel.

![Regionalna analiza i tablica za preuzimanje](./docs/screenshots/regije.png)

Usporedba ustanova pomaže korisniku staviti rezultate odabrane ustanove u kontekst
sličnih ustanova istog tipa. Prikazane značajke i ograničenja objašnjeni su uz tablicu.

![Usporedba profila sličnih ustanova](./docs/screenshots/usporedba-ustanova.png)

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
- `institutions.json` — ustanove iz školskih, predškolskih i visokih registara. Zrcalni zapisi spajaju
  se samo kad se podudaraju normalizirani naziv, mjesto, adresa i poštanski broj;
  sačuvane su reference na izvorne retke.
- `project_institution_matches.json` / `.csv` — rezultat povezivanja svakog projekta
  s registrom i mogući kandidati.
- `regional_summary.json` — županijski zbrojevi za projekte sigurno povezane sa školskim,
  predškolskim i visokoškolskim registrom; županije visokih učilišta izvode se samo iz
  jednoznačnog podudaranja mjesta sa školskim registrom.
- `study_programs.json` / `study_program_summary.json` — veze studijskih programa s
  visokim učilištima prema izvođaču i mjestu te županijski kontekst ponude studija.
- `funding_results.json` — financijski rezultati po godini, mjeri i sektoru iz tablice 8.
- `application_results.json` — prijave, ugovoreni projekti i stope prolaznosti po godini,
  ključnoj aktivnosti i sektoru iz tablice 9.
- `dashboard_summary.json` — sažeti pokazatelji za početni prikaz.
- `data_quality.json` — provjere, duplikati i ograničenja podataka.

U `data_quality.json` nalazi se i godišnja usporedba broja projekata i financiranja
iz popisa projekata s agregatnim tablicama prijava i financija. Razlike su upozorenja
za pregled, ne automatski razlog za uklanjanje zapisa.

## Što prikazuje sučelje

- **Sažetak** — ključni pokazatelji, projekti po godini, sredstva po sektoru te
  agregatni broj prijava i ugovorenih projekata.
- **Regije** — županijski prikaz projekata sigurno povezanih sa školama i visokim
  učilištima te zaseban kontekst zapisa studijskih programa po županiji.
- **Korisnici** — usporedba sudjelovanja prema vrsti ustanove te pretraživi
  profili korisnika iz popisa projekata, s odvojenim prikazom sigurnih veza na registre
  i usporedbom odabrane ustanove s drugim ustanovama iste vrste sličnog Erasmus+
  profila.
- **Koncentracija** — udio vodećih korisnika i broj ponovljenih korisnika.
- **Podaci i metodologija** — izvori, pravila povezivanja i kvaliteta podataka,
  uz pretraživ popis projekata na dnu stranice i preuzimanje pripremljenih skupova
  u Excelu. Ispod važnijih tablica nalazi se gumb **Preuzmi** za XLSX; izbornik
  ugrađene tablice Streamlit može nuditi i vlastiti CSV izvoz.

Filtri godina i sektora projekata u bočnoj traci odnose se na popis projekata
(2024.–2026.). Agregati prijava imaju zaseban filtar godina (2021.–2026.) i nisu
filtrirani prema sektoru projekata. Svi podaci koji se preuzimaju kroz sučelje
dostupni su u XLSX formatu; iznosi ostaju numeričke vrijednosti. Ugniježđeni
elementi u analitičkim skupovima prikazuju se kao JSON tekst unutar ćelija.
Pripremljeni JSON/CSV izlazi i dalje su dostupni u mapi `2021-2027/processed/`.

Regionalni pokazatelj „udio ustanova s povezanim projektom” dijeli jedinstvene škole,
dječje vrtiće i visoka učilišta povezana s projektom u odabranom skupu s brojem
obrazovnih ustanova u registru županije. Županija visokog učilišta preuzima se iz mjesta samo kad je veza sa
školskim registrima jednoznačna. To je obuhvat registarskih zapisa, a ne stopa prijava,
odobravanja ili dostupnosti programa. Studijski programi agregirani po županiji daju
kontekst obrazovne ponude i ne predstavljaju Erasmus+ projekte ni financiranje.

Usporedba sličnih ustanova uzima samo ustanove iste vrste s barem jednim
sigurno povezanim projektom u odabranim godinama i sektorima. Uspoređuje broj
projektnih brojeva, aktivnosti, godine sudjelovanja i ukupna sredstva; ne
ocjenjuje kvalitetu ustanove. Metodu i uvjete za prikaz rezultata objašnjava
[tehnička dokumentacija](./DATATHON.md).

## Pravila povezivanja i ograničenja

Nazivi se normaliziraju uklanjanjem dijakritika, ujednačavanjem razmaka i interpunkcije
te proširenjem čestih kratica `OŠ`, `SŠ` i `DV`. Projekt se povezuje kad se naziv i
mjesto jedinstveno podudaraju, kad se točan naziv registra podudara nakon uklanjanja
završnog naziva mjesta iz korisnikova naziva, kad naziv jedinstveno upućuje na ustanovu
iako se mjesto razlikuje, ili kad se skraćeni naziv može razriješiti jedinstvenom
točnom adresom.
Ako naziv završava nazivom mjesta, ono se odvaja i preostali naziv mora točno
odgovarati jedinstvenoj ustanovi u tom mjestu. Tim su pravilom i provjerom
jedinstvenih točnih adresa povezane još 34 projektne stavke, uključujući III.
gimnaziju Zagreb i dječje vrtiće. Korisnica je dodatno potvrdila 45 veza osnovnih škola nakon pregleda kandidata;
tri talijanska/dvojezična zapisa iz Rovinja ostaju nepovezana. Ta ručno potvrđena
iznimka nije automatsko fuzzy povezivanje. Više nerazriješenih kandidata ostaje
nepovezano. Mjesto u projektnom popisu označava korisnika, a ne mjesto provedbe projekta.

U preglednoj Excelici 555 znači broj nepovezanih projektnih zapisa iz obrazovanja
odraslih, mladih i sporta. Broj 326 označava različite očišćene tekstualne nazive
među tih 555 zapisa, a ne broj zapisa ni broj ustanova. Ako se isti naziv ponovi
u više projekata, broji se jednom; različiti zapisi iste ustanove mogu se brojiti
zasebno ako su nazivi dovoljno različiti.

Popis financiranih projekata sadrži korisnike iz više sektora, dok dostupni registri
pokrivaju škole, dječje vrtiće i visoka učilišta. Zato su županijski rezultati namjerno označeni kao
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
ne traži vanjske kartografske pločice. Prazna županija znači da nema pouzdano povezane obrazovne ustanove u obuhvaćenim
projektima, a ne da ondje nema Erasmus+ projekata.