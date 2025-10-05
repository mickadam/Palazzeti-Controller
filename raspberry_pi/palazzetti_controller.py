"""
Contrôleur Palazzetti avec logique de contrôle séparée de la communication
"""
import time
import threading
import logging
from serial_communicator import SerialCommunicator
from frame import parse_temperature, parse_status, parse_setpoint
from config import *

logger = logging.getLogger(__name__)


class PalazzettiController:
    """Contrôleur pour le poêle Palazzetti avec logique de contrôle séparée"""
    
    def __init__(self):
        self.communicator = SerialCommunicator()
        self.state_lock = threading.Lock()  # Sémaphore pour get_state()
        self.last_state_read = 0  # Timestamp de la dernière lecture
        self.state_cache_duration = 10  # Durée du cache en secondes
        self.state = {
            'connected': False,
            'synchronized': False,
            'status': 'OFF',
            'power': False,
            'temperature': DEFAULT_TEMPERATURE,
            'setpoint': DEFAULT_TEMPERATURE,
            'night_mode': False,
            'error_code': 0,
            'error_message': 'Aucune erreur',
            'seco': 0,            # Seuil de déclenchement (trigger) pour arrêt/démarrage automatique
            'power_level': 0,     # Niveau de puissance (1-5)
            'alarm_status': 0,    # Statut des alarmes
            'timer_enabled': False # Timer activé/désactivé
        }
        self.running = False
        
    def connect(self, port=None, baudrate=38400, timeout=10):
        """
        Établir la connexion au poêle
        
        Args:
            port: Port série (utilise SERIAL_PORT par défaut si None)
            baudrate: Vitesse de communication
            timeout: Timeout en secondes
        
        Returns:
            bool: True si connexion réussie, False sinon
        """
        if port is None:
            port = SERIAL_PORT
            
        success = self.communicator.connect(port, baudrate, timeout)
        self.state['connected'] = success
        if success:
            # Connexion établie, mais pas encore synchronisé
            self.state['synchronized'] = False
        else:
            # Connexion échouée
            self.state['synchronized'] = False
        return success
    
    def disconnect(self):
        """Fermer la connexion au poêle"""
        self.communicator.disconnect()
        self.state['connected'] = False
        self.state['synchronized'] = False
    
    def is_connected(self):
        """Vérifier si le contrôleur est connecté"""
        return self.communicator.is_connected()
    
    def get_state(self):
        """Obtenir l'état complet du poêle"""
        if not self.state['connected']:
            return self.state
        
        # Vérifier si on peut utiliser le cache
        current_time = time.time()
        if current_time - self.last_state_read < self.state_cache_duration:
            logger.debug("Utilisation du cache d'état (lecture récente)")
            return self.state
        
        # Utiliser un sémaphore pour éviter les appels concurrents
        with self.state_lock:
            # Vérifier à nouveau le cache (double-checked locking)
            if current_time - self.last_state_read < self.state_cache_duration:
                logger.debug("Utilisation du cache d'état (après sémaphore)")
                return self.state
            return self._read_state()
    
    def _read_state(self):
        """Lecture interne de l'état (protégée par le sémaphore)"""
        start_time = time.time()
        successful_reads = 0  # Compteur de lectures réussies
        total_reads = 0       # Compteur total de lectures
        try:
            logger.info("Lecture de l'état du poêle...")
            
            # Lire le statut
            logger.debug("Lecture du registre statut...")
            total_reads += 1
            status_frame = self.communicator.send_read_command(REGISTER_STATUS)
            if status_frame:
                status_code, status_name, power_on = parse_status(status_frame.get_data())
                self.state['status'] = status_name
                self.state['power'] = power_on
                successful_reads += 1
                logger.debug(f"Statut lu: {status_name}, Puissance: {'ON' if power_on else 'OFF'}")
            else:
                logger.warning("Échec de lecture du registre statut")
            
            # Lire la température actuelle
            logger.debug("Lecture du registre température...")
            total_reads += 1
            temp_frame = self.communicator.send_read_command(REGISTER_TEMPERATURE)
            if temp_frame:
                temperature = parse_temperature(temp_frame.get_data())
                self.state['temperature'] = temperature
                successful_reads += 1
                logger.debug(f"Température lue: {temperature}°C")
            else:
                logger.warning("Échec de lecture du registre température")
            
            # Lire la température de consigne avec fluide type 0 (granulés)
            logger.debug("Lecture du registre consigne...")
            total_reads += 1
            setpoint_result = self.get_setpoint()
            if setpoint_result:
                setpoint, seco = setpoint_result
                self.state['setpoint'] = setpoint
                self.state['seco'] = seco
                successful_reads += 1
                logger.debug(f"Consigne lue: {setpoint}°C, Seuil: {seco}°C")
            else:
                logger.warning("Échec de lecture du registre consigne")
            
            # Lire le code d'erreur
            logger.debug("Lecture du registre code d'erreur...")
            error_frame = self.communicator.send_read_command(REGISTER_ERROR_CODE)
            if error_frame:
                error_code = error_frame.get_data()[0]
                self.state['error_code'] = error_code
                self.state['error_message'] = ERROR_MAP.get(error_code, f'Erreur inconnue: {error_code}')
                logger.debug(f"Code d'erreur lu: {error_code}")
            else:
                logger.warning("Échec de lecture du registre code d'erreur")
            
            # Lire le niveau de puissance
            logger.debug("Lecture du registre niveau de puissance...")
            power_level_frame = self.communicator.send_read_command(REGISTER_POWER_LEVEL)
            if power_level_frame:
                power_level = power_level_frame.get_data()[0]
                self.state['power_level'] = power_level
                logger.debug(f"Niveau de puissance lu: {power_level}/5")
            else:
                logger.warning("Échec de lecture du registre niveau de puissance")
            
            # Lire le statut des alarmes
            logger.debug("Lecture du registre statut des alarmes...")
            alarm_frame = self.communicator.send_read_command(REGISTER_ALARM_STATUS)
            if alarm_frame:
                alarm_status = alarm_frame.get_data()[0]
                self.state['alarm_status'] = alarm_status
                logger.debug(f"Statut des alarmes lu: {alarm_status}")
            else:
                logger.warning("Échec de lecture du registre statut des alarmes")
            
            # Lire les paramètres du timer
            logger.debug("Lecture du registre paramètres timer...")
            timer_frame = self.communicator.send_read_command(REGISTER_TIMER_SETTINGS)
            if timer_frame:
                timer_settings = timer_frame.get_data()[0]
                self.state['timer_enabled'] = timer_settings == TIMER_ENABLE
                logger.debug(f"Paramètres timer lus: {'Activé' if timer_settings == TIMER_ENABLE else 'Désactivé'}")
            else:
                logger.warning("Échec de lecture du registre paramètres timer")
                
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'état: {e}")
        
        # Calculer le temps de lecture
        end_time = time.time()
        read_duration = end_time - start_time
        
        # Mettre à jour le timestamp de la dernière lecture
        self.last_state_read = time.time()
        
        # Logger l'état complet avec le temps de lecture
        logger.info("=== État du poêle ===")
        logger.info(f"Connexion: {'✓ Connecté' if self.state['connected'] else '✗ Déconnecté'}")
        logger.info(f"Synchronisation: {'✓ Synchronisé' if self.state['synchronized'] else '✗ Non synchronisé'}")
        logger.info(f"Statut: {self.state.get('status', 'N/A')}")
        logger.info(f"Température: {self.state.get('temperature', 'N/A')}°C")
        logger.info(f"Consigne: {self.state.get('setpoint', 'N/A')}°C")
        logger.info(f"Puissance: {'ON' if self.state.get('power', False) else 'OFF'}")
        logger.info(f"Niveau de puissance: {self.state.get('power_level', 'N/A')}/5")
        logger.info(f"Code d'erreur: {self.state.get('error_code', 'N/A')}")
        logger.info(f"Message d'erreur: {self.state.get('error_message', 'N/A')}")
        logger.info(f"Statut alarme: {self.state.get('alarm_status', 'N/A')}")
        logger.info(f"Timer activé: {'Oui' if self.state.get('timer_enabled', False) else 'Non'}")
        logger.info(f"Seuil déclenchement: {self.state.get('seco', 'N/A')}°C")
        logger.info(f"⏱️  Temps de lecture: {read_duration:.3f}s")
        logger.info("==================")
        
        # Déterminer si on est synchronisé basé sur le succès des lectures
        # On considère synchronisé si au moins 2 des 3 lectures principales ont réussi
        if total_reads >= 3 and successful_reads >= 2:
            self.state['synchronized'] = True
            logger.info(f"✅ Synchronisation réussie ({successful_reads}/{total_reads} lectures)")
        else:
            self.state['synchronized'] = False
            logger.warning(f"❌ Synchronisation échouée ({successful_reads}/{total_reads} lectures)")
            
        return self.state
    
    def force_state_refresh(self):
        """Forcer la lecture de l'état (ignorer le cache)"""
        if not self.state['connected']:
            return self.state
        
        with self.state_lock:
            return self._read_state()
    
    def get_setpoint(self):
        """
        Obtenir la consigne de température avec seuil de déclenchement
        Pour granulés (type 0)
        
        Returns:
            tuple: (setpoint, seco) ou None si erreur
            - setpoint: Température de consigne en °C
            - seco: Seuil de déclenchement (trigger) pour arrêt/démarrage automatique
        """
        try:
            # Fluide type 0: lecture de 8 octets à 0x1C32
            frame = self.communicator.send_read_command(REGISTER_SETPOINT_8BYTES)
            if frame and frame.is_valid():
                data = frame.get_data()
                setpoint, seco = parse_setpoint(data)
                
                # Mettre à jour l'état
                self.state['setpoint'] = setpoint
                self.state['seco'] = seco
                
                return setpoint, seco
            
            logger.error("Impossible de lire la consigne")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la consigne: {e}")
            return None
    
    def set_temperature(self, temperature):
        """
        Définir la température de consigne
        
        Args:
            temperature: Température en degrés Celsius
        
        Returns:
            bool: True si succès, False sinon
        """
        if not MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE:
            logger.error(f"Température hors limites: {temperature}°C (plage valide: {MIN_TEMPERATURE}-{MAX_TEMPERATURE}°C)")
            return False
            
        try:
            # Convertir la température en bytes (température * 5 sur 1 octet)
            temp_raw = int(temperature * 5)
            value_bytes = [temp_raw & 0xFF]
            
            # Envoyer la commande d'écriture
            response = self.communicator.send_write_command(REGISTER_SETPOINT, value_bytes)
            if response:
                self.state['setpoint'] = temperature
                # Forcer un refresh de l'état après modification
                self.force_state_refresh()
                logger.info(f"Température de consigne définie à {temperature}°C")
                return True
            else:
                logger.error("Échec de la définition de la température")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la définition de la température: {e}")
            return False
    
    def set_power(self, power_on):
        """
        Allumer ou éteindre le poêle
        
        Args:
            power_on: True pour allumer, False pour éteindre
        
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Utiliser la vraie commande de puissance via le protocole
            power_code = POWER_ON if power_on else POWER_OFF
            value_bytes = [power_code] + [0x00] * 7  # 1 byte de commande + 7 bytes de padding
            
            # Envoyer la commande de puissance
            response = self.communicator.send_write_command(REGISTER_POWER_CONTROL, value_bytes)
            if response:
                self.state['power'] = power_on
                # Forcer un refresh de l'état après modification
                self.force_state_refresh()
                logger.info(f"Commande de puissance envoyée: {'ON' if power_on else 'OFF'}")
                return True
            else:
                logger.error("Échec de la commande de puissance")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du changement d'état: {e}")
            return False
    
    def start_monitoring(self):
        """Démarrer la surveillance en arrière-plan"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Surveillance démarrée")
    
    def stop_monitoring(self):
        """Arrêter la surveillance"""
        if self.running:
            self.running = False
            logger.info("Surveillance arrêtée")
            
            # Attendre que le thread de surveillance se termine
            if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
                if self.monitor_thread.is_alive():
                    logger.warning("Thread de surveillance n'a pas pu s'arrêter proprement")
    
    def _monitor_loop(self):
        """Boucle de surveillance en arrière-plan"""
        while self.running:
            try:
                old_state = self.state.copy()
                self.get_state()
                
                # Émettre les changements via WebSocket si callback défini
                if old_state != self.state and hasattr(self, 'websocket_callback'):
                    self.websocket_callback('state_update', self.state)
                    
            except Exception as e:
                logger.error(f"Erreur dans la boucle de surveillance: {e}")
                
            time.sleep(10)  # Mise à jour toutes les 10 secondes
    
    def set_websocket_callback(self, callback):
        """
        Définir le callback pour les événements WebSocket
        
        Args:
            callback: Fonction qui sera appelée avec (event, data)
        """
        self.websocket_callback = callback
