@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SitePilot AI - One Click Launcher
color 0F

echo ==============================================
echo       SITEPILOT AI - ONE CLICK LAUNCHER
echo ==============================================
echo.
echo Project folder: %CD%
echo.

where python >nul 2>&1
if errorlevel 1 goto no_python
where npm >nul 2>&1
if errorlevel 1 goto no_npm

if not exist "backend\.venv\Scripts\python.exe" (
  echo [1/5] Creating Python virtual environment...
  python -m venv "backend\.venv"
  if errorlevel 1 goto fail
) else echo [1/5] Python environment found.

if not exist "backend\.venv\.sitepilot_deps_ok" (
  echo [2/5] Installing backend dependencies...
  "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
  if errorlevel 1 goto fail
  "backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
  if errorlevel 1 goto fail
  type nul > "backend\.venv\.sitepilot_deps_ok"
) else echo [2/5] Backend dependencies found.

echo [3/5] Checking frontend packages...
pushd "frontend"
if not exist "node_modules\.bin\vite.cmd" (
  echo Installing frontend packages. Please wait...
  call npm install --no-audit --no-fund
  if errorlevel 1 (
    popd
    goto fail
  )
)
echo Building frontend...
call npm run build
if errorlevel 1 (
  popd
  goto fail
)
popd

if not exist "frontend\dist\index.html" goto no_dist

echo [4/5] Starting backend in a visible window...
start "SitePilot AI Backend" cmd /k "cd /d "%~dp0backend" && echo SitePilot AI Backend && echo. && .venv\Scripts\python.exe run.py"

echo Waiting for backend...
set "READY="
for /l %%I in (1,1,20) do (
  powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 1 http://127.0.0.1:8000/api/health; if($r.StatusCode -eq 200){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>&1
  if not errorlevel 1 set "READY=1"
  if defined READY goto ready
  timeout /t 1 /nobreak >nul
)

echo WARNING: Backend did not respond within 20 seconds.
echo Check the backend window for the exact error.
goto keep

:ready
echo [5/5] SitePilot AI is ready.
start "" "http://localhost:8000/"
echo.
echo ==============================================
echo              SITEPILOT AI READY
echo ==============================================
echo App:    http://localhost:8000/
echo Health: http://localhost:8000/api/health
echo.
echo IMPORTANT: Keep the Backend window open.
echo This launcher window will stay open so errors are visible.
echo.
goto keep

:no_python
echo ERROR: Python is not installed or not on PATH.
goto fail
:no_npm
echo ERROR: Node.js/npm is not installed or not on PATH.
goto fail
:no_dist
echo ERROR: frontend\dist\index.html was not created.
goto fail
:fail
echo.
echo ==============================================
echo STARTUP FAILED - READ THE ERROR ABOVE
echo ==============================================
echo.
:keep
pause
exit /b 0
