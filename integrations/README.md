# Aktivace nabídek úklidu

Implementace je připravená, ale ve výchozím stavu nic neodesílá.

## Resend
Odesílatel: Chalupa Vernířovice <uklidvernirovice@libertionova.com>.
Reply-To: adam.leitmancik@libertionova.com. Odesílací adresa nepotřebuje placenou
poštovní schránku. Resend sám nevytváří schránku pro příjem odpovědí.

Doména byla přidána v účtu leitmancikadam. Ověření zatím čeká na DNS v Active24.
Přesné aktuální záznamy číst z https://resend.com/domains (nepřebírat obecné příklady):
- TXT resend._domainkey: veřejný DKIM klíč z Resendu.
- CNAME rsend: rsend-euw1.forge.rmta.net
- CNAME send: send.forge.rmta.net
Nepřepisovat stávající MX ani SPF kořenové domény a neoslabovat případný DMARC.
Příjem zpráv v Resendu nezapínat.
V Resendu vytvořit API klíč pouze pro odesílání z této domény. Klíč ukládat
přímo do Script Properties; nevkládat do GitHubu ani do konverzace.

## Koordinátor v Google Apps Script
Vytvořit samostatný Apps Script projekt pro Codex aplikaci a vložit cleaning.gs.
Nepřepisovat skript původní aplikace Claude. Webová aplikace i minutový trigger
musí patřit ke stejnému projektu, aby sdílely ScriptLock.

Script Properties:
- SHEET_ID: 1izUy4AgW32PJFLSL3Cs9xHfLmmPf229FUSz6Z6w0oNM
- APP_URL: https://chalupa-codex.streamlit.app
- API_SECRET: náhodný tajný řetězec alespoň 32 znaků
- TOKEN_SECRET: jiný náhodný tajný řetězec alespoň 32 znaků
- RESEND_API_KEY: omezený Resend klíč

Spustit setup() a autorizovat potřebný přístup k tabulce a odesílacímu API.
setup pouze připraví sloupce/listy a minutový trigger; neodesílá historické pobyty.
Nasadit jako webovou aplikaci vykonávanou pod vlastníkem projektu. Endpoint musí
být dosažitelný ze Streamlit serveru bez Google přihlášení; každá operace je
ověřená API_SECRET. Samotná znalost URL neumožňuje číst ani měnit data.
Resend API klíč a oba tajné řetězce zůstávají výhradně v nastavení.

V Streamlit Secrets přidat [cleaning_mail] podle vzoru, url finálního /exec
nasazení, shodné API_SECRET do secret a enabled = true. Stejné nastavení použít
pro případnou lokální práci se skutečnými daty. Po změně kódu Apps Script vydat
novou verzi existujícího nasazení; nestačí uložit editor.

## Změny tabulky
- Úklid: stávající Jméno a E-mail zůstávají; na konci přibudou E-mailing a
  Odhlášeno dne. Prázdný E-mailing znamená Přihlášeno kvůli původním kontaktům.
  Odhlášeno = vynechat další nabídky, zachovat kontaktní historii a převzaté úklidy.
- Rezervace: používá se existující Úklid - e-mail, dohledaný podle hlavičky.
- Nabídky úklidu: ID nabídky, ID rezervace, Datum úklidu, Vytvořeno.
- E-maily úklidu: ID zprávy, ID nabídky, E-mail, Stav, První pokus, Resend ID, Obsah.
  Obsah je uložený payload pro přesně stejné opakování nejistých odeslání.
  Obsahuje osobní odkazy: nesdílet tuto tabulku veřejně.
Původní data a další sloupce se nemažou ani neposouvají. Při opakovaném setup
nedochází k resetu odhlášení ani k duplicitě triggeru.

## Chování
Změna stavu na Zaplaceno připraví jednu nabídku pro dosud nepřiřazený budoucí
úklid a jednu zprávu pro každý přihlášený unikátní e-mail. Opakované přepnutí
nevytváří další nabídku. Zpětná rozesílka historických zaplacených pobytů se
neprovádí. Frontu průběžně posílá minutový trigger, nejvýše pět zpráv v běhu.

Tlačítko e-mailu otevře Streamlit s podepsaným osobním odkazem. Načtení odkazu
nic nemění. Teprve potvrzení přiřadí kontakt pod společným zámkem. Druhý tým
nemůže přepsat první. Kontroluje se aktuální zaplacení, datum odjezdu, existence
kontaktu, odhlášení a uzávěrka v 11:00 v den úklidu. Změněné datum zneplatní
původní nabídku. Již přiřazený tým nebo zrušená rezervace zabrání dalšímu odesílání.
Samostatné tlačítko Odhlásit z e-mailingu po potvrzení označí kontakt Odhlášeno.

Ruční změny stavů, ruční přiřazení a mazání rezervací v nakonfigurované Codex
aplikaci používají stejný zámek. Přímé ruční zásahy do tabulky a původní aplikace
Claude tento zámek nepoužívají: neupravovat souběžně přiřazení/řádky jinými cestami.
Změny stavu přímo v tabulce nebo v původní aplikaci nerozesílají nabídky.

Resend deduplikuje podle klíče 24 hodin. Stejný obsah a klíč se opakují pouze
v bezpečném okně 23 hodin; pak se nejisté odeslání označí Nutná kontrola.
Stav Odesláno znamená přijetí Resendem, nikoli potvrzené doručení do schránky.
Chyba 4xx kromě limitu 429 vyžaduje kontrolu konfigurace v listu E-maily úklidu.
Limit 429 / dočasná chyba se zkusí při dalším spuštění, bez vytváření nové nabídky.
Odebrání kontaktu za nesplnění standardu je rozhodnutí majitele po kontrole;
není automatické. Znovupřihlášení se zatím provádí vědomou změnou E-mailing na
Přihlášeno v tabulce po žádosti kontaktu.

## Ověření před aktivací
Python: python -m unittest discover -s tests -v
Koordinátor: node tests/test_cleaning_gateway.cjs
Nejdřív otestovat nasazený koordinátor na kopii tabulky a vlastní testovací
adrese. Ověřit přijetí zprávy, potvrzení, druhý tým, odhlášení a neodeslání po něm.
Nesmí se testovat změnou skutečných rezervací nebo rozesílkou skutečným týmům.
Lokální testy nyní prošly; živá rozesílka a produkční setup zatím nejsou provedené.
