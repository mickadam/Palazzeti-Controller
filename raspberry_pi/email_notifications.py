"""
Système de notifications par email pour le contrôleur Palazzetti
"""
import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from config import NOTIFICATION_CONFIG

logger = logging.getLogger(__name__)

class EmailNotificationManager:
    """Gestionnaire de notifications par email"""
    
    def __init__(self, smtp_config=None):
        self.config = NOTIFICATION_CONFIG
        self.smtp_config = smtp_config or self._get_default_smtp_config()
        self.last_alerts = {}  # Pour gérer les cooldowns
        
    def _get_default_smtp_config(self):
        """Configuration SMTP par défaut"""
        import os
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', ''),
            'to_emails': os.getenv('TO_EMAILS', '').split(',') if os.getenv('TO_EMAILS') else [],
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        }
    
    def _should_send_alert(self, alert_type):
        """Vérifier si une alerte doit être envoyée (gestion des cooldowns)"""
        if alert_type not in self.config['alerts']:
            return True
        
        cooldown = self.config['alerts'][alert_type]['cooldown']
        last_sent = self.last_alerts.get(alert_type, 0)
        
        if time.time() - last_sent > cooldown:
            self.last_alerts[alert_type] = time.time()
            return True
        
        return False
    
    def _send_email(self, subject, body, html_body=None):
        """Envoyer un email"""
        if not self.smtp_config['username'] or not self.smtp_config['to_emails']:
            logger.warning("Configuration SMTP incomplète, email non envoyé")
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_config['from_email'] or self.smtp_config['username']
            msg['To'] = ', '.join(self.smtp_config['to_emails'])
            msg['Subject'] = subject
            
            # Ajouter le texte brut
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Ajouter le HTML si fourni
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Connexion SMTP
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            
            if self.smtp_config['use_tls']:
                server.starttls()
            
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            # Envoyer l'email
            text = msg.as_string()
            server.sendmail(msg['From'], self.smtp_config['to_emails'], text)
            server.quit()
            
            logger.info(f"Email envoyé avec succès: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            return False
    
    def send_critical_error_alert(self, error_code, error_message):
        """Envoyer une alerte d'erreur critique"""
        if not self._should_send_alert('critical_errors'):
            return
        
        subject = "🚨 Alerte Critique - Poêle Palazzetti"
        body = f"""
ALERTE CRITIQUE - POÊLE PALAZZETTI

Code d'erreur: {error_code}
Message: {error_message}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Action requise: Vérifiez immédiatement votre poêle à pellets.

---
Contrôleur Palazzetti
Système de surveillance automatique
        """.strip()
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #ffebee; border-left: 5px solid #f44336; padding: 20px; margin: 20px 0;">
                <h2 style="color: #d32f2f; margin: 0 0 15px 0;">🚨 ALERTE CRITIQUE - POÊLE PALAZZETTI</h2>
                
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>Code d'erreur:</strong> {error_code}</p>
                    <p><strong>Message:</strong> {error_message}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                <div style="background: #fff3e0; padding: 15px; border-radius: 5px; border-left: 3px solid #ff9800;">
                    <p><strong>⚠️ Action requise:</strong> Vérifiez immédiatement votre poêle à pellets.</p>
                </div>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Contrôleur Palazzetti - Système de surveillance automatique
            </p>
        </body>
        </html>
        """
        
        self._send_email(subject, body, html_body)
    
    def send_low_pellets_alert(self, fill_level, threshold):
        """Envoyer une alerte de niveau de pellets bas"""
        if not self._should_send_alert('low_pellets'):
            return
        
        subject = "⚠️ Niveau de Pellets Bas - Poêle Palazzetti"
        body = f"""
ALERTE NIVEAU DE PELLETS BAS

Niveau actuel: {fill_level}%
Seuil d'alerte: {threshold}%
Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Recommandation: Préparez-vous à remplir le poêle avec des pellets.

---
Contrôleur Palazzetti
Système de surveillance automatique
        """.strip()
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #fff3e0; border-left: 5px solid #ff9800; padding: 20px; margin: 20px 0;">
                <h2 style="color: #f57c00; margin: 0 0 15px 0;">⚠️ NIVEAU DE PELLETS BAS</h2>
                
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>Niveau actuel:</strong> {fill_level}%</p>
                    <p><strong>Seuil d'alerte:</strong> {threshold}%</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; border-left: 3px solid #4caf50;">
                    <p><strong>💡 Recommandation:</strong> Préparez-vous à remplir le poêle avec des pellets.</p>
                </div>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Contrôleur Palazzetti - Système de surveillance automatique
            </p>
        </body>
        </html>
        """
        
        self._send_email(subject, body, html_body)
    
    def send_maintenance_alert(self, consumption_since_reset, threshold):
        """Envoyer une alerte de maintenance requise"""
        if not self._should_send_alert('maintenance'):
            return
        
        subject = "🔧 Maintenance Requise - Poêle Palazzetti"
        body = f"""
ALERTE MAINTENANCE REQUISE

Consommation depuis le dernier entretien: {consumption_since_reset} kg
Seuil de maintenance: {threshold} kg
Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Recommandation: Planifiez un entretien de votre poêle à pellets.

---
Contrôleur Palazzetti
Système de surveillance automatique
        """.strip()
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #e3f2fd; border-left: 5px solid #2196f3; padding: 20px; margin: 20px 0;">
                <h2 style="color: #1976d2; margin: 0 0 15px 0;">🔧 MAINTENANCE REQUISE</h2>
                
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>Consommation depuis le dernier entretien:</strong> {consumption_since_reset} kg</p>
                    <p><strong>Seuil de maintenance:</strong> {threshold} kg</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                <div style="background: #fff3e0; padding: 15px; border-radius: 5px; border-left: 3px solid #ff9800;">
                    <p><strong>📅 Recommandation:</strong> Planifiez un entretien de votre poêle à pellets.</p>
                </div>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Contrôleur Palazzetti - Système de surveillance automatique
            </p>
        </body>
        </html>
        """
        
        self._send_email(subject, body, html_body)
    
    def send_connection_lost_alert(self):
        """Envoyer une alerte de perte de connexion"""
        if not self._should_send_alert('connection_lost'):
            return
        
        subject = "🔌 Connexion Perdue - Poêle Palazzetti"
        body = f"""
ALERTE PERTE DE CONNEXION

La connexion avec le poêle a été perdue.
Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Action requise: Vérifiez le câble de connexion et l'alimentation du poêle.

---
Contrôleur Palazzetti
Système de surveillance automatique
        """.strip()
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #ffebee; border-left: 5px solid #f44336; padding: 20px; margin: 20px 0;">
                <h2 style="color: #d32f2f; margin: 0 0 15px 0;">🔌 PERTE DE CONNEXION</h2>
                
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>Problème:</strong> La connexion avec le poêle a été perdue</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                <div style="background: #fff3e0; padding: 15px; border-radius: 5px; border-left: 3px solid #ff9800;">
                    <p><strong>🔧 Action requise:</strong> Vérifiez le câble de connexion et l'alimentation du poêle.</p>
                </div>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Contrôleur Palazzetti - Système de surveillance automatique
            </p>
        </body>
        </html>
        """
        
        self._send_email(subject, body, html_body)
    
    def send_test_email(self, custom_message=None):
        """Envoyer un email de test"""
        subject = "🧪 Test - Notifications Email Palazzetti"
        message = custom_message or "Ceci est un email de test pour vérifier le bon fonctionnement du système de notifications par email."
        
        body = f"""
TEST DES NOTIFICATIONS EMAIL

{message}

Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Si vous recevez cet email, le système de notifications fonctionne correctement.

---
Contrôleur Palazzetti
Système de surveillance automatique
        """.strip()
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #e8f5e8; border-left: 5px solid #4caf50; padding: 20px; margin: 20px 0;">
                <h2 style="color: #2e7d32; margin: 0 0 15px 0;">🧪 TEST DES NOTIFICATIONS EMAIL</h2>
                
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <p>{message}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 3px solid #2196f3;">
                    <p><strong>✅ Succès:</strong> Si vous recevez cet email, le système de notifications fonctionne correctement.</p>
                </div>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Contrôleur Palazzetti - Système de surveillance automatique
            </p>
        </body>
        </html>
        """
        
        return self._send_email(subject, body, html_body)
    
    def check_all_conditions(self, state, consumption_data=None):
        """Vérifier toutes les conditions d'alerte"""
        if not self.config['enabled']:
            return
        
        try:
            # Vérifier les erreurs critiques
            error_code = state.get('error_code', 0)
            error_message = state.get('error_message', 'Erreur inconnue')
            critical_codes = self.config['alerts']['critical_errors']['codes']
            
            if error_code in critical_codes:
                self.send_critical_error_alert(error_code, error_message)
            
            # Vérifier le niveau de pellets
            fill_level = state.get('fill_level', {}).get('fill_level', 100)
            threshold = self.config['alerts']['low_pellets']['threshold']
            
            if fill_level < threshold:
                self.send_low_pellets_alert(fill_level, threshold)
            
            # Vérifier la perte de connexion
            if not state.get('connected', False):
                self.send_connection_lost_alert()
            
            # Vérifier la maintenance
            if consumption_data:
                consumption_since_reset = consumption_data.get('consumption_since_reset', 0)
                threshold = self.config['alerts']['maintenance']['threshold']
                
                if consumption_since_reset > threshold:
                    self.send_maintenance_alert(consumption_since_reset, threshold)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des conditions d'alerte: {e}")
    
    def get_config_status(self):
        """Obtenir le statut de la configuration email"""
        return {
            'smtp_configured': bool(self.smtp_config['username'] and self.smtp_config['to_emails']),
            'smtp_server': self.smtp_config['smtp_server'],
            'from_email': self.smtp_config['from_email'] or self.smtp_config['username'],
            'to_emails': self.smtp_config['to_emails'],
            'last_alerts': self.last_alerts
        }
