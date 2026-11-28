ALTER TABLE assignments ADD UNIQUE (id, membership_id);
ALTER TABLE wage_agreements ADD UNIQUE (id, assignment_id);

CREATE TABLE ledger_entries (
 id uuid PRIMARY KEY,
 membership_id uuid NOT NULL REFERENCES memberships(id),
 kind text NOT NULL CHECK (kind IN ('earning','advance','payment','adjustment','reversal')),
 effective_date date NOT NULL,
 amount_paise bigint NOT NULL CHECK (amount_paise >= -9223372036854775807),
 assignment_id uuid,
 wage_agreement_id uuid,
 daily_rate_paise bigint CHECK (daily_rate_paise > 0),
 half_day_units smallint CHECK (half_day_units BETWEEN 0 AND 2),
 reverses_id uuid UNIQUE,
 replaces_id uuid UNIQUE,
 request_id uuid,
 notes text NOT NULL DEFAULT '' CHECK (length(notes) <= 500),
 created_by uuid NOT NULL REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE (id, membership_id),
 UNIQUE (id, membership_id, effective_date),
 UNIQUE (membership_id, request_id),
 FOREIGN KEY (assignment_id, membership_id) REFERENCES assignments(id, membership_id),
 FOREIGN KEY (wage_agreement_id, assignment_id) REFERENCES wage_agreements(id, assignment_id),
 FOREIGN KEY (reverses_id, membership_id) REFERENCES ledger_entries(id, membership_id),
 FOREIGN KEY (replaces_id, membership_id) REFERENCES ledger_entries(id, membership_id),
 CHECK (
  (kind = 'earning' AND assignment_id IS NOT NULL AND wage_agreement_id IS NOT NULL
    AND daily_rate_paise IS NOT NULL AND half_day_units IS NOT NULL
    AND amount_paise = floor((daily_rate_paise::numeric * half_day_units + 1) / 2))
  OR (kind <> 'earning' AND assignment_id IS NULL AND wage_agreement_id IS NULL
     AND daily_rate_paise IS NULL AND half_day_units IS NULL)
 ),
 CHECK ((kind = 'reversal') = (reverses_id IS NOT NULL)),
 CHECK (kind <> 'reversal' OR replaces_id IS NULL),
 CHECK (kind NOT IN ('payment','advance') OR amount_paise < 0),
 CHECK (kind <> 'adjustment' OR amount_paise <> 0)
);
CREATE INDEX ledger_period ON ledger_entries(membership_id, effective_date, created_at, id);

-- A slot indexes the current attendance record. The underlying posted record is immutable.
CREATE TABLE attendance_slots (
 membership_id uuid NOT NULL,
 work_date date NOT NULL,
 entry_id uuid NOT NULL UNIQUE,
 PRIMARY KEY (membership_id, work_date),
 FOREIGN KEY (entry_id, membership_id, work_date) REFERENCES ledger_entries(id, membership_id, effective_date)
);

CREATE TABLE ledger_reviews (
 entry_id uuid NOT NULL REFERENCES ledger_entries(id),
 kind text NOT NULL CHECK (kind IN ('acknowledged','receipt_confirmed')),
 worker_id uuid NOT NULL REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY (entry_id, kind)
);

CREATE TABLE ledger_disputes (
 entry_id uuid PRIMARY KEY REFERENCES ledger_entries(id),
 worker_id uuid NOT NULL REFERENCES users(id),
 reason text NOT NULL CHECK (length(trim(reason)) BETWEEN 1 AND 500),
 created_at timestamptz NOT NULL DEFAULT now()
);

-- Response history defines the current state without editing earlier decisions.
CREATE TABLE ledger_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 entry_id uuid NOT NULL REFERENCES ledger_entries(id),
 actor_id uuid NOT NULL REFERENCES users(id),
 kind text NOT NULL CHECK (kind IN ('posted','reversed','acknowledged','receipt_confirmed',
  'disputed','responded','correction_proposed','response_rejected','resolved')),
 details jsonb NOT NULL DEFAULT '{}'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ledger_events_entry ON ledger_events(entry_id, id DESC);

CREATE FUNCTION prevent_ledger_rewrite() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 RAISE EXCEPTION 'Posted records and review history are immutable' USING ERRCODE='23514';
END;
$$;
CREATE TRIGGER freeze_ledger BEFORE UPDATE OR DELETE ON ledger_entries
 FOR EACH ROW EXECUTE FUNCTION prevent_ledger_rewrite();
CREATE TRIGGER freeze_reviews BEFORE UPDATE OR DELETE ON ledger_reviews
 FOR EACH ROW EXECUTE FUNCTION prevent_ledger_rewrite();
CREATE TRIGGER freeze_disputes BEFORE UPDATE OR DELETE ON ledger_disputes
 FOR EACH ROW EXECUTE FUNCTION prevent_ledger_rewrite();
CREATE TRIGGER freeze_events BEFORE UPDATE OR DELETE ON ledger_events
 FOR EACH ROW EXECUTE FUNCTION prevent_ledger_rewrite();

CREATE FUNCTION validate_ledger_links() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE original ledger_entries%ROWTYPE;
BEGIN
 IF NEW.reverses_id IS NOT NULL THEN
  SELECT * INTO original FROM ledger_entries WHERE id=NEW.reverses_id AND membership_id=NEW.membership_id;
  IF NOT FOUND OR original.kind='reversal' OR NEW.amount_paise <> -original.amount_paise
     OR NEW.effective_date <> original.effective_date THEN
   RAISE EXCEPTION 'Reversals must exactly offset the original entry' USING ERRCODE='23514';
  END IF;
 END IF;
 IF NEW.replaces_id IS NOT NULL THEN
  SELECT * INTO original FROM ledger_entries WHERE id=NEW.replaces_id AND membership_id=NEW.membership_id;
  IF NOT FOUND OR NEW.kind <> original.kind OR NEW.effective_date <> original.effective_date
     OR NEW.assignment_id IS DISTINCT FROM original.assignment_id
     OR NEW.wage_agreement_id IS DISTINCT FROM original.wage_agreement_id
     OR NEW.daily_rate_paise IS DISTINCT FROM original.daily_rate_paise
     OR NOT EXISTS (SELECT 1 FROM ledger_entries WHERE reverses_id=original.id) THEN
   RAISE EXCEPTION 'Replacement requires a matching reversed entry' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END;
$$;
CREATE TRIGGER ledger_links BEFORE INSERT ON ledger_entries
 FOR EACH ROW EXECUTE FUNCTION validate_ledger_links();
