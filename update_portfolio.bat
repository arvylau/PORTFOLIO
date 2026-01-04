@echo off
echo ============================================================
echo Portfolio Update - Quick Update Tool
echo ============================================================
echo.

REM Move new CSV from Downloads
echo Moving PORTFOLIO.csv from Downloads...
move /Y "C:\Users\lauar\Downloads\PORTFOLIO.csv" "C:\Users\lauar\Documents\GitHub\PORTFOLIO\PORTFOLIO.csv"
if errorlevel 1 (
    echo ERROR: Could not move file. Make sure it exists in Downloads.
    pause
    exit /b 1
)
echo [OK] File moved successfully
echo.

REM Regenerate portal
echo Regenerating portfolio portal...
"C:\Program Files\Python311\python.exe" "C:\Users\lauar\Documents\GitHub\PORTFOLIO\create_portfolio_portal_v2.py"
if errorlevel 1 (
    echo ERROR: Portal generation failed
    pause
    exit /b 1
)
echo.

REM Open the portal
echo Opening portfolio portal...
start "" "C:\Users\lauar\Documents\GitHub\PORTFOLIO\portfolio_portal.html"

echo.
echo ============================================================
echo Update complete!
echo ============================================================
pause
