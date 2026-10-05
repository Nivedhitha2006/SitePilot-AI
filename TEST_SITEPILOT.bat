@echo off
setlocal
cd /d "%~dp0"
echo ==============================================
echo          SITEPILOT AI HEALTH TEST
echo ==============================================
echo.
where curl >nul 2>&1
if errorlevel 1 (
  echo curl is not available. Use a browser and open:
  echo http://localhost:8000/api/health
  pause
  exit /b 1
)

echo Checking http://localhost:8000/api/health ...
curl -s http://localhost:8000/api/health
echo.
echo.
echo If you see {"status":"ok"}, the backend is running.
echo Next, open http://localhost:8000/ and run a website audit.
echo.
pause
