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
        self.communication_lock = threading.Lock()  # Sémaphore pour les communications série
        self.last_state_read = 0  # Timestamp de la dernière lecture
        self.state_cache_duration = 10  # Durée du cache en secondes
        self.current_operation = None  # Opération en cours
        self.operation_lock = threading.Lock()  # Lock pour gérer les opérations
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
            'timer_enabled': False, # Timer activé/désactivé
            'chrono_programs': [],  # Programmes de timer (6 programmes)
            'chrono_days': []       # Programmation par jour (7 jours)
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
        # Vérifier d'abord si la connexion série est toujours active
        if not self.communicator.is_connected():
            logger.warning("Connexion série perdue - retour d'état déconnecté")
            self.state['connected'] = False
            self.state['synchronized'] = False
            self.state['error_message'] = 'Connexion série perdue - vérifiez le câble'
            return self.state
        
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
    
    def get_pellet_consumption(self):
        """Obtenir la consommation de pellets"""
        if not self.communicator.is_connected():
            logger.warning("Connexion série perdue - impossible de lire la consommation de pellets")
            return None
        
        try:
            from config import REGISTER_PELLET_CONSUMPTION
            frame = self.communicator.send_read_command(REGISTER_PELLET_CONSUMPTION)
            if frame:
                data = frame.get_data()
                if data and len(data) >= 2:
                    # Le registre 0x2002 contient un word (16 bits)
                    consumption = (data[1] << 8) | data[0]
                    logger.info(f"Consommation de pellets lue: {consumption}")
                    return consumption
                else:
                    logger.warning("Pas de données valides pour la consommation de pellets")
                    return None
            else:
                logger.warning("Pas de réponse valide pour la consommation de pellets")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la consommation de pellets: {e}")
            return None
    
    def _read_state(self):
        """Lecture interne de l'état (protégée par le sémaphore)"""
        def _read_state_internal():
            start_time = time.time()
            successful_reads = 0  # Compteur de lectures réussies
            total_reads = 0       # Compteur total de lectures
            
            # Vérifier d'abord si la connexion est toujours active
            if not self.communicator.is_connected():
                logger.error("Connexion série perdue - câble peut-être déconnecté")
                self.state['connected'] = False
                self.state['synchronized'] = False
                self.state['error_message'] = 'Connexion série perdue - vérifiez le câble'
                return self.state
            
            # Utiliser le sémaphore de communication pour éviter les conflits
            with self.communication_lock:
                try:
                    logger.info("Lecture de l'état du poêle...")
                    
                    # Lire le statut
                    logger.debug("Lecture du registre statut...")
                    total_reads += 1
                    status_code = None  # Initialiser la variable
                    status_frame = self.communicator.send_read_command(REGISTER_STATUS)
                    if status_frame:
                        status_code, status_name, power_on = parse_status(status_frame.get_data())
                        self.state['status'] = status_name
                        self.state['power'] = power_on
                        successful_reads += 1
                        logger.debug(f"Statut lu: {status_name}, Puissance: {'ON' if power_on else 'OFF'}")
                        
                        # Si le statut indique une erreur (codes 241-254), mettre à jour l'erreur
                        if status_code >= 241 and status_code <= 254:
                            self.state['error_code'] = status_code
                            self.state['error_message'] = STATUS_ERROR_MAP.get(status_code, f'Erreur inconnue: {status_code}')
                            logger.info(f"Erreur détectée via statut: {status_code} - {self.state['error_message']}")
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
                
                    # Lire le code d'erreur seulement si aucune erreur n'a été détectée via le statut
                    if not (status_code and status_code >= 241 and status_code <= 254):
                        logger.debug("Lecture du registre code d'erreur...")
                        error_frame = self.communicator.send_read_command(REGISTER_ERROR_CODE)
                        if error_frame:
                            error_code = error_frame.get_data()[0]
                            self.state['error_code'] = error_code
                            # Essayer d'abord le mapping des codes de statut numériques, puis le mapping des codes d'erreur
                            self.state['error_message'] = STATUS_ERROR_MAP.get(error_code, 
                                ERROR_MAP.get(error_code, f'Erreur inconnue: {error_code}'))
                            logger.debug(f"Code d'erreur lu: {error_code} - {self.state['error_message']}")
                        else:
                            logger.warning("Échec de lecture du registre code d'erreur")
                    else:
                        logger.debug("Erreur déjà détectée via le statut, pas besoin de lire le registre d'erreur")
                
                    
                    # Lire le statut des alarmes
                    logger.debug("Lecture du registre statut des alarmes...")
                    alarm_frame = self.communicator.send_read_command(REGISTER_ALARM_STATUS)
                    if alarm_frame:
                        alarm_status = alarm_frame.get_data()[0]
                        self.state['alarm_status'] = alarm_status
                        logger.debug(f"Statut des alarmes lu: {alarm_status}")
                    else:
                        logger.warning("Échec de lecture du registre statut des alarmes")
                    
                    # Lire le statut du timer
                    logger.debug("Lecture du registre statut timer...")
                    timer_frame = self.communicator.send_read_command(REGISTER_CHRONO_STATUS)
                    if timer_frame:
                        timer_status = timer_frame.get_data()[0]
                        self.state['timer_enabled'] = (timer_status & 0x01) == 1
                        logger.debug(f"Statut timer lu: {'Activé' if self.state['timer_enabled'] else 'Désactivé'}")
                    else:
                        logger.warning("Échec de lecture du registre statut timer")
                    
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
        
        # Exécuter l'opération avec gestion des conflits
        return self._execute_operation('read_state', _read_state_internal)
    
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
            # Utiliser le sémaphore de communication pour éviter les conflits
            with self.communication_lock:
                # Convertir la température en bytes (température * 5 sur 1 octet)
                temp_raw = int(temperature * 5)
                value_bytes = [temp_raw & 0xFF]
                
                # Envoyer la commande d'écriture
                response = self.communicator.send_write_command(REGISTER_SETPOINT, value_bytes)
            
            # Mettre à jour l'état local même si la réponse n'est pas parfaite
            # car la commande peut avoir été envoyée avec succès
            self.state['setpoint'] = temperature
            
            if response:
                logger.info(f"Température de consigne définie à {temperature}°C (réponse reçue)")
                # Forcer un refresh de l'état après modification
                self.force_state_refresh()
                return True
            else:
                logger.warning(f"Température de consigne définie à {temperature}°C (pas de réponse confirmée)")
                # Ne pas forcer le refresh si pas de réponse, mais considérer comme succès
                return True
                
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
        """Démarrer la surveillance en arrière-plan - DÉSACTIVÉE pour l'instant"""
        # Surveillance périodique désactivée - lecture uniquement à la demande
        logger.info("Surveillance périodique désactivée - lecture uniquement à la demande")
        return
    
    def stop_monitoring(self):
        """Arrêter la surveillance - DÉSACTIVÉE pour l'instant"""
        # Surveillance périodique désactivée
        logger.info("Surveillance périodique désactivée")
        return
    
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
                
            time.sleep(60)  # Mise à jour toutes les 10 secondes
    
    def set_websocket_callback(self, callback):
        """
        Définir le callback pour les événements WebSocket
        
        Args:
            callback: Fonction qui sera appelée avec (event, data)
        """
        self.websocket_callback = callback
    
    def _execute_operation(self, operation_name, operation_func):
        """
        Exécuter une opération avec gestion des conflits et annulation
        
        Args:
            operation_name: Nom de l'opération (ex: 'read_state', 'chrono_data')
            operation_func: Fonction à exécuter
        
        Returns:
            Résultat de l'opération ou None si annulée
        """
        with self.operation_lock:
            # Vérifier si une autre opération est en cours
            if self.current_operation is not None and self.current_operation != operation_name:
                logger.info(f"Opération {operation_name} en attente - {self.current_operation} en cours")
                # Attendre que l'opération en cours se termine
                while self.current_operation is not None:
                    time.sleep(0.1)
            
            # Marquer cette opération comme en cours
            self.current_operation = operation_name
            logger.debug(f"Début de l'opération {operation_name}")
            
            try:
                # Exécuter l'opération
                result = operation_func()
                return result
            except Exception as e:
                logger.error(f"Erreur dans l'opération {operation_name}: {e}")
                return None
            finally:
                # Libérer l'opération
                self.current_operation = None
                logger.debug(f"Fin de l'opération {operation_name}")
    
    def get_chrono_data(self):
        """
        Récupérer toutes les données du système de timer/chrono
        """
        def _read_chrono_data():
            try:
                if not self.state['connected']:
                    logger.warning("Poêle non connecté, impossible de lire les données du chrono")
                    return None
                
                logger.debug("Lecture des données du chrono...")
                
                # Utiliser le sémaphore de communication pour éviter les conflits
                with self.communication_lock:
                    # Lire les températures de consigne des programmes (0x802D)
                    setpoints_frame = self.communicator.send_read_command(REGISTER_CHRONO_SETPOINTS)
                    if not setpoints_frame:
                        logger.warning("Échec de lecture des températures de consigne des programmes")
                        return None
                
                setpoints_data = setpoints_frame.get_data()
                
                # Lire les programmes de timer (0x8000-0x8014)
                programs = []
                for i in range(6):  # 6 programmes
                    addr = [REGISTER_CHRONO_PROGRAMS[0], REGISTER_CHRONO_PROGRAMS[1] + i * 4]
                    program_frame = self.communicator.send_read_command(addr)
                    if not program_frame:
                        logger.warning(f"Échec de lecture du programme {i+1}")
                        return None
                    
                    program_data = program_frame.get_data()
                    program = {
                        'number': i + 1,
                        'start_hour': program_data[0],
                        'start_minute': program_data[1],
                        'stop_hour': program_data[2],
                        'stop_minute': program_data[3],
                        'setpoint': setpoints_data[i] / 5.0 if setpoints_data[i] > 0 else 0  # Conversion pour fluide type 0
                    }
                    programs.append(program)
                
                # Lire la programmation par jour (0x8018-0x802A)
                days = []
                for i in range(7):  # 7 jours
                    addr = [REGISTER_CHRONO_DAYS[0], REGISTER_CHRONO_DAYS[1] + i * 3]
                    day_frame = self.communicator.send_read_command(addr)
                    if not day_frame:
                        logger.warning(f"Échec de lecture du jour {i+1}")
                        return None
                    
                    day_data = day_frame.get_data()
                    day = {
                        'day_number': i + 1,
                        'day_name': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][i],
                        'memory_1': day_data[0],
                        'memory_2': day_data[1],
                        'memory_3': day_data[2]
                    }
                    days.append(day)
                
                # Lire le statut du timer (0x207E)
                status_frame = self.communicator.send_read_command(REGISTER_CHRONO_STATUS)
                if not status_frame:
                    logger.warning("Échec de lecture du statut du timer")
                    return None
                
                status_data = status_frame.get_data()
                timer_enabled = (status_data[0] & 0x01) == 1
                
                chrono_data = {
                    'timer_enabled': timer_enabled,
                    'programs': programs,
                    'days': days
                }
                
                # Mettre à jour l'état
                self.state['chrono_programs'] = programs
                self.state['chrono_days'] = days
                self.state['timer_enabled'] = timer_enabled
                
                logger.info(f"Données du chrono lues: Timer {'activé' if timer_enabled else 'désactivé'}")
                return chrono_data
            
            except Exception as e:
                logger.error(f"Erreur lors de la lecture des données du chrono: {e}")
                return None
        
        # Exécuter l'opération avec gestion des conflits
        return self._execute_operation('chrono_data', _read_chrono_data)
    
    def set_chrono_program(self, program_number, start_hour, start_minute, stop_hour, stop_minute, setpoint):
        """
        Configurer un programme de timer
        """
        try:
            if not self.state['connected']:
                logger.warning("Poêle non connecté, impossible de configurer le programme")
                return False
            
            if not (1 <= program_number <= 6):
                logger.error(f"Numéro de programme invalide: {program_number} (doit être entre 1 et 6)")
                return False
            
            if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59):
                logger.error(f"Heure de démarrage invalide: {start_hour:02d}:{start_minute:02d}")
                return False
            
            if not (0 <= stop_hour <= 23 and 0 <= stop_minute <= 59):
                logger.error(f"Heure d'arrêt invalide: {stop_hour:02d}:{stop_minute:02d}")
                return False
            
            if not (MIN_TEMPERATURE <= setpoint <= MAX_TEMPERATURE):
                logger.error(f"Température de consigne invalide: {setpoint}°C")
                return False
            
            logger.info(f"Configuration du programme {program_number}: {start_hour:02d}:{start_minute:02d} - {stop_hour:02d}:{stop_minute:02d} à {setpoint}°C")
            
            # Calculer l'adresse du programme (0x8000 + (program_number-1) * 4)
            program_addr = [REGISTER_CHRONO_PROGRAMS[0], REGISTER_CHRONO_PROGRAMS[1] + (program_number - 1) * 4]
            
            # Écrire les heures de démarrage/arrêt
            program_data = [start_hour, start_minute, stop_hour, stop_minute]
            result = self.communicator.send_write_command(program_addr, program_data)
            if not result:
                logger.error(f"Échec de l'écriture du programme {program_number}")
                return False
            
            # Écrire la température de consigne (0x802D + program_number - 1)
            setpoint_addr = [REGISTER_CHRONO_SETPOINTS[0], REGISTER_CHRONO_SETPOINTS[1] + program_number - 1]
            setpoint_value = int(setpoint * 5)  # Conversion pour fluide type 0
            result = self.communicator.send_write_command(setpoint_addr, [setpoint_value])
            if not result:
                logger.error(f"Échec de l'écriture de la température de consigne du programme {program_number}")
                return False
            
            logger.info(f"Programme {program_number} configuré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du programme {program_number}: {e}")
            return False
    
    def set_chrono_day(self, day_number, memory_1, memory_2, memory_3):
        """
        Configurer la programmation d'un jour
        """
        try:
            if not self.state['connected']:
                logger.warning("Poêle non connecté, impossible de configurer le jour")
                return False
            
            if not (1 <= day_number <= 7):
                logger.error(f"Numéro de jour invalide: {day_number} (doit être entre 1 et 7)")
                return False
            
            for memory in [memory_1, memory_2, memory_3]:
                if not (0 <= memory <= 6):
                    logger.error(f"Numéro de mémoire invalide: {memory} (doit être entre 0 et 6)")
                    return False
            
            day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            logger.info(f"Configuration du {day_names[day_number-1]}: M1={memory_1}, M2={memory_2}, M3={memory_3}")
            
            # Calculer l'adresse du jour (0x8018 + (day_number-1) * 3)
            day_addr = [REGISTER_CHRONO_DAYS[0], REGISTER_CHRONO_DAYS[1] + (day_number - 1) * 3]
            
            # Écrire les mémoires
            day_data = [memory_1, memory_2, memory_3]
            result = self.communicator.send_write_command(day_addr, day_data)
            if not result:
                logger.error(f"Échec de l'écriture du jour {day_number}")
                return False
            
            logger.info(f"{day_names[day_number-1]} configuré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du jour {day_number}: {e}")
            return False
    
    def set_chrono_status(self, enabled):
        """
        Activer ou désactiver le timer
        """
        try:
            if not self.state['connected']:
                logger.warning("Poêle non connecté, impossible de modifier le statut du timer")
                return False
            
            logger.info(f"{'Activation' if enabled else 'Désactivation'} du timer")
            
            # Lire le statut actuel
            status_frame = self.communicator.send_read_command(REGISTER_CHRONO_STATUS)
            if not status_frame:
                logger.error("Échec de lecture du statut du timer")
                return False
            
            status_data = status_frame.get_data()
            current_status = status_data[0]
            
            # Modifier le bit 0
            if enabled:
                new_status = current_status | 0x01
            else:
                new_status = current_status & 0xFE
            
            # Écrire le nouveau statut
            result = self.communicator.send_write_command(REGISTER_CHRONO_STATUS, [new_status])
            if not result:
                logger.error("Échec de l'écriture du statut du timer")
                return False
            
            # Mettre à jour l'état
            self.state['timer_enabled'] = enabled
            
            logger.info(f"Timer {'activé' if enabled else 'désactivé'} avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification du statut du timer: {e}")
            return False
