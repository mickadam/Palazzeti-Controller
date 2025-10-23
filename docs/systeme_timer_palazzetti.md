# Système de Timer/Chrono - Poêle Palazzetti

## Vue d'ensemble

Le système de timer du poêle Palazzetti permet de programmer automatiquement les heures d'allumage et d'éteignage du poêle selon un planning hebdomadaire. Cette fonctionnalité est maintenant entièrement intégrée dans l'interface web du contrôleur.

## Architecture du système

### Structure des données

```
Timer System
├── Statut global (activé/désactivé)
├── 6 Programmes de timer
│   ├── Programme 1: 07:00-09:00 à 22°C
│   ├── Programme 2: 18:00-22:00 à 24°C
│   ├── Programme 3: ...
│   ├── Programme 4: ...
│   ├── Programme 5: ...
│   └── Programme 6: ...
└── Programmation hebdomadaire
    ├── Lundi: M1=1, M2=2, M3=0
    ├── Mardi: M1=1, M2=2, M3=0
    ├── Mercredi: M1=1, M2=2, M3=0
    ├── Jeudi: M1=1, M2=2, M3=0
    ├── Vendredi: M1=1, M2=2, M3=0
    ├── Samedi: M1=3, M2=0, M3=0
    └── Dimanche: M1=3, M2=0, M3=0
```

### Adresses mémoire

| Adresse | Description | Taille |
|---------|-------------|--------|
| 0x802D | Températures de consigne des programmes | 6 bytes |
| 0x8000-0x8014 | Heures de démarrage/arrêt des programmes | 24 bytes (4 par programme) |
| 0x8018-0x802A | Programmation par jour | 21 bytes (3 par jour) |
| 0x207E | Statut du timer (bit 0) | 2 bytes |

## Fonctionnement

### 1. Programmes de timer
- **6 programmes disponibles** (numérotés de 1 à 6)
- Chaque programme définit :
  - Heure de démarrage (0-23)
  - Minute de démarrage (0-59)
  - Heure d'arrêt (0-23)
  - Minute d'arrêt (0-59)
  - Température de consigne

### 2. Programmation hebdomadaire
- **7 jours de la semaine** (Lundi à Dimanche)
- Chaque jour peut avoir **3 mémoires** (M1, M2, M3)
- Chaque mémoire référence un programme (0-6, 0 = aucun programme)

### 3. Logique d'exécution
1. Le timer doit être activé globalement
2. Le poêle vérifie le jour actuel
3. Il lit les mémoires du jour (M1, M2, M3)
4. Pour chaque mémoire non-nulle, il applique le programme correspondant
5. Le poêle s'allume/éteint selon les heures programmées
6. La température de consigne est définie selon le programme actif

## Interface utilisateur

### Page Timer (`/timer`)

#### Statut du Timer
- Toggle pour activer/désactiver le timer
- Affichage de l'état actuel
- Compteur de programmes configurés

#### Programmes de Timer
- Grille de 6 cartes de programmes
- Affichage des heures de démarrage/arrêt
- Température de consigne
- Indicateur visuel (configuré/vide)

#### Programmation par Jour
- 7 cartes pour les jours de la semaine
- Affichage des 3 mémoires (M1, M2, M3)
- Indication des programmes assignés

### Navigation
- Lien "⏰ Timer" dans le menu principal
- Navigation fluide entre les pages

## API Endpoints

### Lecture des données
```http
GET /api/chrono_data
```
Retourne toutes les données du timer :
```json
{
  "success": true,
  "data": {
    "timer_enabled": true,
    "programs": [
      {
        "number": 1,
        "start_hour": 7,
        "start_minute": 0,
        "stop_hour": 9,
        "stop_minute": 0,
        "setpoint": 22.0
      }
    ],
    "days": [
      {
        "day_number": 1,
        "day_name": "Lundi",
        "memory_1": 1,
        "memory_2": 2,
        "memory_3": 0
      }
    ]
  }
}
```

### Configuration d'un programme
```http
POST /api/chrono_program
Content-Type: application/json

{
  "program_number": 1,
  "start_hour": 7,
  "start_minute": 0,
  "stop_hour": 9,
  "stop_minute": 0,
  "setpoint": 22.0
}
```

### Configuration d'un jour
```http
POST /api/chrono_day
Content-Type: application/json

{
  "day_number": 1,
  "memory_1": 1,
  "memory_2": 2,
  "memory_3": 0
}
```

### Activation/désactivation du timer
```http
POST /api/chrono_status
Content-Type: application/json

{
  "enabled": true
}
```

## Exemple d'utilisation

### Configuration typique
1. **Programme 1** : Matin (07:00-09:00) à 22°C
2. **Programme 2** : Soir (18:00-22:00) à 24°C
3. **Programme 3** : Weekend (08:00-23:00) à 23°C

### Programmation hebdomadaire
- **Lundi-Vendredi** : M1=1 (matin), M2=2 (soir), M3=0
- **Samedi-Dimanche** : M1=3 (journée), M2=0, M3=0

### Résultat
- En semaine : Le poêle s'allume le matin à 7h (22°C) et le soir à 18h (24°C)
- Le weekend : Le poêle s'allume à 8h et reste allumé jusqu'à 23h (23°C)

## Avantages

1. **Automatisation complète** : Plus besoin de gérer manuellement l'allumage/éteignage
2. **Économies d'énergie** : Le poêle ne fonctionne que quand nécessaire
3. **Confort** : Température optimale selon les habitudes
4. **Flexibilité** : 6 programmes et 3 créneaux par jour
5. **Interface intuitive** : Configuration facile via l'interface web

## Notes techniques

- Les températures sont stockées avec un facteur de 5 (fluide type 0)
- Les heures sont en format 24h
- Le timer fonctionne indépendamment du contrôle manuel
- La programmation est sauvegardée dans la mémoire du poêle
- L'interface affiche l'état en temps réel
