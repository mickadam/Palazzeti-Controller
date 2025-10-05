#!/bin/bash

# Script de désinstallation du service Palazzeti Controller
# Usage: sudo ./uninstall.sh

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

log_info "🗑️  Désinstallation du service Palazzeti Controller"
echo "====================================================="

# Variables
SERVICE_NAME="palazzeti-controller"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
INSTALL_DIR="/opt/palazzeti-controller"
LOG_DIR="/var/log/palazzeti-controller"

# Vérifier si le service existe
if [ ! -f "$SERVICE_FILE" ]; then
    log_warning "Le service $SERVICE_NAME n'est pas installé"
    exit 0
fi

# Arrêter le service s'il est en cours d'exécution
if systemctl is-active --quiet $SERVICE_NAME; then
    log_info "Arrêt du service..."
    systemctl stop $SERVICE_NAME
    log_success "Service arrêté"
else
    log_info "Le service n'était pas en cours d'exécution"
fi

# Désactiver le service
if systemctl is-enabled --quiet $SERVICE_NAME; then
    log_info "Désactivation du service..."
    systemctl disable $SERVICE_NAME
    log_success "Service désactivé"
else
    log_info "Le service n'était pas activé"
fi

# Supprimer le fichier de service
log_info "Suppression du fichier de service..."
rm -f $SERVICE_FILE
log_success "Fichier de service supprimé"

# Supprimer la configuration de rotation des logs
if [ -f "/etc/logrotate.d/palazzeti-controller" ]; then
    log_info "Suppression de la configuration de rotation des logs..."
    rm -f /etc/logrotate.d/palazzeti-controller
    log_success "Configuration de rotation des logs supprimée"
fi

# Recharger systemd
log_info "Rechargement de la configuration systemd..."
systemctl daemon-reload
log_success "Configuration systemd rechargée"

# Demander si on veut supprimer les fichiers d'installation
if [ -d "$INSTALL_DIR" ]; then
    echo ""
    read -p "Voulez-vous supprimer les fichiers d'installation ($INSTALL_DIR) ? [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Suppression des fichiers d'installation..."
        rm -rf $INSTALL_DIR
        log_success "Fichiers d'installation supprimés"
    else
        log_info "Conservation des fichiers d'installation: $INSTALL_DIR"
    fi
fi

# Demander si on veut supprimer les logs
if [ -d "$LOG_DIR" ]; then
    echo ""
    read -p "Voulez-vous supprimer le répertoire de logs ($LOG_DIR) ? [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Suppression du répertoire de logs..."
        rm -rf $LOG_DIR
        log_success "Répertoire de logs supprimé"
    else
        log_info "Conservation du répertoire de logs: $LOG_DIR"
    fi
fi

# Vérifier que le service est bien supprimé
if [ ! -f "$SERVICE_FILE" ] && ! systemctl list-unit-files | grep -q $SERVICE_NAME; then
    log_success "Service désinstallé avec succès!"
    echo ""
    log_info "Le contrôleur Palazzeti peut toujours être lancé manuellement :"
    echo "  cd /opt/palazzeti-controller"
    echo "  source venv/bin/activate"
    echo "  python app.py"
else
    log_error "Erreur lors de la désinstallation du service"
    exit 1
fi

log_success "Désinstallation terminée!"
