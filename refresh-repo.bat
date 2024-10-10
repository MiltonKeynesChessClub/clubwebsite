@echo off
REM Navigate to the folder where the batch file is located
cd /d "%~dp0"
echo Refreshing repository...
git pull origin main
pause