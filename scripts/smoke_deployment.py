"""Read-only deployed-service checks, with optional writes to a disposable test DB."""
import argparse
import json
import re
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4


def verify(base_url: str, exercise_api: bool = False):
    parsed = urlparse(base_url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError('Provide an HTTP(S) origin without embedded credentials.')
    base_url = base_url.rstrip('/')

    def request(path, expected=200, method='GET', body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        data = json.dumps(body).encode() if body is not None else None
        try:
            response = urlopen(Request(base_url + path, data=data, headers=headers, method=method), timeout=30)
        except HTTPError as error:
            response = error
        with response:
            payload = response.read()
            if response.status != expected:
                raise RuntimeError(f'{method} {path}: expected {expected}, received {response.status}')
            if not payload:
                return None
            if 'application/json' in response.headers.get('Content-Type', ''):
                return json.loads(payload)
            return payload.decode()

    expected_health = {'status': 'ok', 'database': 'connected'}
    for path in ('/health', '/api/health'):
        if request(path) != expected_health:
            raise RuntimeError('Database health check did not report a connected database.')
    index = request('/')
    assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', index)
    if not assets:
        raise RuntimeError('Built frontend assets were not found in the served page.')
    for asset in assets:
        request(asset)
    request('/api/auth/me', expected=401)
    request('/api/worksites', expected=401)
    request('/api/memberships', expected=401)
    request('/api/not-a-route', expected=404)
    request('/backend/auth.py', expected=404)
    request('/.env', expected=404)
    print('PASS: database health, frontend/assets, protected API and private-file boundaries')
    if not exercise_api:
        return

    # This mode leaves three synthetic accounts in the DB. Use only a disposable CI DB.
    identities = []
    for role in ('contractor', 'contractor', 'worker'):
        credentials = {'email': f'smoke-{uuid4().hex}@example.com', 'password': uuid4().hex}
        user = request('/api/auth/signup', expected=201, method='POST', body={**credentials, 'role': role})
        token = request('/api/auth/login', method='POST', body=credentials)['access_token']
        if request('/api/auth/me', token=token) != user:
            raise RuntimeError('Authenticated identity does not match signup.')
        identities.append((user, token))
    (_, owner), (_, other), (worker, worker_token) = identities
    site = request('/api/worksites', expected=201, method='POST', token=owner,
                   body={'name': 'Container smoke site', 'location': 'Test data'})
    route = '/api/worksites/' + site['id']
    request(route, expected=404, token=other)
    request(route, expected=403, token=worker_token)
    page = request('/api/worksites?q=Container&limit=1', token=owner)
    if page['total'] != 1 or page['items'][0]['id'] != site['id']:
        raise RuntimeError('Created worksite was not returned by search.')
    updated = request(route, method='PUT', token=owner, body={'name': 'Archived smoke site', 'active': False})
    if updated['active']:
        raise RuntimeError('Worksite update was not persisted.')
    membership = request('/api/memberships', expected=201, method='POST', token=owner,
                         body={'worker_id': worker['id']})
    accept = '/api/memberships/' + membership['id'] + '/accept'
    request(accept, expected=403, method='POST', token=other)
    accepted = request(accept, method='POST', token=worker_token)
    if accepted['status'] != 'accepted':
        raise RuntimeError('Worker invitation was not accepted.')
    request(route, expected=204, method='DELETE', token=owner)
    request(route, expected=404, token=owner)
    print('PASS: container signup/login, worksite CRUD/search/ownership, worker invitation/acceptance')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True, help='Service origin, e.g. https://<actual-hostname>')
    parser.add_argument('--exercise-api', action='store_true', help='WRITE synthetic fixtures; disposable test DB only')
    args = parser.parse_args()
    verify(args.url, args.exercise_api)
