"""Participant-scoped attendance, wage postings, statements and disputes."""
import calendar
import csv
from datetime import date, datetime
from io import StringIO
from typing import Annotated, Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import psycopg
from psycopg.types.json import Jsonb
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, BeforeValidator, Field, StrictInt

from backend.assignments import iso_date
from backend.auth import connection, current_user
from backend.wages import BIGINT_MAX, disbursement_paise, earnings_paise
from backend.worksites import contractor

router = APIRouter(tags=['ledger'])
WorkDate = Annotated[date, BeforeValidator(iso_date)]
Note = Annotated[str, Field(max_length=500)]
Units = Annotated[StrictInt, Field(ge=0, le=2)]
Paise = Annotated[StrictInt, Field(ge=-BIGINT_MAX, le=BIGINT_MAX)]

DISPUTE_EVENTS = "('disputed','responded','correction_proposed','response_rejected','resolved')"
STATUS = f"""(SELECT kind FROM ledger_events WHERE entry_id=e.id
                AND kind IN {DISPUTE_EVENTS} ORDER BY id DESC LIMIT 1)"""
ENTRY_FIELDS = f"""e.*, e.amount_paise::text AS exact_amount,
 e.daily_rate_paise::text AS exact_rate, w.name AS worksite_name, {STATUS} AS dispute_status,
 EXISTS (SELECT 1 FROM ledger_entries WHERE reverses_id=e.id) AS reversed,
 EXISTS (SELECT 1 FROM ledger_reviews WHERE entry_id=e.id AND kind='acknowledged') AS acknowledged,
 EXISTS (SELECT 1 FROM ledger_reviews WHERE entry_id=e.id AND kind='receipt_confirmed') AS receipt_confirmed"""
ENTRY_FROM = """FROM ledger_entries e LEFT JOIN assignments a ON a.id=e.assignment_id
 LEFT JOIN worksites w ON w.id=a.worksite_id"""


class Attendance(BaseModel):
    assignment_id: UUID
    work_date: WorkDate
    half_day_units: Units
    notes: Note = ''
    request_id: UUID


class Posting(BaseModel):
    kind: Literal['advance', 'payment', 'adjustment']
    effective_date: WorkDate
    amount_paise: Paise
    notes: Note = ''
    request_id: UUID


class Message(BaseModel):
    reason: Annotated[str, Field(min_length=1, max_length=500)]


class Correction(Message):
    replace_units: Units | None = None
    replace_amount_paise: Paise | None = None


class DisputeResponse(Correction):
    correct: bool = False


class Decision(BaseModel):
    accept: bool
    notes: Note = ''


def today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()


def past_or_today(day):
    if day > today():
        raise HTTPException(422, 'Date cannot be in the future')


def reason_text(value):
    result = value.strip()
    if not result:
        raise HTTPException(422, 'Enter a reason')
    return result


def member(db, membership_id, user, lock=False):
    suffix = ' FOR UPDATE' if lock else ''
    row = db.execute('''SELECT * FROM memberships WHERE id=%s AND status='accepted'
                        AND (contractor_id=%s OR worker_id=%s)''' + suffix,
                     (membership_id, user['id'], user['id'])).fetchone()
    if not row:
        raise HTTPException(404, 'Accepted membership not found')
    return row


def scoped_entry(db, entry_id, user, lock=False):
    suffix = ' FOR UPDATE OF e' if lock else ''
    row = db.execute('''SELECT e.* FROM ledger_entries e JOIN memberships m ON m.id=e.membership_id
          WHERE e.id=%s AND (m.contractor_id=%s OR m.worker_id=%s)''' + suffix,
          (entry_id, user['id'], user['id'])).fetchone()
    if not row:
        raise HTTPException(404, 'Ledger entry not found')
    return row


def serialize(row):
    row['amount_paise'] = str(row.pop('exact_amount', row['amount_paise']))
    rate = row.pop('exact_rate', row.get('daily_rate_paise'))
    row['daily_rate_paise'] = None if rate is None else str(rate)
    return row


