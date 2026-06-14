# app.py — Flask entry point for ACPE

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import models
import psycopg2

app = Flask(__name__)
app.secret_key = "acpe_secret_key_change_in_production"


# ════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/student/dashboard")
def student_dashboard():
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("index"))
    student = models.get_student_by_id(student_id)
    jobs    = models.get_eligible_jobs_for_student(student_id)
    apps    = models.get_applications_for_student(student_id)
    return render_template("student_dashboard.html",
                           student=student, jobs=jobs, applications=apps)

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("index"))
    students  = models.get_all_students()
    jobs      = models.get_all_jobs()
    companies = models.get_all_companies()
    stats     = models.get_placement_stats()
    return render_template("admin_dashboard.html",
                           students=students, jobs=jobs,
                           companies=companies, stats=stats)


# ════════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════════

@app.route("/login", methods=["POST"])
def login():
    data  = request.get_json()
    email = data.get("email", "")
    if email == "admin@acpe.edu" and data.get("password") == "admin123":
        session["role"] = "admin"
        return jsonify({"redirect": "/admin/dashboard"}), 200
    student = models.get_student_by_email(email)
    if student:
        session["student_id"] = str(student["student_id"])
        session["role"]       = "student"
        return jsonify({"redirect": "/student/dashboard"}), 200
    return jsonify({"error": "Invalid email or password."}), 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ════════════════════════════════════════════════════════════
#  STUDENT API
# ════════════════════════════════════════════════════════════

@app.route("/api/students", methods=["POST"])
def register_student():
    data = request.get_json()
    try:
        result = models.create_student(
            full_name       = data["full_name"],
            email           = data["email"],
            password_hash   = data["password"],
            roll_number     = data["roll_number"],
            branch          = data["branch"],
            batch_year      = int(data["batch_year"]),
            cgpa            = float(data["cgpa"]),
            active_backlogs = int(data.get("active_backlogs", 0))
        )
        return jsonify(result[0]), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Email or roll number already registered."}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/students/<student_id>/applications")
def student_applications_api(student_id):
    apps = models.get_applications_for_student(student_id)
    for row in apps:
        row["rounds"]         = models.get_rounds_for_application(str(row["application_id"]))
        row["application_id"] = str(row["application_id"])
        row["applied_at"]     = str(row["applied_at"])
        for r in row["rounds"]:
            r["round_id"]       = str(r["round_id"])
            r["application_id"] = str(r["application_id"])
            r["created_at"]     = str(r["created_at"])
            r["updated_at"]     = str(r["updated_at"])
            if r.get("scheduled_at"):
                r["scheduled_at"] = str(r["scheduled_at"])
    return jsonify(apps), 200


# ════════════════════════════════════════════════════════════
#  APPLICATION API
# ════════════════════════════════════════════════════════════

@app.route("/api/applications", methods=["POST"])
def apply():
    data = request.get_json()
    try:
        result = models.apply_to_job(data["student_id"], data["job_id"])
        return jsonify(result[0]), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Already applied to this job."}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/applications/<application_id>/status", methods=["PATCH"])
def update_status(application_id):
    data = request.get_json()
    try:
        result = models.update_application_status(application_id, data["status"])
        return jsonify(result[0]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ════════════════════════════════════════════════════════════
#  ROUND API
# ════════════════════════════════════════════════════════════

@app.route("/api/rounds/<round_id>/result", methods=["PATCH"])
def update_round(round_id):
    data   = request.get_json()
    result = models.update_round_result(round_id, data["result"], data.get("remarks"))
    return jsonify(result[0]), 200


# ════════════════════════════════════════════════════════════
#  JOB API
# ════════════════════════════════════════════════════════════

@app.route("/api/jobs", methods=["POST"])
def create_job():
    data = request.get_json()
    try:
        # Parse branches and batches from comma-separated strings
        branches = [b.strip().upper() for b in data.get("allowed_branches","").split(",") if b.strip()]
        batches  = [int(b.strip()) for b in data.get("allowed_batches","").split(",") if b.strip()]
        result = models.create_job(
            company_id       = data["company_id"],
            title            = data["title"],
            job_type         = data.get("job_type", "full_time"),
            ctc_lpa          = float(data["ctc_lpa"]) if data.get("ctc_lpa") else None,
            min_cgpa         = float(data.get("min_cgpa", 0)),
            max_backlogs     = int(data.get("max_backlogs", 0)),
            allowed_branches = branches,
            allowed_batches  = batches
        )
        return jsonify(result[0]), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/jobs/<job_id>/close", methods=["PATCH"])
def close_job(job_id):
    try:
        result = models.close_job(job_id)
        return jsonify(result[0]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True)