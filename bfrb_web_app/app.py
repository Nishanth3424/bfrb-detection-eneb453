"""
BFRB Detection Web App - Flask Backend  (v5 - Full Tier 1-4 stack)
====================================================================
Full-featured BFRB detection system with:
  - SQLite database for sessions, detections, calibrations, bouts,
    pilot studies, and per-frame telemetry
  - Real-time session management
  - Detection logging with confidence scores
  - User feedback collection (was detection accurate?)
  - Daily/historical stats and trends
  - BFRB type management

v4 (Tier 1 + Tier 2):
  [Tier 1 / 2.2]  ML classifier endpoint (/api/predict)
  [Tier 2 / 2.3]  Adaptive threshold calibration (/api/calibrate)
  [Tier 1 / 3.1]  Late multimodal fusion in /api/predict
  [Tier 2 / 2.5]  hand_pose label persisted with each detection

NEW IN v5 (Tier 3 + Tier 4):
  [Tier 3 / 4.1]  Bout detection (/api/bouts/<sid>)
                  Groups consecutive detections of the same type into
                  "bouts" (gap < threshold) for clinical analytics.
  [Tier 3 / 5.2]  WebSocket real-time prediction via Flask-SocketIO.
                  Clients emit 'predict_frame' and receive 'prediction';
                  HTTP /api/predict remains as a fallback.
  [Tier 3 / 6.3]  Pilot-study mode (/api/pilot/*) - structured ground-truth
                  collection for IEEE-grade evaluation.
  [Tier 4 / 4.6]  PWA - manifest + service worker served from /static/.
  [IEEE log]      Per-frame telemetry endpoint (/api/telemetry) +
                  CSV export (/api/export/session/<sid>).

Routes:
  GET  /                          -> Serve the web app
  GET  /api/bfrb-types            -> List all BFRB types
  POST /api/sessions              -> Start a new session
  PUT  /api/sessions/<id>/end     -> End a session
  GET  /api/sessions              -> List all sessions
  GET  /api/sessions/<id>         -> Get session details + detections
  POST /api/detections            -> Log a detection event
  POST /api/feedback              -> Submit user feedback on a detection
  POST /api/predict               -> Run ML classifier (Tier 1 / 2.2)
  POST /api/calibrate             -> Save adaptive threshold (Tier 2 / 2.3)
  GET  /api/calibrate/<sid>       -> Retrieve calibration
  GET  /api/stats/overview        -> Overall lifetime stats
  GET  /api/stats/daily           -> Daily detection counts
  GET  /api/stats/session/<id>    -> Stats for a specific session
  GET  /api/stats/trends          -> Detection trends over time
  GET  /api/model/info            -> Trained model metadata
  GET  /api/bouts/<sid>           -> [Tier 3 / 4.1] Bout aggregation
  POST /api/pilot/start           -> [Tier 3 / 6.3] Start a pilot trial
  PUT  /api/pilot/<id>/end        -> End a pilot trial
  GET  /api/pilot/<id>            -> Get pilot trial result
  GET  /api/pilot                 -> List recent pilot trials
  POST /api/telemetry             -> [IEEE] Batch per-frame telemetry
  GET  /api/export/session/<sid>  -> [IEEE] CSV export of session data

WebSocket events (Tier 3 / 5.2):
  client -> 'predict_frame' { features, rule_score, fusion_w }
  server -> 'prediction'    { ok, probability, fused_score, ... }
  client -> 'telemetry_frame' { session_id, t_ms, ... }
  server -> 'pong'          { server_t_ms }   (latency probe)
"""

from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session
from functools import wraps
import sqlite3
import os
import io
import csv
import json
import time
import hashlib
import secrets
from datetime import datetime, timedelta

# ML deps - model is loaded lazily so the app still starts if these are missing.
try:
    import joblib
    import numpy as np
    _ML_OK = True
except Exception as _ml_err:
    _ML_OK = False
    _ml_err_msg = str(_ml_err)

# WebSocket support (Tier 3 / 5.2) - threading mode works on Windows without
# eventlet/gevent. If flask-socketio is missing we fall back to HTTP-only.
try:
    from flask_socketio import SocketIO, emit
    _WS_OK = True
except Exception as _ws_err:
    _WS_OK = False
    _ws_err_msg = str(_ws_err)

app = Flask(__name__,
            static_url_path="/static",
            static_folder="static")
app.config["SECRET_KEY"] = "bfrb-eneb-2026-secret"

if _WS_OK:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading",
                        logger=False, engineio_logger=False)
else:
    socketio = None
    print(f"[WS] Flask-SocketIO unavailable: {_ws_err_msg}. "
          f"Real-time predictions will use HTTP only.")

