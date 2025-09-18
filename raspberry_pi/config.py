"""
Configuration pour le contrôleur Palazzetti
"""
import os

# Configuration série (protocole binaire Palazzetti)
SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')  # Port série pour le câble RJ11
BAUD_RATE = int(os.getenv('BAUD_RATE', '38400'))  # 38400 bauds selon documentation
TIMEOUT = int(os.getenv('TIMEOUT', '5'))

# Configuration Flask
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Configuration du poêle
DEFAULT_TEMPERATURE = 22.0
MIN_TEMPERATURE = 15.0
MAX_TEMPERATURE = 35.0

# Adresses de registres (protocole binaire)
REGISTER_STATUS = [0x20, 0x1C]  # Statut du poêle
REGISTER_TEMPERATURE = [0x20, 0x0E]  # Température actuelle
REGISTER_SETPOINT = [0x20, 0x0F]  # Température de consigne

# Codes de statut
STATUS_OFF = 0x00
STATUS_BURNING = 0x06
STATUS_COOLING = 0x09
STATUS_STARTING = 0x11

# Mapping des statuts
STATUS_MAP = {
    STATUS_OFF: 'OFF',
    STATUS_BURNING: 'BURNING',
    STATUS_COOLING: 'COOLING',
    STATUS_STARTING: 'STARTING'
}

