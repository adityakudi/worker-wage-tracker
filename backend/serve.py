"""Container entry point: validate configuration, migrate, then start the server."""
import os
from pathlib import Path

from backend.migrate import migrate


def main():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        raise SystemExit('DATABASE_URL is required.')
    if len(os.environ.get('JWT_SECRET', '')) < 32:
        raise SystemExit('JWT_SECRET must contain at least 32 characters.')
    try:
        port = int(os.environ.get('PORT', '8000'))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise SystemExit('PORT must be between 1 and 65535.')
    if not (Path(__file__).resolve().parent.parent / 'frontend' / 'dist' / 'index.html').is_file():
        raise SystemExit('Build frontend/dist before starting the combined service.')
    applied = migrate(url)
    print('Migrations:', ', '.join(applied) or 'already up to date', flush=True)
    os.execvp('uvicorn', ['uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', str(port)])


if __name__ == '__main__':
    main()
