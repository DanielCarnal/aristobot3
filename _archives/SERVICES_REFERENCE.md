# RÉFÉRENCE DES SERVICES ARISTOBOT3.1

## 🚀 **SERVICES ACTIFS (Architecture Native)**

### **Terminal 1 : Serveur Web + WebSocket (Daphne)**
- **Commande** : `daphne aristobot.asgi:application`
- **Port** : 8000
- **Fichier de démarrage** : `Start0 - terminal.bat`
- **Rôle** : Serveur HTTP/WebSocket principal, APIs Django

### **Terminal 2 : Service Heartbeat**
- **Commande** : `python manage.py run_heartbeat`
- **Fichier de démarrage** : `Start1 - Heartbeat.bat`
- **Rôle** : WebSocket Binance, signaux temporels, bougies OHLCV

### **Terminal 3 : Trading Engine**
- **Commande** : `python manage.py run_trading_engine`
- **Rôle** : Écoute Heartbeat, exécution des stratégies

### **Terminal 4 : Frontend Vue.js**
- **Commande** : `npm run dev`
- **Port** : 5173
- **Rôle** : Interface utilisateur

### **Terminal 5 : Exchange Gateway (NATIF)**
- **Commande** : `python manage.py run_native_exchange_service`
- **Fichier de démarrage** : `Start2 - Terminal 5 _ Native Exchange Service.bat`
- **Rôle** : APIs natives exchanges (Bitget, Binance, KuCoin, Kraken)

## 📦 **FICHIERS DE SERVICES**

### **Services de Production**
- ✅ `backend/apps/core/management/commands/run_heartbeat.py`
- ✅ `backend/apps/core/management/commands/run_native_exchange_service.py`
- ✅ `backend/apps/core/management/commands/run_trading_engine.py`

### **Services de Test/Référence**
- 🧪 `backend/apps/core/management/commands/run_working_native_service.py` (version de référence validée)
- 🧪 `backend/apps/core/management/commands/run_simple_native_service.py` (version test simple)

### **Services Obsolètes (post-migration)**
- ❌ `backend/apps/core/management/commands/run_ccxt_service.py` (ancien Terminal 5 CCXT)

## 🔄 **ARCHITECTURE DE COMMUNICATION**

### **Channels Redis**
- `heartbeat` : Terminal 2 → Terminal 3
- `ccxt_requests` : Terminal 1/3 → Terminal 5 (réutilise canal existant)
- `ccxt_responses` : Terminal 5 → Terminal 1/3 (réutilise canal existant)
- `websockets` : Tous → Terminal 1 → Frontend

### **Services Clients**
- **ExchangeClient** : `backend/apps/core/services/exchange_client.py`
- **BitgetNativeClient** : `backend/apps/core/services/bitget_native_client.py`
- **NativeExchangeManager** : `backend/apps/core/services/native_exchange_manager.py`

## 📋 **ORDRE DE DÉMARRAGE**

1. **Terminal 1** : `daphne aristobot.asgi:application`
2. **Terminal 2** : `python manage.py run_heartbeat`
3. **Terminal 5** : `python manage.py run_native_exchange_service`
4. **Terminal 4** : `npm run dev`
5. **Terminal 3** : `python manage.py run_trading_engine` (optionnel)

## 🎯 **MIGRATION COMPLETED**

- ✅ **Terminal 5** : Migration CCXT → Natif terminée
- ✅ **Performance** : ~56% d'amélioration sur les requêtes
- ✅ **Compatibilité** : Interface ExchangeClient préservée
- ✅ **Base de données** : Symboles depuis PostgreSQL
- ✅ **Erreurs PostgreSQL** : Limites décimales corrigées

Date de migration : 8 septembre 2025