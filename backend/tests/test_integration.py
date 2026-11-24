"""Real PostgreSQL contract checks, isolated inside a disposable unique schema.

Set TEST_DATABASE_URL to run. No tables outside this test's schema are changed.
"""
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient

from backend.main import app
from backend.migrate import migrate


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Set TEST_DATABASE_URL for PostgreSQL integration checks')
class PostgreSQLContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ['TEST_DATABASE_URL']
        cls.schema = 'test_' + uuid4().hex
        with psycopg.connect(cls.url, autocommit=True) as db:
            db.execute(psycopg.sql.SQL('CREATE SCHEMA {}').format(psycopg.sql.Identifier(cls.schema)))
        cls.environment = patch.dict(os.environ, {
            'DATABASE_URL':cls.url, 'JWT_SECRET': 'integration-only-' + uuid4().hex,
            'PGOPTIONS': '-c search_path=' + cls.schema,
        })
        cls.environment.start()
        try:
            cls.first_migrations = migrate(cls.url)
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()
        with psycopg.connect(cls.url, autocommit=True) as db:
            db.execute(psycopg.sql.SQL('DROP SCHEMA {} CASCADE').format(psycopg.sql.Identifier(cls.schema)))

    def setUp(self):
        app.dependency_overrides.clear()
        self.client = TestClient(app)
        # PGOPTIONS makes this reference exclusive to the test schema.
        with psycopg.connect(self.url) as db:
            db.execute('TRUNCATE users CASCADE')
        self.owner, self.owner_headers = self.register('owner@example.com','contractor')
        self.other, self.other_headers = self.register('other@example.com','contractor')
        self.worker, self.worker_headers = self.register('worker@example.com','worker')
        self.stranger, self.stranger_headers = self.register('stranger@example.com','worker')

    def register(self, email, role):
        body = {'email':email,'password':'correct horse battery staple','role':role}
        response = self.client.post('/auth/signup',json=body)
        self.assertEqual(response.status_code,201,response.text)
        user = response.json()
        login = self.client.post('/auth/login',json={'email':email,'password':body['password']})
        self.assertEqual(login.status_code,200,login.text)
        return user, {'Authorization':'Bearer '+login.json()['access_token']}

    def site(self, name='North worksite'):
        response=self.client.post('/worksites',json={'name':name,'location':'Jaipur'},headers=self.owner_headers)
        self.assertEqual(response.status_code,201,response.text)
        return response.json()

    def invite(self):
        response=self.client.post('/memberships',json={'worker_id':self.worker['id']},headers=self.owner_headers)
        self.assertEqual(response.status_code,201,response.text)
        return response.json()

    def test_health_queries_real_database(self):
        self.assertEqual(self.client.get('/health').json(),{'status':'ok','database':'connected'})

    def test_signup_hash_and_authenticated_identity(self):
        self.assertNotIn('password_hash',self.worker)
        with psycopg.connect(self.url) as db:
            stored=db.execute('SELECT password_hash FROM users WHERE id=%s',(self.worker['id'],)).fetchone()[0]
        self.assertTrue(stored.startswith('$argon2'))
        self.assertNotEqual(stored,'correct horse battery staple')
        me=self.client.get('/auth/me',headers=self.worker_headers)
        self.assertEqual(me.status_code,200)
        self.assertEqual(me.json(),self.worker)

    def test_case_normalized_email_duplicate(self):
        response=self.client.post('/auth/signup',json={'email':'OWNER@EXAMPLE.COM','password':'another long password','role':'contractor'})
        self.assertEqual(response.status_code,409)

    def test_wrong_password_and_unknown_user(self):
        for email in ['worker@example.com','unknown@example.com']:
            result=self.client.post('/auth/login',json={'email':email,'password':'not the correct password'})
            self.assertEqual(result.status_code,401)
            self.assertEqual(result.json()['detail'],'Invalid credentials')

    def test_deleted_user_token_denied(self):
        with psycopg.connect(self.url) as db:
            db.execute('DELETE FROM users WHERE id=%s',(self.stranger['id'],))
        self.assertEqual(self.client.get('/auth/me',headers=self.stranger_headers).status_code,401)

    def test_worksite_crud_and_ownership(self):
        site=self.site()
        route='/worksites/'+site['id']
        self.assertEqual(self.client.get(route,headers=self.owner_headers).status_code,200)
        for method,kwargs in [('get',{}),('put',{'json':{'name':'Stolen'}}),('delete',{})]:
            self.assertEqual(getattr(self.client,method)(route,headers=self.other_headers,**kwargs).status_code,404)
        changed=self.client.put(route,json={'name':'Updated','active':False},headers=self.owner_headers)
        self.assertEqual(changed.status_code,200)
        self.assertFalse(changed.json()['active'])
        self.assertEqual(self.client.delete(route,headers=self.owner_headers).status_code,204)
        self.assertEqual(self.client.get(route,headers=self.owner_headers).status_code,404)

    def test_search_filters_pagination_and_owner_isolation(self):
        self.site('Alpha');self.site('Beta');self.site('Gamma')
        page=self.client.get('/worksites?limit=1&offset=1',headers=self.owner_headers).json()
        self.assertEqual(page['total'],3)
        self.assertEqual(page['items'][0]['name'],'Beta')
        found=self.client.get('/worksites?q=Alpha&active=true',headers=self.owner_headers).json()
        self.assertEqual(found['total'],1)
        self.assertEqual(self.client.get('/worksites',headers=self.other_headers).json()['total'],0)

    def test_invitation_is_private_and_only_invitee_accepts(self):
        invited=self.invite()
        route='/memberships/'+invited['id']+'/accept'
        self.assertEqual(self.client.get('/memberships',headers=self.stranger_headers).json()['items'],[])
        self.assertEqual(self.client.get('/memberships',headers=self.other_headers).json()['items'],[])
        self.assertEqual(self.client.post(route,headers=self.stranger_headers).status_code,404)
        accepted=self.client.post(route,headers=self.worker_headers)
        self.assertEqual(accepted.status_code,200)
        self.assertEqual(accepted.json()['status'],'accepted')
        self.assertIsNotNone(accepted.json()['accepted_at'])
        self.assertEqual(self.client.post(route,headers=self.worker_headers).status_code,404)

    def test_duplicate_and_invalid_worker_invitations(self):
        self.invite()
        self.assertEqual(self.client.post('/memberships',json={'worker_id':self.worker['id']},headers=self.owner_headers).status_code,409)
        self.assertEqual(self.client.post('/memberships',json={'worker_id':self.other['id']},headers=self.owner_headers).status_code,404)

    def test_migrations_are_repeatable(self):
        self.assertEqual(migrate(self.url),[])
        with psycopg.connect(self.url) as db:
            names=[row[0] for row in db.execute('SELECT name FROM schema_migrations ORDER BY name')]
        self.assertEqual(names,sorted(p.name for p in Path('backend/migrations').glob('*.sql')))

    def test_database_failure_is_service_unavailable(self):
        with patch.dict(os.environ, {'DATABASE_URL':'postgresql://127.0.0.1:1/missing'}):
            self.assertEqual(self.client.get('/health').status_code,503)
            self.assertEqual(self.client.get('/auth/me',headers=self.owner_headers).status_code,503)
