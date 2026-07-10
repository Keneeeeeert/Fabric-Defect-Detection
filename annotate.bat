@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo ====================================================
echo   Fabric Defect Annotation Tool
echo ====================================================
echo.
echo   [1] hole
echo   [2] dirt
echo   [3] thread
echo.
set /p cls="Choose class (1/2/3): "
if "%cls%"=="1" set cls=hole
if "%cls%"=="2" set cls=dirt
if "%cls%"=="3" set cls=thread

echo.
echo   [1] train (training set)
echo   [2] val   (validation set)
set /p mode="Dataset (1/2): "
if "%mode%"=="1" set mode=train
if "%mode%"=="2" set mode=val

del /q annotate_progress.json 2>nul
python annotate.py --cls %cls% --img dataset/images/%mode% --label dataset/labels/%mode%
pause
