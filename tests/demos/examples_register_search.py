#!/usr/bin/env python3
"""
Exemples d'utilisation du script register_search.py
"""
import subprocess
import sys
import os

def run_example(description, command):
    """Exécuter un exemple et afficher le résultat"""
    print(f"\n{'='*60}")
    print(f"EXEMPLE: {description}")
    print(f"Commande: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        print(result.stdout)
        if result.stderr:
            print("Erreurs:", result.stderr)
    except subprocess.TimeoutExpired:
        print("Timeout - exemple interrompu")
    except Exception as e:
        print(f"Erreur: {e}")

def main():
    """Fonction principale avec exemples"""
    print("EXEMPLES D'UTILISATION DU SCRIPT REGISTER_SEARCH.PY")
    print("="*60)
    
    # Vérifier que le script existe
    script_path = os.path.join(os.path.dirname(__file__), 'register_search.py')
    if not os.path.exists(script_path):
        print(f"Erreur: Le script {script_path} n'existe pas")
        return 1
    
    examples = [
        (
            "Lecture d'une petite plage (1C00-1C0F) avec 2 octets",
            "python3 register_search.py --start 1C00 --end 1C0F --bytes 2 --mock"
        ),
        (
            "Recherche de la valeur 22 dans la plage 1C00-1CFF avec 1 octet",
            "python3 register_search.py --start 1C00 --end 1CFF --search 22 --bytes 1 --mock"
        ),
        (
            "Recherche de la valeur hexadécimale 0x1234 dans la plage 2000-207C",
            "python3 register_search.py --start 2000 --end 207C --search 0x1234 --bytes 2 --mock"
        ),
        (
            "Lecture de la plage complète 1C00-207C (mode mock)",
            "python3 register_search.py --start 1C00 --end 207C --bytes 2 --mock"
        ),
        (
            "Recherche avec correspondance partielle",
            "python3 register_search.py --start 1C00 --end 1CFF --search 0x12 --bytes 1 --partial --mock"
        )
    ]
    
    print("Choisissez un exemple à exécuter:")
    for i, (desc, _) in enumerate(examples, 1):
        print(f"{i}. {desc}")
    
    print("0. Exécuter tous les exemples")
    print("q. Quitter")
    
    while True:
        choice = input("\nVotre choix: ").strip()
        
        if choice.lower() == 'q':
            print("Au revoir !")
            break
        elif choice == '0':
            # Exécuter tous les exemples
            for desc, cmd in examples:
                run_example(desc, cmd)
                input("\nAppuyez sur Entrée pour continuer...")
            break
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(examples):
                    desc, cmd = examples[idx]
                    run_example(desc, cmd)
                else:
                    print("Choix invalide")
            except ValueError:
                print("Choix invalide")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
