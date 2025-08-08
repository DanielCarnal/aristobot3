# SPECIFICATIONS ARISTOBOT3

**!!!! Version d'origine du projet pour archve !!!!**
**!!! Suivre Aristobot3.md qui est à jours !!!**


## 🎯 Philosophie du projet

**Aristobot V3** est un reboot pragmatique d'un bot de trading crypto personnel, développé en mode "vibe coding" avec l'aide d'IA.

### Principes fondamentaux

* **Fun > Perfection** : Le plaisir de développer prime sur la perfection technique
* **Shipping > Process** : Livrer des fonctionnalités plutôt que suivre des processus
* **Pragmatique > Enterprise** : Solutions simples pour un projet personnel (5 users max)
* **Itération rapide** : Cycles courts, feedback immédiat, amélioration continue

### Limites du projet

* Maximum 5 utilisateurs
* Maximum 20 stratégies (une paire = une stratégie)
* Développement avec Claude Code et VS Code
* Environnement Conda Python 3.11

## 🏗️ Architecture technique

### Stack technologique (FIXE - Ne pas changer)

* **Backend** : Django 4.2.15 + Django Channels (WebSocket)
* **Base de données** : PostgreSQL (tout : users, trades, stratégies, bougies)
* **Frontend** : Vue.js 3 avec WebSocket temps réel
* **Exchanges** : CCXT pour intégration multi-exchanges
* **Serveur** : Daphne ASGI
* **Cache/Messaging** : Redis pour Django Channels
* **Parallélisme** : asyncio (pas de Celery)

### Structure du projet

```
Aristobot3/
├── backend/
│   ├── aristobot/              # Configuration Django principale
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py            # Config ASGI pour WebSocket
│   │   └── routing.py         # Routes WebSocket
│   ├── apps/
│   │   ├── core/              # Services partagés + Heartbeat
│   │   │   ├── management/commands/
│   │   │   │   └── run_heartbeat.py
│   │   │   ├── consumers.py   # WebSocket publishers
│   │   │   └── models.py      # Modèles partagés
│   │   ├── accounts/          # Gestion utilisateurs Django standard
│   │   ├── brokers/           # Gestion des brokers/exchanges
│   │   ├── market_data/       # Stockage et gestion des bougies
│   │   ├── strategies/        # CRUD des stratégies
│   │   ├── trading_engine/    # Exécution des trades
│   │   │   └── management/commands/
│   │   │       └── run_trading_engine.py
│   │   ├── trading_manual/    # Trading manuel
│   │   ├── backtest/          # Backtesting
│   │   ├── webhooks/          # Réception webhooks TradingView
│   │   └── stats/             # Statistiques
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── views/             # Pages Vue.js
│   │   ├── components/        # Composants réutilisables
│   │   ├── api/              # Appels API
│   │   ├── websocket/        # Gestion WebSocket
│   │   └── design-system/    # Tokens et styles
│   │       ├── tokens.js     # Design tokens
│   │       └── README.md     # Documentation design
│   ├── package.json
│   └── vite.config.js
├── docs/
│   └── design/               # Mockups et références visuelles
├── .env.example
├── .gitignore
├── .claude-instructions      # Instructions pour Claude Code
└── README.md
```

## 📡 Services auto-démarrés

### Lancement de l'application

```bash
# Terminal 1 : Serveur web + WebSocket
daphne aristobot.asgi:application

# Terminal 2 : Service Heartbeat (lecture Binance)
python manage.py run_heartbeat

# Terminal 3 : Service Trading Engine (exécution stratégies)
python manage.py run_trading_engine
```

### Service Heartbeat (`core/management/commands/run_heartbeat.py`)

Ce service démarre immédiatement au lancement, sans avoir besoin qu'un client web se connecte.

**Fonctions :**

* Lit le stream WebSocket Binance
* Analyse les timeframes : 1min, 3min, 5min, 10min, 15min, 1h, 2h, 4h
* Publie dans le channel "Heartbeat" chaque bougie de clôture
* Publie dans le channel "StreamBrut" le stream Binance temps réel
* Enregistre toutes les bougies clôturées dans PostgreSQL avec timestamp d'enregistrement et timestamp de la bougie

### Service Trading Engine (`trading_engine/management/commands/run_trading_engine.py`)

Ce service démarre immédiatement et écoute le Heartbeat.

**Fonctions :**

