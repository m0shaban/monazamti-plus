:: filepath: e:\apps\new\New folder (4)\project_management\setup.bat
@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not added to PATH.
    pause
    exit /b 1
)

:: Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not installed or not added to PATH.
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

:: Check if .env file exists, copy .env.example if missing
if not exist ".env" (
    if exist ".env.example" (
        echo Copying .env.example to .env...
        copy .env.example .env >nul
        if %errorlevel% neq 0 (
            echo ERROR: Failed to copy .env.example to .env.
            pause
            exit /b 1
        )
    ) else (
        echo WARNING: .env.example not found. Please create a .env file manually.
    )
)

:: Apply database migrations
echo Applying database migrations...
flask db upgrade
if %errorlevel% neq 0 (
    echo ERROR: Failed to apply database migrations.
    pause
    exit /b 1
)

:: Run the application
echo Starting the Flask application...
python run.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to start the Flask application.
    pause
    exit /b 1
)

:: Keep the command window open for debugging
echo Application stopped. Press any key to exit.
pause