# ─── DATABASE SETUP ──────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bfrb_detection.db")


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database schema and seed data."""
    conn = get_db()
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL UNIQUE,
            email       TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name   TEXT,
            onboarding_complete INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS onboarding_responses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            question_key TEXT NOT NULL,
            response    TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS bfrb_types (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT,
            category    TEXT DEFAULT 'general',
            is_custom   INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            input_type      TEXT NOT NULL DEFAULT 'webcam',
            selected_types  TEXT,
            selection_mode  TEXT DEFAULT 'multi',
            start_time      TEXT NOT NULL,
            end_time        TEXT,
            total_detections INTEGER DEFAULT 0,
            total_confirmed  INTEGER DEFAULT 0,
            total_rejected   INTEGER DEFAULT 0,
            notes           TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS detections (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id        INTEGER NOT NULL,
            bfrb_type         TEXT NOT NULL,
            frame_number      INTEGER,
            timestamp_ms      INTEGER NOT NULL,
            confidence_score  REAL NOT NULL,
            smoothed_distance REAL,
            bfrb_score        REAL,
            ml_score          REAL,            -- Tier 1 / 2.2: probability from trained classifier
            fused_score       REAL,            -- Tier 1 / 3.1: late-fusion = w*rule + (1-w)*ml
            hand_pose         TEXT,            -- Tier 2 / 2.5: pinch_grip / open_hand / curled / pointing / fist
            user_confirmed    INTEGER,
            feedback_time     TEXT,
            detected_at       TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS calibrations (
            session_id        INTEGER PRIMARY KEY,
            baseline_distance REAL NOT NULL,   -- hand far from face
            touch_distance    REAL NOT NULL,   -- hand touching face
            alpha             REAL NOT NULL DEFAULT 0.3,
            threshold         REAL NOT NULL,   -- derived: touch + alpha*(baseline - touch)
            extra             TEXT,            -- JSON: per-zone calibrations, etc.
            created_at        TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_feedback (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            detection_id    INTEGER NOT NULL,
            session_id      INTEGER NOT NULL,
            is_accurate     INTEGER NOT NULL,
            bfrb_type       TEXT NOT NULL,
            confidence_at   REAL,
            response_time_ms INTEGER,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        -- [Tier 3 / 6.3] Pilot study trials with structured ground-truth.
        CREATE TABLE IF NOT EXISTS pilot_trials (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id         INTEGER NOT NULL,
            participant_id     TEXT NOT NULL,
            target_gesture     TEXT NOT NULL,
            expected_count     INTEGER NOT NULL DEFAULT 0,
            duration_sec       INTEGER NOT NULL DEFAULT 30,
            start_time         TEXT NOT NULL,
            end_time           TEXT,
            actual_count       INTEGER NOT NULL DEFAULT 0,
            true_positive      INTEGER NOT NULL DEFAULT 0,
            false_positive     INTEGER NOT NULL DEFAULT 0,
            false_negative     INTEGER NOT NULL DEFAULT 0,
            notes              TEXT,
            metrics_json       TEXT,           -- precision/recall/f1 JSON
            created_at         TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        -- [IEEE log] Per-frame structured telemetry (one row per ~250ms batch).
        CREATE TABLE IF NOT EXISTS telemetry (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id         INTEGER NOT NULL,
            timestamp_ms       INTEGER NOT NULL,
            payload_json       TEXT NOT NULL,
            created_at         TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_detections_session ON detections(session_id);
        CREATE INDEX IF NOT EXISTS idx_detections_type ON detections(bfrb_type);
        CREATE INDEX IF NOT EXISTS idx_detections_time ON detections(detected_at);
        CREATE INDEX IF NOT EXISTS idx_feedback_detection ON user_feedback(detection_id);
        CREATE INDEX IF NOT EXISTS idx_feedback_session ON user_feedback(session_id);
        CREATE INDEX IF NOT EXISTS idx_pilot_session ON pilot_trials(session_id);
        CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry(session_id);
        CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp_ms);
    """)

    # Schema migration: ensure new columns exist on legacy detections table
    cursor.execute("PRAGMA table_info(detections)")
    existing = {row[1] for row in cursor.fetchall()}
    for col, decl in [
        ("ml_score",    "REAL"),
        ("fused_score", "REAL"),
        ("hand_pose",   "TEXT"),
    ]:
        if col not in existing:
            cursor.execute(f"ALTER TABLE detections ADD COLUMN {col} {decl}")

    # Seed BFRB types if empty
    count = cursor.execute("SELECT COUNT(*) FROM bfrb_types").fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO bfrb_types (name, description, category, is_custom) VALUES (?, ?, ?, ?)",
            [
                ("Hair Pulling", "Repetitive pulling or tugging of hair from the scalp, eyebrows, or eyelashes (trichotillomania).", "pulling", 0),
                ("Nail Biting", "Bringing fingertips to the mouth and biting the nails or surrounding skin (onychophagia).", "biting", 0),
                ("Skin Picking", "Using fingertips to repeatedly pick, scratch, or squeeze skin (excoriation).", "picking", 0),
                ("Nose Picking", "Inserting a finger into the nostril, detected by fingertip proximity to nose tip (rhinotillexomania).", "picking", 0),
                ("Lip Picking", "Using thumb or fingertip to pick, pull, or bite the lips repeatedly.", "picking", 0),
                ("Face Touching", "Sustained contact of hand with face without specific BFRB pattern.", "touching", 0),
                ("Forehead Touching", "Prolonged hand contact with the forehead region.", "touching", 0),
                ("Cheek Touching", "Prolonged hand contact with the cheek region.", "touching", 0),
            ]
        )

    conn.commit()
    conn.close()


# Initialize on startup
init_db()


# ─── AUTH HELPERS ────────────────────────────────────────────────────────────

def hash_password(password):
    """Hash a password with a random salt using SHA-256."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(stored_hash, password):
    """Verify a password against a stored hash."""
    salt, h = stored_hash.split(":", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == h


def login_required(f):
    """Decorator: redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """Return the current user dict, or None."""
    uid = session.get("user_id")
    if uid is None:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return dict(user) if user else None


