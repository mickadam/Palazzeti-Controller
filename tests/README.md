# Dossier Tests

Ce dossier contient tous les scripts et documents de test pour le projet Palazzeti Controller.

## Structure

### 📁 `scripts/`
Scripts de test et de débogage :
- `test_*.py` - Scripts de test unitaires et fonctionnels
- `debug_communication.py` - Script de débogage de la communication
- `read_1C00_207C.py` - Script de lecture de registres spécifiques
- `register_search.py` - Outil de recherche flexible dans les registres
- `register_tester.py` - CLI pour tester la lecture/écriture des registres

### 📁 `demos/`
Scripts de démonstration et d'exemples :
- `demo_*.py` - Scripts de démonstration
- `examples_*.py` - Exemples d'utilisation
- `read_registers_range.py` - Script de lecture de plages de registres

### 📁 `docs/`
Documentation technique et guides :
- `README_REGISTER_SEARCH.md` - Documentation pour la recherche de registres
- `README_REGISTER_TESTER.md` - Documentation pour le testeur de registres
- `COMPARISON_C_SHARP_PYTHON.md` - Comparaison entre C# et Python

## Utilisation

Pour exécuter les tests, naviguez vers le dossier approprié et lancez le script Python :

```bash
# Tests
cd tests/scripts
python test_communication.py

# Outils de recherche et test
cd tests/scripts
python register_search.py --start 1C00 --end 207C --bytes 2
python register_tester.py --interactive

# Démonstrations
cd tests/demos
python demo_registers.py
```

## Notes

- Tous les scripts de test ont été déplacés depuis le dossier `raspberry_pi/`
- Les imports peuvent nécessiter des ajustements selon l'environnement d'exécution
- Consultez la documentation dans `docs/` pour plus d'informations sur chaque composant
