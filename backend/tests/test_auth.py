import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import jwt
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth import hasher

class AuthTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
    def test_missing_token(self):
        self.assertEqual(self.client.get('/auth/me').status_code, 401)
    @patch.dict(os.environ, {'JWT_SECRET':'x'*40})
    def test_bad_token(self):
        self.assertEqual(self.client.get('/auth/me', headers={'Authorization':'Bearer broken'}).status_code, 401)
    @patch.dict(os.environ, {'JWT_SECRET':'x'*40})
    def test_expired_token(self):
        token = jwt.encode({'sub':'test','iat':datetime.now(timezone.utc)-timedelta(hours=2),'exp':datetime.now(timezone.utc)-timedelta(hours=1),'iss':'worker-wage-tracker','aud':'worker-wage-api'}, 'x'*40, algorithm='HS256')
        self.assertEqual(self.client.get('/auth/me', headers={'Authorization':'Bearer '+token}).status_code,401)
    def test_bad_signup(self):
        self.assertEqual(self.client.post('/auth/signup',json={'email':'bad','password':'short','role':'admin'}).status_code,422)
    def test_hash(self):
        value=hasher.hash('a-long-password')
        self.assertNotEqual(value,'a-long-password')
        self.assertTrue(hasher.verify('a-long-password',value))
        self.assertFalse(hasher.verify('different',value))
