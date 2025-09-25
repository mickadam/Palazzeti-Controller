#!/usr/bin/env python3
"""
Script de test simple pour la fonction get_setpoint_atech() sans Flask
"""
import sys
import os
import time
import threading
import serial

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from config import *
from frame import Frame, construct_read_frame, parse_setpoint_atech


class SimplePalazzettiController:
    """Version simplifiée du contrôleur sans Flask"""
    
    def __init__(self, use_mock=False):
        self.use_mock = use_mock
        self.serial_connection = None
        self.lock = threading.Lock()
        self.connected = False
        
    def connect(self) -> bool:
        """Établir la connexion au poêle"""
        print("Connexion au poêle Palazzetti...")
        
        if self.use_mock:
            self.connected = True
            print("✓ Connexion établie (mode mock)")
            return True
        else:
            try:
                self.serial_connection = serial.Serial(
                    port=SERIAL_PORT,
                    baudrate=BAUD_RATE,
                    timeout=TIMEOUT,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_TWO,
                )
                self.connected = True
                print("✓ Connexion établie")
                print(f"  Port série: {SERIAL_PORT}")
                print(f"  Configuration: {BAUD_RATE} bauds, 8N2")
                return True
            except Exception as e:
                print(f"✗ Échec de la connexion: {e}")
                self.connected = False
                return False
    
    def disconnect(self):
        """Fermer la connexion"""
        if self.connected:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            self.connected = False
            print("Connexion fermée")
    
    def wait_for_sync_frame(self, timeout=5):
        """Attendre la trame de synchronisation (0x00)"""
        if self.use_mock:
            return True
            
        if not self.serial_connection or not self.serial_connection.is_open:
            return False
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting >= 11:
                buffer = self.serial_connection.read(11)
                frame = Frame(buffer=buffer)
                if frame.get_id() == 0x00:
                    return True
        return False
    
    def synchro_trame(self, expected_id, timeout=5):
        """Attendre une trame avec un ID spécifique"""
        if self.use_mock:
            return self._get_mock_response(expected_id)
            
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting >= 11:
                buffer = self.serial_connection.read(11)
                frame = Frame(buffer=buffer)
                if frame.is_valid():
                    if frame.get_id() == expected_id:
                        return frame
        return None
    
    def send_read_command(self, address):
        """Envoyer une commande de lecture pour une adresse donnée"""
        if self.use_mock:
            return self._get_mock_response(address)
            
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
            
        with self.lock:
            try:
                read_frame = construct_read_frame(address)
                expected_id = read_frame.get_id()
                
                # Boucle de retry (max 2 tentatives)
                for attempt in range(2):
                    # Attendre la trame de synchronisation
                    sync_frame = self.synchro_trame(0x00, timeout=2)
                    if sync_frame:
                        self.serial_connection.write(read_frame.as_bytes())
                        self.serial_connection.flush()
                        
                        # Attendre la réponse
                        response = self.synchro_trame(expected_id, timeout=2)
                        if response:
                            return response
                
                return None
                    
            except Exception as e:
                return None
    
    def _get_mock_response(self, address):
        """Simuler une réponse pour le mode développement"""
        # Simuler les données de votre poêle
        if address == REGISTER_SETPOINT_ATECH_8BYTES:
            # Vos données réelles: 0x1C32-0x1C39
            mock_data = [12, 105, 0, 12, 130, 205, 80, 215] + [0x00]  # 9 bytes
            return Frame(frame_id=0x02, data=mock_data)
        else:
            # Réponse générique
            mock_data = [address[1], address[0]] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)
    
    def get_setpoint_atech(self, fluid_type=0):
        """
        Obtenir la consigne de température selon le code C iGetSetPointAtech()
        Utilise uniquement le fluide type 0 (granulés)
        """
        try:
            # Fluide type 0: lecture de 8 octets à 0x1C32
            frame = self.send_read_command(REGISTER_SETPOINT_ATECH_8BYTES)
            if frame and frame.is_valid():
                data = frame.get_data()
                setpoint, seco, beco = parse_setpoint_atech(data, fluid_type)
                
                print(f"Données brutes: {' '.join([f'{b:02X}' for b in data[:8]])}")
                print(f"Consigne Atech (fluide {fluid_type} - granulés): {setpoint}°C, SECO: {seco}")
                return setpoint, seco, beco
            
            print(f"Impossible de lire la consigne pour le fluide {fluid_type}")
            return None
            
        except Exception as e:
            print(f"Erreur lors de la lecture de la consigne Atech: {e}")
            return None


def test_setpoint_atech():
    """Tester la lecture de la consigne selon le code C"""
    print("Test de la fonction get_setpoint_atech() - Version simplifiée")
    print("=" * 60)
    
    # Créer le contrôleur
    controller = SimplePalazzettiController(use_mock=False)  # Mode réel
    
    try:
        # Se connecter
        if not controller.connect():
            print("✗ Impossible de se connecter au poêle")
            return False
        
        print("✓ Connexion établie")
        
        # Tester avec fluide type 0 (granulés)
        print("\n--- Test avec fluide type 0 (granulés) ---")
        result = controller.get_setpoint_atech(fluid_type=0)
        if result:
            setpoint, seco, beco = result
            print(f"✓ Consigne: {setpoint}°C")
            print(f"✓ SECO: {seco}")
            print(f"✓ BECO: {beco} (ignoré pour granulés)")
            
            # Vérifier le calcul
            print(f"\n--- Vérification du calcul ---")
            print(f"Données brutes: SECO=12, SETP=105")
            print(f"SECO converti: 12 ÷ 10 = {12/10}")
            print(f"SETP converti: 105 ÷ 5 = {105/5}")
            print(f"Résultat attendu: {105/5}°C")
            
        else:
            print("✗ Échec de la lecture")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False
    finally:
        controller.disconnect()


def test_with_register_search():
    """Tester avec le script register_search.py"""
    print("\n" + "=" * 60)
    print("Test avec register_search.py")
    print("=" * 60)
    
    print("Commande pour fluide type 0 (granulés - 8 octets):")
    print("python3 register_search.py --start 1C32 --end 1C39 --bytes 1 --show-all")
    print("\nCela devrait afficher les 8 octets de données pour fluide type 0")
    print("Avec vos données précédentes:")
    print("0x1C32: 12 (SECO)")
    print("0x1C33: 105 (SETP - consigne brute)")
    print("0x1C34: 0")
    print("0x1C35: 12 (BECO - ignoré pour granulés)")
    print("0x1C36-0x1C39: autres octets")
    print("\nConsigne calculée: 105 ÷ 5 = 21.0°C (conversion pour granulés)")


if __name__ == '__main__':
    success = test_setpoint_atech()
    test_with_register_search()
    
    if success:
        print("\n✓ Tests terminés avec succès")
    else:
        print("\n✗ Tests échoués")
        sys.exit(1)
