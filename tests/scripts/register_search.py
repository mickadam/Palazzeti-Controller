#!/usr/bin/env python3
"""
Script flexible pour lire et rechercher dans les registres Palazzetti
Permet de choisir l'adresse de début, l'adresse de fin, la valeur recherchée et le nombre d'octets
"""
import sys
import os
import time
import argparse
from typing import List, Tuple, Optional, Union

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from config import *
from frame import Frame, construct_read_frame
import serial
import threading


class FlexibleRegisterReader:
    """Lecteur flexible de registres avec recherche"""
    
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
    
    def send_read_command(self, address, debug=False):
        """Envoyer une commande de lecture pour une adresse donnée"""
        if self.use_mock:
            return self._get_mock_response(address)
            
        if not self.serial_connection or not self.serial_connection.is_open:
            if debug:
                print("    ✗ Connexion série fermée")
            return None
            
        with self.lock:
            try:
                read_frame = construct_read_frame(address)
                expected_id = read_frame.get_id()
                
                # Boucle de retry (max 2 tentatives pour éviter les blocages)
                for attempt in range(2):
                    # Attendre la trame de synchronisation avec timeout plus court
                    sync_frame = self.synchro_trame(0x00, timeout=2)
                    if sync_frame:
                        self.serial_connection.write(read_frame.as_bytes())
                        self.serial_connection.flush()
                        
                        # Attendre la réponse avec timeout plus court
                        response = self.synchro_trame(expected_id, timeout=2)
                        if response:
                            return response
                return None
                    
            except Exception as e:
                if debug:
                    print(f"    ✗ Exception: {e}")
                return None
    
    def _get_mock_response(self, address):
        """Simuler une réponse pour le mode développement"""
        import random
        mock_data = [address[1], address[0]]  # Adresse LSB, MSB
        
        # Simuler des données aléatoires
        if self.use_mock:
            # Pour la démo, utiliser des valeurs prévisibles basées sur l'adresse
            base_value = (address[0] << 8) | address[1]
            mock_data.extend([base_value & 0xFF, (base_value >> 8) & 0xFF])
        else:
            mock_data.extend([random.randint(0, 255), random.randint(0, 255)])
        
        # Compléter avec des zéros
        while len(mock_data) < 9:
            mock_data.append(0x00)
        return Frame(frame_id=0x02, data=mock_data)
    
    def read_register(self, address: int, bytes_count: int = 2, debug: bool = False) -> Tuple[Optional[int], Optional[List[int]]]:
        """
        Lire un registre spécifique
        
        Args:
            address: Adresse du registre
            bytes_count: Nombre d'octets à lire (1 ou 2)
            debug: Afficher les détails de debug
        
        Returns:
            Tuple (valeur, données_brutes)
        """
        if not self.connected:
            return None, None
        
        # Convertir l'adresse en format [MSB, LSB]
        address_bytes = [(address >> 8) & 0xFF, address & 0xFF]
        
        try:
            frame = self.send_read_command(address_bytes, debug)
            
            if frame is None or not frame.is_valid():
                return None, None
            
            data = frame.get_data()
            if len(data) < bytes_count:  # Juste les données, pas d'adresse
                return None, None
            
            # Extraire les données selon le nombre d'octets
            if bytes_count == 1:
                # 1 octet: data[0]
                value = data[0]
                raw_data = [data[0]]
            else:
                # 2 octets: data[0] (poids faible) + data[1] (poids fort)
                value = data[0] | (data[1] << 8)
                raw_data = [data[0], data[1]]
            
            return value, raw_data
            
        except Exception as e:
            return None, None
    
    def search_value_in_range(self, start_addr: int, end_addr: int, search_value: int, 
                            bytes_count: int = 2, exact_match: bool = True, debug: bool = False) -> List[Tuple[int, int, List[int]]]:
        """
        Rechercher une valeur dans une plage de registres
        
        Args:
            start_addr: Adresse de début
            end_addr: Adresse de fin
            search_value: Valeur à rechercher
            bytes_count: Nombre d'octets (1 ou 2)
            exact_match: True pour correspondance exacte, False pour correspondance partielle
        
        Returns:
            Liste des correspondances (adresse, valeur, données_brutes)
        """
        if not self.connected:
            print("✗ Non connecté au poêle")
            return []
        
        matches = []
        total_registers = end_addr - start_addr + 1
        current = 0
        
        print(f"\nRecherche de la valeur {search_value} dans la plage 0x{start_addr:04X}-0x{end_addr:04X}")
        print(f"Mode: {'exact' if exact_match else 'partiel'}, Octets: {bytes_count}")
        print(f"Total: {total_registers} registres à vérifier")
        print("-" * 60)
        
        for addr in range(start_addr, end_addr + 1):
            current += 1
            
            # Afficher la progression
            if current % 20 == 0 or current == total_registers:
                print(f"Progression: {current}/{total_registers} ({current/total_registers*100:.1f}%)")
            
            value, raw_data = self.read_register(addr, bytes_count, debug=debug)
            
            # Affichage compact en temps réel si debug activé
            if debug and value is not None:
                hex_str = f"0x{value:02X}" if bytes_count == 1 else f"0x{value:04X}"
                data_str = ' '.join([f"{b:02X}" for b in raw_data])
                print(f"  0x{addr:04X}: {value:3d} ({hex_str}) [{data_str}]")
            elif debug and value is None:
                print(f"  0x{addr:04X}: --- (échec lecture)")
            
            if value is not None:
                match = False
                if exact_match:
                    match = (value == search_value)
                else:
                    # Correspondance partielle: vérifier si la valeur recherchée est contenue
                    if bytes_count == 1:
                        match = (search_value & 0xFF) == value
                    else:
                        # Pour 2 octets, vérifier si la valeur recherchée correspond aux octets
                        if isinstance(search_value, int):
                            # Si search_value est un int, vérifier la correspondance complète
                            match = value == search_value
                        else:
                            # Si c'est une liste d'octets, vérifier chaque octet
                            match = all(raw_data[i] == search_value[i] for i in range(min(len(raw_data), len(search_value))))
                
                if match:
                    matches.append((addr, value, raw_data))
                    print(f"  ★ CORRESPONDANCE à 0x{addr:04X}: {value} (0x{value:04X})")
            
            # Pause entre les lectures
            time.sleep(0.1)
        
        return matches
    
    def read_range(self, start_addr: int, end_addr: int, bytes_count: int = 2, debug: bool = False) -> List[Tuple[int, int, List[int]]]:
        """
        Lire une plage de registres
        
        Args:
            start_addr: Adresse de début
            end_addr: Adresse de fin
            bytes_count: Nombre d'octets à lire (1 ou 2)
        
        Returns:
            Liste des résultats (adresse, valeur, données_brutes)
        """
        if not self.connected:
            print("✗ Non connecté au poêle")
            return []
        
        results = []
        total_registers = end_addr - start_addr + 1
        current = 0
        
        print(f"\nLecture des registres de 0x{start_addr:04X} à 0x{end_addr:04X}")
        print(f"Octets par registre: {bytes_count}")
        print(f"Total: {total_registers} registres")
        print("-" * 60)
        
        for addr in range(start_addr, end_addr + 1):
            current += 1
            
            if current % 20 == 0 or current == total_registers:
                print(f"Progression: {current}/{total_registers} ({current/total_registers*100:.1f}%)")
            
            value, raw_data = self.read_register(addr, bytes_count, debug=debug)
            results.append((addr, value, raw_data))
            
            # Pause entre les lectures
            time.sleep(0.05)
        
        return results
    
    def display_results(self, results: List[Tuple[int, int, List[int]]], bytes_count: int = 2, 
                       show_all: bool = True, search_value: Optional[int] = None):
        """Afficher les résultats dans un tableau formaté"""
        if not results:
            print("Aucun résultat à afficher")
            return
        
        print("\n" + "=" * 80)
        if search_value is not None:
            print(f"RÉSULTATS DE LA RECHERCHE (valeur: {search_value})")
        else:
            print("RÉSULTATS DE LA LECTURE")
        print("=" * 80)
        
        if bytes_count == 1:
            print(f"{'Adresse':<10} {'Hex':<6} {'Int8':<6} {'Données':<8} {'Statut'}")
        else:
            print(f"{'Adresse':<10} {'Hex':<8} {'Int16':<8} {'Données':<12} {'Statut'}")
        print("-" * 80)
        
        success_count = 0
        match_count = 0
        
        for addr, value, raw_data in results:
            if value is None:
                if show_all:
                    addr_str = f"0x{addr:04X}"
                    print(f"{addr_str:<10} {'N/A':<8} {'N/A':<8} {'N/A':<12} ✗")
                continue
                
            success_count += 1
            
            addr_str = f"0x{addr:04X}"
            hex_str = f"0x{value:02X}" if bytes_count == 1 else f"0x{value:04X}"
            int_str = str(value)
            data_str = ' '.join([f"{b:02X}" for b in raw_data])
            status = "✓"
            
            # Vérifier si c'est une correspondance de recherche
            if search_value is not None and value == search_value:
                status = "★"  # Étoile pour les correspondances
                match_count += 1
            
            if show_all or (search_value is not None and value == search_value):
                print(f"{addr_str:<10} {hex_str:<8} {int_str:<8} {data_str:<12} {status}")
        
        print("-" * 80)
        print(f"Résumé: {success_count}/{len(results)} registres lus avec succès")
        if search_value is not None:
            print(f"Correspondances trouvées: {match_count}")
        print("=" * 80)


