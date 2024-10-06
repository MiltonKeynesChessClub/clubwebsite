@echo off
REM Navigate to the folder where the batch file is located
cd /d "%~dp0"
echo Staging changes...
git add .
set /p comment="Enter commit message: "
git commit -m "%comment%"
git push origin main
pause
