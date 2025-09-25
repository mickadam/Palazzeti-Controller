#!/usr/bin/env python3
"""
Script de démonstration pour le testeur de registres Palazzetti
Montre les différentes façons d'utiliser le CLI
"""
import sys
import os

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from register_tester import RegisterTester


def demo_basic_usage():
    """Démonstration de l'utilisation de base"""
    print("=== Démonstration: Utilisation de base ===")
    
    # Créer le testeur en mode mock pour la démo
    tester = RegisterTester(use_mock=True)
    
    if not tester.connect():
        print("Erreur de connexion")
        return
    
    print("\n1. Lister tous les registres disponibles:")
    tester.list_registers()
    
    print("\n2. Lire quelques registres:")
    tester.read_register('status')
    tester.read_register('temperature')
    tester.read_register('setpoint')
    
    print("\n3. Afficher l'état complet:")
    tester.show_complete_state()
    
    tester.disconnect()


def demo_register_operations():
    """Démonstration des opérations sur les registres"""
    print("\n=== Démonstration: Opérations sur les registres ===")
    
    tester = RegisterTester(use_mock=True)
    
    if not tester.connect():
        print("Erreur de connexion")
        return
    
    print("\n1. Test de lecture de tous les registres:")
    tester.test_all_registers()
    
    print("\n2. Test d'écriture dans un registre modifiable:")
    print("   Tentative d'écriture de la température de consigne à 24°C")
    tester.write_register('setpoint', 24.0)
    
    print("\n3. Vérification de l'écriture:")
    tester.read_register('setpoint')
    
    print("\n4. Test d'écriture dans le contrôle de puissance:")
    print("   Tentative d'allumage du poêle")
    tester.write_register('power_control', True)
    
    print("\n5. Vérification de l'état après modification:")
    tester.show_complete_state()
    
    tester.disconnect()


def demo_validation():
    """Démonstration de la validation des données"""
    print("\n=== Démonstration: Validation des données ===")
    
    tester = RegisterTester(use_mock=True)
    
    if not tester.connect():
        print("Erreur de connexion")
        return
    
    print("\n1. Test de valeurs valides:")
    print("   Température valide (22°C):")
    tester.write_register('setpoint', 22.0)
    
    print("\n   Niveau de puissance valide (3):")
    tester.write_register('power_level', 3)
    
    print("\n2. Test de valeurs invalides:")
    print("   Température trop basse (10°C):")
    tester.write_register('setpoint', 10.0)
    
    print("\n   Niveau de puissance invalide (10):")
    tester.write_register('power_level', 10)
    
    print("\n3. Test de lecture d'un registre non modifiable:")
    print("   Tentative d'écriture dans le registre de statut:")
    tester.write_register('status', 0x06)
    
    tester.disconnect()


def main():
    """Fonction principale de démonstration"""
    print("Démonstration du testeur de registres Palazzetti")
    print("=" * 60)
    
    try:
        demo_basic_usage()
        demo_register_operations()
        demo_validation()
        
        print("\n" + "=" * 60)
        print("Démonstration terminée!")
        print("\nPour utiliser le CLI en mode interactif:")
        print("  python3 register_tester.py --interactive")
        print("\nPour voir toutes les options:")
        print("  python3 register_tester.py --help")
        
    except KeyboardInterrupt:
        print("\nDémonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\nErreur lors de la démonstration: {e}")


if __name__ == '__main__':
    main()
