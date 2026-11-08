# Erasmus+ Explorer RH — dokumentacija za Datathon

## Sažetak rješenja

Erasmus+ Explorer RH je prototip za istraživanje financiranih Erasmus+ projekata
i sudjelovanja obrazovnih ustanova u Hrvatskoj. Povezuje popis projekata,
agregate prijava i financiranja te registre škola i visokih učilišta. Služi kao
informacijski alat za obrazovne ustanove, javnu upravu, istraživače i građane koji
žele razumjeti gdje se projekti provode, koje vrste ustanova sudjeluju i koliko je
financiranje koncentrirano.

Rješenje ne procjenjuje kvalitetu pojedinih ustanova niti uzročni učinak programa.
Broj projekata nije isto što i vjerojatnost uspjeha ili dostupnost prilike.

## Pitanje i javna korist

Jesu li financirani Erasmus+ projekti i iznosi ravnomjerno raspoređeni među
obrazovnim sektorima, vrstama ustanova i hrvatskim županijama — i koliko je
pouzdano to moguće zaključiti iz javno dostupnih podataka?

Odgovor pomaže korisnicima uočiti obrasce sudjelovanja, ponovljene korisnike,
regionalne razlike i praznine u podacima. Ustanove mogu pronaći usporedive
korisnike i vidjeti da li je njihov kraj zastupljen u dostupnim rezultatima.
Javna uprava može lakše prepoznati gdje su potrebni dodatni podaci ili ciljana
informativna podrška. To su indikacije za daljnje istraživanje, ne dokaz
nejednakog pristupa ili uzroka slabijeg sudjelovanja.

## Funkcionalnosti prototipa

- Pregled financiranih projektnih zapisa, iznosa po sektoru i agregatnih prijava
  i ugovorenih projekata.
- Regionalna karta i tablica za škole, dječje vrtiće i visoka učilišta: projekti, sredstva,
  registarski nazivnici te broj studijskih programa po županiji kao kontekst
  obrazovne ponude.
- Usporedba registarskih i povezanih ustanova prema vrsti ustanove, s brojem
  korisnika, projektnim zapisima, jedinstvenim projektnim brojevima i iznosima.
- Pretraživanje profila korisnika, analiza koncentracije financiranja i preuzimanje
  filtriranih projektnih, regionalnih i institucionalnih tablica te obrađenih
  analitičkih skupova u XLSX formatu.
- Pametna usporedba odabrane obrazovne ustanove s do pet najsličnijih ustanova
  iste vrste, prema broju projekata, aktivnostima, godinama sudjelovanja i
  odobrenim sredstvima; način izračuna i broj usporedivih ustanova vidljivi su
  uz rezultat.
- Prikaz kvalitete podataka, nepodudarnosti izvora i metodologije; na istoj
  stranici nalazi se i filtrirani popis projekata.

Sučelje je namijenjeno i osobama koje ne rade svakodnevno s analizom podataka:
uz prikaze su kratka objašnjenja ključnih mjera i načina čitanja. Granice podataka
i metodološka ograničenja navedeni su odvojeno na stranici „Podaci i metodologija”.

## Snimke zaslona sučelja

Početni pregled povezuje financirane projektne zapise s agregatima prijava i
ugovaranja. Regionalna karta i tablica zatim prikazuju prostorni raspored
sigurno povezanih ustanova; gumb **Preuzmi** uz tablicu sprema XLSX s brojčanim
vrijednostima.

![Početni pregled programa i financiranja](./docs/screenshots/pregled.png)

![Regionalna karta i županijska tablica](./docs/screenshots/regije.png)

Na stranici korisnika moguće je usporediti ustanovu s drugim ustanovama istog
tipa. Usporedba prikazuje značajke, broj uključenih ustanova i ograničenja
metode, a tablica se može preuzeti u Excel.

![Usporedba odabrane ustanove sličnim ustanovama](./docs/screenshots/usporedba-ustanova.png)

