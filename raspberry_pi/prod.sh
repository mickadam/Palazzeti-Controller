#!/bin/bash

# Script de production pour Linux/macOS
# Lance l'application en mode production avec communication série réelle

echo "🏭 Démarrage du contrôleur Palazzetti en mode production"
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

# Lancer l'application en mode production
echo "🚀 Lancement de l'application..."
echo "   - Mode: Production (communication série réelle)"
echo "   - Interface: http://localhost:5000"
echo "   - Arrêt: Ctrl+C"
echo ""

# Définir DEBUG=False pour forcer le mode production
# LOG_LEVEL peut être: DEBUG, INFO, WARNING, ERROR
DEBUG=False LOG_LEVEL=DEBUG python palazzeti_controller.py
