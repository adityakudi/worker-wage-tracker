import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth import current_user

class WorksiteAccessTests(unittest.TestCase):
    def tearDown(self): app.dependency_overrides.clear()
    def test_requires_login(self):
        self.assertEqual(TestClient(app).get('/worksites').status_code,401)
    def test_worker_denied(self):
        app.dependency_overrides[current_user]=lambda:{'id':'worker','role':'worker'}
        self.assertEqual(TestClient(app).post('/worksites',json={'name':'Site'}).status_code,403)
    def test_pagination_bounds(self):
        app.dependency_overrides[current_user]=lambda:{'id':'owner','role':'contractor'}
        self.assertEqual(TestClient(app).get('/worksites?limit=101').status_code,422)
    def test_blank_name(self):
        app.dependency_overrides[current_user]=lambda:{'id':'owner','role':'contractor'}
        self.assertEqual(TestClient(app).post('/worksites',json={'name':'   '}).status_code,422)
