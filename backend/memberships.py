from uuid import UUID, uuid4
import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from backend.auth import connection, current_user
from backend.worksites import contractor

router=APIRouter(prefix='/memberships',tags=['memberships'])
class Invitation(BaseModel):
    worker_id: UUID

@router.post('',status_code=201)
def invite(body: Invitation,user=Depends(contractor)):
    try:
        with connection() as db:
            worker=db.execute("SELECT id FROM users WHERE id=%s AND role='worker'",(body.worker_id,)).fetchone()
            if not worker: raise HTTPException(404,'Worker not found')
            return db.execute('INSERT INTO memberships(id,contractor_id,worker_id) VALUES(%s,%s,%s) RETURNING *',(str(uuid4()),user['id'],body.worker_id)).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409,'Membership already exists')

@router.get('')
def listing(limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0),user=Depends(current_user)):
    with connection() as db:
        rows=db.execute('SELECT * FROM memberships WHERE contractor_id=%s OR worker_id=%s ORDER BY created_at,id LIMIT %s OFFSET %s',(user['id'],user['id'],limit,offset)).fetchall()
    return {'items':rows,'limit':limit,'offset':offset}

@router.post('/{membership_id}/accept')
def accept(membership_id:UUID,user=Depends(current_user)):
    if user['role']!='worker': raise HTTPException(403,'Worker access required')
    with connection() as db:
        row=db.execute("UPDATE memberships SET status='accepted',accepted_at=now() WHERE id=%s AND worker_id=%s AND status='invited' RETURNING *",(membership_id,user['id'])).fetchone()
    if not row: raise HTTPException(404,'Pending invitation not found')
    return row
