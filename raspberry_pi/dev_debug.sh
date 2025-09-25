#!/bin/bash

# Script de développement avec debug activé
# Lance l'application en mode développement avec logs détaillés

echo "🔧 Démarrage du contrôleur Palazzetti en mode développement avec DEBUG"
echo "=================================================================="

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

# Lancer l'application en mode développement avec debug
echo "🚀 Lancement de l'application..."
echo "   - Mode: Développement (mock) avec logs DEBUG"
echo "   - Interface: http://localhost:5000"
echo "   - Arrêt: Ctrl+C"
echo ""

# Définir DEBUG=True et LOG_LEVEL=DEBUG
DEBUG=True LOG_LEVEL=DEBUG python palazzeti_controller.py
