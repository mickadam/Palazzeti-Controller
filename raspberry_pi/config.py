"""
Configuration pour le contrôleur Palazzetti
"""
import os

# Configuration série (protocole binaire Palazzetti)
SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')  # Port série pour le câble RJ11
BAUD_RATE = int(os.getenv('BAUD_RATE', '38400'))  # 38400 bauds selon documentation
TIMEOUT = int(os.getenv('TIMEOUT', '10'))

# Configuration Flask
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'  # Mode dev activé par défaut

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

# Codes de statut
STATUS_OFF = 0x00
STATUS_TEST_FIRE = 0x01
STATUS_HEAT_UP = 0x02
STATUS_BURNING = 0x06
STATUS_COOLING = 0x09
STATUS_STARTING = 0x11
STATUS_ALARM = 0xFF

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
ERROR_DOOR_OPEN = 0x108        # E108: Porte ou trémie ouverte
ERROR_PRESSURE_ALARM = 0x109   # E109: Alarme pression/disjoncteur
ERROR_AIR_TEMP_SENSOR = 0x110  # E110: Sonde température air
ERROR_FLUE_TEMP_SENSOR = 0x111 # E111: Sonde température fumées

# Mapping des statuts
STATUS_MAP = {
    STATUS_OFF: 'OFF',
    STATUS_TEST_FIRE: 'TEST_FIRE',
    STATUS_HEAT_UP: 'HEAT_UP',
    STATUS_BURNING: 'BURNING',
    STATUS_COOLING: 'COOLING',
    STATUS_STARTING: 'STARTING',
    STATUS_ALARM: 'ALARM'
}

# Mapping des codes d'erreur
ERROR_MAP = {
    ERROR_NONE: 'Aucune erreur',
    ERROR_KEYBOARD: 'E001: Clavier de commande défectueux',
    ERROR_COMM_LINK: 'E004: Coupure de liaison carte/clavier',
    ERROR_IGNITION_FAILED: 'E101: Allumage raté (granulés ou braséro)',
    ERROR_DOOR_OPEN: 'E108: Porte ou trémie ouverte',
    ERROR_PRESSURE_ALARM: 'E109: Alarme pression/disjoncteur',
    ERROR_AIR_TEMP_SENSOR: 'E110: Dysfonctionnement sonde température air',
    ERROR_FLUE_TEMP_SENSOR: 'E111: Dysfonctionnement sonde température fumées'
}