# ─── AUTH ROUTES ─────────────────────────────────────────────────────────────

@app.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Username or email already exists"}), 409

    pw_hash = hash_password(password)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO users (username, email, password_hash, full_name)
           VALUES (?, ?, ?, ?)""",
        (username, email, pw_hash, full_name),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session["user_id"] = user_id
    session["username"] = username
    return jsonify({"id": user_id, "username": username, "onboarding_complete": False}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?", (username, username)
    ).fetchone()
    conn.close()

    if not user or not verify_password(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "onboarding_complete": bool(user["onboarding_complete"]),
    })


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "logged_out"})


@app.route("/api/auth/me")
def auth_me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False}), 401
    return jsonify({
        "authenticated": True,
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "onboarding_complete": bool(user["onboarding_complete"]),
    })


# ─── ONBOARDING ─────────────────────────────────────────────────────────────

@app.route("/api/onboarding", methods=["POST"])
def save_onboarding():
    """Save onboarding questionnaire responses."""
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    responses = data.get("responses") or {}

    conn = get_db()
    cursor = conn.cursor()
    # Clear old responses
    cursor.execute("DELETE FROM onboarding_responses WHERE user_id = ?", (uid,))
    for key, value in responses.items():
        cursor.execute(
            "INSERT INTO onboarding_responses (user_id, question_key, response) VALUES (?, ?, ?)",
            (uid, key, json.dumps(value) if not isinstance(value, str) else value),
        )
    cursor.execute("UPDATE users SET onboarding_complete = 1 WHERE id = ?", (uid,))
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"}), 201


@app.route("/api/onboarding")
def get_onboarding():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT question_key, response FROM onboarding_responses WHERE user_id = ?",
        (uid,)
    ).fetchall()
    conn.close()

    responses = {}
    for r in rows:
        try:
            responses[r["question_key"]] = json.loads(r["response"])
        except (json.JSONDecodeError, TypeError):
            responses[r["question_key"]] = r["response"]
    return jsonify(responses)


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    return render_template("index.html")


# ─── BFRB TYPES ──────────────────────────────────────────────────────────────

@app.route("/api/bfrb-types")
def get_bfrb_types():
    conn = get_db()
    types = conn.execute("SELECT * FROM bfrb_types ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(t) for t in types])


# ─── SESSIONS ────────────────────────────────────────────────────────────────

@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    conn = get_db()
    sessions = conn.execute(
        "SELECT * FROM sessions ORDER BY start_time DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return jsonify([dict(s) for s in sessions])


@app.route("/api/sessions", methods=["POST"])
def create_session():
    data = request.get_json(silent=True) or {}
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sessions (input_type, selected_types, selection_mode, start_time)
           VALUES (?, ?, ?, datetime('now'))""",
        (
            data.get("input_type", "webcam"),
            json.dumps(data.get("selected_types", [])),
            data.get("selection_mode", "multi"),
        )
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": session_id, "status": "started"}), 201


@app.route("/api/sessions/<int:session_id>/end", methods=["PUT"])
def end_session(session_id):
    conn = get_db()
    # Count stats
    stats = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN user_confirmed = 1 THEN 1 ELSE 0 END) as confirmed,
            SUM(CASE WHEN user_confirmed = 0 THEN 1 ELSE 0 END) as rejected
        FROM detections WHERE session_id = ?
    """, (session_id,)).fetchone()

    conn.execute(
        """UPDATE sessions
           SET end_time = datetime('now'),
               total_detections = ?,
               total_confirmed = ?,
               total_rejected = ?
           WHERE id = ?""",
        (stats["total"], stats["confirmed"] or 0, stats["rejected"] or 0, session_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ended"})


@app.route("/api/sessions/<int:session_id>")
def get_session(session_id):
    conn = get_db()
    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        conn.close()
        return jsonify({"error": "Session not found"}), 404

    detections = conn.execute(
        "SELECT * FROM detections WHERE session_id = ? ORDER BY timestamp_ms",
        (session_id,)
    ).fetchall()

    feedback = conn.execute(
        "SELECT * FROM user_feedback WHERE session_id = ? ORDER BY created_at",
        (session_id,)
    ).fetchall()

    conn.close()
    return jsonify({
        "session": dict(session),
        "detections": [dict(d) for d in detections],
        "feedback": [dict(f) for f in feedback],
    })


# ─── DETECTIONS ──────────────────────────────────────────────────────────────

@app.route("/api/detections", methods=["POST"])
def log_detection():
    data = request.get_json(silent=True) or {}
    required = ["session_id", "bfrb_type", "timestamp_ms", "confidence_score"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO detections
           (session_id, bfrb_type, frame_number, timestamp_ms, confidence_score,
            smoothed_distance, bfrb_score, ml_score, fused_score, hand_pose)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["session_id"],
            data["bfrb_type"],
            data.get("frame_number", 0),
            data["timestamp_ms"],
            data["confidence_score"],
            data.get("smoothed_distance"),
            data.get("bfrb_score"),
            data.get("ml_score"),
            data.get("fused_score"),
            data.get("hand_pose"),
        )
    )
    detection_id = cursor.lastrowid

    # Update session detection count
    conn.execute(
        "UPDATE sessions SET total_detections = total_detections + 1 WHERE id = ?",
        (data["session_id"],)
    )

    conn.commit()
    conn.close()
    return jsonify({"id": detection_id}), 201


# ─── FEEDBACK ────────────────────────────────────────────────────────────────

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json(silent=True) or {}
    required = ["detection_id", "session_id", "is_accurate", "bfrb_type"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Insert feedback record
    cursor.execute(
        """INSERT INTO user_feedback
           (detection_id, session_id, is_accurate, bfrb_type, confidence_at, response_time_ms)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            data["detection_id"],
            data["session_id"],
            1 if data["is_accurate"] else 0,
            data["bfrb_type"],
            data.get("confidence_at"),
            data.get("response_time_ms"),
        )
    )

    # Update detection with feedback
    confirmed = 1 if data["is_accurate"] else 0
    conn.execute(
        "UPDATE detections SET user_confirmed = ?, feedback_time = datetime('now') WHERE id = ?",
        (confirmed, data["detection_id"])
    )

    # Update session counters
    if data["is_accurate"]:
        conn.execute(
            "UPDATE sessions SET total_confirmed = total_confirmed + 1 WHERE id = ?",
            (data["session_id"],)
        )
    else:
        conn.execute(
            "UPDATE sessions SET total_rejected = total_rejected + 1 WHERE id = ?",
            (data["session_id"],)
        )

    conn.commit()
    conn.close()
    return jsonify({"status": "recorded"}), 201


