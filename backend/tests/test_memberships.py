import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth import current_user
class MembershipTests(unittest.TestCase):
    def tearDown(self): app.dependency_overrides.clear()
    def test_login_required(self):
        self.assertEqual(TestClient(app).get('/memberships').status_code,401)
    def test_worker_cannot_invite(self):
        app.dependency_overrides[current_user]=lambda:{'id':'worker','role':'worker'}
        self.assertEqual(TestClient(app).post('/memberships',json={'worker_id':'00000000-0000-0000-0000-000000000001'}).status_code,403)
    def test_contractor_cannot_accept(self):
        app.dependency_overrides[current_user]=lambda:{'id':'owner','role':'contractor'}
        self.assertEqual(TestClient(app).post('/memberships/00000000-0000-0000-0000-000000000001/accept').status_code,403)
