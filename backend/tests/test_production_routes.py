"""Check the boundary between public frontend files and protected API routes."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.main import create_app


class ProductionRouteTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        (root / 'index.html').write_text('<!doctype html><title>Tracker</title>')
        (root / 'assets').mkdir()
        (root / 'assets' / 'app.js').write_text('console.log("tracker");')
        self.client = TestClient(create_app(root))

    def test_frontend_and_assets_are_served(self):
        self.assertIn('<title>Tracker</title>', self.client.get('/').text)
        script = self.client.get('/assets/app.js')
        self.assertEqual(script.status_code, 200)
        self.assertIn('javascript', script.headers['content-type'])

    def test_api_is_protected_in_both_namespaces(self):
        for prefix in ('', '/api'):
            for path in ('/auth/me', '/worksites', '/memberships', '/assignments'):
                result = self.client.get(prefix + path)
                self.assertEqual(result.status_code, 401, (prefix, path, result.text))
                self.assertEqual(result.headers['content-type'], 'application/json')

    def test_unknown_routes_never_fall_back_to_html(self):
        for path in ('/api/unknown', '/api/auth/unknown', '/backend/auth.py', '/.env'):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_health_status_survives_static_mount(self):
        with patch.dict(os.environ, {'DATABASE_URL': ''}):
            for path in ('/health', '/api/health'):
                result = self.client.get(path)
                self.assertEqual(result.status_code, 503)
                self.assertEqual(result.json()['database'], 'not_configured')
