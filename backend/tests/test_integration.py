"""Real PostgreSQL contract checks, isolated inside a disposable unique schema.

Set TEST_DATABASE_URL to run. No tables outside this test's schema are changed.
"""
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

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

    def assignment(self, site=None):
        site = site or self.site()
        member = self.invite()
        self.assertEqual(self.client.post('/memberships/'+member['id']+'/accept', headers=self.worker_headers).status_code, 200)
        response = self.client.post('/assignments', headers=self.owner_headers, json={
            'membership_id': member['id'], 'worksite_id': site['id'],
            'start_date': '2026-11-17', 'end_date': '2026-12-31',
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def proposal(self, assigned, effective='2026-11-17', rate=60000):
        response = self.client.post('/assignments/'+assigned['id']+'/wage-agreements', headers=self.owner_headers,
                                    json={'effective_from': effective, 'daily_rate_paise': rate})
        self.assertEqual(response.status_code, 201, response.text)
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

    def test_assignments_require_accepted_membership_and_owned_active_site(self):
        site = self.site()
        member = self.invite()
        body = {'membership_id': member['id'], 'worksite_id': site['id'], 'start_date': '2026-11-17'}
        self.assertEqual(self.client.post('/assignments', json=body, headers=self.owner_headers).status_code, 409)
        self.client.post('/memberships/'+member['id']+'/accept', headers=self.worker_headers)
        self.assertEqual(self.client.post('/assignments', json=body, headers=self.other_headers).status_code, 404)
        self.assertEqual(self.client.post('/assignments', json=body, headers=self.worker_headers).status_code, 403)
        bad_end = self.client.post('/assignments', json={**body, 'end_date':'2026-11-16'}, headers=self.owner_headers)
        self.assertEqual(bad_end.status_code, 422)
        self.assertEqual(self.client.post('/assignments', json={**body, 'start_date':1794873600}, headers=self.owner_headers).status_code, 422)
        self.client.put('/worksites/'+site['id'], json={'name':'Archived', 'active':False}, headers=self.owner_headers)
        self.assertEqual(self.client.post('/assignments', json=body, headers=self.owner_headers).status_code, 409)

    def test_assignment_visibility_search_filters_and_pagination(self):
        assigned = self.assignment()
        second = self.client.post('/assignments', headers=self.owner_headers, json={
            'membership_id': assigned['membership_id'], 'worksite_id': assigned['worksite_id'], 'start_date':'2026-11-18'})
        self.assertEqual(second.status_code, 201, second.text)
        for headers in (self.owner_headers, self.worker_headers):
            page = self.client.get('/assignments?q=North&limit=1&offset=1', headers=headers).json()
            self.assertEqual(page['total'], 2)
            self.assertEqual(page['items'][0]['id'], second.json()['id'])
            filtered = self.client.get('/assignments?membership_id='+assigned['membership_id'], headers=headers).json()
            self.assertEqual(filtered['total'], 2)
            self.assertEqual(self.client.get('/assignments/'+assigned['id'], headers=headers).status_code, 200)
        for headers in (self.other_headers, self.stranger_headers):
            self.assertEqual(self.client.get('/assignments', headers=headers).json()['total'], 0)
            self.assertEqual(self.client.get('/assignments/'+assigned['id'], headers=headers).status_code, 404)

    def test_wage_proposals_require_strict_money_dates_and_owner(self):
        assigned = self.assignment()
        route = '/assignments/'+assigned['id']+'/wage-agreements'
        body = {'daily_rate_paise':60000, 'effective_from':'2026-11-17'}
        for bad in (True, 60000.0, 60000.5, '60000', 0, -1, 2**63):
            self.assertEqual(self.client.post(route, headers=self.owner_headers, json={**body,'daily_rate_paise':bad}).status_code, 422)
        for bad in ('2026-02-30', '2026-11-17T00:00:00', '20261117', 1794873600):
            self.assertEqual(self.client.post(route, headers=self.owner_headers, json={**body,'effective_from':bad}).status_code, 422)
        self.assertEqual(self.client.post(route, headers=self.other_headers, json=body).status_code, 404)
        self.assertEqual(self.client.post(route, headers=self.worker_headers, json=body).status_code, 403)
        for bad in ('2026-11-16', '2027-01-01'):
            self.assertEqual(self.client.post(route, headers=self.owner_headers, json={**body,'effective_from':bad}).status_code, 409)
        first = self.proposal(assigned)
        self.assertIsNone(first['acknowledged_at'])
        self.assertIsNone(first['acknowledged_by'])
        self.assertEqual(self.client.post(route, headers=self.owner_headers, json=body).status_code, 409)
        self.proposal(assigned, '2026-11-20', 65000)
        self.assertEqual(self.client.post(route, headers=self.owner_headers, json={**body,'effective_from':'2026-11-19'}).status_code, 409)

    def test_only_assigned_worker_can_acknowledge_and_rates_stay_immutable(self):
        assigned = self.assignment()
        first = self.proposal(assigned)
        route = '/wage-agreements/'+first['id']+'/acknowledge'
        self.assertEqual(self.client.post(route, headers=self.owner_headers).status_code, 403)
        self.assertEqual(self.client.post(route, headers=self.stranger_headers).status_code, 404)
        accepted = self.client.post(route, headers=self.worker_headers)
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()['acknowledged_by'], self.worker['id'])
        self.assertIsNotNone(accepted.json()['acknowledged_at'])
        self.assertEqual(self.client.post(route, headers=self.worker_headers).status_code, 409)
        self.proposal(assigned, '2026-11-20', 65000)
        with psycopg.connect(self.url) as db:
            old = db.execute('SELECT daily_rate_paise,acknowledged_at FROM wage_agreements WHERE id=%s',(first['id'],)).fetchone()
        self.assertEqual(old[0], 60000)
        self.assertIsNotNone(old[1])
        for sql, params in [
            ('UPDATE wage_agreements SET daily_rate_paise=1 WHERE id=%s', (first['id'],)),
            ('UPDATE wage_agreements SET acknowledged_at=NULL,acknowledged_by=NULL WHERE id=%s', (first['id'],)),
            ('DELETE FROM wage_agreements WHERE id=%s', (first['id'],)),
        ]:
            with self.assertRaises(psycopg.errors.CheckViolation):
                with psycopg.connect(self.url) as db:
                    db.execute(sql, params)

    def test_wage_agreements_are_visible_only_to_participants(self):
        assigned = self.assignment()
        self.proposal(assigned)
        route = '/assignments/'+assigned['id']+'/wage-agreements'
        for headers in (self.owner_headers, self.worker_headers):
            listing = self.client.get(route+'?limit=1', headers=headers)
            self.assertEqual(listing.status_code, 200)
            self.assertEqual(listing.json()['total'], 1)
        for headers in (self.other_headers, self.stranger_headers):
            self.assertEqual(self.client.get(route, headers=headers).status_code, 404)

    def test_database_rejects_cross_owner_assignment_and_forged_acknowledgement(self):
        assigned = self.assignment()
        site = self.client.post('/worksites', headers=self.other_headers, json={'name':'Other owner'}).json()
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            with psycopg.connect(self.url) as db:
                db.execute('''INSERT INTO assignments(id,contractor_id,membership_id,worksite_id,start_date)
                  VALUES(%s,%s,%s,%s,%s)''', (uuid4(),self.owner['id'],assigned['membership_id'],site['id'],'2026-11-17'))
        pending = self.client.post('/memberships', headers=self.owner_headers, json={'worker_id':self.stranger['id']}).json()
        with self.assertRaises(psycopg.errors.CheckViolation):
            with psycopg.connect(self.url) as db:
                db.execute('''INSERT INTO assignments(id,contractor_id,membership_id,worksite_id,start_date)
                  VALUES(%s,%s,%s,%s,%s)''', (uuid4(),self.owner['id'],pending['id'],assigned['worksite_id'],'2026-11-17'))
        proposed = self.proposal(assigned)
        with self.assertRaises(psycopg.errors.CheckViolation):
            with psycopg.connect(self.url) as db:
                db.execute('UPDATE wage_agreements SET acknowledged_at=now(),acknowledged_by=%s WHERE id=%s',
                           (self.stranger['id'],proposed['id']))

    def test_assigned_worksite_is_retained_and_can_be_archived(self):
        assigned = self.assignment()
        route = '/worksites/'+assigned['worksite_id']
        result = self.client.delete(route, headers=self.owner_headers)
        self.assertEqual(result.status_code, 409)
        self.assertIn('archive', result.json()['detail'])
        archived = self.client.put(route, headers=self.owner_headers, json={'name':'Archived site','active':False})
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(self.client.get('/assignments/'+assigned['id'], headers=self.worker_headers).status_code, 200)

    def test_concurrent_same_date_proposals_create_one_rate(self):
        assigned = self.assignment()
        route = '/assignments/'+assigned['id']+'/wage-agreements'
        def submit(rate):
            with TestClient(app) as client:
                return client.post(route, headers=self.owner_headers,
                    json={'daily_rate_paise':rate,'effective_from':'2026-11-17'}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(submit, [60000,65000]))
        self.assertEqual(sorted(codes), [201,409])
        self.assertEqual(self.client.get(route, headers=self.worker_headers).json()['total'], 1)
