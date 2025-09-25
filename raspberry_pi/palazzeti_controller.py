"""
Contrôleur Palazzetti avec protocole binaire pur
"""
import serial
import time
import threading
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from config import *
from frame import Frame, construct_read_frame, construct_write_frame, parse_temperature, parse_status, parse_setpoint

# Configuration du logging
import os
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
if log_level == 'DEBUG':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
elif log_level == 'WARNING':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
elif log_level == 'ERROR':
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'palazzetti_secret'
socketio = SocketIO(app, cors_allowed_origins="*")


class PalazzettiController:
    """Contrôleur pour le poêle Palazzetti avec protocole binaire"""
    
    def __init__(self, use_mock=False):
        self.use_mock = use_mock
        self.serial_connection = None
        self.lock = threading.Lock()
        self.state_lock = threading.Lock()  # Sémaphore pour get_state()
        self.last_state_read = 0  # Timestamp de la dernière lecture
        self.state_cache_duration = 10  # Durée du cache en secondes
        self.state = {
            'connected': False,
            'status': 'OFF',
            'power': False,
            'temperature': DEFAULT_TEMPERATURE,
            'setpoint': DEFAULT_TEMPERATURE,
            'night_mode': False,
            'error_code': 0,
            'error_message': 'Aucune erreur',
            'fluid_type': 0,      # Type de fluide (fixé à 0 - granulés)
            'seco': 0,            # Seuil de déclenchement (trigger) pour arrêt/démarrage automatique
            'power_level': 0,     # Niveau de puissance (1-5)
            'alarm_status': 0,    # Statut des alarmes
            'timer_enabled': False # Timer activé/désactivé
        }
        self.running = False
        
    def connect(self):
        """Établir la connexion au poêle (mock ou réel)"""
        if self.use_mock:
            self.state['connected'] = True
            logger.info("Mode développement (mock) activé: aucune connexion série requise")
            return True
            
        try:
            self.serial_connection = serial.Serial(
                port=SERIAL_PORT,
                baudrate=BAUD_RATE,
                timeout=TIMEOUT,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,  # 2 stop bits selon documentation
            )
            logger.info(f"Connexion série établie sur {SERIAL_PORT} (38400, 8N2)")
            self.state['connected'] = True
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion série: {e}")
            self.state['connected'] = False
            return False
    
    def disconnect(self):
        """Fermer la connexion série"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                logger.info("Connexion série fermée")
        except Exception as e:
            logger.warning(f"Erreur lors de la fermeture de la connexion série: {e}")
        finally:
            self.state['connected'] = False
    
    def synchro_trame(self, expected_id, timeout=5):
        """
        Attendre une trame avec un ID spécifique (équivalent C# SynchroTrame)
        
        Args:
            expected_id: ID de trame attendu
            timeout: Timeout en secondes (défaut 5s comme C#)
        
        Returns:
            Frame ou None si timeout
        """
        if self.use_mock:
            return self._get_mock_response([0x20, 0x0E])  # Mock response
            
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting >= 11:
                buffer = self.serial_connection.read(11)
                frame = Frame(buffer=buffer)
                if frame.is_valid():
                    #logger.debug(f"Trame reçue: {frame}")
                    if frame.get_id() == expected_id:
                        logger.debug(f"Trame trouvée avec ID 0x{expected_id:02X}")
                        return frame
                    #else:
                        #logger.debug(f"ID reçu 0x{frame.get_id():02X}, attendu 0x{expected_id:02X}")
            # Pas de sleep pour être plus réactif comme le code C#
        
        logger.debug(f"Timeout: aucune trame avec ID 0x{expected_id:02X} reçue")
        return None
    
    
    def send_read_command(self, address):
        """
        Envoyer une commande de lecture pour une adresse donnée
        Implémentation basée sur le code C# ReadRegisterWithID
        """
        if self.use_mock:
            return self._get_mock_response(address)
            
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Connexion série non disponible")
            return None
        
        start_time = time.time()
        with self.lock:
            try:
                # Construire la trame de lecture
                read_frame = construct_read_frame(address)
                expected_id = read_frame.get_id()
                
                # Boucle de retry comme dans le code C# (max 2 tentatives)
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
                logger.error(f"Échec après 2 tentatives (⏱️ {read_duration:.3f}s)")
                return None
                    
            except Exception as e:
                end_time = time.time()
                read_duration = end_time - start_time
                logger.error(f"Erreur lors de l'envoi de commande de lecture: {e} (⏱️ {read_duration:.3f}s)")
                return None
    
    def send_write_command(self, address, value_bytes):
        """Envoyer une commande d'écriture pour une adresse et des données"""
        if self.use_mock:
            return self._get_mock_write_response(address, value_bytes)
            
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
    
    def _get_mock_response(self, address):
        """Simuler une réponse pour le mode développement"""
        if address == REGISTER_STATUS:
            # Simuler un statut BURNING
            mock_data = [STATUS_BURNING] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)  # ID 0x02 pour lecture
        elif address == REGISTER_TEMPERATURE:
            # Simuler une température de 22.5°C
            temp_raw = int(22.5 * 10)  # 225
            mock_data = [(temp_raw >> 8) & 0xFF, temp_raw & 0xFF] + [0x00] * 6
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_SETPOINT:
            # Simuler une consigne de 22°C (format température * 5 sur 1 byte)
            temp_raw = int(22.0 * 5)  # 110
            mock_data = [temp_raw & 0xFF] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_POWER_CONTROL:
            # Simuler un état de puissance ON
            mock_data = [POWER_ON] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_POWER_LEVEL:
            # Simuler un niveau de puissance 3
            mock_data = [3] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_ERROR_CODE:
            # Simuler aucun erreur
            mock_data = [ERROR_NONE] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_ALARM_STATUS:
            # Simuler aucun alarme
            mock_data = [0x00] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_TIMER_SETTINGS:
            # Simuler timer désactivé
            mock_data = [TIMER_DISABLE] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_SETPOINT_8BYTES:
            # Simuler consigne (8 bytes) pour fluide type 0 (granulés)
            # Format: [seco_raw][setpoint_raw][0][beco][0][0][0][0]
            seco_raw = int(1.2 * 10)  # 1.2°C seuil de déclenchement
            setpoint_raw = int(22.0 * 5)  # 22°C consigne
            mock_data = [seco_raw, setpoint_raw, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            return Frame(frame_id=0x02, data=mock_data)
        else:
            return None
    
    def _get_mock_write_response(self, address, value_bytes):
        """Simuler une réponse d'écriture pour le mode développement"""
        # Simuler une réponse de confirmation
        mock_data = [0x01] + [0x00] * 7  # Code de succès
        
        # Si c'est une commande de puissance, mettre à jour l'état simulé
        if address == REGISTER_POWER_CONTROL:
            power_on = value_bytes[0] == POWER_ON
            self.state['power'] = power_on
            logger.info(f"Mock: Commande de puissance simulée: {'ON' if power_on else 'OFF'}")
        
        return Frame(frame_id=0x02, data=mock_data)
    
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
        try:
            logger.info("Lecture de l'état du poêle...")
            
            # Lire le statut
            logger.debug("Lecture du registre statut...")
            status_frame = self.send_read_command(REGISTER_STATUS)
            if status_frame:
                status_code, status_name, power_on = parse_status(status_frame.get_data())
                self.state['status'] = status_name
                self.state['power'] = power_on
                logger.debug(f"Statut lu: {status_name}, Puissance: {'ON' if power_on else 'OFF'}")
            else:
                logger.warning("Échec de lecture du registre statut")
            
            # Lire la température actuelle
            logger.debug("Lecture du registre température...")
            temp_frame = self.send_read_command(REGISTER_TEMPERATURE)
            if temp_frame:
                temperature = parse_temperature(temp_frame.get_data())
                self.state['temperature'] = temperature
                logger.debug(f"Température lue: {temperature}°C")
            else:
                logger.warning("Échec de lecture du registre température")
            
            # Lire la température de consigne avec fluide type 0 (granulés)
            logger.debug("Lecture du registre consigne...")
            setpoint_result = self.get_setpoint(fluid_type=0)
            if setpoint_result:
                setpoint, seco, beco = setpoint_result
                self.state['setpoint'] = setpoint
                self.state['seco'] = seco
                self.state['fluid_type'] = 0
                logger.debug(f"Consigne lue: {setpoint}°C, Seuil: {seco}°C")
            else:
                logger.warning("Échec de lecture du registre consigne")
            
            # Lire le code d'erreur
            logger.debug("Lecture du registre code d'erreur...")
            error_frame = self.send_read_command(REGISTER_ERROR_CODE)
            if error_frame:
                error_code = error_frame.get_data()[0]
                self.state['error_code'] = error_code
                self.state['error_message'] = ERROR_MAP.get(error_code, f'Erreur inconnue: {error_code}')
                logger.debug(f"Code d'erreur lu: {error_code}")
            else:
                logger.warning("Échec de lecture du registre code d'erreur")
            
            # Lire le niveau de puissance
            logger.debug("Lecture du registre niveau de puissance...")
            power_level_frame = self.send_read_command(REGISTER_POWER_LEVEL)
            if power_level_frame:
                power_level = power_level_frame.get_data()[0]
                self.state['power_level'] = power_level
                logger.debug(f"Niveau de puissance lu: {power_level}/5")
            else:
                logger.warning("Échec de lecture du registre niveau de puissance")
            
            # Lire le statut des alarmes
            logger.debug("Lecture du registre statut des alarmes...")
            alarm_frame = self.send_read_command(REGISTER_ALARM_STATUS)
            if alarm_frame:
                alarm_status = alarm_frame.get_data()[0]
                self.state['alarm_status'] = alarm_status
                logger.debug(f"Statut des alarmes lu: {alarm_status}")
            else:
                logger.warning("Échec de lecture du registre statut des alarmes")
            
            # Lire les paramètres du timer
            logger.debug("Lecture du registre paramètres timer...")
            timer_frame = self.send_read_command(REGISTER_TIMER_SETTINGS)
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
        logger.info(f"Type de fluide: {self.state.get('fluid_type', 'N/A')}")
        logger.info(f"⏱️  Temps de lecture: {read_duration:.3f}s")
        logger.info("==================")
            
        return self.state
    
    def force_state_refresh(self):
        """Forcer la lecture de l'état (ignorer le cache)"""
        if not self.state['connected']:
            return self.state
        
        with self.state_lock:
            return self._read_state()
    
    def get_setpoint(self, fluid_type=0):
        """
        Obtenir la consigne de température avec seuil de déclenchement
        Utilise uniquement le fluide type 0 (granulés)
        
        Args:
            fluid_type: Type de fluide (fixé à 0)
        
        Returns:
            tuple: (setpoint, seco, beco) ou None si erreur
            - setpoint: Température de consigne en °C
            - seco: Seuil de déclenchement (trigger) pour arrêt/démarrage automatique
            - beco: Booléen BECO
        """
        try:
            # Fluide type 0: lecture de 8 octets à 0x1C32
            frame = self.send_read_command(REGISTER_SETPOINT_8BYTES)
            if frame and frame.is_valid():
                data = frame.get_data()
                setpoint, seco, beco = parse_setpoint(data, fluid_type)
                
                # Mettre à jour l'état
                self.state['setpoint'] = setpoint
                self.state['seco'] = seco
                self.state['fluid_type'] = fluid_type
                
                #logger.info(f"Consigne  (fluide {fluid_type} - granulés): {setpoint}°C, Seuil déclenchement: {seco}°C")
                return setpoint, seco, beco
            
            logger.error(f"Impossible de lire la consigne pour le fluide {fluid_type}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la consigne Atech: {e}")
            return None
    
    def set_temperature(self, temperature):
        """Définir la température de consigne"""
        if not MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE:
            logger.error(f"Température hors limites: {temperature}°C (plage valide: {MIN_TEMPERATURE}-{MAX_TEMPERATURE}°C)")
            return False
            
        try:
            # Convertir la température en bytes (température * 5 sur 1 octet)
            temp_raw = int(temperature * 5)
            value_bytes = [temp_raw & 0xFF]
            
            # Envoyer la commande d'écriture
            response = self.send_write_command(REGISTER_SETPOINT, value_bytes)
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
        """Allumer ou éteindre le poêle"""
        try:
            # Utiliser la vraie commande de puissance via le protocole
            power_code = POWER_ON if power_on else POWER_OFF
            value_bytes = [power_code] + [0x00] * 7  # 1 byte de commande + 7 bytes de padding
            
            # Envoyer la commande de puissance
            response = self.send_write_command(REGISTER_POWER_CONTROL, value_bytes)
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
                
                # Émettre les changements via WebSocket
                if old_state != self.state:
                    socketio.emit('state_update', self.state)
                    
            except Exception as e:
                logger.error(f"Erreur dans la boucle de surveillance: {e}")
                
            time.sleep(10)  # Mise à jour toutes les 2 secondes


# Instance globale du contrôleur (sera initialisée dans main())
controller = None


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')


@app.route('/api/state')
def api_state():
    """API pour obtenir l'état du poêle"""
    if controller is None:
        return jsonify({'error': 'Contrôleur non initialisé'}), 500
    return jsonify(controller.get_state())


@app.route('/api/set_temperature', methods=['POST'])
def api_set_temperature():
    """API pour définir la température"""
    data = request.get_json()
    temperature = float(data.get('temperature', DEFAULT_TEMPERATURE))
    
    if controller.set_temperature(temperature):
        return jsonify({'success': True, 'message': f'Température définie à {temperature}°C'})
    else:
        return jsonify({'success': False, 'message': 'Erreur lors de la définition de la température'}), 400


@app.route('/api/set_power', methods=['POST'])
def api_set_power():
    """API pour allumer/éteindre le poêle"""
    data = request.get_json()
    power_on = data.get('power', False)
    
    if controller.set_power(power_on):
        return jsonify({'success': True, 'message': f'Poêle {"allumé" if power_on else "éteint"}'})
    else:
        return jsonify({'success': False, 'message': 'Erreur lors du changement d\'état'}), 400


@app.route('/api/dev_mode')
def api_dev_mode():
    """API pour vérifier si on est en mode développement"""
    if controller is None:
        return jsonify({'error': 'Contrôleur non initialisé'}), 500
    return jsonify({
        'dev_mode': controller.use_mock,
        'read_only_mode': True,
        'message': 'Mode lecture seule activé - Écriture désactivée'
    })


@app.route('/api/simulate_state', methods=['POST'])
def api_simulate_state():
    """API pour simuler un état du poêle (mode dev uniquement)"""
    if controller is None:
        return jsonify({'error': 'Contrôleur non initialisé'}), 500
    if not controller.use_mock:
        return jsonify({'success': False, 'message': 'Simulation disponible uniquement en mode développement'}), 403
    
    data = request.get_json()
    status = data.get('status', 'OFF')
    temperature = float(data.get('temperature', 22.0))
    setpoint = float(data.get('setpoint', 22.0))
    power = data.get('power', False)
    
    # Mettre à jour l'état simulé
    controller.state.update({
        'status': status,
        'temperature': temperature,
        'setpoint': setpoint,
        'power': power,
        'connected': True,
        'synchronized': True
    })
    
    # Émettre la mise à jour via WebSocket
    socketio.emit('state_update', controller.state)
    
    return jsonify({
        'success': True, 
        'message': f'État simulé: {status}, {temperature}°C, consigne {setpoint}°C',
        'state': controller.state
    })


@socketio.on('connect')
def handle_connect(auth=None):
    """Gestionnaire de connexion WebSocket"""
    logger.info('Client connecté')
    if controller is not None:
        emit('state_update', controller.get_state())


@socketio.on('disconnect')
def handle_disconnect():
    """Gestionnaire de déconnexion WebSocket"""
    logger.info('Client déconnecté')


def main():
    """Fonction principale"""
    import sys
    import signal
    
    # Créer le contrôleur
    global controller
    controller = None
    
    def signal_handler(signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        logger.info("Signal d'arrêt reçu, fermeture en cours...")
        if controller:
            controller.stop_monitoring()
            controller.disconnect()
        sys.exit(0)
    
    # Enregistrer les gestionnaires de signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Vérifier les arguments de ligne de commande
        use_mock = '--dev' in sys.argv or DEBUG
        
        # Créer le contrôleur
        controller = PalazzettiController(use_mock=use_mock)
        
        # Se connecter
        if not controller.connect():
            logger.error("Impossible de se connecter au poêle")
            return
        
        # Démarrer la surveillance
        controller.start_monitoring()
        
        # Démarrer le serveur web
        logger.info(f"Démarrage du serveur sur {HOST}:{PORT}")
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
        
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
    finally:
        if controller:
            controller.stop_monitoring()
            controller.disconnect()
        logger.info("Application fermée")


if __name__ == '__main__':
    main()

