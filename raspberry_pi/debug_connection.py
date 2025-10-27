#!/usr/bin/env python3
"""
Script de debug pour diagnostiquer les problèmes de connexion
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from palazzetti_controller import PalazzettiController
from config import *

def test_connection():
    """Tester la connexion étape par étape"""
    print("🔍 Test de connexion Palazzetti")
    print("=" * 50)
    
    try:
        # 1. Créer le contrôleur
        print("1. Création du contrôleur...")
        controller = PalazzettiController()
        print("   ✅ Contrôleur créé")
        
        # 2. Tester la connexion
        print("2. Test de connexion...")
        if controller.connect():
            print("   ✅ Connexion établie")
        else:
            print("   ❌ Échec de la connexion")
            return
        
        # 3. Tester is_connected()
        print("3. Test de is_connected()...")
        is_conn = controller.is_connected()
        print(f"   {'✅' if is_conn else '❌'} is_connected() = {is_conn}")
        
        # 4. Tester get_state()
        print("4. Test de get_state()...")
        try:
            state = controller.get_state()
            if state:
                print(f"   ✅ get_state() réussi - connected: {state.get('connected', 'N/A')}, synchronized: {state.get('synchronized', 'N/A')}")
                print(f"   📊 Température: {state.get('temperature', 'N/A')}°C")
                print(f"   📊 Consigne: {state.get('setpoint', 'N/A')}°C")
            else:
                print("   ❌ get_state() retourne None")
        except Exception as e:
            print(f"   ❌ Erreur get_state(): {e}")
        
        # 5. Tester get_pellet_consumption()
        print("5. Test de get_pellet_consumption()...")
        try:
            consumption = controller.get_pellet_consumption()
            if consumption is not None:
                print(f"   ✅ Consommation lue: {consumption} kg")
            else:
                print("   ❌ Consommation non lue")
        except Exception as e:
            print(f"   ❌ Erreur consommation: {e}")
        
        # 6. Test de l'API /api/state
        print("6. Test de l'API /api/state...")
        try:
            import requests
            response = requests.get("http://localhost:5000/api/state", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API /api/state OK - connected: {data.get('connected', 'N/A')}")
                print(f"   📊 Message: {data.get('error_message', 'N/A')}")
            else:
                print(f"   ❌ API /api/state échouée - Code: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur API: {e}")
        
        # 7. Fermer la connexion
        print("7. Fermeture de la connexion...")
        controller.disconnect()
        print("   ✅ Connexion fermée")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
