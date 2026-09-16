# Předání projektu Chalupa · Codex
Stav k 16. 9. 2026. Tento soubor je souhrn pro pokračování na MacBooku Pro.
Nezačínejte projekt znovu. Aktuální aplikace už existuje, běží a poslední funkce Úklid je hotová.

## Projekt a rozhodnutí uživatele
Adam Leitmancik porovnává samostatnou aplikaci vytvořenou Codexem s původní aplikací vytvořenou Claude Code. Obě používají stejná skutečná data. Uživatelské označení „Excel“ zde znamená Google Sheets.
- Nový soukromý repozitář: https://github.com/Leitmancik/Chalupa_Codex
- Živá aplikace: https://chalupa-codex.streamlit.app/
- Původní projekt: Leitmancik/Reservation_project; na Airu v /Users/adamleitmancik/Desktop/Reservation_project. Neupravovat místo nového projektu.
- Nový projekt na Airu: /Users/adamleitmancik/Documents/Codex/2026-09-16/cht/outputs/chalupa-codex
- Společná tabulka: https://docs.google.com/spreadsheets/d/1izUy4AgW32PJFLSL3Cs9xHfLmmPf229FUSz6Z6w0oNM/edit
- Uživatel chce moderní přívětivé české UX/UI; inspirace Awwwards, Booking, Airbnb. Schválil změny vzhledu a prvků podle úsudku.
- Kalendář přístupný hostům. Výslovně schválil prozatím veřejné všechny sekce bez přihlášení, aby se produkt snáze ladil. Oprávnění až později.
- Nasazení na Streamlit Cloud schváleno a dokončeno. Výslovně schválen přenos existujícího klíče servisního účtu do zabezpečených Secrets nové aplikace.

## Hotové a nasazené funkce
1. Kalendář: dva měsíce, příjezdové/odjezdové půldny, výběr termínu kliknutím i datovými poli, kontrola dostupnosti, žádost o rezervaci se jménem, příjmením a e-mailem, cena s rozpisem nocí.
2. Rezervace: filtrování a hledání, potvrzení, mazání s potvrzením, souhrny, export CSV a XLSX.
3. Cenotvorba: základní cena a sezónní období, jejich přidání, úprava a mazání, upozornění na překryvy.
4. Úklid: záložka /uklid, neutrální název „Úklidový tým“, seznam a hledání osob i firem, přidání jména/názvu a e-mailu. E-mail se kontroluje a duplicitní adresy se odmítají bez ohledu na velikost písmen.
5. U každé rezervace je výběr kontaktu z úklidového týmu. Úklid patří ke dni odjezdu. Přiřazení lze uložit, změnit nebo odebrat volbou Nepřiřazeno.
Vzhled: světlé krémové pozadí, lesní zelená, české texty, responzivní zobrazení. Uživatel chce pokračovat v této aplikaci, nikoli zakládat její další kopii.

## Co výslovně zatím NEDĚLAT
Automatické e-maily a přihlašování na úklid jsou odložené na další zadání. Budoucí představa: po vytvoření rezervace nabídnout všem kontaktům e-mailem možnost úklidu v den odjezdu a umožnit přihlášení. Nyní se žádné takové zprávy neposílají.
Úpravy a mazání kontaktů úklidového týmu nebyly součástí posledního požadavku.

## Data a kompatibilita
List Rezervace zachovává původních devět sloupců v pořadí:
Jméno | Příjmení | email | Datum - Start | Datum - Konec | Stav | ID | Vytvořeno | Cena celkem
Přiřazení úklidu je navíc ve sloupci „Úklid - e-mail“, vyhledávaném podle názvu. Původní sloupce se neposouvají.
List Cenotvorba: Od | Do | Cena za noc | Popis | ID
Nový list Úklid: Jméno | E-mail
Nový list a sloupec již byly ve společné tabulce připraveny. Původní rezervace a cenotvorba zůstaly zachované. Nevkládat testovací kontakty ani rezervace do produkčních dat.
Pouhé čtení nemigruje ani nezakládá listy. Explicitní storage.ensure_cleaning_storage() a první potřebný zápis připraví chybějící strukturu. Další existující sloupce se zachovávají. Zápisy textů používají RAW.
Úklid odkazuje na kontakt e-mailem. Pokud kontakt někdo ručně odstraní z tabulky, aplikace zobrazí původní adresu a umožní přiřazení odebrat.

