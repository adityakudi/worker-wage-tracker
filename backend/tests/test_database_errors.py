import os
import unittest
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient
from backend.main import app


class DatabaseErrorTests(unittest.TestCase):
    @patch.dict(os.environ, {'DATABASE_URL':'postgresql://unavailable/test','JWT_SECRET':'test-only-'+'a'*40})
    @patch('backend.auth.psycopg.connect', side_effect=psycopg.OperationalError('private connection details'))
    def test_login_database_failure_returns_safe_503(self, connect):
        response = TestClient(app).post('/auth/login',json={'email':'person@example.com','password':'long-enough-password'})
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json(), {'detail':'Database temporarily unavailable'})
        self.assertNotIn('private',response.text)

    def test_unconfigured_health_returns_503(self):
        with patch.dict(os.environ, {'DATABASE_URL':''}):
            response = TestClient(app).get('/health')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['database'],'not_configured')
