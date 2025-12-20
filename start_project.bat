@echo off
echo ============================================
echo   Starting Performance Optimizer System
echo ============================================

echo [1/3] Starting Backend Server...
start "Performance Optimizer Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload"

echo [2/3] Starting Frontend Server...
start "Performance Optimizer Frontend" cmd /k "cd frontend && npm run dev"

echo [3/3] Opening Application in Browser...
echo Waiting 5 seconds for services to spin up...
timeout /t 5 /nobreak >nul
start http://127.0.0.1:3000

echo ============================================
echo   System Started!
echo   Backend: http://127.0.0.1:8000
echo   Frontend: http://127.0.0.1:3000
echo ============================================
