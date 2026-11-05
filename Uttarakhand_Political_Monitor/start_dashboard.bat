@echo off
title Uttarakhand Live Political Radar Server
echo ========================================================
echo   Uttarakhand & Hill States Live Political Radar
echo   Starting local server at http://localhost:8080/dashboard.html
echo ========================================================
start "" "http://localhost:8080/dashboard.html"
python -m http.server 8080
pause
