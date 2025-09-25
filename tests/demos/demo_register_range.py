#!/usr/bin/env python3
"""
Démonstration du lecteur de registres pour la plage 1C00-207C
"""
import sys
import os

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from read_registers_range import RegisterRangeReader


def demo_small_range():
    """Démonstration avec une petite plage pour tester"""
    print("=== DÉMONSTRATION - Lecture d'une petite plage de registres ===")
    print("Plage: 0x1C00 à 0x1C0F (16 registres)")
    print()
    
    reader = RegisterRangeReader(use_mock=True)  # Mode mock pour la démo
    
    try:
        if not reader.connect():
            print("Erreur de connexion")
            return
        
        # Lire une petite plage pour la démo
        results = reader.read_register_range(0x1C00, 0x1C0F)
        
        # Afficher le tableau
        reader.display_results_table(results)
        
    finally:
        reader.disconnect()


def demo_full_range():
    """Démonstration avec la plage complète demandée"""
    print("=== DÉMONSTRATION - Lecture de la plage complète 1C00-207C ===")
    print("Plage: 0x1C00 à 0x207C (1152 registres)")
    print("ATTENTION: Cette démo utilise le mode mock pour éviter les timeouts")
    print()
    
    reader = RegisterRangeReader(use_mock=True)  # Mode mock pour la démo
    
    try:
        if not reader.connect():
            print("Erreur de connexion")
            return
        
        # Lire la plage complète
        results = reader.read_register_range(0x1C00, 0x207C)
        
        # Afficher le tableau
        reader.display_results_table(results)
        
    finally:
        reader.disconnect()


def main():
    """Fonction principale de démonstration"""
    print("Démonstration du lecteur de registres Palazzetti")
    print("=" * 50)
    
    while True:
        print("\nOptions disponibles:")
        print("1. Démo petite plage (0x1C00-0x1C0F)")
        print("2. Démo plage complète (0x1C00-0x207C)")
        print("3. Quitter")
        
        choice = input("\nVotre choix (1-3): ").strip()
        
        if choice == '1':
            demo_small_range()
        elif choice == '2':
            demo_full_range()
        elif choice == '3':
            print("Au revoir !")
            break
        else:
            print("Choix invalide, veuillez réessayer")


if __name__ == '__main__':
    main()
