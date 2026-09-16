@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

echo ===================================================
echo   Massive Reconstruction - Environment Setup
echo ===================================================

cd /d "%~dp0"
if not exist "tools" mkdir tools
cd tools

echo.
echo [1/3] Downloading COLMAP...
if not exist "COLMAP\COLMAP.bat" (
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/colmap/colmap/releases/download/3.9.1/COLMAP-3.9.1-windows-cuda.zip' -OutFile 'colmap.zip'"
    echo Extracting COLMAP...
    powershell -Command "Expand-Archive -Path 'colmap.zip' -DestinationPath 'COLMAP' -Force"
    del colmap.zip
    echo COLMAP setup complete.
) else (
    echo COLMAP already exists. Skipping.
)

echo.
echo [2/3] Cloning Gaussian Splatting...
if not exist "gaussian-splatting" (
    git clone https://github.com/graphdeco-inria/gaussian-splatting --recursive
) else (
    echo gaussian-splatting already exists. Skipping.
)

echo.
echo [3/3] Copying custom scripts...
if exist "..\gs_scripts\convert.py" (
    copy /Y "..\gs_scripts\convert.py" "gaussian-splatting\convert.py" >nul
    copy /Y "..\gs_scripts\train.py" "gaussian-splatting\train.py" >nul
    echo Scripts copied successfully.
) else (
    echo ERROR: Could not find gs_scripts folder.
)

echo.
echo ===================================================
echo Setup Complete! 
echo You can now run start.bat
echo ===================================================
pause