## Izvori podataka i metapodaci

Lokalne podatkovne datoteke preuzete su 6. studenoga 2026. Kataloški metapodaci
provjereni su 7. studenoga 2026. U nastavku su kataloške kartice, izdavači,
licence prikazane u CKAN-u i lokalne datoteke. Datum izmjene odnosi se na
metapodatke kartice, ne nužno na sadržaj svake lokalne CSV snimke.

Svaka lokalna CSV snimka preuzeta je izravno s odgovarajućeg CKAN skupa ili
njegova resursa navedenog u tablici ispod; izvorne datoteke nisu naknadno
filtrirane, ručno skraćivane niti prepravljane. Skripta učitava te snimke i
priprema podatke za analizu:
pretvara tipove vrijednosti, normalizira tekst radi povezivanja te izrađuje
izvedene sažetke. Filtri u aplikaciji su interaktivni i mijenjaju samo prikaz,
ne sadržaj preuzetih izvornih CSV datoteka. Iznimke i opseg izvedenih tablica
objašnjeni su u odjeljku analize ulaznih tablica.

| Kataloški skup | Lokalna datoteka i uloga | Izdavač | Licencija u katalogu | Izmjena metapodataka |
|---|---|---|---|---|
| [Program Erasmus+ 2021.–2027.](https://data.gov.hr/ckan/hr/dataset/program-erasmus-za-razdoblje-od-2021-do-2027-godine) ([CSV projekata](https://data.gov.hr/ckan/dataset/8212ac19-861e-4a41-b2fa-cc66bdbda907/resource/74a703c5-9b28-4868-88a5-984c928c5070/download/tablica_7_popis-financiranih-projekata-programa-erasmus_2021_2027.csv)) | `tablica_7_...csv`: pojedinačni projekti, korisnik, sektor, godina i iznos. | Agencija za mobilnost i programe Europske unije | Otvorena dozvola (OD) | 9. 10. 2026. |
| [Program Erasmus+ — isti skup](https://data.gov.hr/ckan/hr/dataset/program-erasmus-za-razdoblje-od-2021-do-2027-godine) ([CSV financija](https://data.gov.hr/ckan/dataset/8212ac19-861e-4a41-b2fa-cc66bdbda907/resource/5af3727b-30dc-4d34-8009-2d74bebb2bd4/download/tablica_8_pregled-financijskih-rezultata-programa-erasmus-2021_2027.csv)) | `tablica_8_...csv`: agregatni financijski rezultati i usklađenje iznosa. | Agencija za mobilnost i programe Europske unije | Otvorena dozvola (OD) | 9. 10. 2026. |
| [Program Erasmus+ — isti skup](https://data.gov.hr/ckan/hr/dataset/program-erasmus-za-razdoblje-od-2021-do-2027-godine) ([CSV prijava i ugovaranja](https://data.gov.hr/ckan/dataset/8212ac19-861e-4a41-b2fa-cc66bdbda907/resource/8ab34131-385a-4e08-a883-151d5054f112/download/tablica_9_broj-erasmus-zaprimljenih-i-odobrenih-projekata-2021_2027.csv)) | `tablica_9_...csv`: broj prijava i ugovorenih projekata te agregatne stope. | Agencija za mobilnost i programe Europske unije | Otvorena dozvola (OD) | 9. 10. 2026. |
| [Osnovne škole](https://data.gov.hr/ckan/hr/dataset/osnovne-skole) | `data (1).csv`: podaci o osnovnim školama za povezivanje i klasifikaciju. | Ministarstvo znanosti, obrazovanja i mladih | Otvorena dozvola (OD) | 15. 4. 2026. |
| [Srednje škole](https://data.gov.hr/ckan/hr/dataset/srednje-skole) | `data.csv`: podaci o srednjim školama za povezivanje, vrstu i županiju. | Ministarstvo znanosti, obrazovanja i mladih | Otvorena dozvola (OD) | 15. 4. 2026. |
| [Ustanove iz sustava visokog obrazovanja](https://data.gov.hr/ckan/hr/dataset/ustanove-iz-sustava-visokog-obrazovanja) | `data (2).csv`: registar ustanova za povezivanje i klasifikaciju visokih učilišta; mjesto se koristi za izvedbu županije. | Ministarstvo znanosti, obrazovanja i mladih | Otvorena dozvola (OD) | 15. 4. 2026. |
| [Studijski programi visokih učilišta](https://data.gov.hr/ckan/dataset/studijski-programi-visokih-ucilista) | `data (3).csv`: studijski programi povezani s registrom ustanova po izvođaču i mjestu te agregirani po županiji kao kontekst obrazovne ponude. | Ministarstvo znanosti, obrazovanja i mladih | Otvorena dozvola (OD) | 15. 4. 2026. |
| [Dječji vrtići](https://data.gov.hr/ckan/hr/dataset/djecji-vrtici) ([CSV resurs](https://data.gov.hr/ckan/dataset/0b951eaa-d9e7-4c68-adcf-5090f452abf4/resource/7e7c26cd-6ad4-4cdd-b0cb-42b0ad2a933c/download/data.csv)) | `data (4).csv`: 885 zapisa dječjih vrtića i drugih pravnih osoba koje provode predškolske programe; koristi se za povezivanje projekata. | Ministarstvo znanosti, obrazovanja i mladih | Otvorena dozvola (OD) | Kartica: 15. 4. 2026.; CSV-resurs: 19. 5. 2025. |

CKAN u pregledanim karticama navodi [Otvorenu dozvolu RH](https://data.gov.hr/id/licence/otvorena-dozvola-rh). Prije daljnje
distribucije provjerite tekst dozvole i obveze atribucije. Datum preuzimanja
lokalnih datoteka je 6. studenoga 2026.; datum provjere kataloških metapodataka
je 7. studenoga 2026. Aplikacija radi nad lokalnim snimkama i ne dohvaća
podatke uživo.

## Analiza ulaznih tablica

Brojevi zapisa u nastavku ne uključuju zaglavlje CSV-a. Izvorne datoteke nisu
prepravljane; čišćenje i normalizacija rade se u pripremi podataka, a izvorni
redci ostaju sačuvani. Iznosi u europskom formatu pretvaraju se u numeričke
vrijednosti, a nazivi i mjesta normaliziraju se za sigurno povezivanje.
Projektni brojevi čuvaju se kao tekst, bez automatskog mijenjanja ili uklanjanja.

| Ulazna tablica | Što sadrži i nalaz | Obrada, ograničenja i veza s analizom |
|---|---|---|
| `tablica_7_popis-financiranih-projekata…csv` | 1.856 zapisa pojedinačnih financiranih projekata, s godinom, sektorom, korisnikom, mjestom, aktivnošću, projektnim brojem, odobrenim iznosom i datumom ažuriranja. Ima 1.855 različitih projektnih brojeva. | Decimalni zarezi i iznosi s oznakom EUR parsiraju se u brojeve; godina, naziv/mjesto i identifikatori se normaliziraju. Projektni broj `2024-2-HR01-KA155-YOU-000267618` pojavljuje se dvaput: uz korisnike „SUMA – Udruga za održivi razvoj” i „Natura i kultura”. Oba retka su zadržana jer se razlikuju korisnici; nije dokazano da je jedan duplikat za brisanje. Ovo je jedina tablica na razini pojedinačnog projekta i temelj je korisničkih, regionalnih i koncentracijskih prikaza. |
| `tablica_8_pregled-financijskih-rezultata…csv` | Godišnji agregati raspoloživih, ugovorenih i realiziranih sredstava te postoci, razvrstani po sektoru i ukupno; dostupni agregati obuhvaćaju 2021.–2026. | Agregatna je tablica, nije popis projekata niti korisnika. Služi za pregled raspodjele kroz razdoblje i provjeru ukupno ugovorenog iznosa prema pojedinačnoj tablici projekata. Tablica i popis mogu imati različit datum ažuriranja, pa se razlike prikazuju, a ne ispravljaju automatski. |
| `tablica_9_broj-erasmus-zaprimljenih-i-odobrenih…csv` | Agregatni broj prijava i ugovorenih projekata prema godini, ključnoj aktivnosti i sektoru, uz objavljene stope. Pokriva 2021.–2026. | Nema korisnika ni projektnih brojeva, pa se ne može izravno povezati s registrom ustanova niti s pojedinačnim projektima. Koristi se za grafikon prijava i ugovaranja te usporedbu godišnjeg broja ugovorenih projekata. |
| `data (1).csv` — osnovne škole | 926 zapisa škola, s nazivom, mjestom, adresom, županijom i vrstom ustanove. | Povezivanje koristi jedinstven normalizirani naziv; ako se mjesto razlikuje, veza se prihvaća samo kad naziv upućuje na jednu registriranu ustanovu. Adresa može razriješiti skraćeni naziv kad se jedinstveno podudara. |
| `data.csv` — srednje škole | 443 zapisa srednjih škola s mjestom, adresom, županijom i vrstom ustanove; postoje i kombinirane vrste koje obuhvaćaju više razina obrazovanja. | Kombinirane vrste se u prikazu grupiraju zasebno kako ustanova ne bi ulazila u više nazivnika. Vrsta i županija dolaze iz registra; adresa pomaže razriješiti jedinstveni kratki naziv korisnika. |
| `data (2).csv` — ustanove visokog obrazovanja | 133 zapisa ustanova visokog obrazovanja, uključujući naziv, mjesto i vrstu ustanove. | Županija se dodjeljuje samo ako mjesto ustanove ima točno jednu županiju u školskim registrima. U ovom presjeku svih 133 mjesta imaju jednoznačnu vezu. To omogućuje da i projekti sigurno povezani s visokim učilištima uđu u regionalnu analizu. |
| `data (3).csv` — studijski programi | 1.727 zapisa programa s nazivom, ECTS-om, trajanjem, izvođačem/nositeljem, mjestom i akademskim stupnjem. | 1.709 zapisa sigurno je povezano s registarskim visokim učilištem po normaliziranom nazivu izvođača i mjestu; svih 1.709 dobiva županiju. Preostalih 18 nije povezano s ustanovom i izostavljeno je iz županijskih zbrojeva studija. Broj programa je kontekst obrazovne ponude, ne mjera Erasmus+ sudjelovanja ili financiranja. |
| `data (4).csv` — dječji vrtići | 885 zapisa iz CSV-resursa CKAN-a s nazivom, adresom, mjestom i županijom. Skup obuhvaća i druge pravne osobe koje provode predškolske programe. | Koristi se za povezivanje predškolskih ustanova s projektnim korisnicima i njihovo uključivanje u usporedbu vrsta i regija. Izdavač je Ministarstvo znanosti, obrazovanja i mladih; katalog navodi Otvorenu dozvolu (OD). |

Četiri registra ustanova sadrže ukupno 2.387 izvornih redaka, konsolidiranih u
2.374 ustanove radi uklanjanja ponovljenih registarskih zapisa. Županije visokih
učilišta izvedene su iz mjesta preko školskih registara samo kad je mjesto
jednoznačno povezano s jednom županijom. Projekt se povezuje kad se naziv i mjesto točno
podudaraju, kad jedinstven naziv upućuje na jednu ustanovu neovisno o razlici u
mjestu, kad je jedinstven registarski naziv naveden uz isto mjesto na kraju
naziva korisnika, ili kad skraćeni naziv i točna adresa daju jedinstvenu vezu.
Uz ta automatska pravila korisnica je potvrdila još 45 povezivanja osnovnih škola
prema nazivu, mjestu i pregledu registarskih kandidata. Tri projektna zapisa
talijanske ili dvojezične škole u Rovinju ostaju nepovezana jer se ne mogu
sigurno spariti s odgovarajućim registrom. U ovom presjeku 1.163 projektna
zapisa imaju povezanu ustanovu, a za 693 nije pronađen potvrđen kandidat u ovim
registrima. Dodatno je povezano 34 zapisa u kojima je naziv ustanove bio točan,
ali je mjesto bilo dodano na kraj naziva korisnika, ili su se jedinstvena točna
adresa i naziv ustanove podudarali. Među njima su III. gimnazija Zagreb i više
dječjih vrtića. Svih 44 ranije izdvojenih razlika u mjestu
sada su povezane jedinstvenim nazivom ili točnom adresom; pet redaka pod kratkim
nazivom „Tehnička škola” adresom Eugena Kumičića 55 povezano je s Tehničkom
školom u Slavonskom Brodu. Mjesto u projektnom popisu označava mjesto korisnika,
ne nužno mjesto provedbe aktivnosti. Nepovezivanje nije dokaz da korisnik ne
postoji; registri ne pokrivaju sve vrste korisnika. Ne primjenjuje se automatsko
fuzzy povezivanje; 45 ručno potvrđenih školskih veza izričito je evidentirano.
Nakon njihova povezivanja i dodatnog povezivanja zapisa koji imaju točan naziv
uz dodano mjesto ili jedinstvenu točnu adresu, 138 zapisa obrazovnih sektora
još nije povezano;
među preostalim zapisima iz obrazovanja odraslih, mladih i sporta 555 nema
potvrđene veze. Ti zapisi nisu uklonjeni.

Prethodni popis 561 zapisa iz obrazovanja odraslih, mladih i sporta imao je 328
različitih normaliziranih naziva korisnika. Nakon povezivanja jedinstvenih
podudaranja ostalo je 555 nepovezanih projektnih zapisa i 326 različitih
normaliziranih tekstualnih naziva među njima. Primjerice, ako se isti naziv
korisnika pojavi u tri projekta, to su tri projektna zapisa, ali jedan naziv
u broju 326. Razlike samo u velikim slovima, dijakritici ili interpunkciji
nakon čišćenja ne stvaraju novi naziv. Broj 326 zato nije broj ustanova:
različite ustanove mogu imati isti naziv, a ista ustanova može biti zapisana
pod dovoljno različitim nazivima da se broje odvojeno.

U usporedbi izvora za godine u kojima postoji projektni popis, 2024. broj se
podudara (575), ali se iznos razlikuje za **+312.097 EUR** u popisu projekata
prema financijskom agregatu. Za 2025. popis ima **641** zapis, a agregat
ugovaranja **642**; iznos popisa manji je za **307.606,12 EUR**. Za 2026. broj
(640) i iznos (**50.706.031,90 EUR**) podudaraju se. Mogući razlozi poput
različitih datuma presjeka ili načina agregiranja ne mogu se potvrditi samo iz
datoteka, zato su razlike označene za provjeru i nijedan izvor nije tiho
prepravljan.

## Metodologija i tumačenje pokazatelja

- **Projektni zapis** je redak u popisu financiranih projekata. Projektni broj se
  čuva kao poseban pokazatelj; ponovljeni broj se ne uklanja automatski jer
  izvorni redci mogu imati različite korisnike.
- **Korisnik** se grupira prema normaliziranom nazivu i mjestu.
- Različit broj projektnih redaka i jedinstvenih naziva korisnika ne znači
  jednak broj pravnih osoba. „Jedinstveni nazivi” broje tekstualne oznake nakon
  normalizacije; više organizacija može imati sličan naziv, a ista organizacija
  može biti zapisana pod različitim nazivima.
- **Pouzdana veza s registrom** postoji kad naziv i mjesto daju jedinstvenu vezu,
  kad je normalizirani naziv jedinstven u registru neovisno o mjestu, ili kad
  se skraćeni naziv može razriješiti jedinstvenom točnom adresom. Ako ostane
  više kandidata, zapis se ne povezuje automatski.
- **Sličnost obrazovnih ustanova** nije model koji ustanove svrstava u unaprijed
  zadane skupine niti ocjena njihove kvalitete. Za odabranu ustanovu prvo se
  izdvoje druge ustanove iste vrste koje imaju barem jedan sigurno povezani
  projekt u trenutno odabranim godinama i sektorima. Ako ih je manje od četiri,
  usporedba se ne prikazuje. Inače se prikazuje do pet najsličnijih ustanova
  prema četiri jednako ponderirane značajke: broj različitih projektnih
  brojeva i ukupno odobrena sredstva uspoređuju se prema rasponu u toj skupini,
  a preklapanje aktivnosti i godina računa se Jaccardovim omjerom. Prikazuju se
  broj usporedivih ustanova, rezultat sličnosti i stvarne vrijednosti značajki.
  To je namjerno jednostavna i objašnjiva usporedba; ne koristi K-means jer
  količina i obuhvat podataka ne opravdavaju složenije grupiranje.
- **Vrsta ustanove** izvedena je iz vrste u registru. Kombinirane vrste škola
  prikazuju se kao zasebna kategorija kako ista ustanova ne bi bila više puta
  uračunata u nazivnik. Visoka učilišta određuju se prema vrsti registra.
- **Udio ustanova s povezanim projektom** računa broj jedinstvenih ustanova iz
  registra koje imaju projekt u odabranom skupu podijeljen ukupnim brojem
  jedinstvenih škola, vrtića i visokih učilišta u registru županije. To je pokrivenost
  dostupnog registra odabranim popisom, a ne stopa prijava, odobravanja ili
  stvarne dostupnosti programa.
- Regionalni projektni prikaz uključuje pouzdano povezane škole, dječje vrtiće
  i visoka učilišta s pridruženom županijom. Županija za visoka učilišta izvedena je iz
  mjesta koje se jednoznačno podudara sa školskim registrom; mjesta s više
  mogućih županija ne koriste se za tu dopunu.
- Studijski programi povezuju se s visokim učilištem samo po jedinstvenom
  normaliziranom nazivu izvođača i mjestu; broj se zatim agregira po županiji.
  To je odvojeni kontekst ponude studija, ne veza studija s Erasmus+ projektima.
- Pojedinačni projektni popis pokriva 2024.–2026.; agregati prijava pokrivaju
  2021.–2026. Te vremenske serije nisu izravno usporedive.
- Razlike između popisa projekata i agregatnih tablica te ponovljeni projektni
  brojevi objavljuju se kao upozorenja. Nema tihog odbacivanja zapisa.

## Tehnička arhitektura i pokretanje

`2021-2027/prepare_data.py` učitava lokalne CSV datoteke, validira obvezna polja,
normalizira nazive, povezuje projekte i ustanove te zapisuje JSON/CSV rezultate
u `2021-2027/processed/`. `2021-2027/streamlit_app.py` prikazuje analize nad tim
rezultatima. Pomoćne agregacije nalaze se u `2021-2027/app_helpers.py`.

### Osvježavanje podataka i proširenje

U ovoj verziji podaci se osvježavaju ručno: CSV-resursi su preuzeti izravno s
poveznica u tablici izvora, ali aplikacija ih još ne dohvaća sama s CKAN-a niti
se automatski osvježava. U budućem razvoju može se dodati kontrolirano
preuzimanje s istih pojedinačnih poveznica, provjera promjene strukture izvora
i datuma preuzimanja te čuvanje preuzete izvorne datoteke prije obrade. Tako
automatsko osvježavanje ne bi narušilo usporedivost podataka niti zamijenilo
stabilnu lokalnu demonstraciju.

Za novi presjek podataka potrebno je preuzeti novije CSV-resurse s poveznica u
tablici izvora, zamijeniti odgovarajuće lokalne ulazne datoteke u
`2021-2027/` uz nazive koje očekuje `prepare_data.py`, zabilježiti datum
preuzimanja i provjeriti jesu li zaglavlja/obvezna polja promijenjena. Zatim
iz korijena repozitorija pokrenuti:

```powershell
python .\2021-2027\prepare_data.py
python -m unittest discover -s .\2021-2027 -p "test_*.py"
python -m streamlit run .\2021-2027\streamlit_app.py
```

Prva naredba ponovno gradi obrađene datoteke u
`2021-2027/processed/`; aplikacija ih čita iz tih JSON/CSV izlaza. Treba
provjeriti stranicu kvalitete podataka, broj povezivanja, usporedbu izvornih
zbrojeva i prikaze u aplikaciji prije objave novog presjeka. Izvorne CSV snimke
ostaju zasebne od obrađenih rezultata i ne treba ručno mijenjati JSON-ove.

Za proširenje na druge godine ili programska razdoblja potrebno je dodati
odgovarajuće projektne i agregatne resurse, utvrditi njihova polja i mapirati
ih na zajedničku strukturu projektnog zapisa. Projektno razdoblje treba ostati zasebnim filtrom ili metapodatkom kako se
podaci iz razdoblja s različitim pravilima ne bi neprimjetno zbrajali. Za nove
javne registre potrebno je dodati ulazne datoteke, provjeru strukture, pravila
normalizacije i povezivanja, referencu na izvor te testove kvalitete. Nesigurne
veze trebaju ostati odvojene, a ne automatski potvrđene. Na taj način struktura
rezultata u `processed/` može ostati stabilna za sučelje i kad se izvori
proširuju. Trenutačna verzija nema CKAN API, zakazano osvježavanje ni javni API.

Iz korijena repozitorija:

```powershell
python -m pip install -r .\requirements.txt
python .\2021-2027\prepare_data.py
python -m streamlit run .\2021-2027\streamlit_app.py
```

Testovi:

```powershell
python -m unittest discover -s .\2021-2027 -p "test_*.py"
```

Priprema podataka koristi Python standardnu biblioteku; aplikacija koristi
Streamlit, pandas, Plotly i openpyxl. Rezultati su dostupni kao JSON/CSV za daljnju
integraciju. Trenutna verzija nema javni API, zakazano osvježavanje ni
automatizirano dohvaćanje podataka.

## Usklađenost s kriterijima ocjenjivanja

| Kriterij iz poziva | Dokaz u rješenju / preostali korak tima |
|---|---|
| Upotreba otvorenih podataka (1–5) | Više skupova s kataloškim URL-ovima, izdavačima, licencijama i datumom preuzimanja lokalnih snimki navedenima u dokumentaciji i aplikaciji. |
| Povezivanje javno dostupnih podataka (1–5) | Projekti su povezani sa školskim i visokoobrazovnim registrima; regionalni pokazatelji kombiniraju projekte i registre. Veze su konzervativne i objašnjene. |
| Relevantnost rješenja (1–5) | Analiza podataka za obrazovne ustanove pripada javnim uslugama i informiranju građana. |
| Utjecaj i korist zajednici (1–5) | Karta, usporedba vrsta i koncentracija financiranja olakšavaju uočavanje obrazaca. Za tvrdnje o pristupu potrebni su podaci o prijavama i prihvatljivim ustanovama. |
| Inovativnost i tehnologija (1–5) | Povezivanje više skupova, provjera kvalitete, regionalno normalizirani pokazatelji i preuzimanje podataka daju novu uporabnu vrijednost. Ne tvrdi se da prototip koristi AI ili druge napredne tehnologije. |
| Izvedivost rješenja (1–10) | Pokretljiv Streamlit prototip, ponovljiva priprema podataka i automatizirani testovi. Tim treba demonstrirati lokalno pokretanje i provjeriti sve stranice. |
| Tehnička arhitektura i integracijski potencijal (1–5) | Dokumentirani pipeline i JSON/CSV izlazi. Javni API i automatizirano osvježavanje ostaju mogući nastavak, ne postojeća funkcionalnost. |
| Dojam rješenja (1–5) | Pokazati stvarni prototip i jasno objasniti što karta može, a što ne može zaključiti. |
| Prezentacija rješenja (1–10) | Poziv traži video-prezentaciju od 3 minute. Scenarij je ispod; tim treba snimiti i provjeriti trajanje videa. |

## Predloženi tijek 3-minutnog videa

Ovo je struktura za snimanje stvarne demonstracije, ne zamjena za predani video.

| Vrijeme | Što prikazati i reći |
|---|---|
| 0:00–0:25 | Problem: objavljeni popisi projekata, financija i ustanova postoje odvojeno; teško je vidjeti tko sudjeluje i gdje. |
| 0:25–0:50 | Ukratko prikazati početnu stranicu i objasniti razliku između projektnog popisa 2024.–2026. i agregata prijava 2021.–2026. |
| 0:50–1:20 | Otvoriti kartu. Pokazati broj ustanova u registru, broj s povezanim projektom i udio; naglasiti da to nije mjera pristupa ni uspjeha. |
| 1:20–1:50 | Otvoriti usporedbu vrsta ustanova. Prikazati izdvojene kategorije i objasniti da se kombinirane vrste broje kao zasebna kategorija. |
| 1:50–2:15 | Pokazati koncentraciju financiranja i prebaciti obuhvat sa svih korisnika na pouzdano povezane obrazovne ustanove. |
| 2:15–2:40 | Pokazati stranicu „Podaci i metodologija”: veze s registrima, razlike izvora, ponovljene projektne brojeve i popis projekata. |
| 2:40–3:00 | Sažeti korist, navesti gdje se nalaze kod i dokumentacija te pozvati na nastavak povezivanja izvora. |

## Kontrolni popis prije predaje

Pravila organizatora traže završno rješenje i dokumentaciju, izvorni kod ili
poveznicu na javni repozitorij, korištene skupove podataka s izvorima te demo
materijale (primjerice poveznicu na radni prototip ili snimke zaslona).
Pojedinosti o prijavi tima i roku treba provjeriti u pravilima i javnom pozivu
na [Portalu otvorenih podataka](https://data.gov.hr/uploads/images/2026-10-19/1792415200857_praviladatathonfinal.pdf).

- [x] Navesti kataloške poveznice, izdavače i licence korištenih skupova.
- [x] Zabilježiti da su lokalne izvorne datoteke preuzete 6. 11. 2026. i
  pojasniti da CSV snimke nisu naknadno filtrirane.
- [x] Priložiti lokalne CSV snimke i pripremljene rezultate aplikacije.
- [x] Uključiti kod, README i tehničku dokumentaciju u projektu.
- [x] Ponovno generirati pripremljene podatke i uspješno pokrenuti testove
  (33 testa).
- [ ] Objaviti posljednje izmjene na javnom repozitoriju ili pripremiti izvorni
  kod za dostavu; lokalne izmjene same po sebi organizatorima nisu dostupne.
- [ ] Pripremiti demo materijal za organizatora: javno dostupnu poveznicu na
  pokrenutu aplikaciju ili snimke zaslona. Lokalna provjera nije javni demo.
- [ ] Snimiti i dostaviti 3-minutnu video-prezentaciju iz javnog poziva te
  provjeriti da njezini prikazi i zaključci odgovaraju predanim podacima.
- [ ] Provjeriti da je tim zasebno podnio traženu prijavu za izazov te da su
  naziv tima, izazov i kontakt mentora ispravno navedeni.
- [ ] Provjeriti aktualni rok i način dostave u javnom pozivu prije slanja.
