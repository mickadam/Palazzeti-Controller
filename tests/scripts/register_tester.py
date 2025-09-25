#!/usr/bin/env python3
"""
CLI pour tester la lecture et l'écriture des registres Palazzetti
Permet de valider chaque registre individuellement
"""
import sys
import os
import time
import json
from typing import Dict, List, Tuple, Optional, Any

# Ajouter le répertoire raspberry_pi au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'raspberry_pi'))

from config import *
from frame import Frame, construct_read_frame, construct_write_frame, parse_temperature, parse_setpoint, parse_status
import serial
import threading


class RegisterTester:
    """CLI pour tester les registres Palazzetti"""
    
    def __init__(self, use_mock=False):
        self.use_mock = use_mock
        self.serial_connection = None
        self.lock = threading.Lock()
        self.connected = False
        
        # Définition complète des registres avec leurs propriétés
        self.registers = {
            'status': {
                'address': REGISTER_STATUS,
                'name': 'Statut du poêle',
                'readable': True,
                'writable': False,
                'parser': self._parse_status,
                'formatter': self._format_status,
                'description': 'État actuel du poêle (OFF, BURNING, COOLING, etc.)'
            },
            'temperature': {
                'address': REGISTER_TEMPERATURE,
                'name': 'Température actuelle',
                'readable': True,
                'writable': False,
                'parser': self._parse_temperature,
                'formatter': self._format_temperature,
                'description': 'Température actuelle du poêle en °C'
            },
            'setpoint': {
                'address': REGISTER_SETPOINT,
                'name': 'Température de consigne',
                'readable': True,
                'writable': True,
                'parser': self._parse_setpoint,
                'formatter': self._format_temperature,
                'description': f'Température de consigne en °C ({MIN_TEMPERATURE}-{MAX_TEMPERATURE}°C)',
                'validator': self._validate_temperature
            },
            'power_control': {
                'address': REGISTER_POWER_CONTROL,
                'name': 'Contrôle ON/OFF',
                'readable': True,
                'writable': True,
                'parser': self._parse_power,
                'formatter': self._format_power,
                'description': 'Allumer/éteindre le poêle (0=OFF, 1=ON)',
                'validator': self._validate_power
            },
            'power_level': {
                'address': REGISTER_POWER_LEVEL,
                'name': 'Niveau de puissance',
                'readable': True,
                'writable': True,
                'parser': self._parse_power_level,
                'formatter': self._format_power_level,
                'description': 'Niveau de puissance du poêle (1-5)',
                'validator': self._validate_power_level
            },
            'start_control': {
                'address': REGISTER_START_CONTROL,
                'name': 'Contrôle de démarrage',
                'readable': True,
                'writable': True,
                'parser': self._parse_start_control,
                'formatter': self._format_start_control,
                'description': 'Contrôle du démarrage du poêle',
                'validator': self._validate_start_control
            },
            'error_code': {
                'address': REGISTER_ERROR_CODE,
                'name': 'Code d\'erreur',
                'readable': True,
                'writable': False,
                'parser': self._parse_error_code,
                'formatter': self._format_error_code,
                'description': 'Code d\'erreur actuel du poêle'
            },
            'alarm_status': {
                'address': REGISTER_ALARM_STATUS,
                'name': 'Statut des alarmes',
                'readable': True,
                'writable': False,
                'parser': self._parse_alarm_status,
                'formatter': self._format_alarm_status,
                'description': 'État des alarmes du poêle'
            },
            'timer_settings': {
                'address': REGISTER_TIMER_SETTINGS,
                'name': 'Paramètres Timer',
                'readable': True,
                'writable': True,
                'parser': self._parse_timer_settings,
                'formatter': self._format_timer_settings,
                'description': 'Paramètres du timer (0=Disable, 1=Enable)',
                'validator': self._validate_timer_settings
            }
        }
    
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
        Attendre une trame avec un ID spécifique (équivalent C# SynchroTrame)
        
        Args:
            expected_id: ID de trame attendu
            timeout: Timeout en secondes (défaut 5s comme C#)
        
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
                    print(f"  Trame reçue: {frame}")
                    if frame.get_id() == expected_id:
                        print(f"✓ Trame trouvée avec ID 0x{expected_id:02X}")
                        return frame
                    else:
                        print(f"  ID reçu 0x{frame.get_id():02X}, attendu 0x{expected_id:02X}")
            # Pas de sleep pour être plus réactif comme le code C#
        
        print(f"✗ Timeout: aucune trame avec ID 0x{expected_id:02X} reçue")
        return None
    
    def send_read_command(self, address):
        """
        Envoyer une commande de lecture pour une adresse donnée
        Implémentation basée sur le code C# ReadRegisterWithID
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
                
                # Boucle de retry comme dans le code C# (max 10 tentatives)
                for attempt in range(10):
                    print(f"Tentative {attempt + 1}/10...")
                    
                    # 1. Attendre la trame de synchronisation (0x00)
                    sync_frame = self.synchro_trame(0x00, timeout=5)
                    if sync_frame:
                        print("✓ Trame de synchronisation reçue")
                        
                        # 2. Envoyer la commande de lecture
                        print(f"Envoi commande: {read_frame}")
                        self.serial_connection.write(read_frame.as_bytes())
                        self.serial_connection.flush()
                        
                        # 3. Attendre la réponse avec le même ID
                        response = self.synchro_trame(expected_id, timeout=5)
                        if response:
                            print(f"✓ Réponse reçue: {response}")
                            return response
                        else:
                            print(f"✗ Pas de réponse avec ID 0x{expected_id:02X}")
                    else:
                        print("✗ Pas de trame de synchronisation")
                
                print("✗ Échec après 10 tentatives")
                return None
                    
            except Exception as e:
                print(f"✗ Erreur lors de l'envoi de commande de lecture: {e}")
                return None
    
    def send_write_command(self, address, value_bytes):
        """Envoyer une commande d'écriture pour une adresse et des données"""
        if self.use_mock:
            return self._get_mock_write_response(address, value_bytes)
            
        if not self.serial_connection or not self.serial_connection.is_open:
            print("✗ Connexion série non disponible")
            return None
            
        with self.lock:
            try:
                # Attendre la trame de synchronisation
                if not self.wait_for_sync_frame():
                    print("✗ Pas de trame de synchronisation")
                    return None
                
                # Construire et envoyer la trame d'écriture
                write_frame = construct_write_frame(address, value_bytes)
                
                self.serial_connection.write(write_frame.as_bytes())
                self.serial_connection.flush()
                
                # Attendre la réponse
                response_frame = self.wait_for_frame_by_id(write_frame.get_id())
                if response_frame and response_frame.is_valid():
                    return response_frame
                else:
                    print("✗ Réponse invalide ou timeout")
                    return None
                    
            except Exception as e:
                print(f"✗ Erreur lors de l'envoi de commande d'écriture: {e}")
                return None
    
    def _get_mock_response(self, address):
        """Simuler une réponse pour le mode développement"""
        if address == REGISTER_STATUS:
            # Simuler un statut BURNING - format C#: [adresse_LSB][adresse_MSB][statut][padding...]
            mock_data = [address[1], address[0], STATUS_BURNING] + [0x00] * 6
            return Frame(frame_id=0x02, data=mock_data)  # ID 0x02 pour lecture
        elif address == REGISTER_TEMPERATURE:
            # Simuler une température de 22.5°C - format C#: [adresse_LSB][adresse_MSB][temp_MSB][temp_LSB][padding...]
            temp_raw = int(22.5 * 10)  # 225
            mock_data = [address[1], address[0], (temp_raw >> 8) & 0xFF, temp_raw & 0xFF] + [0x00] * 5
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_SETPOINT:
            # Simuler une consigne de 22°C (température * 5 sur 1 octet)
            temp_raw = int(22.0 * 5)  # 110
            mock_data = [address[1], address[0], temp_raw & 0xFF] + [0x00] * 6
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_POWER_CONTROL:
            # Simuler un état de puissance
            mock_data = [address[1], address[0], POWER_ON] + [0x00] * 6
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_POWER_LEVEL:
            # Simuler un niveau de puissance
            mock_data = [address[1], address[0], 3] + [0x00] * 6
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_ERROR_CODE:
            # Simuler aucun erreur
            mock_data = [address[1], address[0], ERROR_NONE] + [0x00] * 6
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_ALARM_STATUS:
            # Simuler aucun alarme
            mock_data = [address[1], address[0], 0x00] + [0x00] * 6
            return Frame(frame_id=0x02, data=mock_data)
        elif address == REGISTER_TIMER_SETTINGS:
            # Simuler timer désactivé
            mock_data = [address[1], address[0], TIMER_DISABLE] + [0x00] * 6
            return Frame(frame_id=0x02, data=mock_data)
        else:
            # Réponse générique
            mock_data = [address[1], address[0]] + [0x00] * 7
            return Frame(frame_id=0x02, data=mock_data)
    
    def _get_mock_write_response(self, address, value_bytes):
        """Simuler une réponse d'écriture pour le mode développement"""
        # Simuler une réponse de confirmation - format C#: [adresse_LSB][adresse_MSB][code_succès][padding...]
        mock_data = [address[1], address[0], 0x01] + [0x00] * 6  # Code de succès
        return Frame(frame_id=0x01, data=mock_data)  # ID 0x01 pour écriture
    
    def list_registers(self):
        """Afficher la liste des registres disponibles"""
        print("\n=== Registres disponibles ===")
        print(f"{'Nom':<20} {'Adresse':<10} {'R/W':<4} {'Description'}")
        print("-" * 80)
        
        for key, reg in self.registers.items():
            rw = "R" if reg['readable'] else "-"
            rw += "W" if reg['writable'] else "-"
            address_str = f"0x{reg['address'][0]:02X} 0x{reg['address'][1]:02X}"
            print(f"{reg['name']:<20} {address_str:<10} {rw:<4} {reg['description']}")
    
    def read_register(self, register_key: str) -> Optional[Any]:
        """Lire un registre spécifique"""
        if not self.connected:
            print("✗ Non connecté au poêle")
            return None
            
        if register_key not in self.registers:
            print(f"✗ Registre '{register_key}' inconnu")
            return None
            
        reg = self.registers[register_key]
        if not reg['readable']:
            print(f"✗ Le registre '{register_key}' n'est pas lisible")
            return None
        
        print(f"\nLecture du registre: {reg['name']}")
        print(f"Adresse: 0x{reg['address'][0]:02X} 0x{reg['address'][1]:02X}")
        
        try:
            # Envoyer la commande de lecture
            frame = self.send_read_command(reg['address'])
            
            if frame is None:
                print("✗ Aucune réponse reçue")
                return None
            
            if not frame.is_valid():
                print("✗ Trame de réponse invalide (checksum incorrect)")
                return None
            
            print(f"✓ Trame reçue: {frame}")
            
            # Parser les données
            parsed_data = reg['parser'](frame.get_data())
            formatted_data = reg['formatter'](parsed_data)
            
            print(f"Données brutes: {' '.join([f'{b:02X}' for b in frame.get_data()])}")
            print(f"Données parsées: {formatted_data}")
            
            return parsed_data
            
        except Exception as e:
            print(f"✗ Erreur lors de la lecture: {e}")
            return None
    
    def write_register(self, register_key: str, value: Any) -> bool:
        """Écrire dans un registre spécifique"""
        if not self.connected:
            print("✗ Non connecté au poêle")
            return False
            
        if register_key not in self.registers:
            print(f"✗ Registre '{register_key}' inconnu")
            return False
            
        reg = self.registers[register_key]
        if not reg['writable']:
            print(f"✗ Le registre '{register_key}' n'est pas modifiable")
            return False
        
        # Valider la valeur si un validateur existe
        if 'validator' in reg:
            if not reg['validator'](value):
                print(f"✗ Valeur invalide pour le registre '{register_key}'")
                return False
        
        print(f"\nÉcriture dans le registre: {reg['name']}")
        print(f"Adresse: 0x{reg['address'][0]:02X} 0x{reg['address'][1]:02X}")
        print(f"Valeur: {value}")
        
        try:
            # Convertir la valeur en bytes selon le type de registre
            value_bytes = self._convert_to_bytes(register_key, value)
            print(f"Bytes à envoyer: {' '.join([f'{b:02X}' for b in value_bytes])}")
            
            # Envoyer la commande d'écriture
            frame = self.send_write_command(reg['address'], value_bytes)
            
            if frame is None:
                print("✗ Aucune réponse reçue")
                return False
            
            if not frame.is_valid():
                print("✗ Trame de réponse invalide (checksum incorrect)")
                return False
            
            print(f"✓ Trame de confirmation reçue: {frame}")
            print("✓ Écriture réussie")
            
            return True
            
        except Exception as e:
            print(f"✗ Erreur lors de l'écriture: {e}")
            return False
    
    def test_all_registers(self):
        """Tester la lecture de tous les registres"""
        print("\n=== Test de lecture de tous les registres ===")
        
        results = {}
        for key, reg in self.registers.items():
            if reg['readable']:
                print(f"\n--- Test du registre: {reg['name']} ---")
                result = self.read_register(key)
                results[key] = result is not None
                
                if result is not None:
                    print(f"✓ Lecture réussie")
                else:
                    print(f"✗ Lecture échouée")
                
                time.sleep(0.5)  # Pause entre les lectures
        
        # Résumé
        print(f"\n=== Résumé des tests ===")
        success_count = sum(results.values())
        total_count = len(results)
        
        for key, success in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {self.registers[key]['name']}")
        
        print(f"\nRésultat: {success_count}/{total_count} registres lus avec succès")
        return success_count == total_count
    
    def interactive_mode(self):
        """Mode interactif pour tester les registres"""
        print("\n=== Mode interactif ===")
        print("Commandes disponibles:")
        print("  list                    - Lister tous les registres")
        print("  read <nom>             - Lire un registre")
        print("  write <nom> <valeur>   - Écrire dans un registre")
        print("  test                   - Tester tous les registres")
        print("  state                  - Afficher l'état complet du poêle")
        print("  help                   - Afficher cette aide")
        print("  quit                   - Quitter")
        
        while True:
            try:
                command = input("\n> ").strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'help':
                    print("Commandes disponibles:")
                    print("  list                    - Lister tous les registres")
                    print("  read <nom>             - Lire un registre")
                    print("  write <nom> <valeur>   - Écrire dans un registre")
                    print("  test                   - Tester tous les registres")
                    print("  state                  - Afficher l'état complet du poêle")
                    print("  quit                   - Quitter")
                elif cmd == 'list':
                    self.list_registers()
                elif cmd == 'read':
                    if len(command) < 2:
                        print("Usage: read <nom_du_registre>")
                        continue
                    self.read_register(command[1])
                elif cmd == 'write':
                    if len(command) < 3:
                        print("Usage: write <nom_du_registre> <valeur>")
                        continue
                    try:
                        # Essayer de convertir la valeur en nombre
                        value = float(command[2]) if '.' in command[2] else int(command[2])
                        self.write_register(command[1], value)
                    except ValueError:
                        # Si ce n'est pas un nombre, utiliser la chaîne
                        self.write_register(command[1], command[2])
                elif cmd == 'test':
                    self.test_all_registers()
                elif cmd == 'state':
                    self.show_complete_state()
                else:
                    print(f"Commande inconnue: {cmd}")
                    print("Tapez 'help' pour voir les commandes disponibles")
                    
            except KeyboardInterrupt:
                print("\nInterruption par l'utilisateur")
                break
            except EOFError:
                break
    
    def show_complete_state(self):
        """Afficher l'état complet du poêle"""
        print("\n=== État complet du poêle ===")
        
        if not self.connected:
            print("✗ Non connecté au poêle")
            return
        
        print(f"Connexion: {'✓ Connecté' if self.connected else '✗ Déconnecté'}")
        
        # Lire les registres principaux
        try:
            # Statut
            status_frame = self.send_read_command(REGISTER_STATUS)
            if status_frame:
                status_code, status_name, power_on = parse_status(status_frame.get_data())
                print(f"Statut: {status_name}")
                print(f"Alimenté: {'Oui' if power_on else 'Non'}")
            
            # Température actuelle
            temp_frame = self.send_read_command(REGISTER_TEMPERATURE)
            if temp_frame:
                temperature = parse_temperature(temp_frame.get_data())
                print(f"Température: {temperature}°C")
            
            # Température de consigne (utilise parse_setpoint_atech avec fluide type 0)
            setpoint_frame = self.send_read_command(REGISTER_SETPOINT)
            if setpoint_frame:
                # Pour le registre simple, on utilise seulement le premier byte
                data = setpoint_frame.get_data()
                if len(data) >= 1:
                    setpoint = data[0] / 5.0  # Format température * 5
                    print(f"Consigne: {setpoint}°C")
            
            # Code d'erreur
            error_frame = self.send_read_command(REGISTER_ERROR_CODE)
            if error_frame:
                error_code = error_frame.get_data()[2]  # data[2] après l'adresse
                error_message = ERROR_MAP.get(error_code, f'Erreur inconnue: {error_code}')
                print(f"Code d'erreur: {error_code}")
                print(f"Message d'erreur: {error_message}")
                
        except Exception as e:
            print(f"Erreur lors de la lecture de l'état: {e}")
    
    # Parsers pour les différents types de registres
    def _parse_status(self, data: List[int]) -> Tuple[int, str, bool]:
        """Parser le statut du poêle"""
        return parse_status(data)
    
    def _parse_temperature(self, data: List[int]) -> float:
        """Parser une température"""
        return parse_temperature(data)
    
    def _parse_setpoint(self, data: List[int]) -> float:
        """Parser la consigne simple (température * 5 sur 1 byte)"""
        if len(data) < 1:
            return 0.0
        return data[0] / 5.0
    
    def _parse_power(self, data: List[int]) -> bool:
        """Parser l'état de puissance (1 byte)"""
        if len(data) < 3:
            return False
        return data[0] == POWER_ON  # data[2] après l'adresse - 1 byte
    
    def _parse_power_level(self, data: List[int]) -> int:
        """Parser le niveau de puissance (1 byte)"""
        if len(data) < 3:
            return 0
        return data[0]  # data[2] après l'adresse - 1 byte
    
    def _parse_start_control(self, data: List[int]) -> int:
        """Parser le contrôle de démarrage (1 byte)"""
        if len(data) < 3:
            return 0
        return data[0]  # data[2] après l'adresse - 1 byte
    
    def _parse_error_code(self, data: List[int]) -> int:
        """Parser le code d'erreur (1 byte)"""
        if len(data) < 3:
            return 0
        return data[0]  # data[2] après l'adresse - 1 byte
    
    def _parse_alarm_status(self, data: List[int]) -> int:
        """Parser le statut des alarmes (1 byte)"""
        if len(data) < 3:
            return 0
        return data[0]  # data[2] après l'adresse - 1 byte
    
    def _parse_timer_settings(self, data: List[int]) -> bool:
        """Parser les paramètres du timer (1 byte)"""
        if len(data) < 3:
            return False
        return data[0] == TIMER_ENABLE  # data[2] après l'adresse - 1 byte
    
    # Formatters pour l'affichage
    def _format_status(self, data: Tuple[int, str, bool]) -> str:
        """Formatter le statut pour l'affichage"""
        status_code, status_name, power_on = data
        return f"{status_name} (code: 0x{status_code:02X}, alimenté: {'Oui' if power_on else 'Non'})"
    
    def _format_temperature(self, data: float) -> str:
        """Formatter une température pour l'affichage"""
        return f"{data}°C"
    
    def _format_power(self, data: bool) -> str:
        """Formatter l'état de puissance pour l'affichage"""
        return "ON" if data else "OFF"
    
    def _format_power_level(self, data: int) -> str:
        """Formatter le niveau de puissance pour l'affichage"""
        return f"Niveau {data}/5"
    
    def _format_start_control(self, data: int) -> str:
        """Formatter le contrôle de démarrage pour l'affichage"""
        return f"Code: 0x{data:02X}"
    
    def _format_error_code(self, data: int) -> str:
        """Formatter le code d'erreur pour l'affichage"""
        error_msg = ERROR_MAP.get(data, f"Erreur inconnue: 0x{data:02X}")
        return f"0x{data:02X} - {error_msg}"
    
    def _format_alarm_status(self, data: int) -> str:
        """Formatter le statut des alarmes pour l'affichage"""
        return f"Code: 0x{data:02X}"
    
    def _format_timer_settings(self, data: bool) -> str:
        """Formatter les paramètres du timer pour l'affichage"""
        return "Activé" if data else "Désactivé"
    
    # Validateurs
    def _validate_temperature(self, value: float) -> bool:
        """Valider une température"""
        return MIN_TEMPERATURE <= value <= MAX_TEMPERATURE
    
    def _validate_power(self, value: Any) -> bool:
        """Valider une valeur de puissance"""
        if isinstance(value, bool):
            return True
        if isinstance(value, int):
            return value in [0, 1]
        if isinstance(value, str):
            return value.lower() in ['on', 'off', 'true', 'false', '0', '1']
        return False
    
    def _validate_power_level(self, value: int) -> bool:
        """Valider un niveau de puissance"""
        return 1 <= value <= 5
    
    def _validate_start_control(self, value: int) -> bool:
        """Valider un code de contrôle de démarrage"""
        return 0 <= value <= 255
    
    def _validate_timer_settings(self, value: Any) -> bool:
        """Valider les paramètres du timer"""
        if isinstance(value, bool):
            return True
        if isinstance(value, int):
            return value in [0, 1]
        if isinstance(value, str):
            return value.lower() in ['enable', 'disable', 'true', 'false', '0', '1']
        return False
    
    # Convertisseurs
    def _convert_to_bytes(self, register_key: str, value: Any) -> List[int]:
        """Convertir une valeur en bytes selon le type de registre"""
        if register_key == 'setpoint':
            # Température sur 1 byte (température * 5)
            temp_raw = int(value * 5)
            return [temp_raw & 0xFF]
        elif register_key == 'power_control':
            # Commande de puissance sur 1 byte
            if isinstance(value, bool):
                power_code = POWER_ON if value else POWER_OFF
            elif isinstance(value, str):
                power_code = POWER_ON if value.lower() in ['on', 'true', '1'] else POWER_OFF
            else:
                power_code = POWER_ON if value else POWER_OFF
            return [power_code]
        elif register_key == 'power_level':
            # Niveau de puissance sur 1 byte
            return [int(value)]
        elif register_key == 'start_control':
            # Code de contrôle sur 1 byte
            return [int(value)]
        elif register_key == 'timer_settings':
            # Paramètres timer sur 1 byte
            if isinstance(value, bool):
                timer_code = TIMER_ENABLE if value else TIMER_DISABLE
            elif isinstance(value, str):
                timer_code = TIMER_ENABLE if value.lower() in ['enable', 'true', '1'] else TIMER_DISABLE
            else:
                timer_code = TIMER_ENABLE if value else TIMER_DISABLE
            return [timer_code]
        else:
            # Par défaut, traiter comme un entier
            return [int(value)]


def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Testeur de registres Palazzetti')
    parser.add_argument('--mock', action='store_true', help='Utiliser le mode mock (développement)')
    parser.add_argument('--list', action='store_true', help='Lister tous les registres')
    parser.add_argument('--read', type=str, help='Lire un registre spécifique')
    parser.add_argument('--write', nargs=2, metavar=('REGISTER', 'VALUE'), help='Écrire dans un registre')
    parser.add_argument('--test', action='store_true', help='Tester tous les registres')
    parser.add_argument('--state', action='store_true', help='Afficher l\'état complet')
    parser.add_argument('--interactive', action='store_true', help='Mode interactif')
    
    args = parser.parse_args()
    
    # Créer le testeur
    tester = RegisterTester(use_mock=args.mock)
    
    try:
        # Se connecter
        if not tester.connect():
            print("Impossible de se connecter au poêle")
            return 1
        
        # Exécuter les commandes
        if args.list:
            tester.list_registers()
        elif args.read:
            tester.read_register(args.read)
        elif args.write:
            register, value = args.write
            try:
                # Essayer de convertir en nombre
                value = float(value) if '.' in value else int(value)
            except ValueError:
                pass  # Garder comme string
            tester.write_register(register, value)
        elif args.test:
            tester.test_all_registers()
        elif args.state:
            tester.show_complete_state()
        elif args.interactive:
            tester.interactive_mode()
        else:
            # Mode par défaut: afficher l'aide et lancer le mode interactif
            print("Testeur de registres Palazzetti")
            print("Utilisez --help pour voir les options disponibles")
            print("Ou utilisez --interactive pour le mode interactif")
            tester.interactive_mode()
    
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur")
    finally:
        tester.disconnect()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
