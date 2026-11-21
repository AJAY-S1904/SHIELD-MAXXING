# IndicShield-JEV Launcher Script
$env:NODE_OPTIONS = "--max-old-space-size=4096"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🛡️  STARTING INDICSHIELD-JEV: FASTAPI BACKEND + AERO VISTA FRONTEND" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# Start FastAPI backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& 'C:\Users\ABHINAV B M\AppData\Local\Programs\Python\Python312\python.exe' 'D:\HACKATHON\api_server.py'"

Start-Sleep -Seconds 3

# Start Next.js frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:NODE_OPTIONS='--max-old-space-size=4096'; Set-Location 'D:\HACKATHON\frontend'; npm run start"

Start-Sleep -Seconds 2

# Open browser
Start-Process "http://localhost:3000"

Write-Host "`n✅ IndicShield-JEV is launching!" -ForegroundColor Green
Write-Host "🌐 Frontend UI: http://localhost:3000" -ForegroundColor Yellow
Write-Host "⚡ API Backend: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
