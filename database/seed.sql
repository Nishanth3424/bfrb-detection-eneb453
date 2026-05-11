-- ============================================================
-- BFRB Detection System — Seed Data
-- ENEB453 Final Project | Nishanth S. | University of Maryland
-- Run AFTER schema.sql (MySQL only — SQLite auto-seeds via app.py)
-- ============================================================

USE bfrb_detection;

-- ─────────────────────────────────────────────
-- Seed: bfrb_types (8 built-in behaviors)
-- ─────────────────────────────────────────────
INSERT INTO bfrb_types (name, description, category, is_custom, created_at) VALUES
('Hair Pulling',
 'Repetitive pulling or tugging of hair from the scalp, eyebrows, or eyelashes (trichotillomania).',
 'pulling', 0, '2026-04-01 09:00:00'),

('Nail Biting',
 'Bringing fingertips to the mouth and biting the nails or surrounding skin (onychophagia).',
 'biting', 0, '2026-04-01 09:00:00'),

('Skin Picking',
 'Using fingertips to repeatedly pick, scratch, or squeeze skin (excoriation).',
 'picking', 0, '2026-04-01 09:00:00'),

('Nose Picking',
 'Inserting a finger into the nostril, detected by fingertip proximity to nose tip (rhinotillexomania).',
 'picking', 0, '2026-04-01 09:00:00'),

('Lip Picking',
 'Using thumb or fingertip to pick, pull, or bite the lips repeatedly.',
 'picking', 0, '2026-04-01 09:00:00'),

('Face Touching',
 'Sustained contact of hand with face without specific BFRB pattern.',
 'touching', 0, '2026-04-01 09:00:00'),

('Forehead Touching',
 'Prolonged hand contact with the forehead region.',
 'touching', 0, '2026-04-01 09:00:00'),

('Cheek Touching',
 'Prolonged hand contact with the cheek region.',
 'touching', 0, '2026-04-01 09:00:00');

-- ─────────────────────────────────────────────
-- Seed: bfrb_landmark_rules
-- ─────────────────────────────────────────────
INSERT INTO bfrb_landmark_rules
    (bfrb_type_id, hand_landmark_index, face_landmark_index, distance_threshold_px, rule_description)
VALUES
-- Hair Pulling: index/middle tip near forehead or scalp
(1, 8,  10,  40.0, 'Index fingertip within 40px of forehead landmark'),
(1, 12, 10,  40.0, 'Middle fingertip within 40px of forehead landmark'),

-- Nail Biting: fingertips near upper lip
(2, 8,  13,  35.0, 'Index fingertip within 35px of upper lip'),
(2, 12, 13,  35.0, 'Middle fingertip within 35px of upper lip'),
(2, 4,  13,  35.0, 'Thumb tip within 35px of upper lip'),

-- Skin Picking: index tip near cheek/forehead
(3, 8,  127, 30.0, 'Index fingertip within 30px of left cheek'),
(3, 8,  10,  30.0, 'Index fingertip within 30px of forehead'),

-- Nose Picking: index tip near nose tip
(4, 8,  1,   25.0, 'Index fingertip within 25px of nose tip'),

-- Lip Picking: thumb near upper/lower lip
(5, 4,  13,  30.0, 'Thumb tip within 30px of upper lip'),
(5, 4,  14,  30.0, 'Thumb tip within 30px of lower lip'),

-- Face Touching: wrist near nose
(6, 0,  1,   50.0, 'Wrist within 50px of nose tip'),

-- Forehead Touching: wrist near forehead
(7, 0,  10,  50.0, 'Wrist within 50px of forehead'),

-- Cheek Touching: index near cheek
(8, 8, 234,  35.0, 'Index fingertip within 35px of left cheek');

-- ─────────────────────────────────────────────
-- Seed: sample sessions
-- ─────────────────────────────────────────────
INSERT INTO sessions (input_type, selected_types, selection_mode, start_time, end_time, total_detections, total_confirmed, total_rejected, created_at) VALUES
('webcam', '["Hair Pulling","Nail Biting","Skin Picking","Nose Picking","Lip Picking","Face Touching"]', 'multi',
 '2026-04-08 10:05:00', '2026-04-08 10:22:00', 7, 5, 2, '2026-04-08 10:05:00'),
('webcam', '["Nail Biting"]', 'single',
 '2026-04-09 14:00:00', '2026-04-09 14:18:00', 5, 3, 1, '2026-04-09 14:00:00'),
('webcam', '["Hair Pulling","Skin Picking"]', 'multi',
 '2026-04-10 16:30:00', '2026-04-10 16:47:00', 5, 4, 0, '2026-04-10 16:30:00');

