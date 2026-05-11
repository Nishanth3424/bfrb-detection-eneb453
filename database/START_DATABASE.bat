@echo off
echo ============================================
echo  BFRB Detection System - Start Database
echo  ENEB453 Final Project | Nishanth S.
echo ============================================
echo.

REM Make sure Docker Desktop is open before running this
echo [1/3] Starting MySQL container...
docker compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Docker failed. Make sure Docker Desktop is open and running.
    pause
    exit /b 1
)

echo.
echo [2/3] Waiting 20 seconds for MySQL to initialize...
timeout /t 20 /nobreak > nul

echo.
echo [3/3] Verifying database...
docker exec bfrb_mysql mysql -u bfrb_user -pbfrb_pass_2026 bfrb_detection -e "SELECT COUNT(*) AS total_bfrb_types FROM bfrb_types; SELECT COUNT(*) AS total_sessions FROM sessions; SELECT COUNT(*) AS total_detections FROM detections;"

echo.
echo ============================================
echo  Database is ready!
echo  Host:     localhost:3306
echo  Database: bfrb_detection
echo  User:     bfrb_user
echo  Password: bfrb_pass_2026
echo ============================================
pause
