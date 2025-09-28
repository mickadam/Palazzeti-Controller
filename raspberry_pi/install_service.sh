#!/bin/bash

# Script d'installation du service Palazzeti Controller
# Usage: sudo ./install_service.sh

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier que le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root (utilisez sudo)"
    exit 1
fi

log_info "🏭 Installation du service Palazzeti Controller"
echo "=================================================="

# Variables
SERVICE_NAME="palazzeti-controller"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="/home/pi/Palazzeti-Controller"
SERVICE_DIR="${PROJECT_DIR}/raspberry_pi"
VENV_DIR="${SERVICE_DIR}/venv"
LOG_DIR="/var/log/palazzeti-controller"

# Vérifier que le répertoire du projet existe
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Le répertoire du projet n'existe pas: $PROJECT_DIR"
    log_info "Assurez-vous que le projet est cloné dans le bon répertoire"
    exit 1
fi

# Vérifier que le répertoire raspberry_pi existe
if [ ! -d "$SERVICE_DIR" ]; then
    log_error "Le répertoire raspberry_pi n'existe pas: $SERVICE_DIR"
    exit 1
fi

log_info "📁 Répertoire du projet: $PROJECT_DIR"
log_info "📁 Répertoire du service: $SERVICE_DIR"

# Arrêter le service s'il est déjà en cours d'exécution
if systemctl is-active --quiet $SERVICE_NAME; then
    log_info "Arrêt du service existant..."
    systemctl stop $SERVICE_NAME
fi

# Désactiver le service s'il existe
if systemctl is-enabled --quiet $SERVICE_NAME; then
    log_info "Désactivation du service existant..."
    systemctl disable $SERVICE_NAME
fi

# Créer le répertoire de logs
log_info "📁 Création du répertoire de logs: $LOG_DIR"
mkdir -p $LOG_DIR
chown pi:pi $LOG_DIR
chmod 755 $LOG_DIR

# Installer la configuration de rotation des logs
log_info "📄 Installation de la configuration de rotation des logs..."
if [ -f "palazzeti-controller.logrotate" ]; then
    cp palazzeti-controller.logrotate /etc/logrotate.d/palazzeti-controller
    chmod 644 /etc/logrotate.d/palazzeti-controller
    log_success "Configuration de rotation des logs installée"
else
    log_warning "Fichier de configuration de rotation des logs non trouvé"
fi

# Vérifier et créer l'environnement virtuel si nécessaire
if [ ! -d "$VENV_DIR" ]; then
    log_info "📦 Création de l'environnement virtuel Python..."
    cd $SERVICE_DIR
    sudo -u pi python3 -m venv venv
    log_success "Environnement virtuel créé"
fi

# Activer l'environnement virtuel et installer les dépendances
log_info "📦 Installation des dépendances Python..."
cd $SERVICE_DIR
sudo -u pi $VENV_DIR/bin/pip install --upgrade pip
sudo -u pi $VENV_DIR/bin/pip install -r requirements.txt
log_success "Dépendances installées"

# Copier le fichier de service
log_info "📄 Installation du fichier de service systemd..."
cp palazzeti-controller.service $SERVICE_FILE

# Adapter le chemin dans le fichier de service si nécessaire
if [ "$PROJECT_DIR" != "/home/pi/Palazzeti-Controller" ]; then
    log_info "🔧 Adaptation des chemins dans le fichier de service..."
    sed -i "s|/home/pi/Palazzeti-Controller|$PROJECT_DIR|g" $SERVICE_FILE
fi

# Recharger systemd
log_info "🔄 Rechargement de la configuration systemd..."
systemctl daemon-reload

# Activer le service
log_info "✅ Activation du service..."
systemctl enable $SERVICE_NAME

# Démarrer le service
log_info "🚀 Démarrage du service..."
systemctl start $SERVICE_NAME

# Attendre un peu pour que le service démarre
sleep 3

# Vérifier le statut du service
if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "Service installé et démarré avec succès!"
    echo ""
    log_info "📊 Statut du service:"
    systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    log_info "📋 Commandes utiles:"
    echo "  • Voir les logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  • Redémarrer: sudo systemctl restart $SERVICE_NAME"
    echo "  • Arrêter: sudo systemctl stop $SERVICE_NAME"
    echo "  • Statut: sudo systemctl status $SERVICE_NAME"
    echo ""
    log_info "🌐 Interface web: http://$(hostname -I | awk '{print $1}'):5000"
else
    log_error "Échec du démarrage du service"
    log_info "Vérifiez les logs avec: sudo journalctl -u $SERVICE_NAME -f"
    exit 1
fi

log_success "Installation terminée!"
