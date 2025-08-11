BROUILLON 

Frontend Global - Affichage d'une barre de status "stratégie live en cours" , "Hertbeat Actif/inactif", "Heartbeat cohérant ou non" - Affichage du menus "Heartbeat | Trading manuel | Trading BOT | Statégies | Backtest | Webhooks | Statistiques | Moncompte"

Backend Global Ces services démarrent immédiatement au lancement du serveur, sans avoir besoin qu'un client web se connecte.

Gestion du "Heartbeat" - Fait un channel "Heartbeat" qui permet aux apps Django de se connecter et d'exécuter une action spécifique en fonction du signal publié - Fait un channel "StreamBrut" pour publier le strem Websocket de Binance - Lit le stream WebSocket Binance. - Analyse le stream 1min, 3min, 5min, 10min, 15min, 1h, 2h, 4h - Publier dans "Hertbeat" chaque bougie de clôture - Enregistre toutes les bougies clôturée dans des collections spécifique dans PostgeSQL "Date/Heure/min de lenregistrement et date/heure/min de la bougie de clôture"

Stratégies Pour chaque signal dans "Hertbeat", recherche dans PostgeSQL si une stratégie est active (plage de date début et fin de validité de la stratégie), que le timeframe correspond (1h par ex.). Si c'est le cas, lance les calculs de la stratégie, et en fonction du résultat, lance l'ordre achat, et positionne les StopLoss et TakeProfit calculés. Enregistre dans PostgeSQL le trade (date/heure/min, quantité, prix, asset, TP et SL). Toutes les "1min", vérifier dans PostgeSQL si un trade est encours. Si c'est le cas vérifier s'il est actif (Take Profit ou Stop loss programmés). Si la position n'existe plus (TP ou SL atteint), rechercher la transaction avec les API CCXT adhoc. Calculer la perte/profit. Enregistre dans MongDB la vente (date/heure/min, quantité, prix, perte/profit) **Faut-il prévoir les calculs en parallèle ? multi tâche / multi process ? qu'est-ce qui est le mieux pour Django?**

webhooks Reçoit un webhook de Tradingview. En fonction du contenu, un ordre est déclanché, comme pour Stratégies de Backent Global

Divers - Prévoir une vérification de la cohésion des bougies enregistées et de la date et heure actuelle ?? Point à réfléhir, ne pas implémenter

Liste des apps Django: - Heartbeat: Description Affichage du Heartbeat. Backend S'abonner au channel fait par le backend global "Heartbeat" S'abonner au channel fait par le backend global "StreamBrut" frontend Dans la case temps réel afficher le stream en cours et si une bougie de clôture se présente elle est affichée en vert. La liste temps réel affiche 20 éléments et est scollable sur 60. Exceptionellement, le calcul Affichage des signaux pour chaques timeframe dans une case adaptée à son timeframe. PostgeSQL Pas d'utilisté pour le moment