## Pravidla rezervací a cen
- Příjezd 15:00, odjezd 11:00. Časová zóna Europe/Prague.
- Čekající i potvrzené rezervace blokují termín. Stejnodenní výměna hostů je povolena.
- Překryv intervalů: start < existující konec a existující začátek < end.
- Noci: počáteční datum včetně, odjezd bez noci. Poslední den cenového období zahrnuje noc, která tímto dnem začíná.
- Základní cena má obě data prázdná. Při překryvu cen vítězí kratší období, při stejné délce pořadí v tabulce.
- Uložená cena rezervace je snapshot: pozdější změny ceníku ji nepřepočítávají. Staré chybějící ceny nejsou nula.
- Nové rezervace mají stav „Čeká na potvrzení“ a 12znakové UUID. Potvrzený stav je „Potvrzeno“. Záznam bez ID nelze upravovat.
- Cache 30 sekund se ověřuje při další interakci; Obnovit načte ihned. Před uložením se dostupnost a ceny načtou čerstvě; změněná cena vyžaduje znovu odeslat žádost.
- Google Sheets nemají atomické ověření a zápis. Procesový zámek nechrání proti současnému zápisu původní aplikace. Při přesně souběžných zápisech je možná kolize; mazání řádků může ovlivnit jejich adresování. Pro ostrý provoz bude potřeba společné transakční řešení.

## Technická orientace
Python 3.12, Streamlit 1.63.0, pandas 3.0.5, gspread 6.2.1; ostatní závislosti v requirements.txt.
- streamlit_app.py: navigace a spuštění.
- page_calendar.py, calendar_view.py: kalendář a žádosti.
- page_reservations.py: správa, export, přiřazení úklidu.
- page_pricing.py: cenotvorba.
- page_cleaning.py: úklidový tým.
- domain.py: čistá pravidla a validace.
- storage.py: přístup ke Google Sheets a lokálnímu SQLite.
- ui.py, style.css: vzhled.
- demo.py: místní ukázková data.
- tests/test_app.py, tests/test_cleaning.py: testy.
Tato aplikace používá gspread nebo SQLite; nepřebírat automaticky architekturu Apps Script z původního projektu Claude.

## Tajné údaje a prostředí
Skutečný .streamlit/secrets.toml je ignorovaný Gitem. Obsahuje sheet_id a sekci gcp_service_account. V repozitáři je jen vzor .streamlit/secrets.toml.example.
Cloud už má funkční Secrets. Přesun pracovního počítače nevyžaduje novou aplikaci, novou tabulku ani nový servisní účet.
Lokální tajné údaje přenést samostatně soukromým kanálem, například AirDropem. Nikdy je nevkládat do chatu, dokumentace, archivu ani GitHubu.
Bez přihlašovacích údajů aplikace používá vlastní SQLite ve work/. CHALUPA_DEMO=1 vynutí lokální režim i při existujících Secrets. SQLite není trvalé produkční úložiště na Streamlit Cloud.

## Ověření a poslední změny
Poslední funkční commit: 2af87a2 — Pridat uklidovy tym a prirazeni uklidu k rezervacim.
Předchozí: 2c9da07 — Osetrit starsi cenove zaznamy bez ID a overit validaci.
Základ aplikace: 4e9699f — Vytvorit samostatnou rezervacni aplikaci se spolecnymi daty.
Po dokončení Úklidu prošlo 17 testů a nová stránka byla ověřena na veřejné adrese. Testy používají izolovanou SQLite; produkční testovací záznamy nebyly vytvářeny.
Testy: python -m unittest discover -s tests -v
Git push do origin/main aktualizuje stávající Streamlit aplikaci. Před změnami zkontrolovat git status a zachovat práci uživatele.

## Aktuální předání
Poslední požadavek je přesun kontextu na MacBook Pro. Funkce Úklid je dokončena; není potřeba ji implementovat znovu. Další produktový krok si má zvolit uživatel.
Dostupné textové zprávy jsou v CONVERSATION_EXPORT.md. Nejde o úplný technický export vlákna; výstupy nástrojů, interní záznamy a tajné údaje nejsou zahrnuty. Hlasová část je doplněna odděleným souhrnem.
