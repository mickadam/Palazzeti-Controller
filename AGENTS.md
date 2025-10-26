# AGENTS.md - Informations pour les futures tâches

## Contexte du projet
Ce projet est un contrôleur pour poêle à pellets Palazzetti qui communique via protocole série.

## Fonctionnement actuel du poêle
- **État principal** : Le poêle peut être ON ou OFF
- **Sous-états** : Quand ON, il peut être allumé (feu actif) ou éteint (pas de feu)
- **Logique de contrôle automatique** :
  - Le feu s'allume quand la température ambiante < consigne - delta (1,2°C par défaut)
  - Le feu s'éteint quand la température ambiante > consigne + 1,2°C
- **Contrôle manuel** : Seulement via la température de consigne (pas de contrôle on/off direct)

## Modifications récentes (session actuelle)
- **Contrôles on/off supprimés** : Les boutons "Allumer/Éteindre" ont été retirés de l'interface
- **Route API commentée** : `/api/set_power` est temporairement désactivée
- **Surveillance périodique désactivée** : Plus de lecture automatique en arrière-plan
- **Lecture à la demande uniquement** : 
  - À l'ouverture de la page
  - Via le bouton "Rafraîchir" (🔄)
- **Menu de debug supprimé** : Interface simplifiée, plus de mode développement
- **Test de connexion amélioré** : Détection de l'absence de câble avec test de communication
- **Gestion d'erreur de connexion** : Affichage d'erreur spécifique quand le câble est déconnecté
- **Interface accessible sans connexion** : L'interface web démarre même si le poêle n'est pas connecté
- **État de chargement** : Affichage de "--" pour les températures quand déconnecté
- **Gestion d'erreur robuste** : Messages d'erreur clairs en cas de problème de communication
- **Socket.IO supprimé** : Plus de temps réel, interface simplifiée
- **Reconnexion automatique** : Tentative de reconnexion lors du rafraîchissement (F5 ou bouton 🔄)
- **Bouton de test de connexion supprimé** : Seul le bouton de rafraîchissement gère la reconnexion
- **Interface de statut améliorée** : Icônes distinctes pour l'état ON/OFF du poêle et l'état du feu
- **Affichage du slider corrigé** : La valeur du slider se met à jour avec la consigne lue du poêle
- **Vérification de connexion renforcée** : Test de communication avant retour d'état pour éviter les données en cache quand déconnecté
- **Définition de température améliorée** : Logique plus permissive pour éviter les erreurs quand la commande est envoyée avec succès
- **Timeout de test de connexion configurable** : Variable d'environnement `CONNECTION_TEST_TIMEOUT` (défaut: 5s) pour le test de synchronisation
- **Interface mobile améliorée** : Barre de température agrandie, boutons + et - pour incrémenter/décrémenter, valeur de consigne repositionnée au-dessus
- **Affichage du timer** : Icône ⏰ affichée quand `timer_enabled = true` pour indiquer que le timer est activé

## Architecture technique
- **Backend** : Flask (Socket.IO supprimé)
- **Frontend** : HTML/CSS/JavaScript avec interface responsive
- **Communication** : Protocole série avec le poêle Palazzetti
- **Fichiers principaux** :
  - `raspberry_pi/app.py` : Application Flask principale
  - `raspberry_pi/palazzetti_controller.py` : Logique de contrôle du poêle
  - `raspberry_pi/templates/index.html` : Interface utilisateur
  - `raspberry_pi/serial_communicator.py` : Communication série
  - `raspberry_pi/frame.py` : Parsing des trames du protocole

## Configuration
- **Port série** : Configuré dans `config.py` (défaut: `/dev/ttyUSB0`)
- **Température** : Plage 15-27°C, pas de 1°C
- **Delta par défaut** : 1,2°C pour le déclenchement automatique
- **Timeouts** :
  - `TIMEOUT` : Timeout général de communication (défaut: 10s)
  - `CONNECTION_TEST_TIMEOUT` : Timeout pour test de connexion (défaut: 5s)
- **Notifications** :
  - `NOTIFICATIONS_ENABLED` : Activer/désactiver les notifications (défaut: true)
  - `NOTIFICATION_CHECK_INTERVAL` : Intervalle de vérification en minutes (défaut: 30)
  - `SMTP_SERVER` : Serveur SMTP (défaut: smtp.gmail.com)
  - `SMTP_PORT` : Port SMTP (défaut: 587)
  - `SMTP_USERNAME` : Nom d'utilisateur SMTP
  - `SMTP_PASSWORD` : Mot de passe SMTP
  - `FROM_EMAIL` : Email expéditeur
  - `TO_EMAILS` : Emails destinataires (séparés par virgules)
  - `SMTP_USE_TLS` : Utiliser TLS (défaut: true)
- **Variables d'environnement** : Configurées dans le service systemd

## Points d'attention pour les futures tâches
1. **Contrôle on/off** : Actuellement désactivé, à réactiver quand le fonctionnement sera confirmé
2. **Surveillance périodique** : Désactivée, peut être réactivée si nécessaire
3. **Mode développement** : Supprimé, interface simplifiée
4. **Gestion d'erreurs** : Codes d'erreur mappés dans `ERROR_MAP`
5. **Cache d'état** : Durée de 10 secondes pour éviter les lectures trop fréquentes
6. **Test de connexion** : Amélioré pour détecter l'absence de câble
7. **Gestion de déconnexion** : Erreur spécifique affichée quand le câble est déconnecté

