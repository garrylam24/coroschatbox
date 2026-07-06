@echo off
echo Starting COROS Chatbox...
echo.

echo Step 1: Installing backend dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install backend dependencies.
    pause
    exit /b 1
)

echo.
echo Step 2: Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install
if %errorlevel% neq 0 (
    echo Failed to install frontend dependencies.
    pause
    exit /b 1
)

echo.
echo Step 3: Starting backend on http://localhost:8000...
cd /d "%~dp0backend"
start "COROS Backend" cmd /c "python main.py"

echo Step 4: Starting frontend on http://localhost:5173...
cd /d "%~dp0frontend"
start "COROS Frontend" cmd /c "npm run dev"

echo.
echo ============================================
echo  Both servers are starting up!
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000
echo ============================================
echo.
echo Close this window to stop all servers.
pause
