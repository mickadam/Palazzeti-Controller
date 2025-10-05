#!/bin/bash

# Script de lancement pour Linux/macOS
# Lance l'application avec communication série réelle

echo "🏭 Démarrage du contrôleur Palazzetti"
echo "========================================================"

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances si nécessaire
echo "📦 Vérification des dépendances..."
pip install -r requirements.txt --quiet

# Lancer l'application
echo "🚀 Lancement de l'application..."
echo "   - Mode: Communication série réelle"
echo "   - Interface: http://localhost:5000"
echo "   - Arrêt: Ctrl+C"
echo ""

# Configuration de l'environnement
# LOG_LEVEL peut être: DEBUG, INFO, WARNING, ERROR
DEBUG=False LOG_LEVEL=INFO python app.py
