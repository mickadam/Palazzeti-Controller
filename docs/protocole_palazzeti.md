# Protocole de Communication Série - Poêle Palazzetti

## Vue d'ensemble

Le poêle Palazzetti utilise un protocole de communication série **binaire** via le port RJ11. Ce protocole permet de contrôler et de surveiller le poêle à granulés de manière bidirectionnelle.

### Caractéristiques principales

- **Protocole binaire** : Utilise des trames de 11 bytes
- **Communication bidirectionnelle** : Lecture et écriture des registres
- **Synchronisation** : Basée sur des trames de synchronisation
- **Vérification d'intégrité** : Checksum sur chaque trame
- **Temps réel** : Mise à jour continue de l'état du poêle

## Configuration matérielle

### Paramètres de communication série

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| **Baudrate** | 38400 bps | Vitesse de transmission |
| **Bits de données** | 8 | Taille des données |
| **Parité** | Aucune | Pas de bit de parité |
| **Bits d'arrêt** | 2 | Nombre de bits d'arrêt |
| **Contrôle de flux** | Aucun | Pas de contrôle de flux |
| **Niveau logique** | TTL 3.3V | Niveau de tension |

## Format des trames

### Structure générale

Chaque trame fait exactement **11 bytes** avec la structure suivante :

```
[ID][D0][D1][D2][D3][D4][D5][D6][D7][D8][CS]
```

