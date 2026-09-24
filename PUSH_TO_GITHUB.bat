@echo off
title Push Tamil Ilakkiya AI to GitHub
echo ========================================================
echo   Tamil Ilakkiya AI - GitHub Push Assistant
echo ========================================================
echo.

cd /d "%~dp0"

:: Add Git and GitHub CLI to current session PATH
set "PATH=C:\Users\rdeep\.gemini\antigravity\tools\gh\bin;C:\Users\rdeep\.gemini\antigravity\tools\git\cmd;%PATH%"

echo [1/3] Verifying Git repository status...
git status -s
if %ERRORLEVEL% neq 0 (
    echo Git repository is not initialized. Initializing now...
    git init -b main
    git add .
    git commit -m "feat: complete Tamil Ilakkiya AI application"
)

echo.
echo [2/3] Choose how you want to push to GitHub:
echo   1. Automatically create and push a NEW GitHub repository (using GitHub CLI)
echo   2. Push to an EXISTING GitHub repository URL
echo.
set /p CHOICE="Enter your choice (1 or 2): "

if "%CHOICE%"=="1" (
    echo.
    echo [*] Checking GitHub authentication...
    gh auth status >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [*] Please complete one-time GitHub browser login...
        gh auth login --web -h github.com
    )
    echo [*] Creating new repository 'tamil-ilakkiya-ai' on GitHub and pushing...
    gh repo create tamil-ilakkiya-ai --public --source=. --remote=origin --push
    if %ERRORLEVEL% equ 0 (
        echo.
        echo [SUCCESS] Your project is now live on GitHub!
        gh repo view --web
    ) else (
        echo.
        echo If the repository already exists, try pushing with option 2.
    )
) else (
    echo.
    set /p REPO_URL="Enter your GitHub repository URL (e.g. https://github.com/your-username/repo.git): "
    if not "%REPO_URL%"=="" (
        git remote remove origin >nul 2>&1
        git remote add origin "%REPO_URL%"
        git branch -M main
        echo [*] Pushing to %REPO_URL%...
        git push -u origin main
        if %ERRORLEVEL% equ 0 (
            echo.
            echo [SUCCESS] Pushed successfully to %REPO_URL%!
        )
    ) else (
        echo [ERROR] No repository URL entered.
    )
)

echo.
echo ========================================================
pause
