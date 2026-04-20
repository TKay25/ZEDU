@echo off
REM Delete legacy template backups
del /Q "templates\index.html" 2>nul
del /Q "templates\forums.html" 2>nul
del /Q "templates\tutor_dashboard.html" 2>nul
del /Q "templates\student_dashboard.html" 2>nul
del /Q "templates\parent_dashboard.html" 2>nul
echo Legacy templates deleted successfully!
pause
