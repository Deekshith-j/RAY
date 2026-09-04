#!/usr/bin/env bash
# RAY — Autonomous Revenue Recovery & Verification Engine
# Phase 7 Production Demonstration Launcher (Bash)

set -e

echo "==========================================================================="
echo "   RAY — AUTONOMOUS REVENUE RECOVERY & VERIFICATION ENGINE"
echo "   Razorpay AI Buildathon Demonstration Launcher"
echo "==========================================================================="

echo -e "\n[1/5] Checking environment & initializing database..."
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"

echo -e "\n[2/5] Validating ML Recoverability Pipeline & Customer Isolation..."
python -m app.ml.train

echo -e "\n[3/5] Seeding 5 Core Demonstration Scenarios..."
python backend/scripts/demo_recovery.py

echo -e "\n[4/5] Checking Backend Server on http://127.0.0.1:8000..."
if curl -s -f http://127.0.0.1:8000/health > /dev/null; then
    echo "Backend server is running."
else
    echo "Starting backend server..."
    cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
    cd ..
    sleep 3
fi

echo -e "\n[5/5] Checking Frontend Dashboard on http://localhost:3000..."
if curl -s -f http://localhost:3000 > /dev/null; then
    echo "Frontend dashboard is live."
else
    echo "Starting frontend dashboard..."
    cd frontend && npm run dev -- -p 3000 &
    cd ..
    sleep 3
fi

echo "==========================================================================="
echo "   DEMONSTRATION READY!"
echo "   - Frontend Control Center: http://localhost:3000"
echo "   - Case Detail (₹24,999):   http://localhost:3000/cases/PAY_DEMO_001"
echo "   - High-Value Gate (₹75k):  http://localhost:3000/cases/PAY_DEMO_HIGH_VALUE"
echo "   - Conflict Demo (Dual-Sig):http://localhost:3000/cases/PAY_DEMO_CONFLICT"
echo "   - Idempotency Demo:        http://localhost:3000/cases/PAY_DEMO_DUPLICATE"
echo "   - Prompt Injection Demo:   http://localhost:3000/cases/PAY_DEMO_INJECTION"
echo "   - API Provenance Endpoint: http://127.0.0.1:8000/api/v1/recovery/PAY_DEMO_001/provenance"
echo "   - System Health:           http://127.0.0.1:8000/health"
echo "==========================================================================="