## Nouvelles fonctionnalités implémentées
### Gestion du Timer/Chrono
- **Fonctionnalité** : Page de visualisation et paramétrage du timer du poêle
- **Objectif** : Permettre la configuration des heures d'allumage et d'éteignage automatiques
- **Statut** : ✅ Implémenté et fonctionnel
- **Fonctionnalités** :
  - Visualisation des 6 programmes de timer disponibles
  - Affichage des heures de démarrage/arrêt et températures de consigne
  - Programmation par jour de la semaine (7 jours, 3 mémoires par jour)
  - Activation/désactivation du timer via toggle
  - **Timeline de programmation** : Visualisation graphique des créneaux programmés
  - Interface responsive et intuitive
- **API endpoints** :
  - `GET /api/chrono_data` : Récupérer toutes les données du timer
  - `POST /api/chrono_program` : Configurer un programme de timer
  - `POST /api/chrono_day` : Configurer la programmation d'un jour
  - `POST /api/chrono_status` : Activer/désactiver le timer
- **Navigation** : Lien "⏰ Timer" ajouté dans le menu principal
- **Page** : `/timer` - Interface complète de gestion du timer
- **Timeline** : Visualisation graphique des créneaux programmés par jour avec :
  - Sélecteur de jour (Lun-Dim)
  - Timeline 24h avec créneaux colorés par programme
  - Légende des programmes configurés
  - Informations détaillées au survol des créneaux

### Système de Notifications Email Intelligentes
- **Fonctionnalité** : Notifications automatiques par email pour les alertes critiques
- **Objectif** : Alerter l'utilisateur des problèmes sans spam (une seule notification par problème)
- **Statut** : ✅ Implémenté et fonctionnel
- **Fonctionnalités** :
  - **Notifications intelligentes** : Une seule alerte par problème détecté
  - **Notifications de résolution** : Confirmation quand les problèmes sont résolus
  - **Types d'alertes** :
    - 🚨 **Erreurs critiques** : Codes d'erreur E114, E108, E109, E113, E115
    - ⚠️ **Niveau de pellets bas** : Seuil configurable (défaut: 20%)
    - 🔧 **Maintenance requise** : Basé sur la consommation (défaut: 500kg)
    - 🔌 **Perte de connexion** : Détection de déconnexion du poêle
  - **Configuration SMTP** : Support Gmail et autres serveurs SMTP
  - **Cooldowns intelligents** : Évite le spam de notifications
- **Fichiers principaux** :
  - `raspberry_pi/email_notifications.py` : Gestionnaire de notifications email
  - `raspberry_pi/notification_scheduler.py` : Planificateur de surveillance
  - `raspberry_pi/.env` : Configuration SMTP (exemple: `env.example`)
- **API endpoints** :
  - `GET /api/notifications/status` : Statut des notifications
  - `POST /api/notifications/test` : Test d'envoi d'email
  - `GET /api/notifications/config` : Configuration des notifications
- **Logique intelligente** :
  - **Détection** : Email envoyé à la première détection d'un problème
  - **Persistance** : Pas d'email tant que le problème persiste
  - **Résolution** : Email de confirmation quand le problème est résolu
  - **Nouveau problème** : Email envoyé pour un nouveau problème différent

### Suivi de Consommation de Pellets
- **Spécification** : `docs/specification_consommation_pellets.md`
- **Objectif** : Afficher la consommation de pellets en temps réel et historique
- **Statut** : En phase de recherche (identification du registre)
- **Prochaines étapes** :
  1. Identifier l'adresse du registre de consommation dans le protocole Palazzetti
  2. Tester la lecture et valider le format des données
  3. Implémenter l'API backend
  4. Créer le widget d'affichage dans l'interface
  5. Ajouter le système d'historique et de stockage

## Commandes utiles
- **Démarrage** : `python app.py` dans le dossier `raspberry_pi/`
- **Installation service** : Scripts dans `raspberry_pi/service/`
- **Tests** : Scripts de test dans le dossier `tests/`
- **Notifications** :
  - **Test email** : `curl -X POST http://localhost:5000/api/notifications/test`
  - **Statut notifications** : `curl http://localhost:5000/api/notifications/status`
  - **Configuration** : `curl http://localhost:5000/api/notifications/config`
  - **Logs service** : `sudo journalctl -u palazzeti-controller -f`

## Fonctionnement du système de Timer/Chrono

### Structure des données
Le système de timer utilise plusieurs structures de données :

1. **Programmes de timer** (6 programmes disponibles) :
   - Chaque programme contient :
     - Heure de démarrage (0-23)
     - Minute de démarrage (0-59)
     - Heure d'arrêt (0-23)
     - Minute d'arrêt (0-59)
     - Température de consigne pour ce programme

2. **Programmation par jour** (7 jours de la semaine) :
   - Chaque jour peut avoir 3 mémoires (M1, M2, M3)
   - Chaque mémoire référence un programme (0-6, 0 = aucun programme)

3. **Statut du timer** :
   - Bit 0 : Timer activé (1) ou désactivé (0)

### Adresses mémoire
- **0x802D** : Températures de consigne des programmes
- **0x8000-0x8014** : Heures de démarrage/arrêt des programmes (4 bytes par programme)
- **0x8018-0x802A** : Programmation par jour (3 bytes par jour)
- **0x207E** : Statut du timer (activation/désactivation)

### Logique de fonctionnement
1. Le timer peut être activé/désactivé globalement
2. Quand activé, le poêle suit la programmation par jour
3. Chaque jour peut avoir jusqu'à 3 créneaux de fonctionnement
4. Chaque créneau référence un programme avec ses heures et température
5. Le poêle s'allume/éteint automatiquement selon la programmation

## Notes importantes
- Le poêle fonctionne en mode automatique basé sur la température
- L'interface ne permet que de modifier la consigne de température
- La lecture d'état se fait uniquement à la demande (pas de polling automatique)
- Le protocole de communication est documenté dans `docs/protocole_palazzeti.md`
- Le système de timer permet une programmation hebdomadaire complète
