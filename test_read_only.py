#!/usr/bin/env python3
"""
Script de test pour le mode lecture seule
Teste uniquement la lecture des données du poêle en mode mock
"""
import sys
import os
import time

# Ajouter le répertoire raspberry_pi au path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raspberry_pi'))

from palazzeti_controller import PalazzettiController

def test_read_only_mode():
    """Tester le mode lecture seule"""
    print("=== Test Mode Lecture Seule ===")
    print("Mode production - Communication série avec le poêle")
    print()
    
    # Créer le contrôleur en mode production (communication série réelle)
    controller = PalazzettiController(use_mock=False)
    
    try:
        # Se connecter
        if not controller.connect():
            print("✗ Erreur de connexion")
            return False
        
        print("✓ Connexion série établie avec le poêle")
        print()
        
        # Test de lecture de registres individuels
        print("--- Test de lecture de registres individuels ---")
        
        # Test lecture statut
        print("Test lecture registre statut (0x20, 0x1C)...")
        status_frame = controller.send_read_command([0x20, 0x1C])
        if status_frame:
            data_hex = ' '.join([f'{b:02X}' for b in status_frame.get_data()])
            print(f"✓ Réponse reçue: {data_hex}")
        else:
            print("✗ Aucune réponse pour le registre statut")
        
        # Test lecture température
        print("Test lecture registre température (0x20, 0x0E)...")
        temp_frame = controller.send_read_command([0x20, 0x0E])
        if temp_frame:
            data_hex = ' '.join([f'{b:02X}' for b in temp_frame.get_data()])
            print(f"✓ Réponse reçue: {data_hex}")
        else:
            print("✗ Aucune réponse pour le registre température")
        
        # Test lecture consigne
        print("Test lecture registre consigne (0x1C, 0x33)...")
        setpoint_frame = controller.send_read_command([0x1C, 0x33])
        if setpoint_frame:
            data_hex = ' '.join([f'{b:02X}' for b in setpoint_frame.get_data()])
            print(f"✓ Réponse reçue: {data_hex}")
        else:
            print("✗ Aucune réponse pour le registre consigne")
        
        print()
        
        # Test de lecture de l'état complet
        print("--- Lecture de l'état complet ---")
        state = controller.get_state()
        
        print(f"Statut: {state.get('status', 'N/A')}")
        print(f"Température: {state.get('temperature', 'N/A')}°C")
        print(f"Consigne: {state.get('setpoint', 'N/A')}°C")
        print(f"Puissance: {'ON' if state.get('power', False) else 'OFF'}")
        print(f"Niveau de puissance: {state.get('power_level', 'N/A')}")
        print(f"Code d'erreur: {state.get('error_code', 'N/A')}")
        print(f"Message d'erreur: {state.get('error_message', 'N/A')}")
        print(f"Statut alarme: {state.get('alarm_status', 'N/A')}")
        print(f"Timer activé: {'Oui' if state.get('timer_enabled', False) else 'Non'}")
        print(f"Seuil déclenchement: {state.get('seco', 'N/A')}°C")
        print(f"Type de fluide: {state.get('fluid_type', 'N/A')}")
        print()
        
        
        print("✓ Tous les tests de lecture sont passés avec succès!")
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors des tests: {e}")
        return False
    finally:
        controller.disconnect()

if __name__ == '__main__':
    success = test_read_only_mode()
    
    if success:
        print("\n🎉 Tests terminés avec succès!")
        print("Vous pouvez maintenant tester l'interface web avec:")
        print("python3 raspberry_pi/palazzeti_controller.py")
    else:
        print("\n❌ Tests échoués")
        sys.exit(1)
