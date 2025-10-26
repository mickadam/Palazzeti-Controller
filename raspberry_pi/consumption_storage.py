"""
Gestionnaire de stockage pour les données de consommation de pellets
"""
import json
import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConsumptionStorage:
    """Gestionnaire de stockage pour les données de consommation de pellets"""
    
    def __init__(self, storage_file='consumption_data.json'):
        self.storage_file = storage_file
        self.data = self._load_data()
    
    def _load_data(self):
        """Charger les données depuis le fichier JSON"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Données de consommation chargées depuis {self.storage_file}")
                    return data
            else:
                logger.info(f"Fichier {self.storage_file} n'existe pas, création des données par défaut")
                return self._create_default_data()
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            return self._create_default_data()
    
    def _create_default_data(self):
        """Créer les données par défaut"""
        return {
            'last_fill': {
                'timestamp': None,
                'consumption_at_fill': None,
                'date': None
            },
            'maintenance_counter': {
                'consumption_at_reset': None,
                'reset_timestamp': None,
                'reset_date': None
            },
            'total_consumption': 0,
            'last_updated': None
        }
    
    def _save_data(self):
        """Sauvegarder les données dans le fichier JSON"""
        try:
            self.data['last_updated'] = datetime.now().isoformat()
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Données de consommation sauvegardées dans {self.storage_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des données: {e}")
    
    def update_total_consumption(self, consumption):
        """Mettre à jour la consommation totale"""
        if consumption is not None:
            self.data['total_consumption'] = consumption
            self._save_data()
            logger.info(f"Consommation totale mise à jour: {consumption} kg")
    
    def record_fill(self, consumption_at_fill):
        """Enregistrer un remplissage du poêle"""
        timestamp = time.time()
        date = datetime.now().isoformat()
        
        self.data['last_fill'] = {
            'timestamp': timestamp,
            'consumption_at_fill': consumption_at_fill,
            'date': date
        }
        self._save_data()
        logger.info(f"Remplissage enregistré: {consumption_at_fill} kg le {date}")
    
    def reset_maintenance_counter(self, consumption_at_reset):
        """Réinitialiser le compteur de maintenance"""
        timestamp = time.time()
        date = datetime.now().isoformat()
        
        self.data['maintenance_counter'] = {
            'consumption_at_reset': consumption_at_reset,
            'reset_timestamp': timestamp,
            'reset_date': date
        }
        self._save_data()
        logger.info(f"Compteur de maintenance réinitialisé: {consumption_at_reset} kg le {date}")
    
    def get_fill_level(self, current_consumption):
        """Calculer le taux de remplissage"""
        if not self.data['last_fill']['consumption_at_fill']:
            return None
        
        consumption_since_fill = current_consumption - self.data['last_fill']['consumption_at_fill']
        if consumption_since_fill < 0:
            consumption_since_fill = 0
        
        # Capacité du poêle: 15 kg
        capacity = 15.0
        fill_level = max(0, 100 * (1 - (consumption_since_fill / capacity)))
        
        return {
            'fill_level': round(fill_level, 1),
            'consumption_since_fill': round(consumption_since_fill, 1),
            'capacity': capacity,
            'last_fill_date': self.data['last_fill']['date']
        }
    
    def get_maintenance_consumption(self, current_consumption):
        """Calculer la consommation depuis le dernier reset de maintenance"""
        if not self.data['maintenance_counter']['consumption_at_reset']:
            return None
        
        consumption_since_reset = current_consumption - self.data['maintenance_counter']['consumption_at_reset']
        if consumption_since_reset < 0:
            consumption_since_reset = 0
        
        return {
            'consumption_since_reset': round(consumption_since_reset, 1),
            'reset_date': self.data['maintenance_counter']['reset_date']
        }
    
    def get_all_data(self):
        """Obtenir toutes les données"""
        return self.data.copy()
