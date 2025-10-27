"""
Système de surveillance périodique pour les notifications du contrôleur Palazzetti
"""
import time
import threading
import logging
from datetime import datetime
from palazzetti_controller import PalazzettiController
from consumption_storage import ConsumptionStorage
from email_notifications import EmailNotificationManager
from config import NOTIFICATION_CONFIG, SMTP_CONFIG

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Planificateur de surveillance pour les notifications"""
    
    def __init__(self):
        self.controller = None
        self.consumption_storage = None
        self.email_notification_manager = None
        self.running = False
        self.scheduler_thread = None
        self.config = NOTIFICATION_CONFIG
        
    def initialize(self, controller, consumption_storage):
        """Initialiser les composants"""
        self.controller = controller
        self.consumption_storage = consumption_storage
        self.email_notification_manager = EmailNotificationManager(SMTP_CONFIG)
        logger.info("Scheduler de notifications email initialisé")
    
    def start(self):
        """Démarrer la surveillance périodique"""
        if self.running:
            logger.warning("Scheduler déjà en cours d'exécution")
            return
        
        if not self.config['enabled']:
            logger.info("Notifications désactivées, scheduler non démarré")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info(f"Scheduler de notifications démarré (intervalle: {self.config['check_interval']} minutes)")
    
    def stop(self):
        """Arrêter la surveillance périodique"""
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler de notifications arrêté")
    
    def _scheduler_loop(self):
        """Boucle principale de surveillance"""
        check_interval_seconds = self.config['check_interval'] * 60  # Convertir en secondes
        
        while self.running:
            try:
                logger.debug("Vérification des conditions d'alerte...")
                self._check_all_conditions()
                
                # Attendre l'intervalle configuré
                time.sleep(check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de surveillance: {e}")
                # En cas d'erreur, attendre un peu avant de réessayer
                time.sleep(60)
    
    def _check_all_conditions(self):
        """Vérifier toutes les conditions d'alerte"""
        if not self.controller or not self.email_notification_manager:
            logger.warning("Composants non initialisés pour la surveillance")
            return
        
        try:
            # Lire l'état du poêle pour les notifications (sans modifier l'état interne)
            state = self.controller.get_state_for_notifications()
            if not state:
                logger.warning("Impossible de lire l'état du poêle pour les notifications")
                return
            
            # Vérifier les conditions d'alerte email
            if self.email_notification_manager:
                self.email_notification_manager.check_all_conditions(state, self._get_consumption_data())
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des conditions: {e}")
    
    def _get_consumption_data(self):
        """Obtenir les données de consommation pour la maintenance"""
        if not self.consumption_storage or not self.controller:
            return None
        
        try:
            consumption = self.controller.get_pellet_consumption()
            if consumption is not None:
                return self.consumption_storage.get_maintenance_consumption(consumption)
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des données de consommation: {e}")
        
        return None
    
    def force_check(self):
        """Forcer une vérification immédiate (pour les tests)"""
        if not self.running:
            logger.warning("Scheduler non démarré, impossible de forcer la vérification")
            return
        
        logger.info("Vérification forcée des conditions d'alerte")
        self._check_all_conditions()
    
    def get_status(self):
        """Obtenir le statut du scheduler"""
        return {
            'running': self.running,
            'enabled': self.config['enabled'],
            'check_interval': self.config['check_interval'],
            'last_check': datetime.now().isoformat() if self.running else None
        }


# Instance globale du scheduler
scheduler = NotificationScheduler()

def start_notification_scheduler(controller, consumption_storage):
    """Démarrer le scheduler de notifications email"""
    scheduler.initialize(controller, consumption_storage)
    scheduler.start()

def stop_notification_scheduler():
    """Arrêter le scheduler de notifications"""
    scheduler.stop()

def get_scheduler_status():
    """Obtenir le statut du scheduler"""
    return scheduler.get_status()

def force_notification_check():
    """Forcer une vérification des notifications"""
    scheduler.force_check()
