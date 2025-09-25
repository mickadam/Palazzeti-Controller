# Diagrammes du Protocole de Communication Palazzetti

## Diagramme de séquence - Lecture d'un registre

```mermaid
sequenceDiagram
    participant C as Contrôleur
    participant P as Poêle Palazzetti
    
    Note over P: Poêle envoie périodiquement<br/>des trames de synchronisation
    P->>C: Trame sync (0x00)<br/>00 00 00 00 00 00 00 00 00 00 00
    
    Note over C: Attendre la trame de sync<br/>avant d'envoyer une commande
    C->>C: Attendre trame sync (timeout: 5s)
    
    Note over C: Construire la trame de lecture<br/>pour le registre de statut
    C->>P: Trame lecture (0x02)<br/>02 1C 20 00 00 00 00 00 00 00 3E
    
    Note over P: Traiter la demande<br/>et préparer la réponse
    P->>C: Réponse (0x02)<br/>02 1C 20 06 00 00 00 00 00 00 44
    
    Note over C: Vérifier le checksum<br/>et parser les données
    C->>C: Vérifier checksum (0x44)
    C->>C: Parser statut (0x06 = BURNING)
```

## Diagramme de séquence - Écriture dans un registre

```mermaid
sequenceDiagram
    participant C as Contrôleur
    participant P as Poêle Palazzetti
    
    Note over P: Poêle envoie périodiquement<br/>des trames de synchronisation
    P->>C: Trame sync (0x00)<br/>00 00 00 00 00 00 00 00 00 00 00
    
    Note over C: Attendre la trame de sync<br/>avant d'envoyer une commande
    C->>C: Attendre trame sync (timeout: 5s)
    
    Note over C: Construire la trame d'écriture<br/>pour définir la consigne à 22.5°C
    C->>P: Trame écriture (0x01)<br/>01 0F 20 E1 00 00 00 00 00 00 3C
    
    Note over P: Traiter la commande<br/>et confirmer l'écriture
    P->>C: Confirmation (0x01)<br/>01 0F 20 01 00 00 00 00 00 00 3C
    
    Note over C: Vérifier le checksum<br/>et le code de succès
    C->>C: Vérifier checksum (0x3C)
    C->>C: Vérifier code succès (0x01)
```

## Diagramme de flux - Gestion des erreurs

```mermaid
flowchart TD
    A[Démarrer communication] --> B[Attendre trame sync]
    B --> C{Trame sync reçue?}
    C -->|Non| D[Timeout?]
    D -->|Non| B
    D -->|Oui| E[Incrémenter tentative]
    E --> F{Tentatives < 10?}
    F -->|Oui| B
    F -->|Non| G[Erreur: Pas de sync]
    
    C -->|Oui| H[Envoyer commande]
    H --> I[Attendre réponse]
    I --> J{Réponse reçue?}
    J -->|Non| K[Timeout?]
    K -->|Non| I
    K -->|Oui| E
    
    J -->|Oui| L[Vérifier checksum]
    L --> M{Checksum OK?}
    M -->|Non| N[Erreur: Checksum invalide]
    M -->|Oui| O[Parser les données]
    O --> P[Succès]
    
    G --> Q[Fin avec erreur]
    N --> Q
    P --> R[Fin avec succès]
```

## Diagramme de structure - Format des trames

```mermaid
graph TD
    A[Trame Palazzetti - 11 bytes] --> B[Byte 0: ID]
    A --> C[Bytes 1-9: Données]
    A --> D[Byte 10: Checksum]
    
    B --> B1[0x00: Synchronisation]
    B --> B2[0x01: Écriture]
    B --> B3[0x02: Lecture]
    
    C --> C1[Bytes 1-2: Adresse LSB/MSB]
    C --> C2[Bytes 3-9: Données/Padding]
    
    D --> D1[Somme de tous les bytes<br/>modulo 256]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
```

## Diagramme d'état - Cycle de vie du poêle

```mermaid
stateDiagram-v2
    [*] --> OFF: Démarrage
    OFF --> HEAT_UP: Commande ON
    HEAT_UP --> BURNING: Température atteinte
    BURNING --> COOLING: Commande OFF
    COOLING --> OFF: Refroidissement terminé
    
    HEAT_UP --> ALARM: Erreur d'allumage
    BURNING --> ALARM: Erreur de combustion
    COOLING --> ALARM: Erreur de refroidissement
    
    ALARM --> OFF: Reset manuel
    
    note right of OFF: Poêle éteint<br/>Température ambiante
    note right of HEAT_UP: Phase de chauffe<br/>Allumage en cours
    note right of BURNING: Combustion active<br/>Température de consigne
    note right of COOLING: Refroidissement<br/>Nettoyage automatique
    note right of ALARM: Erreur détectée<br/>Arrêt de sécurité
```

