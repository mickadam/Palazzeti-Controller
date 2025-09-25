"""
Gestion des trames binaires pour le protocole Palazzetti
"""
import logging

logger = logging.getLogger(__name__)


class Frame:
    """Classe pour gérer les trames binaires de 11 bytes"""
    
    def __init__(self, frame_id=None, data=None, buffer=None):
        """
        Initialiser une trame
        
        Args:
            frame_id: ID de la trame (1 byte)
            data: Données (jusqu'à 9 bytes, format C#)
            buffer: Buffer de bytes pour créer une trame depuis des données reçues
        """
        if buffer is not None:
            # Créer une trame depuis un buffer reçu
            self._from_buffer(buffer)
        else:
            # Créer une nouvelle trame
            self.id = frame_id
            self.data = (data or [])[:9]  # Limiter à 9 bytes max (format C#)
            # Compléter avec des zéros si nécessaire
            while len(self.data) < 9:
                self.data.append(0x00)
            self.checksum = self.compute_checksum()
            self.size = 11
    
    def _from_buffer(self, buffer):
        """Créer une trame depuis un buffer de bytes reçu"""
        if len(buffer) < 11:
            raise ValueError(f"Buffer trop court: {len(buffer)} bytes, attendu 11")
        
        self.original_bytes = buffer
        self.id = buffer[0]
        self.data = list(buffer[1:10])  # 9 bytes de données (format C#)
        self.checksum = buffer[10]
        self.size = 11
    
    def compute_checksum(self):
        """Calculer le checksum de la trame"""
        checksum = self.id if self.id is not None else 0
        for byte in self.data:
            checksum += byte
        return checksum & 0xFF  # Garder seulement le byte de poids faible
    
    def is_valid(self):
        """Vérifier si la trame est valide (checksum correct)"""
        if self.checksum is None:
            return False
        return self.compute_checksum() == self.checksum
    
    def as_bytes(self):
        """Convertir la trame en bytes pour l'envoi"""
        if self.size == 11:
            bytes_array = bytearray(11)
            bytes_array[0] = self.id
            for i, byte in enumerate(self.data):
                bytes_array[i + 1] = byte
            bytes_array[10] = self.compute_checksum()
            return bytes(bytes_array)
        else:
            # Fallback pour d'autres tailles
            return self.original_bytes
    
    def get_id(self):
        """Obtenir l'ID de la trame"""
        return self.id
    
    def get_data(self):
        """Obtenir les données de la trame"""
        return self.data
    
    def get_d0(self):
        """Obtenir le premier byte de données (d0) comme en C#"""
        return self.data[0] if len(self.data) > 0 else 0
    
    def __str__(self):
        """Représentation string de la trame"""
        data_str = ' '.join([f'{b:02X}' for b in self.data])
        return f"Frame(ID=0x{self.id:02X}, Data=[{data_str}], CS=0x{self.checksum:02X}, Valid={self.is_valid()})"


def construct_read_frame(address):
    """
    Construire une trame de lecture pour une adresse donnée
    
    Args:
        address: Liste de 2 bytes [adresse_haute, adresse_basse]
    
    Returns:
        Frame: Trame de lecture prête à envoyer
    """
    if len(address) != 2:
        raise ValueError("L'adresse doit contenir exactement 2 bytes")
    
    # Format C#: [adresse_LSB][adresse_MSB] + 7 bytes de padding
    # address[0] = MSB, address[1] = LSB
    data = [address[1], address[0]] + [0x00] * 7  # LSB en premier, puis MSB
    return Frame(frame_id=0x02, data=data)  # ID 0x02 pour la lecture (comme C#)


