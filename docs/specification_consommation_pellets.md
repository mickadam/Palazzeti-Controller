# Spécification - Suivi de Consommation de Pellets

## 1. Contexte et Objectifs

### 1.1 Contexte
Le poêle Palazzetti dispose d'un registre permettant de connaître la consommation de pellets. Cette information est précieuse pour :
- Suivre l'efficacité énergétique
- Planifier les achats de pellets
- Analyser les habitudes de chauffage
- Optimiser l'utilisation du poêle

### 1.2 Objectifs
- **Affichage en temps réel** : Consommation actuelle et cumulée
- **Historique** : Suivi de la consommation dans le temps
- **Statistiques** : Moyennes, tendances, coûts
- **Alertes** : Notifications de consommation élevée ou faible stock

## 2. Analyse Technique

### 2.1 Registre de Consommation
- **Adresse** : `0x2002` (identifié dans la librairie officielle Palazzetti)
- **Format** : Word (16 bits) - quantité totale de pellets consommés
- **Fonction** : `iGetPelletQtUsedAtech()` / `getPelletQtUsed()`
- **Variable** : `_PQT` (Pellet Quantity Total)
- **Unité** : ???
- **Affichage** : ??
- **Précision** : ??
- **Source** : Observation dans [WPalaControl](https://github.com/Domochip/WPalaControl)

### 2.2 Données à Collecter
- **Consommation instantanée** : Pellets consommés par heure
- **Consommation cumulée** : Total depuis la dernière remise à zéro
- **Consommation journalière** : Par jour
- **Consommation mensuelle** : Par mois
- **Consommation saisonnière** : Par saison de chauffage

## 3. Spécifications Fonctionnelles

### 3.1 Interface Utilisateur

#### 3.1.1 Affichage Principal
- **Widget de consommation** : Intégré dans l'interface principale
- **Consommation actuelle** : kg/h ou pellets/h
- **Consommation du jour** : kg consommés aujourd'hui
- **Consommation du mois** : kg consommés ce mois

#### 3.1.2 Page Dédiée (Optionnelle)
- **Graphiques** : Évolution de la consommation dans le temps
- **Tableaux** : Historique détaillé
- **Statistiques** : Moyennes, pics, tendances
- **Export** : Données en CSV/JSON

#### 3.1.3 Alertes et Notifications
- **Consommation élevée** : Seuil configurable
- **Stock faible** : Estimation basée sur la consommation
- **Anomalies** : Détection de comportements inhabituels

### 3.2 Fonctionnalités Avancées

#### 3.2.1 Calculs Automatiques
- **Efficacité** : Consommation par degré de chauffage
- **Coûts** : Estimation des coûts basée sur le prix des pellets
- **Prédictions** : Estimation de la consommation future

#### 3.2.2 Configuration
- **Prix des pellets** : Pour le calcul des coûts
- **Capacité du réservoir** : Pour les alertes de stock
- **Seuils d'alerte** : Consommation anormale
- **Période de chauffage** : Saison de chauffage

## 4. Spécifications Techniques

### 4.1 Backend

#### 4.1.1 Nouveaux Registres
```python
# À ajouter dans config.py
REGISTER_PELLET_CONSUMPTION = [0x20, 0x02]  # Registre de consommation de pellets (0x2002)
```

#### 4.1.2 Nouvelles API
```python
# Routes à ajouter dans app.py
@app.route('/api/pellet_consumption')
def api_pellet_consumption():
    """API pour obtenir la consommation de pellets"""
    pass

@app.route('/api/pellet_history')
def api_pellet_history():
    """API pour obtenir l'historique de consommation"""
    pass

@app.route('/api/pellet_statistics')
def api_pellet_statistics():
    """API pour obtenir les statistiques de consommation"""
    pass
```

#### 4.1.3 Stockage des Données
- **Base de données** : SQLite pour l'historique
- **Fréquence de sauvegarde** : Quotidienne ou horaire
- **Rétention** : 1 an d'historique minimum
- **Backup** : Sauvegarde automatique

### 4.2 Frontend

#### 4.2.1 Widget de Consommation
```html
<div class="consumption-widget">
    <h3>Consommation de Pellets</h3>
    <div class="consumption-current">
        <span class="consumption-value" id="currentConsumption">--</span>
        <span class="consumption-unit">kg/h</span>
    </div>
    <div class="consumption-today">
        <span class="consumption-label">Aujourd'hui:</span>
        <span class="consumption-value" id="todayConsumption">--</span>
        <span class="consumption-unit">kg</span>
    </div>
    <div class="consumption-month">
        <span class="consumption-label">Ce mois:</span>
        <span class="consumption-value" id="monthConsumption">--</span>
        <span class="consumption-unit">kg</span>
    </div>
</div>
```

#### 4.2.2 Graphiques (Optionnel)
- **Bibliothèque** : Chart.js ou D3.js
- **Types** : Ligne, barres, aires
- **Périodes** : Jour, semaine, mois, année
- **Interactivité** : Zoom, sélection de période

## 5. Plan de Développement

### 5.1 Phase 1 - Recherche et Analyse
- [x] **Identifier le registre** : Trouver l'adresse du registre de consommation
- [x] **Analyser le format** : Comprendre la structure des données
- [x] **Tester la lecture** : Vérifier la disponibilité et la précision
- [ ] **Documenter le protocole** : Ajouter à la documentation

### 5.2 Phase 2 - Backend de Base
- [x] **Ajouter le registre** : Dans config.py
- [x] **Implémenter la lecture** : Dans palazzetti_controller.py
- [x] **Créer l'API** : Route /api/pellet_consumption
- [x] **Tests unitaires** : Vérifier le bon fonctionnement

### 5.3 Phase 3 - Interface Utilisateur
- [ ] **Widget de base** : Affichage simple dans l'interface principale
- [ ] **Intégration** : Ajouter au layout existant
- [ ] **Styling** : CSS cohérent avec l'interface actuelle
- [ ] **Tests d'interface** : Vérifier l'affichage

### 5.4 Phase 4 - Historique et Statistiques
- [ ] **Base de données** : SQLite pour l'historique
- [ ] **Sauvegarde automatique** : Script de collecte des données
- [ ] **API d'historique** : Routes pour les données historiques
- [ ] **Calculs statistiques** : Moyennes, tendances

### 5.5 Phase 5 - Fonctionnalités Avancées
- [ ] **Graphiques** : Visualisation des données
- [ ] **Alertes** : Notifications de consommation
- [ ] **Configuration** : Paramètres utilisateur
- [ ] **Export** : Fonctionnalité d'export des données

## 6. Questions à Résoudre

### 6.1 Techniques
- ✅ **Adresse du registre** : `0x2002` (identifié)
- ✅ **Format des données** : Word (16 bits) - compteur total
- ✅ **Unité** : **Dixièmes de kg** (× 0.1 = kg)
- ✅ **Affichage** : Format européen avec virgule (13,886 kg)
- ✅ **Précision** : 3 décimales (milligrammes)
- ❓ **Remise à zéro** : Comment et quand le compteur est-il remis à zéro ?

### 6.2 Fonctionnelles
- **Quelle fréquence de lecture est souhaitée ?**
- **Faut-il une page dédiée ou juste un widget ?**
- **Quels calculs sont les plus utiles ?**
- **Faut-il des alertes automatiques ?**

### 6.3 Techniques
- **Base de données locale ou distante ?**
- **Quelle rétention des données ?**
- **Faut-il un système de backup ?**
- **Intégration avec des systèmes externes ?**

## 7. Critères de Succès

### 7.1 Fonctionnels
- ✅ **Lecture fiable** : Données de consommation disponibles
- ✅ **Affichage clair** : Interface intuitive et informative
- ✅ **Historique complet** : Données conservées et accessibles
- ✅ **Calculs précis** : Statistiques et tendances fiables

### 7.2 Techniques
- ✅ **Performance** : Pas d'impact sur les performances existantes
- ✅ **Fiabilité** : Gestion d'erreurs robuste
- ✅ **Maintenabilité** : Code propre et documenté
- ✅ **Évolutivité** : Architecture extensible

## 8. Risques et Mitigation

### 8.1 Risques Techniques
- **Registre non disponible** : Vérifier la disponibilité avant développement
- **Format inconnu** : Analyser en détail avant implémentation
- **Performance** : Surveiller l'impact sur les performances

### 8.2 Risques Fonctionnels
- **Données imprécises** : Valider la qualité des données
- **Interface complexe** : Garder l'interface simple et claire
- **Surcharge d'information** : Éviter l'encombrement de l'interface

---

**Date de création** : 2025-01-19  
**Version** : 1.0  
**Statut** : En attente de validation
