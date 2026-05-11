@echo off
echo ============================================
echo  BFRB Detection System - Demo Queries
echo  ENEB453 Final Project | Nishanth S.
echo ============================================
echo.

echo === QUERY 1: All detections with behavior name and session type ===
docker exec bfrb_mysql mysql -u bfrb_user -pbfrb_pass_2026 bfrb_detection -e "SELECT d.id AS detection_id, bt.name AS behavior, s.input_type AS session_type, CONCAT(FLOOR(d.timestamp_ms/60000),'m ',FLOOR((d.timestamp_ms%%60000)/1000),'s') AS time_into_session, ROUND(d.confidence_score*100,1) AS confidence_pct FROM detections d JOIN sessions s ON d.session_id=s.id JOIN bfrb_types bt ON d.bfrb_type_id=bt.id ORDER BY d.detected_at;"
echo.

echo === QUERY 2: Detection count per BFRB type ===
docker exec bfrb_mysql mysql -u bfrb_user -pbfrb_pass_2026 bfrb_detection -e "SELECT bt.name AS behavior, bt.is_custom AS custom_flag, COUNT(d.id) AS total_detections, ROUND(AVG(d.confidence_score)*100,1) AS avg_confidence_pct FROM bfrb_types bt LEFT JOIN detections d ON bt.id=d.bfrb_type_id GROUP BY bt.id,bt.name,bt.is_custom ORDER BY total_detections DESC;"
echo.

echo === QUERY 3: Session summary ===
docker exec bfrb_mysql mysql -u bfrb_user -pbfrb_pass_2026 bfrb_detection -e "SELECT s.id AS session_id, s.input_type, COALESCE(s.video_filename,'webcam') AS source, s.start_time, s.end_time, TIMESTAMPDIFF(MINUTE,s.start_time,s.end_time) AS duration_min, COUNT(d.id) AS total_detections FROM sessions s LEFT JOIN detections d ON s.id=d.session_id GROUP BY s.id ORDER BY s.start_time;"
echo.

echo === QUERY 4: Custom BFRB types with landmark rules ===
docker exec bfrb_mysql mysql -u bfrb_user -pbfrb_pass_2026 bfrb_detection -e "SELECT bt.name AS custom_behavior, blr.hand_landmark_index, blr.face_landmark_index, blr.distance_threshold_px, blr.rule_description FROM bfrb_types bt JOIN bfrb_landmark_rules blr ON bt.id=blr.bfrb_type_id WHERE bt.is_custom=1;"
echo.

echo === QUERY 5: High-confidence detections (above 85%%) ===
docker exec bfrb_mysql mysql -u bfrb_user -pbfrb_pass_2026 bfrb_detection -e "SELECT bt.name AS behavior, s.input_type, ROUND(d.confidence_score*100,1) AS confidence_pct, d.detected_at FROM detections d JOIN bfrb_types bt ON d.bfrb_type_id=bt.id JOIN sessions s ON d.session_id=s.id WHERE d.confidence_score>=0.85 ORDER BY d.confidence_score DESC;"
echo.

pause
