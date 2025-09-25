#!/usr/bin/env python3
"""
Script de diagnostic avancé pour analyser la communication avec le poêle Palazzetti
"""
import sys
import os
import time
import serial

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from config import SERIAL_PORT, BAUD_RATE, TIMEOUT
from frame import Frame, construct_read_frame, construct_write_frame


def analyze_incoming_frames(duration=30):
    """Analyser les trames reçues pendant une durée donnée"""
    print(f"=== Analyse des trames reçues pendant {duration} secondes ===")
    
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO
        )
        
        print(f"Connexion établie sur {SERIAL_PORT}")
        print("Attente des trames...")
        
        start_time = time.time()
        frame_count = 0
        id_counts = {}
        
        while time.time() - start_time < duration:
            if ser.in_waiting >= 11:
                buffer = ser.read(11)
                frame = Frame(buffer=buffer)
                frame_count += 1
                
                # Compter les IDs
                frame_id = frame.get_id()
                id_counts[frame_id] = id_counts.get(frame_id, 0) + 1
                
                # Afficher la trame
                print(f"Trame {frame_count}: {frame}")
                
                # Analyser le contenu
                data = frame.get_data()
                if len(data) >= 3:
                    print(f"  Adresse: 0x{data[1]:02X} 0x{data[0]:02X}")
                    if len(data) >= 4:
                        print(f"  Données: {data[2:4]}")
        
        print(f"\n=== Résumé ===")
        print(f"Total trames reçues: {frame_count}")
        print("Répartition par ID:")
        for frame_id, count in sorted(id_counts.items()):
            print(f"  ID 0x{frame_id:02X}: {count} trames")
        
        ser.close()
        
    except Exception as e:
        print(f"Erreur: {e}")


def test_read_with_detailed_logging():
    """Tester la lecture avec un logging détaillé"""
    print("\n=== Test de lecture avec logging détaillé ===")
    
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO
        )
        
        # Attendre une trame de synchronisation
        print("Attente de la trame de synchronisation...")
        sync_received = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            if ser.in_waiting >= 11:
                buffer = ser.read(11)
                frame = Frame(buffer=buffer)
                print(f"Trame reçue: {frame}")
                
                if frame.get_id() == 0x00:
                    print("✓ Trame de synchronisation reçue")
                    sync_received = True
                    break
        
        if not sync_received:
            print("✗ Pas de trame de synchronisation")
            ser.close()
            return
        
        # Attendre un peu plus longtemps
        print("Attente de 2 secondes avant l'envoi...")
        time.sleep(2)
        
        # Envoyer la commande de lecture
        print("Envoi de la commande de lecture de la température...")
        read_frame = construct_read_frame([0x20, 0x0E])  # Température
        print(f"Trame envoyée: {read_frame}")
        print(f"Bytes envoyés: {' '.join([f'{b:02X}' for b in read_frame.as_bytes()])}")
        
        ser.write(read_frame.as_bytes())
        ser.flush()
        
        # Attendre la réponse avec logging détaillé
        print("Attente de la réponse...")
        response_received = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            if ser.in_waiting >= 11:
                buffer = ser.read(11)
                frame = Frame(buffer=buffer)
                print(f"Trame reçue: {frame}")
                
                if frame.get_id() == 0x02 and frame.is_valid():
                    print("✓ Réponse valide reçue!")
                    response_received = True
                    break
                else:
                    print(f"  ID: 0x{frame.get_id():02X}, Valid: {frame.is_valid()}")
        
        if not response_received:
            print("✗ Pas de réponse valide")
        
        ser.close()
        
    except Exception as e:
        print(f"Erreur: {e}")


def test_different_read_commands():
    """Tester différentes commandes de lecture"""
    print("\n=== Test de différentes commandes de lecture ===")
    
    # Adresses à tester
    addresses = [
        ([0x20, 0x0E], "Température"),
        ([0x20, 0x1C], "Statut"),
        ([0x20, 0x0F], "Consigne"),
        ([0x20, 0x1D], "Puissance"),
    ]
    
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO
        )
        
        for address, name in addresses:
            print(f"\n--- Test: {name} (0x{address[0]:02X} 0x{address[1]:02X}) ---")
            
            # Attendre synchronisation
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
                print("✗ Pas de synchronisation")
                continue
            
            # Envoyer commande
            read_frame = construct_read_frame(address)
            print(f"Envoi: {read_frame}")
            ser.write(read_frame.as_bytes())
            ser.flush()
            
            # Attendre réponse
            response_received = False
            start_time = time.time()
            
            while time.time() - start_time < 5:
                if ser.in_waiting >= 11:
                    buffer = ser.read(11)
                    frame = Frame(buffer=buffer)
                    print(f"Réponse: {frame}")
                    
                    if frame.get_id() == 0x02 and frame.is_valid():
                        print("✓ Réponse valide!")
                        response_received = True
                        break
            
            if not response_received:
                print("✗ Pas de réponse")
            
            time.sleep(1)  # Pause entre les tests
        
        ser.close()
        
    except Exception as e:
        print(f"Erreur: {e}")


def main():
    """Fonction principale"""
    print("Diagnostic avancé de communication Palazzetti")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--analyze":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            analyze_incoming_frames(duration)
        elif sys.argv[1] == "--test-read":
            test_read_with_detailed_logging()
        elif sys.argv[1] == "--test-all":
            test_different_read_commands()
        else:
            print("Usage:")
            print("  --analyze [duration]  - Analyser les trames reçues")
            print("  --test-read          - Tester la lecture avec logging")
            print("  --test-all           - Tester toutes les commandes")
    else:
        # Par défaut, analyser les trames
        analyze_incoming_frames(30)


if __name__ == '__main__':
    main()
