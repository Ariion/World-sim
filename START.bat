@echo off
title Genesis Engine

echo.
echo  ==========================================
echo       GENESIS ENGINE - DEMARRAGE
echo  ==========================================
echo.

:: Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non trouve.
    echo Installe Python depuis python.org
    echo Coche "Add Python to PATH" pendant l'installation.
    pause
    exit /b 1
)
echo [OK] Python detecte

:: Creer environnement virtuel
if not exist "venv\" (
    echo [..] Creation environnement virtuel...
    python -m venv venv
    echo [OK] Environnement cree
)

:: Activer venv
call venv\Scripts\activate.bat

:: Installer dependances
echo [..] Installation des dependances...
pip install -q fastapi uvicorn websockets python-dotenv numpy
echo [OK] Dependances installees

:: Creer .env si absent
if not exist ".env" (
    echo WORLD_SEED=42> .env
    echo HOST=0.0.0.0>> .env
    echo PORT=8000>> .env
    echo [OK] Fichier .env cree
)

:: Lancer le serveur
echo.
echo [..] Demarrage du serveur...
start "Genesis Server" cmd /k "call venv\Scripts\activate.bat && uvicorn server.main:app --host 0.0.0.0 --port 8000"

:: Attendre
echo [..] Attente 10 secondes...
timeout /t 10 /nobreak >nul

:: Lancer ngrok si present
if exist "ngrok.exe" (
    echo [..] Lancement ngrok...
    start "Genesis Tunnel" cmd /k "ngrok http 8000"
    timeout /t 3 /nobreak >nul
) else (
    echo [INFO] ngrok.exe absent - serveur local uniquement
)

:: Ouvrir le dashboard
echo [..] Ouverture du dashboard...
start "" "client\index.html"

echo.
echo  ==========================================
echo   GENESIS ENGINE ACTIF
echo  ==========================================
echo   Local  : http://localhost:8000
echo   Docs   : http://localhost:8000/docs
echo   Monde  : http://localhost:8000/world/state
echo  ==========================================
echo.
echo  Ferme cette fenetre pour arreter.
pause
