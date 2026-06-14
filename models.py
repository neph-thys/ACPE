# models.py — all database queries for ACPE

from db import execute_query


# ════════════════════════════════════════════════════════════
#  STUDENTS
# ════════════════════════════════════════════════════════════

def create_student(full_name, email, password_hash, roll_number,
                   branch, batch_year, cgpa, active_backlogs=0):
    sql = """
        INSERT INTO students
            (full_name, email, password_hash, roll_number,
             branch, batch_year, cgpa, active_backlogs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING student_id, full_name, email, roll_number
    """
    return execute_query(sql,
        (full_name, email, password_hash, roll_number,
         branch, batch_year, cgpa, active_backlogs), fetch=True)


def get_student_by_email(email):
    rows = execute_query("SELECT * FROM students WHERE email = %s", (email,), fetch=True)
    return rows[0] if rows else None


def get_student_by_id(student_id):
    rows = execute_query("SELECT * FROM students WHERE student_id = %s", (student_id,), fetch=True)
    return rows[0] if rows else None


def get_all_students():
    sql = """
        SELECT student_id, full_name, email, roll_number,
               branch, batch_year, cgpa, active_backlogs, is_placed
        FROM   students ORDER BY full_name ASC
    """
    return execute_query(sql, fetch=True)


def get_placement_stats():
    sql = """
        SELECT
            COUNT(*)                                         AS total_students,
            COUNT(*) FILTER (WHERE is_placed = TRUE)        AS placed,
            COUNT(*) FILTER (WHERE is_placed = FALSE)       AS unplaced,
            ROUND(COUNT(*) FILTER (WHERE is_placed = TRUE)
                  * 100.0 / NULLIF(COUNT(*), 0), 1)         AS placement_pct
        FROM students
    """
    rows = execute_query(sql, fetch=True)
    return rows[0] if rows else {}


# ════════════════════════════════════════════════════════════
#  JOB POSTINGS
# ════════════════════════════════════════════════════════════

def get_all_open_jobs():
    sql = """
        SELECT jp.*, c.name AS company_name, c.industry
        FROM   job_postings jp
        JOIN   companies c ON c.company_id = jp.company_id
        WHERE  jp.status = 'open'
        ORDER  BY jp.created_at DESC
    """
    return execute_query(sql, fetch=True)


def get_all_jobs():
    sql = """
        SELECT jp.*, c.name AS company_name, c.industry,
               COUNT(a.application_id) FILTER (
                   WHERE a.status = 'accepted'
               ) AS placed_count
        FROM   job_postings jp
        JOIN   companies c ON c.company_id = jp.company_id
        LEFT   JOIN applications a ON a.job_id = jp.job_id
        GROUP  BY jp.job_id, c.name, c.industry
        ORDER  BY jp.created_at DESC
    """
    return execute_query(sql, fetch=True)


def get_eligible_jobs_for_student(student_id):
    sql = """
        SELECT jp.*, c.name AS company_name, c.industry
        FROM   job_postings jp
        JOIN   companies    c ON c.company_id = jp.company_id
        JOIN   students     s ON s.student_id = %s
        WHERE  jp.status = 'open'
          AND  s.is_placed = FALSE
          AND  s.cgpa            >= jp.min_cgpa
          AND  s.active_backlogs <= jp.max_backlogs
          AND  (jp.allowed_branches = '{}' OR s.branch = ANY(jp.allowed_branches))
          AND  (jp.allowed_batches  = '{}' OR s.batch_year = ANY(jp.allowed_batches))
          AND  jp.job_id NOT IN (
                SELECT job_id FROM applications WHERE student_id = %s)
        ORDER  BY jp.ctc_lpa DESC NULLS LAST
    """
    return execute_query(sql, (student_id, student_id), fetch=True)


def create_job(company_id, title, job_type, ctc_lpa,
               min_cgpa, max_backlogs, allowed_branches, allowed_batches):
    sql = """
        INSERT INTO job_postings
            (company_id, title, job_type, ctc_lpa,
             min_cgpa, max_backlogs, allowed_branches, allowed_batches, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open')
        RETURNING job_id, title, status
    """
    return execute_query(sql,
        (company_id, title, job_type, ctc_lpa or None,
         min_cgpa, max_backlogs, allowed_branches, allowed_batches), fetch=True)


def close_job(job_id):
    sql = """
        UPDATE job_postings SET status = 'closed'
        WHERE  job_id = %s
        RETURNING job_id, title, status
    """
    return execute_query(sql, (job_id,), fetch=True)


def get_all_companies():
    sql = "SELECT company_id, name, industry FROM companies ORDER BY name"
    return execute_query(sql, fetch=True)


# ════════════════════════════════════════════════════════════
#  APPLICATIONS
# ════════════════════════════════════════════════════════════

def apply_to_job(student_id, job_id):
    sql = """
        INSERT INTO applications (student_id, job_id)
        VALUES (%s, %s)
        RETURNING application_id, status, applied_at
    """
    return execute_query(sql, (student_id, job_id), fetch=True)


def get_applications_for_student(student_id):
    sql = """
        SELECT a.application_id, a.status, a.applied_at,
               jp.title AS job_title, jp.ctc_lpa, jp.job_type,
               c.name   AS company_name, c.industry
        FROM   applications a
        JOIN   job_postings jp ON jp.job_id    = a.job_id
        JOIN   companies    c  ON c.company_id = jp.company_id
        WHERE  a.student_id = %s
        ORDER  BY a.applied_at DESC
    """
    return execute_query(sql, (student_id,), fetch=True)


def update_application_status(application_id, new_status):
    sql = """
        UPDATE applications SET status = %s
        WHERE  application_id = %s
        RETURNING application_id, student_id, status
    """
    return execute_query(sql, (new_status, application_id), fetch=True)


# ════════════════════════════════════════════════════════════
#  INTERVIEW ROUNDS
# ════════════════════════════════════════════════════════════

def get_rounds_for_application(application_id):
    sql = """
        SELECT * FROM interview_rounds
        WHERE  application_id = %s
        ORDER  BY round_number ASC
    """
    return execute_query(sql, (application_id,), fetch=True)


def update_round_result(round_id, result, remarks=None):
    sql = """
        UPDATE interview_rounds SET result = %s, remarks = %s
        WHERE  round_id = %s
        RETURNING round_id, round_number, result
    """
    return execute_query(sql, (result, remarks, round_id), fetch=True)