#!/usr/bin/env python3
"""
Script simple pour lire les registres de 1C00 à 207C
Usage: python3 read_1C00_207C.py [--mock]
"""
import sys
import os

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from read_registers_range import RegisterRangeReader


def main():
    """Fonction principale"""
    # Vérifier les arguments
    use_mock = '--mock' in sys.argv or '--dev' in sys.argv
    
    print("Lecteur de registres Palazzetti - Plage 1C00-207C")
    print("=" * 50)
    
    if use_mock:
        print("Mode développement (mock) activé")
    else:
        print("Mode production - connexion réelle au poêle")
    
    # Créer le lecteur
    reader = RegisterRangeReader(use_mock=use_mock)
    
    try:
        # Se connecter
        if not reader.connect():
            print("Impossible de se connecter au poêle")
            return 1
        
        # Lire la plage de registres 1C00-207C
        print(f"\nDébut de la lecture des registres...")
        results = reader.read_register_range(0x1C00, 0x207C)
        
        # Afficher le tableau des résultats
        reader.display_results_table(results)
        
        # Optionnel: sauvegarder les résultats dans un fichier
        save_to_file = input("\nVoulez-vous sauvegarder les résultats dans un fichier ? (o/N): ").strip().lower()
        if save_to_file in ['o', 'oui', 'y', 'yes']:
            filename = f"registres_1C00_207C_{'mock' if use_mock else 'reel'}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Résultats de lecture des registres 1C00-207C\n")
                f.write("=" * 50 + "\n")
                f.write(f"{'Adresse':<10} {'Hex':<8} {'Int16':<8} {'Données':<12} {'Statut'}\n")
                f.write("-" * 50 + "\n")
                
                for addr, value_int16, raw_data in results:
                    addr_str = f"0x{addr:04X}"
                    hex_str = f"0x{value_int16:04X}" if value_int16 is not None else "N/A"
                    int16_str = str(value_int16) if value_int16 is not None else "N/A"
                    data_str = f"{raw_data[0]:02X} {raw_data[1]:02X}" if raw_data else "N/A"
                    status = "✓" if value_int16 is not None else "✗"
                    
                    f.write(f"{addr_str:<10} {hex_str:<8} {int16_str:<8} {data_str:<12} {status}\n")
                
                f.write("-" * 50 + "\n")
                success_count = sum(1 for _, value, _ in results if value is not None)
                f.write(f"Résumé: {success_count}/{len(results)} registres lus avec succès\n")
            
            print(f"Résultats sauvegardés dans: {filename}")
        
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur")
    finally:
        reader.disconnect()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
