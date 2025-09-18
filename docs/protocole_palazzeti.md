# Protocole de Communication Palazzeti (Protocole Binaire)

## Vue d'ensemble

Le poêle Palazzeti utilise un protocole de communication série **binaire** via le port RJ11. Le protocole est basé sur des trames binaires de 11 bytes avec checksum.

## Format des trames

### Structure générale
```
[ID][D0][D1][D2][D3][D4][D5][D6][D7][PAD][CS]
```

- **ID** : Identifiant de la trame (1 byte)
- **D0-D7** : Données (8 bytes)
- **PAD** : Padding (1 byte, toujours 0x00)
- **CS** : Checksum (1 byte)

### Types de trames

#### 1. Trame de synchronisation
```
ID = 0x00
```
- Envoyée par le poêle pour synchroniser la communication
- Doit être reçue avant d'envoyer toute commande

#### 2. Trame de lecture
```
ID = 0x01
D0-D1 = Adresse à lire (2 bytes)
D2-D7 = 0x00 (padding)
```

#### 3. Trame de réponse
```
ID = 0x01 (même ID que la lecture)
D0-D7 = Données lues
```

## Adresses de registres

### Registres de lecture

| Adresse | Description | Format |
|---------|-------------|---------|
| `0x20, 0x1C` | Statut du poêle | 1 byte |
| `0x20, 0x0E` | Température actuelle | 2 bytes |
| `0x20, 0x0F` | Température de consigne | 2 bytes |

### Codes de statut

| Code | État | Description |
|------|------|-------------|
| `0x00` | OFF | Poêle éteint |
| `0x06` | BURNING | Poêle en combustion |
| `0x09` | COOLING | Poêle en refroidissement |
| `0x11` | STARTING | Poêle en démarrage |

## Calcul du checksum

Le checksum est calculé par **somme simple** de tous les bytes de la trame :

```python
def compute_checksum(frame_id, data, pad=0x00):
    checksum = frame_id
    for byte in data:
        checksum += byte
    checksum += pad
    return checksum & 0xFF  # Garder seulement le byte de poids faible
```

## Paramètres de communication

- **Baudrate** : 38400 bps
- **Parité** : Aucune
- **Bits de données** : 8
- **Bits d'arrêt** : 2
- **Contrôle de flux** : Aucun
- **Niveau logique** : TTL 3.3V

## Séquence de communication

### 1. Initialisation
1. Attendre la trame de synchronisation `0x00`
2. Envoyer une trame de lecture pour vérifier la connexion
3. Attendre la réponse

### 2. Lecture d'état
```
1. Attendre trame sync (0x00)
2. Envoyer: [0x01][0x20][0x1C][0x00][0x00][0x00][0x00][0x00][0x00][0x00][CS]
3. Attendre: [0x01][STATUT][...][0x00][CS]
```

### 3. Lecture de température
```
1. Attendre trame sync (0x00)
2. Envoyer: [0x01][0x20][0x0E][0x00][0x00][0x00][0x00][0x00][0x00][0x00][CS]
3. Attendre: [0x01][TEMP_H][TEMP_L][...][0x00][CS]
```

## Gestion des erreurs

- **Timeout** : 5 secondes maximum pour une réponse
- **Retry** : 3 tentatives en cas d'échec
- **Validation** : Vérifier le checksum de chaque trame reçue
- **Logging** : Enregistrer toutes les communications pour debug

## Exemple d'implémentation

```python
class Frame:
    def __init__(self, frame_id, data, pad=0x00):
        self.id = frame_id
        self.data = data[:8]  # Limiter à 8 bytes
        self.pad = pad
        self.checksum = self.compute_checksum()
    
    def compute_checksum(self):
        checksum = self.id
        for byte in self.data:
            checksum += byte
        checksum += self.pad
        return checksum & 0xFF
    
    def as_bytes(self):
        return bytes([self.id] + self.data + [self.pad, self.checksum])
```

## Références

- [Blog Palazzetti-Martina - La liaison série](https://palazzetti-martina.blogspot.com/2020/01/la-liaison-serie.html)
- [Blog Palazzetti-Martina - Les trames](https://palazzetti-martina.blogspot.com/2020/01/les-trames.html)
- [Blog Palazzetti-Martina - Table des registres](https://palazzetti-martina.blogspot.com/2020/02/la-table-des-registres.html) 