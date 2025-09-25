# Testeur de Registres Palazzetti

Ce CLI permet de tester individuellement la lecture et l'écriture de tous les registres du poêle Palazzetti pour valider leur fonctionnement.

## Fonctionnalités

- **Lecture de registres** : Test de la lecture de tous les registres disponibles
- **Écriture de registres** : Test de l'écriture dans les registres modifiables
- **Validation des données** : Vérification de la cohérence et de la validité des valeurs
- **Mode interactif** : Interface en ligne de commande pour tester manuellement
- **Mode batch** : Exécution de commandes spécifiques via arguments
- **Mode mock** : Test sans connexion physique au poêle

## Registres supportés

| Nom | Adresse | R/W | Description |
|-----|---------|-----|-------------|
| status | 0x20 0x1C | R | Statut du poêle (OFF, BURNING, COOLING, etc.) |
| temperature | 0x20 0x0E | R | Température actuelle en °C |
| setpoint | 0x20 0x0F | R/W | Température de consigne (15-27°C) |
| power_control | 0x20 0x1D | R/W | Contrôle ON/OFF du poêle |
| power_level | 0x20 0x2A | R/W | Niveau de puissance (1-5) |
| start_control | 0x20 0x44 | R/W | Contrôle de démarrage |
| error_code | 0x20 0x1E | R | Code d'erreur actuel |
| alarm_status | 0x20 0x1F | R | Statut des alarmes |
| timer_settings | 0x20 0x72 | R/W | Paramètres du timer |

## Utilisation

### Mode interactif (recommandé)

```bash
# Mode interactif avec connexion réelle
python3 register_tester.py --interactive

# Mode interactif avec simulation (développement)
python3 register_tester.py --mock --interactive
```

### Commandes en ligne

```bash
# Lister tous les registres
python3 register_tester.py --list

# Lire un registre spécifique
python3 register_tester.py --read status
python3 register_tester.py --read temperature

# Écrire dans un registre
python3 register_tester.py --write setpoint 24.0
python3 register_tester.py --write power_control 1

# Tester tous les registres
python3 register_tester.py --test

# Afficher l'état complet
python3 register_tester.py --state
```

### Commandes interactives

Une fois en mode interactif, vous pouvez utiliser :

- `list` - Lister tous les registres
- `read <nom>` - Lire un registre spécifique
- `write <nom> <valeur>` - Écrire dans un registre
- `test` - Tester tous les registres
- `state` - Afficher l'état complet
- `help` - Afficher l'aide
- `quit` - Quitter

## Exemples d'utilisation

### Test de base

```bash
# Démarrer en mode interactif
python3 register_tester.py --interactive

# Dans le CLI interactif :
> list
> read status
> read temperature
> read setpoint
> test
> quit
```

### Test d'écriture

```bash
# Modifier la température de consigne
python3 register_tester.py --write setpoint 25.0

# Allumer le poêle
python3 register_tester.py --write power_control 1

# Vérifier l'état
python3 register_tester.py --state
```

### Test complet

```bash
# Tester tous les registres en une fois
python3 register_tester.py --test
```

## Démonstration

Un script de démonstration est disponible :

```bash
python3 demo_registers.py
```

Ce script montre :
- L'utilisation de base du CLI
- Les opérations de lecture/écriture
- La validation des données
- Les cas d'erreur

## Configuration

Le testeur utilise la même configuration que le contrôleur principal :

- **Port série** : `/dev/ttyUSB0` (configurable via `SERIAL_PORT`)
- **Vitesse** : 38400 bauds
- **Configuration** : 8N2 (8 bits, pas de parité, 2 stop bits)
- **Timeout** : 5 secondes

## Validation des données

Le testeur inclut des validateurs pour s'assurer de la cohérence des données :

- **Température** : Entre 15°C et 27°C
- **Niveau de puissance** : Entre 1 et 5
- **Contrôle de puissance** : 0 (OFF) ou 1 (ON)
- **Paramètres timer** : 0 (Disable) ou 1 (Enable)

## Dépannage

### Problèmes de connexion

1. Vérifiez que le poêle est allumé
2. Vérifiez la connexion du câble RJ11
3. Vérifiez que le port série est correct (`/dev/ttyUSB0`)
4. Testez avec le mode mock : `--mock`

### Problèmes de communication

1. Vérifiez que le poêle envoie des trames de synchronisation
2. Utilisez `--test` pour diagnostiquer les registres problématiques
3. Vérifiez les logs pour plus de détails

### Valeurs incohérentes

1. Vérifiez que les registres correspondent à la documentation Palazzetti
2. Testez la lecture plusieurs fois pour vérifier la stabilité
3. Comparez avec les valeurs affichées sur le poêle

## Intégration

Ce testeur peut être intégré dans des scripts de test automatisés :

```python
from register_tester import RegisterTester

# Créer le testeur
tester = RegisterTester(use_mock=False)

# Se connecter
if tester.connect():
    # Tester tous les registres
    success = tester.test_all_registers()
    
    if success:
        print("Tous les tests sont passés")
    else:
        print("Certains tests ont échoué")
    
    tester.disconnect()
```

## Sécurité

⚠️ **Attention** : L'écriture dans certains registres peut affecter le fonctionnement du poêle. Testez d'abord en mode mock ou avec des valeurs sûres.

- Ne modifiez pas les registres de statut ou d'erreur
- Testez les modifications de température avec des valeurs raisonnables
- Vérifiez toujours l'état du poêle après une modification
