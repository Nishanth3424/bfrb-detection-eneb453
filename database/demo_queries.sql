-- ============================================================
-- BFRB Detection System — Demo Queries
-- ENEB453 Final Project | Nishanth S. | University of Maryland
-- ============================================================

USE bfrb_detection;

-- ──────────────────────────────────────────────────────────────
-- QUERY 1: All detections with BFRB name, session type, and time
-- Shows the JOIN between detections, sessions, and bfrb_types
-- ──────────────────────────────────────────────────────────────
SELECT
    d.id                                    AS detection_id,
    bt.name                                 AS behavior,
    s.input_type                            AS session_type,
    CONCAT(FLOOR(d.timestamp_ms / 60000), 'm ',
           FLOOR((d.timestamp_ms % 60000) / 1000), 's')  AS time_into_session,
    ROUND(d.confidence_score * 100, 1)      AS confidence_pct,
    d.detected_at
FROM detections d
JOIN sessions  s  ON d.session_id    = s.id
JOIN bfrb_types bt ON d.bfrb_type_id = bt.id
ORDER BY d.detected_at;


-- ──────────────────────────────────────────────────────────────
-- QUERY 2: Detection count and average confidence per BFRB type
-- Useful for presenting which behaviors occur most frequently
-- ──────────────────────────────────────────────────────────────
SELECT
    bt.name                                 AS behavior,
    bt.is_custom                            AS custom_flag,
    COUNT(d.id)                             AS total_detections,
    ROUND(AVG(d.confidence_score) * 100, 1) AS avg_confidence_pct,
    ROUND(MAX(d.confidence_score) * 100, 1) AS max_confidence_pct
FROM bfrb_types bt
LEFT JOIN detections d ON bt.id = d.bfrb_type_id
GROUP BY bt.id, bt.name, bt.is_custom
ORDER BY total_detections DESC;


-- ──────────────────────────────────────────────────────────────
-- QUERY 3: Session summary — total detections per session
-- Demonstrates aggregation and LEFT JOIN
-- ──────────────────────────────────────────────────────────────
SELECT
    s.id                                    AS session_id,
    s.input_type,
    COALESCE(s.video_filename, 'webcam')    AS source,
    s.start_time,
    s.end_time,
    TIMESTAMPDIFF(MINUTE, s.start_time, s.end_time) AS duration_min,
    COUNT(d.id)                             AS total_detections
FROM sessions s
LEFT JOIN detections d ON s.id = d.session_id
GROUP BY s.id, s.input_type, s.video_filename, s.start_time, s.end_time
ORDER BY s.start_time;


-- ──────────────────────────────────────────────────────────────
-- QUERY 4: All custom BFRB types with their detection rules
-- Shows how user-defined behaviors are stored and retrieved
-- ──────────────────────────────────────────────────────────────
SELECT
    bt.name                                 AS custom_behavior,
    bt.description,
    blr.hand_landmark_index,
    blr.face_landmark_index,
    blr.distance_threshold_px,
    blr.rule_description
FROM bfrb_types bt
JOIN bfrb_landmark_rules blr ON bt.id = blr.bfrb_type_id
WHERE bt.is_custom = 1;


-- ──────────────────────────────────────────────────────────────
-- QUERY 5: High-confidence detections only (above 85%)
-- Simulates a filtered alert — only show events worth flagging
-- ──────────────────────────────────────────────────────────────
SELECT
    bt.name                                 AS behavior,
    s.input_type,
    ROUND(d.confidence_score * 100, 1)      AS confidence_pct,
    d.detected_at
FROM detections d
JOIN bfrb_types bt ON d.bfrb_type_id = bt.id
JOIN sessions   s  ON d.session_id   = s.id
WHERE d.confidence_score >= 0.85
ORDER BY d.confidence_score DESC;


-- ──────────────────────────────────────────────────────────────
-- QUERY 6: Detection rules for all built-in BFRB types
-- Shows the normalized landmark rule structure
-- ──────────────────────────────────────────────────────────────
SELECT
    bt.name                                 AS behavior,
    blr.hand_landmark_index                 AS hand_lm,
    blr.face_landmark_index                 AS face_lm,
    blr.distance_threshold_px               AS threshold_px,
    blr.rule_description
FROM bfrb_types bt
JOIN bfrb_landmark_rules blr ON bt.id = blr.bfrb_type_id
WHERE bt.is_custom = 0
ORDER BY bt.id, blr.id;