# ─── STATS ───────────────────────────────────────────────────────────────────

@app.route("/api/stats/overview")
def stats_overview():
    conn = get_db()

    totals = conn.execute("""
        SELECT
            COUNT(*) as total_detections,
            SUM(CASE WHEN user_confirmed = 1 THEN 1 ELSE 0 END) as confirmed,
            SUM(CASE WHEN user_confirmed = 0 THEN 1 ELSE 0 END) as rejected,
            AVG(confidence_score) as avg_confidence,
            COUNT(DISTINCT session_id) as total_sessions
        FROM detections
    """).fetchone()

    by_type = conn.execute("""
        SELECT bfrb_type, COUNT(*) as count,
               AVG(confidence_score) as avg_confidence,
               SUM(CASE WHEN user_confirmed = 1 THEN 1 ELSE 0 END) as confirmed,
               SUM(CASE WHEN user_confirmed = 0 THEN 1 ELSE 0 END) as rejected
        FROM detections
        GROUP BY bfrb_type
        ORDER BY count DESC
    """).fetchall()

    session_count = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]

    # Accuracy rate (only counting detections with feedback)
    feedback_stats = conn.execute("""
        SELECT
            COUNT(*) as total_feedback,
            SUM(CASE WHEN is_accurate = 1 THEN 1 ELSE 0 END) as accurate
        FROM user_feedback
    """).fetchone()

    accuracy = 0
    if feedback_stats["total_feedback"] > 0:
        accuracy = round(feedback_stats["accurate"] / feedback_stats["total_feedback"] * 100, 1)

    conn.close()
    return jsonify({
        "total_detections": totals["total_detections"],
        "total_confirmed": totals["confirmed"] or 0,
        "total_rejected": totals["rejected"] or 0,
        "avg_confidence": round(totals["avg_confidence"] or 0, 3),
        "total_sessions": session_count,
        "accuracy_rate": accuracy,
        "total_feedback": feedback_stats["total_feedback"],
        "by_type": [dict(t) for t in by_type],
    })


@app.route("/api/stats/daily")
def stats_daily():
    days = request.args.get("days", 30, type=int)
    conn = get_db()
    daily = conn.execute("""
        SELECT
            DATE(detected_at) as date,
            COUNT(*) as detections,
            COUNT(DISTINCT session_id) as sessions,
            AVG(confidence_score) as avg_confidence,
            SUM(CASE WHEN user_confirmed = 1 THEN 1 ELSE 0 END) as confirmed,
            SUM(CASE WHEN user_confirmed = 0 THEN 1 ELSE 0 END) as rejected
        FROM detections
        WHERE detected_at >= datetime('now', ?)
        GROUP BY DATE(detected_at)
        ORDER BY date
    """, (f"-{days} days",)).fetchall()
    conn.close()
    return jsonify([dict(d) for d in daily])


@app.route("/api/stats/session/<int:session_id>")
def stats_session(session_id):
    conn = get_db()

    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        conn.close()
        return jsonify({"error": "Session not found"}), 404

    by_type = conn.execute("""
        SELECT bfrb_type, COUNT(*) as count,
               AVG(confidence_score) as avg_confidence,
               MIN(timestamp_ms) as first_ms,
               MAX(timestamp_ms) as last_ms
        FROM detections
        WHERE session_id = ?
        GROUP BY bfrb_type
    """, (session_id,)).fetchall()

    timeline = conn.execute("""
        SELECT timestamp_ms, bfrb_type, confidence_score, user_confirmed
        FROM detections
        WHERE session_id = ?
        ORDER BY timestamp_ms
    """, (session_id,)).fetchall()

    conn.close()
    return jsonify({
        "session": dict(session),
        "by_type": [dict(t) for t in by_type],
        "timeline": [dict(t) for t in timeline],
    })


