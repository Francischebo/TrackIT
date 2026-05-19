@echo off
echo ===================================================
echo 🚀 TrackIT Frontend - Automated Vercel Deployer
echo ===================================================
echo.
echo This script will install the Vercel CLI and deploy
echo the fully-configured, optimized production frontend.
echo.
echo Please ensure your system has active internet access before continuing.
echo.
pause
echo.
echo [1/3] Navigating to the frontend workspace...
cd frontend
echo.
echo [2/3] Installing Vercel CLI globally...
call npm install -g vercel
if %errorlevel% neq 0 (
    echo.
    echo ❌ Failed to install Vercel CLI. Please verify your internet connection.
    pause
    exit /b %errorlevel%
)
echo.
echo [3/3] Initiating Vercel Production Deployment...
echo.
echo Note: If this is your first time, you will be prompted to log in to Vercel.
call vercel --prod
if %errorlevel% neq 0 (
    echo.
    echo ❌ Vercel deployment aborted or failed.
    pause
    exit /b %errorlevel%
)
echo.
echo 🎉 Vercel deployment completed successfully!
pause
