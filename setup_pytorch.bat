@echo off
echo ========================================================
echo Installing PyTorch with CUDA support into Virtual Environment
echo ========================================================
echo.
echo Make sure you have installed NVIDIA CUDA Toolkit globally on your PC!
echo This script will only install the Python libraries into the local venv.
echo.

if not exist "venv" (
    echo Venv not found. Please run setup.bat first.
    pause
    exit /b
)

echo Activating venv and installing torch, torchvision, torchaudio...
echo This might take a while (~3GB download).
echo.

call venv\Scripts\activate.bat
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install tqdm scipy plyfile

echo.
echo ========================================================
echo Installation Complete!
echo You must also install Visual Studio C++ Build Tools globally
echo if you want to compile the diff-gaussian-rasterization package.
echo ========================================================
pause