@app.route("/api/stats/trends")
def stats_trends():
    """Hourly detection trend for today, plus weekly summary."""
    conn = get_db()

    hourly = conn.execute("""
        SELECT
            strftime('%H', detected_at) as hour,
            COUNT(*) as detections
        FROM detections
        WHERE DATE(detected_at) = DATE('now')
        GROUP BY strftime('%H', detected_at)
        ORDER BY hour
    """).fetchall()

    weekly = conn.execute("""
        SELECT
            strftime('%w', detected_at) as day_of_week,
            COUNT(*) as detections,
            AVG(confidence_score) as avg_confidence
        FROM detections
        WHERE detected_at >= datetime('now', '-7 days')
        GROUP BY strftime('%w', detected_at)
        ORDER BY day_of_week
    """).fetchall()

    conn.close()
    return jsonify({
        "hourly": [dict(h) for h in hourly],
        "weekly": [dict(w) for w in weekly],
    })


# ─── ML CLASSIFIER (Tier 1 / 2.2 + 3.1) ─────────────────────────────────────
#
# The trained Random-Forest classifier is loaded once on startup. It expects a
# 16-dimensional feature vector in the *Kaggle scaled space*. The web client
# computes those 16 features from MediaPipe landmarks (see index.html
# extractMLFeatures()) and POSTs them here — the same model that powers the
# offline ML pipeline now powers the live web app, bridging ENEB456 + ENEB453.

MODEL_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "bfrb_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
META_PATH   = os.path.join(MODEL_DIR, "feature_meta.json")

_ML_MODEL = None
_ML_SCALER = None
_ML_META = None


def _load_ml_model():
    """Load classifier + scaler + metadata. Cached after first call."""
    global _ML_MODEL, _ML_SCALER, _ML_META
    if not _ML_OK:
        return None
    if _ML_MODEL is not None:
        return _ML_MODEL

    if not (os.path.exists(MODEL_PATH) and os.path.exists(META_PATH)):
        print(f"[ML] Model files not found in {MODEL_DIR} — /api/predict will be disabled.")
        return None

    try:
        _ML_MODEL  = joblib.load(MODEL_PATH)
        _ML_SCALER = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else None
        with open(META_PATH, "r", encoding="utf-8") as f:
            _ML_META = json.load(f)
        print(f"[ML] Loaded {type(_ML_MODEL).__name__} with "
              f"{len(_ML_META.get('feature_names', []))} features.")
        return _ML_MODEL
    except Exception as e:
        print(f"[ML] Failed to load model: {e}")
        return None


# Try to load at import time so the first request is fast.
_load_ml_model()


