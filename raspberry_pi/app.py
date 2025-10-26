"""
Application Flask pour le contrôleur Palazzetti
"""
import time
import threading
import logging
from flask import Flask, render_template, request, jsonify
from config import *
from palazzetti_controller import PalazzettiController
from consumption_storage import ConsumptionStorage

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
consumption_storage = None


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')

@app.route('/timer')
def timer():
    """Page de gestion du timer"""
    return render_template('timer.html')

@app.route('/consumption')
def consumption():
    """Page de gestion de la consommation"""
    return render_template('consumption.html')


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
            'timer_enabled': False,
            'fill_level': None,
        }
        return jsonify(default_state)
    
    # Si connecté, tenter de lire l'état (avec test de communication)
    try:
        state = controller.get_state()
        
        # L'état des pellets est maintenant détecté via les codes d'erreur (E101)
        # Plus besoin de lire la consommation de pellets
        
        # Vérifier que l'état contient des données valides (pas de cache)
        if state.get('connected', False) and state.get('synchronized', False):
            # Ajouter le taux de remplissage si disponible
            try:
                consumption = controller.get_pellet_consumption()
                if consumption is not None and consumption_storage:
                    # Mettre à jour le stockage
                    consumption_storage.update_total_consumption(consumption)
                    # Calculer le taux de remplissage
                    fill_data = consumption_storage.get_fill_level(consumption)
                    if fill_data:
                        state['fill_level'] = fill_data
                    else:
                        state['fill_level'] = None
                else:
                    state['fill_level'] = None
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du taux de remplissage: {e}")
                state['fill_level'] = None
            
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
                'timer_enabled': False,
                'pellet_consumption_raw': None,
                'fill_level': None
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
            'timer_enabled': False,
            'fill_level': None
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
                'timer_enabled': False,
                'pellet_consumption_raw': None
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


@app.route('/api/pellet_consumption')
def api_pellet_consumption():
    """API pour obtenir la consommation de pellets"""
    if controller is None:
        return jsonify({'error': 'Contrôleur non initialisé'}), 500
    
    if not controller.is_connected():
        return jsonify({'error': 'Connexion série perdue', 'consumption': None}), 503
    
    try:
        consumption = controller.get_pellet_consumption()
        if consumption is not None:
            # Mettre à jour le stockage
            if consumption_storage:
                consumption_storage.update_total_consumption(consumption)
            
            return jsonify({
                'success': True,
                'consumption': consumption,
                'unit': 'kg',
                'message': 'Consommation de pellets lue avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Impossible de lire la consommation de pellets',
                'consumption': None
            }), 500
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la consommation de pellets: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'consumption': None
        }), 500

@app.route('/api/fill_level')
def api_fill_level():
    """API pour obtenir le taux de remplissage du poêle"""
    if controller is None or consumption_storage is None:
        return jsonify({'error': 'Contrôleur ou stockage non initialisé'}), 500
    
    if not controller.is_connected():
        return jsonify({'error': 'Connexion série perdue'}), 503
    
    try:
        consumption = controller.get_pellet_consumption()
        if consumption is not None:
            fill_data = consumption_storage.get_fill_level(consumption)
            if fill_data:
                return jsonify({
                    'success': True,
                    'fill_level': fill_data['fill_level'],
                    'consumption_since_fill': fill_data['consumption_since_fill'],
                    'capacity': fill_data['capacity'],
                    'last_fill_date': fill_data['last_fill_date'],
                    'current_consumption': consumption
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Aucun remplissage enregistré',
                    'fill_level': None
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Impossible de lire la consommation de pellets'
            }), 500
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du taux de remplissage: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/record_fill', methods=['POST'])
def api_record_fill():
    """API pour enregistrer un remplissage du poêle"""
    if controller is None or consumption_storage is None:
        return jsonify({'error': 'Contrôleur ou stockage non initialisé'}), 500
    
    if not controller.is_connected():
        return jsonify({'error': 'Connexion série perdue'}), 503
    
    try:
        consumption = controller.get_pellet_consumption()
        if consumption is not None:
            consumption_storage.record_fill(consumption)
            return jsonify({
                'success': True,
                'message': 'Remplissage enregistré avec succès',
                'consumption_at_fill': consumption
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Impossible de lire la consommation de pellets'
            }), 500
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du remplissage: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/maintenance_consumption')
def api_maintenance_consumption():
    """API pour obtenir la consommation depuis le dernier reset de maintenance"""
    if controller is None or consumption_storage is None:
        return jsonify({'error': 'Contrôleur ou stockage non initialisé'}), 500
    
    if not controller.is_connected():
        return jsonify({'error': 'Connexion série perdue'}), 503
    
    try:
        consumption = controller.get_pellet_consumption()
        if consumption is not None:
            maintenance_data = consumption_storage.get_maintenance_consumption(consumption)
            if maintenance_data:
                return jsonify({
                    'success': True,
                    'consumption_since_reset': maintenance_data['consumption_since_reset'],
                    'reset_date': maintenance_data['reset_date'],
                    'current_consumption': consumption
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Aucun reset de maintenance enregistré',
                    'consumption_since_reset': None
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Impossible de lire la consommation de pellets'
            }), 500
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la consommation de maintenance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reset_maintenance', methods=['POST'])
def api_reset_maintenance():
    """API pour réinitialiser le compteur de maintenance"""
    if controller is None or consumption_storage is None:
        return jsonify({'error': 'Contrôleur ou stockage non initialisé'}), 500
    
    if not controller.is_connected():
        return jsonify({'error': 'Connexion série perdue'}), 503
    
    try:
        consumption = controller.get_pellet_consumption()
        if consumption is not None:
            consumption_storage.reset_maintenance_counter(consumption)
            return jsonify({
                'success': True,
                'message': 'Compteur de maintenance réinitialisé avec succès',
                'consumption_at_reset': consumption
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Impossible de lire la consommation de pellets'
            }), 500
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation du compteur de maintenance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/consumption_status')
def api_consumption_status():
    """API légère pour vérifier la connexion et obtenir la consommation (optimisée pour la page consommation)"""
    if controller is None or consumption_storage is None:
        return jsonify({
            'connected': False,
            'synchronized': False,
            'error': 'Contrôleur ou stockage non initialisé'
        }), 500
    
    # Vérifier seulement la connexion (pas de lecture complète de l'état)
    if not controller.is_connected():
        return jsonify({
            'connected': False,
            'synchronized': False,
            'error': 'Connexion série perdue'
        }), 503
    
    try:
        # Lire seulement la consommation (plus rapide que l'état complet)
        consumption = controller.get_pellet_consumption()
        if consumption is not None:
            # Mettre à jour le stockage
            consumption_storage.update_total_consumption(consumption)
            
            # Calculer le taux de remplissage
            fill_data = consumption_storage.get_fill_level(consumption)
            
            # Calculer la consommation de maintenance
            maintenance_data = consumption_storage.get_maintenance_consumption(consumption)
            
            return jsonify({
                'connected': True,
                'synchronized': True,
                'total_consumption': consumption,
                'fill_level': fill_data,
                'maintenance_consumption': maintenance_data
            })
        else:
            return jsonify({
                'connected': True,
                'synchronized': False,
                'error': 'Impossible de lire la consommation de pellets'
            }), 500
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la consommation: {e}")
        return jsonify({
            'connected': False,
            'synchronized': False,
            'error': str(e)
        }), 500