def parse_address(addr_str: str) -> int:
    """Parser une adresse hexadécimale"""
    try:
        if addr_str.startswith('0x') or addr_str.startswith('0X'):
            return int(addr_str, 16)
        else:
            return int(addr_str, 16)
    except ValueError:
        raise ValueError(f"Adresse invalide: {addr_str}")


def parse_value(value_str: str) -> int:
    """Parser une valeur (hex ou décimal)"""
    try:
        if value_str.startswith('0x') or value_str.startswith('0X'):
            return int(value_str, 16)
        else:
            return int(value_str)
    except ValueError:
        raise ValueError(f"Valeur invalide: {value_str}")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description='Lecteur flexible de registres Palazzetti avec recherche',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # Lire la plage 1C00-207C avec 2 octets
  python3 register_search.py --start 1C00 --end 207C --bytes 2

  # Rechercher la valeur 22 dans la plage 1C00-1CFF avec 1 octet
  python3 register_search.py --start 1C00 --end 1CFF --search 22 --bytes 1

  # Rechercher la valeur hexadécimale 0x1234 dans la plage 2000-207C
  python3 register_search.py --start 2000 --end 207C --search 0x1234 --bytes 2

  # Mode mock pour les tests
  python3 register_search.py --start 1C00 --end 1C0F --mock
        """
    )
    
    parser.add_argument('--start', type=str, required=True, 
                       help='Adresse de début (hex, ex: 1C00)')
    parser.add_argument('--end', type=str, required=True, 
                       help='Adresse de fin (hex, ex: 207C)')
    parser.add_argument('--search', type=str, 
                       help='Valeur à rechercher (hex ou décimal, ex: 22 ou 0x1234)')
    parser.add_argument('--bytes', type=int, choices=[1, 2], default=2,
                       help='Nombre d\'octets à lire (1 ou 2, défaut: 2)')
    parser.add_argument('--mock', action='store_true', 
                       help='Utiliser le mode mock (développement)')
    parser.add_argument('--exact', action='store_true', default=True,
                       help='Correspondance exacte (défaut)')
    parser.add_argument('--partial', action='store_true',
                       help='Correspondance partielle')
    parser.add_argument('--show-all', action='store_true',
                       help='Afficher tous les résultats (pas seulement les correspondances)')
    parser.add_argument('--debug', action='store_true',
                       help='Mode debug avec affichage détaillé des communications')
    
    args = parser.parse_args()
    
    # Parser les adresses
    try:
        start_addr = parse_address(args.start)
        end_addr = parse_address(args.end)
    except ValueError as e:
        print(f"Erreur: {e}")
        return 1
    
    if start_addr > end_addr:
        print("Erreur: L'adresse de début doit être inférieure à l'adresse de fin")
        return 1
    
    # Parser la valeur de recherche si fournie
    search_value = None
    if args.search:
        try:
            search_value = parse_value(args.search)
        except ValueError as e:
            print(f"Erreur: {e}")
            return 1
    
    # Déterminer le mode de correspondance
    exact_match = args.exact and not args.partial
    
    # Créer le lecteur
    reader = FlexibleRegisterReader(use_mock=args.mock)
    
    try:
        # Se connecter
        if not reader.connect():
            print("Impossible de se connecter au poêle")
            return 1
        
        # Exécuter l'opération demandée
        if search_value is not None:
            # Mode recherche
            results = reader.search_value_in_range(
                start_addr, end_addr, search_value, 
                args.bytes, exact_match, args.debug
            )
            reader.display_results(results, args.bytes, args.show_all, search_value)
        else:
            # Mode lecture complète
            results = reader.read_range(start_addr, end_addr, args.bytes, args.debug)
            reader.display_results(results, args.bytes, True)
        
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur")
    finally:
        reader.disconnect()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
