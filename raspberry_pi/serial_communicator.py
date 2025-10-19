"""
Gestionnaire de communication série pour le protocole Palazzetti
"""
import serial
import time
import threading
import logging
from frame import Frame, construct_read_frame, construct_write_frame

logger = logging.getLogger(__name__)


class SerialCommunicator:
    """Gestionnaire de communication série avec le poêle Palazzetti"""
    
    def __init__(self):
        self.serial_connection = None
        self.lock = threading.Lock()
        
    def connect(self, port, baudrate=38400, timeout=10):
        """
        Établir la connexion série au poêle avec test de communication
        
        Args:
            port: Port série (ex: '/dev/ttyUSB0')
            baudrate: Vitesse de communication (défaut: 38400)
            timeout: Timeout en secondes (défaut: 10)
        
        Returns:
            bool: True si connexion réussie, False sinon
        """
        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,  # 2 stop bits selon documentation
            )
            logger.info(f"Connexion série établie sur {port} ({baudrate}, 8N2)")
            
            # Test de communication pour vérifier que le poêle répond
            if self._test_communication():
                logger.info("Test de communication réussi - poêle détecté")
                return True
            else:
                logger.warning("Test de communication échoué - câble peut-être déconnecté")
                self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Erreur de connexion série: {e}")
            return False
    
    def _test_communication(self):
        """
        Tester la communication avec le poêle pour vérifier la connexion
        
        Returns:
            bool: True si le poêle répond, False sinon
        """
        try:
            # Attendre une trame de synchronisation (0x00) pendant 3 secondes
            sync_frame = self.synchro_trame(0x00, timeout=3)
            if sync_frame:
                logger.debug("Trame de synchronisation reçue - poêle détecté")
                return True
            else:
                logger.debug("Aucune trame de synchronisation reçue - poêle non détecté")
                return False
        except Exception as e:
            logger.error(f"Erreur lors du test de communication: {e}")
            return False
    
    def disconnect(self):
        """Fermer la connexion série"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                logger.info("Connexion série fermée")
        except Exception as e:
            logger.warning(f"Erreur lors de la fermeture de la connexion série: {e}")
    
    def is_connected(self):
        """Vérifier si la connexion est active"""
        if not self.serial_connection:
            return False
        
        if not self.serial_connection.is_open:
            return False
        
        # Test de communication pour vérifier que le poêle répond
        try:
            # Tenter de lire une trame de synchronisation avec un timeout configurable
            from config import CONNECTION_TEST_TIMEOUT
            sync_frame = self.synchro_trame(0x00, timeout=CONNECTION_TEST_TIMEOUT)
            if sync_frame:
                logger.debug("Test de connexion réussi - poêle répond")
                return True
            else:
                logger.debug("Aucune trame de synchronisation reçue - connexion considérée comme perdue")
                return False
        except Exception as e:
            logger.debug(f"Erreur lors du test de connexion: {e}")
            return False
    
    def synchro_trame(self, expected_id, timeout=5):
        """
        Attendre une trame avec un ID spécifique (équivalent C# SynchroTrame)
        
        Args:
            expected_id: ID de trame attendu
            timeout: Timeout en secondes (défaut 5s comme C#)
        
        Returns:
            Frame ou None si timeout
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting >= 11:
                buffer = self.serial_connection.read(11)
                frame = Frame(buffer=buffer)
                if frame.is_valid():
                    if frame.get_id() == expected_id:
                        logger.debug(f"Trame trouvée avec ID 0x{expected_id:02X}")
                        return frame
            # Pas de sleep pour être plus réactif comme le code C#
        
        logger.debug(f"Timeout: aucune trame avec ID 0x{expected_id:02X} reçue")
        return None
    
    def send_read_command(self, address):
        """
        Envoyer une commande de lecture pour une adresse donnée
        Implémentation basée sur le code C# ReadRegisterWithID
        
        Args:
            address: Adresse du registre à lire [MSB, LSB]
        
        Returns:
            Frame ou None si erreur
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Connexion série non disponible")
            return None
        
        start_time = time.time()
        with self.lock:
            try:
                # Construire la trame de lecture
                read_frame = construct_read_frame(address)
                expected_id = read_frame.get_id()
                
                # Boucle de retry comme dans le code C# (max 5 tentatives)
                for attempt in range(5):
                    logger.debug(f"Tentative {attempt + 1}/5...")
                    
                    # 1. Attendre la trame de synchronisation (0x00)
                    sync_frame = self.synchro_trame(0x00, timeout=2)
                    if sync_frame:
                        logger.debug("Trame de synchronisation reçue")
                        
                        # 2. Envoyer la commande de lecture
                        logger.debug(f"Envoi commande: {read_frame}")
                        self.serial_connection.write(read_frame.as_bytes())
                        self.serial_connection.flush()
                        
                        # 3. Attendre la réponse avec le même ID
                        response = self.synchro_trame(expected_id, timeout=1)
                        if response:
                            end_time = time.time()
                            read_duration = end_time - start_time
                            logger.debug(f"Réponse reçue: {response} (⏱️ {read_duration:.3f}s)")
                            return response
                        else:
                            logger.debug(f"Pas de réponse avec ID 0x{expected_id:02X}")
                    else:
                        logger.debug("Pas de trame de synchronisation")
                
                end_time = time.time()
                read_duration = end_time - start_time
                logger.error(f"Échec après 5 tentatives (⏱️ {read_duration:.3f}s)")
                return None
                    
            except Exception as e:
                end_time = time.time()
                read_duration = end_time - start_time
                logger.error(f"Erreur lors de l'envoi de commande de lecture: {e} (⏱️ {read_duration:.3f}s)")
                return None
    
    def send_write_command(self, address, value_bytes):
        """
        Envoyer une commande d'écriture pour une adresse et des données
        
        Args:
            address: Adresse du registre à écrire [MSB, LSB]
            value_bytes: Données à écrire
        
        Returns:
            Frame ou None si erreur
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Connexion série non disponible")
            return None
        
        start_time = time.time()
        with self.lock:
            try:
                # Construire la trame d'écriture
                write_frame = construct_write_frame(address, value_bytes)
                expected_id = write_frame.get_id()
                
                # Boucle de retry comme pour la lecture (max 2 tentatives)
                for attempt in range(2):
                    logger.debug(f"Tentative {attempt + 1}/2...")
                    
                    # 1. Attendre la trame de synchronisation (0x00)
                    sync_frame = self.synchro_trame(0x00, timeout=5)
                    if sync_frame:
                        logger.debug("Trame de synchronisation reçue")
                        
                        # 2. Envoyer la commande d'écriture
                        logger.debug(f"Envoi commande: {write_frame}")
                        self.serial_connection.write(write_frame.as_bytes())
                        self.serial_connection.flush()
                        
                        # 3. Attendre la réponse avec le même ID
                        response = self.synchro_trame(expected_id, timeout=5)
                        if response:
                            end_time = time.time()
                            write_duration = end_time - start_time
                            logger.debug(f"Réponse reçue: {response} (⏱️ {write_duration:.3f}s)")
                            return response
                        else:
                            logger.debug(f"Pas de réponse avec ID 0x{expected_id:02X}")
                    else:
                        logger.debug("Pas de trame de synchronisation")
                
                end_time = time.time()
                write_duration = end_time - start_time
                logger.error(f"Échec après 2 tentatives (⏱️ {write_duration:.3f}s)")
                return None
                    
            except Exception as e:
                end_time = time.time()
                write_duration = end_time - start_time
                logger.error(f"Erreur lors de l'envoi de commande d'écriture: {e} (⏱️ {write_duration:.3f}s)")
                return None
    
