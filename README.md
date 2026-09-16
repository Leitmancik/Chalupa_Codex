# Chalupa · Codex

Samostatná česká Streamlit aplikace pro jednu chalupu. Nový projekt a rozhraní,
společná Google tabulka s původní aplikací `Reservation_project`.

## Co je hotové

- Veřejný dvouměsíční kalendář, příjezdové a odjezdové půldny, výběr termínu.
- Formulář žádosti s cenou a rozpisem jednotlivých nocí.
- Správa rezervací, filtrování, potvrzování a mazání s potvrzovacím dialogem.
- Export vyfiltrovaných rezervací do CSV a Excelu.
- Základní cena a úpravy sezónních cenových období.
- České rozhraní, mobilní rozložení, samostatný místní režim pro testování.

Přihlášení se podle zadání řeší až po doladění produktu. Stránky správy jsou
zatím dostupné každému, kdo aplikaci otevře. E-maily se automaticky neodesílají.

## Spuštění

Python 3.12:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Konfigurace společné tabulky je v `.streamlit/secrets.toml`. Vzor je vedle ní
v souboru `secrets.toml.example`. Použijte stejné `sheet_id` a servisní účet
jako v původní aplikaci. Skutečné klíče jsou ignorované Gitem.

Bez servisního účtu aplikace používá vlastní SQLite v `work/`. Nečte databázi
původní aplikace. SQLite na Streamlit Cloudu není trvalé úložiště.

Ukázková data a běh bez jakéhokoliv přístupu ke společné tabulce:

```sh
python demo.py
CHALUPA_DEMO=1 streamlit run streamlit_app.py
```

`CHALUPA_DB` může určit jinou cestu k testovací databázi.

## Nasazení na Streamlit Community Cloud

1. Použijte samostatný GitHub repozitář tohoto projektu, větev `main`.
2. Vytvořte novou aplikaci, vstupní soubor `streamlit_app.py`, Python 3.12.
3. V Advanced settings / Secrets vložte obsah lokálního
   `.streamlit/secrets.toml`. Klíče nevkládejte do repozitáře.
4. Spusťte nasazení a ověřte načtení kalendáře.

## Kompatibilita společných dat

Aplikace při čtení nezakládá listy a neprovádí migrace ani zápisy.
Očekává existující hlavičky, další sloupce na konci povoluje:

- `Rezervace`: Jméno | Příjmení | email | Datum - Start | Datum - Konec |
  Stav | ID | Vytvořeno | Cena celkem
- `Cenotvorba`: Od | Do | Cena za noc | Popis | ID

Nové rezervace používají stav `Čeká na potvrzení` a 12znakové UUID ID.
Čekající i potvrzené rezervace blokují termín. Navazující pobyty se nepřekrývají.
Cena uložená u rezervace se později nepřepočítává. Staré prázdné ceny se
nezaměňují s nulou. Základní cena má obě data prázdná; při překryvu vyhraje
kratší cenové období, při shodné délce pořadí řádků v tabulce stejně jako
v původní aplikaci. Poslední den cenového období zahrnuje začínající noc.

Cache v relaci má 30 sekund a kontroluje se při dalším kliknutí. Tlačítko
Obnovit načte změny ihned. Před uložením žádosti se rezervace a ceník načtou
přímo z Google Sheets, bez cache. Změna ceny vyžaduje znovu odeslat žádost.
Zápis používá RAW, takže text hosta není vyhodnocován jako vzorec.

## Známé hranice současného řešení

Google Sheets neposkytují atomickou transakci „ověřit volno a zapsat“. Zámek
v nové aplikaci brání souběhu jejích vlastních zápisů v jednom procesu,
ale nezamyká původní aplikaci. Přesně současné zápisy z obou aplikací mohou
stále vytvořit kolizi. Pro ostrý provoz je potřeba společná transakční
služba/zámek používaný oběma aplikacemi. Také souběžné mazání řádků a úpravy
z jiné aplikace mohou ovlivnit adresování řádků Google Sheets.

Neplatný rezervovaný interval v tabulce zastaví dostupnost místo toho, aby se
skrytě přeskočil. Záznamy bez ID jsou viditelné, ale nelze je v aplikaci upravit.

Před veřejným ostrým provozem zbývá doplnit přihlášení majitele a oddělit
oprávnění veřejného kalendáře od správy. Zatím jde o vývojovou verzi dle zadání.

## Testy

```sh
python -m unittest discover -s tests -v
```

Testy vždy vynucují místní režim a dočasnou databázi. Obsahují doménová pravidla,
snapshot ceny, idempotenci, čerstvou kontrolu před zápisem a interakční test
Streamlit AppTest: výběr termínu → žádost → potvrzení → vykreslení cenotvorby.
Živé připojení bylo ověřeno pouze čtením; zkušební zápisy do společné tabulky
nebyly provedeny.

## Soubory

- `streamlit_app.py`: spuštění, navigace, společná hlavička.
- `page_*.py`: veřejná stránka a správa.
- `calendar_view.py`, `ui.py`, `style.css`: komponenty a vzhled.
- `domain.py`: pravidla kalendáře, cen a validace.
- `storage.py`: jediný vstup k datům (Google Sheets nebo místní SQLite).
- `tests/test_app.py`: automatické ověření.

Použité Streamlit API: [oficiální dokumentace](https://docs.streamlit.io/develop/api-reference).
