$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path 'backend\.venv\Scripts\python.exe')) { python -m venv backend\.venv }
if (-not (Test-Path 'backend\.venv\.sitepilot_deps_ok')) { & 'backend\.venv\Scripts\python.exe' -m pip install -r backend\requirements.txt; New-Item 'backend\.venv\.sitepilot_deps_ok' -ItemType File -Force | Out-Null }
if (-not (Test-Path 'frontend\node_modules')) { npm --prefix frontend install }
npm --prefix frontend run build
Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot\backend'; & '.\.venv\Scripts\python.exe' run.py"
Start-Sleep -Seconds 3
Start-Process 'http://localhost:8000/'
Write-Host 'SitePilot is running at http://localhost:8000/'
