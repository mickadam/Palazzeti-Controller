#!/bin/bash

# Script de développement pour Linux/macOS
# Lance l'application en mode développement avec mock série

echo "🔥 Démarrage du contrôleur Palazzetti en mode développement"
echo "=========================================================="

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier que pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 n'est pas installé"
    exit 1
fi

# Installer les dépendances si nécessaire
echo "📦 Vérification des dépendances..."
pip3 install -r requirements.txt --quiet

# Lancer l'application en mode développement
echo "🚀 Lancement de l'application..."
echo "   - Mode: Développement (mock série)"
echo "   - Interface: http://localhost:5000"
echo "   - Arrêt: Ctrl+C"
echo ""

python3 palazzetti_controller.py --dev


