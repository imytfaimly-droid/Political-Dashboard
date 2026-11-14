@echo off
chcp 65001 >nul
echo ======================================================
echo    Uttarakhand & Himachal Political Dashboard Sync
echo ======================================================
echo Fetching latest Google Sheets data and rebuilding dashboard...
python "D:\Google-Dowanlod\Uttarakhand_Political_Monitor\sync_sheet_data.py"
python "D:\Google-Dowanlod\Uttarakhand_Political_Monitor\update_meta_data.py"
echo.
echo ======================================================
echo    Sync Complete! Dashboard is fully updated.
echo ======================================================
pause
