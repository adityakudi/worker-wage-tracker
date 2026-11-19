import os
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4
import jwt
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash

router = APIRouter(prefix='/auth', tags=['auth'])
hasher = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
dummy_hash = hasher.hash('dummy-password-for-timing')

class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

class Signup(Credentials):
    role: Literal['worker', 'contractor']

def connection():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise HTTPException(503, 'Database not configured')
    return psycopg.connect(url, connect_timeout=3, row_factory=dict_row)

def secret():
    value = os.getenv('JWT_SECRET', '')
    if len(value) < 32:
        raise HTTPException(503, 'Authentication not configured')
    return value

@router.post('/signup', status_code=201)
def signup(body: Signup):
    secret()
    try:
        with connection() as db:
            user = db.execute('INSERT INTO users (id,email,password_hash,role) VALUES (%s,%s,%s,%s) RETURNING id,email,role',
                (str(uuid4()), str(body.email).lower(), hasher.hash(body.password), body.role)).fetchone()
        return user
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, 'Email already registered')

@router.post('/login')
def login(body: Credentials):
    key = secret()
    with connection() as db:
        user = db.execute('SELECT * FROM users WHERE email=%s', (str(body.email).lower(),)).fetchone()
    valid = hasher.verify(body.password, user['password_hash'] if user else dummy_hash)
    if not user or not valid:
        raise HTTPException(401, 'Invalid credentials', headers={'WWW-Authenticate': 'Bearer'})
    now = datetime.now(timezone.utc)
    token = jwt.encode({'sub': str(user['id']), 'iat': now, 'exp': now + timedelta(minutes=30), 'iss': 'worker-wage-tracker', 'aud': 'worker-wage-api'}, key, algorithm='HS256')
    return {'access_token': token, 'token_type': 'bearer'}

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})
    try:
        claims = jwt.decode(credentials.credentials, secret(), algorithms=['HS256'], audience='worker-wage-api', issuer='worker-wage-tracker', options={'require': ['sub','exp','iat']})
    except jwt.InvalidTokenError:
        raise HTTPException(401, 'Invalid token', headers={'WWW-Authenticate': 'Bearer'})
    with connection() as db:
        user = db.execute('SELECT id,email,role FROM users WHERE id::text=%s', (claims['sub'],)).fetchone()
    if not user:
        raise HTTPException(401, 'Invalid token')
    return user

@router.get('/me')
def me(user=Depends(current_user)):
    return user
