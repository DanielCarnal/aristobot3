# Aristobot3 🚀

Bot de trading crypto personnel développé avec Django et Vue.js selon les spécifications du fichier `SPECIFICATIONS.md`.

## 🎯 Philosophie

**Fun > Perfection** - Projet personnel pragmatique pour 5 utilisateurs max avec 20 stratégies maximum.

## 🏗️ Architecture

- **Backend**: Django 4.2.15 + Django Channels (WebSocket)
- **Frontend**: Vue.js 3 + Vite + Vue Router + Pinia
- **Database**: PostgreSQL (tout : users, trades, stratégies, bougies)
- **Cache/Messaging**: Redis pour Django Channels
- **Exchange**: CCXT pour intégration multi-exchanges
- **Serveur**: Daphne ASGI
- **Parallélisme**: asyncio (pas de Celery)

## 🚀 Installation complète

### Étape 1: Prérequis système

- **Python 3.11** (via Conda recommandé)
- **Node.js 18+**
- **PostgreSQL** (avec base de données `aristobot3`)
- **Redis** (pour Django Channels)

### Étape 2: Environnement Conda

```bash
# Créer l'environnement
conda create -n aristobot3 python=3.11
conda activate aristobot3
```

### Étape 3: Configuration base de données

```bash
# Copier et configurer les variables d'environnement
cp .env.example .env

(Aristobot3) C:\Users\dac\Documents\Python\Django\Aristobot3>psql -U postgres -h localhost -p 5432
Mot de passe pour l'utilisateur postgres : :-) --> aristobot
psql (17.5)
Attention : l'encodage console (850) diffère de l'encodage Windows (1252).
            Les caractères 8 bits peuvent ne pas fonctionner correctement.
            Voir la section « Notes aux utilisateurs de Windows » de la page
            référence de psql pour les détails.
Saisissez « help » pour l'aide.

postgres=# CREATE DATABASE Aristobot3;
CREATE DATABASE
postgres=# GRANT ALL PRIVILEGES ON DATABASE aristobot3 TO postgres;
GRANT
postgres=# \q

# Éditer .env avec tes paramètres :
# - DB_NAME=Aristobot3
# - DB_USER=postgres
# - DB_PASSWORD=aristobot
# - BINANCE_API_KEY=ta_clé_binance (optionnel pour le début)
```

### Étape 4: Backend Django

```bash
cd backend

# Installer les dépendances
pip install -r requirements.txt

# Migrations Django
python manage.py makemigrations
python manage.py migrate

> ✅ Problèmes résolus :
> * Nom de base de données : Aristobot3 → aristobot3 dans .env
> * Encodage UTF-8 : Configuration forcée dans Django avec client_encoding=UTF8
> * Chemin du fichier .env : Correction du load_dotenv() pour pointer vers la racine


# Créer un superuser pour l'admin
# djangoadmin / aristobot (daniel.carnal@gmail.com)
python manage.py createsuperuser
```

### Étape 5: Frontend Vue.js

```bash
cd frontend

# Installer les dépendances
npm install
```

## 🎮 Lancement de l'application

⚠️ **IMPORTANT**: L'application nécessite **4 terminaux** pour fonctionner correctement.

### Terminal 1: Serveur Web + WebSocket
```bash
cd backend
conda activate aristobot3
daphne aristobot.asgi:application
```
➡️ Accessible sur http://localhost:8000

### Terminal 2: Service Heartbeat (auto-démarré)
```bash
cd backend
conda activate aristobot3
python manage.py run_heartbeat
```
➡️ Lit le stream Binance et publie dans les channels WebSocket

### Terminal 3: Trading Engine (auto-démarré)
```bash
cd backend
conda activate aristobot3
python manage.py run_trading_engine
```
➡️ Écoute le Heartbeat et exécute les stratégies actives

### Terminal 4: Frontend Vue.js
```bash
cd frontend
npm run dev
```
➡️ Interface utilisateur sur http://localhost:5173

## 📡 Services Auto-démarrés

### Service Heartbeat (`run_heartbeat.py`)
- ⚡ Lit le stream WebSocket Binance temps réel
- 📊 Analyse les timeframes : 1min, 3min, 5min, 10min, 15min, 1h, 2h, 4h
- 📢 Publie dans le channel "Heartbeat" chaque bougie de clôture
- 📡 Publie dans le channel "StreamBrut" le stream Binance brut
- 💾 Enregistre toutes les bougies clôturées dans PostgreSQL

