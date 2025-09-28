#!/bin/bash

# Script d'installation du service Palazzeti Controller
# Usage: sudo ./install.sh

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

# Détecter automatiquement le répertoire du projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
SOURCE_DIR="${PROJECT_DIR}/raspberry_pi"
INSTALL_DIR="/opt/palazzeti-controller"
VENV_DIR="${INSTALL_DIR}/venv"
LOG_DIR="/var/log/palazzeti-controller"
SERVICE_SCRIPTS_DIR="${SOURCE_DIR}/service"

# Détecter l'utilisateur approprié
if id "pi" &>/dev/null; then
    SERVICE_USER="pi"
    SERVICE_GROUP="pi"
    log_info "Utilisateur 'pi' détecté (Raspberry Pi OS)"
elif [ -n "$SUDO_USER" ]; then
    SERVICE_USER="$SUDO_USER"
    SERVICE_GROUP="$(id -gn $SUDO_USER)"
    log_info "Utilisation de l'utilisateur sudo: $SERVICE_USER"
else
    # Proposer de créer l'utilisateur pi
    echo ""
    read -p "L'utilisateur 'pi' n'existe pas. Voulez-vous le créer ? [Y/n]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        SERVICE_USER="root"
        SERVICE_GROUP="root"
        log_warning "Utilisation de root (non recommandé)"
    else
        log_info "Création de l'utilisateur 'pi'..."
        useradd -m -s /bin/bash pi
        usermod -a -G sudo pi
        echo "pi:raspberry" | chpasswd
        log_success "Utilisateur 'pi' créé avec le mot de passe 'raspberry'"
        SERVICE_USER="pi"
        SERVICE_GROUP="pi"
    fi
fi

log_info "Utilisateur du service: $SERVICE_USER (groupe: $SERVICE_GROUP)"
log_info "📁 Répertoire du script: $SCRIPT_DIR"
log_info "📁 Répertoire du projet détecté: $PROJECT_DIR"

# Vérifier et configurer les permissions série
log_info "🔧 Configuration des permissions d'accès série..."
if ! groups $SERVICE_USER | grep -q dialout; then
    log_info "Ajout de l'utilisateur $SERVICE_USER au groupe dialout pour l'accès série..."
    usermod -a -G dialout $SERVICE_USER
    log_success "Utilisateur ajouté au groupe dialout"
    log_warning "⚠️  IMPORTANT: L'utilisateur doit se reconnecter pour que les permissions prennent effet"
else
    log_success "L'utilisateur $SERVICE_USER a déjà accès au groupe dialout"
fi

# Vérifier que le répertoire du projet existe
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Le répertoire du projet n'existe pas: $PROJECT_DIR"
    log_info "Assurez-vous que le projet est cloné dans le bon répertoire"
    exit 1
fi

# Vérifier que le répertoire raspberry_pi existe
if [ ! -d "$SOURCE_DIR" ]; then
    log_error "Le répertoire raspberry_pi n'existe pas: $SOURCE_DIR"
    exit 1
fi

# Vérifier que le répertoire service existe
if [ ! -d "$SERVICE_SCRIPTS_DIR" ]; then
    log_error "Le répertoire service n'existe pas: $SERVICE_SCRIPTS_DIR"
    exit 1
fi

log_info "📁 Répertoire d'installation: $INSTALL_DIR"

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
chown $SERVICE_USER:$SERVICE_GROUP $LOG_DIR
chmod 755 $LOG_DIR

# Créer le répertoire d'installation
log_info "📁 Création du répertoire d'installation: $INSTALL_DIR"
mkdir -p $INSTALL_DIR
chown $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
chmod 755 $INSTALL_DIR

# Copier les fichiers nécessaires
log_info "📋 Copie des fichiers de l'application..."
cd $SOURCE_DIR

# Fichiers Python essentiels
cp palazzeti_controller.py $INSTALL_DIR/
cp frame.py $INSTALL_DIR/
cp config.py $INSTALL_DIR/
cp requirements.txt $INSTALL_DIR/

# Répertoire templates
if [ -d "templates" ]; then
    cp -r templates $INSTALL_DIR/
fi

log_success "Fichiers copiés vers $INSTALL_DIR"

# Vérifier et créer l'environnement virtuel si nécessaire
if [ ! -d "$VENV_DIR" ]; then
    log_info "📦 Création de l'environnement virtuel Python..."
    cd $INSTALL_DIR
    if [ "$SERVICE_USER" = "root" ]; then
        python3 -m venv venv
    else
        sudo -u $SERVICE_USER python3 -m venv venv
    fi
    log_success "Environnement virtuel créé"
fi

# Activer l'environnement virtuel et installer les dépendances
log_info "📦 Installation des dépendances Python..."
cd $INSTALL_DIR
if [ "$SERVICE_USER" = "root" ]; then
    $VENV_DIR/bin/pip install --upgrade pip
    $VENV_DIR/bin/pip install -r requirements.txt
else
    sudo -u $SERVICE_USER $VENV_DIR/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER $VENV_DIR/bin/pip install -r requirements.txt
fi
log_success "Dépendances installées"

# Installer la configuration de rotation des logs
log_info "📄 Installation de la configuration de rotation des logs..."
if [ -f "$SERVICE_SCRIPTS_DIR/palazzeti-controller.logrotate" ]; then
    cp $SERVICE_SCRIPTS_DIR/palazzeti-controller.logrotate /etc/logrotate.d/palazzeti-controller
    chmod 644 /etc/logrotate.d/palazzeti-controller
    log_success "Configuration de rotation des logs installée"
else
    log_warning "Fichier de configuration de rotation des logs non trouvé"
fi

# Copier et adapter le fichier de service
log_info "📄 Installation du fichier de service systemd..."
cp $SERVICE_SCRIPTS_DIR/palazzeti-controller.service $SERVICE_FILE

# Adapter les chemins et l'utilisateur dans le fichier de service
log_info "🔧 Configuration des chemins et utilisateur dans le fichier de service..."
sed -i "s|/home/pi/Palazzeti-Controller/raspberry_pi|$INSTALL_DIR|g" $SERVICE_FILE
sed -i "s|User=pi|User=$SERVICE_USER|g" $SERVICE_FILE
sed -i "s|Group=pi|Group=$SERVICE_GROUP|g" $SERVICE_FILE

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
