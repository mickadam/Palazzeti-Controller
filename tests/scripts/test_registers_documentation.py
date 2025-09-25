#!/usr/bin/env python3
"""
Script de test pour valider les registres selon la documentation Palazzetti-Martina
"""
import sys
import os

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from register_tester import RegisterTester


def test_all_registers_with_documentation():
    """Tester tous les registres selon la documentation"""
    print("=== Test des registres selon la documentation Palazzetti-Martina ===")
    print("Source: https://palazzetti-martina.blogspot.com/2020/01/")
    print()
    
    # Créer le testeur
    tester = RegisterTester(use_mock=False)
    
    if not tester.connect():
        print("✗ Impossible de se connecter au poêle")
        return
    
    print("✓ Connexion établie")
    print()
    
    # Registres à tester avec leur taille selon la documentation
    registers_to_test = [
        {
            'name': 'status',
            'address': [0x20, 0x1C],
            'size': '1 byte',
            'description': 'Code de statut (0-22)'
        },
        {
            'name': 'temperature',
            'address': [0x20, 0x0E],
            'size': '2 bytes',
            'description': 'Température actuelle'
        },
        {
            'name': 'setpoint',
            'address': [0x20, 0x0F],
            'size': '2 bytes',
            'description': 'Température de consigne'
        },
        {
            'name': 'power_control',
            'address': [0x20, 0x1D],
            'size': '1 byte',
            'description': 'Contrôle ON/OFF'
        },
        {
            'name': 'power_level',
            'address': [0x20, 0x2A],
            'size': '1 byte',
            'description': 'Niveau de puissance (1-5)'
        },
        {
            'name': 'start_control',
            'address': [0x20, 0x44],
            'size': '1 byte',
            'description': 'Contrôle de démarrage'
        },
        {
            'name': 'error_code',
            'address': [0x20, 0x1E],
            'size': '1 byte',
            'description': 'Code d\'erreur'
        },
        {
            'name': 'alarm_status',
            'address': [0x20, 0x1F],
            'size': '1 byte',
            'description': 'Statut des alarmes'
        },
        {
            'name': 'timer_settings',
            'address': [0x20, 0x72],
            'size': '1 byte',
            'description': 'Paramètres du timer'
        }
    ]
    
    results = []
    
    for reg in registers_to_test:
        print(f"--- Test: {reg['name']} ({reg['size']}) ---")
        print(f"Adresse: 0x{reg['address'][0]:02X} 0x{reg['address'][1]:02X}")
        print(f"Description: {reg['description']}")
        
        try:
            result = tester.read_register(reg['name'])
            if result is not None:
                print(f"✓ Lecture réussie")
                results.append((reg['name'], True, reg['size']))
            else:
                print(f"✗ Lecture échouée")
                results.append((reg['name'], False, reg['size']))
        except Exception as e:
            print(f"✗ Erreur: {e}")
            results.append((reg['name'], False, reg['size']))
        
        print()
    
    # Résumé
    print("=== Résumé des tests ===")
    success_count = 0
    for name, success, size in results:
        status = "✓" if success else "✗"
        print(f"{status} {name} ({size})")
        if success:
            success_count += 1
    
    print(f"\nRésultat: {success_count}/{len(results)} registres testés avec succès")
    
    tester.disconnect()


def test_temperature_accuracy():
    """Tester la précision de la température"""
    print("\n=== Test de précision de la température ===")
    
    tester = RegisterTester(use_mock=False)
    
    if not tester.connect():
        print("✗ Impossible de se connecter au poêle")
        return
    
    print("✓ Connexion établie")
    print("Lisez la température sur votre affichage et comparez avec le résultat...")
    print()
    
    try:
        result = tester.read_register('temperature')
        if result is not None:
            print(f"✓ Température lue: {result}°C")
            print("Comparez avec votre affichage du poêle")
        else:
            print("✗ Impossible de lire la température")
    except Exception as e:
        print(f"✗ Erreur: {e}")
    
    tester.disconnect()


def main():
    """Fonction principale"""
    print("Test des registres selon la documentation Palazzetti-Martina")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--temp":
            test_temperature_accuracy()
        else:
            print("Usage:")
            print("  python3 test_registers_documentation.py        - Tester tous les registres")
            print("  python3 test_registers_documentation.py --temp - Tester la précision de la température")
    else:
        test_all_registers_with_documentation()


if __name__ == '__main__':
    main()