def construct_write_frame(address, value_bytes):
    """
    Construire une trame d'écriture pour une adresse et des données
    
    Args:
        address: Liste de 2 bytes [adresse_haute, adresse_basse]
        value_bytes: Liste des bytes à écrire
    
    Returns:
        Frame: Trame d'écriture prête à envoyer
    """
    if len(address) != 2:
        raise ValueError("L'adresse doit contenir exactement 2 bytes")
    
    # Format C#: [adresse_basse][adresse_haute] + valeur + padding
    data = [address[1], address[0]] + value_bytes  # Inverser l'ordre des bytes d'adresse
    while len(data) < 9:  # 9 bytes de données comme en C#
        data.append(0x00)
    
    return Frame(frame_id=0x01, data=data)  # ID 0x01 pour l'écriture (comme C#)


def parse_temperature(data):
    """
    Parser la température depuis les données de la trame
    
    Args:
        data: Liste des bytes de données (format C#: 9 bytes)
    
    Returns:
        float: Température en degrés Celsius
    """
    if len(data) < 1:
        return 0.0
    
    temp_raw = (data[1] << 8) | data[0]
    temperature = temp_raw / 10.0
    
    return temperature


def parse_setpoint(data, fluid_type=0):
    """
    Parser la température de consigne avec seuil de déclenchement
    
    Args:
        data: Liste des bytes de données (8 bytes pour fluide < 2, 2 bytes pour fluide = 2)
        fluid_type: Type de fluide (0, 1, ou 2)
    
    Returns:
        tuple: (setpoint, seco, beco) où:
            - setpoint: Température de consigne en °C
            - seco: Seuil de déclenchement (trigger) pour arrêt/démarrage automatique
            - beco: Booléen BECO
    """
    if fluid_type < 2:
        # Fluide < 2: lecture de 8 octets
        if len(data) < 8:
            return 0.0, 0, False
        
        seco = data[0]  # Premier octet = seuil de déclenchement (trigger)
        setpoint_raw = data[1]  # Deuxième octet = consigne brute
        beco = data[3] > 0  # 4ème octet > 0 = true
        
        if fluid_type == 0:
            # Fluide = 0: conversion en décimal
            seco = seco / 10.0  # Seuil de déclenchement en °C
            setpoint = setpoint_raw / 5.0
        else:
            # Fluide = 1: pas de conversion
            setpoint = float(setpoint_raw)
        
        return setpoint, seco, beco
    
    elif fluid_type == 2:
        # Fluide = 2: lecture de 2 octets
        if len(data) < 2:
            return 0.0, 0, False
        
        # 2 octets en little-endian
        setpoint_raw = data[0] | (data[1] << 8)
        setpoint = float(setpoint_raw)  # Conversion en int16_t
        
        return setpoint, 0, False
    
    else:
        return 0.0, 0, False


def parse_status(data):
    """
    Parser le statut depuis les données de la trame
    
    Args:
        data: Liste des bytes de données
    
    Returns:
        tuple: (status_code, status_name, power_on)
    """
    if len(data) < 1:
        return 0, 'UNKNOWN', False
    
    # Le statut est dans data[0] (après l'adresse LSB, MSB) - 1 byte
    status_code = data[0]
    
    # Mapping des codes de statut
    status_map = {
        0: ('OFF', False),
        1: ('---', False),
        2: ('TEST FIRE', True),
        3: ('HEAT UP', True),
        4: ('FUEL IGN', True),
        5: ('IGN TEST', True),
        6: ('BURNING', True),
        7: ('---', False),
        8: ('---', False),
        9: ('COOLING', False),
        10: ('FIRE STOP', False),
        11: ('CLEAN FIRE', False),
        12: ('COOL', False),
        13: ('OFF', False),
        14: ('HEAT UP', True),
        15: ('FIRE UP', True),
        16: ('STABILIZATION', True),
        17: ('BURNING', True),
        18: ('CLEANING', False),
        19: ('FINAL CLEANING', False),
        20: ('STANDBY', False),
        21: ('ALARM', False),
        22: ('ALARM', False)
    }
    
    status_name, power_on = status_map.get(status_code, (f'STATUS_{status_code}', False))
    return status_code, status_name, power_on

