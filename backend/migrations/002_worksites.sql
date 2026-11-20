BEGIN;
CREATE TABLE worksites (
 id uuid PRIMARY KEY,
 contractor_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 name varchar(120) NOT NULL CHECK (length(trim(name)) > 0),
 location varchar(300) NOT NULL DEFAULT '',
 active boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE (id,contractor_id)
);
CREATE INDEX worksites_owner_name ON worksites(contractor_id,name,id);
COMMIT;
