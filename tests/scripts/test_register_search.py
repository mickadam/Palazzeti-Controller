#!/usr/bin/env python3
"""
Script de test pour register_search.py
"""
import subprocess
import sys
import os

def test_script():
    """Tester le script avec différentes options"""
    
    script_path = os.path.join(os.path.dirname(__file__), 'register_search.py')
    
    if not os.path.exists(script_path):
        print(f"Erreur: Le script {script_path} n'existe pas")
        return False
    
    print("Test du script register_search.py")
    print("=" * 50)
    
    # Test 1: Aide
    print("\n1. Test de l'aide...")
    try:
        result = subprocess.run([sys.executable, script_path, '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Aide affichée correctement")
        else:
            print(f"✗ Erreur aide: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Erreur test aide: {e}")
        return False
    
    # Test 2: Mode mock avec petite plage
    print("\n2. Test mode mock (petite plage)...")
    try:
        result = subprocess.run([sys.executable, script_path, '--start', '1C00', '--end', '1C05', 
                               '--mock', '--bytes', '1'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Mode mock fonctionne")
            print("Sortie:", result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
        else:
            print(f"✗ Erreur mode mock: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Erreur test mock: {e}")
        return False
    
    # Test 3: Recherche avec mode mock
    print("\n3. Test recherche avec mode mock...")
    try:
        result = subprocess.run([sys.executable, script_path, '--start', '1C00', '--end', '1C0F', 
                               '--search', '22', '--bytes', '1', '--mock'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Recherche mock fonctionne")
        else:
            print(f"✗ Erreur recherche mock: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Erreur test recherche: {e}")
        return False
    
    print("\n✓ Tous les tests sont passés !")
    return True

if __name__ == '__main__':
    success = test_script()
    sys.exit(0 if success else 1)
