# Gestion de la Consommation de Pellets

Ce document décrit les nouvelles fonctionnalités de gestion de la consommation de pellets implémentées dans le contrôleur Palazzetti.

## Fonctionnalités Implémentées

### 1️⃣ Affichage du Taux de Remplissage du Poêle

**Objectif :** Afficher le pourcentage de pellets restants dans le poêle sur la page d'accueil.

**Fonctionnalités :**
- Capacité totale du poêle : 15 kg
- Bouton "Remplissage" pour indiquer que le poêle vient d'être rempli
- Calcul automatique du taux de remplissage : `100 × (1 - (consommation depuis remplissage / 15))`
- Affichage en temps réel avec icônes colorées :
  - 🟢 Vert : > 50% (niveau correct)
  - 🟡 Jaune : 20-50% (niveau moyen)
  - 🔴 Rouge : < 20% (niveau bas)

**Emplacement :** Page d'accueil (section principale du poêle)

### 2️⃣ Compteur de Pellets pour l'Entretien

**Objectif :** Permettre de suivre la consommation depuis le dernier nettoyage du poêle.

**Fonctionnalités :**
- Compteur réinitialisable affichant la quantité totale de pellets consommée depuis le dernier reset
- Interface dédiée sur la page "Consommation"
- Historique des resets avec dates
- Calcul automatique de la consommation depuis le dernier entretien

**Emplacement :** Page "Consommation" (nouvelle page)

## Architecture Technique

### Stockage des Données

Les données sont stockées dans un fichier JSON (`consumption_data.json`) avec la structure suivante :

```json
{
  "last_fill": {
    "timestamp": 1703123456.789,
    "consumption_at_fill": 150.5,
    "date": "2023-12-21T10:30:45.123456"
  },
  "maintenance_counter": {
    "consumption_at_reset": 160.0,
    "reset_timestamp": 1703123456.789,
    "reset_date": "2023-12-21T10:30:45.123456"
  },
  "total_consumption": 200.0,
  "last_updated": "2023-12-21T10:30:45.123456"
}
```

### APIs Disponibles

#### GET `/api/pellet_consumption`
Récupère la consommation totale de pellets depuis le poêle.

**Réponse :**
```json
{
  "success": true,
  "consumption": 200.5,
  "unit": "kg",
  "message": "Consommation de pellets lue avec succès"
}
```

#### GET `/api/fill_level`
Récupère le taux de remplissage du poêle.

**Réponse :**
```json
{
  "success": true,
  "fill_level": 75.2,
  "consumption_since_fill": 3.7,
  "capacity": 15.0,
  "last_fill_date": "2023-12-21T10:30:45.123456",
  "current_consumption": 200.5
}
```

#### POST `/api/record_fill`
Enregistre un remplissage du poêle.

**Réponse :**
```json
{
  "success": true,
  "message": "Remplissage enregistré avec succès",
  "consumption_at_fill": 200.5
}
```

#### GET `/api/maintenance_consumption`
Récupère la consommation depuis le dernier reset de maintenance.

**Réponse :**
```json
{
  "success": true,
  "consumption_since_reset": 25.3,
  "reset_date": "2023-12-21T10:30:45.123456",
  "current_consumption": 200.5
}
```

#### POST `/api/reset_maintenance`
Réinitialise le compteur de maintenance.

**Réponse :**
```json
{
  "success": true,
  "message": "Compteur de maintenance réinitialisé avec succès",
  "consumption_at_reset": 200.5
}
```

## Interface Utilisateur

### Page d'Accueil

**Nouveaux éléments :**
- Affichage du taux de remplissage dans la section de statut
- Bouton "🪵 Remplissage" pour enregistrer un remplissage
- Bouton "📊 Actualiser niveau" pour mettre à jour l'affichage
- Informations détaillées sur la consommation depuis le dernier remplissage

### Page Consommation

**Nouvelle page accessible via le menu "🪵 Consommation" :**
- Affichage de la consommation totale de pellets
- Affichage de la consommation depuis le dernier entretien
- Bouton "🔄 Actualiser" pour mettre à jour les données
- Bouton "🔧 Reset entretien" pour réinitialiser le compteur de maintenance

## Utilisation

### Enregistrer un Remplissage

1. Aller sur la page d'accueil
2. Cliquer sur le bouton "🪵 Remplissage"
3. Le système enregistre automatiquement la consommation actuelle comme point de référence
4. L'affichage du taux de remplissage se met à jour automatiquement

### Réinitialiser le Compteur de Maintenance

1. Aller sur la page "Consommation"
2. Cliquer sur le bouton "🔧 Reset entretien"
3. Confirmer l'action dans la boîte de dialogue
4. Le système enregistre la consommation actuelle comme point de départ pour le prochain entretien

### Suivi du Niveau de Pellets

Le taux de remplissage est calculé automatiquement et affiché en temps réel :
- **Calcul :** `100 × (1 - (consommation depuis remplissage / 15))`
- **Mise à jour :** Automatique lors du rafraîchissement de l'état du poêle
- **Indicateurs visuels :** Icônes colorées selon le niveau

## Fichiers Modifiés

### Nouveaux Fichiers
- `consumption_storage.py` - Gestionnaire de stockage des données de consommation
- `templates/consumption.html` - Page de gestion de la consommation
- `test_consumption.py` - Script de test des fonctionnalités

### Fichiers Modifiés
- `app.py` - Ajout des nouvelles APIs et routes
- `templates/base.html` - Ajout du lien vers la page consommation
- `templates/index.html` - Ajout de l'affichage du taux de remplissage

## Configuration

Aucune configuration supplémentaire n'est requise. Le système utilise :
- Le registre `REGISTER_PELLET_CONSUMPTION` (0x2002) pour lire la consommation
- Un fichier JSON local pour stocker les données de remplissage et maintenance
- Les mêmes paramètres de connexion série que le reste du système

## Tests

Un script de test est disponible pour vérifier le bon fonctionnement :

```bash
cd raspberry_pi
python test_consumption.py
```

Ce script teste :
- Le stockage et la récupération des données
- Le calcul du taux de remplissage
- Le calcul de la consommation de maintenance
- Les différents scénarios d'utilisation

## Notes Importantes

1. **Capacité du poêle :** Fixée à 15 kg (peut être modifiée dans le code si nécessaire)
2. **Précision :** Les calculs sont effectués avec une précision de 1 décimale
3. **Persistance :** Les données sont sauvegardées automatiquement à chaque modification
4. **Sécurité :** Les boutons sont désactivés si le poêle n'est pas connecté
5. **Interface responsive :** Compatible avec les appareils mobiles et tablettes
