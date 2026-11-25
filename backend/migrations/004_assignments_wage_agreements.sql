CREATE TABLE assignments (
 id uuid PRIMARY KEY,
 contractor_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 membership_id uuid NOT NULL,
 worksite_id uuid NOT NULL,
 start_date date NOT NULL,
 end_date date,
 created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY (membership_id,contractor_id) REFERENCES memberships(id,contractor_id) ON DELETE RESTRICT,
 FOREIGN KEY (worksite_id,contractor_id) REFERENCES worksites(id,contractor_id) ON DELETE RESTRICT,
 CHECK (end_date IS NULL OR end_date >= start_date)
);
CREATE INDEX assignments_owner ON assignments(contractor_id,start_date,id);
CREATE INDEX assignments_member ON assignments(membership_id,start_date,id);

CREATE FUNCTION check_assignment_membership() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 PERFORM 1 FROM memberships WHERE id=NEW.membership_id AND contractor_id=NEW.contractor_id
   AND status='accepted' FOR SHARE;
 IF NOT FOUND THEN
  RAISE EXCEPTION 'Assignment requires an accepted membership' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END;
$$;
CREATE TRIGGER assignment_membership_guard BEFORE INSERT OR UPDATE ON assignments
 FOR EACH ROW EXECUTE FUNCTION check_assignment_membership();

CREATE TABLE wage_agreements (
 id uuid PRIMARY KEY,
 assignment_id uuid NOT NULL REFERENCES assignments(id) ON DELETE RESTRICT,
 daily_rate_paise bigint NOT NULL CHECK(daily_rate_paise > 0),
 effective_from date NOT NULL,
 acknowledged_at timestamptz,
 acknowledged_by uuid REFERENCES users(id) ON DELETE RESTRICT,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(assignment_id,effective_from),
 CHECK((acknowledged_at IS NULL)=(acknowledged_by IS NULL))
);

CREATE FUNCTION guard_wage_agreement() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
 assigned assignments%ROWTYPE;
 latest date;
 assigned_worker uuid;
BEGIN
 IF TG_OP='DELETE' THEN
  RAISE EXCEPTION 'Wage agreements retain their history' USING ERRCODE='23514';
 END IF;
 -- Serialize proposals and acknowledgements for an assignment, including direct SQL.
 SELECT * INTO assigned FROM assignments WHERE id=NEW.assignment_id FOR UPDATE;
 IF NOT FOUND THEN
  RAISE EXCEPTION 'Assignment not found' USING ERRCODE='23503';
 END IF;
 IF TG_OP='INSERT' THEN
  SELECT max(effective_from) INTO latest FROM wage_agreements WHERE assignment_id=NEW.assignment_id;
  IF NEW.effective_from < assigned.start_date OR
     (assigned.end_date IS NOT NULL AND NEW.effective_from > assigned.end_date) OR
     (latest IS NOT NULL AND NEW.effective_from <= latest) THEN
   RAISE EXCEPTION 'Rate dates must be inside the assignment and increase' USING ERRCODE='23514';
  END IF;
  IF NEW.acknowledged_at IS NOT NULL OR NEW.acknowledged_by IS NOT NULL THEN
   RAISE EXCEPTION 'New agreements require separate worker acknowledgement' USING ERRCODE='23514';
  END IF;
 ELSE
  IF ROW(NEW.id,NEW.assignment_id,NEW.daily_rate_paise,NEW.effective_from,NEW.created_at)
     IS DISTINCT FROM ROW(OLD.id,OLD.assignment_id,OLD.daily_rate_paise,OLD.effective_from,OLD.created_at)
     OR OLD.acknowledged_at IS NOT NULL OR NEW.acknowledged_at IS NULL THEN
   RAISE EXCEPTION 'Agreement terms and acknowledgement history are immutable' USING ERRCODE='23514';
  END IF;
  SELECT worker_id INTO assigned_worker FROM memberships WHERE id=assigned.membership_id;
  IF NEW.acknowledged_by IS DISTINCT FROM assigned_worker THEN
   RAISE EXCEPTION 'Only the assigned worker can acknowledge' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END;
$$;
CREATE TRIGGER wage_agreement_guard BEFORE INSERT OR UPDATE OR DELETE ON wage_agreements
 FOR EACH ROW EXECUTE FUNCTION guard_wage_agreement();