## Diagramme de déploiement - Architecture système

```mermaid
graph TB
    subgraph "Raspberry Pi"
        A[Application Python]
        B[Module Communication]
        C[Port Série /dev/ttyUSB0]
    end
    
    subgraph "Câblage"
        D[Câble RJ11]
        E[Convertisseur USB-Série]
    end
    
    subgraph "Poêle Palazzetti"
        F[Contrôleur Poêle]
        G[Registres Mémoire]
        H[Capteurs]
        I[Actionneurs]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    G --> I
    
    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style F fill:#fff3e0
    style G fill:#fce4ec
```

## Diagramme de timing - Séquence de communication

```mermaid
gantt
    title Séquence de Communication Palazzetti
    dateFormat X
    axisFormat %L ms
    
    section Synchronisation
    Attendre sync    :0, 2000
    Trame sync reçue :2000, 2100
    
    section Lecture
    Envoyer lecture  :2100, 2200
    Traitement poêle :2200, 2500
    Réponse reçue    :2500, 2600
    
    section Écriture
    Envoyer écriture :2600, 2700
    Traitement poêle :2700, 3000
    Confirmation     :3000, 3100
    
    section Pause
    Attente          :3100, 5000
```

## Diagramme de classes - Structure du code

```mermaid
classDiagram
    class PalazzettiFrame {
        +int id
        +List[int] data
        +int checksum
        +compute_checksum() int
        +is_valid() bool
        +as_bytes() bytes
        +from_buffer(buffer) Frame
    }
    
    class PalazzettiCommunicator {
        -Serial serial
        -Lock lock
        +connect() bool
        +disconnect() void
        +wait_for_sync() bool
        +read_register(address) Frame
        +write_register(address, data) Frame
        -wait_for_response(id) Frame
    }
    
    class RegisterTester {
        -PalazzettiCommunicator comm
        -Dict registers
        +list_registers() void
        +read_register(name) Any
        +write_register(name, value) bool
        +test_all_registers() bool
        +interactive_mode() void
    }
    
    class PalazzettiController {
        -PalazzettiCommunicator comm
        -Dict state
        -Thread monitor_thread
        +get_state() Dict
        +set_temperature(temp) bool
        +set_power(on) bool
        +start_monitoring() void
        +stop_monitoring() void
    }
    
    PalazzettiCommunicator --> PalazzettiFrame
    RegisterTester --> PalazzettiCommunicator
    PalazzettiController --> PalazzettiCommunicator
```

## Diagramme de flux de données - Parsing des registres

```mermaid
flowchart TD
    A[Trame reçue] --> B[Vérifier checksum]
    B --> C{Checksum valide?}
    C -->|Non| D[Erreur: Trame corrompue]
    C -->|Oui| E[Extraire ID et données]
    
    E --> F{Type de registre?}
    F -->|Statut| G[Parser statut<br/>data[2] = code]
    F -->|Température| H[Parser température<br/>data[2-3] = temp_raw/10]
    F -->|Consigne| I[Parser consigne<br/>data[2-3] = temp_raw/10]
    F -->|Puissance| J[Parser puissance<br/>data[2] = on/off]
    F -->|Erreur| K[Parser erreur<br/>data[2] = code]
    
    G --> L[Retourner (code, nom, alimenté)]
    H --> M[Retourner température °C]
    I --> N[Retourner consigne °C]
    J --> O[Retourner booléen]
    K --> P[Retourner code + message]
    
    D --> Q[Fin avec erreur]
    L --> R[Fin avec succès]
    M --> R
    N --> R
    O --> R
    P --> R
```

## Diagramme de cas d'usage - Scénarios typiques

```mermaid
graph TD
    A[Utilisateur] --> B[Contrôler le poêle]
    
    B --> C[Allumer le poêle]
    B --> D[Éteindre le poêle]
    B --> E[Changer la température]
    B --> F[Surveiller l'état]
    
    C --> C1[Envoyer commande ON]
    C1 --> C2[Vérifier statut BURNING]
    
    D --> D1[Envoyer commande OFF]
    D1 --> D2[Vérifier statut COOLING]
    
    E --> E1[Calculer bytes température]
    E1 --> E2[Envoyer consigne]
    E2 --> E3[Vérifier confirmation]
    
    F --> F1[Lecture périodique]
    F1 --> F2[Parser statut]
    F2 --> F3[Parser température]
    F3 --> F4[Parser erreurs]
    F4 --> F5[Mettre à jour interface]
    
    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#ffebee
    style E fill:#fff3e0
    style F fill:#f1f8e9
```
