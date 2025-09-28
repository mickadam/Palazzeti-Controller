# WIP - Contrôleur Palazzetti

Interface web moderne pour contrôler un poêle à pellets Palazzetti via communication série.

## 🚀 Fonctionnalités

- **Interface web moderne** avec design responsive
- **Communication série binaire** avec le protocole Palazzetti (38400, 8N2)
- **Contrôle en temps réel** via WebSocket
- **Mode développement** avec simulation série
- **Tests de communication** intégrés
- **Support multi-plateforme** (Windows, Linux, macOS)

## 📋 Prérequis

- Python 3.7+
- Port série disponible (USB-RS232 ou adaptateur RJ11)
- Poêle Palazzetti compatible

## 🛠️ Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd PalazzetiControler/raspberry_pi
```

### 2. Créer et activer l'environnement virtuel
```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
# Sur Linux/macOS :
source venv/bin/activate
# Sur Windows :
venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

> **Note** : L'environnement virtuel est nécessaire pour éviter les conflits avec les packages système, surtout sur les nouvelles versions de Python qui protègent l'environnement global.

### 4. Gestion de l'environnement virtuel

#### Activation/Désactivation
```bash
# Activer l'environnement virtuel
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows

# Désactiver l'environnement virtuel
deactivate
```

#### Vérification
```bash
# Vérifier que l'environnement est activé (vous devriez voir (venv) dans le prompt)
which python    # Linux/macOS
where python    # Windows
```

### 5. Configuration
Les paramètres par défaut sont dans `config.py` :
- **Port série** : `/dev/ttyUSB0` (Linux) ou `COM3` (Windows)
- **Baudrate** : 38400
- **Configuration** : 8N2 (8 bits, pas de parité, 2 stop bits)

## 🎯 Utilisation

### Mode développement (sans poêle)
```bash
# Linux/macOS - Le script gère automatiquement l'environnement virtuel
./dev.sh

# Windows - Le script gère automatiquement l'environnement virtuel
dev.cmd
```

### Mode production (avec poêle connecté)
```bash
# Linux/macOS - Activer l'environnement virtuel d'abord
source venv/bin/activate
python palazzetti_controller.py

# Windows - Le script gère automatiquement l'environnement virtuel
dev-serial.cmd
```

## 🚀 Installation en tant que service (Raspberry Pi)

Pour lancer automatiquement le contrôleur au démarrage du Raspberry Pi :

### 1. Installation du service
```bash
# Se placer dans le répertoire du service
cd /home/pi/Palazzeti-Controller/raspberry_pi/service

# Rendre le script d'installation exécutable
chmod +x install.sh

# Installer le service (nécessite sudo)
sudo ./install.sh
```

### 2. Gestion du service
```bash
# Voir le statut du service
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

### 3. Désinstallation du service
```bash
# Se placer dans le répertoire du service
cd /home/pi/Palazzeti-Controller/raspberry_pi/service

# Rendre le script de désinstallation exécutable
chmod +x uninstall.sh

# Désinstaller le service
sudo ./uninstall.sh
```

### 4. Configuration du service

Le service est configuré pour :
- **Démarrage automatique** au boot du système
- **Redémarrage automatique** en cas de crash
- **Logs centralisés** via journald
- **Permissions série** (groupe dialout)
- **Sécurité** (isolation des processus)

### 5. Accès à l'interface

Une fois le service installé et démarré, l'interface web est accessible sur :
- **URL locale** : http://localhost:5000
- **URL réseau** : http://[IP_DU_RASPBERRY]:5000

Pour trouver l'IP de votre Raspberry Pi :
```bash
hostname -I
```

## 📁 Structure du projet

```
Palazzeti-Controller/
├── raspberry_pi/                 # Code principal
│   ├── palazzeti_controller.py   # Application principale
│   ├── frame.py                  # Gestion des trames
│   ├── config.py                 # Configuration
│   ├── templates/                # Templates web
│   ├── service/                  # Scripts de service
│   │   ├── install.sh            # Installation du service
│   │   ├── uninstall.sh          # Désinstallation du service
│   │   ├── palazzeti-controller.service
│   │   ├── palazzeti-controller.logrotate
│   │   └── README.md             # Documentation du service
│   └── requirements.txt          # Dépendances Python
├── docs/                         # Documentation
└── tests/                        # Tests et scripts de debug
```

### Tests de communication
```bash
# Activer l'environnement virtuel d'abord
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Test complet
python test_communication.py