* Pour chaque signal dans "Heartbeat", recherche les stratégies actives (plage de date début/fin, timeframe correspondant)
* Lance les calculs de la stratégie
* Passe les ordres d'achat et positionne StopLoss/TakeProfit
* Enregistre le trade dans PostgreSQL
* Toutes les minutes, vérifie les trades en cours et leur statut (TP/SL atteints)
* Utilise `asyncio` pour le parallélisme

## 🎨 Frontend Global

### Barre de status

* Stratégie live en cours
* Heartbeat Actif/Inactif
* Heartbeat cohérent ou non

### Menu principal

* Heartbeat
* Trading manuel
* Trading BOT
* Stratégies
* Backtest
* Webhooks
* Statistiques
* Mon compte

### Layout

* Sidebar fixe à gauche (menu)
* Header fixe avec status bar
* Zone principale scrollable
* Style dark mode crypto avec couleurs néon
* Responsive desktop first
* WebSocket pour mises à jour temps réel sans rechargement page

## 🎨 Design System

### Couleurs

* **Primary** : #00D4FF (Bleu électrique)
* **Success** : #00FF88 (Vert néon)
* **Danger** : #FF0055 (Rouge trading)
* **Background** : #0A0A0A (Noir profond)
* **Surface** : #1A1A1A (Gris foncé)
* **Text** : #FFFFFF

### Style

* Dark mode crypto/trading inspiré de Binance, TradingView
* Cards avec fond sombre et bordure subtile luminescente
* Frontend Vue 3 Composition API uniquement
* Desktop first (traders utilisent des écrans larges)
* Design tokens dans `frontend/src/design-system/tokens.js`

## 📦 Applications Django

### 1. Heartbeat (`apps/heartbeat/`)

**Description :** Affichage du Heartbeat en temps réel

**Backend :**

* S'abonne au channel "Heartbeat" (publié par le service)
* S'abonne au channel "StreamBrut" (publié par le service)
* API REST pour configuration

**Frontend :**

* Affichage temps réel du stream (20 éléments, scrollable sur 60)
* Bougies de clôture affichées en vert
* Affichage des signaux par timeframe dans des cases adaptées

**PostgreSQL :**

* Lecture des configurations si nécessaire

### 2. User Account (`apps/accounts/`)

**Description :** Gestion des utilisateurs

**Backend :**

* Utilise le système d'authentification Django standard
* Fonctions CRUD pour profils utilisateurs
* Gestion du broker par défaut

**Frontend :**

* Gestion des mots de passe (CRUD)
* Gestion du Broker par défaut

**PostgreSQL :**

* Table Django User standard
* Table pour broker par défaut (relation User → Broker)

### 3. Trading Manuel (`apps/trading_manual/`)

**Description :** Passer des ordres d'achat/vente et voir les actifs en cours

**Backend :**

* Fonctions de connexion aux brokers via CCXT
* CRUD des brokers
* Passage d'ordres (achat/vente, limite/marché)
* Recherche des actifs en cours
* Enregistrement des trades

**Frontend :**

* Affichage et gestion des brokers (CRUD)

* Affichage des assets en cours avec totaux

* Sélection des paires (USDT, USDC, USD)

* Zone de saisie du trade :

  * Saisie quantité → calcul valeur USD
  * Saisie montant → calcul quantité
  * Boutons achat/vente
  * Type de transaction (limite/marché)

**PostgreSQL :**

* Table brokers (id, user\_id, name, description, default)
* Table trades (timestamp, type, transaction\_type, price, quantity)

### 4. Backtest (`apps/backtest/`)

**Description :** Tester une stratégie sur une plage de dates

**Backend :**

* CRUD des backtests
* Charge les données depuis PostgreSQL ou exchange
* Calculs de stratégie (date/heure, prix, gains, %)
* WebSocket pour avancement en temps réel
* Enregistrement des résultats
* Interruption possible des calculs

**Frontend :**

* Liste et gestion des stratégies (CRUD)
* Sélection : dates, broker, timeframe, asset, montant initial
* Bouton interruption des calculs
* Affichage statistiques et liste des trades

**PostgreSQL :**

* Table stratégies
* Table bougies historiques
* Table résultats backtest

### 5. Stratégies (`apps/strategies/`)

**Description :** Création de stratégies avec indicateurs techniques et assistant IA

**Backend :**

* CRUD des stratégies
* Validation syntaxe Python
* Template de base pour stratégies

**Frontend :**

* Gestion des stratégies (CRUD)
* Éditeur de code (classe Python)
* Assistant IA avec prompt
* Bouton test syntaxe

