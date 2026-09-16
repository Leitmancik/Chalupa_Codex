"""Správa rezervací a export aktuálně vyfiltrovaných záznamů."""
from html import escape
from io import BytesIO
import pandas as pd
import streamlit as st
import storage
from domain import STATUS, StorageError, date_label, money, today, nights_label
import ui


@st.dialog('Smazat rezervaci?')
def remove(reservation):
    st.write(f"{reservation['first_name']} {reservation['last_name']} · "
             f"{date_label(reservation['date_from'])} – {date_label(reservation['date_to'])}")
    st.write('Rezervace se odstraní i ze společné tabulky a termín se uvolní v obou aplikacích.')
    if st.button('Ano, smazat rezervaci', type='primary', width='stretch'):
        try:
            storage.delete_reservation(reservation['id'])
        except StorageError as error:
            st.error(str(error))
        else:
            ui.flash('Rezervace byla smazána a termín je opět volný.')
            st.rerun()


def safe_cell(value):
    # Export nesmí z textů hosta vytvářet vzorce při otevření v Excelu.
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def export_frame(rows):
    columns = ['Jméno', 'Příjmení', 'E-mail', 'Příjezd', 'Odjezd', 'Nocí', 'Stav', 'Cena celkem', 'ID']
    return pd.DataFrame([
        [safe_cell(r['first_name']), safe_cell(r['last_name']), safe_cell(r['email']),
         r['date_from'].isoformat(), r['date_to'].isoformat(),
         (r['date_to']-r['date_from']).days, STATUS[r['status']], r['price'], safe_cell(r['id'])]
        for r in rows], columns=columns)


def render():
    ui.heading('PRO MAJITELE / REZERVACE', 'Všechny pobyty. Na jednom místě.',
               'Potvrďte nové žádosti a mějte přehled o tom, kdo přijede příště.')
    ui.admin_note()
    ui.show_flash()
    if st.button('Obnovit data', icon=':material/refresh:', type='tertiary'):
        storage.refresh()
    try:
        rows = storage.load_reservations()
    except StorageError as error:
        st.error(str(error))
        return
    confirmed = [r for r in rows if r['status'] == 'confirmed']
    pending = sum(r['status'] == 'pending' for r in rows)
    missing = sum(r['price'] is None for r in confirmed)
    revenue = sum(r['price'] or 0 for r in confirmed)
    coming = sum(r['date_to'] > today() for r in rows)
    st.html('<div class="metric-grid">'
            f'<div class="metric-card"><small>Čeká na potvrzení</small><strong>{pending}</strong><span>žádosti k vyřízení</span></div>'
            f'<div class="metric-card"><small>Nadcházející a probíhající</small><strong>{coming}</strong><span>pobyty v kalendáři</span></div>'
            f'<div class="metric-card"><small>Hodnota potvrzených pobytů</small><strong>{money(revenue)}</strong><span>všechny potvrzené · {missing} bez uložené ceny</span></div></div>')
    filters = st.columns([2, 1, 1])
    search = filters[0].text_input('Hledat hosta', placeholder='Jméno, e-mail nebo kód rezervace')
    status = filters[1].selectbox('Stav', ['Všechny stavy', 'Čeká na potvrzení', 'Potvrzeno'])
    period = filters[2].selectbox('Období', ['Nadcházející a probíhající', 'Všechny pobyty', 'Minulé pobyty'])
    filtered = [r for r in rows if (
        (not search or search.casefold() in f"{r['first_name']} {r['last_name']} {r['email']} {r['id']}".casefold())
        and (status == 'Všechny stavy' or STATUS[r['status']] == status)
        and (period == 'Všechny pobyty' or (r['date_to'] > today()) == (period == 'Nadcházející a probíhající')))]
    st.caption(f'Zobrazeno {len(filtered)} z {len(rows)} rezervací · Souhrny nahoře zahrnují všechny záznamy.')
    if not filtered:
        st.info('Žádné rezervace pro tento výběr. Zkuste upravit filtry.')
    for i, r in enumerate(filtered):
        with st.container(border=True):
            cols = st.columns([2, 2, 1.2, 1.5])
            cols[0].html(f'<p class="res-title">{escape(r["first_name"])} {escape(r["last_name"])}</p>'
                         f'<p class="res-detail">{escape(r["email"])}<br>#{escape(r["id"] or "bez ID")}</p>')
            cols[1].html(f'<p class="res-title">{date_label(r["date_from"])} → {date_label(r["date_to"])}</p>'
                         f'<p class="res-detail">{nights_label((r["date_to"]-r["date_from"]).days)} · {money(r["price"])}</p>')
            cols[2].html(ui.badge(STATUS[r['status']], 'amber' if r['status'] == 'pending' else 'green'))
            with cols[3]:
                try:
                    if r['status'] == 'pending' and st.button('Potvrdit', key=f'confirm_{i}',
                                                            disabled=not r['id'], width='stretch'):
                        storage.set_status(r['id'], 'confirmed')
                        ui.flash('Rezervace byla potvrzena.')
                        st.rerun()
                    if st.button('Smazat', key=f'delete_{i}', type='tertiary', disabled=not r['id'], width='stretch'):
                        remove(r)
                except StorageError as error:
                    st.error(str(error))
    if filtered:
        frame = export_frame(filtered)
        with st.expander('Exportovat zobrazené rezervace'):
            csv = frame.to_csv(index=False, sep=';').encode('utf-8-sig')
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                frame.to_excel(writer, sheet_name='Rezervace', index=False)
                sheet = writer.sheets['Rezervace']
                sheet.freeze_panes = 'A2'
                sheet.auto_filter.ref = sheet.dimensions
                from openpyxl.styles import Font, PatternFill
                for cell in sheet[1]:
                    cell.font = Font(bold=True, color='FFFFFF')
                    cell.fill = PatternFill('solid', fgColor='234D40')
                for column in sheet.columns:
                    sheet.column_dimensions[column[0].column_letter].width = min(45, max(len(str(c.value or '')) for c in column) + 3)
            a, b = st.columns(2)
            a.download_button('Stáhnout Excel', output.getvalue(), 'rezervace.xlsx',
                              mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', width='stretch')
            b.download_button('Stáhnout CSV', csv, 'rezervace.csv', mime='text/csv', width='stretch')
