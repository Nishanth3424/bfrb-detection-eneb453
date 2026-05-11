# BFRB Detection System

**ENEB453 Final Project - University of Maryland**
**Author: Nishanth S.**

A real-time web-based Body-Focused Repetitive Behavior (BFRB) detection system using webcam-based computer vision and machine learning.

## Features

- **Real-time BFRB Detection** - Uses MediaPipe Holistic for face and hand landmark tracking
- **ML Classifier** - Random Forest model trained on Kaggle CMI sensor data (77% accuracy)
- **Late Multimodal Fusion** - Combines rule-based detection with ML classifier scores
- **User Authentication** - Secure sign-up/login with password hashing
- **Onboarding Questionnaire** - Personalized setup for each user
- **Session Management** - Start, stop, and review detection sessions
- **Adaptive Threshold Calibration** - Per-session calibration for different users/distances
- **Statistical Dashboard** - Charts and analytics (daily trends, per-type distribution, accuracy)
- **Bout Detection** - Groups consecutive detections into clinically meaningful bouts
- **WebSocket Real-Time Predictions** - Low-latency ML inference via Flask-SocketIO
- **Pilot Study Mode** - Structured ground-truth collection with precision/recall/F1 metrics
- **IEEE Telemetry Logging** - Per-frame structured logs with CSV export
- **Progressive Web App (PWA)** - Offline-capable app shell

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 2.3+ |
| Database | SQLite (embedded) |
| Real-Time | Flask-SocketIO 5.3+ |
| ML Inference | scikit-learn 1.3+, Random Forest |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Computer Vision | MediaPipe Holistic (CDN) |
| Charts | Chart.js 4.4+ |
| PWA | Web APIs (manifest + service worker) |

## Setup & Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/bfrb-detection-eneb453.git
cd bfrb-detection-eneb453/bfrb_web_app

# Install Python dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open in browser
# http://localhost:5000
```

## Database Schema (3NF)

- `users` - User accounts with hashed passwords
- `onboarding_responses` - User setup questionnaire data
- `bfrb_types` - BFRB catalog (8 seeded types + custom)
- `sessions` - Detection sessions
- `detections` - Individual BFRB events with confidence scores
- `calibrations` - Per-session adaptive thresholds
- `user_feedback` - Yes/no feedback on detections
- `pilot_trials` - Structured ground-truth trials
- `telemetry` - Per-frame structured logs

## Detection Pipeline

1. **One Euro Filter** - Adaptive low-pass smoothing on landmarks
2. **Multi-Zone Face Detection** - 13 anatomical face regions
3. **Hand Pose Classifier** - Pinch grip / fist / pointing / open hand / curled
4. **4-State Rule Engine** - IDLE -> PROXIMITY -> DWELL -> BFRB
5. **ML Classifier** - 16-feature Random Forest (trained on Kaggle CMI data)
6. **Late Fusion** - fused_score = 0.6 * ML + 0.4 * rule
7. **Adaptive Threshold** - Per-session calibration
8. **WebSocket Transport** - Real-time predictions over persistent socket

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Sign in |
| POST | `/api/auth/logout` | Sign out |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/onboarding` | Save onboarding |
| GET | `/api/bfrb-types` | List BFRB types |
| POST | `/api/sessions` | Start session |
| PUT | `/api/sessions/<id>/end` | End session |
| POST | `/api/detections` | Log detection |
| POST | `/api/feedback` | Submit feedback |
| POST | `/api/predict` | ML classifier |
| POST | `/api/calibrate` | Save calibration |
| GET | `/api/stats/overview` | Lifetime stats |
| GET | `/api/stats/daily` | Daily counts |
| GET | `/api/bouts/<sid>` | Bout aggregation |
| POST | `/api/pilot/start` | Start pilot trial |
| GET | `/api/export/session/<sid>` | CSV export |

## Project Structure

```
ENEB453/
  bfrb_web_app/
    app.py                 # Flask backend (1300+ lines)
    requirements.txt       # Python dependencies
    transform_and_train.py # ML model training
    model/
      bfrb_model.pkl       # Trained Random Forest
      scaler.pkl           # Feature scaler
      feature_meta.json    # Feature metadata
    templates/
      index.html           # Main web app UI (3300+ lines)
      login.html           # Authentication page
    static/
      manifest.json        # PWA manifest
      service-worker.js    # PWA service worker
      icon-192.png         # App icon
      icon-512.png         # App icon
  database/
    schema.sql             # MySQL schema (reference)
    seed.sql               # Sample data
    demo_queries.sql       # Demo SQL queries
  erd/
    erd_diagram.html       # Interactive ERD
  wireframe/
    wireframe.html         # UI mockup
```

## License

Academic project - University of Maryland ENEB453, Spring 2026.
