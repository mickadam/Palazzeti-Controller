# Changelog - Nettoyage du code

## Version actuelle - Suppression des modes mock/dev

### 🗑️ **Supprimé :**

#### SerialCommunicator (`serial_communicator.py`)
- ❌ Paramètre `use_mock` dans le constructeur
- ❌ Toutes les méthodes mock : `_get_mock_response()`, `_get_mock_write_response()`
- ❌ Logique conditionnelle basée sur `self.use_mock`
- ❌ Messages de log "Mode développement (mock) activé"

#### PalazzettiController (`palazzetti_controller_refactored.py`)
- ❌ Paramètre `use_mock` dans le constructeur
- ❌ Passage du paramètre `use_mock` au SerialCommunicator

#### Application principale (`palazzeti_controller.py`)
- ❌ Routes API `/api/dev_mode` et `/api/simulate_state`
- ❌ Vérification des arguments `--dev` en ligne de commande
- ❌ Logique conditionnelle basée sur `DEBUG` pour le mode mock
- ❌ Références à `controller.use_mock`

#### Configuration (`config.py`)
- ❌ Mode DEBUG activé par défaut (maintenant désactivé par défaut)

### ✅ **Conservé :**

#### Système de logging
- ✅ Configuration des niveaux de log (DEBUG, INFO, WARNING, ERROR)
- ✅ Variable d'environnement `LOG_LEVEL` pour contrôler le niveau
- ✅ Format de log avec timestamp, nom du module, niveau et message
- ✅ Tous les appels `logger.info()`, `logger.debug()`, `logger.error()`, etc.

#### Fonctionnalités principales
- ✅ Communication série réelle avec le poêle
- ✅ Gestion des trames binaires
- ✅ Lecture/écriture des registres
- ✅ Surveillance en arrière-plan
- ✅ API REST et WebSocket
- ✅ Gestion des erreurs et timeouts

### 🎯 **Résultat :**

Le code est maintenant **production-ready** avec :
- Communication série réelle uniquement
- Système de logging complet et configurable
- Code plus simple et maintenable
- Suppression de toute la complexité liée aux modes de développement

### 📝 **Configuration des logs :**

Pour contrôler le niveau de log, utilisez la variable d'environnement :
```bash
export LOG_LEVEL=DEBUG    # Logs détaillés
export LOG_LEVEL=INFO     # Logs informatifs (défaut)
export LOG_LEVEL=WARNING  # Avertissements uniquement
export LOG_LEVEL=ERROR    # Erreurs uniquement
```

---

## Version actuelle - Simplification fluid_type

### 🗑️ **Supprimé :**

#### PalazzettiController (`palazzetti_controller_refactored.py`)
- ❌ Champ `'fluid_type': 0` dans l'état du contrôleur
- ❌ Paramètre `fluid_type=0` dans `get_setpoint()`
- ❌ Assignation `self.state['fluid_type'] = 0`
- ❌ Log "Type de fluide" dans l'affichage de l'état
- ❌ Paramètre `fluid_type` dans les appels à `parse_setpoint()`

#### Frame (`frame.py`)
- ❌ Paramètre `fluid_type=0` dans `parse_setpoint()`
- ❌ Logique conditionnelle basée sur `fluid_type` (types 0, 1, 2)
- ❌ Support des fluides types 1 et 2
- ❌ Lecture de 2 octets pour fluide type 2

### ✅ **Conservé :**

#### Fonctionnalités granulés uniquement
- ✅ Lecture de 8 octets pour granulés (type 0)
- ✅ Conversion en décimal : `seco = seco / 10.0` et `setpoint = setpoint_raw / 5.0`
- ✅ Parsing du seuil de déclenchement (seco)
- ✅ Parsing du booléen BECO
- ✅ Toutes les autres fonctionnalités

### 🎯 **Résultat :**

Le code est maintenant **spécialisé pour les granulés uniquement** avec :
- Code plus simple et plus lisible
- Suppression de la complexité multi-fluides
- Fonction `parse_setpoint()` simplifiée
- Moins de paramètres et de conditions

---

## Version actuelle - Suppression du BECO

### 🗑️ **Supprimé :**

#### Frame (`frame.py`)
- ❌ Variable `beco = data[3] > 0` dans `parse_setpoint()`
- ❌ Retour du tuple `(setpoint, seco, beco)` → maintenant `(setpoint, seco)`
- ❌ Documentation du paramètre `beco` dans la docstring

#### PalazzettiController (`palazzetti_controller_refactored.py`)
- ❌ Déstructuration `setpoint, seco, beco = setpoint_result`
- ❌ Déstructuration `setpoint, seco, beco = parse_setpoint(data)`
- ❌ Retour du tuple `(setpoint, seco, beco)` → maintenant `(setpoint, seco)`
- ❌ Documentation du paramètre `beco` dans la docstring

