# Script de Recherche de Registres Palazzetti

Ce script permet de lire et rechercher des valeurs dans les registres du poêle Palazzetti de manière flexible.

## Fonctionnalités

- **Lecture de plage** : Lire tous les registres dans une plage d'adresses
- **Recherche de valeur** : Rechercher une valeur spécifique dans une plage
- **Support 1 ou 2 octets** : Lire les données sur 1 ou 2 octets
- **Mode mock** : Test sans connexion physique au poêle
- **Correspondance exacte ou partielle** : Options de recherche avancées

## Utilisation

### Syntaxe de base

```bash
python3 register_search.py --start <adresse_début> --end <adresse_fin> [options]
```

### Paramètres obligatoires

- `--start` : Adresse de début (hexadécimal, ex: `1C00`)
- `--end` : Adresse de fin (hexadécimal, ex: `207C`)

### Paramètres optionnels

- `--search <valeur>` : Valeur à rechercher (hex ou décimal)
- `--bytes <1|2>` : Nombre d'octets à lire (défaut: 2)
- `--mock` : Mode développement (simulation)
- `--exact` : Correspondance exacte (défaut)
- `--partial` : Correspondance partielle
- `--show-all` : Afficher tous les résultats

## Exemples d'utilisation

### 1. Lecture d'une plage de registres

```bash
# Lire la plage 1C00-207C avec 2 octets
python3 register_search.py --start 1C00 --end 207C --bytes 2

# Lire une petite plage pour test
python3 register_search.py --start 1C00 --end 1C0F --bytes 2 --mock
```

### 2. Recherche de valeur

```bash
# Rechercher la valeur 22 dans la plage 1C00-1CFF avec 1 octet
python3 register_search.py --start 1C00 --end 1CFF --search 22 --bytes 1

# Rechercher la valeur hexadécimale 0x1234
python3 register_search.py --start 2000 --end 207C --search 0x1234 --bytes 2

# Recherche avec correspondance partielle
python3 register_search.py --start 1C00 --end 1CFF --search 0x12 --bytes 1 --partial
```

### 3. Mode développement

```bash
# Tous les exemples avec --mock pour éviter la connexion réelle
python3 register_search.py --start 1C00 --end 1C0F --mock
```

## Format des données

### Lecture sur 1 octet
- **Données brutes** : `data[2]` (après l'adresse)
- **Valeur** : Entier 8 bits (0-255)

### Lecture sur 2 octets
- **Données brutes** : `data[2]` (poids faible) + `data[3]` (poids fort)
- **Valeur** : Entier 16 bits (0-65535)
- **Format** : Little-endian (poids faible en premier)

## Exemples de sortie

### Lecture de plage
```
Lecture des registres de 0x1C00 à 0x1C0F
Octets par registre: 2
Total: 16 registres
------------------------------------------------------------
Progression: 16/16 (100.0%)

================================================================================
RÉSULTATS DE LA LECTURE
================================================================================
Adresse    Hex      Int16     Données      Statut
--------------------------------------------------------------------------------
0x1C00     0x1C00   7168      00 1C        ✓
0x1C01     0x1C01   7169      01 1C        ✓
0x1C02     0x1C02   7170      02 1C        ✓
...
```

### Recherche de valeur
```
Recherche de la valeur 22 dans la plage 0x1C00-0x1CFF
Mode: exact, Octets: 1
Total: 256 registres à vérifier
------------------------------------------------------------
✓ Correspondance trouvée à 0x1C16: 22 (0x0016)

================================================================================
RÉSULTATS DE LA RECHERCHE (valeur: 22)
================================================================================
Adresse    Hex      Int16     Données      Statut
--------------------------------------------------------------------------------
0x1C16     0x0016   22        16           ★
```

## Codes de statut

- `✓` : Lecture réussie
- `★` : Correspondance trouvée (mode recherche)
- `✗` : Erreur de lecture

## Mode mock

Le mode mock (`--mock`) simule les réponses du poêle pour les tests :
- Génère des données prévisibles basées sur l'adresse
- Évite les timeouts et erreurs de connexion
- Permet de tester le script sans poêle connecté

## Dépannage

### Problèmes de connexion
1. Vérifiez que le poêle est allumé
2. Vérifiez la connexion du câble RJ11
3. Vérifiez que le port série est correct (`/dev/ttyUSB0`)
4. Utilisez le mode mock pour tester : `--mock`

### Problèmes de performance
- Les lectures peuvent être lentes sur de grandes plages
- Utilisez des plages plus petites pour les tests
- Le mode mock est plus rapide pour les tests

### Valeurs inattendues
- Vérifiez le nombre d'octets (`--bytes`)
- Certains registres peuvent ne pas être accessibles
- Utilisez le mode mock pour comparer les résultats

## Intégration

Le script peut être intégré dans d'autres outils :

```python
from register_search import FlexibleRegisterReader

# Créer le lecteur
reader = FlexibleRegisterReader(use_mock=True)

# Se connecter
if reader.connect():
    # Lire un registre spécifique
    value, data = reader.read_register(0x1C00, 2)
    print(f"Valeur: {value}, Données: {data}")
    
    # Rechercher une valeur
    matches = reader.search_value_in_range(0x1C00, 0x1CFF, 22, 1)
    print(f"Correspondances: {matches}")
    
    reader.disconnect()
```

## Sécurité

⚠️ **Attention** : 
- Ne modifiez pas les registres sans connaître leur fonction
- Testez d'abord en mode mock
- Certains registres peuvent affecter le fonctionnement du poêle
