-- ============================================================
-- BFRB Detection System — Database Schema
-- ENEB453 Final Project | Nishanth S. | University of Maryland
-- Normalized to 3rd Normal Form (3NF)
-- Supports both SQLite (app.py embedded) and MySQL (Docker)
-- ============================================================

-- NOTE: The Flask app uses SQLite (bfrb_detection.db) with auto-init.
-- This schema is provided for MySQL/Docker reference and documentation.

CREATE DATABASE IF NOT EXISTS bfrb_detection;
USE bfrb_detection;

-- ─────────────────────────────────────────────
-- TABLE 1: bfrb_types
-- Catalog of all BFRB behavior types.
-- ─────────────────────────────────────────────
CREATE TABLE bfrb_types (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL UNIQUE,
    description TEXT,
    category    VARCHAR(50)     DEFAULT 'general',
    is_custom   TINYINT(1)      NOT NULL DEFAULT 0,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- TABLE 2: bfrb_landmark_rules
-- MediaPipe landmark detection rules per BFRB type.
-- FK → bfrb_types.id
-- ─────────────────────────────────────────────
CREATE TABLE bfrb_landmark_rules (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    bfrb_type_id            INT         NOT NULL,
    hand_landmark_index     INT         NOT NULL,
    face_landmark_index     INT         NOT NULL,
    distance_threshold_px   FLOAT       NOT NULL,
    rule_description        VARCHAR(255),

    CONSTRAINT fk_rules_bfrb_type
        FOREIGN KEY (bfrb_type_id) REFERENCES bfrb_types(id)
        ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- TABLE 3: sessions
-- One row per detection session.
-- Tracks selected BFRB types and selection mode.
-- ─────────────────────────────────────────────
CREATE TABLE sessions (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    input_type       ENUM('webcam', 'video') NOT NULL DEFAULT 'webcam',
    selected_types   JSON,
    selection_mode   VARCHAR(10) DEFAULT 'multi',
    start_time       DATETIME    NOT NULL,
    end_time         DATETIME,
    total_detections INT         DEFAULT 0,
    total_confirmed  INT         DEFAULT 0,
    total_rejected   INT         DEFAULT 0,
    notes            TEXT,
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- TABLE 4: detections
-- One row per detected BFRB event within a session.
-- Stores raw engine signals for analysis.
-- FK → sessions.id
-- ─────────────────────────────────────────────
CREATE TABLE detections (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    session_id        INT             NOT NULL,
    bfrb_type         VARCHAR(100)    NOT NULL,
    frame_number      INT,
    timestamp_ms      INT             NOT NULL,
    confidence_score  DECIMAL(5,4)    NOT NULL,
    smoothed_distance DECIMAL(6,4),
    bfrb_score        DECIMAL(5,4),
    user_confirmed    TINYINT(1),
    feedback_time     DATETIME,
    detected_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_detections_session
        FOREIGN KEY (session_id) REFERENCES sessions(id)
        ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- TABLE 5: user_feedback
-- Stores user yes/no feedback on detections.
-- Used to calculate model accuracy and improve detection.
-- FK → detections.id, sessions.id
-- ─────────────────────────────────────────────
CREATE TABLE user_feedback (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    detection_id     INT          NOT NULL,
    session_id       INT          NOT NULL,
    is_accurate      TINYINT(1)   NOT NULL,
    bfrb_type        VARCHAR(100) NOT NULL,
    confidence_at    DECIMAL(5,4),
    response_time_ms INT,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_feedback_detection
        FOREIGN KEY (detection_id) REFERENCES detections(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_feedback_session
        FOREIGN KEY (session_id) REFERENCES sessions(id)
        ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- INDEXES for query performance
-- ─────────────────────────────────────────────
CREATE INDEX idx_detections_session ON detections(session_id);
CREATE INDEX idx_detections_type ON detections(bfrb_type);
CREATE INDEX idx_detections_time ON detections(detected_at);
CREATE INDEX idx_feedback_detection ON user_feedback(detection_id);
CREATE INDEX idx_feedback_session ON user_feedback(session_id);