### ✅ **Conservé :**

#### Fonctionnalités essentielles
- ✅ Lecture du seuil de déclenchement (seco)
- ✅ Lecture de la température de consigne (setpoint)
- ✅ Conversion en décimal pour granulés
- ✅ Toutes les autres fonctionnalités

### 🎯 **Résultat :**

Le code est maintenant **adapté à votre poêle spécifique** avec :
- **Suppression du BECO** (non supporté par votre poêle)
- **Conservation du SECO** (seuil de déclenchement)
- **Code plus simple** avec moins de variables inutiles
- **Meilleure correspondance** avec votre matériel

---

## Version actuelle - Renommage des fichiers

### 🔄 **Renommé :**

#### Structure des fichiers
- ❌ `palazzetti_controller_refactored.py` → ✅ `palazzetti_controller.py`
- ❌ `palazzeti_controller.py` (ancien fichier principal) → ✅ `app.py`

#### Organisation finale
- ✅ **`palazzetti_controller.py`** : Classe `PalazzettiController` avec logique de contrôle
- ✅ **`app.py`** : Application Flask avec routes API et WebSocket
- ✅ **`serial_communicator.py`** : Gestionnaire de communication série
- ✅ **`frame.py`** : Gestion des trames binaires
- ✅ **`config.py`** : Configuration

### 🎯 **Résultat :**

Le code est maintenant **bien organisé** avec :
- **Noms de fichiers clairs** sans "refactored"
- **Séparation claire** entre logique métier et application web
- **Structure modulaire** et maintenable
- **Import simple** : `from palazzetti_controller import PalazzettiController`

---

## Version actuelle - Mise à jour des services

### 🔄 **Mis à jour :**

#### Service systemd (`palazzeti-controller.service`)
- ❌ `ExecStart=.../python palazzeti_controller.py` → ✅ `ExecStart=.../python app.py`

#### Script d'installation (`install.sh`)
- ❌ `cp palazzeti_controller.py $INSTALL_DIR/` → ✅ `cp app.py $INSTALL_DIR/`
- ✅ Ajout de `cp palazzetti_controller.py $INSTALL_DIR/`
- ✅ Ajout de `cp serial_communicator.py $INSTALL_DIR/`

#### Script de désinstallation (`uninstall.sh`)
- ❌ `python palazzeti_controller.py` → ✅ `python app.py`

### 🎯 **Résultat :**

Les services sont maintenant **synchronisés** avec la nouvelle structure :
- **Service systemd** pointe vers le bon fichier principal (`app.py`)
- **Scripts d'installation** copient tous les fichiers nécessaires
- **Documentation** mise à jour pour refléter les changements
- **Installation/désinstallation** fonctionne avec la nouvelle architecture

---

## Version actuelle - Nettoyage des scripts de lancement

### 🗑️ **Supprimé :**

#### Scripts de développement obsolètes
- ❌ `dev.sh` - Script de développement avec mode mock (plus nécessaire)
- ❌ `dev_debug.sh` - Script de développement avec debug (plus nécessaire)

### 🔄 **Mis à jour :**

#### Script de production (`prod.sh`)
- ❌ `python palazzeti_controller.py` → ✅ `python app.py`
- ❌ `LOG_LEVEL=DEBUG` → ✅ `LOG_LEVEL=INFO` (plus approprié pour la production)

### 🎯 **Résultat :**

Les scripts de lancement sont maintenant **simplifiés et cohérents** :
- **Un seul script** : `launch.sh` pour le lancement de l'application
- **Plus de confusion** entre modes dev/prod (un seul mode maintenant)
- **Scripts obsolètes supprimés** (dev.sh, dev_debug.sh)
- **Configuration optimisée** (LOG_LEVEL=INFO)

---

## Version actuelle - Renommage du script de lancement

### 🔄 **Renommé :**

#### Script de lancement
- ❌ `prod.sh` → ✅ `launch.sh`

#### Mise à jour du contenu
- ❌ "Script de production" → ✅ "Script de lancement"
- ❌ "Mode: Production" → ✅ "Mode: Communication série réelle"
- ❌ "Définir DEBUG=False pour forcer le mode production" → ✅ "Configuration de l'environnement"

### 🎯 **Résultat :**

Le script de lancement est maintenant **plus générique et clair** :
- **Nom plus approprié** : `launch.sh` au lieu de `prod.sh`
- **Terminologie simplifiée** : plus de référence au mode "production"
- **Usage universel** : un seul script pour tous les cas d'usage
- **Documentation mise à jour** pour refléter les changements
