@echo off
REM Navigate to your repository folder (Change this to your repository path)
cd C:\Users\sumit\www.miltonkeyneschessclub.co.uk

REM Add all the changes
git add .

REM Prompt for commit message
set /p msg="Enter commit message: "

REM Commit the changes
git commit -m "%msg%"

REM Push the changes to the origin main branch
git push origin main

REM Wait for user to close the window
pause



