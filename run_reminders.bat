@echo off
REM Runs the LibraryConnect reminder service once. Used by Windows Task Scheduler.
REM You can also run it by hand:  run_reminders.bat --dry-run
cd /d "%~dp0"
if not exist instance mkdir instance
echo ===== %date% %time% ===== >> instance\reminder_log.txt
call ..\.venv\Scripts\activate.bat
python send_reminders.py %* >> instance\reminder_log.txt 2>&1
exit /b %ERRORLEVEL%
