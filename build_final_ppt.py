"""
Build the ENEB453 Final Project Defense Presentation (25 minutes)
BFRB Detection System - Nishanth S. | University of Maryland
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "ENEB453_Final_Defense_NishanthS.pptx")

# ── Colors (White + Dark Blue Professional Theme) ──
NAVY      = RGBColor(0x1A, 0x3A, 0x5C)
NAVY_DARK = RGBColor(0x0F, 0x25, 0x3D)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG  = RGBColor(0xF0, 0xF4, 0xF8)
TEXT_DARK = RGBColor(0x1A, 0x23, 0x32)
TEXT_DIM  = RGBColor(0x5A, 0x6A, 0x7E)
ACCENT_RED = RGBColor(0xD9, 0x53, 0x4F)
GREEN     = RGBColor(0x2E, 0x8B, 0x57)
GOLD      = RGBColor(0xD4, 0x88, 0x0F)
BLUE_LT   = RGBColor(0x2A, 0x6C, 0xB6)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H


# ── Helpers ──────────────────────────────────────────────
def add_bg(slide, color=NAVY):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, w, h, color):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_text_box(slide, left, top, w, h, text, size=18, color=WHITE,
                 bold=False, align=PP_ALIGN.LEFT, font_name="Segoe UI"):
    txBox = slide.shapes.add_textbox(left, top, w, h)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = align
    return txBox


def add_bullet_slide(title, bullets, speaker_notes="", bg_color=NAVY):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, bg_color)
    # Top accent bar
    add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.06), ACCENT_RED)
    # Title
    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.8),
                 title, size=36, color=WHITE, bold=True)
    # Underline
    add_rect(slide, Inches(0.8), Inches(1.15), Inches(2.5), Inches(0.04), ACCENT_RED)
    # Bullets
    y = Inches(1.6)
    for bullet in bullets:
        if bullet.startswith("**"):
            # Sub-header
            clean = bullet.strip("*")
            add_text_box(slide, Inches(1.0), y, Inches(10.5), Inches(0.5),
                         clean, size=20, color=GOLD, bold=True)
            y += Inches(0.45)
        else:
            add_text_box(slide, Inches(1.2), y, Inches(10.5), Inches(0.45),
                         bullet, size=18, color=WHITE)
            y += Inches(0.42)
    # Slide number
    add_text_box(slide, Inches(12.3), Inches(7.0), Inches(0.8), Inches(0.3),
                 str(len(prs.slides)), size=10, color=TEXT_DIM,
                 align=PP_ALIGN.RIGHT)
    # Speaker notes
    if speaker_notes:
        slide.notes_slide.notes_text_frame.text = speaker_notes
    return slide


def add_two_col_slide(title, left_items, right_items, speaker_notes=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, NAVY)
    add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.06), ACCENT_RED)
    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.8),
                 title, size=36, color=WHITE, bold=True)
    add_rect(slide, Inches(0.8), Inches(1.15), Inches(2.5), Inches(0.04), ACCENT_RED)
    # Left column
    y = Inches(1.6)
    for item in left_items:
        add_text_box(slide, Inches(0.8), y, Inches(5.5), Inches(0.42),
                     item, size=17, color=WHITE)
        y += Inches(0.40)
    # Right column
    y = Inches(1.6)
    for item in right_items:
        add_text_box(slide, Inches(6.8), y, Inches(5.5), Inches(0.42),
                     item, size=17, color=WHITE)
        y += Inches(0.40)
    add_text_box(slide, Inches(12.3), Inches(7.0), Inches(0.8), Inches(0.3),
                 str(len(prs.slides)), size=10, color=TEXT_DIM,
                 align=PP_ALIGN.RIGHT)
    if speaker_notes:
        slide.notes_slide.notes_text_frame.text = speaker_notes
    return slide


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 1: TITLE
# ═══════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, NAVY_DARK)
add_rect(slide, Inches(0), Inches(3.2), SLIDE_W, Inches(0.06), ACCENT_RED)
add_text_box(slide, Inches(1), Inches(1.5), Inches(11), Inches(1.2),
             "BFRB Detection System", size=52, color=WHITE, bold=True,
             align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(2.6), Inches(11), Inches(0.6),
             "Real-Time Webcam-Based Body-Focused Repetitive Behavior Detection",
             size=22, color=LIGHT_BG, align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(3.8), Inches(11), Inches(0.5),
             "ENEB453 Final Project Defense", size=20, color=GOLD,
             bold=True, align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(4.6), Inches(11), Inches(0.5),
             "Nishanth S.  |  University of Maryland  |  Spring 2026",
             size=18, color=TEXT_DIM, align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(5.3), Inches(11), Inches(0.5),
             "May 11, 2026", size=16, color=TEXT_DIM, align=PP_ALIGN.CENTER)
slide.notes_slide.notes_text_frame.text = (
    "Good afternoon. I'm Nishanth, and today I'll be presenting my ENEB453 "
    "final project: a real-time BFRB detection system. BFRBs are body-focused "
    "repetitive behaviors like hair pulling, nail biting, and skin picking that "
    "affect millions of people. My system uses webcam computer vision and machine "
    "learning to detect these behaviors in real time."
)

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2: AGENDA
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Presentation Agenda", [
    "1.  Problem Statement: What are BFRBs and why detect them?",
    "2.  System Architecture: Tech stack and design decisions",
    "3.  Database Design: Schema, 3NF normalization, ERD",
    "4.  Backend Implementation: Flask API, session management",
    "5.  ML Pipeline: Random Forest classifier, feature engineering",
    "6.  Frontend UI: Real-time detection dashboard",
    "7.  Authentication & Onboarding: User management",
    "8.  Advanced Features: Calibration, bouts, pilot studies, PWA",
    "9.  Live Demonstration",
    "10. Results, Challenges & Future Work",
    "11. Q&A",
], "Walk through the agenda. Mention this is a 25-minute presentation with a live demo.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 3: PROBLEM STATEMENT
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Problem Statement: BFRBs", [
    "**What are BFRBs?**",
    "Body-Focused Repetitive Behaviors: compulsive self-grooming actions",
    "Hair pulling (trichotillomania), nail biting, skin picking, face touching",
    "Affects 2-5% of the population worldwide",
    "",
    "**The Challenge**",
    "Most people are UNAWARE when they're engaging in BFRBs",
    "Awareness is the first step to behavioral change",
    "Current solutions: rubber bands, journals, therapy alone",
    "",
    "**Our Solution**",
    "Real-time webcam detection using computer vision + ML",
    "Immediate visual alerts when BFRB is detected",
    "Track patterns over time for therapy support",
], "Explain the clinical significance. 2-5% of population = millions of people. "
   "Most people don't realize they're pulling hair or biting nails until after. "
   "Our system provides real-time awareness through webcam monitoring.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4: SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════
add_two_col_slide("System Architecture",
    [
        "--- Frontend ---",
        "HTML5, CSS3, Vanilla JavaScript",
        "MediaPipe Holistic (face + hand tracking)",
        "Chart.js (statistical dashboard)",
        "Socket.IO client (real-time)",
        "Progressive Web App (PWA)",
        "",
        "--- Computer Vision ---",
        "468 face landmarks per frame",
        "21 hand landmarks per frame",
        "One Euro Filter for smoothing",
        "13 anatomical face zones",
    ],
    [
        "--- Backend ---",
        "Python 3.11 + Flask 2.3",
        "SQLite (embedded database)",
        "Flask-SocketIO (WebSocket)",
        "scikit-learn (ML inference)",
        "",
        "--- ML Pipeline ---",
        "Random Forest classifier",
        "16 semantic features",
        "Trained on Kaggle CMI dataset",
        "574,945 readings, 8,151 sequences",
        "Late multimodal fusion",
    ],
    "Two main components: the browser handles video capture and landmark extraction, "
    "the Flask backend handles ML inference, data persistence, and session management. "
    "Explain how MediaPipe runs in the browser for privacy - video never leaves the device.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 5: DATABASE DESIGN
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Database Design (3NF Normalized)", [
    "**9 Tables in Third Normal Form (3NF)**",
    "users - accounts with hashed passwords (SHA-256 + salt)",
    "onboarding_responses - personalization questionnaire data",
    "bfrb_types - 8 seeded BFRB categories (extensible)",
    "sessions - detection sessions (start, end, stats)",
    "detections - individual events (confidence, ML score, fused score)",
    "calibrations - per-session adaptive thresholds",
    "user_feedback - yes/no feedback on each detection",
    "pilot_trials - structured ground-truth collection",
    "telemetry - per-frame IEEE-grade logging",
    "",
    "**Key Design Decisions**",
    "SQLite for zero-config deployment (no Docker needed)",
    "Foreign keys + WAL journaling for data integrity",
    "Auto-migration: new columns added transparently",
], "Explain 3NF: no transitive dependencies, proper foreign keys. "
   "Show that all tables have proper PKs, FKs, and indexes. "
   "Mention the MySQL schema is also provided for production deployment.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 6: BACKEND API
# ═══════════════════════════════════════════════════════════════════════════
add_two_col_slide("Backend: Flask API (20+ Endpoints)",
    [
        "--- Authentication ---",
        "POST /api/auth/register",
        "POST /api/auth/login",
        "POST /api/auth/logout",
        "GET  /api/auth/me",
        "",
        "--- Sessions ---",
        "POST /api/sessions (start)",
        "PUT  /api/sessions/<id>/end",
        "GET  /api/sessions (list)",
        "",
        "--- Detection & Feedback ---",
        "POST /api/detections",
        "POST /api/feedback",
    ],
    [
        "--- ML Inference ---",
        "POST /api/predict (HTTP)",
        "WS predict_frame (WebSocket)",
        "POST /api/calibrate",
        "",
        "--- Analytics ---",
        "GET /api/stats/overview",
        "GET /api/stats/daily",
        "GET /api/stats/trends",
        "GET /api/bouts/<sid>",
        "",
        "--- Research ---",
        "POST /api/pilot/start",
        "GET /api/export/session/<sid>",
    ],
    "Walk through the major API categories. Emphasize RESTful design, "
    "proper HTTP methods, error handling with JSON responses. "
    "Mention the WebSocket alternative for ML predictions.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 7: ML PIPELINE
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("ML Pipeline: Feature Engineering & Classification", [
    "**Training Data: Kaggle CMI 'Detect Behavior with Sensor Data'**",
    "80 participants wearing wrist sensors | 574,945 readings",
    "18 gesture types (8 BFRB-like + 10 normal controls)",
    "",
    "**16 Semantic Features (bridging sensors -> camera)**",
    "Accelerometer -> wrist velocity (mean, std, max)",
    "Gyroscope -> palm rotation dynamics",
    "Thermopile -> hand-face overlap fraction",
    "Time-of-Flight -> 5 anatomical distances (nose, mouth, cheek, forehead, chin)",
    "",
    "**Model: Random Forest (200 estimators)**",
    "5-fold cross-validation | Macro F1 evaluation",
    "MinMaxScaler normalization [0, 1]",
    "",
    "**Late Multimodal Fusion**",
    "fused_score = 0.6 x ML_score + 0.4 x rule_score",
], "Key insight: same BFRB behaviors produce similar patterns whether measured "
   "by wrist sensors or by camera. We train on sensor data but deploy on camera. "
   "Late fusion combines the ML probability with the rule-based detector score.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 8: DETECTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Detection Pipeline (9-Stage)", [
    "1. One Euro Filter - adaptive low-pass smoothing on all landmarks",
    "2. Multi-Zone Face Detection - 13 anatomical regions with centroids",
    "3. Hand Pose Classifier - pinch_grip / fist / pointing / open_hand / curled",
    "4. 4-State Rule Engine - IDLE -> PROXIMITY -> DWELL -> BFRB",
    "5. Multi-Signal BFRB Score - 11 weighted factors (proximity, dwell, curl...)",
    "6. ML Classifier - 16-feature Random Forest, 1.5s sliding window",
    "7. Late Fusion - combines ML + rule scores (0.6/0.4 split)",
    "8. Adaptive Threshold - per-session calibration (baseline vs touch distance)",
    "9. IEEE Telemetry - per-frame structured logging for reproducibility",
    "",
    "**False Positive Filters**",
    "Eating detection (mouth wide open + hand near mouth + open palm)",
    "Resting detection (static hand + open palm + no recent BFRB history)",
], "Walk through each stage. Emphasize the false positive filtering - "
   "eating and resting are NOT BFRBs even though the hand is near the face.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 9: FRONTEND UI
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Frontend: Professional Web Dashboard", [
    "**Clean White + Dark Blue Professional Theme**",
    "Responsive design (desktop + tablet)",
    "Real-time video feed with landmark overlays",
    "",
    "**Three Main Views**",
    "Dashboard: live detection feed + controls + BFRB selector + signals",
    "Session HUD: charts (daily detections, type distribution, timeline, accuracy)",
    "History: session table with stats per session",
    "",
    "**Interactive Elements**",
    "BFRB type multi-select (8 types, multi/single mode)",
    "Detection notifications with yes/no feedback buttons",
    "Calibration wizard (2-step: far baseline + touch measurement)",
    "Pilot study modal (structured ground-truth collection)",
    "CSV export for offline analysis",
    "",
    "**Authentication: sign up, sign in, onboarding questionnaire**",
], "Explain the UI design philosophy: professional, not AI-looking. "
   "White background with dark blue accents. All 3 views are tab-navigated. "
   "Mention the onboarding questionnaire that personalizes the experience.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 10: AUTH & ONBOARDING
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Authentication & User Onboarding", [
    "**Secure Authentication**",
    "Password hashing: SHA-256 with random 16-byte salt",
    "Flask session-based auth with login_required decorator",
    "Username or email login support",
    "",
    "**Onboarding Questionnaire (first login)**",
    "Which BFRBs do you experience? (multi-select)",
    "How often do these behaviors occur? (5 frequency levels)",
    "What triggers your BFRBs? (stress, boredom, anxiety, focus...)",
    "What is your primary goal? (awareness, reduce, track, research, clinical)",
    "Alert preferences (visual only, visual+sound, gentle, silent)",
    "",
    "**Personalization**",
    "Pre-selects the user's reported BFRB types in the detector",
    "Responses stored in onboarding_responses table for future use",
], "Show how the login flow works: new users see the onboarding questionnaire "
   "after their first sign-in. This data personalizes which BFRB types are "
   "monitored by default.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 11: ADVANCED FEATURES
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Advanced Features", [
    "**Adaptive Threshold Calibration (Tier 2)**",
    "2-step wizard: measure far-baseline and touch distance",
    "threshold = touch + 0.3 * (baseline - touch)",
    "Accounts for different face sizes and camera distances",
    "",
    "**Bout Detection (Tier 3)**",
    "Groups consecutive detections into clinical 'bouts'",
    "5-second gap threshold | per-type aggregation",
    "",
    "**Pilot Study Mode (Tier 3)**",
    "Structured ground-truth collection: participant, gesture, duration",
    "Computes precision, recall, F1 per trial",
    "",
    "**WebSocket Real-Time (Tier 3)**",
    "Flask-SocketIO: ML predictions over persistent socket",
    "250ms throttle on WS vs 400ms on HTTP fallback",
    "",
    "**PWA (Tier 4) - Offline-capable app shell**",
], "Explain each advanced feature briefly. Calibration is important for "
   "different users sitting at different distances from the camera.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 12: LIVE DEMO PLAN
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Live Demonstration", [
    "**Demo Flow (5-7 minutes)**",
    "",
    "1. Login Page - create a new account",
    "2. Onboarding - answer setup questionnaire",
    "3. Dashboard - show the clean white + dark blue interface",
    "4. Start Session - camera activates, MediaPipe loads",
    "5. Show Detection - bring hand near face, trigger BFRB detection",
    "6. Feedback - respond to detection notification (yes/no)",
    "7. Calibration - run 2-step adaptive threshold calibration",
    "8. Session HUD - switch to charts tab, show daily/type/timeline charts",
    "9. History - view past sessions in the table",
    "10. Export CSV - download session data",
    "11. Stop Session - end and show summary",
    "12. Sign Out",
], "This is the live demo script. Follow these steps in order. "
   "Make sure to show all the major features: auth, onboarding, detection, "
   "feedback, calibration, charts, history, and export.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 13: GITHUB REPOSITORY
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("GitHub Repository & Deployment", [
    "**Repository: github.com/Nishanth3424/bfrb-detection-eneb453**",
    "",
    "**Project Structure**",
    "bfrb_web_app/app.py         - Flask backend (1,300+ lines)",
    "bfrb_web_app/templates/     - index.html (3,300+ lines) + login.html",
    "bfrb_web_app/model/         - Trained ML model + feature metadata",
    "bfrb_web_app/static/        - PWA manifest + service worker + icons",
    "database/                   - MySQL schema, seed data, demo queries",
    "erd/                        - Interactive ERD visualization",
    "wireframe/                  - UI wireframe mockup",
    "",
    "**How to Run**",
    "pip install -r requirements.txt",
    "python app.py",
    "Open http://localhost:5000",
    "",
    "**Total: ~4,800 lines of code (Python + HTML/CSS/JS)**",
], "Show the GitHub page. Mention that the entire project is open source "
   "and can be cloned and run locally. No Docker required - SQLite is embedded.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 14: RESULTS & METRICS
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Results & Performance", [
    "**ML Model Performance**",
    "Random Forest: 77% accuracy (5-fold CV)",
    "Macro F1: handles class imbalance (64% BFRB / 36% non-BFRB)",
    "Training on 8,151 labeled sequences from 80 participants",
    "",
    "**Real-Time Performance**",
    "25-30 FPS with MediaPipe Holistic in browser",
    "ML inference: <10ms per prediction (server-side)",
    "WebSocket latency: ~5-15ms round-trip",
    "",
    "**Detection Capability**",
    "8 BFRB types supported (+ custom types)",
    "Multi-zone face detection (13 anatomical regions)",
    "False positive filtering (eating, resting)",
    "Adaptive calibration per user",
    "",
    "**Code Coverage: 20+ API endpoints, 9 database tables**",
], "Discuss the key metrics. 77% accuracy is reasonable for a sensor-to-camera "
   "domain transfer. Real-time performance is smooth at 25-30 FPS.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 15: CHALLENGES
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Challenges & Solutions", [
    "**Challenge 1: Sensor-to-Camera Domain Gap**",
    "Kaggle data = wrist sensors, our system = camera",
    "Solution: semantic feature mapping (16 features bridge both modalities)",
    "",
    "**Challenge 2: False Positives**",
    "Eating, resting, scratching look similar to BFRBs",
    "Solution: multi-signal scoring + eating/resting filters + dwell timers",
    "",
    "**Challenge 3: Varying User Distances**",
    "Proximity thresholds break at different camera distances",
    "Solution: adaptive calibration normalizes by face width",
    "",
    "**Challenge 4: Real-Time Performance**",
    "MediaPipe + ML inference must run at >20 FPS",
    "Solution: One Euro filter + sliding window + WebSocket transport",
    "",
    "**Challenge 5: User Experience**",
    "Technical ML system must be accessible to non-technical users",
    "Solution: onboarding questionnaire + clean professional UI",
], "Be honest about challenges. The domain gap is the hardest part - "
   "we're training on wrist sensors but deploying on camera.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 16: FUTURE WORK
# ═══════════════════════════════════════════════════════════════════════════
add_bullet_slide("Future Work", [
    "**Short-Term Improvements**",
    "Fine-tune ML model on camera-derived features (labeled webcam data)",
    "Add multi-user support with role-based access (patient vs therapist)",
    "Mobile-optimized layout for smartphone webcam use",
    "",
    "**Research Extensions**",
    "Federated learning: train across users without sharing raw data",
    "CORAL domain adaptation: align sensor and camera feature distributions",
    "Longitudinal studies: track behavior patterns over weeks/months",
    "",
    "**Clinical Integration**",
    "Therapist dashboard: view patient BFRB trends remotely",
    "Integration with CBT (Cognitive Behavioral Therapy) protocols",
    "Smart notifications: context-aware alerts based on time/location",
    "",
    "**Deployment**",
    "Cloud hosting (AWS/GCP) for multi-user access",
    "Browser extension version for always-on monitoring",
], "These are realistic next steps. The federated learning and CORAL work "
   "already exists as offline prototypes in the Tier 4 pipeline.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 17: REQUIREMENTS CHECKLIST
# ═══════════════════════════════════════════════════════════════════════════
add_two_col_slide("Project Requirements Checklist",
    [
        "--- Database ---",
        "[DONE] 3NF normalized schema",
        "[DONE] Proper foreign keys & indexes",
        "[DONE] 9 tables (users, sessions, etc.)",
        "[DONE] MySQL reference schema + Docker",
        "[DONE] ERD diagram",
        "",
        "--- Backend ---",
        "[DONE] Flask routes (20+ endpoints)",
        "[DONE] Session management",
        "[DONE] Error handling (JSON responses)",
        "[DONE] ML inference endpoint",
        "[DONE] WebSocket real-time",
    ],
    [
        "--- Frontend ---",
        "[DONE] Responsive HTML/CSS/JS",
        "[DONE] Real-time webcam detection",
        "[DONE] Charts & analytics dashboard",
        "[DONE] Authentication (login/signup)",
        "[DONE] Onboarding questionnaire",
        "",
        "--- Extras ---",
        "[DONE] BFRB type selector (custom)",
        "[DONE] Adaptive calibration",
        "[DONE] CSV export",
        "[DONE] PWA (offline capable)",
        "[DONE] GitHub repository",
    ],
    "Walk through each requirement and confirm it's met. "
    "This shows completeness of the project.")

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 18: THANK YOU & Q&A
# ═══════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, NAVY_DARK)
add_rect(slide, Inches(0), Inches(3.2), SLIDE_W, Inches(0.06), ACCENT_RED)
add_text_box(slide, Inches(1), Inches(2.0), Inches(11), Inches(1.0),
             "Thank You!", size=52, color=WHITE, bold=True,
             align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(3.6), Inches(11), Inches(0.6),
             "Questions & Discussion", size=28, color=GOLD,
             align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(4.5), Inches(11), Inches(0.5),
             "Nishanth S.  |  ENEB453  |  University of Maryland",
             size=18, color=TEXT_DIM, align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(5.2), Inches(11), Inches(0.5),
             "GitHub: github.com/Nishanth3424/bfrb-detection-eneb453",
             size=16, color=BLUE_LT, align=PP_ALIGN.CENTER)
slide.notes_slide.notes_text_frame.text = (
    "Thank the audience. Open for questions. Key talking points for Q&A: "
    "Why MediaPipe over other CV libraries? (Free, browser-native, real-time). "
    "Why Random Forest? (Tabular features, interpretable, fast inference). "
    "How accurate is it? (77% on Kaggle data, real-world depends on calibration). "
    "Privacy? (Video never leaves the device - all CV runs in browser)."
)

# ── Save ──
prs.save(OUT)
print(f"Presentation saved to: {OUT}")
print(f"Total slides: {len(prs.slides)}")