**PostgreSQL :**

* Table stratégies (code Python, paramètres)

### 6. Trading BOT (`apps/trading_engine/`)

**Description :** Activation et monitoring des stratégies live

**Backend :**

* Enregistrement des stratégies dans la DB
* Parcour les stratégies, trouve les stratégies actives et lance les calculs
* Calcul des stats (10 derniers trades, P\&L)
* Gestion des ordres de vente automatique en fonction calculs effectué par les stratégies actives

**Frontend :**

* Sélection : stratégie, broker, asset, dates
* Liste stratégies actives
* Boutons : Vendre (ordre immédiat), Stop (désactive)
* Affichage 10 derniers trades et solde

**PostgreSQL :**

* Table stratégies actives (dates, asset, timeframe, broker)
* Lecture des trades

### 7. Webhooks (`apps/webhooks/`)

**Description :** Réception signaux TradingView (service indépendant)

**Backend :**

* Endpoint webhook
* Passage d'ordres selon signal
* Enregistrement des trades

**Frontend :**

* Affichage webhooks reçus
* Résultats des ordres placés

**PostgreSQL :**

* Table webhooks reçus
* Table trades webhooks

### 8. Statistiques (`apps/stats/`)

**Description :** Évolution du solde par broker

**Backend :**

* Calculs évolution globale
* Calculs par stratégie
* Calculs par webhook

**Frontend :**

* Sélection compte broker
* Affichage graphiques et stats

**PostgreSQL :**

* Lecture des trades pour calculs

## 🤖 Instructions Claude Code

### Fichier `.claude-instructions`

```markdown
# Aristobot3 - Instructions Claude Code

## Contexte
Bot de trading crypto personnel en Django/Vue.js pour 5 users max.
Approche pragmatique : shipping > perfection.

## Structure stricte
- Backend Django dans `/backend/apps/`
- Frontend Vue.js dans `/frontend/src/`
- Services auto-démarrés dans `apps/*/management/commands/`
- WebSocket via Django Channels

## Conventions de code
- Python : PEP 8, type hints quand utile
- Vue 3 Composition API uniquement
- Pas de commentaires inutiles
- Noms de variables en anglais

## Base de données
- PostgreSQL uniquement
- Django ORM (pas de SQL brut)
- Migrations Django

## À ne PAS faire
- Pas de microservices
- Pas de Celery (utiliser asyncio)
- Pas de MongoDB
- Pas d'over-engineering
```

### Template de prompt optimal

```
Contexte : [App Django concernée]
Objectif : [Ce que doit faire la fonctionnalité]
Backend : [Endpoints, modèles, logique]
Frontend : [Composants Vue, style attendu]
Contraintes : [Limites techniques]
```

## 🚀 Initialisation du projet

### Commandes d'initialisation

```bash
# Créer l'environnement Conda
conda create -n aristobot3 python=3.11
conda activate aristobot3

# Installer les dépendances backend
pip install django==4.2.15 djangorestframework django-cors-headers
pip install channels channels-redis daphne
pip install psycopg2-binary python-dotenv
pip install ccxt

# Créer le projet Django
django-admin startproject aristobot backend
cd backend

# Créer les applications
python manage.py startapp core
python manage.py startapp accounts
# ... etc pour chaque app

# Frontend
cd ../frontend
npm init vue@latest .
npm install axios
```

### Requirements backend

```txt
django==4.2.15
djangorestframework
django-cors-headers
channels
channels-redis
daphne
psycopg2-binary
python-dotenv
ccxt
redis
```

### Package.json frontend

```json
{
  "dependencies": {
    "vue": "^3.x",
    "vue-router": "^4.x",
    "pinia": "^2.x",
    "axios": "^1.x"
  }
}
```

## 📋 Points techniques importants

1. **Architecture monolithe modulaire** : pas de microservices
2. **WebSocket via Django Channels** : communication temps réel
3. **PostgreSQL pour tout** : users, trades, stratégies, bougies
4. **asyncio pour le parallélisme** : pas de Celery
5. **Services auto-démarrés** : management commands Django
6. **Vibe coding optimisé** : structure claire pour l'IA

***

**Note pour Claude Code :** Ce document contient toutes les spécifications d'Aristobot3. Commence par créer la structure de base du projet en suivant ces spécifications. Utilise la philosophie "Fun > Perfection" et privilégie des solutions simples et pragmatiques.
