# Autonomous Campus Placement Engine (ACPE)

A full-stack placement management platform built to automate and enforce campus recruitment workflows through a database-driven architecture.

ACPE transforms traditional placement management by shifting critical business rules from the application layer directly into PostgreSQL using triggers and stored procedures. This ensures policy compliance, eliminates manual intervention, and provides a transparent recruitment process for students, recruiters, and placement administrators.

---

## Features

### Student Portal

* Student registration and authentication
* Personalized dashboard
* Eligibility-based job recommendations
* Application tracking
* Interview round progress monitoring
* Placement status updates

### Recruiter Portal

* Company registration and login
* Job posting management
* Applicant review system
* Interview round result updates
* Candidate shortlisting

### Administrator Portal

* Student profile management
* Recruitment drive management
* Job posting moderation
* Placement monitoring dashboard
* Centralized recruitment oversight

---

## Core System Innovations

### One Student, One Job Policy

Once a student accepts an offer, all other active applications are automatically withdrawn through database triggers, preventing multiple simultaneous placements.

### Automated Interview Workflow

The system automatically creates and manages interview rounds:

* Aptitude Round
* Technical Round
* HR Round

### Eligibility Enforcement

Applications are validated using:

* Minimum CGPA requirements
* Branch restrictions
* Backlog constraints

Only eligible students can view and apply for matching opportunities.

### State Locking Mechanism

Application states follow forward-only transitions, preventing unauthorized reversal of recruitment outcomes and maintaining a tamper-proof audit trail.

---

## Technology Stack

### Backend

* Python 3.10
* Flask 2.3

### Database

* PostgreSQL 14
* Stored Procedures
* SQL Triggers
* Relational Database Design

### Frontend

* HTML5
* CSS3
* Jinja2 Templates

### Database Administration

* pgAdmin 4

### Database Connectivity

* Psycopg2

---

## System Architecture

ACPE follows a Three-Tier Architecture:

### Presentation Layer

Role-based interfaces for:

* Students
* Recruiters
* Placement Officers

### Application Layer

Flask backend responsible for:

* Authentication
* Session Management
* Routing
* Database communication

### Database Logic Layer

PostgreSQL acts as the primary policy enforcement engine through:

* Triggers
* Stored Procedures
* Constraints
* Automated workflow management

---

## Database Schema

### Students

Stores:

* Academic information
* CGPA
* Branch
* Backlog count
* Placement status

### Companies

Maintains recruiter information and contact details.

### Job Postings

Contains:

* Role details
* CTC
* Eligibility criteria
* Recruitment status

### Applications

Links students to job postings and tracks application status.

### Interview Rounds

Tracks progression through:

* Aptitude
* Technical
* HR rounds

---

## Key Functionalities

* Automated eligibility filtering
* Placement lifecycle automation
* Dynamic student dashboards
* Role-based access control
* Recruitment analytics queries
* Auto-withdrawal of competing applications
* Interview round tracking
* Real-time placement updates

---

## Sample Business Rules Implemented

* One Student, One Job Policy
* Automatic Interview Round Creation
* Eligibility Validation
* Placement Status Locking
* Application Auto-Withdrawal

---

## Installation

Clone the repository:

```bash
git clone https://github.com/neph-thys/ACPE.git
cd ACPE
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure PostgreSQL credentials and database settings.

Run the application:

```bash
python app.py
```

---

## Future Enhancements

* Resume parsing and ranking
* AI-based candidate-job matching
* Placement analytics dashboard
* Email notification system
* Multi-campus support
* Interview scheduling automation

---


(Developed as part of the Database Systems Laboratory Project at Manipal Institute of Technology Bengaluru.)
