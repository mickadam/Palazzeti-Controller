#!/usr/bin/env python3
"""
Script pour lire les registres de 1C00 à 207C et afficher les valeurs en format int16
"""
import sys
import os
import time
from typing import List, Tuple, Optional

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from config import *
from frame import Frame, construct_read_frame
import serial
import threading


class RegisterRangeReader:
    """Lecteur de registres pour une plage d'adresses"""
    
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
            print("  Mode développement (mock) activé")
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
            except Exception as e:
                print(f"✗ Échec de la connexion: {e}")
                self.connected = False
            
        return self.connected
    
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
        """
        Attendre une trame avec un ID spécifique
        
        Args:
            expected_id: ID de trame attendu
            timeout: Timeout en secondes
        
        Returns:
            Frame ou None si timeout
        """
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
            # Pas de sleep pour être plus réactif
        
        return None
    
    def send_read_command(self, address):
        """
        Envoyer une commande de lecture pour une adresse donnée
        """
        if self.use_mock:
            return self._get_mock_response(address)
            
        if not self.serial_connection or not self.serial_connection.is_open:
            print("✗ Connexion série non disponible")
            return None
            
        with self.lock:
            try:
                # Construire la trame de lecture
                read_frame = construct_read_frame(address)
                expected_id = read_frame.get_id()
                
                # Boucle de retry (max 3 tentatives pour éviter les timeouts)
                for attempt in range(3):
                    # 1. Attendre la trame de synchronisation (0x00)
                    sync_frame = self.synchro_trame(0x00, timeout=3)
                    if sync_frame:
                        # 2. Envoyer la commande de lecture
                        self.serial_connection.write(read_frame.as_bytes())
                        self.serial_connection.flush()
                        
                        # 3. Attendre la réponse avec le même ID
                        response = self.synchro_trame(expected_id, timeout=3)
                        if response:
                            return response
                
                return None
                    
            except Exception as e:
                print(f"✗ Erreur lors de l'envoi de commande de lecture: {e}")
                return None
    
    def _get_mock_response(self, address):
        """Simuler une réponse pour le mode développement"""
        # Simuler des données aléatoires pour les tests
        import random
        mock_data = [address[1], address[0]]  # Adresse LSB, MSB
        # Ajouter des données simulées (2 bytes pour int16)
        mock_data.extend([random.randint(0, 255), random.randint(0, 255)])
        # Compléter avec des zéros
        while len(mock_data) < 9:
            mock_data.append(0x00)
        return Frame(frame_id=0x02, data=mock_data)
    
    def read_register_range(self, start_addr: int, end_addr: int) -> List[Tuple[int, int, Optional[int]]]:
        """
        Lire une plage de registres
        
        Args:
            start_addr: Adresse de début (ex: 0x1C00)
            end_addr: Adresse de fin (ex: 0x207C)
        
        Returns:
            Liste de tuples (adresse, valeur_int16, données_brutes)
        """
        if not self.connected:
            print("✗ Non connecté au poêle")
            return []
        
        results = []
        total_registers = end_addr - start_addr + 1
        current = 0
        
        print(f"\nLecture des registres de 0x{start_addr:04X} à 0x{end_addr:04X}")
        print(f"Total: {total_registers} registres")
        print("-" * 60)
        
        for addr in range(start_addr, end_addr + 1):
            current += 1
            # Convertir l'adresse en format [MSB, LSB]
            address_bytes = [(addr >> 8) & 0xFF, addr & 0xFF]
            
            print(f"[{current:3d}/{total_registers}] Lecture 0x{addr:04X}...", end=" ")
            
            try:
                # Envoyer la commande de lecture
                frame = self.send_read_command(address_bytes)
                
                if frame is None:
                    print("✗ Pas de réponse")
                    results.append((addr, None, None))
                    continue
                
                if not frame.is_valid():
                    print("✗ Trame invalide")
                    results.append((addr, None, None))
                    continue
                
                # Extraire les données (après l'adresse)
                data = frame.get_data()
                if len(data) >= 4:  # Adresse (2 bytes) + données (2 bytes minimum)
                    # data[0] = adresse LSB, data[1] = adresse MSB
                    # data[2] = données poids faible, data[3] = données poids fort
                    if len(data) >= 4:
                        # Convertir en int16: data[2] (poids faible) + data[3] (poids fort)
                        value_int16 = data[2] | (data[3] << 8)
                        print(f"✓ {value_int16:5d} (0x{value_int16:04X})")
                        results.append((addr, value_int16, data[2:4]))
                    else:
                        print("✗ Données insuffisantes")
                        results.append((addr, None, None))
                else:
                    print("✗ Données insuffisantes")
                    results.append((addr, None, None))
                
                # Pause entre les lectures pour éviter de surcharger le poêle
                time.sleep(0.1)
                
            except Exception as e:
                print(f"✗ Erreur: {e}")
                results.append((addr, None, None))
        
        return results
    
    def display_results_table(self, results: List[Tuple[int, int, Optional[int]]]):
        """Afficher les résultats dans un tableau formaté"""
        print("\n" + "=" * 80)
        print("TABLEAU DES VALEURS LUES")
        print("=" * 80)
        print(f"{'Adresse':<10} {'Hex':<8} {'Int16':<8} {'Données':<12} {'Statut'}")
        print("-" * 80)
        
        success_count = 0
        for addr, value_int16, raw_data in results:
            addr_str = f"0x{addr:04X}"
            hex_str = f"0x{value_int16:04X}" if value_int16 is not None else "N/A"
            int16_str = str(value_int16) if value_int16 is not None else "N/A"
            data_str = f"{raw_data[0]:02X} {raw_data[1]:02X}" if raw_data else "N/A"
            status = "✓" if value_int16 is not None else "✗"
            
            print(f"{addr_str:<10} {hex_str:<8} {int16_str:<8} {data_str:<12} {status}")
            
            if value_int16 is not None:
                success_count += 1
        
        print("-" * 80)
        print(f"Résumé: {success_count}/{len(results)} registres lus avec succès")
        print("=" * 80)


def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lecteur de registres Palazzetti (plage 1C00-207C)')
    parser.add_argument('--mock', action='store_true', help='Utiliser le mode mock (développement)')
    parser.add_argument('--start', type=str, default='1C00', help='Adresse de début (hex, défaut: 1C00)')
    parser.add_argument('--end', type=str, default='207C', help='Adresse de fin (hex, défaut: 207C)')
    
    args = parser.parse_args()
    
    # Convertir les adresses hex en int
    try:
        start_addr = int(args.start, 16)
        end_addr = int(args.end, 16)
    except ValueError:
        print("Erreur: Les adresses doivent être en format hexadécimal (ex: 1C00)")
        return 1
    
    if start_addr > end_addr:
        print("Erreur: L'adresse de début doit être inférieure à l'adresse de fin")
        return 1
    
    # Créer le lecteur
    reader = RegisterRangeReader(use_mock=args.mock)
    
    try:
        # Se connecter
        if not reader.connect():
            print("Impossible de se connecter au poêle")
            return 1
        
        # Lire la plage de registres
        results = reader.read_register_range(start_addr, end_addr)
        
        # Afficher le tableau des résultats
        reader.display_results_table(results)
        
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur")
    finally:
        reader.disconnect()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