@app.route('/api/chrono_data', methods=['GET'])
def api_chrono_data():
    """
    API pour récupérer les données du timer/chrono
    """
    try:
        if not controller.is_connected():
            return jsonify({
                'success': False,
                'error': 'Poêle non connecté'
            }), 500
        
        chrono_data = controller.get_chrono_data()
        if chrono_data is None:
            return jsonify({
                'success': False,
                'error': 'Échec de lecture des données du chrono'
            }), 500
        
        return jsonify({
            'success': True,
            'data': chrono_data
        })
        
    except Exception as e:
        logger.error(f"Erreur API données chrono: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chrono_program', methods=['POST'])
def api_set_chrono_program():
    """
    API pour configurer un programme de timer
    """
    try:
        if not controller.is_connected():
            return jsonify({
                'success': False,
                'error': 'Poêle non connecté'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400
        
        required_fields = ['program_number', 'start_hour', 'start_minute', 'stop_hour', 'stop_minute', 'setpoint']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ manquant: {field}'
                }), 400
        
        success = controller.set_chrono_program(
            data['program_number'],
            data['start_hour'],
            data['start_minute'],
            data['stop_hour'],
            data['stop_minute'],
            data['setpoint']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Échec de la configuration du programme'
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'Programme {data["program_number"]} configuré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur API configuration programme: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chrono_day', methods=['POST'])
def api_set_chrono_day():
    """
    API pour configurer la programmation d'un jour
    """
    try:
        if not controller.is_connected():
            return jsonify({
                'success': False,
                'error': 'Poêle non connecté'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400
        
        required_fields = ['day_number', 'memory_1', 'memory_2', 'memory_3']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ manquant: {field}'
                }), 400
        
        success = controller.set_chrono_day(
            data['day_number'],
            data['memory_1'],
            data['memory_2'],
            data['memory_3']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Échec de la configuration du jour'
            }), 500
        
        day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        day_name = day_names[data['day_number'] - 1]
        
        return jsonify({
            'success': True,
            'message': f'{day_name} configuré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur API configuration jour: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chrono_status', methods=['POST'])
def api_set_chrono_status():
    """
    API pour activer/désactiver le timer
    """
    try:
        if not controller.is_connected():
            return jsonify({
                'success': False,
                'error': 'Poêle non connecté'
            }), 500
        
        data = request.get_json()
        if not data or 'enabled' not in data:
            return jsonify({
                'success': False,
                'error': 'Champ "enabled" manquant'
            }), 400
        
        success = controller.set_chrono_status(data['enabled'])
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Échec de la modification du statut du timer'
            }), 500
        
        status_text = 'activé' if data['enabled'] else 'désactivé'
        return jsonify({
            'success': True,
            'message': f'Timer {status_text} avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur API statut timer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
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
    
    # Créer le contrôleur et le stockage
    global controller, consumption_storage
    controller = None
    consumption_storage = None
    
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
        # Créer le contrôleur et le stockage
        controller = PalazzettiController()
        consumption_storage = ConsumptionStorage()
        
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