-- ─────────────────────────────────────────────
-- Seed: sample detections
-- ─────────────────────────────────────────────
INSERT INTO detections (session_id, bfrb_type, frame_number, timestamp_ms, confidence_score, smoothed_distance, bfrb_score, user_confirmed, detected_at) VALUES
-- Session 1
(1, 'Hair Pulling',   120,  4000,  0.8912, 0.25, 0.72, 1,    '2026-04-08 10:05:04'),
(1, 'Nail Biting',    345,  11500, 0.7234, 0.18, 0.65, 1,    '2026-04-08 10:05:12'),
(1, 'Hair Pulling',   678,  22600, 0.9145, 0.22, 0.78, 1,    '2026-04-08 10:05:23'),
(1, 'Skin Picking',   890,  29667, 0.6100, 0.30, 0.58, 0,    '2026-04-08 10:05:30'),
(1, 'Nose Picking',  1020,  34000, 0.8003, 0.15, 0.70, 1,    '2026-04-08 10:05:34'),
(1, 'Nail Biting',   1350,  45000, 0.7756, 0.20, 0.68, 0,    '2026-04-08 10:05:45'),
(1, 'Hair Pulling',  1800,  60000, 0.9302, 0.12, 0.82, 1,    '2026-04-08 10:06:00'),
-- Session 2
(2, 'Nail Biting',    200,  6667,  0.7421, 0.19, 0.63, 1,    '2026-04-09 14:00:07'),
(2, 'Nail Biting',    450,  15000, 0.8811, 0.14, 0.75, 1,    '2026-04-09 14:00:15'),
(2, 'Nail Biting',    700,  23333, 0.6543, 0.28, 0.57, 0,    '2026-04-09 14:00:23'),
(2, 'Nail Biting',    950,  31667, 0.7200, 0.22, 0.64, 1,    '2026-04-09 14:00:32'),
(2, 'Nail Biting',   1100,  36667, 0.8900, 0.13, 0.79, NULL, '2026-04-09 14:00:37'),
-- Session 3
(3, 'Hair Pulling',    90,  3000,  0.7100, 0.27, 0.61, 1,    '2026-04-10 16:30:03'),
(3, 'Hair Pulling',   310,  10333, 0.9400, 0.10, 0.85, 1,    '2026-04-10 16:30:10'),
(3, 'Skin Picking',   560,  18667, 0.8234, 0.20, 0.71, 1,    '2026-04-10 16:30:19'),
(3, 'Skin Picking',   820,  27333, 0.7655, 0.24, 0.66, 1,    '2026-04-10 16:30:27'),
(3, 'Hair Pulling',  1080,  36000, 0.9001, 0.11, 0.80, NULL, '2026-04-10 16:30:36');

-- ─────────────────────────────────────────────
-- Seed: sample user_feedback
-- ─────────────────────────────────────────────
INSERT INTO user_feedback (detection_id, session_id, is_accurate, bfrb_type, confidence_at, response_time_ms, created_at) VALUES
(1, 1, 1, 'Hair Pulling',  0.89, 2100, '2026-04-08 10:05:06'),
(2, 1, 1, 'Nail Biting',   0.72, 3400, '2026-04-08 10:05:15'),
(3, 1, 1, 'Hair Pulling',  0.91, 1800, '2026-04-08 10:05:25'),
(4, 1, 0, 'Skin Picking',  0.61, 4200, '2026-04-08 10:05:34'),
(5, 1, 1, 'Nose Picking',  0.80, 2600, '2026-04-08 10:05:37'),
(6, 1, 0, 'Nail Biting',   0.78, 5100, '2026-04-08 10:05:50'),
(7, 1, 1, 'Hair Pulling',  0.93, 1500, '2026-04-08 10:06:02'),
(8, 2, 1, 'Nail Biting',   0.74, 2200, '2026-04-09 14:00:09'),
(9, 2, 1, 'Nail Biting',   0.88, 1900, '2026-04-09 14:00:17'),
(10, 2, 0, 'Nail Biting',  0.65, 3800, '2026-04-09 14:00:27'),
(11, 2, 1, 'Nail Biting',  0.72, 2400, '2026-04-09 14:00:34'),
(13, 3, 1, 'Hair Pulling',  0.71, 2800, '2026-04-10 16:30:06'),
(14, 3, 1, 'Hair Pulling',  0.94, 1600, '2026-04-10 16:30:12'),
(15, 3, 1, 'Skin Picking',  0.82, 2100, '2026-04-10 16:30:21'),
(16, 3, 1, 'Skin Picking',  0.77, 3200, '2026-04-10 16:30:30');