### Service Trading Engine (`run_trading_engine.py`)
- 👂 Écoute les signaux "Heartbeat"
- 🔍 Recherche les stratégies actives (dates, timeframe correspondant)
- ⚙️ Lance les calculs de stratégie
- 💰 Passe les ordres d'achat/vente et positionne StopLoss/TakeProfit
- 📈 Vérifie toutes les minutes les trades en cours (TP/SL atteints)
- 🚀 Utilise `asyncio` pour le parallélisme

## 🎨 Design System

**Style dark mode crypto** inspiré de Binance et TradingView :
- **Primary**: `#00D4FF` (Bleu électrique)
- **Success**: `#00FF88` (Vert néon)
- **Danger**: `#FF0055` (Rouge trading)
- **Background**: `#0A0A0A` (Noir profond)
- **Surface**: `#1A1A1A` (Gris foncé)

➡️ Détails complets dans `frontend/src/design-system/`

## 📱 Applications Frontend

| Page | Description | Fonctionnalités |
|------|-------------|-----------------|
| 📡 **Heartbeat** | Stream temps réel | Affichage stream Binance, signaux par timeframe |
| 📈 **Trading Manuel** | Ordres manuels | CRUD brokers, passage d'ordres, visualisation assets |
| 🤖 **Trading BOT** | Stratégies live | Activation stratégies, monitoring P&L, vente manuelle |
| ⚡ **Stratégies** | Création/édition | Éditeur code Python, assistant IA, validation syntaxe |
| 🔄 **Backtest** | Tests historiques | Sélection dates/asset, calculs avec progression temps réel |
| 🔗 **Webhooks** | Signaux TradingView | Réception webhooks, passage d'ordres automatique |
| 📊 **Statistiques** | Analyse performance | Évolution solde par broker, stats par stratégie |
| 👤 **Mon compte** | Gestion utilisateur | Profil, mots de passe, broker par défaut |

## 🛠️ Structure du projet

```
Aristobot3/
├── backend/                 # Django 4.2.15
│   ├── aristobot/          # Configuration principale
│   └── apps/               # 10 applications Django
│       ├── core/           # Services partagés + Heartbeat
│       ├── accounts/       # Gestion utilisateurs
│       ├── brokers/        # Gestion brokers/exchanges
│       ├── market_data/    # Stockage bougies
│       ├── strategies/     # CRUD stratégies
│       ├── trading_engine/ # Exécution trades
│       ├── trading_manual/ # Trading manuel
│       ├── backtest/       # Backtesting
│       ├── webhooks/       # TradingView webhooks
│       └── stats/          # Statistiques
├── frontend/               # Vue.js 3 + Vite
│   ├── src/
│   │   ├── views/          # 8 pages principales
│   │   ├── components/     # Composants réutilisables
│   │   ├── design-system/  # Tokens et styles
│   │   └── websocket/      # Gestion WebSocket temps réel
└── docs/                   # Documentation et mockups
```

## 🔧 Développement

### Variables d'environnement importantes

```bash
# Base de données
DB_NAME=aristobot3
DB_USER=postgres
DB_PASSWORD=ton_password

# APIs exchanges (optionnel pour débuter)
BINANCE_API_KEY=ta_clé
BINANCE_SECRET_KEY=ton_secret
```

### Commandes utiles

```bash
# Migrations après modification des modèles
python manage.py makemigrations
python manage.py migrate

# Accès admin Django
http://localhost:8000/admin/

# Tests (quand implémentés)
python manage.py test

# Shell Django pour debug
python manage.py shell
```

## 🚨 Dépannage

### Problème : WebSocket ne se connecte pas
- Vérifier que Redis est démarré
- Vérifier que Daphne tourne sur le bon port

### Problème : Heartbeat ne reçoit pas de données
- Vérifier la connexion internet
- Les clés Binance ne sont pas obligatoires pour le stream public

### Problème : Frontend ne trouve pas le backend
- Vérifier que le backend tourne sur `localhost:8000`
- Vérifier la configuration CORS dans `settings.py`

---

## 📝 Notes de développement

- **Philosophie** : "Fun > Perfection" - Shipping rapide et itératif
- **Limites** : 5 utilisateurs max, 20 stratégies max
- **Architecture** : Monolithe modulaire (pas de microservices)
- **Base de données** : PostgreSQL pour tout (pas de MongoDB)
- **Parallélisme** : asyncio uniquement (pas de Celery)

*Développé avec ❤️ et Claude Code selon les spécifications du fichier `SPECIFICATIONS.md`*