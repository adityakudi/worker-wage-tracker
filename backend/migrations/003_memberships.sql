BEGIN;
CREATE TABLE memberships (
 id uuid PRIMARY KEY,
 contractor_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 worker_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 status text NOT NULL DEFAULT 'invited' CHECK(status IN ('invited','accepted')),
 created_at timestamptz NOT NULL DEFAULT now(),
 accepted_at timestamptz,
 UNIQUE(contractor_id,worker_id),
 UNIQUE(id,contractor_id),
 CHECK(contractor_id<>worker_id),
 CHECK((status='accepted')=(accepted_at IS NOT NULL))
);
CREATE INDEX memberships_worker ON memberships(worker_id,created_at,id);
COMMIT;
