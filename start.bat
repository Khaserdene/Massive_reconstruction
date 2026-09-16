@echo off
echo ------------------------------------------
echo 3DGS Data Collector - Server (HTTPS Enabled)
echo ------------------------------------------
echo Your local IP addresses (use HTTPS on your phone):
ipconfig | findstr "IPv4"
echo ------------------------------------------
echo Starting HTTPS server on port 8000...
echo.

cd /d "%~dp0server"
..\venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem

pause
