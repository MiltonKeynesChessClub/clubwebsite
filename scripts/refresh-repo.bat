@echo off
REM Navigate to your repository folder (Change this to your repository path)
cd C:\Users\sumit\www.miltonkeyneschessclub.co.uk

REM Fetch the latest updates from the origin and pull changes
git fetch --all
git pull origin main

REM Wait for user to close the window
pause