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
from frame import Frame, construct_read_frame, construct_write_frame, parse_temperature, parse_status

# Configuration du logging
logging.basicConfig(level=logging.INFO)
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
        self.state = {
            'connected': False,
            'status': 'OFF',
            'power': False,
            'temperature': DEFAULT_TEMPERATURE,
            'setpoint': DEFAULT_TEMPERATURE,
            'night_mode': False
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
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            logger.info("Connexion série fermée")
        self.state['connected'] = False
    
    def wait_for_sync_frame(self, timeout=5):
        """Attendre la trame de synchronisation (0x00)"""
        if self.use_mock:
            return True
            
        if not self.serial_connection or not self.serial_connection.is_open:
            return False
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting >= 11:
                buffer = self.serial_connection.read(11)
                frame = Frame(buffer=buffer)
                if frame.get_id() == 0x00:
                    logger.debug("Trame de synchronisation reçue")
                    return True
        return False
    
    def wait_for_frame_by_id(self, expected_id, timeout=5):
        """Attendre une trame avec un ID spécifique"""
        if self.use_mock:
            return None
            
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting >= 11:
                buffer = self.serial_connection.read(11)
                frame = Frame(buffer=buffer)
                if frame.get_id() == expected_id and frame.is_valid():
                    return frame
        return None
    
    def send_read_command(self, address):
        """Envoyer une commande de lecture pour une adresse donnée"""
        if self.use_mock:
            return self._get_mock_response(address)
            
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Connexion série non disponible")
            return None
            
        with self.lock:
            try:
                # Attendre la trame de synchronisation
                if not self.wait_for_sync_frame():
                    logger.error("Pas de trame de synchronisation")
                    return None
                
                # Construire et envoyer la trame de lecture
                read_frame = construct_read_frame(address)
                logger.debug(f"Envoi trame de lecture: {read_frame}")
                
                self.serial_connection.write(read_frame.as_bytes())
                self.serial_connection.flush()
                
                # Attendre la réponse
                response_frame = self.wait_for_frame_by_id(read_frame.get_id())
                if response_frame and response_frame.is_valid():
                    logger.debug(f"Réponse reçue: {response_frame}")
                    return response_frame
                else:
                    logger.error("Réponse invalide ou timeout")
                    return None
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de commande de lecture: {e}")
                return None
    
    def send_write_command(self, address, value_bytes):
        """Envoyer une commande d'écriture pour une adresse et des données"""
        if self.use_mock:
            return self._get_mock_write_response(address, value_bytes)
            
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Connexion série non disponible")
            return None
            
        with self.lock:
            try:
                # Attendre la trame de synchronisation
                if not self.wait_for_sync_frame():
                    logger.error("Pas de trame de synchronisation")
                    return None
                
                # Construire et envoyer la trame d'écriture
                write_frame = construct_write_frame(address, value_bytes)
                logger.debug(f"Envoi trame d'écriture: {write_frame}")
                
                self.serial_connection.write(write_frame.as_bytes())
                self.serial_connection.flush()
                
                # Attendre la réponse
                response_frame = self.wait_for_frame_by_id(write_frame.get_id())
                if response_frame and response_frame.is_valid():
                    logger.debug(f"Réponse reçue: {response_frame}")
                    return response_frame
                else:
                    logger.error("Réponse invalide ou timeout")
                    return None
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de commande d'écriture: {e}")
                return None
    
    def _get_mock_response(self, address):
        """Simuler une réponse pour le mode développement"""
        if address == REGISTER_STATUS:
            # Simuler un statut BURNING
            mock_data = [STATUS_BURNING] + [0x00] * 7
            return Frame(frame_id=0x01, data=mock_data)
        elif address == REGISTER_TEMPERATURE:
            # Simuler une température de 22.5°C
            temp_raw = int(22.5 * 10)  # 225
            mock_data = [(temp_raw >> 8) & 0xFF, temp_raw & 0xFF] + [0x00] * 6
            return Frame(frame_id=0x01, data=mock_data)
        elif address == REGISTER_SETPOINT:
            # Simuler une consigne de 22°C
            temp_raw = int(22.0 * 10)  # 220
            mock_data = [(temp_raw >> 8) & 0xFF, temp_raw & 0xFF] + [0x00] * 6
            return Frame(frame_id=0x01, data=mock_data)
        else:
            return None
    
    def _get_mock_write_response(self, address, value_bytes):
        """Simuler une réponse d'écriture pour le mode développement"""
        # Simuler une réponse de confirmation
        mock_data = [0x01] + [0x00] * 7  # Code de succès
        return Frame(frame_id=0x02, data=mock_data)
    
    def get_state(self):
        """Obtenir l'état complet du poêle"""
        if not self.state['connected']:
            return self.state
            
        try:
            # Lire le statut
            status_frame = self.send_read_command(REGISTER_STATUS)
            if status_frame:
                status_code, status_name, power_on = parse_status(status_frame.get_data())
                self.state['status'] = status_name
                self.state['power'] = power_on
            
            # Lire la température actuelle
            temp_frame = self.send_read_command(REGISTER_TEMPERATURE)
            if temp_frame:
                temperature = parse_temperature(temp_frame.get_data())
                self.state['temperature'] = temperature
            
            # Lire la température de consigne
            setpoint_frame = self.send_read_command(REGISTER_SETPOINT)
            if setpoint_frame:
                setpoint = parse_temperature(setpoint_frame.get_data())
                self.state['setpoint'] = setpoint
                
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'état: {e}")
            
        return self.state
    
    def set_temperature(self, temperature):
        """Définir la température de consigne"""
        if not MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE:
            logger.error(f"Température hors limites: {temperature}")
            return False
            
        try:
            # Convertir la température en bytes
            temp_raw = int(temperature * 10)
            value_bytes = [(temp_raw >> 8) & 0xFF, temp_raw & 0xFF]
            
            # Envoyer la commande d'écriture
            response = self.send_write_command(REGISTER_SETPOINT, value_bytes)
            if response:
                self.state['setpoint'] = temperature
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
            # Pour l'instant, on simule avec la température
            # TODO: Implémenter la vraie commande on/off selon le protocole
            if power_on:
                # Allumer = définir une température de consigne
                if self.state['setpoint'] < MIN_TEMPERATURE:
                    self.set_temperature(MIN_TEMPERATURE)
            else:
                # Éteindre = définir une température très basse
                self.set_temperature(MIN_TEMPERATURE - 1)
                
            self.state['power'] = power_on
            logger.info(f"Poêle {'allumé' if power_on else 'éteint'}")
            return True
            
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
        self.running = False
        logger.info("Surveillance arrêtée")
    
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
                
            time.sleep(2)  # Mise à jour toutes les 2 secondes


# Instance globale du contrôleur
controller = PalazzettiController(use_mock=DEBUG)


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')


@app.route('/api/state')
def api_state():
    """API pour obtenir l'état du poêle"""
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


@socketio.on('connect')
def handle_connect():
    """Gestionnaire de connexion WebSocket"""
    logger.info('Client connecté')
    emit('state_update', controller.get_state())


@socketio.on('disconnect')
def handle_disconnect():
    """Gestionnaire de déconnexion WebSocket"""
    logger.info('Client déconnecté')


def main():
    """Fonction principale"""
    import sys
    
    # Vérifier les arguments de ligne de commande
    use_mock = '--dev' in sys.argv or DEBUG
    
    # Créer le contrôleur
    global controller
    controller = PalazzettiController(use_mock=use_mock)
    
    # Se connecter
    if not controller.connect():
        logger.error("Impossible de se connecter au poêle")
        return
    
    try:
        # Démarrer la surveillance
        controller.start_monitoring()
        
        # Démarrer le serveur web
        logger.info(f"Démarrage du serveur sur {HOST}:{PORT}")
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG)
        
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    finally:
        controller.stop_monitoring()
        controller.disconnect()


if __name__ == '__main__':
    main()