| Position | Nom | Taille | Description |
|----------|-----|--------|-------------|
| 0 | ID | 1 byte | Identifiant de la trame |
| 1-9 | D0-D8 | 9 bytes | Données (format C#) |
| 10 | CS | 1 byte | Checksum |

### Types de trames

#### 1. Trame de synchronisation
```
ID = 0x00
```
- **Émetteur** : Poêle Palazzetti
- **Fréquence** : Périodique (toutes les ~2 secondes)
- **Usage** : Synchronisation de la communication
- **Données** : 9 bytes de padding (0x00)

**Exemple** :
```
00 00 00 00 00 00 00 00 00 00 00
```

#### 2. Trame de lecture
```
ID = 0x02
D0-D1 = Adresse à lire (LSB, MSB)
D2-D8 = Padding (0x00)
```
- **Émetteur** : Contrôleur (Raspberry Pi)
- **Usage** : Demander la lecture d'un registre
- **Format d'adresse** : Little-endian (LSB en premier)

**Exemple** - Lecture du statut :
```
02 1C 20 00 00 00 00 00 00 00 3E
```

#### 3. Trame de réponse (lecture)
```
ID = 0x02 (même ID que la demande)
D0-D1 = Adresse lue (LSB, MSB)
D2-D8 = Données lues
```
- **Émetteur** : Poêle Palazzetti
- **Usage** : Réponse à une demande de lecture

**Exemple** - Réponse statut (BURNING) :
```
02 1C 20 06 00 00 00 00 00 00 44
```

#### 4. Trame d'écriture
```
ID = 0x01
D0-D1 = Adresse à écrire (LSB, MSB)
D2-D8 = Données à écrire
```
- **Émetteur** : Contrôleur (Raspberry Pi)
- **Usage** : Écrire des données dans un registre

**Exemple** - Écriture température de consigne (22°C) :
```
01 0F 20 DC 00 00 00 00 00 00 3C
```

#### 5. Trame de confirmation (écriture)
```
ID = 0x01 (même ID que la demande)
D0-D1 = Adresse écrite (LSB, MSB)
D2 = Code de confirmation (0x01 = succès)
D3-D8 = Padding (0x00)
```
- **Émetteur** : Poêle Palazzetti
- **Usage** : Confirmer l'écriture

## Adresses de registres

### Registres de lecture/écriture

| Nom | Adresse | Description | Format | R/W |
|-----|---------|-------------|--------|-----|
| **Statut** | `0x201C` | État du poêle | 1 byte | R |
| **Température** | `0x200E` | Température actuelle | 2 bytes | R |
| **Consigne** | `0x200F` | Température de consigne | 2 bytes | R/W |
| **Contrôle puissance** | `0x201D` | ON/OFF du poêle | 1 byte | R/W |
| **Niveau puissance** | `0x202A` | Niveau 1-5 | 1 byte | R/W |
| **Contrôle démarrage** | `0x2044` | Contrôle démarrage | 1 byte | R/W |
| **Code erreur** | `0x201E` | Code d'erreur | 1 byte | R |
| **Statut alarmes** | `0x201F` | État des alarmes | 1 byte | R |
| **Paramètres timer** | `0x2072` | Timer enable/disable | 1 byte | R/W |

### Format des données

#### Température (2 bytes)
- **Format** : Little-endian, valeur × 10
- **Exemple** : 22.5°C = 225 = `0xE1 0x00`

#### Statut (1 byte)
- **Valeurs** : Voir section [Codes de statut](#codes-de-statut)

#### Contrôle de puissance (1 byte)
- `0x00` : OFF
- `0x01` : ON

## Codes de statut et erreurs

### Codes de statut du poêle

| Code | Nom | Description | Alimenté |
|------|-----|-------------|----------|
| `0x00` | OFF | Poêle éteint | Non |
| `0x01` | --- | État réservé | Non |
| `0x02` | TEST FIRE | Test de combustion | Oui |
| `0x03` | HEAT UP | Phase de chauffe | Oui |
| `0x04` | FUEL IGN | Allumage du combustible | Oui |
| `0x05` | IGN TEST | Test d'allumage | Oui |
| `0x06` | BURNING | Combustion active | Oui |
| `0x07` | --- | État réservé | Non |
| `0x08` | --- | État réservé | Non |
| `0x09` | COOLING | Refroidissement | Non |
| `0x0A` | FIRE STOP | Arrêt de combustion | Non |
| `0x0B` | CLEAN FIRE | Nettoyage de combustion | Non |
| `0x0C` | COOL | Froid | Non |
| `0x0D` | OFF | Poêle éteint | Non |
| `0x0E` | HEAT UP | Phase de chauffe | Oui |
| `0x0F` | FIRE UP | Montée en température | Oui |
| `0x10` | STABILIZATION | Stabilisation | Oui |
| `0x11` | BURNING | Combustion active | Oui |
| `0x12` | CLEANING | Nettoyage | Non |
| `0x13` | FINAL CLEANING | Nettoyage final | Non |
| `0x14` | STANDBY | Veille | Non |
| `0x15` | ALARM | Alarme | Non |
| `0x16` | ALARM | Alarme | Non |

### Codes d'erreur

| Code | Erreur | Description |
|------|--------|-------------|
| `0x00` | Aucune erreur | Fonctionnement normal |
| `0x01` | E001 | Clavier de commande défectueux |
| `0x04` | E004 | Coupure de liaison carte/clavier |
| `0x101` | E101 | Allumage raté (granulés ou braséro) |
| `0x108` | E108 | Porte ou trémie ouverte |
| `0x109` | E109 | Alarme pression/disjoncteur |
| `0x110` | E110 | Dysfonctionnement sonde température air |
| `0x111` | E111 | Dysfonctionnement sonde température fumées |

## Calcul du checksum

Le checksum est calculé par **somme simple** de tous les bytes de la trame :

```python
def compute_checksum(frame_id, data):
    checksum = frame_id
    for byte in data:
        checksum += byte
    return checksum & 0xFF  # Garder seulement le byte de poids faible
```

## Séquence de communication

### 1. Initialisation
1. Attendre la trame de synchronisation `0x00`
2. Envoyer une trame de lecture pour vérifier la connexion
3. Attendre la réponse

### 2. Lecture d'état
```
1. Attendre trame sync (0x00)
2. Envoyer: [0x02][0x1C][0x20][0x00][0x00][0x00][0x00][0x00][0x00][0x00][0x3E]
3. Attendre: [0x02][0x1C][0x20][0x06][0x00][0x00][0x00][0x00][0x00][0x00][0x44]
```

### 3. Lecture de température
```
1. Attendre trame sync (0x00)
2. Envoyer: [0x02][0x0E][0x20][0x00][0x00][0x00][0x00][0x00][0x00][0x00][0x30]
3. Attendre: [0x02][0x0E][0x20][0xE1][0x00][0x00][0x00][0x00][0x00][0x00][0x11]
```

### 4. Écriture de consigne
```
1. Attendre trame sync (0x00)
2. Envoyer: [0x01][0x0F][0x20][0xDC][0x00][0x00][0x00][0x00][0x00][0x00][0x3C]
3. Attendre: [0x01][0x0F][0x20][0x01][0x00][0x00][0x00][0x00][0x00][0x00][0x3C]
```

## Gestion des erreurs

- **Timeout** : 5 secondes maximum pour une réponse
- **Retry** : 10 tentatives en cas d'échec
- **Validation** : Vérifier le checksum de chaque trame reçue
- **Logging** : Enregistrer toutes les communications pour debug

## Exemple d'implémentation

```python
class PalazzettiFrame:
    def __init__(self, frame_id, data):
        self.id = frame_id
        self.data = data[:9]  # Limiter à 9 bytes (format C#)
        self.checksum = self.compute_checksum()
    
    def compute_checksum(self):
        checksum = self.id
        for byte in self.data:
            checksum += byte
        return checksum & 0xFF
    
    def is_valid(self):
        return self.compute_checksum() == self.checksum
    
    def as_bytes(self):
        return bytes([self.id] + self.data + [self.checksum])
    
    @classmethod
    def from_buffer(cls, buffer):
        if len(buffer) < 11:
            raise ValueError(f"Buffer trop court: {len(buffer)} bytes, attendu 11")
        
        frame = cls(None, None)
        frame.id = buffer[0]
        frame.data = list(buffer[1:10])  # 9 bytes de données
        frame.checksum = buffer[10]
        return frame

def construct_read_frame(address):
    """Construire une trame de lecture"""
    if len(address) != 2:
        raise ValueError("L'adresse doit contenir exactement 2 bytes")
    
    # Format C#: [adresse_LSB][adresse_MSB] + 7 bytes de padding
    data = [address[1], address[0]] + [0x00] * 7  # LSB en premier
    return PalazzettiFrame(frame_id=0x02, data=data)

def construct_write_frame(address, value_bytes):
    """Construire une trame d'écriture"""
    if len(address) != 2:
        raise ValueError("L'adresse doit contenir exactement 2 bytes")
    
    # Format C#: [adresse_LSB][adresse_MSB] + valeur + padding
    data = [address[1], address[0]] + value_bytes
    while len(data) < 9:  # 9 bytes de données
        data.append(0x00)
    
    return PalazzettiFrame(frame_id=0x01, data=data)
```

## Exemples pratiques

### Lecture du statut
```python
# 1. Attendre la trame de synchronisation
sync_frame = wait_for_sync_frame()

# 2. Envoyer la commande de lecture
read_frame = construct_read_frame([0x20, 0x1C])
serial.write(read_frame.as_bytes())

# 3. Attendre la réponse
response = wait_for_frame_by_id(0x02)
status_code, status_name, power_on = parse_status(response.data)
```

### Définition de la température de consigne
```python
# 1. Attendre la trame de synchronisation
sync_frame = wait_for_sync_frame()

# 2. Convertir la température (22.5°C)
temp_raw = int(22.5 * 10)  # 225
value_bytes = [temp_raw & 0xFF, (temp_raw >> 8) & 0xFF]  # [0xE1, 0x00]

# 3. Envoyer la commande d'écriture
write_frame = construct_write_frame([0x20, 0x0F], value_bytes)
serial.write(write_frame.as_bytes())

# 4. Attendre la confirmation
response = wait_for_frame_by_id(0x01)
```

## Bonnes pratiques

### 1. Gestion des timeouts
- Toujours définir des timeouts appropriés
- Implémenter une stratégie de retry robuste
- Logger les échecs de communication

### 2. Validation des données
- Vérifier le checksum de chaque trame
- Valider les plages de valeurs
- Gérer les cas d'erreur gracieusement

### 3. Synchronisation
- Toujours attendre la trame de synchronisation
- Ne pas envoyer de commandes en parallèle
- Utiliser des verrous pour la communication série

## Références

- [Blog Palazzetti-Martina - La liaison série](https://palazzetti-martina.blogspot.com/2020/01/la-liaison-serie.html)
- [Blog Palazzetti-Martina - Les trames](https://palazzetti-martina.blogspot.com/2020/01/les-trames.html)
- [Blog Palazzetti-Martina - Table des registres](https://palazzetti-martina.blogspot.com/2020/02/la-table-des-registres.html)
- Documentation technique Palazzetti (modèles concernés)
- Code source du projet Palazzeti-Controller 