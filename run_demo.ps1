# RAY — Autonomous Revenue Recovery & Verification Engine
# Phase 7 Production Demonstration Launcher (PowerShell)

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "   RAY — AUTONOMOUS REVENUE RECOVERY & VERIFICATION ENGINE" -ForegroundColor Cyan
Write-Host "   Razorpay AI Buildathon Demonstration Launcher" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan

# 1. Ensure Python dependencies
Write-Host "`n[1/5] Checking environment & initializing database..." -ForegroundColor Yellow
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"

# 2. Train & benchmark ML model
Write-Host "`n[2/5] Validating ML Recoverability Pipeline & Customer Isolation..." -ForegroundColor Yellow
python -m app.ml.train

# 3. Seed deterministic demo scenarios
Write-Host "`n[3/5] Seeding 5 Core Demonstration Scenarios..." -ForegroundColor Yellow
python backend/scripts/demo_recovery.py

# 4. Start Backend Server if not active
Write-Host "`n[4/5] Checking Backend Server on http://127.0.0.1:8000..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 2
    Write-Host "Backend server is running: $($response.app)" -ForegroundColor Green
} catch {
    Write-Host "Starting backend server in background..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory "$PSScriptRoot\backend"
    Start-Sleep -Seconds 3
}

# 5. Check Frontend Server on http://localhost:3000
Write-Host "`n[5/5] Checking Frontend Dashboard on http://localhost:3000..." -ForegroundColor Yellow
try {
    $frontResp = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 2
    Write-Host "Frontend dashboard is live!" -ForegroundColor Green
} catch {
    Write-Host "Starting frontend server in background..." -ForegroundColor Yellow
    Start-Process cmd -ArgumentList "/c npm run dev -- -p 3000" -WorkingDirectory "$PSScriptRoot\frontend"
    Start-Sleep -Seconds 3
}

Write-Host "`n===========================================================================" -ForegroundColor Green
Write-Host "   DEMONSTRATION READY!" -ForegroundColor Green
Write-Host "   - Frontend Control Center: http://localhost:3000" -ForegroundColor White
Write-Host "   - Case Detail (₹24,999):   http://localhost:3000/cases/PAY_DEMO_001" -ForegroundColor White
Write-Host "   - High-Value Gate (₹75k):  http://localhost:3000/cases/PAY_DEMO_HIGH_VALUE" -ForegroundColor White
Write-Host "   - Conflict Demo (Dual-Sig):http://localhost:3000/cases/PAY_DEMO_CONFLICT" -ForegroundColor White
Write-Host "   - Idempotency Demo:        http://localhost:3000/cases/PAY_DEMO_DUPLICATE" -ForegroundColor White
Write-Host "   - Prompt Injection Demo:   http://localhost:3000/cases/PAY_DEMO_INJECTION" -ForegroundColor White
Write-Host "   - API Provenance Endpoint: http://127.0.0.1:8000/api/v1/recovery/PAY_DEMO_001/provenance" -ForegroundColor White
Write-Host "   - System Health:           http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host "===========================================================================" -ForegroundColor Green
