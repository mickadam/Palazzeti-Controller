"""
Application Flask pour le contrôleur Palazzetti
"""
import time
import threading
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from config import *
from palazzetti_controller import PalazzettiController

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
        # Créer le contrôleur
        controller = PalazzettiController()
        
        # Se connecter
        if not controller.connect():
            logger.error("Impossible de se connecter au poêle")
            return
        
        # Configurer le callback WebSocket
        controller.set_websocket_callback(lambda event, data: socketio.emit(event, data))
        
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
