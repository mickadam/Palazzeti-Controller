# Service Palazzeti Controller

Ce dossier contient tous les fichiers nécessaires pour installer et gérer le service Palazzeti Controller sur un système Linux.

## 📁 Contenu du dossier

- **`install.sh`** - Script d'installation du service
- **`uninstall.sh`** - Script de désinstallation du service
- **`palazzeti-controller.service`** - Fichier de configuration systemd
- **`palazzeti-controller.logrotate`** - Configuration de rotation des logs
- **`README.md`** - Ce fichier de documentation

## 🚀 Installation

### Prérequis
- Système Linux avec systemd
- Python 3.7+
- Accès root (sudo)

### Installation du service
```bash
# Se placer dans le dossier service
cd /home/pi/Palazzeti-Controller/raspberry_pi/service

# Rendre le script exécutable
chmod +x install.sh

# Installer le service (nécessite sudo)
sudo ./install.sh
```

### Gestion du service
```bash
# Voir le statut
sudo systemctl status palazzeti-controller

# Démarrer le service
sudo systemctl start palazzeti-controller

# Arrêter le service
sudo systemctl stop palazzeti-controller

# Redémarrer le service
sudo systemctl restart palazzeti-controller

# Voir les logs en temps réel
sudo journalctl -u palazzeti-controller -f

# Voir les logs récents
sudo journalctl -u palazzeti-controller --since "1 hour ago"
```

## 🗑️ Désinstallation

```bash
# Se placer dans le dossier service
cd /home/pi/Palazzeti-Controller/raspberry_pi/service

# Rendre le script exécutable
chmod +x uninstall.sh

# Désinstaller le service
sudo ./uninstall.sh
```

## ⚙️ Configuration

### Utilisateur du service
Le script d'installation détecte automatiquement l'utilisateur approprié :
- **Raspberry Pi OS** : Utilise l'utilisateur `pi`
- **Autres systèmes** : Utilise l'utilisateur qui a lancé sudo
- **Création automatique** : Propose de créer l'utilisateur `pi` si nécessaire

### Permissions série
Le script ajoute automatiquement l'utilisateur du service au groupe `dialout` pour l'accès aux ports série.

### Répertoires
- **Installation** : `/opt/palazzeti-controller/`
- **Logs** : `/var/log/palazzeti-controller/`
- **Service** : `/etc/systemd/system/palazzeti-controller.service`

## 🔧 Personnalisation

### Variables d'environnement
Le service utilise les variables d'environnement suivantes (modifiables dans le fichier `.service`) :
- `DEBUG=False` - Mode debug
- `LOG_LEVEL=INFO` - Niveau de log
- `SERIAL_PORT=/dev/ttyUSB0` - Port série
- `HOST=0.0.0.0` - Adresse d'écoute
- `PORT=5000` - Port web

### Rotation des logs
La configuration de rotation des logs est installée automatiquement dans `/etc/logrotate.d/palazzeti-controller`.

## 🌐 Accès à l'interface

Une fois le service installé et démarré, l'interface web est accessible sur :
- **URL locale** : http://localhost:5000
- **URL réseau** : http://[IP_DU_SYSTEME]:5000

Pour trouver l'IP de votre système :
```bash
hostname -I
```

## 🐛 Dépannage

### Service ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u palazzeti-controller -f

# Vérifier le statut
sudo systemctl status palazzeti-controller

# Vérifier les permissions
ls -la /opt/palazzeti-controller/
```

### Problème d'accès série
```bash
# Vérifier les groupes de l'utilisateur
groups pi

# Ajouter manuellement au groupe dialout
sudo usermod -a -G dialout pi
```

### Interface non accessible
```bash
# Vérifier que le service écoute
sudo netstat -tlnp | grep :5000

# Vérifier le firewall
sudo ufw status
```

## 📚 Documentation

- [README principal](../../README.md)
- [Protocole de communication](../../docs/protocole_palazzeti.md)
- [Guide d'utilisation](../../docs/guide_utilisation.md)
