"""
Gestion des trames binaires pour le protocole Palazzetti
"""
import logging

logger = logging.getLogger(__name__)


class Frame:
    """Classe pour gérer les trames binaires de 11 bytes"""
    
    def __init__(self, frame_id=None, data=None, pad=0x00, buffer=None):
        """
        Initialiser une trame
        
        Args:
            frame_id: ID de la trame (1 byte)
            data: Données (jusqu'à 8 bytes)
            pad: Padding (1 byte, par défaut 0x00)
            buffer: Buffer de bytes pour créer une trame depuis des données reçues
        """
        if buffer is not None:
            # Créer une trame depuis un buffer reçu
            self._from_buffer(buffer)
        else:
            # Créer une nouvelle trame
            self.id = frame_id
            self.data = (data or [])[:8]  # Limiter à 8 bytes max
            # Compléter avec des zéros si nécessaire
            while len(self.data) < 8:
                self.data.append(0x00)
            self.pad = pad
            self.checksum = self.compute_checksum()
            self.size = 11
    
    def _from_buffer(self, buffer):
        """Créer une trame depuis un buffer de bytes reçu"""
        if len(buffer) < 11:
            raise ValueError(f"Buffer trop court: {len(buffer)} bytes, attendu 11")
        
        self.original_bytes = buffer
        self.id = buffer[0]
        self.data = list(buffer[1:9])
        self.pad = buffer[9]
        self.checksum = buffer[10]
        self.size = 11
    
    def compute_checksum(self):
        """Calculer le checksum de la trame"""
        checksum = self.id if self.id is not None else 0
        for byte in self.data:
            checksum += byte
        checksum += self.pad
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
            bytes_array[9] = self.pad
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
    
    data = address + [0x00] * 6  # Adresse + 6 bytes de padding
    return Frame(frame_id=0x01, data=data)


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
    
    # Construire les données: adresse + valeur + padding
    data = address + value_bytes
    while len(data) < 8:
        data.append(0x00)
    
    return Frame(frame_id=0x02, data=data)  # ID 0x02 pour l'écriture


def parse_temperature(data):
    """
    Parser la température depuis les données de la trame
    
    Args:
        data: Liste des bytes de données
    
    Returns:
        float: Température en degrés Celsius
    """
    if len(data) < 2:
        return 0.0
    
    # Température sur 2 bytes (big-endian)
    temp_raw = (data[0] << 8) | data[1]
    # Conversion selon le format Palazzetti (à ajuster selon la documentation)
    temperature = temp_raw / 10.0
    return temperature


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
    
    status_code = data[0]
    
    # Mapping des codes de statut
    status_map = {
        0x00: ('OFF', False),
        0x06: ('BURNING', True),
        0x09: ('COOLING', False),
        0x11: ('STARTING', True)
    }
    
    status_name, power_on = status_map.get(status_code, (f'STATUS_{status_code:02X}', False))
    return status_code, status_name, power_on

