from uuid import UUID, uuid4
import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from backend.auth import current_user, connection

router = APIRouter(prefix='/worksites', tags=['worksites'])

def contractor(user=Depends(current_user)):
    if user['role'] != 'contractor':
        raise HTTPException(403, 'Contractor access required')
    return user

class Worksite(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r'\S')
    location: str = Field(default='', max_length=300)
    active: bool = True

@router.post('', status_code=201)
def create(body: Worksite, user=Depends(contractor)):
    with connection() as db:
        return db.execute('INSERT INTO worksites (id,contractor_id,name,location,active) VALUES (%s,%s,%s,%s,%s) RETURNING *', (str(uuid4()),user['id'],body.name.strip(),body.location,body.active)).fetchone()

@router.get('')
def listing(q: str = Query('',max_length=120), active: bool | None = None, limit: int = Query(20,ge=1,le=100), offset: int = Query(0,ge=0), user=Depends(contractor)):
    with connection() as db:
        params=(user['id'],'%'+q+'%',active,active)
        where='contractor_id=%s AND name ILIKE %s AND (%s::boolean IS NULL OR active=%s)'
        total=db.execute('SELECT count(*) AS total FROM worksites WHERE '+where,params).fetchone()['total']
        items=db.execute('SELECT * FROM worksites WHERE '+where+' ORDER BY name,id LIMIT %s OFFSET %s',params+(limit,offset)).fetchall()
        return {'items':items,'total':total,'limit':limit,'offset':offset}

@router.get('/{worksite_id}')
def detail(worksite_id: UUID, user=Depends(contractor)):
    with connection() as db:
        row=db.execute('SELECT * FROM worksites WHERE id=%s AND contractor_id=%s',(worksite_id,user['id'])).fetchone()
    if not row: raise HTTPException(404,'Worksite not found')
    return row

@router.put('/{worksite_id}')
def update(worksite_id: UUID, body: Worksite, user=Depends(contractor)):
    with connection() as db:
        row=db.execute('UPDATE worksites SET name=%s,location=%s,active=%s WHERE id=%s AND contractor_id=%s RETURNING *',(body.name.strip(),body.location,body.active,worksite_id,user['id'])).fetchone()
    if not row: raise HTTPException(404,'Worksite not found')
    return row

@router.delete('/{worksite_id}',status_code=204)
def delete(worksite_id: UUID,user=Depends(contractor)):
    try:
        with connection() as db:
            row=db.execute('DELETE FROM worksites WHERE id=%s AND contractor_id=%s RETURNING id',(worksite_id,user['id'])).fetchone()
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(409,'Worksite has assignments; archive it instead')
    if not row: raise HTTPException(404,'Worksite not found')
