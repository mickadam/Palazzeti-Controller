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
- **Variables d'environnement** : Configurées dans le service systemd

## Points d'attention pour les futures tâches
1. **Contrôle on/off** : Actuellement désactivé, à réactiver quand le fonctionnement sera confirmé
2. **Surveillance périodique** : Désactivée, peut être réactivée si nécessaire
3. **Mode développement** : Supprimé, interface simplifiée
4. **Gestion d'erreurs** : Codes d'erreur mappés dans `ERROR_MAP`
5. **Cache d'état** : Durée de 10 secondes pour éviter les lectures trop fréquentes
6. **Test de connexion** : Amélioré pour détecter l'absence de câble
7. **Gestion de déconnexion** : Erreur spécifique affichée quand le câble est déconnecté

## Commandes utiles
- **Démarrage** : `python app.py` dans le dossier `raspberry_pi/`
- **Installation service** : Scripts dans `raspberry_pi/service/`
- **Tests** : Scripts de test dans le dossier `tests/`

## Notes importantes
- Le poêle fonctionne en mode automatique basé sur la température
- L'interface ne permet que de modifier la consigne de température
- La lecture d'état se fait uniquement à la demande (pas de polling automatique)
- Le protocole de communication est documenté dans `docs/protocole_palazzeti.md`