@app.route("/api/model/info")
def model_info():
    if _load_ml_model() is None:
        return jsonify({"loaded": False, "reason": "model files unavailable"}), 200
    return jsonify({
        "loaded":           True,
        "model_type":       type(_ML_MODEL).__name__,
        "feature_names":    _ML_META.get("feature_names", []),
        "scaler_min":       _ML_META.get("scaler_min", []),
        "scaler_max":       _ML_META.get("scaler_max", []),
        "training_date":    _ML_META.get("training_date"),
        "n_sequences":      _ML_META.get("n_sequences"),
        "n_bfrb":           _ML_META.get("n_bfrb"),
        "n_no_bfrb":        _ML_META.get("n_no_bfrb"),
        "mediapipe_normalization": _ML_META.get("mediapipe_normalization", {}),
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    """Tier 1 / 2.2 + 3.1 — run ML classifier on a feature vector and (optionally)
    fuse with the rule-based score (late fusion).

    Body JSON:
      {
        "features":     [16 floats],            (required, already in [0,1] space)
        "rule_score":   float in [0,1] | null,  (optional, for late fusion)
        "fusion_w":     float in [0,1]          (optional weight for ML;
                                                 default 0.6 → 60% ML / 40% rule)
      }

    Returns:
      {
        "ok": true, "is_bfrb": 0|1,
        "probability": float,        (P[BFRB] from the classifier)
        "fused_score": float | null, (late-fusion score in [0,1])
        "decision":    "bfrb" | "no_bfrb"
      }
    """
    if _load_ml_model() is None:
        return jsonify({"ok": False, "error": "model not loaded"}), 503

    data = request.get_json(silent=True) or {}
    feats = data.get("features")
    feature_names = _ML_META.get("feature_names", [])
    if not isinstance(feats, list) or len(feats) != len(feature_names):
        return jsonify({
            "ok": False,
            "error": f"features must be a list of {len(feature_names)} floats",
            "expected_features": feature_names,
        }), 400

    try:
        x = np.asarray(feats, dtype=float).reshape(1, -1)
        x = np.nan_to_num(x, nan=0.0, posinf=1.0, neginf=0.0)
        proba = _ML_MODEL.predict_proba(x)[0]
        # The training pipeline labels: 0 = No-BFRB, 1 = BFRB
        # Detect the BFRB index defensively — if the classifier was trained
        # with a different label ordering we still pick the larger class id.
        classes = list(_ML_MODEL.classes_)
        bfrb_idx = classes.index(1) if 1 in classes else int(np.argmax(classes))
        p_bfrb = float(proba[bfrb_idx])
        is_bfrb = int(p_bfrb >= 0.5)

        fused = None
        rule_score = data.get("rule_score")
        if rule_score is not None:
            try:
                w_ml = float(data.get("fusion_w", 0.6))
                w_ml = max(0.0, min(1.0, w_ml))
                fused = w_ml * p_bfrb + (1.0 - w_ml) * float(rule_score)
            except Exception:
                fused = None

        return jsonify({
            "ok": True,
            "is_bfrb": is_bfrb,
            "probability": p_bfrb,
            "fused_score": fused,
            "decision": "bfrb" if (fused if fused is not None else p_bfrb) >= 0.5 else "no_bfrb",
        })
    except Exception as e:
        return jsonify({"ok": False, "error": f"inference failed: {e}"}), 500


# ─── ADAPTIVE THRESHOLD CALIBRATION (Tier 2 / 2.3) ──────────────────────────

@app.route("/api/calibrate", methods=["POST"])
def save_calibration():
    """Persist a per-session calibration measurement.

    Body:
      {
        "session_id":         int (required),
        "baseline_distance":  float (required, hand far from face),
        "touch_distance":     float (required, hand touching face),
        "alpha":              float [0,1] (optional, default 0.3),
        "extra":              object (optional)
      }
    Threshold is derived as:
        threshold = touch + alpha * (baseline - touch)
    """
    data = request.get_json(silent=True) or {}
    sid = data.get("session_id")
    base = data.get("baseline_distance")
    touch = data.get("touch_distance")
    alpha = float(data.get("alpha", 0.3))
    if sid is None or base is None or touch is None:
        return jsonify({"error": "session_id, baseline_distance and touch_distance required"}), 400

    base = float(base); touch = float(touch)
    if base <= touch:
        return jsonify({"error": "baseline_distance must be greater than touch_distance"}), 400

    threshold = touch + alpha * (base - touch)
    extra_json = json.dumps(data.get("extra") or {})

    conn = get_db()
    conn.execute(
        """INSERT INTO calibrations (session_id, baseline_distance, touch_distance,
                                     alpha, threshold, extra)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(session_id) DO UPDATE SET
              baseline_distance=excluded.baseline_distance,
              touch_distance=excluded.touch_distance,
              alpha=excluded.alpha,
              threshold=excluded.threshold,
              extra=excluded.extra,
              created_at=datetime('now')""",
        (int(sid), base, touch, alpha, threshold, extra_json),
    )
    conn.commit()
    conn.close()
    return jsonify({
        "session_id": int(sid),
        "baseline_distance": base,
        "touch_distance":    touch,
        "alpha":             alpha,
        "threshold":         threshold,
    }), 201


@app.route("/api/calibrate/<int:session_id>")
def get_calibration(session_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM calibrations WHERE session_id = ?",
                       (session_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"calibrated": False}), 200
    d = dict(row)
    try:
        d["extra"] = json.loads(d.get("extra") or "{}")
    except Exception:
        d["extra"] = {}
    d["calibrated"] = True
    return jsonify(d)


# ─── LEGACY ROUTES (backward compat) ────────────────────────────────────────

@app.route("/status")
def status():
    return jsonify({
        "status":   "ok",
        "engine":   "v5-fused-ml-rule-ws",
        "database": "sqlite",
        "ml_model_loaded": _load_ml_model() is not None,
        "websocket_enabled": _WS_OK,
    })


# ─── BOUTS  (Tier 3 / 4.1) ───────────────────────────────────────────────────
#
# A "bout" is a contiguous burst of detections of the same BFRB type, separated
# from neighbouring bursts by a gap > GAP_THRESHOLD seconds. This is the unit
# of analysis used in clinical BFRB studies (vs raw detection counts).

@app.route("/api/bouts/<int:session_id>")
def get_bouts(session_id):
    gap_sec   = float(request.args.get("gap", 5.0))
    min_count = int(request.args.get("min_count", 1))

    conn = get_db()
    rows = conn.execute(
        """SELECT id, bfrb_type, timestamp_ms, confidence_score, fused_score, hand_pose
           FROM detections
           WHERE session_id = ?
           ORDER BY timestamp_ms""",
        (session_id,)
    ).fetchall()
    conn.close()

    bouts = []
    current = None
    gap_ms = int(gap_sec * 1000)
    for r in rows:
        d = dict(r)
        if (current is None
            or d["bfrb_type"] != current["bfrb_type"]
            or d["timestamp_ms"] - current["last_ms"] > gap_ms):
            if current is not None and current["count"] >= min_count:
                bouts.append(current)
            current = {
                "bfrb_type":  d["bfrb_type"],
                "start_ms":   d["timestamp_ms"],
                "last_ms":    d["timestamp_ms"],
                "count":      1,
                "detection_ids": [d["id"]],
                "max_confidence": d["confidence_score"] or 0.0,
                "max_fused":      d["fused_score"] or 0.0,
            }
        else:
            current["last_ms"] = d["timestamp_ms"]
            current["count"]  += 1
            current["detection_ids"].append(d["id"])
            if (d["confidence_score"] or 0.0) > current["max_confidence"]:
                current["max_confidence"] = d["confidence_score"]
            if (d["fused_score"] or 0.0) > current["max_fused"]:
                current["max_fused"] = d["fused_score"]

    if current is not None and current["count"] >= min_count:
        bouts.append(current)

    for b in bouts:
        b["duration_ms"] = b["last_ms"] - b["start_ms"]

    return jsonify({
        "session_id": session_id,
        "gap_threshold_sec": gap_sec,
        "min_count": min_count,
        "n_bouts": len(bouts),
        "n_detections": sum(b["count"] for b in bouts),
        "bouts": bouts,
    })


# ─── PILOT STUDY  (Tier 3 / 6.3) ─────────────────────────────────────────────

@app.route("/api/pilot", methods=["GET"])
def list_pilots():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM pilot_trials ORDER BY start_time DESC LIMIT 50"
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        try: d["metrics"] = json.loads(d.pop("metrics_json") or "{}")
        except Exception: d["metrics"] = {}
        out.append(d)
    return jsonify(out)


@app.route("/api/pilot/start", methods=["POST"])
def start_pilot():
    """Begin a structured ground-truth trial.

    Body:  { session_id, participant_id, target_gesture, expected_count,
             duration_sec }
    """
    data = request.get_json(silent=True) or {}
    required = ["session_id", "participant_id", "target_gesture"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing required fields: {required}"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO pilot_trials
           (session_id, participant_id, target_gesture, expected_count,
            duration_sec, start_time)
           VALUES (?, ?, ?, ?, ?, datetime('now'))""",
        (
            int(data["session_id"]),
            str(data["participant_id"]),
            str(data["target_gesture"]),
            int(data.get("expected_count") or 0),
            int(data.get("duration_sec") or 30),
        ),
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"pilot_id": pid, "status": "started"}), 201


@app.route("/api/pilot/<int:pilot_id>/end", methods=["PUT"])
def end_pilot(pilot_id):
    """Finalize a pilot trial with ground-truth labels.

    Body:  { actual_count, true_positive, false_positive, false_negative,
             notes }
    Computes precision, recall, F1 from the supplied confusion-matrix counts.
    """
    data = request.get_json(silent=True) or {}
    tp = int(data.get("true_positive") or 0)
    fp = int(data.get("false_positive") or 0)
    fn = int(data.get("false_negative") or 0)
    actual_count = int(data.get("actual_count") or (tp + fp))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    metrics = {
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
        "tp": tp, "fp": fp, "fn": fn,
    }

    conn = get_db()
    conn.execute(
        """UPDATE pilot_trials
           SET end_time = datetime('now'),
               actual_count = ?,
               true_positive = ?,
               false_positive = ?,
               false_negative = ?,
               notes = ?,
               metrics_json = ?
           WHERE id = ?""",
        (actual_count, tp, fp, fn, data.get("notes"), json.dumps(metrics), pilot_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"pilot_id": pilot_id, "status": "ended", "metrics": metrics})


@app.route("/api/pilot/<int:pilot_id>")
def get_pilot(pilot_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM pilot_trials WHERE id = ?", (pilot_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Pilot not found"}), 404
    d = dict(row)
    try: d["metrics"] = json.loads(d.pop("metrics_json") or "{}")
    except Exception: d["metrics"] = {}
    return jsonify(d)


# ─── IEEE TELEMETRY  ─────────────────────────────────────────────────────────
#
# /api/telemetry takes a batch of per-frame events. The web client buffers
# ~50 frames (~2s) and POSTs them at once to keep traffic low while preserving
# every observation. Stored as a JSON blob per row for forward-compat.

@app.route("/api/telemetry", methods=["POST"])
def post_telemetry():
    data = request.get_json(silent=True) or {}
    sid = data.get("session_id")
    events = data.get("events") or []
    if sid is None or not isinstance(events, list):
        return jsonify({"error": "session_id and events[] required"}), 400
    if not events:
        return jsonify({"stored": 0})

    conn = get_db()
    cur = conn.cursor()
    rows = []
    for e in events:
        try:
            ts = int(e.get("t_ms") or 0)
        except Exception:
            ts = 0
        rows.append((int(sid), ts, json.dumps(e, default=float)))
    cur.executemany(
        "INSERT INTO telemetry (session_id, timestamp_ms, payload_json) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    return jsonify({"stored": len(rows)})


# ─── CSV EXPORT  (IEEE artifact) ─────────────────────────────────────────────

@app.route("/api/export/session/<int:session_id>")
def export_session_csv(session_id):
    """Streamed multi-section CSV (detections + bouts + telemetry summary)."""
    conn = get_db()
    sess = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not sess:
        conn.close()
        return jsonify({"error": "session not found"}), 404
    detections = conn.execute(
        "SELECT * FROM detections WHERE session_id = ? ORDER BY timestamp_ms",
        (session_id,)
    ).fetchall()
    feedbacks = conn.execute(
        "SELECT * FROM user_feedback WHERE session_id = ? ORDER BY id",
        (session_id,)
    ).fetchall()
    telemetry = conn.execute(
        "SELECT timestamp_ms, payload_json FROM telemetry WHERE session_id = ? ORDER BY timestamp_ms",
        (session_id,)
    ).fetchall()
    pilots = conn.execute(
        "SELECT * FROM pilot_trials WHERE session_id = ?",
        (session_id,)
    ).fetchall()
    conn.close()

    # Assemble multi-section CSV in memory.
    buf = io.StringIO()
    w = csv.writer(buf)

    w.writerow(["# BFRB Detection - Session Export"])
    w.writerow(["# session_id", session_id])
    w.writerow(["# generated_at", datetime.utcnow().isoformat() + "Z"])
    w.writerow(["# Section: SESSION"])
    w.writerow(list(sess.keys()))
    w.writerow(list(sess))

    w.writerow([])
    w.writerow(["# Section: DETECTIONS"])
    if detections:
        w.writerow(list(detections[0].keys()))
        for r in detections:
            w.writerow(list(r))

    w.writerow([])
    w.writerow(["# Section: FEEDBACK"])
    if feedbacks:
        w.writerow(list(feedbacks[0].keys()))
        for r in feedbacks:
            w.writerow(list(r))

    w.writerow([])
    w.writerow(["# Section: PILOT_TRIALS"])
    if pilots:
        w.writerow(list(pilots[0].keys()))
        for r in pilots:
            w.writerow(list(r))

    w.writerow([])
    w.writerow(["# Section: TELEMETRY  (one row per frame batch, payload is JSON)"])
    w.writerow(["timestamp_ms", "payload_json"])
    for r in telemetry:
        w.writerow([r["timestamp_ms"], r["payload_json"]])

    csv_bytes = buf.getvalue().encode("utf-8")
    fname = f"bfrb_session_{session_id}.csv"
    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


# ─── PWA SHELL FILES  (Tier 4 / 4.6) ─────────────────────────────────────────

@app.route("/manifest.json")
def manifest_root():
    """Allow /manifest.json shorthand for the PWA manifest."""
    return app.send_static_file("manifest.json")


@app.route("/service-worker.js")
def service_worker_root():
    """Service worker is served from / so its scope is the entire app."""
    response = app.send_static_file("service-worker.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


# ─── WEBSOCKET REAL-TIME PREDICTION  (Tier 3 / 5.2) ──────────────────────────
#
# Real-time event handlers. Designed to be a near-zero-latency replacement for
# the HTTP /api/predict endpoint - same business logic, no per-call HTTP cost.

if socketio is not None:

    @socketio.on("connect")
    def _ws_connect():
        emit("hello", {
            "ok": True,
            "ml_model_loaded": _load_ml_model() is not None,
            "server_time_ms":  int(time.time() * 1000),
        })

    @socketio.on("ping_latency")
    def _ws_ping(data):
        emit("pong_latency", {
            "client_t_ms": (data or {}).get("client_t_ms"),
            "server_t_ms": int(time.time() * 1000),
        })

    @socketio.on("predict_frame")
    def _ws_predict(data):
        """Same shape as POST /api/predict, but over a persistent WS."""
        if _load_ml_model() is None:
            emit("prediction", {"ok": False, "error": "model not loaded"})
            return

        feats = (data or {}).get("features")
        feature_names = _ML_META.get("feature_names", [])
        if not isinstance(feats, list) or len(feats) != len(feature_names):
            emit("prediction", {"ok": False,
                                "error": f"features must be {len(feature_names)} floats"})
            return

        try:
            x = np.asarray(feats, dtype=float).reshape(1, -1)
            x = np.nan_to_num(x, nan=0.0, posinf=1.0, neginf=0.0)
            proba = _ML_MODEL.predict_proba(x)[0]
            classes = list(_ML_MODEL.classes_)
            bfrb_idx = classes.index(1) if 1 in classes else int(np.argmax(classes))
            p_bfrb = float(proba[bfrb_idx])
            is_bfrb = int(p_bfrb >= 0.5)

            fused = None
            rule_score = (data or {}).get("rule_score")
            if rule_score is not None:
                try:
                    w_ml = float((data or {}).get("fusion_w", 0.6))
                    w_ml = max(0.0, min(1.0, w_ml))
                    fused = w_ml * p_bfrb + (1.0 - w_ml) * float(rule_score)
                except Exception:
                    fused = None

            emit("prediction", {
                "ok": True,
                "is_bfrb": is_bfrb,
                "probability": p_bfrb,
                "fused_score": fused,
                "decision": "bfrb" if (fused if fused is not None else p_bfrb) >= 0.5 else "no_bfrb",
                "client_seq": (data or {}).get("seq"),       # echo for ordering
                "server_t_ms": int(time.time() * 1000),
            })
        except Exception as e:
            emit("prediction", {"ok": False, "error": f"inference failed: {e}"})

    @socketio.on("telemetry_frame")
    def _ws_telemetry(data):
        """Optional WS path for per-frame telemetry; we just persist it."""
        try:
            sid = int((data or {}).get("session_id") or 0)
            ts  = int((data or {}).get("t_ms") or 0)
        except Exception:
            return
        if sid <= 0:
            return
        conn = get_db()
        conn.execute(
            "INSERT INTO telemetry (session_id, timestamp_ms, payload_json) VALUES (?, ?, ?)",
            (sid, ts, json.dumps(data, default=float)),
        )
        conn.commit()
        conn.close()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== BFRB Detection Web App  (v5: rule + ML + late-fusion + WS + PWA) ===")
    print(f"Database:        {DB_PATH}")
    print(f"WebSocket:       {'ENABLED (Flask-SocketIO threading mode)' if _WS_OK else 'DISABLED (HTTP fallback only)'}")
    print(f"ML model loaded: {_load_ml_model() is not None}")
    print("Open http://localhost:5000 in your browser\n")
    if socketio is not None:
        socketio.run(app, debug=False, host="0.0.0.0", port=5000,
                     allow_unsafe_werkzeug=True)
    else:
        app.run(debug=False, host="0.0.0.0", port=5000)