def entry_detail(db, entry_id):
    return serialize(db.execute(f'SELECT {ENTRY_FIELDS} {ENTRY_FROM} WHERE e.id=%s',
                                (entry_id,)).fetchone())


def event(db, entry_id, actor, kind, **details):
    db.execute('INSERT INTO ledger_events(entry_id,actor_id,kind,details) VALUES (%s,%s,%s,%s)',
               (entry_id, actor, kind, Jsonb(details)))


def insert_entry(db, membership_id, kind, day, amount, actor, notes, *, assignment_id=None,
                 agreement_id=None, rate=None, units=None, reverses=None, replaces=None,
                 request_id=None):
    entry_id = uuid4()
    db.execute('''INSERT INTO ledger_entries
        (id,membership_id,kind,effective_date,amount_paise,created_by,notes,assignment_id,
         wage_agreement_id,daily_rate_paise,half_day_units,reverses_id,replaces_id,request_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (entry_id, membership_id, kind, day, amount, actor, notes, assignment_id, agreement_id,
         rate, units, reverses, replaces, request_id))
    event(db, entry_id, actor, 'posted')
    if kind == 'earning':
        db.execute('INSERT INTO attendance_slots VALUES (%s,%s,%s)', (membership_id, day, entry_id))
    return entry_id


def previous_request(db, membership_id, request_id, **expected):
    old = db.execute('SELECT * FROM ledger_entries WHERE membership_id=%s AND request_id=%s',
                     (membership_id, request_id)).fetchone()
    if old:
        if any(old[key] != value for key, value in expected.items()):
            raise HTTPException(409, 'This request ID was already used for different details')
        return entry_detail(db, old['id'])
    return None


@router.post('/attendance', status_code=201)
def post_attendance(body: Attendance, user=Depends(contractor)):
    past_or_today(body.work_date)
    with connection() as db:
        assigned = db.execute('''SELECT * FROM assignments WHERE id=%s AND contractor_id=%s FOR UPDATE''',
                              (body.assignment_id, user['id'])).fetchone()
        if not assigned:
            raise HTTPException(404, 'Assignment not found')
        membership_id = assigned['membership_id']
        member(db, membership_id, user, lock=True)
        previous = previous_request(db, membership_id, body.request_id, kind='earning',
                                    assignment_id=body.assignment_id, effective_date=body.work_date,
                                    half_day_units=body.half_day_units, notes=body.notes)
        if previous:
            return previous
        if not assigned['start_date'] <= body.work_date <= (assigned['end_date'] or date.max):
            raise HTTPException(422, 'Attendance date must fall within the assignment')
        if db.execute('SELECT 1 FROM attendance_slots WHERE membership_id=%s AND work_date=%s',
                      (membership_id, body.work_date)).fetchone():
            raise HTTPException(409, 'Attendance already exists for this worker and date')
        rate = db.execute('''SELECT * FROM wage_agreements WHERE assignment_id=%s AND effective_from<=%s
                            ORDER BY effective_from DESC LIMIT 1''',
                          (body.assignment_id, body.work_date)).fetchone()
        if not rate or not rate['acknowledged_at']:
            raise HTTPException(409, 'The latest applicable wage rate needs worker acknowledgement')
        daily_rate = rate['daily_rate_paise']
        entry_id = insert_entry(db, membership_id, 'earning', body.work_date,
                                earnings_paise(daily_rate, body.half_day_units), user['id'], body.notes,
                                assignment_id=body.assignment_id, agreement_id=rate['id'],
                                rate=daily_rate, units=body.half_day_units, request_id=body.request_id)
        return entry_detail(db, entry_id)


def posting_amount(kind, value):
    if kind == 'adjustment':
        if not value:
            raise HTTPException(422, 'Adjustments must be nonzero')
        return value
    if value <= 0:
        raise HTTPException(422, 'Enter a positive disbursement amount')
    return disbursement_paise(value)


@router.post('/memberships/{membership_id}/ledger', status_code=201)
def post_money(membership_id: UUID, body: Posting, user=Depends(contractor)):
    past_or_today(body.effective_date)
    amount = posting_amount(body.kind, body.amount_paise)
    notes = reason_text(body.notes) if body.kind == 'adjustment' else body.notes
    with connection() as db:
        member(db, membership_id, user, lock=True)
        previous = previous_request(db, membership_id, body.request_id, kind=body.kind,
                                    effective_date=body.effective_date, amount_paise=amount, notes=notes)
        if previous:
            return previous
        entry_id = insert_entry(db, membership_id, body.kind, body.effective_date, amount,
                                user['id'], notes, request_id=body.request_id)
        return entry_detail(db, entry_id)


def dispute_state(db, entry_id):
    return db.execute(f'''SELECT kind,details FROM ledger_events WHERE entry_id=%s AND kind IN {DISPUTE_EVENTS}
                         ORDER BY id DESC LIMIT 1''', (entry_id,)).fetchone()


def is_reversed(db, entry_id):
    return db.execute('SELECT 1 FROM ledger_entries WHERE reverses_id=%s', (entry_id,)).fetchone() is not None


def correction_fields(old, units, amount):
    if units is not None and old['kind'] != 'earning':
        raise HTTPException(422, 'Attendance units can only replace an attendance entry')
    if amount is not None and old['kind'] not in ('advance','payment','adjustment'):
        raise HTTPException(422, 'Money can only replace a disbursement or adjustment')
    if amount is not None:
        posting_amount(old['kind'], amount)


def correct_entry(db, old, actor, reason, units=None, amount=None):
    if old['kind'] == 'reversal':
        raise HTTPException(409, 'A reversal cannot itself be reversed')
    if is_reversed(db, old['id']):
        raise HTTPException(409, 'Entry has already been reversed')
    correction_fields(old, units, amount)
    # Keep the effective date and record the real correction timestamp separately.
    reversal = insert_entry(db, old['membership_id'], 'reversal', old['effective_date'],
                            -old['amount_paise'], actor, reason, reverses=old['id'])
    event(db, old['id'], actor, 'reversed', reversal_id=str(reversal), reason=reason)
    replacement = None
    if old['kind'] == 'earning':
        db.execute('DELETE FROM attendance_slots WHERE entry_id=%s', (old['id'],))
        if units is not None:
            replacement = insert_entry(db, old['membership_id'], 'earning', old['effective_date'],
                                       earnings_paise(old['daily_rate_paise'], units), actor, reason,
                                       assignment_id=old['assignment_id'],
                                       agreement_id=old['wage_agreement_id'],
                                       rate=old['daily_rate_paise'], units=units, replaces=old['id'])
    elif amount is not None:
        replacement = insert_entry(db, old['membership_id'], old['kind'], old['effective_date'],
                                   posting_amount(old['kind'], amount), actor, reason, replaces=old['id'])
    return {'reversal_id': reversal, 'replacement_id': replacement}


@router.post('/ledger/{entry_id}/reverse')
def reverse(entry_id: UUID, body: Correction, user=Depends(contractor)):
    with connection() as db:
        old = scoped_entry(db, entry_id, user, lock=True)
        state = dispute_state(db, entry_id)
        if state and state['kind'] != 'resolved':
            raise HTTPException(409, 'Resolve the open dispute before making a separate correction')
        return correct_entry(db, old, user['id'], reason_text(body.reason),
                             body.replace_units, body.replace_amount_paise)


def worker_only(user):
    if user['role'] != 'worker':
        raise HTTPException(403, 'Worker access required')
    return user


@router.post('/ledger/{entry_id}/reviews/{kind}', status_code=201)
def review(entry_id: UUID, kind: Literal['acknowledged','receipt_confirmed'], user=Depends(current_user)):
    worker_only(user)
    with connection() as db:
        old = scoped_entry(db, entry_id, user, lock=True)
        if kind == 'receipt_confirmed' and (old['kind'] not in ('advance','payment') or is_reversed(db, entry_id)):
            raise HTTPException(409, 'Only a current disbursement can be confirmed')
        row = db.execute('''INSERT INTO ledger_reviews(entry_id,kind,worker_id) VALUES (%s,%s,%s)
                            ON CONFLICT DO NOTHING RETURNING *''',
                         (entry_id, kind, user['id'])).fetchone()
        if not row:
            raise HTTPException(409, 'Review already recorded')
        event(db, entry_id, user['id'], kind)
        return row


@router.post('/ledger/{entry_id}/dispute', status_code=201)
def raise_dispute(entry_id: UUID, body: Message, user=Depends(current_user)):
    worker_only(user)
    reason = reason_text(body.reason)
    with connection() as db:
        old = scoped_entry(db, entry_id, user, lock=True)
        if old['kind'] == 'reversal' or is_reversed(db, entry_id):
            raise HTTPException(409, 'Raise a dispute on a current original entry')
        row = db.execute('''INSERT INTO ledger_disputes(entry_id,worker_id,reason) VALUES (%s,%s,%s)
                            ON CONFLICT DO NOTHING RETURNING *''', (entry_id, user['id'], reason)).fetchone()
        if not row:
            raise HTTPException(409, 'This entry already has a dispute history')
        event(db, entry_id, user['id'], 'disputed', reason=reason)
        return row


@router.post('/ledger/{entry_id}/dispute/respond')
def respond(entry_id: UUID, body: DisputeResponse, user=Depends(contractor)):
    reason = reason_text(body.reason)
    if not body.correct and (body.replace_units is not None or body.replace_amount_paise is not None):
        raise HTTPException(422, 'Select correction to propose a replacement')
    with connection() as db:
        old = scoped_entry(db, entry_id, user, lock=True)
        state = dispute_state(db, entry_id)
        if not state or state['kind'] not in ('disputed','response_rejected'):
            raise HTTPException(409, 'Dispute is not waiting for a contractor response')
        correction_fields(old, body.replace_units, body.replace_amount_paise)
        status = 'correction_proposed' if body.correct else 'responded'
        event(db, entry_id, user['id'], status, reason=reason, replace_units=body.replace_units,
              replace_amount_paise=None if body.replace_amount_paise is None else str(body.replace_amount_paise))
        return {'status': status}


@router.post('/ledger/{entry_id}/dispute/decide')
def decide(entry_id: UUID, body: Decision, user=Depends(current_user)):
    worker_only(user)
    with connection() as db:
        old = scoped_entry(db, entry_id, user, lock=True)
        state = dispute_state(db, entry_id)
        if not state or state['kind'] not in ('responded','correction_proposed'):
            raise HTTPException(409, 'Dispute is not waiting for a worker decision')
        status = 'resolved' if body.accept else 'response_rejected'
        if body.accept and state['kind'] == 'correction_proposed':
            proposed = state['details']
            amount = proposed['replace_amount_paise']
            links = correct_entry(db, old, user['id'], proposed['reason'], proposed['replace_units'],
                                  None if amount is None else int(amount))
            event(db, entry_id, user['id'], status, notes=body.notes,
                  **{key: str(value) if value else None for key, value in links.items()})
        else:
            event(db, entry_id, user['id'], status, notes=body.notes)
        return {'status': status}


@router.get('/ledger/{entry_id}')
def detail(entry_id: UUID, user=Depends(current_user)):
    with connection() as db:
        scoped_entry(db, entry_id, user)
        output = entry_detail(db, entry_id)
        output['history'] = db.execute('''SELECT actor_id,kind,details,created_at FROM ledger_events
                                          WHERE entry_id=%s ORDER BY id''', (entry_id,)).fetchall()
        return output


PERIOD_TOTALS = '''SELECT
 COALESCE(sum(amount_paise) FILTER (WHERE effective_date < %s),0) AS opening_paise,
 COALESCE(sum(amount_paise) FILTER (WHERE effective_date >= %s AND kind='earning'),0) AS earnings_paise,
 -COALESCE(sum(amount_paise) FILTER (WHERE effective_date >= %s AND kind='advance'),0) AS advances_paise,
 -COALESCE(sum(amount_paise) FILTER (WHERE effective_date >= %s AND kind='payment'),0) AS payments_paise,
 COALESCE(sum(amount_paise) FILTER (WHERE effective_date >= %s AND kind IN ('adjustment','reversal')),0) AS adjustments_paise,
 COALESCE(sum(amount_paise),0) AS closing_paise
 FROM ledger_entries WHERE membership_id=%s AND effective_date<=%s'''


def period_totals(db, membership_id, start, end):
    result = db.execute(PERIOD_TOTALS, (start,) * 5 + (membership_id, end)).fetchone()
    return {name: str(value) for name, value in result.items()}


@router.get('/memberships/{membership_id}/ledger')
def listing(membership_id: UUID, start: date | None = None, end: date | None = None,
            q: str = Query('', max_length=120), limit: int = Query(20, ge=1, le=100),
            offset: int = Query(0, ge=0), user=Depends(current_user)):
    now = today()
    start = start or now.replace(day=1)
    end = end or now
    if start > end:
        raise HTTPException(422, 'Start date must be on or before end date')
    where = ''' WHERE e.membership_id=%s AND e.effective_date BETWEEN %s AND %s
                AND concat_ws(' ',e.kind,e.notes,w.name) ILIKE %s'''
    values = (membership_id, start, end, '%' + q + '%')
    with connection() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        member(db, membership_id, user)
        total = db.execute('SELECT count(*) AS count ' + ENTRY_FROM + where, values).fetchone()['count']
        rows = db.execute('SELECT ' + ENTRY_FIELDS + ' ' + ENTRY_FROM + where +
                          ' ORDER BY e.effective_date DESC,e.created_at DESC,e.id DESC LIMIT %s OFFSET %s',
                          values + (limit, offset)).fetchall()
        return {'items': [serialize(row) for row in rows], 'total': total,
                'totals': period_totals(db, membership_id, start, end), 'limit': limit, 'offset': offset}


def csv_text(value):
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t','\r','\n')) else value


@router.get('/memberships/{membership_id}/statement.csv')
def statement(membership_id: UUID, month: str = Query(pattern=r'^\d{4}-(0[1-9]|1[0-2])$'),
              user=Depends(current_user)):
    try:
        start = date.fromisoformat(month + '-01')
    except ValueError:
        raise HTTPException(422, 'Invalid statement month')
    end = start.replace(day=calendar.monthrange(start.year, start.month)[1])
    output = StringIO(newline='')
    writer = csv.writer(output)
    with connection() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        member(db, membership_id, user)
        totals = period_totals(db, membership_id, start, end)
        writer.writerow(totals.keys())
        writer.writerow(totals.values())
        writer.writerow([])
        writer.writerow(('date','type','signed_amount_paise','notes','entry_id','reverses_id','replaces_id','dispute_status'))
        rows = db.execute(f'''SELECT e.*, {STATUS} AS dispute_status FROM ledger_entries e
         WHERE e.membership_id=%s AND e.effective_date BETWEEN %s AND %s
         ORDER BY e.effective_date,e.created_at,e.id''', (membership_id, start, end))
        for row in rows:
            writer.writerow((row['effective_date'], row['kind'], row['amount_paise'], csv_text(row['notes']),
                             row['id'], row['reverses_id'], row['replaces_id'], row['dispute_status']))
    return Response(content=output.getvalue(), media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="wages-{month}.csv"',
                             'Cache-Control': 'no-store'})
