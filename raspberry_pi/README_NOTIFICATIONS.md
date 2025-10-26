# 📧 Système de Notifications Email - Contrôleur Palazzetti

Ce document décrit le système de notifications email implémenté pour le contrôleur Palazzetti.

## 📋 Fonctionnalités

### ✅ **Notifications Email**
- **Support SMTP** : Envoi d'emails via serveur SMTP standard
- **Multi-destinataires** : Envoi à plusieurs adresses email
- **Notifications en arrière-plan** : Surveillance automatique périodique
- **Configuration simple** : Support Gmail, Outlook, et autres serveurs SMTP

### ✅ **Types d'Alertes**
1. **🚨 Alertes Critiques** (Cooldown: 30 min)
   - Plus de pellets (E114)
   - Porte ou trémie ouverte (E108)
   - Alarme pression/disjoncteur (E109)
   - Gaz surchauffés (E113)
   - Erreur générale (E115)

2. **⚠️ Niveau de Pellets Bas** (Cooldown: 1h)
   - Seuil configurable (défaut: 20%)
   - Calcul basé sur la consommation depuis le dernier remplissage

3. **🔧 Maintenance Requise** (Cooldown: 24h)
   - Seuil configurable (défaut: 500kg)
   - Basé sur la consommation depuis le dernier reset

4. **🔌 Perte de Connexion** (Cooldown: 30 min)
   - Détection de la perte de communication série

## 🏗️ Architecture

### **Composants**
- **`email_notifications.py`** : Gestionnaire principal des notifications email
- **`notification_scheduler.py`** : Surveillance périodique automatique
- **`config.py`** : Configuration SMTP et des alertes

### **APIs Disponibles**
- `GET /api/notifications/status` : Statut des notifications
- `POST /api/notifications/test` : Test de notification email
- `GET /api/notifications/config` : Configuration

## 🚀 Installation et Configuration

### **1. Dépendances**
```bash
pip install Flask pyserial
```

### **2. Configuration**
Copiez `env.example` vers `.env` et configurez :
```bash
cp env.example .env
```

Variables importantes :
```env
# Configuration des notifications email
NOTIFICATIONS_ENABLED=true
NOTIFICATION_CHECK_INTERVAL=30
NOTIFICATION_URL=http://localhost:5000

# Configuration SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-app
FROM_EMAIL=votre-email@gmail.com
TO_EMAILS=alerte@domaine.com,admin@domaine.com
SMTP_USE_TLS=true
```

### **3. Démarrage**
```bash
python app.py
```

## 📧 Configuration Email

### **Gmail**
1. Activez l'authentification à 2 facteurs
2. Générez un mot de passe d'application :
   - Allez dans [Paramètres Google](https://myaccount.google.com/)
   - Sécurité → Mots de passe des applications
   - Générez un mot de passe pour "Mail"
3. Utilisez ce mot de passe dans `SMTP_PASSWORD`

### **Outlook/Hotmail**
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### **Autres Serveurs SMTP**
Configurez selon votre fournisseur :
- **Port 587** : TLS/STARTTLS (recommandé)
- **Port 465** : SSL/TLS
- **Port 25** : Non chiffré (non recommandé)

## 🔧 Configuration Avancée

### **Seuils d'Alerte**
Modifiez dans `config.py` :
```python
NOTIFICATION_CONFIG = {
    'alerts': {
        'low_pellets': {
            'threshold': 20,  # % pour alerte niveau bas
            'cooldown': 3600,  # 1 heure
        },
        'maintenance': {
            'threshold': 500,  # kg pour alerte maintenance
            'cooldown': 86400,  # 24 heures
        }
    }
}
```

### **Surveillance Périodique**
- **Intervalle** : Configurable via `NOTIFICATION_CHECK_INTERVAL` (minutes)
- **Démarrage automatique** : Au démarrage de l'application
- **Arrêt propre** : Via les signaux système

## 🔍 Dépannage

### **Emails ne sont pas envoyés**
1. Vérifiez la configuration SMTP dans `.env`
2. Testez la connexion avec le bouton de test
3. Consultez les logs de l'application
4. Vérifiez les paramètres de sécurité de votre compte email

### **Erreur d'authentification SMTP**
1. Vérifiez le nom d'utilisateur et mot de passe
2. Pour Gmail, utilisez un mot de passe d'application
3. Vérifiez que l'authentification à 2 facteurs est activée
4. Testez avec un client email externe

### **Emails reçus mais dans les spams**
1. Vérifiez l'adresse `FROM_EMAIL`
2. Configurez les enregistrements SPF/DKIM de votre domaine
3. Utilisez une adresse email professionnelle

## 📊 Monitoring

### **Logs**
Les notifications sont loggées avec le niveau INFO :
```
INFO - Email 'Test - Contrôleur Palazzetti' envoyé avec succès
WARNING - Alerte critique envoyée: 253 - E114: Plus de pellets
```

### **Statut**
Consultez le statut via l'API :
```bash
curl http://localhost:5000/api/notifications/status
```

### **Test**
Testez l'envoi d'email :
```bash
curl -X POST http://localhost:5000/api/notifications/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Test de notification"}'
```

## 🔒 Sécurité

### **Mots de Passe**
- **Gmail** : Utilisez des mots de passe d'application
- **Autres** : Évitez les mots de passe principaux
- **Stockage** : Les mots de passe sont dans `.env` (non versionné)

### **Configuration**
- Le fichier `.env` ne doit pas être partagé
- Utilisez des comptes email dédiés si possible
- Configurez les permissions de lecture seule sur `.env`

## 🚀 Évolutions Futures

### **Fonctionnalités Possibles**
- Notifications SMS (via API externe)
- Configuration des seuils via l'interface
- Historique des notifications
- Templates d'email personnalisés
- Notifications groupées
- Intégration avec des services de monitoring

### **Améliorations Techniques**
- Support des pièces jointes
- Gestion des quotas et limites
- Analytics des notifications
- Intégration avec des services externes
- Support des notifications push (si HTTPS disponible)

## 📞 Support

Pour toute question ou problème :
1. Consultez les logs de l'application
2. Vérifiez la configuration SMTP
3. Testez avec l'API de test
4. Consultez la documentation des APIs

---

**Note** : Ce système de notifications email est conçu pour être simple, fiable et compatible avec tous les environnements. Il s'intègre parfaitement avec l'architecture existante du contrôleur Palazzetti.