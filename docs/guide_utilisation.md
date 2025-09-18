# Guide d'utilisation - Contrôleur Palazzeti Ines 9

## Prérequis

### Matériel requis
- Raspberry Pi 3 ou 4 (recommandé)
- Câble RJ11 vers USB pour Palazzeti
- Carte microSD 16GB minimum
- Alimentation pour Raspberry Pi
- Câble réseau ou WiFi

### Logiciel requis
- Raspberry Pi OS (Bullseye ou plus récent)
- Python 3.7+
- pip (gestionnaire de paquets Python)

## Installation

### Étape 1 : Préparation du Raspberry Pi

1. **Installer Raspberry Pi OS**
   - Téléchargez Raspberry Pi OS depuis [raspberrypi.org](https://www.raspberrypi.org/software/)
   - Flashez l'image sur votre carte microSD
   - Insérez la carte dans le Raspberry Pi et démarrez

2. **Configuration initiale**
   ```bash
   sudo raspi-config
   ```
   - Activez SSH
   - Configurez votre réseau WiFi
   - Changez le mot de passe par défaut

3. **Mise à jour du système**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

### Étape 2 : Installation du contrôleur

1. **Cloner le projet**
   ```bash
   git clone https://github.com/votre-repo/PalazzetiControler.git
   cd PalazzetiControler
   ```

2. **Exécuter le script d'installation**
   ```bash
   chmod +x raspberry_pi/install.sh
   ./raspberry_pi/install.sh
   ```

3. **Vérifier l'installation**
   ```bash
   sudo systemctl status palazzeti-controller.service
   ```

### Étape 3 : Configuration

1. **Connecter le câble RJ11**
   - Branchez le câble RJ11 vers USB au port USB du Raspberry Pi
   - Vérifiez que le poêle est allumé

2. **Tester la communication**
   ```bash
   cd /opt/palazzeti-controller
   source venv/bin/activate
   python test_communication.py
   ```

3. **Configurer le port série (si nécessaire)**
   ```bash
   sudo nano /opt/palazzeti-controller/config.py
   ```
   Modifiez `SERIAL_PORT` selon votre configuration :
   - `/dev/ttyUSB0` (port USB standard)
   - `/dev/ttyUSB1` (si plusieurs ports USB)
   - `/dev/ttyACM0` (certains adaptateurs)

## Utilisation

### Interface web

1. **Accéder à l'interface**
   - Ouvrez votre navigateur
   - Allez à `http://[IP_RASPBERRY_PI]:5000`
   - Remplacez `[IP_RASPBERRY_PI]` par l'adresse IP de votre Raspberry Pi

2. **Fonctionnalités disponibles**
   - **État du poêle** : Affichage en temps réel de la température, alimentation, mode nuit
   - **Contrôle de température** : Définir la température de consigne (15-30°C)
   - **Allumage/Extinction** : Contrôler l'alimentation du poêle
   - **Mode nuit** : Activer/désactiver le mode nuit
   - **Arrêt d'urgence** : Arrêter immédiatement le poêle

### Commandes système

```bash
# Démarrer le service
sudo systemctl start palazzeti-controller.service

# Arrêter le service
sudo systemctl stop palazzeti-controller.service

# Redémarrer le service
sudo systemctl restart palazzeti-controller.service

# Vérifier le statut
sudo systemctl status palazzeti-controller.service

# Voir les logs
sudo journalctl -u palazzeti-controller.service -f
```

### Dépannage

#### Problème de connexion série
```bash
# Lister les ports disponibles
ls /dev/tty*

# Tester la communication
python test_communication.py

# Vérifier les permissions
sudo usermod -a -G dialout $USER
```

#### Problème de réseau
```bash
# Vérifier l'adresse IP
hostname -I

# Tester la connectivité
ping google.com

# Vérifier le pare-feu
sudo ufw status
```

#### Problème de service
```bash
# Vérifier les logs
sudo journalctl -u palazzeti-controller.service -n 50

# Redémarrer le service
sudo systemctl restart palazzeti-controller.service

# Vérifier la configuration
sudo systemctl cat palazzeti-controller.service
```

## Sécurité

### Recommandations
1. **Changez le mot de passe par défaut** du Raspberry Pi
2. **Utilisez un réseau sécurisé** pour l'accès WiFi
3. **Limitez l'accès réseau** si nécessaire
4. **Surveillez les logs** régulièrement

### Pare-feu
```bash
# Activer le pare-feu
sudo ufw enable

# Autoriser SSH
sudo ufw allow ssh

# Autoriser le port web
sudo ufw allow 5000

# Vérifier le statut
sudo ufw status
```

## Maintenance

### Mise à jour
```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Redémarrer le service
sudo systemctl restart palazzeti-controller.service
```

### Sauvegarde
```bash
# Sauvegarder la configuration
sudo cp -r /opt/palazzeti-controller /backup/

# Restaurer la configuration
sudo cp -r /backup/palazzeti-controller /opt/
```

### Surveillance
```bash
# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier la température du Raspberry Pi
vcgencmd measure_temp
```

## Support

### Logs utiles
- **Logs du service** : `sudo journalctl -u palazzeti-controller.service`
- **Logs système** : `sudo journalctl -f`
- **Logs réseau** : `sudo journalctl -u NetworkManager`

### Informations système
```bash
# Informations Raspberry Pi
cat /proc/cpuinfo | grep Model
cat /proc/meminfo | grep MemTotal

# Informations réseau
ip addr show
ip route show

# Informations série
dmesg | grep tty
```

## Désinstallation

```bash
# Arrêter le service
sudo systemctl stop palazzeti-controller.service

# Désactiver le service
sudo systemctl disable palazzeti-controller.service

# Supprimer le service
sudo rm /etc/systemd/system/palazzeti-controller.service

# Recharger systemd
sudo systemctl daemon-reload

# Supprimer les fichiers
sudo rm -rf /opt/palazzeti-controller
``` 