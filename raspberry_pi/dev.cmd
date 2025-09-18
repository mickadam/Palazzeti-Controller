@echo off
REM Script de développement pour Windows
REM Lance l'application en mode développement avec mock série

echo 🔥 Démarrage du contrôleur Palazzetti en mode développement
echo ==========================================================

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

REM Lancer l'application en mode développement
echo 🚀 Lancement de l'application...
echo    - Mode: Développement (mock série)
echo    - Interface: http://localhost:5000
echo    - Arrêt: Ctrl+C
echo.

python palazzetti_controller.py --dev

pause


