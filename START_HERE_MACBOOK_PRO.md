# Pokračování na MacBooku Pro
Projekt je hotový a nasazený: https://chalupa-codex.streamlit.app/
Repozitář je soukromý: https://github.com/Leitmancik/Chalupa_Codex

## Nejrychlejší postup
1. Na MacBooku Pro se přihlaste ke GitHubu účtem s přístupem k repozitáři.
2. Stáhněte/klonujte repozitář Chalupa_Codex. Pokud ho už máte, stáhněte aktuální změny.
3. Otevřete složku projektu v Codexu a vložte zadání níže. Pokud používáte běžný ChatGPT, přiložte PROJECT_CONTEXT.md a CONVERSATION_EXPORT.md; pro úpravy kódu otevřete projekt v Codexu.
4. Existující aplikace na Streamlit Cloud zůstává beze změny. Nemusíte znovu nasazovat nový projekt.

## Zadání ke zkopírování do Codexu
> Pokračujeme v existující aplikaci Chalupa · Codex z MacBooku Air. Repozitář je https://github.com/Leitmancik/Chalupa_Codex, živá aplikace https://chalupa-codex.streamlit.app/. Přečti PROJECT_CONTEXT.md, README.md a podle potřeby CONVERSATION_EXPORT.md. Zkontroluj aktuální stav repozitáře. Nezakládej novou aplikaci ani tabulku. Kalendář, rezervace, cenotvorba i Úklidový tým s přiřazením k rezervaci už jsou hotové. Vše je zatím veřejné podle mého rozhodnutí. Automatické e-maily zatím nedělej. Zachovej společná produkční data a klíče mimo Git. Stručně potvrď, že znáš stav, a počkej na moje další zadání.

## Místní spuštění pro vývoj
Vyžaduje Python 3.12. V terminálu:
```sh
git clone https://github.com/Leitmancik/Chalupa_Codex.git
cd Chalupa_Codex
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python demo.py
CHALUPA_DEMO=1 python -m streamlit run streamlit_app.py
```
Pokud už repozitář máte, neklonujte ho znovu. Příkazy pro demo pracují s místní databází.

Pro lokální práci se skutečnou společnou tabulkou přeneste soukromě z Airu soubor:
`/Users/adamleitmancik/Documents/Codex/2026-09-16/cht/outputs/chalupa-codex/.streamlit/secrets.toml`
do stejné relativní cesty v novém projektu. Není v GitHubu ani přiloženém ZIPu. Následně spusťte aplikaci bez CHALUPA_DEMO=1. Cloud má Secrets již nastavené.

Testy:
```sh
python -m unittest discover -s tests -v
```

## Co se přenáší
PROJECT_CONTEXT.md obsahuje rozhodnutí, architekturu, datové schéma, hotové funkce a odložené požadavky. CONVERSATION_EXPORT.md obsahuje dostupné textové zprávy a souhrn hlasové části. To umožní pokračovat v práci, ale neimportuje automaticky původní vlákno do historie aplikace na druhém počítači.
