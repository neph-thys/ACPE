-- ============================================================
--  ACPE — Autonomous Campus Placement Engine
--  schema.sql
--  Run once: psql -U <user> -d <dbname> -f schema.sql
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- for gen_random_uuid()


--  1. STUDENTS
CREATE TABLE students (
    student_id      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       VARCHAR(120)    NOT NULL,
    email           VARCHAR(150)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    roll_number     VARCHAR(30)     NOT NULL UNIQUE,
    branch          VARCHAR(60)     NOT NULL,          -- e.g. 'CSE', 'ECE', 'MECH'
    batch_year      SMALLINT        NOT NULL,          -- e.g. 2025
    cgpa            NUMERIC(4,2)    NOT NULL CHECK (cgpa >= 0.00 AND cgpa <= 10.00),
    active_backlogs SMALLINT        NOT NULL DEFAULT 0 CHECK (active_backlogs >= 0),
    is_placed       BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_students_branch      ON students (branch);
CREATE INDEX idx_students_batch_year  ON students (batch_year);
CREATE INDEX idx_students_is_placed   ON students (is_placed);


--  2. COMPANIES
CREATE TABLE companies (
    company_id      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(150)    NOT NULL UNIQUE,
    industry        VARCHAR(80),                       -- e.g. 'IT Services', 'Finance'
    website         VARCHAR(255),
    contact_email   VARCHAR(150),
    contact_name    VARCHAR(120),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);


--  3. JOB_POSTINGS
CREATE TABLE job_postings (
    job_id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID            NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    title               VARCHAR(150)    NOT NULL,
    description         TEXT,
    job_type            VARCHAR(30)     NOT NULL DEFAULT 'full_time'
                            CHECK (job_type IN ('full_time', 'internship', 'ppo')),
    ctc_lpa             NUMERIC(6,2),                  -- Cost to Company in LPA; NULL = undisclosed
    location            VARCHAR(100),

    -- Eligibility criteria
    min_cgpa            NUMERIC(4,2)    NOT NULL DEFAULT 0.00
                            CHECK (min_cgpa >= 0.00 AND min_cgpa <= 10.00),
    max_backlogs        SMALLINT        NOT NULL DEFAULT 0
                            CHECK (max_backlogs >= 0),
    allowed_branches    TEXT[]          NOT NULL DEFAULT '{}',
                            -- empty array = all branches allowed
    allowed_batches     SMALLINT[]      NOT NULL DEFAULT '{}',
                            -- empty array = all batches allowed

    -- Lifecycle
    status              VARCHAR(20)     NOT NULL DEFAULT 'open'
                            CHECK (status IN ('open', 'closed', 'cancelled')),
    application_deadline DATE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_job_postings_company  ON job_postings (company_id);
CREATE INDEX idx_job_postings_status   ON job_postings (status);


--  4. APPLICATIONS
--  Core rule: one student can hold at most ONE accepted offer.
--  Enforced by the partial unique index below + trigger.
CREATE TABLE applications (
    application_id  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID            NOT NULL REFERENCES students  (student_id) ON DELETE CASCADE,
    job_id          UUID            NOT NULL REFERENCES job_postings (job_id)  ON DELETE CASCADE,
    status          VARCHAR(25)     NOT NULL DEFAULT 'applied'
                        CHECK (status IN (
                            'applied',       -- submitted, not yet reviewed
                            'shortlisted',   -- invited to interview process
                            'in_progress',   -- currently in interview rounds
                            'offered',       -- offer extended
                            'accepted',      -- student accepted — triggers is_placed
                            'rejected',      -- rejected at any stage
                            'withdrawn'      -- student withdrew application
                        )),
    applied_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- One application per student per job
    CONSTRAINT uq_student_job UNIQUE (student_id, job_id)
);

-- ONE STUDENT, ONE JOB:
-- A student may not have more than one 'accepted' application.
CREATE UNIQUE INDEX uq_one_accepted_offer
    ON applications (student_id)
    WHERE status = 'accepted';

CREATE INDEX idx_applications_student  ON applications (student_id);
CREATE INDEX idx_applications_job      ON applications (job_id);
CREATE INDEX idx_applications_status   ON applications (status);


--  5. INTERVIEW_ROUNDS
CREATE TABLE interview_rounds (
    round_id        UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID            NOT NULL REFERENCES applications (application_id) ON DELETE CASCADE,
    round_number    SMALLINT        NOT NULL CHECK (round_number >= 1),
    round_type      VARCHAR(40)     NOT NULL
                        CHECK (round_type IN (
                            'aptitude_test',
                            'group_discussion',
                            'technical_interview',
                            'hr_interview',
                            'case_study',
                            'other'
                        )),
    scheduled_at    TIMESTAMPTZ,
    result          VARCHAR(15)     DEFAULT 'pending'
                        CHECK (result IN ('pending', 'pass', 'fail')),
    remarks         TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- No duplicate round numbers for the same application
    CONSTRAINT uq_application_round UNIQUE (application_id, round_number)
);

CREATE INDEX idx_rounds_application  ON interview_rounds (application_id);
CREATE INDEX idx_rounds_result       ON interview_rounds (result);


--  6. TRIGGER — keep updated_at current on every row change
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_job_postings_updated_at
    BEFORE UPDATE ON job_postings
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_rounds_updated_at
    BEFORE UPDATE ON interview_rounds
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


--  7. TRIGGER — enforce One Student, One Job policy
--  When an application is marked 'accepted', set is_placed=TRUE on the student.
--  Block any further 'accepted' status changes for that student
--  (the unique index handles the DB-level block;
--  this trigger gives a clear error message).
CREATE OR REPLACE FUNCTION enforce_one_job_policy()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.status = 'accepted' THEN
        -- Check if student is already placed
        IF (SELECT is_placed FROM students WHERE student_id = NEW.student_id) THEN
            RAISE EXCEPTION
                'Policy violation: student % is already placed. Cannot accept another offer.',
                NEW.student_id;
        END IF;
        -- Mark student as placed
        UPDATE students SET is_placed = TRUE WHERE student_id = NEW.student_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_one_job_policy
    BEFORE UPDATE OF status ON applications
    FOR EACH ROW
    WHEN (NEW.status = 'accepted')
    EXECUTE FUNCTION enforce_one_job_policy();