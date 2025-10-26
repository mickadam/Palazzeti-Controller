"""
Configuration pour le contrôleur Palazzetti
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration série (protocole binaire Palazzetti)
SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')  # Port série pour le câble RJ11
BAUD_RATE = int(os.getenv('BAUD_RATE', '38400'))  # 38400 bauds selon documentation
TIMEOUT = int(os.getenv('TIMEOUT', '10'))
CONNECTION_TEST_TIMEOUT = int(os.getenv('CONNECTION_TEST_TIMEOUT', '5'))  # Timeout pour test de connexion

# Configuration Flask
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'  # Mode debug désactivé par défaut

# Configuration du poêle
DEFAULT_TEMPERATURE = 22.0
MIN_TEMPERATURE = 15.0
MAX_TEMPERATURE = 27.0

# Adresses de registres (protocole binaire)
REGISTER_STATUS = [0x20, 0x1C]  # Statut du poêle
REGISTER_TEMPERATURE = [0x20, 0x0E]  # Température actuelle
REGISTER_SETPOINT = [0x1C, 0x33]  # Température de consigne [0x20, 0x0F] 
REGISTER_POWER_CONTROL = [0x20, 0x1D]  # Contrôle ON/OFF du poêle

# Adresses pour la consigne avec seuil de déclenchement
REGISTER_SETPOINT_8BYTES = [0x1C, 0x32]  # Consigne pour fluide < 2 (8 octets)
REGISTER_SETPOINT_2BYTES = [0x1C, 0x54]  # Consigne pour fluide = 2 (2 octets)

# Registres supplémentaires (à implémenter)
REGISTER_POWER_LEVEL = [0x20, 0x2A]  # Niveau de puissance du poêle [1-5]
REGISTER_START_CONTROL = [0x20, 0x44]  # Contrôle de démarrage
REGISTER_ERROR_CODE = [0x20, 0x1E]  # Code d'erreur du poêle
REGISTER_ALARM_STATUS = [0x20, 0x1F]  # Statut des alarmes
REGISTER_TIMER_SETTINGS = [0x20, 0x72]  # Paramètres utilisateur - Timer (0:Disable 1:Enable)

# Registre de consommation de pellets
REGISTER_PELLET_CONSUMPTION = [0x20, 0x02]  # Consommation totale de pellets (0x2002)

# Registres pour le système de timer/chrono
REGISTER_CHRONO_SETPOINTS = [0x80, 0x2D]  # Températures de consigne des programmes (0x802D)
REGISTER_CHRONO_PROGRAMS = [0x80, 0x00]   # Programmes de timer (0x8000-0x8014)
REGISTER_CHRONO_DAYS = [0x80, 0x18]       # Programmation par jour (0x8018-0x802A)
REGISTER_CHRONO_STATUS = [0x20, 0x7E]     # Statut du timer (0x207E)

# Codes de statut
STATUS_OFF = 0x00
STATUS_TEST_FIRE = 0x01
STATUS_HEAT_UP = 0x02
STATUS_BURNING = 0x06
STATUS_COOLING = 0x09
STATUS_STARTING = 0x11
STATUS_ALARM = 0xFF
STATUS_NO_PELLETS = 253  # E114: No pellets

# Codes de commande de puissance
POWER_OFF = 0x00
POWER_ON = 0x01

# Codes de paramètres utilisateur
TIMER_DISABLE = 0x00
TIMER_ENABLE = 0x01

# Codes d'erreur Palazzetti
ERROR_NONE = 0x00
ERROR_KEYBOARD = 0x01          # E001: Clavier défectueux
ERROR_COMM_LINK = 0x04         # E004: Coupure liaison carte/clavier
ERROR_IGNITION_FAILED = 0x101  # E101: Allumage raté
ERROR_CHIMNEY_DIRTY = 0x102    # E102: Conduit sale (statut 241)
ERROR_NTC2 = 0x105            # E105: Capteur température NTC2 (statut 244)
ERROR_NTC3 = 0x106            # E106: Capteur température NTC3 (statut 245)
ERROR_TC2 = 0x107             # E107: Capteur température TC2 (statut 246)
ERROR_DOOR_OPEN = 0x108        # E108: Porte ou trémie ouverte (statut 247)
ERROR_PRESSURE_ALARM = 0x109   # E109: Alarme pression/disjoncteur (statut 248)
ERROR_AIR_TEMP_SENSOR = 0x110  # E110: Sonde température air (statut 249)
ERROR_FLUE_TEMP_SENSOR = 0x111 # E111: Sonde température fumées (statut 250)
ERROR_GASES_OVER_TEMP = 0x113  # E113: Gaz surchauffés (statut 252)
ERROR_NO_PELLETS = 0x114       # E114: Pas de pellets (statut 253)
ERROR_GENERAL = 0x115          # E115: Erreur générale (statut 254)

# Mapping des statuts
STATUS_MAP = {
    STATUS_OFF: 'OFF',
    STATUS_TEST_FIRE: 'TEST_FIRE',
    STATUS_HEAT_UP: 'HEAT_UP',
    STATUS_BURNING: 'BURNING',
    STATUS_COOLING: 'COOLING',
    STATUS_STARTING: 'STARTING',
    STATUS_ALARM: 'ALARM',
    STATUS_NO_PELLETS: 'NO_PELLETS'
}

# Mapping des codes d'erreur
ERROR_MAP = {
    ERROR_NONE: 'Aucune erreur',
    ERROR_KEYBOARD: 'E001: Clavier de commande défectueux',
    ERROR_COMM_LINK: 'E004: Coupure de liaison carte/clavier',
    ERROR_IGNITION_FAILED: 'E101: Allumage raté (granulés ou braséro)',
    ERROR_CHIMNEY_DIRTY: 'E102: Conduit sale (nettoyage requis)',
    ERROR_NTC2: 'E105: Capteur température NTC2 défaillant',
    ERROR_NTC3: 'E106: Capteur température NTC3 défaillant',
    ERROR_TC2: 'E107: Capteur température TC2 défaillant',
    ERROR_DOOR_OPEN: 'E108: Porte ou trémie ouverte',
    ERROR_PRESSURE_ALARM: 'E109: Alarme pression/disjoncteur',
    ERROR_AIR_TEMP_SENSOR: 'E110: Dysfonctionnement sonde température air',
    ERROR_FLUE_TEMP_SENSOR: 'E111: Dysfonctionnement sonde température fumées',
    ERROR_GASES_OVER_TEMP: 'E113: Gaz surchauffés (nettoyage conduit)',
    ERROR_NO_PELLETS: 'E114: Plus de pellets',
    ERROR_GENERAL: 'E115: Erreur générale (appeler service)'
}

# Mapping des codes de statut numériques vers les messages d'erreur
STATUS_ERROR_MAP = {
    241: 'E102: Conduit sale (nettoyage requis)',
    244: 'E105: Capteur température NTC2 défaillant',
    245: 'E106: Capteur température NTC3 défaillant',
    246: 'E107: Capteur température TC2 défaillant',
    247: 'E108: Porte ou trémie ouverte',
    248: 'E109: Alarme pression/disjoncteur',
    249: 'E110: Dysfonctionnement sonde température air',
    250: 'E111: Dysfonctionnement sonde température fumées',
    252: 'E113: Gaz surchauffés (nettoyage conduit)',
    253: 'E114: Plus de pellets',
    254: 'E115: Erreur générale (appeler service)'
}

# Configuration des notifications
NOTIFICATION_URL = os.getenv('NOTIFICATION_URL', 'http://localhost:5000')

# Configuration des notifications email
NOTIFICATION_CONFIG = {
    'enabled': os.getenv('NOTIFICATIONS_ENABLED', 'true').lower() == 'true',
    'check_interval': int(os.getenv('NOTIFICATION_CHECK_INTERVAL', '30')),  # minutes
    'alerts': {
        'critical_errors': {
            'codes': [253, 247, 248, 252, 254],  # E114, E108, E109, E113, E115
            'cooldown': 1800,  # 30 minutes
            'title': '🚨 Alerte Critique - Poêle Palazzetti'
        },
        'low_pellets': {
            'threshold': 20,  # %
            'cooldown': 3600,  # 1 heure
            'title': '⚠️ Niveau de Pellets Bas'
        },
        'maintenance': {
            'threshold': 500,  # kg
            'cooldown': 86400,  # 24 heures
            'title': '🔧 Maintenance Requise'
        },
        'connection_lost': {
            'cooldown': 1800,  # 30 minutes
            'title': '🔌 Connexion Perdue'
        }
    }
}

# Configuration SMTP pour les notifications email
SMTP_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'username': os.getenv('SMTP_USERNAME', ''),
    'password': os.getenv('SMTP_PASSWORD', ''),
    'from_email': os.getenv('FROM_EMAIL', ''),
    'to_emails': os.getenv('TO_EMAILS', '').split(',') if os.getenv('TO_EMAILS') else [],
    'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
}