# Tests spécifiques
python test_communication.py --ports    # Lister les ports
python test_communication.py --sync     # Test synchronisation
python test_communication.py --status   # Test lecture statut
python test_communication.py --temp     # Test lecture température
```

## 🌐 Interface web

Une fois lancé, l'interface est disponible sur :
- **URL** : http://localhost:5000
- **Fonctionnalités** :
  - Affichage du statut en temps réel
  - Contrôle de la température de consigne
  - Allumage/Extinction du poêle
  - Interface responsive (mobile/desktop)

## 🔧 Configuration avancée

### Variables d'environnement
```bash
export SERIAL_PORT="/dev/ttyUSB0"  # Port série
export BAUD_RATE="38400"           # Vitesse de communication
export TIMEOUT="5"                 # Timeout en secondes
export HOST="0.0.0.0"              # Adresse d'écoute
export PORT="5000"                 # Port web
export DEBUG="true"                # Mode debug
```

### Protocole de communication

Le poêle Palazzetti utilise un **protocole binaire** :
- **Format** : Trames de 11 bytes `[ID][D0-D7][PAD][CS]`
- **Synchronisation** : Trame `0x00` avant chaque commande
- **Lecture** : ID `0x01` avec adresse sur 2 bytes
- **Écriture** : ID `0x02` avec adresse + données
- **Checksum** : Somme simple des bytes

#### Adresses de registres
- `0x20, 0x1C` : Statut du poêle
- `0x20, 0x0E` : Température actuelle
- `0x20, 0x0F` : Température de consigne

## 🐛 Dépannage

### Problèmes courants

#### 1. Port série non trouvé
```bash
# Activer l'environnement virtuel d'abord
source venv/bin/activate

# Lister les ports disponibles
python test_communication.py --ports

# Vérifier les permissions (Linux)
sudo usermod -a -G dialout $USER
```

#### 2. Erreur de communication
- Vérifier que le poêle est allumé
- Vérifier la connexion du câble RJ11
- Tester avec `python test_communication.py --sync` (après activation de l'environnement virtuel)

#### 3. Interface non accessible
- Vérifier que le port 5000 est libre
- Vérifier le firewall
- Utiliser `http://127.0.0.1:5000` au lieu de `localhost`

### Logs de debug
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Activer les logs détaillés
export DEBUG=true
python palazzetti_controller.py
```

## 📚 Documentation

- [Protocole de communication](docs/protocole_palazzeti.md)
- [Guide d'utilisation](docs/guide_utilisation.md)
- [Mode nuit](docs/mode_nuit_explication.md)

## 🔗 Références

- [Blog Palazzetti-Martina - La liaison série](https://palazzetti-martina.blogspot.com/2020/01/la-liaison-serie.html)
- [Blog Palazzetti-Martina - Les trames](https://palazzetti-martina.blogspot.com/2020/01/les-trames.html)
- [Blog Palazzetti-Martina - Table des registres](https://palazzetti-martina.blogspot.com/2020/02/la-table-des-registres.html)
- [Bibliothèque C++ Palazzetti par Domochip](https://github.com/Domochip/Palazzetti) - Implémentation alternative en C++ pour ESP8266 et microcontrôleurs

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Ajouter de nouvelles fonctionnalités

## 📞 Support

Pour toute question ou problème :
1. Vérifiez la documentation
2. Consultez les issues existantes
3. Créez une nouvelle issue si nécessaire


