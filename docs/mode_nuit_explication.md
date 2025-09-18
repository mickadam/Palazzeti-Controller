# Mode Nuit - Explication

## Qu'est-ce que le mode nuit ?

Le mode nuit est une fonctionnalité **optionnelle** qui peut être présente sur certains modèles de poêles Palazzeti. Cette fonctionnalité permet de :

- **Réduire la puissance** du poêle pendant la nuit
- **Économiser les pellets** en maintenant une température plus basse
- **Réduire le bruit** de fonctionnement
- **Optimiser la consommation** énergétique

## Fonctionnalité optionnelle

⚠️ **Important** : Le mode nuit n'est **pas disponible sur tous les modèles** de poêles Palazzeti. Cela dépend de :

- **L'année de fabrication** du poêle
- **Le modèle spécifique** (Ines 9, Ines 9 Plus, etc.)
- **La version du firmware** installée
- **Les options installées** à l'achat

## Comment savoir si votre poêle a le mode nuit ?

### Méthode 1 : Test automatique
Le contrôleur détecte automatiquement si le mode nuit est disponible :

1. Lancez le script de détection :
   ```bash
   python detect_features.py
   ```

2. Le script testera toutes les fonctionnalités et vous dira si le mode nuit est disponible.

### Méthode 2 : Test manuel
Vous pouvez tester manuellement en envoyant la commande :
```
$WN1*XX
```
- Si vous recevez `$OK*XX` → Le mode nuit est disponible
- Si vous recevez `$ER*XX` → Le mode nuit n'est pas disponible

### Méthode 3 : Interface web
L'interface web masque automatiquement le bouton "Mode nuit" si cette fonctionnalité n'est pas disponible sur votre poêle.

## Que faire si le mode nuit n'est pas disponible ?

**Aucun problème !** Le contrôleur fonctionne parfaitement sans le mode nuit. Vous pouvez toujours :

- ✅ **Contrôler la température** (15-30°C)
- ✅ **Allumer/éteindre** le poêle
- ✅ **Surveiller l'état** en temps réel
- ✅ **Utiliser l'interface web** complètement

## Alternatives au mode nuit

Si votre poêle n'a pas le mode nuit, vous pouvez :

1. **Programmer manuellement** : Réduire la température le soir
2. **Utiliser un thermostat** : Connecter un thermostat externe
3. **Optimiser l'usage** : Ajuster la température selon vos besoins

## Modèles connus avec mode nuit

- Palazzeti Ines 9 Plus (modèles récents)
- Certains modèles avec firmware avancé
- Poêles avec options premium

## Modèles sans mode nuit

- Palazzeti Ines 9 (modèles de base)
- Anciens modèles
- Modèles sans options premium

## Conclusion

Le mode nuit est une fonctionnalité **bonus** qui n'affecte pas le fonctionnement principal du contrôleur. Votre poêle fonctionnera parfaitement avec ou sans cette fonctionnalité.

Le contrôleur s'adapte automatiquement et vous propose uniquement les fonctionnalités disponibles sur votre modèle spécifique. 