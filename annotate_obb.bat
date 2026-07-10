@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo ====================================================
echo   OBB Annotation Tool - Thread Defect
echo ====================================================
echo.
echo   [1] train  (24 images)
echo   [2] val    (6 images)
echo.
set /p mode="Dataset (1/2): "
if "%mode%"=="1" set mode=train
if "%mode%"=="2" set mode=val

del /q annotate_obb_progress.json 2>nul
python annotate_obb.py --img dataset_obb/images/%mode% --label dataset_obb/labels/%mode%
pause
