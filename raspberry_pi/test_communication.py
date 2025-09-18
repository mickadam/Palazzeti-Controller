"""
Scripts de test pour la communication avec le poêle Palazzetti
"""
import serial
import time
import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import SERIAL_PORT, BAUD_RATE, TIMEOUT, REGISTER_STATUS, REGISTER_TEMPERATURE, REGISTER_SETPOINT
from frame import Frame, construct_read_frame, construct_write_frame, parse_temperature, parse_status


def list_serial_ports():
    """Lister les ports série disponibles"""
    import serial.tools.list_ports
    
    print("=== Ports série disponibles ===")
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("Aucun port série trouvé")
        return []
    
    for port in ports:
        print(f"- {port.device}: {port.description}")
    
    return [port.device for port in ports]


def test_serial_connection():
    """Tester la connexion série de base"""
    print("\n=== Test de connexion série ===")
    
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO
        )
        
        print(f"✓ Connexion établie sur {SERIAL_PORT}")
        print(f"  - Baudrate: {BAUD_RATE}")
        print(f"  - Timeout: {TIMEOUT}s")
        print(f"  - Configuration: 8N2")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"✗ Erreur de connexion: {e}")
        return False


def test_sync_frame():
    """Tester la réception de la trame de synchronisation"""
    print("\n=== Test de la trame de synchronisation ===")
    
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO
        )
        
        print("Attente de la trame de synchronisation (0x00)...")
        print("(Cette trame est envoyée périodiquement par le poêle)")
        
        start_time = time.time()
        sync_received = False
        
        while time.time() - start_time < 10:  # Attendre 10 secondes max
            if ser.in_waiting >= 11:
                buffer = ser.read(11)
                frame = Frame(buffer=buffer)
                
                print(f"Trame reçue: {frame}")
                
                if frame.get_id() == 0x00:
                    print("✓ Trame de synchronisation reçue!")
                    sync_received = True
                    break
                else:
                    print(f"  ID reçu: 0x{frame.get_id():02X} (attendu: 0x00)")
        
        if not sync_received:
            print("✗ Aucune trame de synchronisation reçue dans les 10 secondes")
            print("  Vérifiez que le poêle est allumé et connecté")
        
        ser.close()
        return sync_received
        
    except Exception as e:
        print(f"✗ Erreur lors du test de synchronisation: {e}")
        return False


def test_read_status():
    """Tester la lecture du statut du poêle"""
    print("\n=== Test de lecture du statut ===")
    
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO
        )
        
        # Attendre la trame de synchronisation
        print("Attente de la trame de synchronisation...")
        sync_received = False
        start_time = time.time()
        
        while time.time() - start_time < 5:
            if ser.in_waiting >= 11:
                buffer = ser.read(11)
                frame = Frame(buffer=buffer)
                if frame.get_id() == 0x00:
                    sync_received = True
                    break
        
        if not sync_received:
            print("✗ Pas de trame de synchronisation")
            ser.close()
            return False
        
        # Envoyer la commande de lecture du statut
        print("Envoi de la commande de lecture du statut...")
        read_frame = construct_read_frame(REGISTER_STATUS)
        print(f"Trame de lecture: {read_frame}")
        
        ser.write(read_frame.as_bytes())
        ser.flush()
        
        # Attendre la réponse
        print("Attente de la réponse...")
        response_received = False
        start_time = time.time()
        
        while time.time() - start_time < 5:
            if ser.in_waiting >= 11:
                buffer = ser.read(11)
                frame = Frame(buffer=buffer)
                
                if frame.get_id() == 0x01 and frame.is_valid():
                    print(f"✓ Réponse reçue: {frame}")
                    
                    # Parser le statut
                    status_code, status_name, power_on = parse_status(frame.get_data())
                    print(f"  Statut: {status_name} (code: 0x{status_code:02X})")
                    print(f"  Alimenté: {'Oui' if power_on else 'Non'}")
                    
                    response_received = True
                    break
        
        if not response_received:
            print("✗ Pas de réponse valide")
        
        ser.close()
        return response_received
        
    except Exception as e:
        print(f"✗ Erreur lors du test de lecture: {e}")
        return False


def test_read_temperature():
    """Tester la lecture de la température"""
    print("\n=== Test de lecture de la température ===")
    
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO
        )
        
        # Attendre la trame de synchronisation
        print("Attente de la trame de synchronisation...")
        sync_received = False
        start_time = time.time()
        
        while time.time() - start_time < 5:
            if ser.in_waiting >= 11:
                buffer = ser.read(11)
                frame = Frame(buffer=buffer)
                if frame.get_id() == 0x00:
                    sync_received = True
                    break
        
        if not sync_received:
            print("✗ Pas de trame de synchronisation")
            ser.close()
            return False
        
        # Envoyer la commande de lecture de la température
        print("Envoi de la commande de lecture de la température...")
        read_frame = construct_read_frame(REGISTER_TEMPERATURE)
        print(f"Trame de lecture: {read_frame}")
        
        ser.write(read_frame.as_bytes())
        ser.flush()
        
        # Attendre la réponse
        print("Attente de la réponse...")
        response_received = False
        start_time = time.time()
        
        while time.time() - start_time < 5:
            if ser.in_waiting >= 11:
                buffer = ser.read(11)
                frame = Frame(buffer=buffer)
                
                if frame.get_id() == 0x01 and frame.is_valid():
                    print(f"✓ Réponse reçue: {frame}")
                    
                    # Parser la température
                    temperature = parse_temperature(frame.get_data())
                    print(f"  Température: {temperature}°C")
                    
                    response_received = True
                    break
        
        if not response_received:
            print("✗ Pas de réponse valide")
        
        ser.close()
        return response_received
        
    except Exception as e:
        print(f"✗ Erreur lors du test de lecture de température: {e}")
        return False


def test_palazzetti_communication():
    """Test complet de communication avec le poêle"""
    print("\n=== Test complet de communication Palazzetti ===")
    
    # Lister les ports disponibles
    ports = list_serial_ports()
    if not ports:
        print("Aucun port série disponible pour les tests")
        return False
    
    # Vérifier que le port configuré est disponible
    if SERIAL_PORT not in ports:
        print(f"⚠️  Port configuré {SERIAL_PORT} non trouvé dans la liste")
        print("Ports disponibles:", ", ".join(ports))
        print(f"Utilisation du premier port disponible: {ports[0]}")
        # Note: On ne change pas SERIAL_PORT ici, c'est juste informatif
    
    # Tests séquentiels
    tests = [
        ("Connexion série", test_serial_connection),
        ("Trame de synchronisation", test_sync_frame),
        ("Lecture du statut", test_read_status),
        ("Lecture de la température", test_read_temperature),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Test: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Erreur inattendue: {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    print(f"\n{'='*50}")
    print("RÉSUMÉ DES TESTS")
    print('='*50)
    
    success_count = 0
    for test_name, result in results:
        status = "✓ RÉUSSI" if result else "✗ ÉCHEC"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\nRésultat global: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("🎉 Tous les tests sont passés! La communication fonctionne correctement.")
        return True
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la connexion et la configuration.")
        return False


def main():
    """Fonction principale"""
    print("Test de communication Palazzetti")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--ports":
            list_serial_ports()
            return
        elif sys.argv[1] == "--sync":
            test_sync_frame()
            return
        elif sys.argv[1] == "--status":
            test_read_status()
            return
        elif sys.argv[1] == "--temp":
            test_read_temperature()
            return
    
    # Test complet par défaut
    test_palazzetti_communication()


if __name__ == '__main__':
    main()

