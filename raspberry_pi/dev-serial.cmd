@echo off
REM Script de développement pour Windows avec poêle connecté
REM Lance l'application avec communication série réelle

echo 🔥 Démarrage du contrôleur Palazzetti avec communication série
echo =============================================================

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    pause
    exit /b 1
)

REM Vérifier que pip est installé
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip n'est pas installé
    pause
    exit /b 1
)

REM Installer les dépendances si nécessaire
echo 📦 Vérification des dépendances...
pip install -r requirements.txt --quiet

REM Tester la communication série
echo 🔌 Test de la communication série...
python test_communication.py --ports

echo.
echo 🚀 Lancement de l'application...
echo    - Mode: Communication série réelle
echo    - Port: %SERIAL_PORT% (38400, 8N2)
echo    - Interface: http://localhost:5000
echo    - Arrêt: Ctrl+C
echo.

REM Lancer l'application avec communication série
python palazzetti_controller.py

pause


