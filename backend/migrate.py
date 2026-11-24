"""Apply versioned SQL migrations atomically; never rewrite applied migrations."""
import hashlib
import os
from pathlib import Path

import psycopg


def migrate(url: str) -> list[str]:
    applied = []
    with psycopg.connect(url, autocommit=True, connect_timeout=5) as db:
        # Serialize migration processes for this database without keeping a DDL transaction open.
        db.execute("SELECT pg_advisory_lock(724062024)")
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
                name text PRIMARY KEY, sha256 text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now())""")
            for path in sorted(Path(__file__).with_name('migrations').glob('*.sql')):
                source = path.read_text()
                digest = hashlib.sha256(source.encode()).hexdigest()
                row = db.execute('SELECT sha256 FROM schema_migrations WHERE name=%s', (path.name,)).fetchone()
                if row:
                    if row[0] != digest:
                        raise RuntimeError(f'Applied migration changed: {path.name}')
                    continue
                with db.transaction():
                    db.execute(source)
                    db.execute('INSERT INTO schema_migrations(name,sha256) VALUES(%s,%s)', (path.name,digest))
                applied.append(path.name)
        finally:
            db.execute("SELECT pg_advisory_unlock(724062024)")
    return applied


if __name__ == '__main__':
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise SystemExit('Set DATABASE_URL before running migrations.')
    print('Applied:', ', '.join(migrate(url)) or 'already up to date')
