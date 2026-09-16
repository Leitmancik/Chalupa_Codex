"""Společná Google tabulka; oddělené SQLite pro vývoj bez připojení."""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import json
import os
import sqlite3
import threading
import time
import uuid

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

from domain import (RES_HEADER, PRICE_HEADER, STATUS, StorageError,
                    parse_date, parse_money, conflict, quote,
                    validate_reservation)


@st.cache_resource
def _lock():
    return threading.RLock()


def config():
    if os.environ.get('CHALUPA_DEMO') == '1':
        return {}
    try:
        return dict(st.secrets)
    except FileNotFoundError:
        return {}


def connected():
    return 'gcp_service_account' in config()


@st.cache_resource(show_spinner=False)
def _document():
    cfg = config()
    if not cfg.get('sheet_id'):
        raise StorageError('V nastavení chybí sheet_id společné tabulky.')
    credentials = Credentials.from_service_account_info(
        dict(cfg['gcp_service_account']),
        scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return gspread.authorize(credentials).open_by_key(cfg['sheet_id'])


@contextmanager
def _errors():
    try:
        yield
    except StorageError:
        raise
    except Exception:
        # Technické výjimky mohou obsahovat přístupové údaje nebo osobní data.
        raise StorageError('Data se nepodařilo načíst nebo uložit. Zkontrolujte '
                           'připojení a sdílení tabulky a zkuste to znovu.') from None


def _sheet(name, header):
    sheet = _document().worksheet(name)
    rows = sheet.get_all_values()
    if not rows or rows[0][:len(header)] != header:
        raise StorageError(f'List {name} nemá očekávané sloupce. '
                           'Strukturu tabulky aplikace automaticky nemění.')
    return sheet, rows[1:]


def _decode_res(rows):
    result = []
    ids = set()
    for row in rows:
        if not any(str(c).strip() for c in row):
            continue
        v = list(row) + [''] * max(0, 9 - len(row))
        start, end = parse_date(v[3]), parse_date(v[4])
        if start is None or end is None or end <= start:
            raise StorageError('Některá rezervace nemá platný příjezd a odjezd. '
                               'Dostupnost nelze bezpečně zobrazit.')
        rid = str(v[6]).strip()
        if rid and rid in ids:
            raise StorageError('Tabulka obsahuje duplicitní ID rezervace.')
        ids.add(rid)
        result.append(dict(first_name=v[0], last_name=v[1], email=v[2],
                           date_from=start, date_to=end,
                           status='confirmed' if v[5] == STATUS['confirmed'] else 'pending',
                           id=rid, created_at=v[7], price=parse_money(v[8])))
    return sorted(result, key=lambda r: r['date_from'])


def _decode_prices(rows):
    result = []
    ids = set()
    for row in rows:
        if not any(str(c).strip() for c in row):
            continue
        v = list(row) + [''] * max(0, 5 - len(row))
        start, end, price = parse_date(v[0]), parse_date(v[1]), parse_money(v[2])
        if ((start is None) != (end is None) or
                (start is not None and end < start) or price is None):
            raise StorageError('Některé cenové období má neplatné datum nebo cenu.')
        rid = str(v[4]).strip()
        if rid and rid in ids:
            raise StorageError('Tabulka obsahuje duplicitní ID cenového období.')
        ids.add(rid)
        result.append(dict(date_from=start, date_to=end, price=price,
                           label=v[3], id=rid))
    if sum(p['date_from'] is None for p in result) > 1:
        raise StorageError('V ceníku je více základních cen. Ponechte pouze jednu.')
    return result


def _db():
    path = Path(os.environ.get('CHALUPA_DB', 'work/reservations.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.execute('CREATE TABLE IF NOT EXISTS records '
               '(kind TEXT, id TEXT PRIMARY KEY, payload TEXT)')
    return db


def _local_rows(kind):
    with _db() as db:
        return [json.loads(row[0]) for row in db.execute(
            'SELECT payload FROM records WHERE kind=? ORDER BY rowid', (kind,))]


def _read(kind):
    with _errors():
        if connected():
            name, header = ('Rezervace', RES_HEADER) if kind == 'res' else ('Cenotvorba', PRICE_HEADER)
            _, rows = _sheet(name, header)
        else:
            rows = _local_rows(kind)
        return _decode_res(rows) if kind == 'res' else _decode_prices(rows)


def _load(kind, force=False):
    key = '_data_' + kind
    cached = st.session_state.get(key)
    if not force and cached and time.monotonic() - cached[0] < 30:
        return cached[1]
    data = _read(kind)
    st.session_state[key] = (time.monotonic(), data)
    return data


def load_reservations(force=False):
    return _load('res', force)


def load_prices(force=False):
    return _load('prices', force)


def refresh():
    for key in ('_data_res', '_data_prices'):
        st.session_state.pop(key, None)


def add_reservation(first, last, email, start, end, expected_price, request_id):
    validate_reservation(first, last, email, start, end)
    with _lock(), _errors():
        if connected():
            sheet, raw = _sheet('Rezervace', RES_HEADER)
            rows = _decode_res(raw)
            if any(r['id'] == request_id for r in rows):
                return request_id
            if conflict(start, end, rows):
                raise StorageError('Termín se mezitím obsadil. Vyberte prosím jiný.')
            price, _ = quote(start, end, load_prices(force=True))
            if price != expected_price:
                raise StorageError('Cena se mezitím změnila. Zkontrolujte nový součet '
                                   'a rezervaci odešlete znovu.')
            values = _reservation_values(first, last, email, start, end, price, request_id)
            try:
                sheet.append_row(values, value_input_option='RAW')
            except Exception:
                # Po ztracené odpovědi neopakujeme zápis naslepo.
                if not any(r['id'] == request_id for r in load_reservations(force=True)):
                    raise StorageError('Uložení nelze ověřit. Obnovte data; '
                                       'při opakování se použije stejné ID.') from None
        else:
            with _db() as db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT 1 FROM records WHERE id=?', (request_id,)).fetchone():
                    return request_id
                raw = [json.loads(r[0]) for r in db.execute(
                    "SELECT payload FROM records WHERE kind='res'")]
                if conflict(start, end, _decode_res(raw)):
                    raise StorageError('Termín se mezitím obsadil. Vyberte prosím jiný.')
                price, _ = quote(start, end, load_prices(force=True))
                if price != expected_price:
                    raise StorageError('Cena se změnila. Zkontrolujte součet a odešlete znovu.')
                values = _reservation_values(first, last, email, start, end, price, request_id)
                db.execute('INSERT INTO records VALUES (?,?,?)',
                           ('res', request_id, json.dumps(values)))
    refresh()
    return request_id


def _reservation_values(first, last, email, start, end, price, rid):
    return [first.strip(), last.strip(), email.strip(), start.isoformat(),
            end.isoformat(), STATUS['pending'], rid,
            datetime.now().astimezone().isoformat(timespec='seconds'),
            '' if price is None else price]


def _mutate(kind, rid, values=None, status=None, delete=False):
    if not rid:
        raise StorageError('Záznam nemá ID; nejprve jej doplňte ve společné tabulce.')
    with _lock(), _errors():
        if connected():
            name, header, col = ('Rezervace', RES_HEADER, 6) if kind == 'res' else ('Cenotvorba', PRICE_HEADER, 4)
            sheet, rows = _sheet(name, header)
            matches = [i + 2 for i, row in enumerate(rows) if len(row) > col and row[col] == rid]
            if len(matches) > 1:
                raise StorageError('ID není jedinečné. Opravte jej prosím v tabulce.')
            if not matches:
                if delete:
                    return
                if values is not None:
                    sheet.append_row(values, value_input_option='RAW')
                else:
                    raise StorageError('Záznam už neexistuje. Obnovte prosím data.')
            elif delete:
                sheet.delete_rows(matches[0])
            elif status:
                sheet.update_cell(matches[0], 6, STATUS[status])
            else:
                sheet.update(range_name=f'A{matches[0]}:E{matches[0]}',
                             values=[values], value_input_option='RAW')
        else:
            with _db() as db:
                if delete:
                    db.execute('DELETE FROM records WHERE id=? AND kind=?', (rid, kind))
                elif status:
                    row = db.execute('SELECT payload FROM records WHERE id=? AND kind=?', (rid, kind)).fetchone()
                    if row is None:
                        raise StorageError('Záznam už neexistuje.')
                    payload = json.loads(row[0])
                    payload[5] = STATUS[status]
                    db.execute('UPDATE records SET payload=? WHERE id=?', (json.dumps(payload), rid))
                else:
                    db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)', (kind, rid, json.dumps(values)))
    refresh()


def set_status(rid, status):
    if status not in STATUS:
        raise StorageError('Neplatný stav rezervace.')
    _mutate('res', rid, status=status)


def delete_reservation(rid):
    _mutate('res', rid, delete=True)


def save_price(rid, start, end, price, label):
    amount = parse_money(price)
    if amount is None or ((start is None) != (end is None)) or (start and end < start):
        raise StorageError('Zkontrolujte cenu a pořadí dat období.')
    prices = load_prices(force=True)
    if start is None:
        existing = next((p for p in prices if p['date_from'] is None), None)
        if existing:
            if not existing['id']:
                raise StorageError('Základní cena nemá ID. Doplňte jej v tabulce.')
            rid = existing['id']
    if rid and not any(p['id'] == rid for p in prices):
        raise StorageError('Období již neexistuje. Obnovte data.')
    rid = rid or uuid.uuid4().hex[:12]
    _mutate('prices', rid, values=[start.isoformat() if start else '',
            end.isoformat() if end else '', amount, label.strip(), rid])


def delete_price(rid):
    _mutate('prices', rid, delete=True)
