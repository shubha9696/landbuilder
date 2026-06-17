@echo off
echo ==========================================================
echo               STARTING LANDBUILDER APP
echo ==========================================================
echo.

echo [1/2] Starting FastAPI Backend on http://localhost:8000...
start "LandBuilder Backend" cmd /k "cd backend && .venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting Vite Frontend on http://localhost:5173...
start "LandBuilder Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo LandBuilder services launched successfully!
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:5173
echo ==========================================================
pause
