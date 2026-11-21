@echo off
echo ======================================================================
echo 🛡️  STARTING INDICSHIELD-JEV: FASTAPI BACKEND + AERO VISTA FRONTEND
echo ======================================================================

set "NODE_OPTIONS=--max-old-space-size=4096"

start "IndicShield-JEV API Backend (Port 8000)" cmd /k "C:\Users\ABHINAV B M\AppData\Local\Programs\Python\Python312\python.exe D:\HACKATHON\api_server.py"

timeout /t 3 /nobreak >nul

start "IndicShield-JEV Next.js Frontend (Port 3000)" cmd /k "cd /d D:\HACKATHON\frontend && set NODE_OPTIONS=--max-old-space-size=4096 && npm run start"

timeout /t 2 /nobreak >nul

start http://localhost:3000

echo.
echo ✅ IndicShield-JEV is launching!
echo 🌐 Frontend UI: http://localhost:3000
echo ⚡ API Backend: http://127.0.0.1:8000
echo ======================================================================
