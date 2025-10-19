"""
Application Flask pour le contrôleur Palazzetti
"""
import time
import threading
import logging
from flask import Flask, render_template, request, jsonify
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

# Instance globale du contrôleur (sera initialisée dans main())
controller = None


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')


@app.route('/api/state')
def api_state():
    """API pour obtenir l'état du poêle avec vérification de connexion"""
    if controller is None:
        return jsonify({'error': 'Contrôleur non initialisé'}), 500
    
    # Vérifier d'abord si la connexion est toujours active
    if not controller.is_connected():
        logger.warning("Connexion série perdue - retour d'état par défaut")
        default_state = {
            'connected': False,
            'synchronized': False,
            'status': 'OFF',
            'power': False,
            'temperature': '--',
            'setpoint': '--',
            'night_mode': False,
            'error_code': 0,
            'error_message': 'Connexion série perdue - vérifiez le câble',
            'seco': 0,
            'power_level': 0,
            'alarm_status': 0,
            'timer_enabled': False
        }
        return jsonify(default_state)
    
    # Si connecté, tenter de lire l'état (avec test de communication)
    try:
        state = controller.get_state()
        # Vérifier que l'état contient des données valides (pas de cache)
        if state.get('connected', False) and state.get('synchronized', False):
            logger.info("État lu avec succès depuis le poêle")
            return jsonify(state)
        else:
            logger.warning("État non synchronisé - retour d'état par défaut")
            default_state = {
                'connected': False,
                'synchronized': False,
                'status': 'OFF',
                'power': False,
                'temperature': '--',
                'setpoint': '--',
                'night_mode': False,
                'error_code': 0,
                'error_message': 'Connexion série perdue - vérifiez le câble',
                'seco': 0,
                'power_level': 0,
                'alarm_status': 0,
                'timer_enabled': False
            }
            return jsonify(default_state)
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de l'état: {e}")
        default_state = {
            'connected': False,
            'synchronized': False,
            'status': 'OFF',
            'power': False,
            'temperature': '--',
            'setpoint': '--',
            'night_mode': False,
            'error_code': 0,
            'error_message': f'Erreur de communication: {str(e)}',
            'seco': 0,
            'power_level': 0,
            'alarm_status': 0,
            'timer_enabled': False
        }
        return jsonify(default_state)


@app.route('/api/refresh_state', methods=['POST'])
def api_refresh_state():
    """API pour forcer le rafraîchissement de l'état du poêle avec tentative de reconnexion"""
    if controller is None:
        return jsonify({'error': 'Contrôleur non initialisé'}), 500
    
    # Si le contrôleur n'est pas connecté, tenter de se reconnecter
    if not controller.is_connected():
        logger.info("Tentative de reconnexion automatique...")
        if controller.connect():
            logger.info("Reconnexion automatique réussie")
            # WebSocket supprimé - plus de temps réel
            # Démarrer la surveillance si pas déjà fait
            controller.start_monitoring()
        else:
            logger.warning("Échec de la reconnexion automatique")
            default_state = {
                'connected': False,
                'synchronized': False,
                'status': 'OFF',
                'power': False,
                'temperature': '--',
                'setpoint': '--',
                'night_mode': False,
                'error_code': 0,
                'error_message': 'Connexion série perdue - vérifiez le câble',
                'seco': 0,
                'power_level': 0,
                'alarm_status': 0,
                'timer_enabled': False
            }
            return jsonify({
                'success': False,
                'state': default_state,
                'message': 'Connexion série perdue - vérifiez le câble'
            })
    
    try:
        # Forcer la lecture de l'état (ignorer le cache)
        state = controller.force_state_refresh()
        return jsonify({
            'success': True,
            'state': state,
            'message': 'État rafraîchi avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement de l'état: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du rafraîchissement'
        }), 500


# Route de test de connexion supprimée - le rafraîchissement gère la reconnexion

@app.route('/api/set_temperature', methods=['POST'])
def api_set_temperature():
    """API pour définir la température"""
    if controller is None:
        return jsonify({'success': False, 'message': 'Contrôleur non initialisé'}), 500
    
    data = request.get_json()
    temperature = float(data.get('temperature', DEFAULT_TEMPERATURE))
    
    logger.info(f"Demande de définition de température: {temperature}°C")
    
    try:
        if controller.set_temperature(temperature):
            logger.info(f"Température définie avec succès: {temperature}°C")
            return jsonify({'success': True, 'message': f'Température définie à {temperature}°C'})
        else:
            logger.error(f"Échec de la définition de température: {temperature}°C")
            return jsonify({'success': False, 'message': 'Erreur lors de la définition de la température'}), 400
    except Exception as e:
        logger.error(f"Exception lors de la définition de température: {e}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500


# Route temporairement désactivée - contrôle on/off non utilisé pour l'instant
# @app.route('/api/set_power', methods=['POST'])
# def api_set_power():
#     """API pour allumer/éteindre le poêle"""
#     data = request.get_json()
#     power_on = data.get('power', False)
#     
#     if controller.set_power(power_on):
#         return jsonify({'success': True, 'message': f'Poêle {"allumé" if power_on else "éteint"}'})
#     else:
#         return jsonify({'success': False, 'message': 'Erreur lors du changement d\'état'}), 400


# Gestionnaires WebSocket supprimés - plus de temps réel


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
        
        # Essayer de se connecter (mais ne pas arrêter si ça échoue)
        if controller.connect():
            logger.info("Connexion au poêle établie")
            # Démarrer la surveillance
            controller.start_monitoring()
        else:
            logger.warning("Impossible de se connecter au poêle - interface web disponible en mode déconnecté")
        
        # Démarrer le serveur web (toujours, même sans connexion au poêle)
        logger.info(f"Démarrage du serveur sur {HOST}:{PORT}")
        app.run(host=HOST, port=PORT, debug=DEBUG)
        
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
