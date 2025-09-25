#!/usr/bin/env python3
"""
Script de test pour la fonction get_setpoint_atech()
"""
import sys
import os

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from palazzeti_controller import PalazzettiController
from config import *


def test_setpoint_atech():
    """
    Tester la lecture de la consigne selon le code C iGetSetPointAtech()
    
    Nouvelle implémentation utilisant:
    - REGISTER_SETPOINT_ATECH_8BYTES [0x1C, 0x32] pour fluide < 2
    - REGISTER_SETPOINT_ATECH_2BYTES [0x1C, 0x54] pour fluide = 2
    
    Types de fluides:
    - 0: Granulés (8 octets, conversion /5.0 et /10.0)
    - 1: Autre fluide (8 octets, pas de conversion)
    - 2: Fluide spécial (2 octets, little-endian)
    """
    print("Test de la fonction get_setpoint_atech() - Nouvelle implémentation C")
    print("=" * 70)
    
    # Créer le contrôleur
    controller = PalazzettiController(use_mock=False)  # Mode réel
    
    try:
        # Se connecter
        if not controller.connect():
            print("✗ Impossible de se connecter au poêle")
            return False
        
        print("✓ Connexion établie")
        
        # Tester avec fluide type 0 (granulés) - 8 octets
        print("\n--- Test avec fluide type 0 (granulés) - 8 octets ---")
        result = controller.get_setpoint_atech(fluid_type=0)
        if result:
            setpoint, seco, beco = result
            print(f"✓ Consigne: {setpoint}°C")
            print(f"✓ SECO: {seco}")
            print(f"✓ BECO: {beco} (ignoré pour granulés)")
        else:
            print("✗ Échec de la lecture")
        
        # Tester avec fluide type 1 - 8 octets
        print("\n--- Test avec fluide type 1 - 8 octets ---")
        result = controller.get_setpoint_atech(fluid_type=1)
        if result:
            setpoint, seco, beco = result
            print(f"✓ Consigne: {setpoint}°C")
            print(f"✓ SECO: {seco}")
            print(f"✓ BECO: {beco}")
        else:
            print("✗ Échec de la lecture")
        
        # Tester avec fluide type 2 - 2 octets
        print("\n--- Test avec fluide type 2 - 2 octets ---")
        result = controller.get_setpoint_atech(fluid_type=2)
        if result:
            setpoint, seco, beco = result
            print(f"✓ Consigne: {setpoint}°C")
            print(f"✓ SECO: {seco} (toujours 0 pour fluide type 2)")
            print(f"✓ BECO: {beco} (toujours False pour fluide type 2)")
        else:
            print("✗ Échec de la lecture")
        
        # Tester l'état complet
        print("\n--- Test de l'état complet ---")
        state = controller.get_state()
        print(f"✓ Statut: {state.get('status', 'N/A')}")
        print(f"✓ Température: {state.get('temperature', 'N/A')}°C")
        print(f"✓ Consigne: {state.get('setpoint', 'N/A')}°C")
        print(f"✓ Puissance: {state.get('power', 'N/A')}")
        print(f"✓ Niveau de puissance: {state.get('power_level', 'N/A')}")
        print(f"✓ Code d'erreur: {state.get('error_code', 'N/A')}")
        print(f"✓ Statut alarme: {state.get('alarm_status', 'N/A')}")
        print(f"✓ Timer activé: {state.get('timer_enabled', 'N/A')}")
        print(f"✓ SECO: {state.get('seco', 'N/A')}")
        print(f"✓ Type de fluide: {state.get('fluid_type', 'N/A')} (granulés)")
        
        # Afficher l'état final
        print("\n--- État final ---")
        state = controller.get_state()
        print(f"Consigne dans l'état: {state.get('setpoint', 'N/A')}°C")
        print(f"SECO dans l'état: {state.get('seco', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False
    finally:
        controller.disconnect()


if __name__ == '__main__':
    success = test_setpoint_atech()
    
    if success:
        print("\n✓ Tests terminés avec succès")
    else:
        print("\n✗ Tests échoués")
        sys.exit(1)
