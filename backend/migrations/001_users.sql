BEGIN;
CREATE TABLE users (
 id uuid PRIMARY KEY,
 email text NOT NULL UNIQUE CHECK (email = lower(email)),
 password_hash text NOT NULL,
 role text NOT NULL CHECK (role IN ('worker','contractor')),
 created_at timestamptz NOT NULL DEFAULT now()
);
COMMIT;