* User account : Description Gestion des utilisateurs Backend Fonctions de gestion des enreistrements des utilisateurs (CRUD) frontend Gestion des mots de passe (CRUD) Gestion du Broker par défaut MongDB Enregistrement des utilisateurs (ID, User name, password) Enregistrement du Brocker par défaut (ID de l'utilisateur, ID du Broker)

* Trading manuel: Utilisatation: Passer des ordres d'acaht et ventes et voir les actifs en cours Backend Fonctions de gestion de la connexion au brocker Fonctions pour la gestion des enregitrements en DB des Brocker (CRUD) Fonctions pour passer les ordres d'achat et vente sur le brocker sélectionnée Fonction de recherche des actifs en cours Fonction d'enregistrement des trades frontend

  * Affichage des Brocker, gestion (CRUD)
  * Affichage des assets en cours, avec total
  * Affichage/Sélection de la liste des assets face à USDT, USDC, USD,
  * Zone de siasie du trade: Saisie de la quantité -> Calcul de la valeur en USD? ou du montant -> qualcul de la quantité Bouton achat, Bouton vente, Sélectionner le type de transaction (Limite ou au marché) PostgeSQL Enregistrement des brockers (ID, ID user, Brocker Name, Description, Défaut(oui/non)) Enregistrement des trades (Date Heure Minute, Acaht/vente, type de transaction, prix, quantité)

  Description complète -> `[root path]\`

* Backtest: Utilisatation: Tester une stratégie sélectionnée sur une plage de date, un asset et un time frame. Backend Effectue les travaux de gestion (CRUD) Charge les données 1) de PostgeSQL ou de l'exchange Effectue les calculs de la statégie (date/heure ouverture et fermeture, prix achat et vente, gain, gain en%) Envoie au frontend une information de l'avancement des calculs en temps réel (Avencement en % calculé entre date début et fin) Enregistre les résultats des calculs dans PostgeSQL Arrêt des calculs en cas de signal reçu du frontend frontend Affichage de la liste des stratégies et gestion (CRUD) Sélection et lancement des calculs de la statégie pour les dates début/fin, broker, timeframe, asset et montant de départ Permettre d'interrompre le calcul en cours Affiche les statistiques de la stratégie Affiche la liste des trades PostgeSQL Enregistre les stratégies (CRUD) Enregistre les bougies de la plage de date, asset, timeframe Enregistre le résultat du backtest de la stratégie et de tous les trades passés Description complète -> `[root path]\`

* Stratégies: Utilisatation: Ajout, supression et cération de stratégie de trading en utilisant des indicateurs technique. Un assistant IA est à disposition pour pour la mise en forme de la classe python, basée sur un template. Backend Effectue les travaux de gestion du CRUD des stratégies Demande du frontend "test de ls stratégie", lancer une procédure de validation de la syntaxe de la stratégie. Retourner le message d'erreur le cas échéant. frontend Affichage de la gestion des stratégies (CRUD). Sélection de la statégie pour modification. Affichage du contenu (classe python) Affichage d'un assistant IA permettant la saisie d'un prompt aidant l'utilisateur à développer la stratégie. Bouton de test "à vide" pour garantir la syntaxe. Afficher le résultat retourné par le Backend PostgeSQL Enregistrer la stratégie (CRUD) Description complète -> `[root path]\`

* Trading BOT: Utilisatation: Permet de sélectionner les stratégies à activer et d'afficher les stratégies en cours pour l'utilisateur La stratégie est dite active si la date/heure de début est plus petite que la date/heure du jours et la date/heure de fin plus grande que la date/heure de fin. Backend Enregistrer la stratégie sélectionnée dans le frontend avec les données saisies Calcul des données à afficher (10 derniers trades) et calcul des perte/profit par trades et du solde. frontend Sélectionner la stratégie, le brocker, l'asset, la date de début et de fin Liste des stratégies actives. Bouton vendre. Bouton Stop. Bouton vendre déclanche un ordre de vente immédiat au marché, sans arrêter la stratégie. Bouton Stop initialise date/heure début et date heure fin à 01.01.01:00h00 Pour chaque stratégie, affiche les 10 derniers trades (perte/profit) et le solde PostgeSQL Enregistre la stratégie sélectionné avec date de début et date de fin, asset, timeframe, brocker Lecture des derniers trades webhook Utilisatation: Signal reçu de Tradingview par webhook. Le signal contient les instructions pour passer un ordre d'achat ou de ventes C'est un service indépendant des Stratégies Backend Fonctions pour passer les ordres au Brocker Enregistre les trades passés frontend affiche les webhook reçu affiche le résultat des ordres placé par le Backend PostgeSQL Fonctions d'enregistrement des trades Statistiques Utilisatation: Affichage de l'évolution du solde du compte Brocker sélectionné backend Réception du compte brocker à calculer Fonctions de lecture dans PostgeSQL pour les trades passés Claculs de l'évolution globale du solde Calculs de l'évolution par stratégies Calculs de l'évolution par webhook frontend Sélection des Compts Brocker Affichage des Statistiques calculées par le Backend PostgeSQL Fonctions de lecture des données nécessaire aux calculs à effectur par le Backend.
===================================================
Suite à ce brouillon, nous avons établis un fichier SPECIFICATIONS.md. Le voici:

# SPECIFICATIONS ARISTOBOT3

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


## 📋 Points techniques importants

1. **Architecture monolithe modulaire** : pas de microservices
2. **WebSocket via Django Channels** : communication temps réel
3. **PostgreSQL pour tout** : users, trades, stratégies, bougies
4. **asyncio pour le parallélisme** : pas de Celery
5. **Services auto-démarrés** : management commands Django
6. **Vibe coding optimisé** : structure claire pour l'IA

***

**Note pour Claude Code :** Ce document contient toutes les spécifications d'Aristobot3. Commence par créer la structure de base du projet en suivant ces spécifications. Utilise la philosophie "Fun > Perfection" et privilégie des solutions simples et pragmatiques.
=============================================
Puis nous avons créé le projet (README.md)
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

=============================================
puis, j'ai commencé le développement avec Claude Code. 
Voici ce que je lui ai demandé: "Lis .claude-instructions et SPECIFICATIONS.md et dis moi quelle sont les étapes suivantes. Ne commence rien sans mon accord".

Voici sa réponse:
"● D'après les fichiers .claude-instructions et SPECIFICATIONS.md, voici les étapes suivantes à réaliser :
  📋 État actuel
  - ✅ Toutes les étapes du README.md sont terminées et fonctionnelles
  - ✅ Les 4 services sont opérationnels (Web, Heartbeat, Trading Engine, Frontend)
  🎯 Étapes suivantes possibles
  1. Amélioration des fonctionnalités existantes
  - Optimiser l'interface utilisateur (design tokens, responsive)
  - Ajouter plus d'indicateurs techniques aux stratégies
  - Améliorer les statistiques et graphiques
  2. Nouvelles fonctionnalités
  - Intégration d'autres exchanges (via CCXT)
  - Système de notifications (email, Telegram)
  - Gestion avancée du risk management
  3. Monitoring et stabilité
  - Logs détaillés pour debug
  - Dashboard de monitoring des services
  - Tests automatisés
  4. Features premium
  - Copy trading
  - Signaux automatisés
  - Analytics avancées
  Quelle direction souhaitez-vous prendre ? Je peux vous proposer des tâches spécifiques selon vos priorités."

A part la mise en place du projet, rien (ou pas grand chose) n'est fait. Je penses que Claude Code n'a pas de plan. Comment en faire un ? Tu peux lire les fichiers cités. Ma demande est "comment utiliser Code Code" et non pas que tu fasses le travail par toi même. Si je ne suis pas clair, pos des questions.

Suite à cela nous avons fait un audit complet et avons lancé une longue discussion pour élaborer le plan complet.

🔍 AUDIT COMPLET - État réel du projet
✅ Ce qui existe vraiment :

Structure des dossiers ✓
Configuration Django de base ✓
Apps Django créées (vides) ✓
Frontend Vue Router configuré ✓
Service Heartbeat basique (WebSocket Binance) ✓
Vue Heartbeat (affichage basique) ✓
Design tokens ✓

❌ Ce qui N'existe PAS :

AUCUN modèle Django défini (tous les models.py sont vides)
AUCUNE API REST (tous les views.py sont vides)
AUCUNE base de données (pas de migrations)
PAS d'authentification
PAS de serializers
Trading Engine : juste un squelette
Toutes les vues frontend : juste des placeholders
=============================================
Tu m'a proposé de faire le plan 

Claude Desktop (moi) vs Claude Code pour le plan
Vous avez raison ! Je suis probablement mieux placé pour créer ce plan initial car :
✅ Mes avantages :

Je viens d'analyser vos fichiers en profondeur
Je comprends votre frustration et le problème
Je peux créer un plan structuré et détaillé
Nous pouvons itérer ensemble sur le plan
Je peux produire un document que vous copierez dans Claude Code

❌ Limitations de Claude Code pour l'analyse initiale :

Peut faire des suppositions incorrectes
Moins de contexte sur votre discussion
Tendance à vouloir avancer vite

💡 Proposition : Créons le plan ensemble ici
Je vais analyser complètement votre projet et créer un plan réaliste. 
et je voulais de soumettre des information et demandes supplémentaires.

		1) je répondrai à tes questions dans un 2ème temps.
		2) Je te soumets tout de même le brouillon. Pose moi des questions par rapport à ce que tu connais déjà
		3) Puis je voudrais que tu m'explique dans un langage humain ce que font chaques applications.
		4) Enfin Je voudrais que tu approfondisse pour chaque applications les besoins de lecture et enristrer des informations dans la DB

Suite à cle voici test questions, mes réponces sont dans le texte=============================================

## 1. Base de données - Clarification critique
 PostgreSQL uniquement
On oublie MongoDB
### 2. Heartbeat - Précisions sur l'affichage
* "20 éléments scrollable sur 60" - Voulez-vous dire :
Il faut afficher 20 lignes visibles en permanence et une scrollbar qui permet de faire défiler les suivantes
### 3. Trading BOT - Comportement des boutons
* Bouton "Vendre" : ordre immédiat sans arrêter la stratégie - OK
* Bouton "Stop" : vous mettez les dates à "01.01.01:00h00" - est-ce une façon de "désactiver" ? Pourquoi pas simplement un flag  ?
Le but est d'éviter qu'une stratégie s'active suite à une mauvaise manipulation. Garde la notion de "01.01.01:00h00" et ajoute un flag "active=False". Prévoir le bouton adhoc. Cela permettrais de suspendre temporairement la stratégie. Quid d'un trade en cours ? -> Prévenir par un message qu'un trade est en cours.
### 4. Stratégies - Template Python
* Vous mentionnez un "template de base" pour les stratégies
* Avez-vous déjà une idée de la structure de ce template ?
<!-- 
from aristobot.strategies import Strategy
import aristobot.indicators as ta
from aristobot import utils
class JustAnotherStrategy(Strategy):
    def should_long(self) -> bool:
        return False
    def should_short(self) -> bool:
        # For futures trading only
        return False

    def go_long(self):
        pass
    def go_short(self):
        # For futures trading only
        pass
-->

Doit-il hériter d'une classe de base ? Je te laisse proposer la meilleure solution. Ce code doit s'afficher dans une fenêtre permettant sa saisie et son enregistrement par ex. "JustAnotherStrategy". Ce code s'intègre au reste de l'application Django lorsque la stratégie est active 
### 5. Webhooks vs Stratégies
Les webhooks sont "indépendants des stratégies"
Mais ils font la même chose (passer des ordres)
Différence principale : webhook = signal externe, stratégie = calcul interne ? EXACTEMENT !! ce sont deux moyens différents de passer des ordres 
### 6. Parallélisme
Vous demandez "multi-tâche/multi-process ?"
Pour Django avec asyncio : multi-tâche asynchrone est idéal
Pas besoin de Celery, asyncio suffit pour 20 stratégies max
D'accord ? OUI 
## 🎯 Ce que j'ai compris des workflows Flux principal :
Heartbeat lit Binance → publie les bougies fermées
Trading Engine écoute → vérifie stratégies actives → passe ordres
Toutes les minutes → vérifie si TP/SL atteints → enregistre résultats Points à confirmer :
Les stratégies calculent uniquement à la fermeture des bougies ? OUI
Pas de calcul en continu sur le prix live ? NON Répondez à ces questions, puis je passerai aux explications en langage humain de chaque application et leurs besoins DB ! Je te donne déjà des précisions pour la DB: Pour chaque utilisateur de Aristobot3, l'utilisateur détient ses propres clé . L'utilisateur peut avoir plusieurs bocker, et plusieurs comptes /sous compte auprès d'un brocker. L'utilisateur dispose de sa propre connection à une IA. Prévoir une route pour OpenRouter et une autre pour Ollama. Seule une route est active Les stratégies appartiennent à l'utilisateur. Plus tard un système de partage ? Les trades sont enregistrés au nom de l'utilisateur et doit mentionner la stratégie Globalement chaque enregistrements dans la DB devra contenir l'identifiant de l'utilisateur
=============================================
Ta réponses:
"Parfait ! J'ai maintenant une vision claire. Passons aux explications"
Dans tes explications j'ai corrigé/ajouté 2-3 précisions.

## 📱 Explication en langage humain de chaque application

### 1. **Heartbeat** 🫀
**Ce que ça fait :** C'est le "cœur" du système qui bat au rythme du marché. Il écoute Binance en temps réel et distribue l'info à tout le système.
- Montre le flux en direct des prix (comme un moniteur cardiaque)
- Signale quand une bougie se ferme (toutes les 1min, 3min, 5min, etc.)
- Garde les 60 derniers battements en mémoire, en montre 20
- **Est utilisé pour déclancher les calculs sur les stratégies**

### 2. **User Account** 👤
**Ce que ça fait :** Gère qui peut utiliser le système et leurs préférences.
- Chaque trader a son compte isolé
- Configure son broker préféré par défaut
- Configure sa connexion IA (OpenRouter ou Ollama local)
- **Peut changer son mot de passe**

### 3. **Trading Manuel** 🎯
**Ce que ça fait :** C'est le tableau de bord pour trader "à la main".
- Connecte plusieurs brokers (Binance, Kraken, etc.)
- Passe des ordres d'achat/vente manuellement
- Montre le portfolio en temps réel
- Calcule automatiquement quantité ↔ valeur USD

### 4. **Trading BOT** 🤖
**Ce que ça fait :** Active et surveille les robots de trading automatiques.
- Active/désactive des stratégies avec dates début/fin
- Bouton "Vendre" = vente d'urgence sans arrêter le robot
- Bouton "Stop" = mise en pause sécurisée
- Montre les 10 derniers trades et le profit/perte
- **Les calculs sont déclanchés grâce au Hertbeat**
- **Si les conditions sont réunies, l'ordre est passé**

### 5. **Stratégies** 🧮
**Ce que ça fait :** L'atelier où on crée les cerveaux des robots.
- Éditeur de code Python pour créer des stratégies
- Assistant IA pour aider à coder
- Test de syntaxe avant activation
- Chaque stratégie hérite d'une classe de base

### 6. **Backtest** ⏮️
**Ce que ça fait :** La machine à remonter le temps pour tester les stratégies.
- Teste une stratégie sur l'historique
- Montre la progression du calcul en temps réel
- Calcule les gains/pertes théoriques
- Peut être interrompu si trop long

### 7. **Webhooks** 📡
**Ce que ça fait :** Reçoit des ordres de TradingView ou autres.
- Écoute les signaux externes
- Passe automatiquement les ordres reçus
- Indépendant des stratégies internes
- Enregistre qui a envoyé quoi et quand

### 8. **Statistiques** 📊
**Ce que ça fait :** Le tableau de bord de performance.
- Évolution du solde global
- Performance par stratégie
- Performance des webhooks
- Graphiques et métriques

## 🗄️ Besoins détaillés en base de données

### Tables principales nécessaires :

#### 1. **users** (Django standard + extensions)
```
- id
- username, email, password (Django)
- default_broker_id (FK)
- ai_provider (choice: 'openrouter'/'ollama')
- ai_api_key (encrypted)
- ai_endpoint_url
- created_at, updated_at
```

#### 2. **brokers**
```
- id
- user_id (FK) ⚠️ Multi-tenant
- name (ex: "Binance Principal")
- exchange (choice: 'binance'/'kraken'/etc.)
- api_key (encrypted)
- api_secret (encrypted)
- subaccount_name (optionnel)
- is_default (boolean)
- is_testnet (boolean)
- created_at, updated_at
```

#### 3. **strategies**
```
- id
- user_id (FK) ⚠️ Multi-tenant
- name
- code (TextField - code Python)
- description
- timeframe (choice: '1m'/'3m'/'5m'/etc.)
- created_at, updated_at
- last_tested_at
- is_valid (boolean)
- error_message (TextField)
```

#### 4. **active_strategies**
```
- id
- user_id (FK) ⚠️ Multi-tenant
- strategy_id (FK)
- broker_id (FK)
- symbol (ex: 'BTCUSDT')
- start_date
- end_date
- is_active (boolean)
- initial_amount
- current_balance
- created_at, updated_at
```

#### 5. **candles** (partagées entre tous les users)
```
- id
- symbol
- timeframe
- open_time
- close_time
- open_price
- high_price
- low_price
- close_price
- volume
- created_at (quand enregistré)
```

#### 6. **trades**
```
- id
- user_id (FK) ⚠️ Multi-tenant
- broker_id (FK)
- strategy_id (FK, nullable)
- webhook_id (FK, nullable)
- symbol
- side ('buy'/'sell')
- order_type ('market'/'limit')
- quantity
- price
- executed_price
- commission
- status ('pending'/'filled'/'cancelled')
- take_profit
- stop_loss
- profit_loss (calculé après vente)
- created_at
- executed_at
```

#### 7. **webhooks**
```
- id
- user_id (FK) ⚠️ Multi-tenant
- source (ex: 'tradingview')
- payload (JSONField)
- action ('buy'/'sell')
- symbol
- quantity
- processed (boolean)
- trade_id (FK, nullable)
- created_at
- processed_at
```

#### 8. **backtest_results**
```
- id
- user_id (FK) ⚠️ Multi-tenant
- strategy_id (FK)
- symbol
- timeframe
- start_date
- end_date
- initial_amount
- final_amount
- total_trades
- winning_trades
- losing_trades
- max_drawdown
- sharpe_ratio
- trades_detail (JSONField)
- created_at
- duration_seconds
```

#### 9. **heartbeat_status** (table système)
```
- id
- is_connected
- last_heartbeat
- symbols_tracked (JSONField)
- timeframes_tracked (JSONField)
- error_message
- updated_at
```

### Points clés pour la DB :

1. **Multi-tenant strict** : Toutes les requêtes doivent filtrer par `user_id`
2. **Encryption** : Les API keys doivent être chiffrées
3. **Indexes** : Sur user_id, symbol, timeframe, dates
4. **Cascade** : Suppression en cascade quand un user est supprimé 
    **--> Point A discuter**
5. **Contraintes** : Une seule stratégie active par symbol/broker/user

Voulez-vous que je continue avec le plan d'implémentation maintenant, ou avez-vous d'autres questions sur ces explications ?

Les points ajouté on permis ton commentaire.
Excellentes remarques ! Vos précisions sont très importantes. Analysons les points clés :
✅ Vos ajouts pertinents
1. Heartbeat → Déclencheur des stratégies
C'est effectivement LE point central du système ! Le flux est :
Heartbeat (bougie fermée) → Trading Engine écoute → Vérifie stratégies actives → Execute calculs → Passe ordres
2. Changement mot de passe
Fonctionnalité basique mais essentielle. Django fournit ça nativement avec PasswordChangeView.
3. Trading BOT - Workflow précisé
Parfait, le flux est clair :

Heartbeat = trigger
Strategy.should_long() = condition
Strategy.go_long() = action

🔍 Point à discuter : Suppression en cascade
Vous avez raison de soulever ce point ! La suppression en cascade des trades est dangereuse
📊 Autre point important : Positions ouvertes
Je remarque qu'il manque peut-être une table pour les positions ouvertes :
=======================================================================================================

🚀 Prochaine étape
Maintenant que nous avons :

✅ Les explications claires
✅ Les besoins DB détaillés
✅ Les points critiques identifiés

Dans quel ordre voulez-vous développer les modules ?
Je suggère cet ordre pragmatique :

Module 1 : Auth + Brokers (base indispensable)
Module 2 : Trading Manuel (tester la connexion réelle)
Module 3 : Heartbeat amélioré + Candles DB
Module 4 : Stratégies + Trading BOT
Module 5 : Backtest + Stats

Qu'en pensez-vous ?  ===========================================================================================================================
	
Voici ma proposition
Je souhaite que tu réfléchisse bien a tout ce que nous avons discuté et ce que je viens de te fournir. C'est maintenant le grand moment, car tout reposera sur toi. Pose encore toutes les questions qui te semblent utiles mêm celles qui te sembles futiles... Je te rappel que c'es Claude Code qui va se charger de la mise en oeuvre. Prévoir le plan en fonction de sa capacité multi agents ?. J'attends tes commentaires et questions.

### 1. User Account (`apps/accounts/`)
Permet de faire le premier accès à l'application
Prévoir un mécanisme permettant un accès identifié mais sans mot de passe durant le développement. Par exemple user "dev" ne passant pas par le login, il a accès a tout de manière inconditionelle. C'est un point à discuter, le but est qu'un agent IA puisse naviguer saus perdre de temps au login.
Permet de valider l'UI (Ecran général et celui de user account.
Permet de programmer les premières fonctions avec CCXT pour valider l'accès au brocker
Rappel, c'est le backend qui fait les connexions, calculs, etc. Le front-end affiche, sélectionne modifie et envoie au backend ce qui a été saisi. Pas plus!
**Préparer un plan détaillés dès que nous sommes d'accord**
### 2. Heartbeat (`apps/heartbeat/`)
Développement primordial, une fois mis en place toute l'architecture est validée
L'affichage des informations se fait sans timer !, c'est le flux qui est affiché
**Prévoir le plan une fois la phase précédente terminée**
### 3. Trading Manuel (`apps/trading_manual/`)
Permet de développer les fonctions d'accès aux brockers par CCXT pour passer les ordres et rechercher des informations sur les marchés.
**Prévoir le plan une fois la phase précédente terminée**
### 7. Webhooks (`apps/webhooks/`)
Permet de tester l'automation rapidement
**Prévoir le plan une fois la phase précédente terminée**
### 5. Stratégies (`apps/strategies/`)
**Prévoir le plan une fois la phase précédente terminée**
### 4. Backtest (`apps/backtest/`)
**Prévoir le plan une fois la phase précédente terminée**
### 6. Trading BOT (`apps/trading_engine/`)
**Prévoir le plan une fois la phase précédente terminée**
### 8. Statistiques (`apps/stats/`)
**Prévoir le plan une fois la phase précédente terminée**
Trading BOT, Webhooks, TradingManuel, User Account utiliseront tous des fonctions de CCXT.
SEUL Heartbeat se connect directement au strem websocket de Binance de manière native		

Tes questions supplémentaires, avec mes réponces dans le texte =================================================================================================================================


Architecture & Infrastructure

Port du backend Django : 8000 par défaut, OK ? OK
Port du frontend Vue : 5173 (Vite par défaut), OK ? OK
Redis : Port 6379 par défaut ? Pas de mot de passe en dev ? PAS DE MOT DE PASSE
PostgreSQL :

Nom de la base : aristobot3 (tout en minuscules) ? OK, existante
User : postgres ? OK
Port : 5432 ? OK

Module 1 - User Account - Questions spécifiques

Utilisateur "dev" sans password :

Un middleware Django qui détecte ?dev=true dans l'URL ? NON
Ou un bouton "Dev Mode" sur la page de login ? NON
Ou auto-login si DEBUG=True dans settings ? OUI, dans quel fichier ? .env ?

Si DEBUG=true
   tout est accessible directement, comme après un login réussi. l'utilisateur identifié est "dev"
   Si l'utilisateur se connecte par le bouton login, il sera identifié pas son login et vérifié correctement
   Si l'utilisateur se déconnecte, l'utilisateur identifié redevient "dev"
Si DEBUG=false
   Afficher la page de login
   Identifier l'utilisateur et donner accès si password correct.
   Déconnection de l'utilisateur, retour à la page de login

Premier utilisateur :

Créé via createsuperuser ? NON
Ou formulaire de "first setup" ? NON
L'agent IA le fait directement en base, user = dac, password = aristobot


Connexion IA (OpenRouter/Ollama) :

Configuration globale ou par utilisateur ?
Par utilisateur
Prévoir OpenRouter   |clé API|   ON/OFF
Prévoir Ollama |suggérer URL par défaut  http://localhost:11434 | ON/OFF
Si Ollama ON, mettre OpenRouter sur Off
SI OpenRouter ON, mettre Ollama Off
Il est possible que les Agents IA soient les deux OFF, dans ce cas, dans l'application Stratégies, l'aide IA ser inactive 


Test CCXT dans User Account :

Juste tester la connexion -> OUI  
ou aussi récupérer le balance ? NON
Mode testnet par défaut pour éviter les vraies transactions ? NON

**Pour testnet, c'est une excellente idée à creuser !!! Par exemple mettre toute l'application en mode testnet ??**
** Il faudra y réfléchir**

Frontend Global

Layout fixe :

Sidebar toujours visible ou collapsible ?
VISIBLE
Largeur sidebar : 250px ?
TU ES LIBRE
Status bar en haut : hauteur 60px ?
TU ES LIBRE

Thème sombre :

Forcer le dark mode ou permettre light/dark ?
PERMETTRE 2 MODES
Les couleurs néon sont-elles obligatoires ou préférées ?
OBLIGATOIRE


WebSocket & Channels

Reconnexion automatique :

Si WebSocket déconnecté, retry toutes les 5 secondes ? OUI
Notification visuelle de déconnexion ? OUI, DANS LA BARRE DE STATUS EN HAUT DE L'ECRAN


Groupes Channels :

Un groupe par user (user_{id}) pour les messages privés ?
PAS COMPRIS, IL FAUT M'EXPLIQUER
Ou tout en broadcast et filtrage côté client ?
PAS COMPRIS, IL FAUT M'EXPLIQUER


CCXT & Trading

Exchanges supportés jour 1 :
PAS COMPRIS
Binance uniquement pour commencer ? PAS COMPRIS
Ou Binance + Binance Testnet ? PAS COMPRIS

Dans la page User Account, l'utilisatuer peut créer autant de comptes qu'il le désire
le CRUD sera en modale, faisant place à la liste des comptes configurés.

Nom de l'exchange | Sous-compte01 | cléAPI                        | défaut |  [AJOUTER]
--------------------------------------------------------------------------------------------------- 
BINANCE           | Sous-compte02 | cléAPI-no-xxxx234asdf32432432 | non    | [Modifier] [Supprimer]  
BINANCE           | Sous-compte01 | cléAPI-no-xxxx23432432sdff432 | non    | [Modifier] [Supprimer]
KUKOIN            | Sous-compte01 | cléAPI-no-xxxx2343243asdf2432 | oui    | [Modifier] [Supprimer]
BITGET            | Sous-compte01 | cléAPI-no-xxxx23432432asdf432 | non    | [Modifier] [Supprimer]



Symboles par défaut :

BTCUSDT uniquement au début ?
NON
Ou liste configurable ?
OUI, mais la liste n'est pas importante ici, elle le sera dans Trading manuel et stratégies

Précision décimale :

8 décimales pour BTC ?
OUI
2 décimales pour USD ?
OUI
Utiliser Decimal Python partout ?
PASCOMPRIS, Peux-tu m'expliquer ?



Sécurité & Encryption

Chiffrement des API keys :

django-cryptography ?
Ou cryptography directement ?
Clé de chiffrement dans .env ?
AU PLUS SIMPLE, pas dans .env

CORS pour le frontend :

Autoriser uniquement localhost:5173 ?
Ou * en dev ?
* en dev, mets en commentaire la modification nécessaire pour la prod


Base de données

Migrations :

Une migration initiale géante ou par module ?
Par module
Fixtures pour données de test ?
Dis moi ce que tu en penses ? si pas vraiment nécessaire non

Index sur les tables :

Les créer dès le début ou optimiser plus tard ?
Dès le début/fin

UUID vs ID :

ID auto-increment classique ou UUID pour les clés primaires ?
ID, le plus simple


Structure du code

Services/Utils partagés :

Créer apps/core/services/ccxt_service.py ?
Ou chaque app a ses propres utils ?
QUEL EST TON CONSEIL ? Par ma formation, je n'écris pas 2 fois la même fonction. Mais pour du vibe coding je dirais que chaque app a ses propres utils
DONNE MOI TON AVIS, et repose moi la question pour valider

Validation des données :

Django Forms --> NON, ou serializers DRF partout OUI
Validation côté client aussi ou backend only ?
CLIENT AUSSI


Gestion d'erreurs

Logs :

Console uniquement en dev ? OK
Niveau : DEBUG ou INFO ? 
Ou pent-on changer ce paramètre en cours de route ? -> DEBUG


Erreurs utilisateur :

Messages d'erreur techniques ou simplifiés ?
Technique
En français ou anglais ?
Français



Questions "futiles" mais importantes

Langue de l'interface :

Français, anglais, ou mixte ?
Les logs en anglais mais l'UI en français ?
Français uniquement

Timezone :

UTC partout en DB ?
UTC partout en DB
Affichage en heure locale utilisateur ?
Affichage en heure locale **AVEC possibilité de passer un UTC ** Champ à prévoir dans User Account.
Prévoir tous les affichages de toute l'application en fonction de ce champ


Format des dates :

EU : 31/12/2024 NON, ou US : 12/31/2024 NON?
ISO : 2024-12-31 OUI ?


Boutons d'action :

Confirmation pour actions critiques (delete, sell all) ?
CONFIRMATION ACTION CRITIQUE
Ou action directe NON?


Cache frontend :

Utiliser Pinia pour état global ?
LocalStorage pour persister des préférences ?
QUE PENSES-TU DU CACHE REDIS ? Si non redemande encore une fois pour confirmation


Tests :

Écrire des tests ou pas du tout (YOLO mode) ?
Si oui : pytest ou Django tests ?
pytest, mais... uniquement sur validation de l'utilisateur. Pas de superflux !
On test d'abord en mode YOLO et si un bug persiste on fait un test.



Pour Claude Code spécifiquement

Style de code :

Comments en anglais ou français ?
Français
Docstrings détaillées ou minimales ?
Intermédiaire (+ type de retour)


Approche d'implémentation :

Faire marcher d'abord OUI, optimiser après OUI?
Ou code "propre" dès le début NON?


Gestion des TODOs :

OK d'avoir des # TODO temporaires ? OUI
Ou tout doit être fini avant de passer au module suivant ? NON


Ensuite, tes nouvelles questions avec mes réponces dans le texte =======================================================================================================

📌 Clarifications sur vos questions
Groupes Channels WebSocket
Quand plusieurs utilisateurs sont connectés, comment on envoie les messages ?

Option A (que je recommande) : Chaque user a son canal privé user_123. Quand le Trading Engine trouve une stratégie active pour l'user 123, il envoie le message UNIQUEMENT à ce canal.
Option B : On envoie tout à tout le monde et le frontend filtre (moins sécurisé)

→ Je recommande Option A pour la sécurité
COMPRIS JE SUIS OK

Decimal Python
Python a des problèmes avec les float (0.1 + 0.2 = 0.30000000000000004). Pour l'argent, on utilise :
pythonfrom decimal import Decimal
price = Decimal("0.1")  # Au lieu de price = 0.1
→ Je recommande Decimal pour tous les montants/prix
OK

Structure du code - Mon avis
Pour le vibe coding avec Claude Code, je recommande :

Phase 1 : Chaque app a ses utils (plus rapide à développer)
Phase 2 : Quand on voit de la duplication, on refactorise dans core/services/

→ Commencer simple, refactoriser après ?
OK 

Cache Frontend
→ D'accord avec Pinia + LocalStorage ?
OK

🎯 Questions de suivi importantes
1. Mode Dev avec user "dev"
python# Dans settings.py
DEBUG = os.getenv('DEBUG', 'False') == 'True'

Si je comprends bien : en mode DEBUG, pas de page login du tout ? OUI, PAS DE LOGIN
L'user "dev" existe en DB ou c'est virtuel ? EXISTE EN DB, COMME UN USER NORMAL
Cet user "dev" a accès à TOUTES les données de TOUS les users ? OUI

2. Exchanges/Brokers dans User Account
Vous listez : BINANCE, KUKOIN, BITGET

On implémente TOUS ces exchanges dès le Module 1 ?
UTILISATION DE LA LIBRAIRIE CCXT qui gère tous les Exchanges. Tu ne dois géré que cette librairie.
Ou on fait juste Binance d'abord et on ajoute les autres plus tard ? PAR CCXT
Pour tester la connexion : juste un appel à exchange.fetch_balance() ? OUI

3. Timezone utilisateur
Vous voulez un switch UTC/Local dans User Account.

Stocker en DB : user.display_timezone = 'UTC' ou 'Europe/Paris' ? OUI
Afficher TOUTES les dates selon ce choix (trades, logs, etc.) ? OUI

4. Mode Testnet Global
Excellente idée ! Questions :

Un switch global "Mode Testnet" dans la status bar ?
OUI, Modifier la couleur de la staus bar. (couleur inverse de la couleur normale)
Ou par broker (certains en testnet, d'autres en prod) ?
Peut-être que certains broker n'ont pas de testnet, donc désactiver le mode Testnet si c'est le cas
Visual warning quand on est en PROD (bordure rouge) ?
OUI

5. Clé de chiffrement API Keys
"Au plus simple, pas dans .env"

Utiliser SECRET_KEY de Django directement ?
OUI
Ou générer une clé au premier lancement et la stocker en DB ?
NON

6. Modale CRUD Brokers
Pour la modale d'ajout/édition :

Tester la connexion avant de sauvegarder ? OUI
Afficher le balance du compte pour vérifier ? OUI si c'est le plus simple
Masquer l'API Secret après sauvegarde (afficher ••••••) ? NON

7. Status Bar - Détails
Dans la barre de status vous voulez :

"Heartbeat Actif/Inactif" → Juste une pastille verte/rouge ? OUI
"Heartbeat cohérent" → C'est quoi un heartbeat incohérent ?
A développer plus tard, tests dans la régularité des bougies reçues en DB depuis le lancement du serveur
"Stratégie live en cours" → Afficher combien ? La plus rentable ?
NON seulement s'il y en a une ou plusieurs en cours.

8. Workflow premier lancement

L'IA créé user "dac" directement en SQL ? NON, finalement
Ou on fait un script python manage.py init_aristobot ? OUI, et également pour "dev"
Ou une page "first setup" qui s'affiche si aucun user existe ? NON

9. Structure des erreurs
Pour les erreurs techniques en français :
python# Option A
"Erreur de connexion à Binance : Invalid API Key"
# Option B  
"Erreur de connexion à Binance : Clé API invalide"
# Option C
"Impossible de se connecter à l'exchange. Vérifiez vos clés API."
→ Quel style préférez-vous ? Option A
10. Question bonus : Logs des trades

Garder un historique complet de TOUTES les tentatives de trades (même échouées) ? OUI
Ou seulement les trades réussis ? NON

======================================================================================================================
J'ai compris que tu nes savaos pas ce qu'est la librairie CCXT, je t'ai fourni la documentation, elle est en HTML...:

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=windows-1252"/>
	<title></title>
	<meta name="generator" content="LibreOffice 6.0.6.2 (Windows)"/>
	<meta name="created" content="2025-03-13T17:55:25.430000000"/>
	<meta name="changed" content="2025-03-13T17:56:01.765000000"/>
	<style type="text/css">
		h2.cjk { font-family: "SimSun" }
		h2.ctl { font-family: "Lucida Sans" }
		pre.cjk { font-family: "NSimSun", monospace }
		h3.cjk { font-family: "SimSun" }
		h3.ctl { font-family: "Lucida Sans" }
		h4.cjk { font-family: "SimSun" }
		h4.ctl { font-family: "Lucida Sans" }
		code.cjk { font-family: "NSimSun", monospace }
	</style>
</head>
<body lang="fr-CH" dir="ltr">
<h2 class="western"><a name="instantiation"></a><a href="https://docs.ccxt.com/#/README?id=instantiation">Instantiation</a></h2>
<p>To connect to an exchange and start trading you need to
instantiate an exchange class from ccxt library.</p>
<p>To get the full list of ids of supported exchanges
programmatically:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">import ccxt</code>
<code class="western">print (ccxt.exchanges)</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<p>An exchange can be instantiated like shown in the examples below:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">import ccxt</code>
<code class="western">exchange = ccxt.okcoin () # default id</code>
<code class="western">okcoin1 = ccxt.okcoin ({ 'id': 'okcoin1' })</code>
<code class="western">okcoin2 = ccxt.okcoin ({ 'id': 'okcoin2' })</code>
<code class="western">id = 'btcchina'</code>
<code class="western">btcchina = eval ('ccxt.%s ()' % id)</code>
<code class="western">coinbasepro = getattr (ccxt, 'coinbasepro') ()</code>

<code class="western"># from variable id</code>
<code class="western">exchange_id = 'binance'</code>
<code class="western">exchange_class = getattr(ccxt, exchange_id)</code>
<code class="western">exchange = exchange_class({</code>
<code class="western">    </code><code class="western">'apiKey': 'YOUR_API_KEY',</code>
<code class="western">    </code><code class="western">'secret': 'YOUR_SECRET',</code>
<code class="western">})</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<h3 class="western"><a name="features"></a><a href="https://docs.ccxt.com/#/README?id=features">Features</a></h3>
<p>Major exchanges have the&nbsp;<code class="western">.features</code>&nbsp;property
available, where you can see what methods and functionalities are
supported for each market-type (if any method is set
to&nbsp;<code class="western">null/undefined</code>&nbsp;it means
method is &quot;not supported&quot; by the exchange)</p>
<p><em>this feature is currently a work in progress and might be
incomplete, feel free to report any issues you find in it</em></p>
<pre class="western"><code class="western">const exchange = new ccxt.binance()</code>
<code class="western">console.log(exchange.features);</code>

<code class="western">// outputs like:</code>
<code class="western">{</code>
<code class="western">  </code><code class="western">spot: {</code>
<code class="western">    </code><code class="western">sandbox: true, // whether testnet is supported</code>
<code class="western">    </code><code class="western">createOrder: {</code>
<code class="western">      </code><code class="western">triggerPrice: true,          // if trigger order is supported</code>
<code class="western">      </code><code class="western">triggerPriceType: undefined, // if trigger price type is supported (last, mark, index)</code>
<code class="western">      </code><code class="western">triggerDirection: false,     // if trigger direction is supported (up, down)</code>
<code class="western">      </code><code class="western">stopLossPrice: true,         // if stop-loss order is supported (read &quot;Stop Loss Orders&quot; paragraph) </code>
<code class="western">      </code><code class="western">takeProfitPrice: true,       // if take-profit order is supported</code>
<code class="western">      </code><code class="western">attachedStopLossTakeProfit: {       </code>
<code class="western">        </code><code class="western">triggerPriceType: {</code>
<code class="western">            </code><code class="western">last: true,</code>
<code class="western">            </code><code class="western">mark: true,</code>
<code class="western">            </code><code class="western">index: true,</code>
<code class="western">        </code><code class="western">},</code>
<code class="western">        </code><code class="western">price: true,               // whether 'limit' price can be used (instead of market order)</code>
<code class="western">      </code><code class="western">},</code>
<code class="western">      </code><code class="western">marginMode: true,            // if `marginMode` param is supported (cross, isolated)</code>
<code class="western">      </code><code class="western">timeInForce: {               // supported TIF types</code>
<code class="western">        </code><code class="western">GTC: true,</code>
<code class="western">        </code><code class="western">IOC: true,</code>
<code class="western">        </code><code class="western">FOK: true,</code>
<code class="western">        </code><code class="western">PO: true,</code>
<code class="western">        </code><code class="western">GTD: false</code>
<code class="western">      </code><code class="western">},</code>
<code class="western">      </code><code class="western">hedged: false,              // if `hedged` param is supported (true, false)</code>
<code class="western">      </code><code class="western">leverage: false,            // if `leverage` param is supported (true, false)</code>
<code class="western">      </code><code class="western">selfTradePrevention: true,  // if `selfTradePrevention` param is supported (true, false)</code>
<code class="western">      </code><code class="western">trailing: true,             // if trailing order is supported</code>
<code class="western">      </code><code class="western">iceberg: true,              // if iceberg order is supported</code>
<code class="western">      </code><code class="western">marketBuyByCost: true,      // if creating market buy order is possible with `cost` param</code>
<code class="western">      </code><code class="western">marketBuyRequiresPrice: true,// if creating market buy order (if 'cost' not used) requires `price` param to be set</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">createOrders: {</code>
<code class="western">        </code><code class="western">'max': 50,              // if batch order creation is supported</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchMyTrades: {</code>
<code class="western">      </code><code class="western">limit: 1000,              // max limit per call</code>
<code class="western">      </code><code class="western">daysBack: undefined,      // max historical period that can be accessed</code>
<code class="western">      </code><code class="western">untilDays: 1              // if `until` param is supported, then this is permitted distance from `since`</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchOrder: {</code>
<code class="western">      </code><code class="western">marginMode: true,         // when supported, margin order should be fetched with this flag</code>
<code class="western">      </code><code class="western">trigger: false,           // similar as above</code>
<code class="western">      </code><code class="western">trailing: false           // similar as above</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">// other methods have similar properties</code>
<code class="western">    </code><code class="western">fetchOpenOrders: {</code>
<code class="western">      </code><code class="western">limit: undefined,</code>
<code class="western">      </code><code class="western">marginMode: true,</code>
<code class="western">      </code><code class="western">trigger: false,</code>
<code class="western">      </code><code class="western">trailing: false</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchOrders: {</code>
<code class="western">      </code><code class="western">limit: 1000,</code>
<code class="western">      </code><code class="western">daysBack: undefined,</code>
<code class="western">      </code><code class="western">untilDays: 10000,</code>
<code class="western">      </code><code class="western">marginMode: true,</code>
<code class="western">      </code><code class="western">trigger: false,</code>
<code class="western">      </code><code class="western">trailing: false</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchClosedOrders: {</code>
<code class="western">      </code><code class="western">limit: 1000,</code>
<code class="western">      </code><code class="western">daysBackClosed: undefined, // max days-back for closed orders</code>
<code class="western">      </code><code class="western">daysBackCanceled: undefined, // max days-back for canceled orders</code>
<code class="western">      </code><code class="western">untilDays: 10000,</code>
<code class="western">      </code><code class="western">marginMode: true,</code>
<code class="western">      </code><code class="western">trigger: false,</code>
<code class="western">      </code><code class="western">trailing: false</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchOHLCV: {</code>
<code class="western">      </code><code class="western">paginate: true,</code>
<code class="western">      </code><code class="western">limit: 1000</code>
<code class="western">    </code><code class="western">}</code>
<code class="western">  </code><code class="western">},</code>
<code class="western">  </code><code class="western">swap: {</code>
<code class="western">    </code><code class="western">linear: { ... }, // similar to above dict</code>
<code class="western">    </code><code class="western">inverse: { ... }, // similar to above dict</code>
<code class="western">  </code><code class="western">}</code>
<code class="western">  </code><code class="western">future: {</code>
<code class="western">    </code><code class="western">linear: { ... }, // similar to above dict</code>
<code class="western">    </code><code class="western">inverse: { ... }, // similar to above dict</code>
<code class="western">  </code><code class="western">}</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><h3 class="western">
<a name="overriding-exchange-properties-upon-instantiation"></a><a href="https://docs.ccxt.com/#/README?id=overriding-exchange-properties-upon-instantiation">Overriding
Exchange Properties Upon Instantiation</a></h3>
<p>Most of exchange properties as well as specific options can be
overrided upon exchange class instantiation or afterwards, like shown
below:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">exchange = ccxt.binance ({</code>
<code class="western">    </code><code class="western">'rateLimit': 10000,  # unified exchange property</code>
<code class="western">    </code><code class="western">'headers': {</code>
<code class="western">        </code><code class="western">'YOUR_CUSTOM_HTTP_HEADER': 'YOUR_CUSTOM_VALUE',</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'options': {</code>
<code class="western">        </code><code class="western">'adjustForTimeDifference': True,  # exchange-specific option</code>
<code class="western">    </code><code class="western">}</code>
<code class="western">})</code>
<code class="western">exchange.options['adjustForTimeDifference'] = False</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<h3 class="western"><a name="overriding-exchange-methods"></a><a href="https://docs.ccxt.com/#/README?id=overriding-exchange-methods">Overriding
Exchange Methods</a></h3>
<p>In all CCXT-supported languages, you can override instance methods
during runtime:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">ex = ccxt.binance()</code>
<code class="western">def my_overload(symbol, params = {}):</code>
<code class="western">    </code><code class="western"># your codes go here</code>

<code class="western">ex.fetch_ticker = my_overload</code>
<code class="western">print(ex.fetch_ticker('BTC/USDT'))</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<h3 class="western"><a name="testnets-and-sandbox-environments"></a><a href="https://docs.ccxt.com/#/README?id=testnets-and-sandbox-environments">Testnets
And Sandbox Environments</a></h3>
<p>Some exchanges also offer separate APIs for testing purposes that
allows developers to trade virtual money for free and test out their
ideas. Those APIs are called&nbsp;<em>&quot;testnets&quot;,
&quot;sandboxes&quot; or &quot;staging environments&quot;</em>&nbsp;(with
virtual testing assets) as opposed to&nbsp;<em>&quot;mainnets&quot;
and &quot;production environments&quot;</em>&nbsp;(with real assets).
Most often a sandboxed API is a clone of a production API, so, it's
literally the same API, except for the URL to the exchange server.</p>
<p>CCXT unifies that aspect and allows the user to switch to the
exchange's sandbox (if supported by the underlying exchange). To
switch to the sandbox one has to call the&nbsp;<code class="western">exchange.setSandboxMode
(true)</code>&nbsp;or&nbsp;<code class="western">exchange.set_sandbox_mode(true)</code>&nbsp;<strong>immediately
after creating the exchange before any other call</strong>!</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">exchange = ccxt.binance(config)</code>
<code class="western">exchange.set_sandbox_mode(True)  # enable sandbox mode</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm">The&nbsp;<code class="western">exchange.setSandboxMode
	(true) / exchange.set_sandbox_mode (True)</code>&nbsp;has to be your
	first call immediately after creating the exchange (before any other
	calls)</p>
	<li/>
<p style="margin-bottom: 0cm">To obtain the&nbsp;<a href="https://docs.ccxt.com/#/README?id=authentication">API
	keys</a>&nbsp;to the sandbox the user has to register with the
	sandbox website of the exchange in question and create a sandbox
	keypair</p>
	<li/>
<p><strong>Sandbox keys are not interchangeable with
	production keys!</strong></p>
</ul>
<h2 class="western"><a name="exchange-structure"></a><a href="https://docs.ccxt.com/#/README?id=exchange-structure">Exchange
Structure</a></h2>
<p>Every exchange has a set of properties and methods, most of which
you can override by passing an associative array of params to an
exchange constructor. You can also make a subclass and override
everything.</p>
<p>Here's an overview of generic exchange properties with values
added for example:</p>
<pre class="western"><code class="western">{</code>
<code class="western">    </code><code class="western">'id':   'exchange'                   // lowercase string exchange id</code>
<code class="western">    </code><code class="western">'name': 'Exchange'                   // human-readable string</code>
<code class="western">    </code><code class="western">'countries': [ 'US', 'CN', 'EU' ],   // array of ISO country codes</code>
<code class="western">    </code><code class="western">'urls': {</code>
<code class="western">        </code><code class="western">'api': 'https://api.example.com/data',  // string or dictionary of base API URLs</code>
<code class="western">        </code><code class="western">'www': 'https://www.example.com'        // string website URL</code>
<code class="western">        </code><code class="western">'doc': 'https://docs.example.com/api',  // string URL or array of URLs</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'version':         'v1',             // string ending with digits</code>
<code class="western">    </code><code class="western">'api':             { ... },          // dictionary of api endpoints</code>
<code class="western">    </code><code class="western">'has': {                             // exchange capabilities</code>
<code class="western">        </code><code class="western">'CORS': false,</code>
<code class="western">        </code><code class="western">'cancelOrder': true,</code>
<code class="western">        </code><code class="western">'createDepositAddress': false,</code>
<code class="western">        </code><code class="western">'createOrder': true,</code>
<code class="western">        </code><code class="western">'fetchBalance': true,</code>
<code class="western">        </code><code class="western">'fetchCanceledOrders': false,</code>
<code class="western">        </code><code class="western">'fetchClosedOrder': false,</code>
<code class="western">        </code><code class="western">'fetchClosedOrders': false,</code>
<code class="western">        </code><code class="western">'fetchCurrencies': false,</code>
<code class="western">        </code><code class="western">'fetchDepositAddress': false,</code>
<code class="western">        </code><code class="western">'fetchMarkets': true,</code>
<code class="western">        </code><code class="western">'fetchMyTrades': false,</code>
<code class="western">        </code><code class="western">'fetchOHLCV': false,</code>
<code class="western">        </code><code class="western">'fetchOpenOrder': false,</code>
<code class="western">        </code><code class="western">'fetchOpenOrders': false,</code>
<code class="western">        </code><code class="western">'fetchOrder': false,</code>
<code class="western">        </code><code class="western">'fetchOrderBook': true,</code>
<code class="western">        </code><code class="western">'fetchOrders': false,</code>
<code class="western">        </code><code class="western">'fetchStatus': 'emulated',</code>
<code class="western">        </code><code class="western">'fetchTicker': true,</code>
<code class="western">        </code><code class="western">'fetchTickers': false,</code>
<code class="western">        </code><code class="western">'fetchBidsAsks': false,</code>
<code class="western">        </code><code class="western">'fetchTrades': true,</code>
<code class="western">        </code><code class="western">'withdraw': false,</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'timeframes': {                      // empty if the exchange.has['fetchOHLCV'] !== true</code>
<code class="western">        </code><code class="western">'1m': '1minute',</code>
<code class="western">        </code><code class="western">'1h': '1hour',</code>
<code class="western">        </code><code class="western">'1d': '1day',</code>
<code class="western">        </code><code class="western">'1M': '1month',</code>
<code class="western">        </code><code class="western">'1y': '1year',</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'timeout':           10000,          // number in milliseconds</code>
<code class="western">    </code><code class="western">'rateLimit':         2000,           // number in milliseconds</code>
<code class="western">    </code><code class="western">'userAgent':        'ccxt/1.1.1 ...' // string, HTTP User-Agent header</code>
<code class="western">    </code><code class="western">'verbose':           false,          // boolean, output error details</code>
<code class="western">    </code><code class="western">'markets':          { ... }          // dictionary of markets/pairs by symbol</code>
<code class="western">    </code><code class="western">'symbols':          [ ... ]          // sorted list of string symbols (traded pairs)</code>
<code class="western">    </code><code class="western">'currencies':       { ... }          // dictionary of currencies by currency code</code>
<code class="western">    </code><code class="western">'markets_by_id':    { ... },         // dictionary of array of dictionaries (markets) by id</code>
<code class="western">    </code><code class="western">'currencies_by_id': { ... },         // dictionary of dictionaries (markets) by id</code>
<code class="western">    </code><code class="western">'apiKey':   '92560ffae9b8a0421...',  // string public apiKey (ASCII, hex, Base64, ...)</code>
<code class="western">    </code><code class="western">'secret':   '9aHjPmW+EtRRKN/Oi...'   // string private secret key</code>
<code class="western">    </code><code class="western">'password': '6kszf4aci8r',           // string password</code>
<code class="western">    </code><code class="western">'uid':      '123456',                // string user id</code>
<code class="western">    </code><code class="western">'options':          { ... },         // exchange-specific options</code>
<code class="western">    </code><code class="western">// ... other properties here ...</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><h3 class="western">
<a name="exchange-properties"></a><a href="https://docs.ccxt.com/#/README?id=exchange-properties">Exchange
Properties</a></h3>
<p>Below is a detailed description of each of the base exchange
properties:</p>
<ul>
	<li/>
<p><code class="western">id</code>: Each exchange has a
	default id. The id is not used for anything, it's a string literal
	for user-land exchange instance identification purposes. You can
	have multiple links to the same exchange and differentiate them by
	ids. Default ids are all lowercase and correspond to exchange names.</p>
	<li/>
<p><code class="western">name</code>: This is a string literal
	containing the human-readable exchange name.</p>
	<li/>
<p><code class="western">countries</code>: An array of string
	literals of 2-symbol ISO country codes, where the exchange is
	operating from.</p>
	<li/>
<p><code class="western">urls['api']</code>: The single string
	literal base URL for API calls or an associative array of separate
	URLs for private and public APIs.</p>
	<li/>
<p><code class="western">urls['www']</code>: The main HTTP
	website URL.</p>
	<li/>
<p><code class="western">urls['doc']</code>: A single string
	URL link to original documentation for exchange API on their website
	or an array of links to docs.</p>
	<li/>
<p><code class="western">version</code>: A string literal
	containing version identifier for current exchange API. The ccxt
	library will append this version string to the API Base URL upon
	each request. You don't have to modify it, unless you are
	implementing a new exchange API. The version identifier is a usually
	a numeric string starting with a letter 'v' in some cases, like
	v1.1. Do not override it unless you are implementing your own new
	crypto exchange class.</p>
	<li/>
<p><code class="western">api</code>: An associative array
	containing a definition of all API endpoints exposed by a crypto
	exchange. The API definition is used by ccxt to automatically
	construct callable instance methods for each available endpoint.</p>
	<li/>
<p><code class="western">has</code>: This is an associative
	array of exchange capabilities
	(e.g&nbsp;<code class="western">fetchTickers</code>,&nbsp;<code class="western">fetchOHLCV</code>&nbsp;or&nbsp;<code class="western">CORS</code>).</p>
	<li/>
<p><code class="western">timeframes</code>: An associative
	array of timeframes, supported by the fetchOHLCV method of the
	exchange. This is only populated when&nbsp;<code class="western">has['fetchOHLCV']</code>&nbsp;property
	is true.</p>
	<li/>
<p><code class="western">timeout</code>: A timeout in
	milliseconds for a request-response roundtrip (default timeout is
	10000 ms = 10 seconds). If the response is not received in that
	time, the library will throw an&nbsp;<code class="western">RequestTimeout</code>&nbsp;exception.
	You can leave the default timeout value or set it to a reasonable
	value. Hanging forever with no timeout is not your option, for sure.
	You don't have to override this option in general case.</p>
	<li/>
<p><code class="western">rateLimit</code>: A request rate
	limit in milliseconds. Specifies the required minimal delay between
	two consequent HTTP requests to the same exchange. The built-in
	rate-limiter is enabled by default and can be turned off by setting
	the&nbsp;<code class="western">enableRateLimit</code>&nbsp;property
	to false.</p>
	<li/>
<p><code class="western">enableRateLimit</code>: A boolean
	(true/false) value that enables the built-in rate limiter and
	throttles consecutive requests. This setting is&nbsp;<code class="western">true</code>&nbsp;(enabled)
	by default.&nbsp;<strong>The user is required to implement own&nbsp;<a href="https://docs.ccxt.com/#/README?id=rate-limit">rate
	limiting</a>&nbsp;or leave the built-in rate limiter enabled to
	avoid being banned from the exchange</strong>.</p>
	<li/>
<p><code class="western">userAgent</code>: An object to set
	HTTP User-Agent header to. The ccxt library will set its User-Agent
	by default. Some exchanges may not like it. If you are having
	difficulties getting a reply from an exchange and want to turn
	User-Agent off or use the default one, set this value to false,
	undefined, or an empty string. The value of&nbsp;<code class="western">userAgent</code>&nbsp;may
	be overrided by HTTP&nbsp;<code class="western">headers</code>&nbsp;property
	below.</p>
	<li/>
<p><code class="western">headers</code>: An associative array
	of HTTP headers and their values. Default value is empty&nbsp;<code class="western">{}</code>.
	All headers will be prepended to all requests. If
	the&nbsp;<code class="western">User-Agent</code>&nbsp;header is set
	within&nbsp;<code class="western">headers</code>, it will override
	whatever value is set in the&nbsp;<code class="western">userAgent</code>&nbsp;property
	above.</p>
	<li/>
<p><code class="western">verbose</code>: A boolean flag
	indicating whether to log HTTP requests to stdout (verbose flag is
	false by default). Python people have an alternative way of DEBUG
	logging with a standard pythonic logger, which is enabled by adding
	these two lines to the beginning of their code:</p>
	<pre class="western"><code class="western">import logging</code>
<code class="western">logging.basicConfig(level=logging.DEBUG)</code>Copy to clipboardErrorCopied</pre>
	<li/>
<p><code class="western">markets</code>: An associative array
	of markets indexed by common trading pairs or symbols. Markets
	should be loaded prior to accessing this property. Markets are
	unavailable until you call the&nbsp;<code class="western">loadMarkets()
	/ load_markets()</code>&nbsp;method on exchange instance.</p>
	<li/>
<p><code class="western">symbols</code>: A non-associative
	array (a list) of symbols available with an exchange, sorted in
	alphabetical order. These are the keys of the&nbsp;<code class="western">markets</code>&nbsp;property.
	Symbols are loaded and reloaded from markets. This property is a
	convenient shorthand for all market keys.</p>
	<li/>
<p><code class="western">currencies</code>: An associative
	array (a dict) of currencies by codes (usually 3 or 4 letters)
	available with an exchange. Currencies are loaded and reloaded from
	markets.</p>
	<li/>
<p><code class="western">markets_by_id</code>: An associative
	array of arrays of markets indexed by exchange-specific ids.
	Typically a length one array unless there are multiple markets with
	the same marketId. Markets should be loaded prior to accessing this
	property.</p>
	<li/>
<p><code class="western">apiKey</code>: This is your public
	API key string literal. Most exchanges require&nbsp;<a href="https://docs.ccxt.com/#/README?id=api-keys-setup">API
	keys setup</a>.</p>
	<li/>
<p><code class="western">secret</code>: Your private secret
	API key string literal. Most exchanges require this as well together
	with the apiKey.</p>
	<li/>
<p><code class="western">password</code>: A string literal
	with your password/phrase. Some exchanges require this parameter for
	trading, but most of them don't.</p>
	<li/>
<p><code class="western">uid</code>: A unique id of your
	account. This can be a string literal or a number. Some exchanges
	also require this for trading, but most of them don't.</p>
	<li/>
<p><code class="western">requiredCredentials</code>: A unified
	associative dictionary that shows which of the above API credentials
	are required for sending private API calls to the underlying
	exchange (an exchange may require a specific set of keys).</p>
	<li/>
<p><code class="western">options</code>: An exchange-specific
	associative dictionary containing special keys and options that are
	accepted by the underlying exchange and supported in CCXT.</p>
	<li/>
<p><code class="western">precisionMode</code>: The exchange
	decimal precision counting mode, read more about&nbsp;<a href="https://docs.ccxt.com/#/README?id=precision-and-limits">Precision
	And Limits</a></p>
	<li/>
<p>For proxies
	-&nbsp;<code class="western">proxyUrl</code>,&nbsp;<code class="western">httpUrl</code>,&nbsp;<code class="western">httpsUrl</code>,&nbsp;<code class="western">socksProxy</code>,&nbsp;<code class="western">wsProxy</code>,&nbsp;<code class="western">wssProxy</code>,&nbsp;<code class="western">wsSocksProxy</code>&nbsp;:
	An url of specific proxy. Read details in&nbsp;<a href="https://docs.ccxt.com/#/README?id=proxy">Proxy</a>&nbsp;section.</p>
</ul>
<p>See this section on&nbsp;<a href="https://docs.ccxt.com/#/README?id=overriding-exchange-properties-upon-instantiation">Overriding
exchange properties</a>.</p>
<h4 class="western"><a name="exchange-metadata"></a><a href="https://docs.ccxt.com/#/README?id=exchange-metadata">Exchange
Metadata</a></h4>
<ul>
	<li/>
<p><code class="western">has</code>: An assoc-array containing
	flags for exchange capabilities, including the following:</p>
	<pre class="western"><code class="western">'has': {</code>

<code class="western">    </code><code class="western">'CORS': false,  // has Cross-Origin Resource Sharing enabled (works from browser) or not</code>

<code class="western">    </code><code class="western">// unified methods availability flags (can be true, false, or 'emulated'):</code>

<code class="western">    </code><code class="western">'cancelOrder': true,</code>
<code class="western">    </code><code class="western">'createDepositAddress': false,</code>
<code class="western">    </code><code class="western">'createOrder': true,</code>
<code class="western">    </code><code class="western">'fetchBalance': true,</code>
<code class="western">    </code><code class="western">'fetchCanceledOrders': false,</code>
<code class="western">    </code><code class="western">'fetchClosedOrder': false,</code>
<code class="western">    </code><code class="western">'fetchClosedOrders': false,</code>
<code class="western">    </code><code class="western">'fetchCurrencies': false,</code>
<code class="western">    </code><code class="western">'fetchDepositAddress': false,</code>
<code class="western">    </code><code class="western">'fetchMarkets': true,</code>
<code class="western">    </code><code class="western">'fetchMyTrades': false,</code>
<code class="western">    </code><code class="western">'fetchOHLCV': false,</code>
<code class="western">    </code><code class="western">'fetchOpenOrder': false,</code>
<code class="western">    </code><code class="western">'fetchOpenOrders': false,</code>
<code class="western">    </code><code class="western">'fetchOrder': false,</code>
<code class="western">    </code><code class="western">'fetchOrderBook': true,</code>
<code class="western">    </code><code class="western">'fetchOrders': false,</code>
<code class="western">    </code><code class="western">'fetchStatus': 'emulated',</code>
<code class="western">    </code><code class="western">'fetchTicker': true,</code>
<code class="western">    </code><code class="western">'fetchTickers': false,</code>
<code class="western">    </code><code class="western">'fetchBidsAsks': false,</code>
<code class="western">    </code><code class="western">'fetchTrades': true,</code>
<code class="western">    </code><code class="western">'withdraw': false,</code>
<code class="western">    </code><code class="western">...</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
	The meaning of each flag showing availability of this or that method
	is:</p>
	<ul>
		<li/>
<p>a value of&nbsp;<code class="western">undefined</code>&nbsp;/&nbsp;<code class="western">None</code>&nbsp;/&nbsp;<code class="western">null</code>&nbsp;means
		the method is not currently implemented in ccxt (either ccxt has
		not unified it yet or the method isn't natively available from the
		exchange API)</p>
		<li/>
<p>boolean&nbsp;<code class="western">false</code>&nbsp;specifically
		means that the endpoint isn't natively available from the exchange
		API</p>
		<li/>
<p>boolean&nbsp;<code class="western">true</code>&nbsp;means
		the endpoint is natively available from the exchange API and
		unified in the ccxt library</p>
		<li/>
<p><code class="western">'emulated'</code>&nbsp;string means
		the endpoint isn't natively available from the exchange API but
		reconstructed (as much as possible) by the ccxt library from other
		available true-methods</p>
		<p>For a complete list of all exchages and their supported methods,
		please, refer to this
		example:&nbsp;<a href="https://github.com/ccxt/ccxt/blob/master/examples/js/exchange-capabilities.js" target="_blank">https://github.com/ccxt/ccxt/blob/master/examples/js/exchange-capabilities.js</a></p>
	</ul>
</ul>
<h2 class="western"><a name="rate-limit"></a><a href="https://docs.ccxt.com/#/README?id=rate-limit">Rate
Limit</a></h2>
<p>Exchanges usually impose what is called a&nbsp;<em>rate limit</em>.
Exchanges will remember and track your user credentials and your IP
address and will not allow you to query the API too frequently. They
balance their load and control traffic congestion to protect API
servers from (D)DoS and misuse.</p>
<p><strong>WARNING: Stay under the rate limit to avoid ban!</strong></p>
<p>Most exchanges allow&nbsp;<strong>up to 1 or 2 requests per
second</strong>. Exchanges may temporarily restrict your access to
their API or ban you for some period of time if you are too
aggressive with your requests.</p>
<p><strong>The&nbsp;</strong><strong><code class="western">exchange.rateLimit</code></strong><strong>&nbsp;property
is set to a safe default which is sub-optimal. Some exchanges may
have varying rate limits for different endpoints. It is up to the
user to tweak&nbsp;</strong><strong><code class="western">rateLimit</code></strong><strong>&nbsp;according
to application-specific purposes.</strong></p>
<p>The CCXT library has a built-in experimental rate-limiter that
will do the necessary throttling in background transparently to the
user.&nbsp;<strong>WARNING: users are responsible for at least some
type of rate-limiting: either by implementing a custom algorithm or
by doing it with the built-in rate-limiter.</strong>.</p>
<p>You can turn on/off the built-in rate-limiter
with&nbsp;<code class="western">.enableRateLimit</code>&nbsp;property,
like so:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western">
<code class="western"># enable built-in rate limiting upon instantiation of the exchange</code>
<code class="western">exchange = ccxt.bitfinex({</code>
<code class="western">    </code><code class="western"># 'enableRateLimit': True,  # enabled by default</code>
<code class="western">})</code>

<code class="western"># or switch the built-in rate-limiter on or off later after instantiation</code>
<code class="western">exchange.enableRateLimit = True  # enable</code>
<code class="western">exchange.enableRateLimit = False  # disable</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<p>In case your calls hit a rate limit or get nonce errors, the ccxt
library will throw an&nbsp;<code class="western">InvalidNonce</code>&nbsp;exception,
or, in some cases, one of the following types:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">DDoSProtection</code></p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">ExchangeNotAvailable</code></p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">ExchangeError</code></p>
	<li/>
<p><code class="western">InvalidNonce</code></p>
</ul>
<p>A later retry is usually enough to handle that.</p>
<h3 class="western"><a name="notes-on-rate-limiter"></a><a href="https://docs.ccxt.com/#/README?id=notes-on-rate-limiter">Notes
On Rate Limiter</a></h3>
<h4 class="western"><a name="one-rate-limiter-per-each-exchange-instance"></a>
<a href="https://docs.ccxt.com/#/README?id=one-rate-limiter-per-each-exchange-instance">One
Rate Limiter Per Each Exchange Instance</a></h4>
<p>The rate limiter is a property of the exchange instance, in other
words, each exchange instance has its own rate limiter that is not
aware of the other instances. In many cases the user should reuse the
same exchange instance throughout the program. Do not use multiple
instances of the same exchange with the same API keypair from the
same IP address.</p>
<pre class="western"><code class="western">// DO NOT DO THIS!</code>

<code class="western">const binance1 = new ccxt.binance ()</code>
<code class="western">const binance2 = new ccxt.binance ()</code>
<code class="western">const binance3 = new ccxt.binance ()</code>

<code class="western">while (true) {</code>
<code class="western">    </code><code class="western">const result = await Promise.all ([</code>
<code class="western">        </code><code class="western">binance1.fetchOrderBook ('BTC/USDT'),</code>
<code class="western">        </code><code class="western">binance2.fetchOrderBook ('ETH/USDT'),</code>
<code class="western">        </code><code class="western">binance3.fetchOrderBook ('ETH/BTC'),</code>
<code class="western">    </code><code class="western">])</code>
<code class="western">    </code><code class="western">console.log (result)</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Reuse the exchange instance as much as possible as shown below:</p>
<pre class="western"><code class="western">// DO THIS INSTEAD:</code>

<code class="western">const binance = new ccxt.binance ()</code>

<code class="western">while (true) {</code>
<code class="western">    </code><code class="western">const result = await Promise.all ([</code>
<code class="western">        </code><code class="western">binance.fetchOrderBook ('BTC/USDT'),</code>
<code class="western">        </code><code class="western">binance.fetchOrderBook ('ETH/USDT'),</code>
<code class="western">        </code><code class="western">binance.fetchOrderBook ('ETH/BTC'),</code>
<code class="western">    </code><code class="western">])</code>
<code class="western">    </code><code class="western">console.log (result)</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Since the rate limiter belongs to the exchange instance, destroying
the exchange instance will destroy the rate limiter as well. Among
the most common pitfalls with the rate limiting is creating and
dropping the exchange instance over and over again. If in your
program you are creating and destroying the exchange instance (say,
inside a function that is called multiple times), then you are
effectively resetting the rate limiter over and over and that will
eventually break the rate limits. If you are recreating the exchange
instance every time instead of reusing it, CCXT will try to load the
markets every time. Therefore, you will force-load the markets over
and over as explained in the&nbsp;<a href="https://docs.ccxt.com/#/README?id=loading-markets">Loading
Markets</a>&nbsp;section. Abusing the markets endpoint will
eventually break the rate limiter as well.</p>
<pre class="western"><code class="western">// DO NOT DO THIS!</code>

<code class="western">async function tick () {</code>
<code class="western">    </code><code class="western">const exchange = new ccxt.binance ()</code>
<code class="western">    </code><code class="western">const response = await exchange.fetchOrderBook ('BTC/USDT')</code>
<code class="western">    </code><code class="western">// ... some processing here ...</code>
<code class="western">    </code><code class="western">return response</code>
<code class="western">}</code>

<code class="western">while (true) {</code>
<code class="western">    </code><code class="western">const result = await tick ()</code>
<code class="western">    </code><code class="western">console.log (result)</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Do not break this rule unless you really understand the inner
workings of the rate-limiter and you are 100% sure you know what
you're doing. In order to stay safe always reuse the exchange
instance throughout your functions and methods callchain like shown
below:</p>
<pre class="western"><code class="western">// DO THIS INSTEAD:</code>

<code class="western">async function tick (exchange) {</code>
<code class="western">    </code><code class="western">const response = await exchange.fetchOrderBook ('BTC/USDT')</code>
<code class="western">    </code><code class="western">// ... some processing here ...</code>
<code class="western">    </code><code class="western">return response</code>
<code class="western">}</code>

<code class="western">const exchange = new ccxt.binance ()</code>
<code class="western">while (true) {</code>
<code class="western">    </code><code class="western">const result = await tick (exchange)</code>
<code class="western">    </code><code class="western">console.log (result)</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><h3 class="western">
<a name="ddos-protection-by-cloudflare-incapsula"></a><a href="https://docs.ccxt.com/#/README?id=ddos-protection-by-cloudflare-incapsula">DDoS
Protection By Cloudflare / Incapsula</a></h3>
<p>Some exchanges are&nbsp;<a href="https://en.wikipedia.org/wiki/Denial-of-service_attack" target="_blank">DDoS</a>-protected
by&nbsp;<a href="https://www.cloudflare.com/" target="_blank">Cloudflare</a>&nbsp;or&nbsp;<a href="https://www.incapsula.com/" target="_blank">Incapsula</a>.
Your IP can get temporarily blocked during periods of high load.
Sometimes they even restrict whole countries and regions. In that
case their servers usually return a page that states a HTTP 40x error
or runs an AJAX test of your browser / captcha test and delays the
reload of the page for several seconds. Then your browser/fingerprint
is granted access temporarily and gets added to a whitelist or
receives a HTTP cookie for further use.</p>
<p>The most common symptoms for a DDoS protection problem,
rate-limiting problem or for a location-based filtering issue:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm">Getting&nbsp;<code class="western">RequestTimeout</code>&nbsp;exceptions
	with all types of exchange methods</p>
	<li/>
<p style="margin-bottom: 0cm">Catching&nbsp;<code class="western">ExchangeError</code>&nbsp;or&nbsp;<code class="western">ExchangeNotAvailable</code>&nbsp;with
	HTTP error codes 400, 403, 404, 429, 500, 501, 503, etc..</p>
	<li/>
<p style="margin-bottom: 0cm">Having DNS resolving issues, SSL
	certificate issues and low-level connectivity issues</p>
	<li/>
<p>Getting a template HTML page instead of JSON from the
	exchange</p>
</ul>
<p>If you encounter DDoS protection errors and cannot reach a
particular exchange then:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm">use a&nbsp;<a href="https://docs.ccxt.com/#/README?id=proxy">proxy</a>&nbsp;(this
	is less responsive, though)</p>
	<li/>
<p style="margin-bottom: 0cm">ask the exchange support to add
	you to a whitelist</p>
	<li/>
<p style="margin-bottom: 0cm">try an alternative IP within a
	different geographic region</p>
	<li/>
<p style="margin-bottom: 0cm">run your software in a
	distributed network of servers</p>
	<li/>
<p style="margin-bottom: 0cm">run your software in close
	proximity to the exchange (same country, same city, same datacenter,
	same server rack, same server)</p>
	<li/>
<p>...</p>
</ul>
<p><br/>
<br/>

</p>
</body>
</html>
-----------------
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=windows-1252"/>
	<title></title>
	<meta name="generator" content="LibreOffice 6.0.6.2 (Windows)"/>
	<meta name="created" content="2025-03-13T17:02:46.921000000"/>
	<meta name="changed" content="2025-03-13T18:04:14.334000000"/>
	<style type="text/css">
		@page { margin: 2cm }
		p { margin-bottom: 0.25cm; line-height: 115% }
		h1 { margin-bottom: 0.21cm }
		h1.western { font-family: "Liberation Serif", serif }
		h1.cjk { font-family: "SimSun"; font-size: 24pt }
		h1.ctl { font-family: "Lucida Sans"; font-size: 24pt }
		pre.cjk { font-family: "NSimSun", monospace }
		h2.cjk { font-family: "SimSun" }
		h2.ctl { font-family: "Lucida Sans" }
		td p { margin-bottom: 0cm }
		th p { margin-bottom: 0cm }
		h3.cjk { font-family: "SimSun" }
		h3.ctl { font-family: "Lucida Sans" }
		h4.cjk { font-family: "SimSun" }
		h4.ctl { font-family: "Lucida Sans" }
		a:link { so-language: zxx }
		code.cjk { font-family: "NSimSun", monospace }
	</style>
</head>
<body lang="fr-CH" dir="ltr">
<p style="margin-bottom: 0cm; line-height: 100%"><font size="4" style="font-size: 16pt"><b>CCXT
Documentation&nbsp;:</b></font></p>
<h1 class="western"><a name="overview"></a><a href="https://docs.ccxt.com/#/README?id=overview">Overview</a></h1>
<p>The ccxt library is a collection of available crypto&nbsp;<em>exchanges</em>&nbsp;or
exchange classes. Each class implements the public and private API
for a particular crypto exchange. All exchanges are derived from the
base Exchange class and share a set of common methods. To access a
particular exchange from ccxt library you need to create an instance
of corresponding exchange class. Supported exchanges are updated
frequently and new exchanges are added regularly.</p>
<p>The structure of the library can be outlined as follows:</p>
<pre class="western"><code class="western">                                 </code><code class="western">User</code>
<code class="western">    </code><code class="western">+-------------------------------------------------------------+</code>
<code class="western">    </code><code class="western">|                            CCXT                             |</code>
<code class="western">    </code><code class="western">+------------------------------+------------------------------+</code>
<code class="western">    </code><code class="western">|            Public            |           Private            |</code>
<code class="western">    </code><code class="western">+=============================================================+</code>
<code class="western">    &#9474;                              </code><code class="western">.                              |</code>
<code class="western">    &#9474;                    </code><code class="western">The Unified CCXT API                     |</code>
<code class="western">    &#9474;                              </code><code class="western">.                              |</code>
<code class="western">    </code><code class="western">|       loadMarkets            .           fetchBalance       |</code>
<code class="western">    </code><code class="western">|       fetchMarkets           .            createOrder       |</code>
<code class="western">    </code><code class="western">|       fetchCurrencies        .            cancelOrder       |</code>
<code class="western">    </code><code class="western">|       fetchTicker            .             fetchOrder       |</code>
<code class="western">    </code><code class="western">|       fetchTickers           .            fetchOrders       |</code>
<code class="western">    </code><code class="western">|       fetchOrderBook         .        fetchOpenOrders       |</code>
<code class="western">    </code><code class="western">|       fetchOHLCV             .      fetchClosedOrders       |</code>
<code class="western">    </code><code class="western">|       fetchStatus            .          fetchMyTrades       |</code>
<code class="western">    </code><code class="western">|       fetchTrades            .                deposit       |</code>
<code class="western">    </code><code class="western">|                              .               withdraw       |</code>
<code class="western">    &#9474;                              </code><code class="western">.                              |</code>
<code class="western">    </code><code class="western">+=============================================================+</code>
<code class="western">    &#9474;                              </code><code class="western">.                              |</code>
<code class="western">    </code><code class="western">|                     Custom Exchange API                     |</code>
<code class="western">    </code><code class="western">|         (Derived Classes And Their Implicit Methods)        |</code>
<code class="western">    &#9474;                              </code><code class="western">.                              |</code>
<code class="western">    </code><code class="western">|       publicGet...           .          privateGet...       |</code>
<code class="western">    </code><code class="western">|       publicPost...          .         privatePost...       |</code>
<code class="western">    </code><code class="western">|                              .          privatePut...       |</code>
<code class="western">    </code><code class="western">|                              .       privateDelete...       |</code>
<code class="western">    </code><code class="western">|                              .                   sign       |</code>
<code class="western">    &#9474;                              </code><code class="western">.                              |</code>
<code class="western">    </code><code class="western">+=============================================================+</code>
<code class="western">    &#9474;                              </code><code class="western">.                              |</code>
<code class="western">    </code><code class="western">|                      Base Exchange Class                    |</code>
<code class="western">    &#9474;                              </code><code class="western">.                              |</code>
<code class="western">    </code><code class="western">+=============================================================+</code>Copy to clipboardErrorCopied</pre><p>
Full public and private HTTP REST APIs for all exchanges are
implemented. WebSocket implementations in JavaScript, PHP, Python are
available in&nbsp;<a href="https://ccxt.pro/" target="_blank">CCXT
Pro</a>, which is a professional addon to CCXT with support for
WebSocket streams.</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><strong><a href="https://docs.ccxt.com/#/README?id=exchanges">Exchanges</a></strong></p>
	<li/>
<p style="margin-bottom: 0cm"><strong><a href="https://docs.ccxt.com/#/README?id=markets">Markets</a></strong></p>
	<li/>
<p style="margin-bottom: 0cm"><strong><a href="https://docs.ccxt.com/#/README?id=implicit-api">Implicit
	API</a></strong></p>
	<li/>
<p style="margin-bottom: 0cm"><strong><a href="https://docs.ccxt.com/#/README?id=unified-api">Unified
	API</a></strong></p>
	<li/>
<p style="margin-bottom: 0cm"><strong><a href="https://docs.ccxt.com/#/README?id=public-api">Public
	API</a></strong></p>
	<li/>
<p style="margin-bottom: 0cm"><strong><a href="https://docs.ccxt.com/#/README?id=private-api">Private
	API</a></strong></p>
	<li/>
<p style="margin-bottom: 0cm"><strong><a href="https://docs.ccxt.com/#/README?id=error-handling">Error
	Handling</a></strong></p>
	<li/>
<p style="margin-bottom: 0cm"><strong><a href="https://docs.ccxt.com/#/README?id=troubleshooting">Troubleshooting</a></strong></p>
	<li/>
<p><strong><a href="https://docs.ccxt.com/#/README?id=ccxt-pro">CCXT
	Pro</a></strong></p>
</ul>
<h2 class="western"><br/>
<br/>

</h2>
<h1 class="western"><a name="exchanges"></a><a href="https://docs.ccxt.com/#/README?id=exchanges">Exchanges</a></h1>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=instantiation">Instantiation</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=exchange-structure">Exchange
	Structure</a></p>
	<li/>
<p><a href="https://docs.ccxt.com/#/README?id=rate-limit">Rate
	Limit</a></p>
</ul>
<p>The CCXT library currently supports the following 106
cryptocurrency exchange markets and trading APIs:</p>
<table width="643" cellpadding="2" cellspacing="0">
	<col width="233">
	<col width="129">
	<col width="44">
	<col width="36">
	<col width="101">
	<col width="76">
	<thead>
		<tr>
			<th width="233" style="border: none; padding: 0cm">
				<p>id</p>
			</th>
			<th width="129" style="border: none; padding: 0cm">
				<p>name</p>
			</th>
			<th width="44" style="border: none; padding: 0cm">
				<p align="center">ver</p>
			</th>
			<th width="36" style="border: none; padding: 0cm">
				<p>type</p>
			</th>
			<th width="101" style="border: none; padding: 0cm">
				<p>certified</p>
			</th>
			<th width="76" style="border: none; padding: 0cm">
				<p>pro</p>
			</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>ace</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://ace.io/" target="_blank">ACE</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/ace-exchange/ace-offical-api-docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image9" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image10" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>alpaca</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://alpaca.markets/" target="_blank">Alpaca</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://alpaca.markets/docs/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image12" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image13" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image14" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>ascendex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://ascendex.com/en-us/register?inviteCode=EL6BXBQM" target="_blank">AscendEX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://ascendex.github.io/ascendex-pro-api/#ascendex-pro-api-documentation" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image16" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image17" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image18" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bequant</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bequant.io/referral/dd104e3bee7634ec" target="_blank">Bequant</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api.bequant.io/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image20" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image21" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image22" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bigone</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://b1.run/users/new?code=D3LLBVFT" target="_blank">BigONE</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://open.big.one/docs/api.html" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image24" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image25" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>binance</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://accounts.binance.com/en/register?ref=D7YA7CLY" target="_blank">Binance</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://developers.binance.com/en" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image27" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image28" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image29" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image30" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>binancecoinm</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://accounts.binance.com/en/register?ref=D7YA7CLY" target="_blank">Binance
				COIN-M</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://binance-docs.github.io/apidocs/delivery/en/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image32" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image33" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image34" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image35" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>binanceus</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.binance.us/?ref=35005074" target="_blank">Binance
				US</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/binance-us/binance-official-api-docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image37" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image38" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image39" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>binanceusdm</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://accounts.binance.com/en/register?ref=D7YA7CLY" target="_blank">Binance
				USD&#9416;-M</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://binance-docs.github.io/apidocs/futures/en/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image41" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image42" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image43" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image44" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bingx</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bingx.com/invite/OHETOM" target="_blank">BingX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://bingx-api.github.io/docs/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image46" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image47" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image48" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image49" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bit2c</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bit2c.co.il/Aff/63bfed10-e359-420c-ab5a-ad368dab0baf" target="_blank">Bit2C</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.bit2c.co.il/home/api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image51" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image52" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitbank</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bitbank.cc/" target="_blank">bitbank</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.bitbank.cc/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image54" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image55" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitbns</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://ref.bitbns.com/1090961" target="_blank">Bitbns</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://bitbns.com/trade/#/api-trading/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image57" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image58" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitfinex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bitfinex.com/" target="_blank">Bitfinex</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.bitfinex.com/v2/docs/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image60" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image61" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image62" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitfinex1</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bitfinex.com/?refcode=P61eYxFL" target="_blank">Bitfinex</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.bitfinex.com/v1/docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image64" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image65" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image66" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitflyer</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bitflyer.com/" target="_blank">bitFlyer</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://lightning.bitflyer.com/docs?lang=en" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image68" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image69" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitget</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bitget.com/expressly?languageType=0&amp;channelCode=ccxt&amp;vipCode=tg9j" target="_blank">Bitget</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.bitget.com/api-doc/common/intro" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image71" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image72" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image73" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image74" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bithumb</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bithumb.com/" target="_blank">Bithumb</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://apidocs.bithumb.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image76" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image77" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image78" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitmart</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="http://www.bitmart.com/?r=rQCFLh" target="_blank">BitMart</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://developer-pro.bitmart.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image80" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image81" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image82" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image83" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitmex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bitmex.com/app/register/NZTR1q" target="_blank">BitMEX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.bitmex.com/app/apiOverview" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image85" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image86" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image87" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image88" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitopro</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bitopro.com/" target="_blank">BitoPro</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/bitoex/bitopro-offical-api-docs/blob/master/v3-1/rest-1/rest.md" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image90" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image91" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image92" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitrue</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bitrue.com/affiliate/landing?cn=600000&amp;inviteCode=EZWETQE" target="_blank">Bitrue</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/Bitrue-exchange/bitrue-official-api-docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image94" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image95" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image96" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitso</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bitso.com/?ref=itej" target="_blank">Bitso</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://bitso.com/api_info" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image98" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image99" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitstamp</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bitstamp.net/" target="_blank">Bitstamp</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.bitstamp.net/api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image101" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image102" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image103" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitteam</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bit.team/auth/sign-up?ref=bitboy2023" target="_blank">BIT.TEAM</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://bit.team/trade/api/documentation" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_6b682c5cc9644c5e.gif" name="Image105" alt="API Version 2.0.6" align="bottom" width="40" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image106" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bitvavo</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bitvavo.com/?a=24F34952F7" target="_blank">Bitvavo</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.bitvavo.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image108" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image109" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image110" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bl3p</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://bl3p.eu/" target="_blank">BL3P</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/BitonicNL/bl3p-api/tree/master/docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image112" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image113" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>blockchaincom</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://blockchain.com/" target="_blank">Blockchain.com</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api.blockchain.com/v3" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image115" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image116" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image117" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>blofin</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://blofin.com/register?referral_code=f79EsS" target="_blank">BloFin</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://blofin.com/docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image119" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image120" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image121" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>btcalpha</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://btc-alpha.com/?r=123788" target="_blank">BTC-Alpha</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://btc-alpha.github.io/api-docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image123" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image124" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>btcbox</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.btcbox.co.jp/" target="_blank">BtcBox</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://blog.btcbox.jp/en/archives/8762" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image126" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image127" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>btcmarkets</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://btcmarkets.net/" target="_blank">BTC Markets</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api.btcmarkets.net/doc/v3" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image129" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image130" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>btcturk</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.btcturk.com/" target="_blank">BTCTurk</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/BTCTrader/broker-api-docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image132" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image133" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>bybit</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.bybit.com/register?affiliate_id=35953" target="_blank">Bybit</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://bybit-exchange.github.io/docs/inverse/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_e63f3e137160a58b.gif" name="Image135" alt="API Version 5" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image136" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image137" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image138" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>cex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://cex.io/r/0/up105393824/0/" target="_blank">CEX.IO</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://trade.cex.io/docs/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image140" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image141" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image142" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinbase</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.coinbase.com/join/58cbe25a355148797479dbd2" target="_blank">Coinbase
				Advanced</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://developers.coinbase.com/api/v2" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image144" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image145" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image146" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinbaseexchange</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://coinbase.com/" target="_blank">Coinbase
				Exchange</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.cloud.coinbase.com/exchange/docs/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image148" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image149" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image150" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinbaseinternational</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://international.coinbase.com/" target="_blank">Coinbase
				International</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.cloud.coinbase.com/intx/docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image152" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image153" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image154" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coincatch</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://partner.coincatch.cc/bg/92hy70391729607848548" target="_blank">CoinCatch</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://coincatch.github.io/github.io/en/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image156" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image157" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image158" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coincheck</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://coincheck.com/" target="_blank">coincheck</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://coincheck.com/documents/exchange/api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image160" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image161" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.coinex.com/register?refer_code=yw5fz" target="_blank">CoinEx</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.coinex.com/api/v2" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image163" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image164" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image165" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image166" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinlist</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://coinlist.co/" target="_blank">Coinlist</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://trade-docs.coinlist.co/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image168" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image169" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinmate</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://coinmate.io/?referral=YTFkM1RsOWFObVpmY1ZjMGREQmpTRnBsWjJJNVp3PT0" target="_blank">CoinMate</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://coinmate.docs.apiary.io/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image171" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image172" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinmetro</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://go.coinmetro.com/?ref=crypto24" target="_blank">Coinmetro</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://documenter.getpostman.com/view/3653795/SVfWN6KS" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image174" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image175" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinone</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://coinone.co.kr/" target="_blank">CoinOne</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://doc.coinone.co.kr/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image177" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image178" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinsph</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://coins.ph/" target="_blank">Coins.ph</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://coins-docs.github.io/rest-api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image180" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image181" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>coinspot</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.coinspot.com.au/register?code=PJURCU" target="_blank">CoinSpot</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.coinspot.com.au/api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image183" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image184" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>cryptocom</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://crypto.com/exch/kdacthrnxt" target="_blank">Crypto.com</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://exchange-docs.crypto.com/exchange/v1/rest-ws/index.html" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image186" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image187" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image188" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image189" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>cryptomus</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://app.cryptomus.com/signup/?ref=JRP4yj" target="_blank">Cryptomus</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://doc.cryptomus.com/personal" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image191" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image192" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>defx</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://app.defx.com/join/6I2CZ7" target="_blank">Defx
				X</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.defx.com/docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image194" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_c37b446da0ef4827.gif" name="Image195" alt="DEX - Distributed EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>delta</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.delta.exchange/app/signup/?code=IULYNB" target="_blank">Delta
				Exchange</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.delta.exchange/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image197" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image198" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>deribit</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.deribit.com/reg-1189.4038" target="_blank">Deribit</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.deribit.com/v2" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image200" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image201" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image202" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>derive</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.derive.xyz/invite/3VB0B" target="_blank">derive</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.derive.xyz/docs/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image204" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_c37b446da0ef4827.gif" name="Image205" alt="DEX - Distributed EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image206" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>digifinex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.digifinex.com/en-ww/from/DhOzBg?channelCode=ljaUPp" target="_blank">DigiFinex</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.digifinex.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image208" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image209" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>ellipx</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.ellipx.com/" target="_blank">Ellipx</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.google.com/document/d/1ZXzTQYffKE_EglTaKptxGQERRnunuLHEMmar7VC9syM" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image211" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image212" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>exmo</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://exmo.me/?ref=131685" target="_blank">EXMO</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://exmo.me/en/api_doc?ref=131685" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_4a797f1e7640a028.gif" name="Image214" alt="API Version 1.1" align="bottom" width="28" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image215" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>fmfwio</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://fmfw.io/referral/da948b21d6c92d69" target="_blank">FMFW.io</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api.fmfw.io/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image217" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image218" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>gate</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.gate.io/signup/2436035" target="_blank">Gate.io</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.gate.io/docs/developers/apiv4/en/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_86d6b2ee53d1a96f.gif" name="Image220" alt="API Version 4" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image221" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image222" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image223" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>gemini</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://gemini.com/" target="_blank">Gemini</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.gemini.com/rest-api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image225" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image226" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image227" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>hashkey</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://global.hashkey.com/en-US/register/invite?invite_code=82FQUN" target="_blank">HashKey
				Global</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://hashkeyglobal-apidoc.readme.io/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image229" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image230" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image231" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image232" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>hitbtc</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://hitbtc.com/?ref_id=5a5d39a65d466" target="_blank">HitBTC</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api.hitbtc.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image234" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image235" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>hollaex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://pro.hollaex.com/signup?affiliation_code=QSWA6G" target="_blank">HollaEx</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://apidocs.hollaex.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image237" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image238" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image239" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>htx</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.htx.com.vc/invite/en-us/1h?invite_code=6rmm2223" target="_blank">HTX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://huobiapi.github.io/docs/spot/v1/en/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image241" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image242" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image243" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image244" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>huobijp</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.huobi.co.jp/register/?invite_code=znnq3" target="_blank">Huobi
				Japan</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api-doc.huobi.co.jp/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image246" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image247" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image248" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>hyperliquid</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://app.hyperliquid.xyz/" target="_blank">Hyperliquid</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image250" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_c37b446da0ef4827.gif" name="Image251" alt="DEX - Distributed EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image252" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image253" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>idex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://idex.io/" target="_blank">IDEX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api-docs-v3.idex.io/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image255" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_c37b446da0ef4827.gif" name="Image256" alt="DEX - Distributed EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image257" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>independentreserve</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.independentreserve.com/" target="_blank">Independent
				Reserve</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.independentreserve.com/API" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image259" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image260" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image261" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>indodax</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://indodax.com/ref/testbitcoincoid/1" target="_blank">INDODAX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/btcid/indodax-official-api-docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_cf542005bd90b591.gif" name="Image263" alt="API Version 2.0" align="bottom" width="28" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image264" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>kraken</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.kraken.com/" target="_blank">Kraken</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.kraken.com/rest/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_6438a092a0449ed1.gif" name="Image266" alt="API Version 0" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image267" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image268" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>krakenfutures</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://futures.kraken.com/" target="_blank">Kraken
				Futures</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.futures.kraken.com/#introduction" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image270" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image271" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image272" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>kucoin</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.kucoin.com/ucenter/signup?rcode=E5wkqe" target="_blank">KuCoin</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.kucoin.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image274" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image275" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image276" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image277" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>kucoinfutures</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://futures.kucoin.com/?rcode=E5wkqe" target="_blank">KuCoin
				Futures</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.kucoin.com/futures" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image279" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image280" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image281" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image282" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>kuna</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://kuna.io/?r=kunaid-gvfihe8az7o4" target="_blank">Kuna</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://kuna.io/documents/api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_86d6b2ee53d1a96f.gif" name="Image284" alt="API Version 4" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image285" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>latoken</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://latoken.com/invite?r=mvgp2djk" target="_blank">Latoken</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api.latoken.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image287" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image288" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>lbank</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.lbank.com/login/?icode=7QCY" target="_blank">LBank</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.lbank.com/en-US/docs/index.html" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image290" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image291" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image292" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>luno</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.luno.com/invite/44893A" target="_blank">luno</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.luno.com/en/api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image294" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image295" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image296" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>mercado</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.mercadobitcoin.com.br/" target="_blank">Mercado
				Bitcoin</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.mercadobitcoin.com.br/api-doc" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image298" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image299" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>mexc</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.mexc.com/register?inviteCode=mexc-1FQ1GNu1" target="_blank">MEXC
				Global</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://mexcdevelop.github.io/apidocs/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image301" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image302" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image303" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image304" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>myokx</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.my.okx.com/join/CCXT2023" target="_blank">MyOKX
				(EEA)</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://my.okx.com/docs-v5/en/#overview" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_e63f3e137160a58b.gif" name="Image306" alt="API Version 5" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image307" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image308" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>ndax</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://one.ndax.io/bfQiSL" target="_blank">NDAX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://apidoc.ndax.io/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image310" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image311" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image312" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>novadax</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.novadax.com.br/?s=ccxt" target="_blank">NovaDAX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://doc.novadax.com/pt-BR/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image314" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image315" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>oceanex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://oceanex.pro/signup?referral=VE24QX" target="_blank">OceanEx</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api.oceanex.pro/doc/v1" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image317" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image318" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>okcoin</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.okcoin.com/account/register?flag=activity&amp;channelId=600001513" target="_blank">OKCoin</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.okcoin.com/docs/en/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_e63f3e137160a58b.gif" name="Image320" alt="API Version 5" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image321" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image322" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>okx</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.okx.com/join/CCXT2023" target="_blank">OKX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.okx.com/docs-v5/en/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_e63f3e137160a58b.gif" name="Image324" alt="API Version 5" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image325" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image326" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image327" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>onetrading</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://onetrading.com/" target="_blank">One Trading</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.onetrading.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image329" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image330" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image331" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>oxfun</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://ox.fun/register?shareAccountId=5ZUD4a7G" target="_blank">OXFUN</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.ox.fun/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image333" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image334" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image335" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>p2b</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://p2pb2b.com/?referral=ee784c53" target="_blank">p2b</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/P2B-team/p2b-api-docs/blob/master/api-doc.md" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image337" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image338" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image339" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>paradex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://app.paradex.trade/r/ccxt24" target="_blank">Paradex</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.api.testnet.paradex.trade/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image341" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_c37b446da0ef4827.gif" name="Image342" alt="DEX - Distributed EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image343" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>paymium</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.paymium.com/page/sign-up?referral=eDAzPoRQFMvaAB8sf-qj" target="_blank">Paymium</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/Paymium/api-documentation" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image345" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image346" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>phemex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://phemex.com/register?referralCode=EDNVJ" target="_blank">Phemex</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://phemex-docs.github.io/#overview" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image348" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image349" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image350" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>poloniex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://poloniex.com/signup?c=UBFZJRPJ" target="_blank">Poloniex</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api-docs.poloniex.com/spot/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image352" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image353" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image354" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>poloniexfutures</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://poloniex.com/signup?c=UBFZJRPJ" target="_blank">Poloniex
				Futures</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://api-docs.poloniex.com/futures/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image356" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image357" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image358" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>probit</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.probit.com/r/34608773" target="_blank">ProBit</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs-en.probit.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image360" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image361" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image362" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>timex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://timex.io/?refcode=1x27vNkTbP1uwkCck" target="_blank">TimeX</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://plasma-relay-backend.timex.io/swagger-ui/index.html" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image364" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image365" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>tokocrypto</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://tokocrypto.com/" target="_blank">Tokocrypto</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.tokocrypto.com/apidocs/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image367" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image368" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>tradeogre</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://tradeogre.com/" target="_blank">tradeogre</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://tradeogre.com/help/api" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_3cb43834389c86e1.gif" name="Image370" alt="API Version 2" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image371" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>upbit</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://upbit.com/" target="_blank">Upbit</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.upbit.com/docs/%EC%9A%94%EC%B2%AD-%EC%88%98-%EC%A0%9C%ED%95%9C" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image373" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image374" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image375" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>vertex</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://app.vertexprotocol.com/?referrer=0xCfC9BaB96a2eA3d3c3F031c005e82E1D9F295aC1" target="_blank">Vertex</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.vertexprotocol.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image377" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_c37b446da0ef4827.gif" name="Image378" alt="DEX - Distributed EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image379" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>wavesexchange</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://wx.network/" target="_blank">Waves.Exchange</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.wx.network/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image381" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_c37b446da0ef4827.gif" name="Image382" alt="DEX - Distributed EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>whitebit</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://whitebit.com/referral/d9bdf40e-28f2-4b52-b2f9-cd1415d82963" target="_blank">WhiteBit</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://github.com/whitebit-exchange/api-docs" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_86d6b2ee53d1a96f.gif" name="Image384" alt="API Version 4" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image385" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image386" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>woo</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://woox.io/register?ref=DIJT0CNL" target="_blank">WOO
				X</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.woox.io/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image388" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image389" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image390" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image391" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>woofipro</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://dex.woo.org/en/trade?ref=CCXT" target="_blank">WOOFI
				PRO</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://orderly.network/docs/build-on-evm/building-on-evm" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image393" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_c37b446da0ef4827.gif" name="Image394" alt="DEX - Distributed EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm">
				<p><a href="https://github.com/ccxt/ccxt/wiki/Certification" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_b54e69a255a64723.gif" name="Image395" alt="CCXT Certified" align="bottom" width="97" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image396" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>xt</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.xt.com/en/accounts/register?ref=9PTM9VW" target="_blank">XT</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://doc.xt.com/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_86d6b2ee53d1a96f.gif" name="Image398" alt="API Version 4" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image399" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm">
				<p><a href="https://ccxt.pro/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_95127093cbab2eb2.gif" name="Image400" alt="CCXT Pro" align="bottom" width="69" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>yobit</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://www.yobit.net/" target="_blank">YoBit</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://www.yobit.net/en/api/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1af0455406e51bd9.gif" name="Image402" alt="API Version 3" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image403" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>zaif</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://zaif.jp/" target="_blank">Zaif</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://techbureau-api-document.readthedocs.io/ja/latest/index.html" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_1ebc63bc2286bff4.gif" name="Image405" alt="API Version 1" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image406" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
		<tr>
			<td width="233" style="border: none; padding: 0cm">
				<p>zonda</p>
			</td>
			<td width="129" style="border: none; padding: 0cm">
				<p><a href="https://auth.zondaglobal.com/ref/jHlbB4mIkdS1" target="_blank">Zonda</a></p>
			</td>
			<td width="44" style="border: none; padding: 0cm">
				<p align="center"><a href="https://docs.zondacrypto.exchange/" target="_blank">
  <font color="#000080">
    <img src="CCXT%20-%20Manual_html_120ce7b16a862ae3.gif" name="Image408" alt="API Version *" align="bottom" width="18" height="21" border="1"/>
  </font>
</a>
</p>
			</td>
			<td width="36" style="border: none; padding: 0cm">
				<p><img src="CCXT%20-%20Manual_html_29d243047b99c87.gif" name="Image409" alt="CEX â€“ Centralized EXchange" align="bottom" width="34" height="21" border="0"/>
</p>
			</td>
			<td width="101" style="border: none; padding: 0cm"></td>
			<td width="76" style="border: none; padding: 0cm"></td>
		</tr>
	</tbody>
</table>
<p>Besides making basic market and limit orders, some exchanges offer
margin trading (leverage), various derivatives (like futures
contracts and options) and also have&nbsp;<a href="https://en.wikipedia.org/wiki/Dark_pool" target="_blank">dark
pools</a>,&nbsp;<a href="https://en.wikipedia.org/wiki/Over-the-counter_(finance)" target="_blank">OTC</a>&nbsp;(over-the-counter
trading), merchant APIs and much more.</p>
<h2 class="western"><a name="instantiation"></a><a href="https://docs.ccxt.com/#/README?id=instantiation">Instantiation</a></h2>
<p>To connect to an exchange and start trading you need to
instantiate an exchange class from ccxt library.</p>
<p>To get the full list of ids of supported exchanges
programmatically:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">import ccxt</code>
<code class="western">print (ccxt.exchanges)</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<p>An exchange can be instantiated like shown in the examples below:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">import ccxt</code>
<code class="western">exchange = ccxt.okcoin () # default id</code>
<code class="western">okcoin1 = ccxt.okcoin ({ 'id': 'okcoin1' })</code>
<code class="western">okcoin2 = ccxt.okcoin ({ 'id': 'okcoin2' })</code>
<code class="western">id = 'btcchina'</code>
<code class="western">btcchina = eval ('ccxt.%s ()' % id)</code>
<code class="western">coinbasepro = getattr (ccxt, 'coinbasepro') ()</code>

<code class="western"># from variable id</code>
<code class="western">exchange_id = 'binance'</code>
<code class="western">exchange_class = getattr(ccxt, exchange_id)</code>
<code class="western">exchange = exchange_class({</code>
<code class="western">    </code><code class="western">'apiKey': 'YOUR_API_KEY',</code>
<code class="western">    </code><code class="western">'secret': 'YOUR_SECRET',</code>
<code class="western">})</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<h3 class="western"><a name="features"></a><a href="https://docs.ccxt.com/#/README?id=features">Features</a></h3>
<p>Major exchanges have the&nbsp;<code class="western">.features</code>&nbsp;property
available, where you can see what methods and functionalities are
supported for each market-type (if any method is set
to&nbsp;<code class="western">null/undefined</code>&nbsp;it means
method is &quot;not supported&quot; by the exchange)</p>
<p><em>this feature is currently a work in progress and might be
incomplete, feel free to report any issues you find in it</em></p>
<pre class="western"><code class="western">const exchange = new ccxt.binance()</code>
<code class="western">console.log(exchange.features);</code>

<code class="western">// outputs like:</code>
<code class="western">{</code>
<code class="western">  </code><code class="western">spot: {</code>
<code class="western">    </code><code class="western">sandbox: true, // whether testnet is supported</code>
<code class="western">    </code><code class="western">createOrder: {</code>
<code class="western">      </code><code class="western">triggerPrice: true,          // if trigger order is supported</code>
<code class="western">      </code><code class="western">triggerPriceType: undefined, // if trigger price type is supported (last, mark, index)</code>
<code class="western">      </code><code class="western">triggerDirection: false,     // if trigger direction is supported (up, down)</code>
<code class="western">      </code><code class="western">stopLossPrice: true,         // if stop-loss order is supported (read &quot;Stop Loss Orders&quot; paragraph) </code>
<code class="western">      </code><code class="western">takeProfitPrice: true,       // if take-profit order is supported</code>
<code class="western">      </code><code class="western">attachedStopLossTakeProfit: {       </code>
<code class="western">        </code><code class="western">triggerPriceType: {</code>
<code class="western">            </code><code class="western">last: true,</code>
<code class="western">            </code><code class="western">mark: true,</code>
<code class="western">            </code><code class="western">index: true,</code>
<code class="western">        </code><code class="western">},</code>
<code class="western">        </code><code class="western">price: true,               // whether 'limit' price can be used (instead of market order)</code>
<code class="western">      </code><code class="western">},</code>
<code class="western">      </code><code class="western">marginMode: true,            // if `marginMode` param is supported (cross, isolated)</code>
<code class="western">      </code><code class="western">timeInForce: {               // supported TIF types</code>
<code class="western">        </code><code class="western">GTC: true,</code>
<code class="western">        </code><code class="western">IOC: true,</code>
<code class="western">        </code><code class="western">FOK: true,</code>
<code class="western">        </code><code class="western">PO: true,</code>
<code class="western">        </code><code class="western">GTD: false</code>
<code class="western">      </code><code class="western">},</code>
<code class="western">      </code><code class="western">hedged: false,              // if `hedged` param is supported (true, false)</code>
<code class="western">      </code><code class="western">leverage: false,            // if `leverage` param is supported (true, false)</code>
<code class="western">      </code><code class="western">selfTradePrevention: true,  // if `selfTradePrevention` param is supported (true, false)</code>
<code class="western">      </code><code class="western">trailing: true,             // if trailing order is supported</code>
<code class="western">      </code><code class="western">iceberg: true,              // if iceberg order is supported</code>
<code class="western">      </code><code class="western">marketBuyByCost: true,      // if creating market buy order is possible with `cost` param</code>
<code class="western">      </code><code class="western">marketBuyRequiresPrice: true,// if creating market buy order (if 'cost' not used) requires `price` param to be set</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">createOrders: {</code>
<code class="western">        </code><code class="western">'max': 50,              // if batch order creation is supported</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchMyTrades: {</code>
<code class="western">      </code><code class="western">limit: 1000,              // max limit per call</code>
<code class="western">      </code><code class="western">daysBack: undefined,      // max historical period that can be accessed</code>
<code class="western">      </code><code class="western">untilDays: 1              // if `until` param is supported, then this is permitted distance from `since`</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchOrder: {</code>
<code class="western">      </code><code class="western">marginMode: true,         // when supported, margin order should be fetched with this flag</code>
<code class="western">      </code><code class="western">trigger: false,           // similar as above</code>
<code class="western">      </code><code class="western">trailing: false           // similar as above</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">// other methods have similar properties</code>
<code class="western">    </code><code class="western">fetchOpenOrders: {</code>
<code class="western">      </code><code class="western">limit: undefined,</code>
<code class="western">      </code><code class="western">marginMode: true,</code>
<code class="western">      </code><code class="western">trigger: false,</code>
<code class="western">      </code><code class="western">trailing: false</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchOrders: {</code>
<code class="western">      </code><code class="western">limit: 1000,</code>
<code class="western">      </code><code class="western">daysBack: undefined,</code>
<code class="western">      </code><code class="western">untilDays: 10000,</code>
<code class="western">      </code><code class="western">marginMode: true,</code>
<code class="western">      </code><code class="western">trigger: false,</code>
<code class="western">      </code><code class="western">trailing: false</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchClosedOrders: {</code>
<code class="western">      </code><code class="western">limit: 1000,</code>
<code class="western">      </code><code class="western">daysBackClosed: undefined, // max days-back for closed orders</code>
<code class="western">      </code><code class="western">daysBackCanceled: undefined, // max days-back for canceled orders</code>
<code class="western">      </code><code class="western">untilDays: 10000,</code>
<code class="western">      </code><code class="western">marginMode: true,</code>
<code class="western">      </code><code class="western">trigger: false,</code>
<code class="western">      </code><code class="western">trailing: false</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">fetchOHLCV: {</code>
<code class="western">      </code><code class="western">paginate: true,</code>
<code class="western">      </code><code class="western">limit: 1000</code>
<code class="western">    </code><code class="western">}</code>
<code class="western">  </code><code class="western">},</code>
<code class="western">  </code><code class="western">swap: {</code>
<code class="western">    </code><code class="western">linear: { ... }, // similar to above dict</code>
<code class="western">    </code><code class="western">inverse: { ... }, // similar to above dict</code>
<code class="western">  </code><code class="western">}</code>
<code class="western">  </code><code class="western">future: {</code>
<code class="western">    </code><code class="western">linear: { ... }, // similar to above dict</code>
<code class="western">    </code><code class="western">inverse: { ... }, // similar to above dict</code>
<code class="western">  </code><code class="western">}</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><h3 class="western">
<a name="overriding-exchange-properties-upon-instantiation"></a><a href="https://docs.ccxt.com/#/README?id=overriding-exchange-properties-upon-instantiation">Overriding
Exchange Properties Upon Instantiation</a></h3>
<p>Most of exchange properties as well as specific options can be
overrided upon exchange class instantiation or afterwards, like shown
below:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">exchange = ccxt.binance ({</code>
<code class="western">    </code><code class="western">'rateLimit': 10000,  # unified exchange property</code>
<code class="western">    </code><code class="western">'headers': {</code>
<code class="western">        </code><code class="western">'YOUR_CUSTOM_HTTP_HEADER': 'YOUR_CUSTOM_VALUE',</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'options': {</code>
<code class="western">        </code><code class="western">'adjustForTimeDifference': True,  # exchange-specific option</code>
<code class="western">    </code><code class="western">}</code>
<code class="western">})</code>
<code class="western">exchange.options['adjustForTimeDifference'] = False</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<h3 class="western"><a name="overriding-exchange-methods"></a><a href="https://docs.ccxt.com/#/README?id=overriding-exchange-methods">Overriding
Exchange Methods</a></h3>
<p>In all CCXT-supported languages, you can override instance methods
during runtime:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">ex = ccxt.binance()</code>
<code class="western">def my_overload(symbol, params = {}):</code>
<code class="western">    </code><code class="western"># your codes go here</code>

<code class="western">ex.fetch_ticker = my_overload</code>
<code class="western">print(ex.fetch_ticker('BTC/USDT'))</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<h3 class="western"><a name="testnets-and-sandbox-environments"></a><a href="https://docs.ccxt.com/#/README?id=testnets-and-sandbox-environments">Testnets
And Sandbox Environments</a></h3>
<p>Some exchanges also offer separate APIs for testing purposes that
allows developers to trade virtual money for free and test out their
ideas. Those APIs are called&nbsp;<em>&quot;testnets&quot;,
&quot;sandboxes&quot; or &quot;staging environments&quot;</em>&nbsp;(with
virtual testing assets) as opposed to&nbsp;<em>&quot;mainnets&quot;
and &quot;production environments&quot;</em>&nbsp;(with real assets).
Most often a sandboxed API is a clone of a production API, so, it's
literally the same API, except for the URL to the exchange server.</p>
<p>CCXT unifies that aspect and allows the user to switch to the
exchange's sandbox (if supported by the underlying exchange). To
switch to the sandbox one has to call the&nbsp;<code class="western">exchange.setSandboxMode
(true)</code>&nbsp;or&nbsp;<code class="western">exchange.set_sandbox_mode(true)</code>&nbsp;<strong>immediately
after creating the exchange before any other call</strong>!</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">exchange = ccxt.binance(config)</code>
<code class="western">exchange.set_sandbox_mode(True)  # enable sandbox mode</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm">The&nbsp;<code class="western">exchange.setSandboxMode
	(true) / exchange.set_sandbox_mode (True)</code>&nbsp;has to be your
	first call immediately after creating the exchange (before any other
	calls)</p>
	<li/>
<p style="margin-bottom: 0cm">To obtain the&nbsp;<a href="https://docs.ccxt.com/#/README?id=authentication">API
	keys</a>&nbsp;to the sandbox the user has to register with the
	sandbox website of the exchange in question and create a sandbox
	keypair</p>
	<li/>
<p><strong>Sandbox keys are not interchangeable with
	production keys!</strong></p>
</ul>
<h2 class="western"><a name="exchange-structure"></a><a href="https://docs.ccxt.com/#/README?id=exchange-structure">Exchange
Structure</a></h2>
<p>Every exchange has a set of properties and methods, most of which
you can override by passing an associative array of params to an
exchange constructor. You can also make a subclass and override
everything.</p>
<p>Here's an overview of generic exchange properties with values
added for example:</p>
<pre class="western"><code class="western">{</code>
<code class="western">    </code><code class="western">'id':   'exchange'                   // lowercase string exchange id</code>
<code class="western">    </code><code class="western">'name': 'Exchange'                   // human-readable string</code>
<code class="western">    </code><code class="western">'countries': [ 'US', 'CN', 'EU' ],   // array of ISO country codes</code>
<code class="western">    </code><code class="western">'urls': {</code>
<code class="western">        </code><code class="western">'api': 'https://api.example.com/data',  // string or dictionary of base API URLs</code>
<code class="western">        </code><code class="western">'www': 'https://www.example.com'        // string website URL</code>
<code class="western">        </code><code class="western">'doc': 'https://docs.example.com/api',  // string URL or array of URLs</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'version':         'v1',             // string ending with digits</code>
<code class="western">    </code><code class="western">'api':             { ... },          // dictionary of api endpoints</code>
<code class="western">    </code><code class="western">'has': {                             // exchange capabilities</code>
<code class="western">        </code><code class="western">'CORS': false,</code>
<code class="western">        </code><code class="western">'cancelOrder': true,</code>
<code class="western">        </code><code class="western">'createDepositAddress': false,</code>
<code class="western">        </code><code class="western">'createOrder': true,</code>
<code class="western">        </code><code class="western">'fetchBalance': true,</code>
<code class="western">        </code><code class="western">'fetchCanceledOrders': false,</code>
<code class="western">        </code><code class="western">'fetchClosedOrder': false,</code>
<code class="western">        </code><code class="western">'fetchClosedOrders': false,</code>
<code class="western">        </code><code class="western">'fetchCurrencies': false,</code>
<code class="western">        </code><code class="western">'fetchDepositAddress': false,</code>
<code class="western">        </code><code class="western">'fetchMarkets': true,</code>
<code class="western">        </code><code class="western">'fetchMyTrades': false,</code>
<code class="western">        </code><code class="western">'fetchOHLCV': false,</code>
<code class="western">        </code><code class="western">'fetchOpenOrder': false,</code>
<code class="western">        </code><code class="western">'fetchOpenOrders': false,</code>
<code class="western">        </code><code class="western">'fetchOrder': false,</code>
<code class="western">        </code><code class="western">'fetchOrderBook': true,</code>
<code class="western">        </code><code class="western">'fetchOrders': false,</code>
<code class="western">        </code><code class="western">'fetchStatus': 'emulated',</code>
<code class="western">        </code><code class="western">'fetchTicker': true,</code>
<code class="western">        </code><code class="western">'fetchTickers': false,</code>
<code class="western">        </code><code class="western">'fetchBidsAsks': false,</code>
<code class="western">        </code><code class="western">'fetchTrades': true,</code>
<code class="western">        </code><code class="western">'withdraw': false,</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'timeframes': {                      // empty if the exchange.has['fetchOHLCV'] !== true</code>
<code class="western">        </code><code class="western">'1m': '1minute',</code>
<code class="western">        </code><code class="western">'1h': '1hour',</code>
<code class="western">        </code><code class="western">'1d': '1day',</code>
<code class="western">        </code><code class="western">'1M': '1month',</code>
<code class="western">        </code><code class="western">'1y': '1year',</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'timeout':           10000,          // number in milliseconds</code>
<code class="western">    </code><code class="western">'rateLimit':         2000,           // number in milliseconds</code>
<code class="western">    </code><code class="western">'userAgent':        'ccxt/1.1.1 ...' // string, HTTP User-Agent header</code>
<code class="western">    </code><code class="western">'verbose':           false,          // boolean, output error details</code>
<code class="western">    </code><code class="western">'markets':          { ... }          // dictionary of markets/pairs by symbol</code>
<code class="western">    </code><code class="western">'symbols':          [ ... ]          // sorted list of string symbols (traded pairs)</code>
<code class="western">    </code><code class="western">'currencies':       { ... }          // dictionary of currencies by currency code</code>
<code class="western">    </code><code class="western">'markets_by_id':    { ... },         // dictionary of array of dictionaries (markets) by id</code>
<code class="western">    </code><code class="western">'currencies_by_id': { ... },         // dictionary of dictionaries (markets) by id</code>
<code class="western">    </code><code class="western">'apiKey':   '92560ffae9b8a0421...',  // string public apiKey (ASCII, hex, Base64, ...)</code>
<code class="western">    </code><code class="western">'secret':   '9aHjPmW+EtRRKN/Oi...'   // string private secret key</code>
<code class="western">    </code><code class="western">'password': '6kszf4aci8r',           // string password</code>
<code class="western">    </code><code class="western">'uid':      '123456',                // string user id</code>
<code class="western">    </code><code class="western">'options':          { ... },         // exchange-specific options</code>
<code class="western">    </code><code class="western">// ... other properties here ...</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><h3 class="western">
<a name="exchange-properties"></a><a href="https://docs.ccxt.com/#/README?id=exchange-properties">Exchange
Properties</a></h3>
<p>Below is a detailed description of each of the base exchange
properties:</p>
<ul>
	<li/>
<p><code class="western">id</code>: Each exchange has a
	default id. The id is not used for anything, it's a string literal
	for user-land exchange instance identification purposes. You can
	have multiple links to the same exchange and differentiate them by
	ids. Default ids are all lowercase and correspond to exchange names.</p>
	<li/>
<p><code class="western">name</code>: This is a string literal
	containing the human-readable exchange name.</p>
	<li/>
<p><code class="western">countries</code>: An array of string
	literals of 2-symbol ISO country codes, where the exchange is
	operating from.</p>
	<li/>
<p><code class="western">urls['api']</code>: The single string
	literal base URL for API calls or an associative array of separate
	URLs for private and public APIs.</p>
	<li/>
<p><code class="western">urls['www']</code>: The main HTTP
	website URL.</p>
	<li/>
<p><code class="western">urls['doc']</code>: A single string
	URL link to original documentation for exchange API on their website
	or an array of links to docs.</p>
	<li/>
<p><code class="western">version</code>: A string literal
	containing version identifier for current exchange API. The ccxt
	library will append this version string to the API Base URL upon
	each request. You don't have to modify it, unless you are
	implementing a new exchange API. The version identifier is a usually
	a numeric string starting with a letter 'v' in some cases, like
	v1.1. Do not override it unless you are implementing your own new
	crypto exchange class.</p>
	<li/>
<p><code class="western">api</code>: An associative array
	containing a definition of all API endpoints exposed by a crypto
	exchange. The API definition is used by ccxt to automatically
	construct callable instance methods for each available endpoint.</p>
	<li/>
<p><code class="western">has</code>: This is an associative
	array of exchange capabilities
	(e.g&nbsp;<code class="western">fetchTickers</code>,&nbsp;<code class="western">fetchOHLCV</code>&nbsp;or&nbsp;<code class="western">CORS</code>).</p>
	<li/>
<p><code class="western">timeframes</code>: An associative
	array of timeframes, supported by the fetchOHLCV method of the
	exchange. This is only populated when&nbsp;<code class="western">has['fetchOHLCV']</code>&nbsp;property
	is true.</p>
	<li/>
<p><code class="western">timeout</code>: A timeout in
	milliseconds for a request-response roundtrip (default timeout is
	10000 ms = 10 seconds). If the response is not received in that
	time, the library will throw an&nbsp;<code class="western">RequestTimeout</code>&nbsp;exception.
	You can leave the default timeout value or set it to a reasonable
	value. Hanging forever with no timeout is not your option, for sure.
	You don't have to override this option in general case.</p>
	<li/>
<p><code class="western">rateLimit</code>: A request rate
	limit in milliseconds. Specifies the required minimal delay between
	two consequent HTTP requests to the same exchange. The built-in
	rate-limiter is enabled by default and can be turned off by setting
	the&nbsp;<code class="western">enableRateLimit</code>&nbsp;property
	to false.</p>
	<li/>
<p><code class="western">enableRateLimit</code>: A boolean
	(true/false) value that enables the built-in rate limiter and
	throttles consecutive requests. This setting is&nbsp;<code class="western">true</code>&nbsp;(enabled)
	by default.&nbsp;<strong>The user is required to implement own&nbsp;<a href="https://docs.ccxt.com/#/README?id=rate-limit">rate
	limiting</a>&nbsp;or leave the built-in rate limiter enabled to
	avoid being banned from the exchange</strong>.</p>
	<li/>
<p><code class="western">userAgent</code>: An object to set
	HTTP User-Agent header to. The ccxt library will set its User-Agent
	by default. Some exchanges may not like it. If you are having
	difficulties getting a reply from an exchange and want to turn
	User-Agent off or use the default one, set this value to false,
	undefined, or an empty string. The value of&nbsp;<code class="western">userAgent</code>&nbsp;may
	be overrided by HTTP&nbsp;<code class="western">headers</code>&nbsp;property
	below.</p>
	<li/>
<p><code class="western">headers</code>: An associative array
	of HTTP headers and their values. Default value is empty&nbsp;<code class="western">{}</code>.
	All headers will be prepended to all requests. If
	the&nbsp;<code class="western">User-Agent</code>&nbsp;header is set
	within&nbsp;<code class="western">headers</code>, it will override
	whatever value is set in the&nbsp;<code class="western">userAgent</code>&nbsp;property
	above.</p>
	<li/>
<p><code class="western">verbose</code>: A boolean flag
	indicating whether to log HTTP requests to stdout (verbose flag is
	false by default). Python people have an alternative way of DEBUG
	logging with a standard pythonic logger, which is enabled by adding
	these two lines to the beginning of their code:</p>
	<pre class="western"><code class="western">import logging</code>
<code class="western">logging.basicConfig(level=logging.DEBUG)</code>Copy to clipboardErrorCopied</pre>
	<li/>
<p><code class="western">markets</code>: An associative array
	of markets indexed by common trading pairs or symbols. Markets
	should be loaded prior to accessing this property. Markets are
	unavailable until you call the&nbsp;<code class="western">loadMarkets()
	/ load_markets()</code>&nbsp;method on exchange instance.</p>
	<li/>
<p><code class="western">symbols</code>: A non-associative
	array (a list) of symbols available with an exchange, sorted in
	alphabetical order. These are the keys of the&nbsp;<code class="western">markets</code>&nbsp;property.
	Symbols are loaded and reloaded from markets. This property is a
	convenient shorthand for all market keys.</p>
	<li/>
<p><code class="western">currencies</code>: An associative
	array (a dict) of currencies by codes (usually 3 or 4 letters)
	available with an exchange. Currencies are loaded and reloaded from
	markets.</p>
	<li/>
<p><code class="western">markets_by_id</code>: An associative
	array of arrays of markets indexed by exchange-specific ids.
	Typically a length one array unless there are multiple markets with
	the same marketId. Markets should be loaded prior to accessing this
	property.</p>
	<li/>
<p><code class="western">apiKey</code>: This is your public
	API key string literal. Most exchanges require&nbsp;<a href="https://docs.ccxt.com/#/README?id=api-keys-setup">API
	keys setup</a>.</p>
	<li/>
<p><code class="western">secret</code>: Your private secret
	API key string literal. Most exchanges require this as well together
	with the apiKey.</p>
	<li/>
<p><code class="western">password</code>: A string literal
	with your password/phrase. Some exchanges require this parameter for
	trading, but most of them don't.</p>
	<li/>
<p><code class="western">uid</code>: A unique id of your
	account. This can be a string literal or a number. Some exchanges
	also require this for trading, but most of them don't.</p>
	<li/>
<p><code class="western">requiredCredentials</code>: A unified
	associative dictionary that shows which of the above API credentials
	are required for sending private API calls to the underlying
	exchange (an exchange may require a specific set of keys).</p>
	<li/>
<p><code class="western">options</code>: An exchange-specific
	associative dictionary containing special keys and options that are
	accepted by the underlying exchange and supported in CCXT.</p>
	<li/>
<p><code class="western">precisionMode</code>: The exchange
	decimal precision counting mode, read more about&nbsp;<a href="https://docs.ccxt.com/#/README?id=precision-and-limits">Precision
	And Limits</a></p>
	<li/>
<p>For proxies
	-&nbsp;<code class="western">proxyUrl</code>,&nbsp;<code class="western">httpUrl</code>,&nbsp;<code class="western">httpsUrl</code>,&nbsp;<code class="western">socksProxy</code>,&nbsp;<code class="western">wsProxy</code>,&nbsp;<code class="western">wssProxy</code>,&nbsp;<code class="western">wsSocksProxy</code>&nbsp;:
	An url of specific proxy. Read details in&nbsp;<a href="https://docs.ccxt.com/#/README?id=proxy">Proxy</a>&nbsp;section.</p>
</ul>
<p>See this section on&nbsp;<a href="https://docs.ccxt.com/#/README?id=overriding-exchange-properties-upon-instantiation">Overriding
exchange properties</a>.</p>
<h4 class="western"><a name="exchange-metadata"></a><a href="https://docs.ccxt.com/#/README?id=exchange-metadata">Exchange
Metadata</a></h4>
<ul>
	<li/>
<p><code class="western">has</code>: An assoc-array containing
	flags for exchange capabilities, including the following:</p>
	<pre class="western"><code class="western">'has': {</code>

<code class="western">    </code><code class="western">'CORS': false,  // has Cross-Origin Resource Sharing enabled (works from browser) or not</code>

<code class="western">    </code><code class="western">// unified methods availability flags (can be true, false, or 'emulated'):</code>

<code class="western">    </code><code class="western">'cancelOrder': true,</code>
<code class="western">    </code><code class="western">'createDepositAddress': false,</code>
<code class="western">    </code><code class="western">'createOrder': true,</code>
<code class="western">    </code><code class="western">'fetchBalance': true,</code>
<code class="western">    </code><code class="western">'fetchCanceledOrders': false,</code>
<code class="western">    </code><code class="western">'fetchClosedOrder': false,</code>
<code class="western">    </code><code class="western">'fetchClosedOrders': false,</code>
<code class="western">    </code><code class="western">'fetchCurrencies': false,</code>
<code class="western">    </code><code class="western">'fetchDepositAddress': false,</code>
<code class="western">    </code><code class="western">'fetchMarkets': true,</code>
<code class="western">    </code><code class="western">'fetchMyTrades': false,</code>
<code class="western">    </code><code class="western">'fetchOHLCV': false,</code>
<code class="western">    </code><code class="western">'fetchOpenOrder': false,</code>
<code class="western">    </code><code class="western">'fetchOpenOrders': false,</code>
<code class="western">    </code><code class="western">'fetchOrder': false,</code>
<code class="western">    </code><code class="western">'fetchOrderBook': true,</code>
<code class="western">    </code><code class="western">'fetchOrders': false,</code>
<code class="western">    </code><code class="western">'fetchStatus': 'emulated',</code>
<code class="western">    </code><code class="western">'fetchTicker': true,</code>
<code class="western">    </code><code class="western">'fetchTickers': false,</code>
<code class="western">    </code><code class="western">'fetchBidsAsks': false,</code>
<code class="western">    </code><code class="western">'fetchTrades': true,</code>
<code class="western">    </code><code class="western">'withdraw': false,</code>
<code class="western">    </code><code class="western">...</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
	The meaning of each flag showing availability of this or that method
	is:</p>
	<ul>
		<li/>
<p>a value of&nbsp;<code class="western">undefined</code>&nbsp;/&nbsp;<code class="western">None</code>&nbsp;/&nbsp;<code class="western">null</code>&nbsp;means
		the method is not currently implemented in ccxt (either ccxt has
		not unified it yet or the method isn't natively available from the
		exchange API)</p>
		<li/>
<p>boolean&nbsp;<code class="western">false</code>&nbsp;specifically
		means that the endpoint isn't natively available from the exchange
		API</p>
		<li/>
<p>boolean&nbsp;<code class="western">true</code>&nbsp;means
		the endpoint is natively available from the exchange API and
		unified in the ccxt library</p>
		<li/>
<p><code class="western">'emulated'</code>&nbsp;string means
		the endpoint isn't natively available from the exchange API but
		reconstructed (as much as possible) by the ccxt library from other
		available true-methods</p>
		<p>For a complete list of all exchages and their supported methods,
		please, refer to this
		example:&nbsp;<a href="https://github.com/ccxt/ccxt/blob/master/examples/js/exchange-capabilities.js" target="_blank">https://github.com/ccxt/ccxt/blob/master/examples/js/exchange-capabilities.js</a></p>
	</ul>
</ul>
<h2 class="western"><a name="rate-limit"></a><a href="https://docs.ccxt.com/#/README?id=rate-limit">Rate
Limit</a></h2>
<p>Exchanges usually impose what is called a&nbsp;<em>rate limit</em>.
Exchanges will remember and track your user credentials and your IP
address and will not allow you to query the API too frequently. They
balance their load and control traffic congestion to protect API
servers from (D)DoS and misuse.</p>
<p><strong>WARNING: Stay under the rate limit to avoid ban!</strong></p>
<p>Most exchanges allow&nbsp;<strong>up to 1 or 2 requests per
second</strong>. Exchanges may temporarily restrict your access to
their API or ban you for some period of time if you are too
aggressive with your requests.</p>
<p><strong>The&nbsp;</strong><strong><code class="western">exchange.rateLimit</code></strong><strong>&nbsp;property
is set to a safe default which is sub-optimal. Some exchanges may
have varying rate limits for different endpoints. It is up to the
user to tweak&nbsp;</strong><strong><code class="western">rateLimit</code></strong><strong>&nbsp;according
to application-specific purposes.</strong></p>
<p>The CCXT library has a built-in experimental rate-limiter that
will do the necessary throttling in background transparently to the
user.&nbsp;<strong>WARNING: users are responsible for at least some
type of rate-limiting: either by implementing a custom algorithm or
by doing it with the built-in rate-limiter.</strong>.</p>
<p>You can turn on/off the built-in rate-limiter
with&nbsp;<code class="western">.enableRateLimit</code>&nbsp;property,
like so:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western">
<code class="western"># enable built-in rate limiting upon instantiation of the exchange</code>
<code class="western">exchange = ccxt.bitfinex({</code>
<code class="western">    </code><code class="western"># 'enableRateLimit': True,  # enabled by default</code>
<code class="western">})</code>

<code class="western"># or switch the built-in rate-limiter on or off later after instantiation</code>
<code class="western">exchange.enableRateLimit = True  # enable</code>
<code class="western">exchange.enableRateLimit = False  # disable</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<p>In case your calls hit a rate limit or get nonce errors, the ccxt
library will throw an&nbsp;<code class="western">InvalidNonce</code>&nbsp;exception,
or, in some cases, one of the following types:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">DDoSProtection</code></p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">ExchangeNotAvailable</code></p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">ExchangeError</code></p>
	<li/>
<p><code class="western">InvalidNonce</code></p>
</ul>
<p>A later retry is usually enough to handle that.</p>
<h3 class="western"><a name="notes-on-rate-limiter"></a><a href="https://docs.ccxt.com/#/README?id=notes-on-rate-limiter">Notes
On Rate Limiter</a></h3>
<h4 class="western"><a name="one-rate-limiter-per-each-exchange-instance"></a>
<a href="https://docs.ccxt.com/#/README?id=one-rate-limiter-per-each-exchange-instance">One
Rate Limiter Per Each Exchange Instance</a></h4>
<p>The rate limiter is a property of the exchange instance, in other
words, each exchange instance has its own rate limiter that is not
aware of the other instances. In many cases the user should reuse the
same exchange instance throughout the program. Do not use multiple
instances of the same exchange with the same API keypair from the
same IP address.</p>
<pre class="western"><code class="western">// DO NOT DO THIS!</code>

<code class="western">const binance1 = new ccxt.binance ()</code>
<code class="western">const binance2 = new ccxt.binance ()</code>
<code class="western">const binance3 = new ccxt.binance ()</code>

<code class="western">while (true) {</code>
<code class="western">    </code><code class="western">const result = await Promise.all ([</code>
<code class="western">        </code><code class="western">binance1.fetchOrderBook ('BTC/USDT'),</code>
<code class="western">        </code><code class="western">binance2.fetchOrderBook ('ETH/USDT'),</code>
<code class="western">        </code><code class="western">binance3.fetchOrderBook ('ETH/BTC'),</code>
<code class="western">    </code><code class="western">])</code>
<code class="western">    </code><code class="western">console.log (result)</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Reuse the exchange instance as much as possible as shown below:</p>
<pre class="western"><code class="western">// DO THIS INSTEAD:</code>

<code class="western">const binance = new ccxt.binance ()</code>

<code class="western">while (true) {</code>
<code class="western">    </code><code class="western">const result = await Promise.all ([</code>
<code class="western">        </code><code class="western">binance.fetchOrderBook ('BTC/USDT'),</code>
<code class="western">        </code><code class="western">binance.fetchOrderBook ('ETH/USDT'),</code>
<code class="western">        </code><code class="western">binance.fetchOrderBook ('ETH/BTC'),</code>
<code class="western">    </code><code class="western">])</code>
<code class="western">    </code><code class="western">console.log (result)</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Since the rate limiter belongs to the exchange instance, destroying
the exchange instance will destroy the rate limiter as well. Among
the most common pitfalls with the rate limiting is creating and
dropping the exchange instance over and over again. If in your
program you are creating and destroying the exchange instance (say,
inside a function that is called multiple times), then you are
effectively resetting the rate limiter over and over and that will
eventually break the rate limits. If you are recreating the exchange
instance every time instead of reusing it, CCXT will try to load the
markets every time. Therefore, you will force-load the markets over
and over as explained in the&nbsp;<a href="https://docs.ccxt.com/#/README?id=loading-markets">Loading
Markets</a>&nbsp;section. Abusing the markets endpoint will
eventually break the rate limiter as well.</p>
<pre class="western"><code class="western">// DO NOT DO THIS!</code>

<code class="western">async function tick () {</code>
<code class="western">    </code><code class="western">const exchange = new ccxt.binance ()</code>
<code class="western">    </code><code class="western">const response = await exchange.fetchOrderBook ('BTC/USDT')</code>
<code class="western">    </code><code class="western">// ... some processing here ...</code>
<code class="western">    </code><code class="western">return response</code>
<code class="western">}</code>

<code class="western">while (true) {</code>
<code class="western">    </code><code class="western">const result = await tick ()</code>
<code class="western">    </code><code class="western">console.log (result)</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Do not break this rule unless you really understand the inner
workings of the rate-limiter and you are 100% sure you know what
you're doing. In order to stay safe always reuse the exchange
instance throughout your functions and methods callchain like shown
below:</p>
<pre class="western"><code class="western">// DO THIS INSTEAD:</code>

<code class="western">async function tick (exchange) {</code>
<code class="western">    </code><code class="western">const response = await exchange.fetchOrderBook ('BTC/USDT')</code>
<code class="western">    </code><code class="western">// ... some processing here ...</code>
<code class="western">    </code><code class="western">return response</code>
<code class="western">}</code>

<code class="western">const exchange = new ccxt.binance ()</code>
<code class="western">while (true) {</code>
<code class="western">    </code><code class="western">const result = await tick (exchange)</code>
<code class="western">    </code><code class="western">console.log (result)</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><h3 class="western">
<a name="ddos-protection-by-cloudflare-incapsula"></a><a href="https://docs.ccxt.com/#/README?id=ddos-protection-by-cloudflare-incapsula">DDoS
Protection By Cloudflare / Incapsula</a></h3>
<p>Some exchanges are&nbsp;<a href="https://en.wikipedia.org/wiki/Denial-of-service_attack" target="_blank">DDoS</a>-protected
by&nbsp;<a href="https://www.cloudflare.com/" target="_blank">Cloudflare</a>&nbsp;or&nbsp;<a href="https://www.incapsula.com/" target="_blank">Incapsula</a>.
Your IP can get temporarily blocked during periods of high load.
Sometimes they even restrict whole countries and regions. In that
case their servers usually return a page that states a HTTP 40x error
or runs an AJAX test of your browser / captcha test and delays the
reload of the page for several seconds. Then your browser/fingerprint
is granted access temporarily and gets added to a whitelist or
receives a HTTP cookie for further use.</p>
<p>The most common symptoms for a DDoS protection problem,
rate-limiting problem or for a location-based filtering issue:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm">Getting&nbsp;<code class="western">RequestTimeout</code>&nbsp;exceptions
	with all types of exchange methods</p>
	<li/>
<p style="margin-bottom: 0cm">Catching&nbsp;<code class="western">ExchangeError</code>&nbsp;or&nbsp;<code class="western">ExchangeNotAvailable</code>&nbsp;with
	HTTP error codes 400, 403, 404, 429, 500, 501, 503, etc..</p>
	<li/>
<p style="margin-bottom: 0cm">Having DNS resolving issues, SSL
	certificate issues and low-level connectivity issues</p>
	<li/>
<p>Getting a template HTML page instead of JSON from the
	exchange</p>
</ul>
<p>If you encounter DDoS protection errors and cannot reach a
particular exchange then:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm">use a&nbsp;<a href="https://docs.ccxt.com/#/README?id=proxy">proxy</a>&nbsp;(this
	is less responsive, though)</p>
	<li/>
<p style="margin-bottom: 0cm">ask the exchange support to add
	you to a whitelist</p>
	<li/>
<p style="margin-bottom: 0cm">try an alternative IP within a
	different geographic region</p>
	<li/>
<p style="margin-bottom: 0cm">run your software in a
	distributed network of servers</p>
	<li/>
<p style="margin-bottom: 0cm">run your software in close
	proximity to the exchange (same country, same city, same datacenter,
	same server rack, same server)</p>
	<li/>
<p>...</p>
</ul>
<h1 class="western"><a name="markets"></a><a href="https://docs.ccxt.com/#/README?id=markets">Markets</a></h1>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=currency-structure">Currency
	Structure</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=market-structure">Market
	Structure</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=precision-and-limits">Precision
	And Limits</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=loading-markets">Loading
	Markets</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=symbols-and-market-ids">Symbols
	And Market Ids</a></p>
	<li/>
<p><a href="https://docs.ccxt.com/#/README?id=market-cache-force-reload">Market
	Cache Force Reload</a></p>
</ul>
<p>Each exchange is a place for trading some kinds of valuables. The
exchanges may use differing terms to call them:&nbsp;<em>&quot;a
currency&quot;</em>,&nbsp;<em>&quot;an asset&quot;</em>,&nbsp;<em>&quot;a
coin&quot;</em>,&nbsp;<em>&quot;a
token&quot;</em>,&nbsp;<em>&quot;stock&quot;</em>,&nbsp;<em>&quot;commodity&quot;</em>,&nbsp;<em>&quot;crypto&quot;</em>,
&quot;fiat&quot;, etc. A place for trading one asset for another is
usually called&nbsp;<em>&quot;a market&quot;</em>,&nbsp;<em>&quot;a
symbol&quot;</em>,&nbsp;<em>&quot;a trading pair&quot;</em>,&nbsp;<em>&quot;a
contract&quot;</em>, etc.</p>
<p>In terms of the ccxt library, every exchange offers
multiple&nbsp;<strong>markets</strong>&nbsp;within itself. Each
market is defined by two or more&nbsp;<strong>currencies</strong>.
The set of markets differs from exchange to exchange opening
possibilities for cross-exchange and cross-market arbitrage.</p>
<h2 class="western"><a name="currency-structure"></a><a href="https://docs.ccxt.com/#/README?id=currency-structure">Currency
Structure</a></h2>
<pre class="western"><code class="western">{</code>
<code class="western">    </code><code class="western">'id':       'btc',       // string literal for referencing within an exchange</code>
<code class="western">    </code><code class="western">'code':     'BTC',       // uppercase unified string literal code of the currency</code>
<code class="western">    </code><code class="western">'name':     'Bitcoin',   // string, human-readable name, if specified</code>
<code class="western">    </code><code class="western">'active':    true,       // boolean, currency status (tradeable and withdrawable)</code>
<code class="western">    </code><code class="western">'fee':       0.123,      // withdrawal fee, flat</code>
<code class="western">    </code><code class="western">'precision': 8,          // number of decimal digits &quot;after the dot&quot; (depends on exchange.precisionMode)</code>
<code class="western">    </code><code class="western">'deposit':   true        // boolean, deposits are available</code>
<code class="western">    </code><code class="western">'withdraw':  true        // boolean, withdraws are available</code>
<code class="western">    </code><code class="western">'limits': {              // value limits when placing orders on this market</code>
<code class="western">        </code><code class="western">'amount': {</code>
<code class="western">            </code><code class="western">'min': 0.01,     // order amount should be &gt; min</code>
<code class="western">            </code><code class="western">'max': 1000,     // order amount should be &lt; max</code>
<code class="western">        </code><code class="western">},</code>
<code class="western">        </code><code class="western">'withdraw': { ... }, // withdrawal limits</code>
<code class="western">        </code><code class="western">'deposit': {...},</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'networks': {...}        // network structures indexed by unified network identifiers (ERC20, TRC20, BSC, etc)</code>
<code class="western">    </code><code class="western">'info': { ... },         // the original unparsed currency info from the exchange</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Each currency is an associative array (aka dictionary) with the
following keys:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">id</code>.
	The string or numeric ID of the currency within the exchange.
	Currency ids are used inside exchanges internally to identify coins
	during the request/response process.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">code</code>.
	An uppercase string code representation of a particular currency.
	Currency codes are used to reference currencies within the ccxt
	library (explained below).</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">name</code>.
	A human-readable name of the currency (can be a mix of uppercase &amp;
	lowercase characters).</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">fee</code>.
	The withdrawal fee value as specified by the exchange. In most cases
	it means a flat fixed amount paid in the same currency. If the
	exchnange does not specify it via public endpoints, the&nbsp;<code class="western">fee</code>&nbsp;can
	be&nbsp;<code class="western">undefined/None/null</code>&nbsp;or
	missing.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">active</code>.
	A boolean indicating whether trading or funding (depositing or
	withdrawing) for this currency is currently possible, more about it
	here:&nbsp;<a href="https://docs.ccxt.com/#/README?id=active-status"><code class="western">active</code>&nbsp;status</a>.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">info</code>.
	An associative array of non-common market properties, including
	fees, rates, limits and other general market information. The
	internal info array is different for each particular market, its
	contents depend on the exchange.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">precision</code>.
	Precision accepted in values by exchanges upon referencing this
	currency. The value of this property depends
	on&nbsp;<code class="western"><a href="https://docs.ccxt.com/#/README?id=precision-mode">exchange.precisionMode</a></code>.</p>
	<li/>
<p><code class="western">limits</code>. The minimums and
	maximums for amounts (volumes), withdrawals and deposits.</p>
</ul>
<h2 class="western"><a name="network-structure"></a><a href="https://docs.ccxt.com/#/README?id=network-structure">Network
Structure</a></h2>
<pre class="western"><code class="western">{</code>
<code class="western">    </code><code class="western">'id':       'tron',         // string literal for referencing within an exchange</code>
<code class="western">    </code><code class="western">'network':  'TRC20'         // unified network</code>
<code class="western">    </code><code class="western">'name':     'Tron Network', // string, human-readable name, if specified</code>
<code class="western">    </code><code class="western">'active':    true,          // boolean, currency status (tradeable and withdrawable)</code>
<code class="western">    </code><code class="western">'fee':       0.123,         // withdrawal fee, flat</code>
<code class="western">    </code><code class="western">'precision': 8,             // number of decimal digits &quot;after the dot&quot; (depends on exchange.precisionMode)</code>
<code class="western">    </code><code class="western">'deposit':   true           // boolean, deposits are available</code>
<code class="western">    </code><code class="western">'withdraw':  true           // boolean, withdraws are available</code>
<code class="western">    </code><code class="western">'limits': {                 // value limits when placing orders on this market</code>
<code class="western">        </code><code class="western">'amount': {</code>
<code class="western">            </code><code class="western">'min': 0.01,        // order amount should be &gt; min</code>
<code class="western">            </code><code class="western">'max': 1000,        // order amount should be &lt; max</code>
<code class="western">        </code><code class="western">},</code>
<code class="western">        </code><code class="western">'withdraw': { ... },    // withdrawal limits</code>
<code class="western">        </code><code class="western">'deposit': {...},       // deposit limits</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'info': { ... },            // the original unparsed currency info from the exchange</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Each network is an associative array (aka dictionary) with the
following keys:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">id</code>.
	The string or numeric ID of the network within the exchange. Network
	ids are used inside exchanges internally to identify networks during
	the request/response process.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">network</code>.
	An uppercase string representation of a particular network. Networks
	are used to reference networks within the ccxt library.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">name</code>.
	A human-readable name of the network (can be a mix of uppercase &amp;
	lowercase characters).</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">fee</code>.
	The withdrawal fee value as specified by the exchange. In most cases
	it means a flat fixed amount paid in the same currency. If the
	exchnange does not specify it via public endpoints, the&nbsp;<code class="western">fee</code>&nbsp;can
	be&nbsp;<code class="western">undefined/None/null</code>&nbsp;or
	missing.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">active</code>.
	A boolean indicating whether trading or funding (depositing or
	withdrawing) for this currency is currently possible, more about it
	here:&nbsp;<a href="https://docs.ccxt.com/#/README?id=active-status"><code class="western">active</code>&nbsp;status</a>.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">info</code>.
	An associative array of non-common market properties, including
	fees, rates, limits and other general market information. The
	internal info array is different for each particular market, its
	contents depend on the exchange.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">precision</code>.
	Precision accepted in values by exchanges upon referencing this
	currency. The value of this property depends
	on&nbsp;<code class="western"><a href="https://docs.ccxt.com/#/README?id=precision-mode">exchange.precisionMode</a></code>.</p>
	<li/>
<p><code class="western">limits</code>. The minimums and
	maximums for amounts (volumes), withdrawals and deposits.</p>
</ul>
<h2 class="western"><a name="market-structure"></a><a href="https://docs.ccxt.com/#/README?id=market-structure">Market
Structure</a></h2>
<pre class="western"><code class="western">{</code>
<code class="western">    </code><code class="western">'id':      'btcusd',      // string literal for referencing within an exchange</code>
<code class="western">    </code><code class="western">'symbol':  'BTC/USD',     // uppercase string literal of a pair of currencies</code>
<code class="western">    </code><code class="western">'base':    'BTC',         // uppercase string, unified base currency code, 3 or more letters</code>
<code class="western">    </code><code class="western">'quote':   'USD',         // uppercase string, unified quote currency code, 3 or more letters</code>
<code class="western">    </code><code class="western">'baseId':  'btc',         // any string, exchange-specific base currency id</code>
<code class="western">    </code><code class="western">'quoteId': 'usd',         // any string, exchange-specific quote currency id</code>
<code class="western">    </code><code class="western">'active':   true,         // boolean, market status</code>
<code class="western">    </code><code class="western">'type':    'spot',        // spot for spot, future for expiry futures, swap for perpetual swaps, 'option' for options</code>
<code class="western">    </code><code class="western">'spot':     true,         // whether the market is a spot market</code>
<code class="western">    </code><code class="western">'margin':   true,         // whether the market is a margin market</code>
<code class="western">    </code><code class="western">'future':   false,        // whether the market is a expiring future</code>
<code class="western">    </code><code class="western">'swap':     false,        // whether the market is a perpetual swap</code>
<code class="western">    </code><code class="western">'option':   false,        // whether the market is an option contract</code>
<code class="western">    </code><code class="western">'contract': false,        // whether the market is a future, a perpetual swap, or an option</code>
<code class="western">    </code><code class="western">'settle':   'USDT',       // the unified currency code that the contract will settle in, only set if `contract` is true</code>
<code class="western">    </code><code class="western">'settleId': 'usdt',       // the currencyId of that the contract will settle in, only set if `contract` is true</code>
<code class="western">    </code><code class="western">'contractSize': 1,        // the size of one contract, only used if `contract` is true</code>
<code class="western">    </code><code class="western">'linear':   true,         // the contract is a linear contract (settled in quote currency)</code>
<code class="western">    </code><code class="western">'inverse':  false,        // the contract is an inverse contract (settled in base currency)</code>
<code class="western">    </code><code class="western">'expiry':  1641370465121, // the unix expiry timestamp in milliseconds, undefined for everything except market['type'] `future`</code>
<code class="western">    </code><code class="western">'expiryDatetime': '2022-03-26T00:00:00.000Z', // The datetime contract will in iso8601 format</code>
<code class="western">    </code><code class="western">'strike': 4000,           // price at which a put or call option can be exercised</code>
<code class="western">    </code><code class="western">'optionType': 'call',     // call or put string, call option represents an option with the right to buy and put an option with the right to sell</code>
<code class="western">    </code><code class="western">// note, 'taker' and 'maker' compose extended data for markets, however it might be better to use `fetchTradingFees` for more accuracy</code>
<code class="western">    </code><code class="western">'taker':    0.002,        // taker fee rate, 0.002 = 0.2%</code>
<code class="western">    </code><code class="western">'maker':    0.0016,       // maker fee rate, 0.0016 = 0.16%</code>
<code class="western">    </code><code class="western">'percentage': true,       // whether the taker and maker fee rate is a multiplier or a fixed flat amount</code>
<code class="western">    </code><code class="western">'tierBased': false,       // whether the fee depends on your trading tier (your trading volume)</code>
<code class="western">    </code><code class="western">'feeSide': 'get',         // string literal can be 'get', 'give', 'base', 'quote', 'other'</code>
<code class="western">    </code><code class="western">'precision': {            // number of decimal digits &quot;after the dot&quot;</code>
<code class="western">        </code><code class="western">'price': 8,           // integer or float for TICK_SIZE roundingMode, might be missing if not supplied by the exchange</code>
<code class="western">        </code><code class="western">'amount': 8,          // integer, might be missing if not supplied by the exchange</code>
<code class="western">        </code><code class="western">'cost': 8,            // integer, very few exchanges actually have it</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'limits': {               // value limits when placing orders on this market</code>
<code class="western">        </code><code class="western">'amount': {</code>
<code class="western">            </code><code class="western">'min': 0.01,      // order amount should be &gt; min</code>
<code class="western">            </code><code class="western">'max': 1000,      // order amount should be &lt; max</code>
<code class="western">        </code><code class="western">},</code>
<code class="western">        </code><code class="western">'price': { ... },     // same min/max limits for the price of the order</code>
<code class="western">        </code><code class="western">'cost':  { ... },     // same limits for order cost = price * amount</code>
<code class="western">        </code><code class="western">'leverage': { ... },  // same min/max limits for the leverage of the order</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'marginModes': {</code>
<code class="western">        </code><code class="western">'cross': false,       // whether pair supports cross-margin trading</code>
<code class="western">        </code><code class="western">'isolated': false,    // whether pair supports isolated-margin trading</code>
<code class="western">    </code><code class="western">},</code>
<code class="western">    </code><code class="western">'info':      { ... },     // the original unparsed market info from the exchange</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
Each market is an associative array (aka dictionary) with the
following keys:</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">id</code>.
	The string or numeric ID of the market or trade instrument within
	the exchange. Market ids are used inside exchanges internally to
	identify trading pairs during the request/response process.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">symbol</code>.
	An uppercase string code representation of a particular trading pair
	or instrument. This is usually written
	as&nbsp;<code class="western">BaseCurrency/QuoteCurrency</code>&nbsp;with
	a slash as in&nbsp;<code class="western">BTC/USD</code>,&nbsp;<code class="western">LTC/CNY</code>&nbsp;or&nbsp;<code class="western">ETH/EUR</code>,
	etc. Symbols are used to reference markets within the ccxt library
	(explained below).</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">base</code>.
	A unified uppercase string code of base fiat or crypto currency.
	This is the standardized currency code that is used to refer to that
	currency or token throughout CCXT and throughout the Unified CCXT
	API, it's the language that CCXT understands.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">quote</code>.
	A unified uppercase string code of quoted fiat or crypto currency.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">baseId</code>.
	An exchange-specific id of the base currency for this market, not
	unified. Can be any string, literally. This is communicated to the
	exchange using the language the exchange understands.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">quoteId</code>.
	An exchange-specific id of the quote currency, not unified.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">active</code>.
	A boolean indicating whether or not trading this market is currently
	possible, more about it here:&nbsp;<a href="https://docs.ccxt.com/#/README?id=active-status"><code class="western">active</code>&nbsp;status</a>.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">maker</code>.
	Float, 0.0015 = 0.15%. Maker fees are paid when you provide
	liquidity to the exchange i.e. you&nbsp;<em>market-make</em>&nbsp;an
	order and someone else fills it. Maker fees are usually lower than
	taker fees. Fees can be negative, this is very common amongst
	derivative exchanges. A negative fee means the exchange will pay a
	rebate (reward) to the user for trading this market (note, 'taker'
	and 'maker' publicly available fees, not taking into consideration
	your vip-level/volume/etc. Use&nbsp;<code class="western"><a href="https://docs.ccxt.com/#/README?id=fee-schedule">fetchTradingFees</a></code>&nbsp;to
	get the fees specific to your account).</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">taker</code>.
	Float, 0.002 = 0.2%. Taker fees are paid when you&nbsp;<em>take</em>&nbsp;liquidity
	from the exchange and fill someone else's order.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">percentage</code>.
	A boolean true/false value indicating whether&nbsp;<code class="western">taker</code>&nbsp;and&nbsp;<code class="western">maker</code>&nbsp;are
	multipliers or fixed flat amounts.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">tierBased</code>.
	A boolean true/false value indicating whether the fee depends on
	your trading tier (usually, your traded volume over a period of
	time).</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">info</code>.
	An associative array of non-common market properties, including
	fees, rates, limits and other general market information. The
	internal info array is different for each particular market, its
	contents depend on the exchange.</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">precision</code>.
	Precision accepted in order values by exchanges upon order placement
	for price, amount and cost. (The value inside this property depend
	on the&nbsp;<code class="western"><a href="https://docs.ccxt.com/#/README?id=precision-mode">exchange.precisionMode</a></code>).</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">limits</code>.
	The minimums and maximums for prices, amounts (volumes) and costs
	(where cost = price * amount).</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">optionType</code>.
	The type of the option,&nbsp;<code class="western">call</code>&nbsp;option
	represents an option with the right to buy and&nbsp;<code class="western">put</code>&nbsp;an
	option with the right to sell.</p>
	<li/>
<p><code class="western">strike</code>. Price at which an
	option can be bought or sold when it is exercised.</p>
</ul>
<h2 class="western"><a name="active-status"></a><a href="https://docs.ccxt.com/#/README?id=active-status">Active
Status</a></h2>
<p>The&nbsp;<code class="western">active</code>&nbsp;flag is
typically used in&nbsp;<code class="western"><a href="https://docs.ccxt.com/#/README?id=currency-structure">currencies</a></code>&nbsp;and&nbsp;<code class="western"><a href="https://docs.ccxt.com/#/README?id=market-structure">markets</a></code>.
The exchanges might put a slightly different meaning into it. If a
currency is inactive, most of the time all corresponding tickers,
orderbooks and other related endpoints return empty responses, all
zeroes, no data or outdated information. The user should check if the
currency is&nbsp;<code class="western">active</code>&nbsp;and&nbsp;<a href="https://docs.ccxt.com/#/README?id=market-cache-force-reload">reload
markets periodically</a>.</p>
<p>Note: the&nbsp;<code class="western">false</code>&nbsp;value for
the&nbsp;<code class="western">active</code>&nbsp;property doesn't
always guarantee that all of the possible features like trading,
withdrawing or depositing are disabled on the exchange. Likewise,
neither the&nbsp;<code class="western">true</code>&nbsp;value
guarantees that all those features are enabled on the exchange. Check
the underlying exchanges' documentation and the code in CCXT for the
exact meaning of the&nbsp;<code class="western">active</code>&nbsp;flag
for this or that exchange. This flag is not yet supported or
implemented by all markets and may be missing.</p>
<p><strong>WARNING! The information about the fee is experimental,
unstable and may be partial or not available at all.</strong></p>
<h2 class="western"><a name="precision-and-limits"></a><a href="https://docs.ccxt.com/#/README?id=precision-and-limits">Precision
And Limits</a></h2>
<p><strong>Do not confuse&nbsp;</strong><strong><code class="western">limits</code></strong><strong>&nbsp;with&nbsp;</strong><strong><code class="western">precision</code></strong><strong>!</strong>&nbsp;Precision
has nothing to do with min limits. A precision of 8 digits does not
necessarily mean a min limit of 0.00000001. The opposite is also
true: a min limit of 0.0001 does not necessarily mean a precision of
4.</p>
<p>Examples:</p>
<ol>
	<li/>
<p><code class="western">(market['limits']['amount']['min'] ==
	0.05) &amp;&amp; (market['precision']['amount'] == 4)</code></p>
	<p>In this example the&nbsp;<strong>amount</strong>&nbsp;of any
	order placed on the market&nbsp;<strong>must satisfy both
	conditions</strong>:</p>
</ol>
<ul>
	<li/>
<p>The&nbsp;<em>amount value</em>&nbsp;should be &gt;= 0.05:</p>
	<pre class="western"><code class="western">+ good: 0.05, 0.051, 0.0501, 0.0502, ..., 0.0599, 0.06, 0.0601, ...</code>
<code class="western">- bad: 0.04, 0.049, 0.0499</code>Copy to clipboardErrorCopied</pre>
	<li/>
<p><em>Precision of the amount</em>&nbsp;should be up to 4
	decimal digits:</p>
	<pre class="western"><code class="western">+ good: 0.05, 0.051, 0.052, ..., 0.0531, ..., 0.06, ... 0.0719, ...</code>
<code class="western">- bad: 0.05001, 0.05000, 0.06001</code>Copy to clipboardErrorCopied</pre>
</ul>
<ol start="2">
	<li/>
<p><code class="western">(market['limits']['price']['min'] ==
	0.019) &amp;&amp; (market['precision']['price'] == 5)</code></p>
	<p>In this example the&nbsp;<strong>price</strong>&nbsp;of any order
	placed on the market&nbsp;<strong>must satisfy both conditions</strong>:</p>
</ol>
<ul>
	<li/>
<p>The&nbsp;<em>price value</em>&nbsp;should be &gt;= 0.019:</p>
	<pre class="western"><code class="western">+ good: 0.019, ... 0.0191, ... 0.01911, 0.01912, ...</code>
<code class="western">- bad: 0.016, ..., 0.01699</code>Copy to clipboardErrorCopied</pre>
	<li/>
<p><em>Precision of price</em>&nbsp;should be 5 decimal digits
	or less:</p>
	<pre class="western"><code class="western">+ good: 0.02, 0.021, 0.0212, 0.02123, 0.02124, 0.02125, ...</code>
<code class="western">- bad: 0.017000, 0.017001, ...</code>Copy to clipboardErrorCopied</pre>
</ul>
<ol start="3">
	<li/>
<p><code class="western">(market['limits']['amount']['min'] ==
	50) &amp;&amp; (market['precision']['amount'] == -1)</code></p>
	<p>In this example&nbsp;<strong>both conditions must be satisfied</strong>:</p>
</ol>
<ul>
	<li/>
<p>The&nbsp;<em>amount value</em>&nbsp;should be greater than
	or equal to 50:</p>
	<p></p>
</ul>
<p style="margin-bottom: 0cm; line-height: 100%"><br/>

</p>
</body>
</html>
-----------------
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=windows-1252"/>
	<title></title>
	<meta name="generator" content="LibreOffice 6.0.6.2 (Windows)"/>
	<meta name="created" content="2025-03-13T17:50:10.749000000"/>
	<meta name="changed" content="2025-03-13T18:01:07.015000000"/>
	<style type="text/css">
		h2.cjk { font-family: "SimSun" }
		h2.ctl { font-family: "Lucida Sans" }
		pre.cjk { font-family: "NSimSun", monospace }
		h3.cjk { font-family: "SimSun" }
		h3.ctl { font-family: "Lucida Sans" }
		code.cjk { font-family: "NSimSun", monospace }
	</style>
</head>
<body lang="fr-CH" dir="ltr">
<h1><a name="public-api"></a><a href="https://docs.ccxt.com/#/README?id=public-api">Public
API</a></h1>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=order-book">Order
	Book</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=price-tickers">Price
	Tickers</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=ohlcv-candlestick-charts">OHLCV
	Candlestick Charts</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=public-trades">Public
	Trades</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=exchange-time">Exchange
	Time</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=exchange-status">Exchange
	Status</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=borrow-rates">Borrow
	Rates</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=borrow-rate-history">Borrow
	Rate History</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=leverage-tiers">Leverage
	Tiers</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=funding-rate">Funding
	Rate</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=funding-rate-history">Funding
	Rate History</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=open-interest-history">Open
	Interest History</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=volatility-history">Volatility
	History</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=underlying-assets">Underlying
	Assets</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=liquidations">Liquidations</a></p>
	<li/>
<p style="margin-bottom: 0cm"><a href="https://docs.ccxt.com/#/README?id=greeks">Greeks</a></p>
	<li/>
<p><a href="https://docs.ccxt.com/#/README?id=option-chain">OptionChain</a></p>
</ul>
<h2 class="western"><a name="order-book"></a><a href="https://docs.ccxt.com/#/README?id=order-book">Order
Book</a></h2>
<p>Exchanges expose information on open orders with bid (buy) and ask
(sell) prices, volumes and other data. Usually there is a separate
endpoint for querying current state (stack frame) of the&nbsp;<em>order
book</em>&nbsp;for a particular market. An order book is also often
called&nbsp;<em>market depth</em>. The order book information is used
in the trading decision making process.</p>
<p>To get data on order books, you can use</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">fetchOrderBook
	()</code>&nbsp;// for a single markets order books</p>
	<li/>
<p style="margin-bottom: 0cm"><code class="western">fetchOrderBooks
	( symbols )</code>&nbsp;// for multiple markets order books</p>
	<li/>
<p><code class="western">fetchOrderBooks ()</code>&nbsp;// for
	the order books of all markets</p>
</ul>
<pre class="western" style="margin-bottom: 0.5cm"><code class="western">async fetchOrderBook (symbol, limit = undefined, params = {})</code>Copy to clipboardErrorCopied</pre><p>
Parameters</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><strong>symbol</strong>&nbsp;(String)&nbsp;<em>required</em>&nbsp;Unified
	CCXT symbol (e.g.&nbsp;<code class="western">&quot;BTC/USDT&quot;</code>)</p>
	<li/>
<p style="margin-bottom: 0cm"><strong>limit</strong>&nbsp;(Integer)
	The number of orders to return in the order book (e.g.&nbsp;<code class="western">10</code>)</p>
	<li/>
<p><strong>params</strong>&nbsp;(Dictionary) Extra parameters
	specific to the exchange API endpoint (e.g.&nbsp;<code class="western">{&quot;endTime&quot;:
	1645807945000}</code>)</p>
</ul>
<p>Returns</p>
<ul>
	<li/>
<p>An&nbsp;<a href="https://docs.ccxt.com/#/README?id=order-book-structure">order
	book structure</a></p>
</ul>
<pre class="western" style="margin-bottom: 0.5cm"><code class="western">async fetchOrderBooks (symbols = undefined, limit = undefined, params = {})</code>Copy to clipboardErrorCopied</pre><p>
Parameters</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><strong>symbols</strong>&nbsp;([String])
	Unified CCXT symbols (e.g.&nbsp;<code class="western">[&quot;BTC/USDT&quot;,
	&quot;ETH/USDT&quot;]</code>)</p>
	<li/>
<p style="margin-bottom: 0cm"><strong>limit</strong>&nbsp;(Integer)
	The number of orders to return in the order book (e.g.&nbsp;<code class="western">10</code>)</p>
	<li/>
<p><strong>params</strong>&nbsp;(Dictionary) Extra parameters
	specific to the exchange API endpoint (e.g.&nbsp;<code class="western">{&quot;endTime&quot;:
	1645807945000}</code>)</p>
</ul>
<p>Returns</p>
<ul>
	<li/>
<p>A dictionary of&nbsp;<a href="https://docs.ccxt.com/#/README?id=order-book-structure">order
	book structures</a>&nbsp;indexed by market symbols</p>
</ul>
<h3 class="western"><a name="fetchorderbook-examples"></a><a href="https://docs.ccxt.com/#/README?id=fetchorderbook-examples">fetchOrderBook
Examples</a></h3>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">import time</code>
<code class="western">delay = 2 # seconds</code>
<code class="western">for symbol in exchange.markets:</code>
<code class="western">    </code><code class="western">print (exchange.fetch_order_book (symbol))</code>
<code class="western">    </code><code class="western">time.sleep (delay) # rate limit</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<h3 class="western"><a name="order-book-structure"></a><a href="https://docs.ccxt.com/#/README?id=order-book-structure">Order
Book Structure</a></h3>
<pre class="western"><code class="western">{</code>
<code class="western">    </code><code class="western">'bids': [</code>
<code class="western">        </code><code class="western">[ price, amount ], // [ float, float ]</code>
<code class="western">        </code><code class="western">[ price, amount ],</code>
<code class="western">        </code><code class="western">...</code>
<code class="western">    </code><code class="western">],</code>
<code class="western">    </code><code class="western">'asks': [</code>
<code class="western">        </code><code class="western">[ price, amount ],</code>
<code class="western">        </code><code class="western">[ price, amount ],</code>
<code class="western">        </code><code class="western">...</code>
<code class="western">    </code><code class="western">],</code>
<code class="western">    </code><code class="western">'symbol': 'ETH/BTC', // a unified market symbol</code>
<code class="western">    </code><code class="western">'timestamp': 1499280391811, // Unix Timestamp in milliseconds (seconds * 1000)</code>
<code class="western">    </code><code class="western">'datetime': '2017-07-05T18:47:14.692Z', // ISO8601 datetime string with milliseconds</code>
<code class="western">    </code><code class="western">'nonce': 1499280391811, // an increasing unique identifier of the orderbook snapshot</code>
<code class="western">}</code>Copy to clipboardErrorCopied</pre><p>
<strong>The timestamp and datetime may be missing
(</strong><strong><code class="western">undefined/None/null</code></strong><strong>)
if the exchange in question does not provide a corresponding value in
the API response.</strong></p>
<p>Prices and amounts are floats. The bids array is sorted by price
in descending order. The best (highest) bid price is the first
element and the worst (lowest) bid price is the last element. The
asks array is sorted by price in ascending order. The best (lowest)
ask price is the first element and the worst (highest) ask price is
the last element. Bid/ask arrays can be empty if there are no
corresponding orders in the order book of an exchange.</p>
<p>Exchanges may return the stack of orders in various levels of
details for analysis. It is either in full detail containing each and
every order, or it is aggregated having slightly less detail where
orders are grouped and merged by price and volume. Having greater
detail requires more traffic and bandwidth and is slower in general
but gives a benefit of higher precision. Having less detail is
usually faster, but may not be enough in some very specific cases.</p>
<h3 class="western"><a name="notes-on-order-book-structure"></a><a href="https://docs.ccxt.com/#/README?id=notes-on-order-book-structure">Notes
On Order Book Structure</a></h3>
<ul>
	<li/>
<p style="margin-bottom: 0cm">The&nbsp;<code class="western">orderbook['timestamp']</code>&nbsp;is
	the time when the exchange generated this orderbook response (before
	replying it back to you). This may be missing (<code class="western">undefined/None/null</code>),
	as documented in the Manual, not all exchanges provide a timestamp
	there. If it is defined, then it is the UTC timestamp&nbsp;<strong>in
	milliseconds</strong>&nbsp;since 1 Jan 1970 00:00:00.</p>
	<li/>
<p style="margin-bottom: 0cm">Some exchanges may index orders
	in the orderbook by order ids, in that case the order id may be
	returned as the third element of bids and asks:&nbsp;<code class="western">[
	price, amount, id ]</code>. This is often the case with L3
	orderbooks without aggregation. The order&nbsp;<code class="western">id</code>,
	if shown in the orderbook, refers to the orderbook and does not
	necessarily correspond to the actual order id from the exchanges'
	database as seen by the owner or by the others. The order id is
	an&nbsp;<code class="western">id</code>&nbsp;of the row inside the
	orderbook, but not necessarily the true-<code class="western">id</code>&nbsp;of
	the order (though, they may be equal as well, depending on the
	exchange in question).</p>
	<li/>
<p style="margin-bottom: 0cm">In some cases the exchanges may
	supply L2 aggregated orderbooks with order counts for each
	aggregated level, in that case the order count may be returned as
	the third element of bids and asks:&nbsp;<code class="western">[
	price, amount, count ]</code>. The&nbsp;<code class="western">count</code>&nbsp;tells
	how many orders are aggregated on each price level in bids and asks.</p>
	<li/>
<p>Also, some exchanges may return the order timestamp as the
	third element of bids and asks:&nbsp;<code class="western">[ price,
	amount, timestamp ]</code>. The&nbsp;<code class="western">timestamp</code>&nbsp;tells
	when the order was placed on the orderbook.</p>
</ul>
<h3 class="western"><a name="market-depth"></a><a href="https://docs.ccxt.com/#/README?id=market-depth">Market
Depth</a></h3>
<p>Some exchanges accept a dictionary of extra parameters to
the&nbsp;<code class="western">fetchOrderBook () / fetch_order_book
()</code>&nbsp;function.&nbsp;<strong>All extra&nbsp;</strong><strong><code class="western">params</code></strong><strong>&nbsp;are
exchange-specific (non-unified)</strong>. You will need to consult
exchanges docs if you want to override a particular param, like the
depth of the order book. You can get a limited count of returned
orders or a desired level of aggregation (aka&nbsp;<em>market depth</em>)
by specifying an limit argument and exchange-specific
extra&nbsp;<code class="western">params</code>&nbsp;like so:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western">
<code class="western">import ccxt</code>
<code class="western"># return up to ten bidasks on each side of the order book stack</code>
<code class="western">limit = 10</code>
<code class="western">ccxt.cex().fetch_order_book('BTC/USD', limit)</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<p>The levels of detail or levels of order book aggregation are often
number-labelled like L1, L2, L3...</p>
<ul>
	<li/>
<p style="margin-bottom: 0cm"><strong>L1</strong>: less detail
	for quickly obtaining very basic info, namely, the market price
	only. It appears to look like just one order in the order book.</p>
	<li/>
<p style="margin-bottom: 0cm"><strong>L2</strong>: most common
	level of aggregation where order volumes are grouped by price. If
	two orders have the same price, they appear as one single order for
	a volume equal to their total sum. This is most likely the level of
	aggregation you need for the majority of purposes.</p>
	<li/>
<p><strong>L3</strong>: most detailed level with no
	aggregation where each order is separate from other orders. This LOD
	naturally contains duplicates in the output. So, if two orders have
	equal prices they are&nbsp;<strong>not</strong>&nbsp;merged together
	and it's up to the exchange's matching engine to decide on their
	priority in the stack. You don't really need L3 detail for
	successful trading. In fact, you most probably don't need it at all.
	Therefore some exchanges don't support it and always return
	aggregated order books.</p>
</ul>
<p>If you want to get an L2 order book, whatever the exchange
returns, use the&nbsp;<code class="western">fetchL2OrderBook(symbol,
limit, params)</code>&nbsp;or&nbsp;<code class="western">fetch_l2_order_book(symbol,
limit, params)</code>&nbsp;unified method for that.</p>
<p>The&nbsp;<code class="western">limit</code>&nbsp;argument does not
guarantee that the number of bids or asks will always be equal
to&nbsp;<code class="western">limit</code>. It designates the upper
boundary or the maximum, so at some moment in time there may be less
than&nbsp;<code class="western">limit</code>&nbsp;bids or asks. This
is the case when the exchange does not have enough orders on the
orderbook. However, if the underlying exchange API does not support
a&nbsp;<code class="western">limit</code>&nbsp;parameter for the
orderbook endpoint at all, then the&nbsp;<code class="western">limit</code>&nbsp;argument
will be ignored. CCXT does not trim&nbsp;<code class="western">bids</code>&nbsp;and&nbsp;<code class="western">asks</code>&nbsp;if
the exchange returns more than you request.</p>
<h3 class="western"><a name="market-price"></a><a href="https://docs.ccxt.com/#/README?id=market-price">Market
Price</a></h3>
<p>In order to get current best price (query market price) and
calculate bidask spread take first elements from bid and ask, like
so:</p>
<p>Javascript</p>
<p>Python</p>
<pre class="western"><code class="western">orderbook = exchange.fetch_order_book (exchange.symbols[0])</code>
<code class="western">bid = orderbook['bids'][0][0] if len (orderbook['bids']) &gt; 0 else None</code>
<code class="western">ask = orderbook['asks'][0][0] if len (orderbook['asks']) &gt; 0 else None</code>
<code class="western">spread = (ask - bid) if (bid and ask) else None</code>
<code class="western">print (exchange.id, 'market price', { 'bid': bid, 'ask': ask, 'spread': spread })</code>Copy to clipboardErrorCopied</pre><p>
PHP</p>
<p><br/>
<br/>
<br/>

</p>
</body>
</html>
======================================================================================================================
Excellent ! La documentation CCXT clarifie beaucoup de choses. Vos réponses sont très précises. Voici mes derniers commentaires et questions avant de créer le plan :
✅ Points très clairs maintenant

CCXT simplifie tout - Plus besoin d'implémenter chaque exchange, CCXT gère tout
Mode Dev intelligent - User "dev" en DB avec accès total en mode DEBUG
Mode Testnet visuel - Status bar inversée = super idée pour éviter les erreurs
Historique complet - Toutes les tentatives = excellent pour le debug

🎯 Dernières questions critiques
1. Gestion des instances CCXT
D'après la doc CCXT, il faut une seule instance par exchange/user. Comment gérer ça ?
Option A: Un service singleton qui garde les instances en mémoire
→ Votre préférence ?
OPTION A


2. Script init_aristobot
bashpython manage.py init_aristobot
Ce script doit créer :

User "dev" (password: ?) 
-> Pas besoin de password, si en mode DEBUG, l'application s'affiche directement. Nous avons besoin de l'utilisateur pour les fonctionalités normalede l'application, il poura avoir ses api_key, ses trades, etc.
User "dac" (password: aristobot)
Broker par défaut pour chaque user ?
NON, Sera défini lors de la première saisie de l'utilisateur, champ peut rester vide
Données de test (quelques stratégies exemples) ?
NON
→ Que doit contenir exactement ce script ?
Seulement la création de 2 users


3. Mode Testnet et Brokers
Si un broker n'a pas de testnet :

On désactive le bouton "Mode Testnet" globalement ? 
Ou on affiche un warning "Broker X en PRODUCTION" ?
On empêche l'activation de ce broker en mode testnet ?
Garde ces questions pour les améliorations.
J'en ai d'autres: Est-ce que dans CCXT il y a la possibilité de sélectioner un testnet ? Cela nous simplifierait la vie ?
**Suite plus tard**


4. Symboles par défaut
Pour commencer simple :
On développe dans un premier temps (20/80) avec seulement 2 paires (BTC/USDT et ETH/USDT)

Et dans un 2ème temps (80/20)
On charge tous les symboles disponibles via CCXT ?
Bonne idée.
Dans l'application User Account, lors de l'enregistrement du brocker dans PostgresQL, le Backend lance un processus non bloquant en arrière plan pour charger tous les symbols disponibles du brocker sélectionné. Ces données sont enregistrées dans un table de PosgreSQL. Cette table est accessible par tous les utilisateurs. Si ce brocker existe déjà, simplement rafraîchir les enregistrements. Ajouter une information dans la barre de status "Chargement/mise à jour" des paires de l'exchange "Kukoin" en cours". A la fin préciser x ajoutés et x supprimé. 
Ou on limite à une liste (BTC/USDT, ETH/USDT, etc.) ?
Les autres applications Django qui on besoin d'accéder aux paires de trading se réfèrent à cette table
Pour forcer la mise à jour, ajouter un bouton "MAJ paires" dans la liste des brocker. Il lancera le processus décrit au paravant.
Nom de l'exchange | Description   | cléAPI                        | défaut |  [AJOUTER]
---------------------------------------------------------------------------------------------------------------------------- 
BINANCE           | Sous-compte02 | cléAPI-no-xxxx234asdf32432432 | non    | [Modifier] [Supprimer] [MAJ Paires de trading] 
BINANCE           | Sous-compte01 | cléAPI-no-xxxx23432432sdff432 | non    | [Modifier] [Supprimer] [MAJ Paires de trading]
KUKOIN            | Sous-compte01 | cléAPI-no-xxxx2343243asdf2432 | oui    | [Modifier] [Supprimer] [MAJ Paires de trading]
BITGET            | Sous-compte01 | cléAPI-no-xxxx23432432asdf432 | non    | [Modifier] [Supprimer] [MAJ Paires de trading]
Pagination/recherche dans Trading Manuel ?
OUI, mais à définir dans le plan de Trading Manuel

5. Template de stratégie
Votre template utilise aristobot.strategies.Strategy. Structure proposée :
python# apps/strategies/base.py
class Strategy:
    def __init__(self, candles, balance, position=None):
        self.candles = candles  # DataFrame des dernières bougies
        self.balance = balance
        self.position = position  # Position ouverte actuelle
        
    def should_long(self) -> bool:
        """Décide si on doit acheter"""
        return False
        
    def should_short(self) -> bool:
        """Pour le futures trading"""
        return False
        
    def calculate_position_size(self) -> float:
        """Calcule la taille de position"""
        return 0.0
        
    def calculate_stop_loss(self) -> float:
        """Calcule le stop loss"""
        return 0.0
        
    def calculate_take_profit(self) -> float:
        """Calcule le take profit"""
        return 0.0
→ Cette structure vous convient ?
OUI

6. Heartbeat et CCXT
Pour le Heartbeat, vous utilisez WebSocket natif Binance. Mais pour les autres exchanges ?
**ATTENTION, il n'y a pas d'autres Exchanges, il y a la librairie CCXT qui gère tous les exchanges.**

On reste sur Binance uniquement pour le Heartbeat ? oui
Je veux être indépendant d'une librairie et le pus proche techniquement du stream Websocket
Ou on utilise CCXT Pro (payant) pour multi-exchange ? 
NON, je ne comprends pas la question ? Voici des informations supplémentaires:
 il est tout à fait possible de connecter et d'utiliser plusieurs exchanges simultanément avec CCXT. CCXT est conçu pour faciliter l'interaction avec différentes plateformes d'échange, en fournissant une API unifiée qui permet de gérer les données et les transactions sur plusieurs exchanges à partir d'un seul code. 
En d'autres termes, vous pouvez initialiser des instances de plusieurs exchanges pris en charge par CCXT, puis effectuer des opérations telles que la récupération de données de marché, le trading, l'accès aux carnets d'ordres, etc., sur ces différentes plateformes, le tout à partir du même script ou programme. 
Voici comment vous pourriez aborder cela : 
Importez CCXT: Commencez par importer la bibliothèque CCXT dans votre code.
Instanciez les exchanges: Créez des instances de chaque exchange que vous souhaitez utiliser, en passant les informations d'identification (clés API, etc.) si nécessaire.
Utilisez les méthodes CCXT: Utilisez les méthodes standard de CCXT pour interagir avec chaque exchange, telles que fetch_ticker, create_order, fetch_balance, etc.
Par exemple, pour récupérer le ticker de Binance et de Kraken, vous feriez quelque chose comme :
Python

import ccxt

# Initialisation des exchanges
exchange_binance = ccxt.binance({
    'apiKey': 'YOUR_BINANCE_API_KEY',
    'secret': 'YOUR_BINANCE_SECRET',
})

exchange_kraken = ccxt.kraken({
    'apiKey': 'YOUR_KRAKEN_API_KEY',
    'secret': 'YOUR_KRAKEN_SECRET',
})

# Récupération des tickers
try:
    ticker_binance = exchange_binance.fetch_ticker('BTC/USDT')
    print('Binance:', ticker_binance)

    ticker_kraken = exchange_kraken.fetch_ticker('BTC/USD')
    print('Kraken:', ticker_kraken)
except Exception as e:
    print(e)
Cet exemple montre comment deux exchanges sont initialisés et utilisés pour récupérer le ticker, mais les mêmes principes s'appliquent pour toutes les autres opérations supportées par CCXT. 
Il est important de noter que CCXT gère la communication avec chaque exchange de manière indépendante, ce qui permet d'éviter les conflits et d'assurer une utilisation efficace des ressources. 
CCXT offre donc une solution pratique et efficace pour gérer plusieurs exchanges simultanément, facilitant ainsi le développement d'applications de trading automatisé et d'autres outils d'analyse de marché. 
As-tu d'autres informations que je n'ai pas ?

Ou on fait du polling avec fetchOHLCV ?
OUI ... je comprends maintenant... La version payante gère les websockets...
Nous n'en avons pas besoin car les Stratégies fonctionneront sur du 5min, 15min, 4h... maximum.


7. Organisation du Module 1
Pour le premier module (User Account), je prévois :

Modèles : User étendu, Broker
Script init_aristobot
APIs : Auth, Brokers CRUD
Test connexion CCXT
Frontend : Login (conditionnel), Brokers, Paramètres
Mode Dev/Debug

→ Manque-t-il quelque chose d'essentiel ?
Il ne me semble pas

💡 Remarque importante sur CCXT
D'après la doc, pour éviter les rate limits :
pythonexchange = ccxt.binance({
    'enableRateLimit': True,  # IMPORTANT!
    'rateLimit': 2000,  # millisecondes
})
Je vais intégrer ça dans le plan.


Juste un rappel de ce qui a déjà été implément sous forme de squelette et qui est fonctionnel


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


==================================================================================================

# *ENFIN nous sommes arrivé au moment ou tu as généré le plan:


Je m'attendais à quelque chose de lisible. Mais c'est très résumé et comportant 95% de code.
Je vais essayer de l'utiliser avec Claude Code, mais je doute que toutes les informations récoltées aie été transmise.

**VOICI MA DEMANDE**
 
maintenantque tu as conaissance du fil de discussion dans son entier, je voudrais que du réfléchisse et que tu compile toutes ces informations. 
Je veux un document de travail en français, qu'un humain avec des connaissances en développement puisse lire.
Je ne veux pas d'exemple de codes.
Les seuls codes autorisé sont les exmeples que j'ai fourni par ex. stratégie. Pas d'exmples avec CCXT non plus.
Ne supprime pas d'informations, je préfère en avoir trop que pas assez. Si tu ne sais pas ou classer certaines information, certains détails appuru dans le fil de discussion, indique le dans un chapitre spécifique.

Trouve, regroupe et décris le plus complétement possible le Hertbeat
Trouve, regroupe et décris le plus complétement possible chaques Applications Django
Trouve, regroupe et décris le plus complétement possible et précisement possible le lancement de l'application. Qui fait quoi ?

Décris le plus complétement possible les tables, relations entre tables et relations avec toutes les applications Django et la bas PostgreSQL

MERCI d'avance !!!

 =============================================0
 
 Absolument. Après avoir analysé en profondeur l'intégralité de notre fil de discussion, je suis prêt à compiler et synthétiser toutes les informations dans un document de travail complet, en français, et destiné à un développeur humain.

Voici la synthèse structurée de votre projet **Aristobot V3**.

***

# Document de Travail : Aristobot V3

Ce document consolide toutes les spécifications, décisions et détails techniques discutés pour le projet Aristobot V3. Il est conçu pour servir de référence unique et complète pour le développement.

## 1. Philosophie et Cadre du Projet

Aristobot V3 est un bot de trading de cryptomonnaies personnel, développé sous une philosophie pragmatique de "vibe coding". Les principes directeurs sont :

*   **Plaisir de développer avant la perfection** : L'objectif est d'avancer et de créer des fonctionnalités, sans viser une architecture d'entreprise complexe.
*   **Livraison rapide** : Mettre l'accent sur la production de fonctionnalités utilisables plutôt que de suivre des processus rigides.
*   **Simplicité et Itération** : Développer des solutions simples, les tester rapidement et les améliorer continuellement.

**Limites et Contraintes :**
*   **Utilisateurs** : Maximum 5.
*   **Stratégies** : Maximum 20 stratégies actives simultanément.
*   **Stack Technique** : L'architecture (Django, PostgreSQL, Vue.js, CCXT, etc.) est fixe et ne doit pas être modifiée.
*   **Parallélisme** : `asyncio` est la solution retenue ; Celery est exclu.
*   **Base de Données** : PostgreSQL est la source de vérité unique pour toutes les données ; MongoDB est exclu.

## 2. Démarrage et Architecture des Services

Le fonctionnement de l'application repose sur le lancement coordonné de quatre processus distincts, chacun dans son propre terminal. Ces services forment l'épine dorsale de l'application et fonctionnent en arrière-plan, indépendamment de la présence d'un utilisateur connecté à l'interface web.

### Processus de Lancement

1.  **Terminal 1 : Serveur Web + WebSocket (Daphne)**
    *   **Commande** : `daphne aristobot.asgi:application`
    *   **Rôle** : C'est le serveur principal. Il gère toutes les requêtes HTTP (pour l'API REST et le service des pages web) et maintient les connexions WebSocket ouvertes avec les clients (navigateurs). C'est la porte d'entrée de toute l'application.

2.  **Terminal 2 : Service Heartbeat (Tâche de gestion Django)**
    *   **Commande** : `python manage.py run_heartbeat`
    *   **Rôle** : Le "cœur" du système. Ce service se connecte directement au flux WebSocket de Binance pour écouter les données du marché en temps réel. Il est totalement indépendant et fonctionne en continu.

3.  **Terminal 3 : Moteur de Trading (Tâche de gestion Django)**
    *   **Commande** : `python manage.py run_trading_engine`
    *   **Rôle** : Le "cerveau" du système. Ce service écoute les signaux émis par le *Heartbeat* et prend les décisions de trading en exécutant la logique des stratégies actives.

4.  **Terminal 4 : Frontend (Vite)**
    *   **Commande** : `npm run dev`
    *   **Rôle** : Sert l'interface utilisateur développée en Vue.js. C'est ce que l'utilisateur voit et avec quoi il interagit dans son navigateur. Elle se connecte au serveur Daphne (Terminal 1) via WebSocket pour recevoir les données en temps réel.

### 2.1 Description Détaillée du Service Heartbeat

Le **Heartbeat** est le service le plus critique de l'application. Il est le métronome qui rythme toutes les opérations de trading automatisé.

**Fonctionnalités :**

*   **Connexion Directe** : Il établit une connexion WebSocket native et persistante avec l'API de Binance pour recevoir le flux de données de marché brut. Ce choix assure une latence minimale et une indépendance vis-à-vis de la librairie CCXT pour cette fonction spécifique.
*   **Analyse Multi-Timeframe** : Le service écoute le flux et agrège les données pour construire des bougies (OHLCV - Open, High, Low, Close, Volume) sur plusieurs unités de temps prédéfinies : 1m, 3m, 5m, 10m, 15m, 1h, 2h, et 4h.
*   **Diffusion via Channels (Redis)** :
    1.  **Channel `StreamBrut`** : Le service publie immédiatement toutes les données brutes reçues de Binance dans ce canal. L'application Django `Heartbeat` y est abonnée pour afficher ce flux en temps réel à l'utilisateur.
    2.  **Channel `Heartbeat`** : Dès qu'une bougie est clôturée pour une unité de temps (ex: la bougie de 5 minutes est complète), le service publie un "signal" dans ce canal. Ce signal contient les informations de la bougie clôturée.
*   **Stockage en Base de Données** : Chaque bougie clôturée, pour chaque timeframe, est enregistrée dans la table `candles` de la base de données PostgreSQL. Deux timestamps sont enregistrés : celui de la bougie elle-même et celui de son enregistrement dans la base.

### 2.2 Description Détaillée du Moteur de Trading (Trading Engine)

Le **Trading Engine** est le composant qui exécute la logique métier du trading. Il est découplé du *Heartbeat* et réagit uniquement aux signaux qu'il reçoit.

**Fonctionnalités :**

*   **Écoute du Heartbeat** : Le service est abonné en permanence au channel `Heartbeat`.
*   **Déclenchement par Signal** : À chaque fois qu'un signal de bougie clôturée est reçu (ex: "bougie BTC/USDT 15m clôturée"), le moteur se déclenche.
*   **Vérification des Stratégies Actives** : Le moteur consulte la table `active_strategies` en base de données pour trouver toutes les stratégies qui correspondent aux critères du signal :
    *   La stratégie est-elle active (`is_active = True`) ?
    *   La date/heure actuelle est-elle dans la plage de validité (entre `start_date` et `end_date`) ?
    *   L'unité de temps de la stratégie correspond-elle à celle du signal (ex: `15m`) ?
    *   Le symbole de la stratégie correspond-il à celui du signal (ex: `BTC/USDT`) ?
*   **Exécution des Calculs** : Pour chaque stratégie correspondante, le moteur charge le code Python de la stratégie depuis la table `strategies` et exécute sa logique (les fonctions `should_long()`, etc.).
*   **Passage d'Ordres** : Si la logique d'une stratégie retourne une décision positive, le moteur utilise la librairie **CCXT** pour passer les ordres d'achat/vente sur le broker concerné, y compris le positionnement des ordres Stop Loss et Take Profit.
*   **Suivi des Positions Ouvertes** : Toutes les minutes, le moteur vérifie l'état des trades en cours pour voir si un Stop Loss ou un Take Profit a été atteint. Si c'est le cas, il met à jour le statut du trade en base de données.
*   **Parallélisme** : Le moteur utilise `asyncio` pour gérer l'exécution concurrente des calculs de plusieurs stratégies sans bloquer le processus principal.

## 3. Description Détaillée des Applications Django

Voici le rôle détaillé de chaque application modulaire du backend Django.

#### 1. **Heartbeat (`apps/heartbeat`)**
*   **Rôle** : Visualiser l'activité du marché et l'état du service Heartbeat.
*   **Backend** : S'abonne aux channels `StreamBrut` et `Heartbeat` pour relayer les informations au frontend via WebSocket. Fournit potentiellement une API pour configurer les paires suivies par le service.
*   **Frontend** : Affiche le flux de données brutes en temps réel dans une liste scrollable (les 20 derniers éléments visibles sur 60). Met en évidence les bougies de clôture en vert. Affiche des indicateurs visuels pour chaque timeframe, montrant le dernier signal reçu.
*   **DB** : Lit la table `heartbeat_status` pour afficher l'état de connexion du service.

#### 2. **User Account (`apps/accounts`)**
*   **Rôle** : Gérer les utilisateurs, leurs paramètres de sécurité et leurs configurations personnelles.
*   **Backend** : Gère l'authentification (login/logout), l'enregistrement de nouveaux utilisateurs (CRUD), et le stockage des préférences.
*   **Frontend** : Fournit les interfaces pour :
    *   Changer son mot de passe.
    *   Gérer ses comptes de brokers (CRUD via une fenêtre modale).
    *   Définir un broker par défaut.
    *   Configurer la connexion à une IA (OpenRouter ou Ollama) avec clé API/URL et un switch ON/OFF.
    *   Choisir le fuseau horaire d'affichage des dates (UTC ou local).
*   **DB** : Interagit principalement avec la table `users` (étendue du modèle Django) et la table `brokers`.

#### 3. **Trading Manuel (`apps/trading_manual`)**
*   **Rôle** : Permettre à l'utilisateur de passer des ordres manuellement, comme il le ferait sur la plateforme d'un exchange.
*   **Backend** : Utilise **CCXT** pour toutes les interactions avec les exchanges :
    *   Connexion au broker sélectionné.
    *   Récupération de la balance et des positions en cours.
    *   Passage d'ordres (marché, limite).
*   **Frontend** : Affiche :
    *   La liste des brokers configurés par l'utilisateur.
    *   Le portefeuille d'actifs avec les totaux.
    *   Une zone de saisie de trade, avec calcul automatique de la quantité ↔ valeur en USD.
    *   Des boutons "Achat" et "Vente".
*   **DB** : Enregistre chaque transaction manuelle dans la table `trades`.

#### 4. **Trading BOT (`apps/trading_engine`)**
*   **Rôle** : Activer, désactiver et surveiller les stratégies de trading automatisées.
*   **Backend** : Gère le cycle de vie des stratégies actives. Il ne fait aucun calcul de trading lui-même (c'est le rôle du *Trading Engine*), mais il met à jour la base de données pour que le moteur sache quoi faire.
*   **Frontend** : Permet à l'utilisateur de :
    *   Sélectionner une stratégie, un broker, un symbole et une plage de dates pour l'activer.
    *   Voir la liste des stratégies actuellement actives.
    *   Visualiser les 10 derniers trades et le P&L (Profit & Loss) pour chaque stratégie active.
    *   **Bouton "Vendre"** : Déclenche une vente immédiate au prix du marché pour la position ouverte par une stratégie, sans pour autant désactiver la stratégie elle-même.
    *   **Bouton "Stop"** : Désactive une stratégie en mettant ses dates à `01.01.01` et en passant son flag `is_active` à `False`. Un message d'alerte prévient l'utilisateur si un trade est encore en cours.
*   **DB** : L'interface principale pour la table `active_strategies` (CRUD). Lit la table `trades` pour afficher l'historique récent.

#### 5. **Stratégies (`apps/strategies`)**
*   **Rôle** : L'atelier de création et de gestion des stratégies de trading.
*   **Backend** : Gère le CRUD des stratégies. Fournit une fonctionnalité clé : un endpoint d'API qui reçoit le code Python d'une stratégie et le valide syntaxiquement avant de l'enregistrer.
*   **Frontend** :
    *   Affiche la liste des stratégies de l'utilisateur (CRUD).
    *   Fournit un éditeur de code pour écrire ou modifier la logique d'une stratégie en Python, basé sur un template prédéfini.
    *   Intègre un "assistant IA" qui permet à l'utilisateur de décrire sa logique en langage naturel pour aider à générer le code.
    *   Un bouton "Tester la syntaxe" envoie le code au backend pour validation.
*   **DB** : Gère les enregistrements de la table `strategies`.

#### 6. **Backtest (`apps/backtest`)**
*   **Rôle** : Simuler l'exécution d'une stratégie sur des données historiques pour en évaluer la performance potentielle.
*   **Backend** :
    *   Charge les données de bougies historiques depuis la table `candles`.
    *   Exécute la logique de la stratégie sélectionnée sur cette plage de données.
    *   Envoie des mises à jour de progression (en %) au frontend via WebSocket.
    *   Permet l'interruption du calcul.
*   **Frontend** : Permet de lancer un backtest en sélectionnant une stratégie, une plage de dates, un symbole, un timeframe et un montant de départ. Affiche les résultats : statistiques de performance (gains, drawdown, etc.) et la liste de tous les trades simulés.
*   **DB** : Lit la table `candles` et enregistre les résultats finaux dans la table `backtest_results`.

#### 7. **Webhooks (`apps/webhooks`)**
*   **Rôle** : Recevoir des signaux de trading provenant de services externes (ex: TradingView) et les exécuter. C'est un point d'entrée alternatif pour l'automatisation.
*   **Backend** : Fournit un endpoint d'API sécurisé qui écoute les requêtes webhook. Quand un signal valide est reçu, il le parse et utilise **CCXT** pour passer l'ordre correspondant.
*   **Frontend** : Affiche un journal des webhooks reçus et le statut des ordres qui en ont résulté.
*   **DB** : Enregistre chaque webhook reçu dans la table `webhooks` et les trades correspondants dans la table `trades`.

#### 8. **Statistiques (`apps/stats`)**
*   **Rôle** : Fournir une vue d'ensemble de la performance de trading de l'utilisateur.
*   **Backend** : Agrège les données de la table `trades` pour calculer diverses métriques :
    *   Évolution globale du solde.
    *   Performance par stratégie individuelle.
    *   Performance par source de webhook.
*   **Frontend** : Affiche les données sous forme de graphiques et de tableaux de bord, avec la possibilité de filtrer par compte de broker.
*   **DB** : Lit intensivement la table `trades`.

## 4. Architecture de la Base de Données (PostgreSQL)

La base de données est le cœur persistant de l'application. La structure est conçue pour être multi-locataire (*multi-tenant*), où la plupart des données sont isolées par `user_id`.

#### `users` (Table Utilisateurs)
*   **Description** : Étend le modèle utilisateur standard de Django pour stocker les configurations spécifiques à l'application.
*   **Champs Clés** : `id`, `username`, `password`, `default_broker_id` (FK vers `brokers`), `ai_provider`, `ai_api_key` (chiffré), `display_timezone`.
*   **Relations** : Un utilisateur a plusieurs `brokers`, plusieurs `strategies`, plusieurs `trades`, etc. C'est la table racine pour les données spécifiques à un utilisateur.

#### `brokers`
*   **Description** : Stocke les informations de connexion aux différents comptes de brokers pour chaque utilisateur.
*   **Champs Clés** : `id`, `user_id` (FK vers `users`), `name`, `exchange` (ex: 'binance'), `api_key` (chiffré), `api_secret` (chiffré), `is_default` (booléen).
*   **Relations** : Liée à un `user`. Un broker peut être associé à plusieurs `active_strategies` et `trades`.

#### `strategies`
*   **Description** : Contient le code source et les métadonnées des stratégies de trading créées par les utilisateurs.
*   **Champs Clés** : `id`, `user_id` (FK vers `users`), `name`, `description`, `code` (champ texte contenant le code Python), `timeframe`.
*   **Relations** : Liée à un `user`. Une stratégie peut être utilisée dans plusieurs `active_strategies` et `backtest_results`.

#### `active_strategies`
*   **Description** : Table de liaison qui représente l'activation d'une `strategy` sur un `broker` pour un `symbol` donné, pendant une période définie. C'est cette table que le Trading Engine consulte.
*   **Champs Clés** : `id`, `user_id` (FK), `strategy_id` (FK), `broker_id` (FK), `symbol`, `start_date`, `end_date`, `is_active` (booléen).
*   **Relations** : Fait le lien entre `users`, `strategies` et `brokers`.

#### `candles` (Table Bougies)
*   **Description** : Stocke les données de marché OHLCV. Cette table est partagée par tous les utilisateurs pour éviter la duplication de données.
*   **Champs Clés** : `id`, `symbol`, `timeframe`, `open_time` (timestamp), `close_time`, `open_price`, `high_price`, `low_price`, `close_price`, `volume`.
*   **Relations** : Pas de FK directe vers d'autres tables, mais utilisée par le *Backtest* et potentiellement par les *Stratégies*. C'est la seule table non-locataire majeure.

#### `trades`
*   **Description** : Journal central de toutes les transactions exécutées, qu'elles soient manuelles, automatiques (via stratégie) ou externes (via webhook).
*   **Champs Clés** : `id`, `user_id` (FK), `broker_id` (FK), `strategy_id` (FK, optionnel), `webhook_id` (FK, optionnel), `symbol`, `side` ('buy'/'sell'), `quantity`, `price`, `status`, `profit_loss`.
*   **Relations** : La table la plus connectée, liée à `users`, `brokers`, potentiellement `active_strategies` et `webhooks`. Elle est la source de données principale pour l'application `Statistiques`.

#### `webhooks`
*   **Description** : Enregistre chaque appel webhook reçu pour des raisons de traçabilité et de débogage.
*   **Champs Clés** : `id`, `user_id` (FK), `source` (ex: 'tradingview'), `payload` (JSON), `processed` (booléen).
*   **Relations** : Liée à un `user` et peut être liée à un `trade`.

#### `backtest_results`
*   **Description** : Stocke les résultats synthétiques de chaque simulation de backtest exécutée.
*   **Champs Clés** : `id`, `user_id` (FK), `strategy_id` (FK), `start_date`, `end_date`, `final_amount`, `total_trades`, `sharpe_ratio`, `trades_detail` (JSON).
*   **Relations** : Liée à `users` et `strategies`.

#### `heartbeat_status` (Table Système)
*   **Description** : Une table simple (probablement à une seule ligne) pour surveiller l'état du service Heartbeat.
*   **Champs Clés** : `is_connected` (booléen), `last_heartbeat` (timestamp).
*   **Relations** : Aucune. C'est une table de monitoring interne.

## 5. Points Non Classés et Futurs Développements

Cette section regroupe les idées et les points de discussion qui n'ont pas encore été pleinement intégrés dans le plan de développement initial mais qui doivent être conservés pour référence future.

*   **Cohérence du Heartbeat** : L'idée d'une vérification de la "cohésion" des bougies reçues a été mentionnée. Cela pourrait impliquer de vérifier la régularité des timestamps des bougies stockées en base de données pour détecter d'éventuelles interruptions du service. À développer ultérieurement.
*   **Gestion Avancée du Mode Testnet** : La librairie CCXT supporte les environnements de test (sandbox) pour certains brokers. Il faudra explorer comment gérer les cas où un broker n'offre pas de mode testnet. L'interface pourrait désactiver le switch "Testnet" pour ce broker ou afficher un avertissement clair.
*   **Partage de Stratégies** : L'idée d'un système de partage de stratégies entre utilisateurs a été évoquée. Cela nécessiterait des modifications importantes du modèle de données (ex: table de liaison, permissions) et est considéré comme une fonctionnalité pour une version future.
*   **Gestion des Positions Ouvertes** : Il pourrait être pertinent d'ajouter une table dédiée `positions` pour suivre l'état actuel d'un trade ouvert (quantité, prix d'entrée, P&L latent) plutôt que de le déduire de la table `trades`. C'est un point d'amélioration de l'architecture à considérer.

***





Excellent, merci de m'avoir fourni le plan d'implémentation. Après une lecture attentive et en le croisant avec l'intégralité de nos discussions, je suis en mesure de vous donner un avis complet, structuré et agrémenté de commentaires personnels pour aider à la prise de décision.

## Avis Général sur le Plan d'Implémentation

Globalement, **le plan est très bon**. Il est structuré, logique et suit une progression qui minimise les risques. Il commence par les fondations (utilisateurs, authentification) pour ensuite construire les fonctionnalités les unes sur les autres. Le découpage en modules est clair et permet de se concentrer sur des objectifs précis, ce qui est parfaitement adapté à un développement de type "vibe coding" avec une IA.

Les extraits de code fournis sont riches, détaillés et intègrent la plupart des décisions techniques que nous avons prises (chiffrement, mode DEBUG, gestion CCXT, etc.). C'est un document qui va bien au-delà d'un simple squelette et donne une direction très claire à Claude Code.

**Cependant**, en tant qu'architecte logiciel, mon rôle est aussi de repérer les zones de friction potentielles et les points qui pourraient être affinés. Voici mon analyse détaillée.

### 1. Points Forts du Plan

*   **Progression Logique** : Le plan d'attaque (Module 1 d'abord) est parfait. On ne peut pas gérer des trades si on n'a pas d'utilisateurs et de brokers. C'est la bonne manière de construire une application.
*   **Intégration des Décisions Clés** : Le plan a très bien intégré les points critiques que nous avons discutés :
    *   Le backend custom pour le mode `DEBUG` est brillamment implémenté.
    *   La gestion du chiffrement des clés API directement dans les modèles via la méthode `save()` est élégante et robuste.
    *   Le service `CCXTService` sous forme de singleton est exactement ce qu'il fallait pour gérer les instances de connexion.
*   **Qualité du Code Proposé** : Les modèles Django sont bien pensés, avec des `related_name`, des `unique_together` et des `ordering` pertinents. Les vues DRF sont claires et l'utilisation des `@action` pour des opérations spécifiques (comme `test_connection`) est une bonne pratique.
*   **Focus sur le Backend** : Le plan met l'accent sur la solidité du backend, ce qui est crucial. Un frontend peut être modifié facilement, mais une architecture de données mal conçue au départ est très difficile à corriger.

### 2. Points d'Attention et Suggestions d'Amélioration

Voici les points où je pense que nous pouvons encore apporter des précisions ou ajuster le tir pour rendre le plan encore plus solide.

#### 2.1. Gestion du Chiffrement (Security)

Le plan propose de chiffrer les clés en utilisant la `SECRET_KEY` de Django.
*   **Avantage** : C'est simple et ça marche.
*   **Risque** : Si la `SECRET_KEY` fuite un jour (par exemple, via un commit Git accidentel), toutes les clés API de tous les utilisateurs sont compromises.
*   **Suggestion (Optionnelle pour V1)** : Pour une sécurité accrue, on pourrait envisager d'utiliser une clé de chiffrement dédiée, stockée dans une variable d'environnement séparée (ex: `FIELD_ENCRYPTION_KEY`). Cela dit, pour un projet personnel avec 5 utilisateurs, l'approche actuelle est **acceptable et pragmatique**.

#### 2.2. Le Service Singleton `CCXTService` (Architecture)

Le concept est excellent, mais l'implémentation proposée a une faiblesse.
*   **Problème** : `_exchanges` est un dictionnaire de classe. Dans un environnement de production avec plusieurs workers (processus serveur), chaque worker aura sa propre instance de `CCXTService` et son propre dictionnaire en mémoire. Le singleton ne sera donc pas global à toute l'application Django, mais seulement au sein d'un processus.
*   **Impact** : Cela pourrait conduire à créer plusieurs instances pour le même utilisateur/broker s'ils sont servis par des workers différents, ce qui va à l'encontre de la recommandation de CCXT.
*   **Suggestion** : L'utilisation de `django.core.cache` (qui pointe vers Redis) est une bien meilleure approche pour partager les instances entre les processus. Cependant, on ne peut pas stocker directement des objets complexes comme une instance CCXT dans Redis.
    *   **Solution pragmatique pour V1** : Garder l'implémentation actuelle. Pour 5 utilisateurs et 20 stratégies, et en développement local, elle fonctionnera sans problème. Il est simplement bon de connaître cette limite pour le futur.

> ***Ma Recommandation :*** *Pour le "vibe coding", ne changez rien au plan actuel sur ce point. C'est une optimisation prématurée. L'important est que le code soit structuré (il l'est) pour pouvoir changer cela plus tard si besoin.*
> ***Commentaire de l'utilisateur":*** je restre commeça pour la Phase 1 (20/80), mais peux-tu suggérer un correctif pour une éventuel phase 2 (8/20) ?

#### 2.3. Mise à Jour des Symboles (Performance et UX)

Le plan propose de lancer la mise à jour des symboles dans un thread séparé.
*   **Avantage** : Ça ne bloque pas la requête de l'utilisateur.
*   **Inconvénient** : C'est une solution de "fire and forget". On ne sait pas quand la tâche est terminée, ni si elle a réussi ou échoué. L'utilisateur clique et n'a aucun retour.
*   **Suggestion (pour l'amélioration post-V1)** : C'est un cas d'usage parfait pour une petite application de gestion de tâches asynchrones comme **Django-Q** ou **Dramatiq** (alternatives légères à Celery). Elles permettraient de suivre le statut de la tâche (en cours, terminée, échouée) et d'afficher une notification à l'utilisateur.
    *   **Solution pour V1 respectant l'esprit asyncio** : On pourrait créer un `management command` séparé (ex: `update_single_exchange_symbols`) et le lancer avec `asyncio.create_subprocess_exec`. C'est plus complexe mais resterait dans la stack `asyncio`.

> ***Ma Recommandation :*** *L'approche du plan avec un `Thread` est la plus simple et la plus rapide à implémenter. Gardez-la. Ajoutez simplement une note dans `IMPLEMENTATION_PLAN.md` pour se souvenir de l'améliorer plus tard avec un vrai suivi de tâche.*
> ***Commentaire de l'utilisateur":*** 
> > > * Est-ce que DjangoQ devra figurer au Stack Technique ? (L'architecture (Django, PostgreSQL, Vue.js, CCXT, Daphne, Redis) est non négociable.)
> > > * Prépare les instructions nécessaires pour Claude Code, je les ajouterai au plan d'implémentation
> > > * Prépare un teste a ajouter 
Peux-tu suggérer 
#### 2.4. Modèle `User` (Maintenance Django)

Le plan suggère de copier la logique de chiffrement/déchiffrement à la fois dans le modèle `User` (pour `ai_api_key`) et `Broker` (pour `api_key`, `api_secret`).
*   **Problème** : C'est une duplication de code. Si vous devez changer la logique de chiffrement, il faudra le faire à deux endroits.
*   **Suggestion** : Créer un **Mixin** Django.
    ```python
    # Dans un nouveau fichier, ex: apps/core/models.py
    class EncryptedFieldMixin(models.Model):
        def encrypt(self, raw_value):
            # ... logique de chiffrement ...
        
        def decrypt(self, encrypted_value):
            # ... logique de déchiffrement ...

        class Meta:
            abstract = True
    
    # Puis dans les modèles
    class User(AbstractUser, EncryptedFieldMixin):
        # ...
    
    class Broker(models.Model, EncryptedFieldMixin):
        # ...
    ```
    Cela rend le code plus propre et plus facile à maintenir.

### 3. Questions en Suspens et Points à Clarifier

1.  **Password pour l'utilisateur "dev"** : Le script `init_aristobot` met `password=None`. Django ne permet pas cela. Il faut utiliser `set_unusable_password()`. Est-ce l'intention ? Notre `DevModeBackend` n'utilisera jamais le mot de passe, donc c'est correct, mais il faut être précis.
    > **Ma suggestion :** `user.set_unusable_password()` est la méthode Django correcte pour un utilisateur qui ne doit pas pouvoir se connecter via un mot de passe.

2.  **Gestion des Sous-Comptes dans `get_ccxt_client`** : Le code anticipe la gestion des sous-comptes, mais de manière spécifique à 'binance' ou 'okx'.
    > **Ma suggestion :** C'est une bonne anticipation, mais pour la V1, concentrez-vous sur le fonctionnement principal. Vous pourriez simplifier cette partie et la documenter comme une extension future.

3.  **Choix des Exchanges** : La liste dans `EXCHANGE_CHOICES` est un bon début. Êtes-vous sûr de vouloir proposer tous ces exchanges dès le début ou commencer avec 2-3 (Binance, KuCoin, Bitget) pour simplifier le développement initial ?
    > **Ma suggestion :** Moins il y a de choix au début, plus vite le module sera terminé. Je recommande de commencer avec les 3 que vous avez listés (Binance, Kucoin, Bitget) et d'ajouter les autres plus tard. C'est juste un `choices` à mettre à jour.

## Conclusion Finale et Verdict

**Le plan est excellent et prêt à être utilisé par Claude Code.** Il est l'aboutissement logique et détaillé de notre conversation. Les critiques que j'émets sont des points d'optimisation d'architecte, mais elles n'invalident en rien la qualité et la pertinence du plan pour atteindre vos objectifs rapidement et de manière pragmatique.

**Mes recommandations finales sont :**

1.  **Valider le plan tel quel** pour le Module 1. Il est fonctionnel et solide.
2.  **Envisager d'appliquer la suggestion du Mixin de chiffrement**. C'est une petite modification qui rendra le code plus propre sans ajouter de complexité. Vous pouvez le demander directement à Claude Code.
3.  **Garder les autres points (gestion du singleton, mise à jour des symboles) comme des notes d'amélioration post-V1.** Essayer de les intégrer maintenant irait à l'encontre de votre philosophie "Shipping > Process".

Vous avez fait un excellent travail de direction de projet en amenant "Claude Desktop" à produire ce document. Il a bien capturé l'essence de vos besoins. Vous pouvez lancer la phase de codage avec une grande confiance.



=====================================================
07.08.2025

Terminé Aristob3.md et validé par Ous.41
Mis à jour IMPLEMANTATION_PLA.md par Opus4.1

08.08.2025

Lancé Claude Code dans l'environnement de dev Conda

**> Durant la phase de développement tu as eu diférents problèmes. Dis moi lesquels et comment tu les as résolu**

● Voici les problèmes rencontrés durant le développement du Module 1 et leurs résolutions :

  1. Problèmes d'encodage Unicode 🔤

  Problème : Multiples SyntaxError avec UnicodeDecodeError lors de la lecture des fichiers Python contenant des caractères français accentués (é, è, à, ç).

  Exemples d'erreurs :
  SyntaxError: (unicode error) 'utf-8' codec can't decode byte 0xe9 in position 866: invalid start byte

  Résolution : Remplacement systématique de tous les caractères accentués par leurs équivalents ASCII dans tous les fichiers Python :
  - é → e
  - è → e
  - à → a
  - ç → c

  2. Conflits de migrations Django 📊

  Problème : InconsistentMigrationHistory - Django tentait d'appliquer admin.0001_initial avant accounts.0001_initial, créant une dépendance circulaire avec le modèle User personnalisé.

  Erreur :
  InconsistentMigrationHistory: Migration admin.0001_initial is applied before its dependency accounts.0001_initial

  Résolution :
  1. Suppression de tous les fichiers de migration existants
  2. Passage temporaire de PostgreSQL à SQLite pour éviter les contraintes
  3. Recréation complète des migrations avec makemigrations et migrate

  3. Problèmes d'affichage console Windows 💻

  Problème : UnicodeEncodeError lors de l'affichage de caractères spéciaux comme ✓ et 🚀 dans les management commands.

  Erreur :
  UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' in position 0: character maps to <undefined>

  Résolution : Remplacement des symboles Unicode par du texte ASCII :
  - ✓ → "OK"
  - 🚀 → ""
  - ⚠️ → "ATTENTION"

  4. Configuration d'authentification en mode DEBUG 🔐

  Problème : Implémentation de l'auto-login pour l'utilisateur 'dev' en mode développement sans compromettre la sécurité en production.

  Résolution : Création d'un backend d'authentification personnalisé (DevModeBackend) qui ne s'active qu'en mode DEBUG :
  if settings.DEBUG and not username:
      try:
          return User.objects.get(username='dev')

  5. Gestion des clés API chiffrées 🔑

  Problème : Besoin de chiffrer les clés API des brokers avec la SECRET_KEY Django sans exposer les données sensibles.

  Résolution : Implémentation de méthodes de chiffrement/déchiffrement dans le modèle Broker :
  def encrypt_api_key(self, raw_key):
      key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
      f = Fernet(key)
      return f.encrypt(raw_key.encode()).decode()

  6. Configuration CCXT avec limitation de taux ⚡

  Problème : Intégration de CCXT avec enableRateLimit: true tout en maintenant un pattern singleton par utilisateur/exchange.

  Résolution : Service singleton CCXTService avec cache par user_id et exchange :
  cache_key = f"ccxt_{broker.user_id}_{broker.exchange}_{broker.id}"
  if cache_key not in self._exchanges:
      # Création nouvelle instance avec enableRateLimit: True

  7. Architecture multi-tenant stricte 🏢

  Problème : Garantir l'isolation complète des données par utilisateur sans compromis de sécurité.

  Résolution : Implémentation de filtres user=request.user dans tous les ViewSets et managers personnalisés pour forcer la ségrégation des données.

  Stratégie de résolution globale :

  1. Tests itératifs : Après chaque fix, test immédiat avec python manage.py check et commandes de gestion
  2. Approche progressive : Résolution un problème à la fois pour éviter les régressions
  3. Compatibilité Windows : Adaptation spécifique pour l'environnement de développement Windows
  4. Sécurité first : Aucun compromis sur le chiffrement et l'isolation des données

  Tous ces problèmes ont été résolus tout en maintenant l'exactitude du code spécifié dans IMPLEMENTATION_PLAN.md.
  
  Configuration Claude Code pour les accents français :
1. Variable d'environnement avant de lancer Claude Code
bashset PYTHONIOENCODING=utf-8
claude-code
2. Configuration PowerShell (si utilisé)
powershell$env:PYTHONIOENCODING="utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
3. Page de codes Windows
bashchcp 65001
# Puis lancer Claude Code
4. Dans le code Python - forcer UTF-8
python# Début de chaque fichier .py
# -*- coding: utf-8 -*-
Impact sur l'existant :
✅ Aucun impact fonctionnel - Les chaînes sans accent fonctionnent parfaitement
✅ Base de données - PostgreSQL gère UTF-8 nativement, aucun problème
✅ APIs - JSON est UTF-8 par défaut
✅ Frontend - Vue.js gère UTF-8 nativement
Seuls impacts cosmétiques :

Messages console : "Cree" au lieu de "Créé"
Commentaires dans le code : "mise a jour" au lieu de "mise à jour"
Help text des modèles Django

Recommandation : Garde tes solutions actuelles, c'est robuste et portable. Ajoute juste chcp 65001 avant de lancer Claude Code pour les prochains modules si tu veux les accents.
L'ASCII c'est plus safe pour la compatibilité cross-platform.

=====================================================

**1) Je souhaite que tu me fasse un résumé des problèmes que nous avons résolus depuis que nous avons passe de SQLlite à PostgreSQL, de manière à ce que je puisse tenir ma documentation.**


 Résumé des Problèmes Résolus : Migration SQLite → PostgreSQL

  🎯 Objectif Initial

  Migration complète de la base de données SQLite vers PostgreSQL avec reset complet, corrections d'encodage UTF-8 et restauration fonctionnelle complète de l'application.

  ✅ Problèmes Résolus

  ● Liste des Problèmes Résolus avec Solutions Techniques

  1. Erreurs d'Encodage UTF-8 dans Fichiers Python

  Problème : SyntaxError: Non-UTF-8 code starting with '\xe9' sur caractères accentués (é, è, à)

  Solution technique :
  - Ajout systématique du header # -*- coding: utf-8 -*- en première ligne de tous les fichiers Python
  - Normalisation des caractères : é→e, è→e, à→a dans les commentaires et strings
  - Identification par grep des fichiers contenant des caractères non-ASCII
  - Validation par redémarrage Django sans erreurs d'encodage

  2. Erreur 404 Frontend Vite Development Server

  Problème : http://localhost:5173/ retourne "404 Not Found"

  Solution technique :
  - Cause : Vite cherche index.html à la racine du projet, pas dans public/
  - Fix : Déplacement de frontend/public/index.html → frontend/index.html
  - Principe Vite : Convention SPA où index.html doit être au niveau du vite.config.js
  - Redémarrage du dev server pour prise en compte nouvelle structure

  3. Page Blanche Vue.js (Runtime Compilation)

  Problème : Application charge mais affiche page blanche, erreur console Vue runtime

  Solution technique :
  - Cause : Vue runtime par défaut ne supporte pas la compilation de templates
  - Fix : Configuration alias dans vite.config.js :
    - 'vue': 'vue/dist/vue.esm-bundler.js' (version complète avec compiler)
  - Feature flags ajoutés :
    - __VUE_OPTIONS_API__: true (support Options API)
    - __VUE_PROD_DEVTOOLS__: false (désactive devtools en prod)
    - __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false (pas de détails mismatch)

  4. Django Multiple Authentication Backends Error

  Problème : ValueError: You have multiple authentication backends configured and therefore must provide the backend argument

  Solution technique :
  - Cause : settings.py définit 2 backends dans AUTHENTICATION_BACKENDS
  - Fix : Spécification explicite du backend dans login() :
    - login(request, user, backend='apps.accounts.backends.DevModeBackend')
  - Logique : Django ne peut choisir automatiquement entre DevModeBackend et ModelBackend
  - Application dans login_view(), logout_view(), et current_user()

  5. Configuration CORS pour Authentification Cross-Origin

  Problème : Sessions non maintenues entre frontend (5173) et backend (8000)

  Solution technique :
  - Paramétrage CORS dans settings.py :
    - CORS_ALLOW_CREDENTIALS = True (autorise envoi cookies/sessions)
    - CORS_ALLOWED_ORIGINS spécifique (sécurisé vs CORS_ALLOW_ALL_ORIGINS)
  - Frontend : axios configuré avec withCredentials: true
  - Sessions Django : Middleware SessionMiddleware maintenu actif

  6. Migration PostgreSQL et Reset Base

  Problème : Conflicts de migrations existantes lors du changement SQLite→PostgreSQL

  Solution technique :
  - Database config : Changement ENGINE vers django.db.backends.postgresql
  - Reset migrations :
    a. Suppression physique dossiers migrations/ (sauf __init__.py)
    b. python manage.py makemigrations accounts (premier car AUTH_USER_MODEL)
    c. python manage.py makemigrations (autres apps)
    d. python manage.py migrate
  - Ordre critique : accounts en premier car dépendance AUTH_USER_MODEL

  7. Permissions API Temporaires pour Debugging

  Problème : Endpoint /api/auth/current/ bloqué par permissions IsAuthenticated

  Solution technique :
  - Changement temporaire : @permission_classes([AllowAny]) sur current_user
  - Logique debug : Auto-login avec user 'dev' si settings.DEBUG et non authentifié
  - Auto-connexion : login(request, user, backend='...') automatique en mode DEBUG
  - Sécurité : Seulement actif si DEBUG=True

  8. Configuration REST Framework Authentication

  Problème : API endpoints ne reconnaissent pas les sessions Django

  Solution technique :
  - DRF Settings configuré pour SessionAuthentication :
  'DEFAULT_AUTHENTICATION_CLASSES': [
      'rest_framework.authentication.SessionAuthentication',
  ]
  - Permissions : IsAuthenticated par défaut sauf endpoints publics
  - Middleware ordre : SessionMiddleware avant AuthenticationMiddleware

  9. DevModeBackend Custom Authentication

  Problème : Backend custom pour auto-login dev non reconnu

  Solution technique :
  - Configuration DEBUG : Backend custom en premier dans liste :
  AUTHENTICATION_BACKENDS = [
      'apps.accounts.backends.DevModeBackend',  # Custom first
      'django.contrib.auth.backends.ModelBackend',  # Fallback
  ]
  - Spécification explicite : backend= parameter dans tous les login() calls
  - Logique conditionnelle : Activation seulement si settings.DEBUG

  10. Structure Fichiers Vite SPA

  Problème : Vite ne trouve pas les assets et point d'entrée

  Solution technique :
  - Structure correcte :
    - frontend/index.html (racine projet)
    - frontend/src/main.js (point d'entrée)
    - frontend/vite.config.js (config)
  - Script import : <script type="module" src="/src/main.js"></script>
  - Convention Vite : index.html doit être au même niveau que vite.config.js
  
   📊 Techniques de Diagnostic Utilisées

  1. Log Analysis : Lecture systématique des erreurs Django console
  2. Browser DevTools : Inspection Network/Console pour erreurs frontend
  3. File Structure Validation : Vérification conventions framework (Vite/Django)
  4. Incremental Testing : Test après chaque modification pour isolation problème
  5. Configuration Comparison : Vérification settings vs documentation officielle
   
  📊 État Final

  Frontend (100% Fonctionnel) ✅

  - ✅ Application charge correctement sur http://localhost:5173/
  - ✅ Navigation entre composants opérationnelle
  - ✅ Interface "clean" et responsive
  - ✅ Aucune erreur de compilation Vue.js
  - ✅ Vite dev server stable

  Backend (Partiellement Fonctionnel) ⚠️

  - ✅ Serveur Django démarre sans erreur
  - ✅ Base PostgreSQL connectée
  - ✅ Migrations appliquées avec succès
  - ⚠️ Problèmes restants : Erreurs 403/500 sur endpoints authentifiés

  🔍 Points Techniques Critiques Résolus

  1. Architecture Multi-tenant : Préservation de l'isolation des données utilisateur
  2. Chiffrement API Keys : Maintien de la sécurité avec Fernet + SECRET_KEY
  3. Configuration CCXT : Intégration exchanges crypto maintenue
  4. WebSocket Channels : Configuration Redis préservée
  5. Structure Django 4.2.15 : Compatibilité assurée

  📝 Fichiers Modifiés Principaux

  - backend/aristobot/settings.py - Configuration PostgreSQL + CORS
  - backend/apps/accounts/views.py - Fix authentification multiple backends
  - frontend/vite.config.js - Configuration Vue runtime + alias
  - frontend/index.html - Repositionné pour Vite SPA
  - Tous fichiers Python - Headers UTF-8 ajoutés

  🎯 Prochaines Étapes Identifiées

  Le problème bloquant restant est l'authentification backend (/api/auth/current/ retourne 403/500). Une fois résolu, l'ensemble de l'application sera pleinement opérationnelle.
 OK, je voudrais la liste des problèmes résolus ET comment ils ont étés résolus. tu peux mette des explications technique.

**2) Est-ce que ces problèmes sont définitivement résolus et ne se produireons plus lors du développment des futures applications ? Répond brievement**

● Non, ces problèmes peuvent se reproduire :

  1. Encodage UTF-8 : Risque sur nouveaux fichiers Python avec caractères accentués
  2. Migrations Django : Problèmes d'ordre possibles si modifications du modèle User
  3. Configuration Vite : Erreurs si changement de version Vue/Vite
  4. CORS : À reconfigurer pour nouveaux domaines/ports

  Solutions préventives :
  - Template IDE avec header UTF-8 automatique
  - Ordre migrations documenté dans CLAUDE.md
  - Configuration Vite versionée
  - Variables d'environnement pour CORS

  **Finalement le fichier "" a été mis à jours**
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

## CONTRAINTES TECHNIQUES CRITIQUES (ajout basé sur debugging)
### Encodage Windows
- # -*- coding: utf-8 -*- obligatoire première ligne Python
- Caractères ASCII : é→e, è→e, à→a (pas d'émojis/accents)

### Frontend Vite/Vue
- index.html à la racine frontend/ (pas dans public/)
- vite.config.js : vue runtime complet + feature flags
- CORS withCredentials + backend CORS_ALLOW_CREDENTIALS

### Django Auth/Migrations  
- Migrations : accounts app TOUJOURS en premier
- Backend auth : spécifier backend= dans login() calls
- Reset migrations si conflicts : DROP DB + delete migrations/

### Multi-tenant
- TOUJOURS filtrer par user_id dans ViewSets
- API keys chiffrées Fernet + SECRET_KEY
- CCXT enableRateLimit: true

### Variables d'environnement
- .env à la racine projet (DEBUG='True' développement)
- SECRET_KEY unique, REDIS_HOST pour Channels

### API REST & Permissions  
- DRF SessionAuthentication par défaut
- Filtrage request.user OBLIGATOIRE dans ViewSets
- @permission_classes([AllowAny]) seulement endpoints auth

### Commandes de base
- python manage.py init_aristobot (user dev)
- Ports : Django 8000, Vue.js 5173
- Test après chaque migration/reset DB1

  Les erreurs d'authentification backend restent à déboguer.
  
====================================================================================
  09.08.2025
  
  ODEBUG=True                # Django debug mode
  DEBUG_ARISTOBOT=True      # Aristobot auto-login mode

  Configuration Actuelle

  - DEBUG=True : Django en mode développement (erreurs détaillées, admin, etc.)
  - DEBUG_ARISTOBOT=True : Mode développement Aristobot (auto-login user 'dev')

  Les deux variables sont bien séparées et configurées correctement. La modification du code est donc complète et cohérente avec la configuration environnement.

  Résultat : Le mode auto-login Aristobot est maintenant contrôlé par DEBUG_ARISTOBOT indépendamment du mode DEBUG de Django.
  
  =========================================
  09.08.2025


Refactoring....

   # Tests basiques avec curl
  curl -X POST "http://127.0.0.1:8000/api/auth/login/" -d '{"username":"dac","password":"aristobot"}' -c cookies.txt
  curl -X PUT "http://127.0.0.1:8000/api/accounts/preferences/" -b cookies.txt -d '{"theme":"dark"}'

  🎯 Ce que j'aurais dû faire en plus :

  1. Tester les deux domaines séparément

  # Tester avec 127.0.0.1
  curl -X POST "http://127.0.0.1:8000/api/auth/login/" -c cookies_127.txt -d '...'
  curl -X PUT "http://127.0.0.1:8000/api/accounts/preferences/" -b cookies_127.txt -d '...'

  # Tester avec localhost
  curl -X POST "http://localhost:8000/api/auth/login/" -c cookies_localhost.txt -d '...'
  curl -X PUT "http://localhost:8000/api/accounts/preferences/" -b cookies_localhost.txt -d '...'

  # Cross-test (le problème aurait été visible !)
  curl -X POST "http://127.0.0.1:8000/api/auth/login/" -c cookies_mixed.txt -d '...'
  curl -X PUT "http://localhost:8000/api/accounts/preferences/" -b cookies_mixed.txt -d '...'
  # ↑ Ceci aurait échoué et révélé le problème !

  2. Simuler les requêtes exactes du frontend

  # Avec les headers CORS exacts
  curl -X PUT "http://localhost:8000/api/accounts/preferences/" \
    -H "Origin: http://localhost:5173" \
    -H "Referer: http://localhost:5173/" \
    -H "Content-Type: application/json" \
    -b cookies.txt -d '{"theme":"dark"}'

  3. Vérifier les cookies de domaine

  # Examiner le contenu des cookies
  cat cookies.txt
  # Aurait montré : domain=127.0.0.1 vs domain=localhost

  # Tester manuellement les domaines
  curl -v "http://127.0.0.1:8000/api/auth/status/" -b "sessionid=ABC123"
  curl -v "http://localhost:8000/api/auth/status/" -b "sessionid=ABC123"

  4. Diagnostiquer CORS spécifiquement

  # Tester preflight OPTIONS
  curl -X OPTIONS "http://localhost:8000/api/accounts/preferences/" \
    -H "Origin: http://localhost:5173" \
    -H "Access-Control-Request-Method: PUT" -v

  # Vérifier headers CORS dans la réponse

  5. Créer un mini-test automatisé

  # Script de test complet
  #!/bin/bash
  echo "=== Test domaine 127.0.0.1 ==="
  SESSION1=$(curl -s -X POST "http://127.0.0.1:8000/api/auth/login/" -d '...' -c /tmp/cookies1 | grep -o 'session[^"]*')

  echo "=== Test domaine localhost ==="
  SESSION2=$(curl -s -X POST "http://localhost:8000/api/auth/login/" -d '...' -c /tmp/cookies2 | grep -o 'session[^"]*')

  echo "=== Cross test (problème attendu) ==="
  curl -s -X PUT "http://localhost:8000/api/accounts/preferences/" -b /tmp/cookies1 -d '...' || echo "ECHEC ATTENDU"

  📝 Leçons apprises :

  1. Toujours tester les cross-domains quand il y a des problèmes de cookies/sessions
  2. Simuler exactement les requêtes frontend avec les bons headers
  3. Examiner le contenu des cookies (domaine, path, expiration)
  4. Tester les preflight CORS séparément des requêtes réelles
  5. Créer des scripts de test répétables pour éviter les erreurs manuelles
  
  
  
  ==================================================================
  Suite à une réflexion concernant CCXT (Chargement des marchés), j'en ai déduit quil serait bon d'implémenter cette librairie de cette manière.
  Quand penses-tu ? sois direct et franc
  
  Aristobot3/
├── backend/
│   ├── aristobot/                  # Configuration Django principale
│   │   ├── settings.py, urls.py, asgi.py, routing.py
│   ├── apps/
│   │   ├── core/                   # Services partagés, Heartbeat, Mixins
│   │   │   ├── management/commands/
│   │   │   │   ├── run_heartbeat.py
│   │   │   │   ├── markets_live.py        # ← NOUVEAU : Tâche de chargement des marchés
│   │   │   ├── consumers.py
│   │   │   ├── models.py
│   │   │   └── services/
│   │   │       └── ccxt_manager.py        # ← NOUVEAU : Singleton CCXT (async)
│   │   ├── accounts/              # Gestion utilisateurs
│   │   ├── brokers/               # Gestion des brokers
│   │   ├── market_data/           # Stockage des bougies et symboles
│   │   ├── strategies/            # CRUD des stratégies
│   │   ├── trading_engine/        # Logique d'exécution des trades
│   │   │   └── management/commands/
│   │   │       └── run_trading_engine.py
│   │   ├── trading_manual/
│   │   ├── backtest/
│   │   ├── webhooks/
│   │   └── stats/
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── views/                 # 8 pages Vue.js
│   │   ├── components/
│   │   ├── api/
│   │   ├── websocket/
│   │   └── design-system/
│   │       ├── tokens.js
│   │       └── README.md
│   ├── package.json
│   └── vite.config.js
├── docs/
│   └── design/                   # Mockups et références visuelles
├── .env.example
├── .gitignore
├── .claude-instructions
└── README.md


Terminal 5 : Chargement des Marchés (Tâche de gestion Django)

Commande : python manage.py markets_live
Rôle : Initialise les connexions CCXT pour tous les brokers configurés, charge les marchés (load_markets() en mode asynchrone), les stocke dans la base de données, et les rend disponibles via un singleton (ccxt_manager.py) pour toutes les autres applications (Trading Engine, Trading Manuel, Stratégies, etc.).
      Terminal 1                      Terminal 2                         Terminal 3                       Terminal 4                      Terminal 5
+-----------------------+     +--------------------------+      +--------------------------+      +-------------------------+      +--------------------------+
|  > daphne ...         |     |  > python manage.py      |      |  > python manage.py      |      |  > npm run dev          |      |  > python manage.py      |
|                       |     |    run_heartbeat         |      |    run_trading_engine    |      |                         |      |    markets_live          |
|   SERVEUR WEB & WSS   |     |                          |      |                          |      |   INTERFACE UTILISATEUR |      |   CHARGEMENT MARCHÉS     |
|   (Le standardiste)   |     |    HEARTBEAT SERVICE     |      |    TRADING ENGINE        |      |   (Le cockpit)          |      |   (Le logisticien)       |
+-----------------------+     +--------------------------+      +--------------------------+      +-------------------------+      +--------------------------+
           ^                             |                                  |                                 ^                                |
           |                             | (Publie sur Redis)               | (Écoute Redis)                  |                                |
           +-----------------------------+----------------------------------+---------------------------------+--------------------------------+
                                         |
                                  +----------------+
                                  |     REDIS      |
                                  | (Le système    |
                                  |    nerveux)    |
                                  +----------------+


3.3 Le Logisticien : Le Service MarketsLive
Le MarketsLive est le service qui prépare le terrain pour les opérations de trading. Il agit comme un logisticien, en assurant que toutes les connexions aux brokers sont établies et que les marchés sont correctement chargés et disponibles.

Rôle : Initialiser les connexions CCXT pour chaque broker configuré, charger les marchés (load_markets()), et les rendre accessibles à l’ensemble du système via un singleton en mémoire (ccxt_manager.py).

Fonctionnement détaillé :

Connexion Asynchrone aux Brokers : Le script markets_live.py utilise ccxt.async_support pour établir des connexions non bloquantes à chaque exchange configuré par les utilisateurs.
Chargement des Marchés : Pour chaque broker, les paires de trading disponibles sont récupérées via await exchange.load_markets() et stockées dans la table Markets de la base de données.
Singleton Partagé : Chaque instance CCXT est enregistrée dans un dictionnaire global (ccxt_instances) indexé par user_id et broker_id, accessible par toutes les autres applications Django (Trading Engine, Trading Manuel, Stratégies, etc.).
Prévention des Rate Limits : En centralisant les connexions et en évitant les appels redondants, le service respecte les limites d’API imposées par les exchanges, garantissant une exécution fluide et fiable.
Complémentarité avec le Trading Engine : Le moteur de trading utilise les connexions et les marchés préchargés par MarketsLive pour exécuter les ordres sans avoir à recharger les données à chaque signal. Cela réduit la latence et améliore la robustesse du système.

**Finalement modifié Aristobot3.md**

Ajout à placer après la section 3.2 (Le Cerveau : Le Moteur de Trading)
3.3 Architecture CCXT : Le Gestionnaire Singleton
Le CCXTManager est le point d'accès unique pour toutes les interactions avec les exchanges. Il garantit une utilisation optimale des connexions et le respect des rate limits.
Principe de fonctionnement :

Une instance par broker : Le singleton maintient un dictionnaire {(user_id, broker_id): exchange_instance} en mémoire
Chargement unique des marchés : load_markets() n'est appelé qu'une fois à la création de l'instance, puis les données restent en cache
Réutilisation permanente : Tous les services (Trading Engine, Trading Manuel, Backtest) utilisent la même instance

Cycle de vie :
python# apps/core/services/ccxt_manager.py
1. get_exchange(broker) → Récupère ou crée l'instance
2. Si nouvelle : await exchange.load_markets() → Cache permanent
3. Retourne l'instance pour utilisation
Initialisation au démarrage :

Le Trading Engine précharge au boot TOUS les brokers configurés
Les nouveaux brokers ajoutés en cours de route sont chargés à la première utilisation
Aucun rechargement des marchés entre les ordres

Modification dans la section 3.2 (Trading Engine)
Ajouter après "Workflow détaillé", point 0 :

0. Initialisation au démarrage : Le Trading Engine précharge toutes les connexions CCXT des brokers actifs via le CCXTManager, garantissant une latence minimale lors de l'exécution des stratégies.

C'est tout ! Ça reste concis et dans l'esprit du document - pragmatique et sans sur-ingénierie.

==============================================================================
