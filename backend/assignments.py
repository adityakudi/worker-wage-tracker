"""Participant-scoped assignments and explicit worker acknowledgement of wage terms."""
from datetime import date
import re
from uuid import UUID, uuid4

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StrictInt, field_validator, model_validator

from backend.auth import connection, current_user
from backend.worksites import contractor

router = APIRouter(tags=['assignments'])


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Use a calendar date in YYYY-MM-DD format')
    return date.fromisoformat(value)


class Assignment(BaseModel):
    membership_id: UUID
    worksite_id: UUID
    start_date: date
    end_date: date | None = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def validate_date(cls, value):
        return None if value is None else iso_date(value)

    @model_validator(mode='after')
    def date_order(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError('End date precedes start date')
        return self


class WageProposal(BaseModel):
    daily_rate_paise: StrictInt = Field(gt=0, le=2**63 - 1)
    effective_from: date

    @field_validator('effective_from', mode='before')
    @classmethod
    def validate_date(cls, value):
        return iso_date(value)


ASSIGNMENT_SELECT = '''SELECT a.*, w.name AS worksite_name, m.worker_id
 FROM assignments a JOIN memberships m ON m.id=a.membership_id
 JOIN worksites w ON w.id=a.worksite_id'''
PARTICIPANT = '(a.contractor_id=%s OR m.worker_id=%s)'


def visible_assignment(db, assignment_id, user):
    row = db.execute(ASSIGNMENT_SELECT + ' WHERE a.id=%s AND ' + PARTICIPANT,
                     (assignment_id, user['id'], user['id'])).fetchone()
    if not row:
        raise HTTPException(404, 'Assignment not found')
    return row


@router.post('/assignments', status_code=201)
def create(body: Assignment, user=Depends(contractor)):
    with connection() as db:
        member = db.execute('SELECT status FROM memberships WHERE id=%s AND contractor_id=%s FOR SHARE',
                            (body.membership_id, user['id'])).fetchone()
        site = db.execute('SELECT active FROM worksites WHERE id=%s AND contractor_id=%s FOR SHARE',
                          (body.worksite_id, user['id'])).fetchone()
        if not member or not site:
            raise HTTPException(404, 'Membership or worksite not found')
        if member['status'] != 'accepted':
            raise HTTPException(409, 'Worker must accept the invitation first')
        if not site['active']:
            raise HTTPException(409, 'Worksite is inactive')
        return db.execute('''INSERT INTO assignments(id,contractor_id,membership_id,worksite_id,start_date,end_date)
          VALUES(%s,%s,%s,%s,%s,%s) RETURNING *''',
          (uuid4(), user['id'], body.membership_id, body.worksite_id, body.start_date, body.end_date)).fetchone()


@router.get('/assignments')
def listing(q: str = Query('', max_length=120), membership_id: UUID | None = None,
            worksite_id: UUID | None = None, limit: int = Query(20, ge=1, le=100),
            offset: int = Query(0, ge=0), user=Depends(current_user)):
    where = PARTICIPANT + ''' AND w.name ILIKE %s
      AND (%s::uuid IS NULL OR a.membership_id=%s)
      AND (%s::uuid IS NULL OR a.worksite_id=%s)'''
    params = (user['id'], user['id'], '%' + q + '%', membership_id, membership_id, worksite_id, worksite_id)
    with connection() as db:
        total = db.execute('SELECT count(*) AS total FROM (' + ASSIGNMENT_SELECT + ' WHERE ' + where + ') found', params).fetchone()['total']
        items = db.execute(ASSIGNMENT_SELECT + ' WHERE ' + where + ' ORDER BY a.start_date,a.id LIMIT %s OFFSET %s',
                           params + (limit, offset)).fetchall()
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}


@router.get('/assignments/{assignment_id}')
def detail(assignment_id: UUID, user=Depends(current_user)):
    with connection() as db:
        return visible_assignment(db, assignment_id, user)


@router.get('/assignments/{assignment_id}/wage-agreements')
def wages(assignment_id: UUID, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
          user=Depends(current_user)):
    with connection() as db:
        visible_assignment(db, assignment_id, user)
        total = db.execute('SELECT count(*) AS total FROM wage_agreements WHERE assignment_id=%s', (assignment_id,)).fetchone()['total']
        items = db.execute('SELECT *, daily_rate_paise::text AS daily_rate_paise_text FROM wage_agreements WHERE assignment_id=%s ORDER BY effective_from,id LIMIT %s OFFSET %s',
                           (assignment_id, limit, offset)).fetchall()
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}


@router.post('/assignments/{assignment_id}/wage-agreements', status_code=201)
def propose(assignment_id: UUID, body: WageProposal, user=Depends(contractor)):
    try:
        with connection() as db:
            assigned = db.execute('SELECT * FROM assignments WHERE id=%s AND contractor_id=%s FOR UPDATE',
                                  (assignment_id, user['id'])).fetchone()
            if not assigned:
                raise HTTPException(404, 'Assignment not found')
            return db.execute('''INSERT INTO wage_agreements(id,assignment_id,daily_rate_paise,effective_from)
              VALUES(%s,%s,%s,%s) RETURNING *''',
              (uuid4(), assignment_id, body.daily_rate_paise, body.effective_from)).fetchone()
    except (psycopg.errors.UniqueViolation, psycopg.errors.CheckViolation):
        raise HTTPException(409, 'Rate date must be inside the assignment and later than existing proposals')


@router.post('/wage-agreements/{agreement_id}/acknowledge')
def acknowledge(agreement_id: UUID, user=Depends(current_user)):
    if user['role'] != 'worker':
        raise HTTPException(403, 'Worker access required')
    with connection() as db:
        # Lock the assignment before the agreement, matching proposal/trigger lock order.
        assigned = db.execute('''SELECT a.id FROM assignments a
          JOIN memberships m ON m.id=a.membership_id
          JOIN wage_agreements g ON g.assignment_id=a.id
          WHERE g.id=%s AND m.worker_id=%s FOR UPDATE OF a''', (agreement_id, user['id'])).fetchone()
        if not assigned:
            raise HTTPException(404, 'Wage agreement not found')
        row = db.execute('''UPDATE wage_agreements SET acknowledged_at=now(),acknowledged_by=%s
          WHERE id=%s AND acknowledged_at IS NULL RETURNING *''', (user['id'], agreement_id)).fetchone()
        if not row:
            raise HTTPException(409, 'Wage agreement already acknowledged')
        return row
