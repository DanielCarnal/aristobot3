# Aristobot3_1.md - GUIDE DU DEVELOPPEUR (ARCHITECTURE NATIVE EXCHANGE GATEWAY)
background-color:: yellow

> **📚 RÈGLES DE DÉVELOPPEMENT STRICTES**
>
> Ce document décrit l'architecture fonctionnelle et les workflows d'Aristobot3.
>
> **Pour les règles techniques NON NÉGOCIABLES (Stack, Design, APIs natives, WebSockets):**
> 👉 **Voir [@DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md)**
>
> Les règles de développement DOIVENT être consultées avant toute implémentation.

---

- ## 1. Philosophie et Cadre du Projet
  background-color:: red
  
  Aristobot V3.1 est un bot de trading de cryptomonnaies personnel, développé sous une philosophie pragmatique de **"vibe coding"**.
- **Principes Directeurs** :
  background-color:: pink
  * **Fun > Perfection** : Le plaisir de développer prime sur la perfection technique.
  * **Shipping > Process** : Livrer des fonctionnalités fonctionnelles rapidement.
  * **Pragmatique > Enterprise** : Des solutions simples pour un projet à échelle humaine.
  * **Itération Rapide** : Des cycles de développement courts pour un feedback immédiat.
  
  * **Limites et Contraintes Fondamentales** :
  * **Utilisateurs** : Strictement limité à 5 utilisateurs.
  * **Stratégies** : Limité à 20 stratégies actives simultanément.
  * **Environnement de Développement** : Conda avec Python 3.11, en utilisant VS Code et des assistants IA.
- **Stack Technique** :
  background-color:: pink

  **⚠️ RÈGLES TECHNIQUES STRICTES:** Voir [@DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) pour toutes les règles architecturales NON NÉGOCIABLES (RÈGLE #2 - Stack Technique, RÈGLE #3 - Design System, RÈGLE #4 - APIs Natives Complètes).

  **Résumé Architecture:**
  * **Backend:** Django 4.2.15 + Django Channels + Daphne
  * **Frontend:** Vue.js 3 (Composition API)
  * **Base de Données:** PostgreSQL (source de vérité unique)
  * **Communication:** Redis + WebSockets
  * **Parallélisme:** asyncio exclusivement
  * **Exchange Gateway:** Service centralisé (Terminal 5) avec APIs natives
- ### Structure des Fichiers
  
  ```
  Aristobot3/
  ├── backend/
  │   ├── aristobot/              # Configuration Django principale
  │   │   ├── settings.py, urls.py, asgi.py, routing.py
  │   ├── apps/
  │   │   ├── core/              # Services partagés, Heartbeat, Exchange Gateway centralisé
  │   │   │   ├── management/commands/
  │   │   │   │   ├── run_heartbeat.py      # Terminal 2
  │   │   │   │   └── run_exchange_service.py   # Terminal 5 (NOUVEAU)
  │   │   │   ├── services/
  │   │   │   │   ├── exchange_manager.py       # Service centralisé Exchange Gateway
  │   │   │   │   ├── exchange_client.py        # Client pour communication Redis (NOUVEAU)
  │   │   │   │   └── symbol_updater.py
  │   │   │   ├── consumers.py   # WebSocket publishers
  │   │   │   └── models.py
  │   │   ├── accounts/          # Gestion utilisateurs
  │   │   ├── brokers/           # Gestion des brokers (APIs natives directes pour tests)
  │   │   ├── market_data/       # Stockage des bougies et symboles
  │   │   ├── strategies/        # CRUD des stratégies
  │   │   ├── trading_engine/    # Logique d'exécution des trades
  │   │   │   └── management/commands/
  │   │   │       └── run_trading_engine.py # Terminal 3 (utilise ExchangeClient)
  │   │   ├── trading_manual/    # Trading manuel (utilise ExchangeClient)
  │   │   ├── backtest/          # Backtesting (utilise ExchangeClient)
  │   │   ├── webhooks/          # Webhooks externes
  │   │   └── stats/             # Statistiques de performance
  │   ├── requirements.txt
  │   └── manage.py
  ├── frontend/
  │   ├── src/
  │   │   ├── views/             # 8 pages Vue.js
  │   │   ├── components/
  │   │   ├── api/
  │   │   ├── websocket/
  │   │   └── design-system/
  │   │       ├── tokens.js     # Design tokens
  │   │       └── README.md
  │   ├── package.json
  │   └── vite.config.js
  ├── docs/
  │   └── design/               # Mockups et références visuelles
  ├── MODULE2-Refacto-Exchange_Gateway.md  # Prompt Claude Code (NOUVEAU)
  ├── Aristobot3.1.md			   # Documentation du projet
  ├── .env
  ├── .env.example
  ├── .gitignore
  ├── .claude-instructions
  └── README.md
  ```
  
  **Nouveaux fichiers pour l'architecture service centralisé :**
- 🆕 `apps/core/management/commands/run_exchange_service.py` : Exchange Gateway centralisé (Terminal 5)
- 🆕 `apps/core/services/exchange_client.py` : Client pour communication Redis avec l'Exchange Gateway
- 🔄 `apps/core/services/exchange_manager.py` : Modifié pour fonctionner uniquement dans le service centralisé
- 🆕 `MODULE2-Refacto-Exchange_Gateway.md` : Instructions détaillées pour Claude Code
  
  **Coexistence APIs natives :**
- ✅ `apps/brokers/` : Garde APIs natives directes pour tests de connexion ponctuels
- ✅ `apps/trading_*` : Utilisent ExchangeClient pour opérations répétées via service centralisé
- ## 2. Expérience Utilisateur (Frontend)
- ### Layout Global
  
  * **Structure** : Une barre latérale (**Sidebar**) fixe à gauche, un bandeau supérieur (**Header**) fixe contenant la barre de statut, et une zone principale de contenu scrollable.
  * **Menu Principal** (dans la Sidebar) :
  
  * Heartbeat
  * Trading manuel
  * Trading BOT
  * Stratégies
  * Backtest
  * Webhooks
  * Statistiques
  * Mon Compte
  * **Barre de Statut** (dans le Header) :
  
  * **Heartbeat Actif/Inactif** : Une pastille visuelle (verte/rouge).
  * **Heartbeat Cohérent/Non Cohérent** : Indicateur de la régularité des données (à développer ultérieurement).
  * **Nombre d'Exchanges :** Indique le nombre de marchés chargé, et si en cours de chargement, affiche "Chargement 'Exchange X' xxx%". C'est un **élément actif**. Sur pression, il lance la fonction de chargement.
  * **Stratégies Live** : Indique si une ou plusieurs stratégies sont en cours d'exécution.
  * **Mode Testnet** : Affiche un avertissement visuel (couleur inversée, bordure rouge) si le mode Testnet est activé.
  * **Bouton** [Déconnexion]
- ### Authentification et Login
  
  * **Rôle** : Permettre à l'utilisateur de s'authentifier ou créer de un compte. Une fonction spéciale DEBUG permet de bypasser l'authentification.
  
  * **Description** :
  * La création d'un nouveau compte se fait par une fenêtre modale.
  * L'authentification s'affiche avent que tout autre éléments de l'application. Un simple saisie du user/password permet l'authentification.
  * Un mode "développement" permet de s'authentifier automatiquement avec un user pré-défini (dev) sans saisie de user/password. Le but est qu'un agent IA puisse se connecter facilement et naviguer (piloter un navigateur) dans l'application à des fin de tests.
    
  * **Mode développement**
      * **Activation** : Variable `DEBUG_ARISTOBOT=True` + bouton UI
      * **Fonctionnement** : Auto-login user "dev"
      * **Sécurité** : Désactivé automatiquement en production
        
  * **Backend** :
  * Lorsque la variable du fichier **`.env`**  a la valeur **`DEBUG_ARISTOBOT=True`**.
    * Le bouton "Mode développement" est affiché en bas de la fenêtre de login utilisateur. C'est un bouton ON/OFF. Il permet d'activer le mode développement s'il est inactif et de le désactiver s'il est actif.
    * **Activation** pression du bouton (initialement sur OFF):
      * L'application enregistre dans la DB table Debug le mode Debug (ON)
      * L'application désactive les champs utilisateur/mot de passe et transmet au module authentication standard l'utilisateur "dev" (comme si les champs user/mot de passe avaient été renseignés pas l'utilisateur.L'utilisateur "dev" est un utilisateur normal comme tous les autre utilisateurs, il a un accès normal aux données qui le concerne.
      * Modifie le status dans la barre de status en haut de la page "Debug actif"
    * **Désactivation** pression du bouton, initialement ON.
      * L'application enregistre dans la DB table Debug le mode Debug (OFF)
      * Le status dans la barre de status en haut de la page "Debug inactif"
      * Active les champs user/password pour permettre un login normal de tout utilisateur le désirant.
  * Lorsque la variable du fichier **`.env`** a la valeur **`DEBUG_ARISTOBOT=False`**
    * Vérifier que dans la DB, la table Debug le mode Debug soit remis à OFF, par sécurité.
    * Le bouton d'activation/désactivation du mode debug  de la fenêtre login utilisateur **n'est pas affiché**
    * Le seul moyen de l'afficher est que l'utilisateur modifie le fichier **`.env`**, et redémarre le serveur Daphne afin de prendre en compte le changement.
  * Le bouton "Déconnexion" permet à l'utilisateur de se déconnecter.
    
  * **Frontend** : Affiche :
  * Les champs user password et le bouton login
  * un bouton "nouveau compte" et une fenêtre modale pour la saisie des éléments (user / password) sur pression de celui-ci.
  * Si les conditions sont réunis, affiche le bouton "Mode debug"
  * Le bouton déconnexion se situe en haut à gauche de la barre de menu
  * Affiche dans la barre de status en haut de la page "Debug actif" si DEBUG=ON sinon RIEN
    
  * **DB** : Lit et enregistre les comptes utilisateur et l'état du bouton "Mode développement"
- ### Design System

  **⚠️ RÈGLES DESIGN STRICTES:** Voir [@DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) RÈGLE #3 pour toutes les contraintes design NON NÉGOCIABLES (couleurs néon, thème sombre, desktop first).

  **Résumé:**
  * **Style:** Thème sombre crypto (Binance/TradingView)
  * **Couleurs:** Néon obligatoires (#00D4FF, #00FF88, #FF0055)
  * **Responsive:** Desktop first
- ## 3. Démarrage et Architecture des Services
  
  L'application est conçue pour fonctionner comme un écosystème de services interdépendants qui démarrent indépendamment et communiquent entre eux.
- ### Processus de Lancement : La "Checklist de Décollage"
  
  Pour que l'application soit pleinement opérationnelle, **cinq terminaux distincts** doivent être lancés.
  Ces services forment l'épine dorsale de l'application et fonctionnent en arrière-plan, indépendamment de la présence d'un utilisateur connecté à l'interface web.
  
- ##### **Terminal 1 : Serveur Web (Daphne)**
  * **Commande** : `daphne aristobot.asgi:application`
- **Port** : 8000
  * **Rôle** : C'est le serveur principal. Il gère toutes les requêtes HTTP (pour l'API REST et le service des pages web) et maintient les connexions WebSocket ouvertes avec les clients (navigateurs). C'est la porte d'entrée de toute l'application. Exécuter le code des apps Django (accounts, brokers, strategies, etc.)


- ##### **Terminal 2** : Service Heartbeat (Tâche de gestion Django)
  * ****Commande**** : `python manage.py run_heartbeat`
  * xxx
  * **Rôle** : Le "cœur" du système. Ce service se connecte directement au flux WebSocket de Binance pour écouter les données du marché en temps réel. Il est totalement indépendant et fonctionne en continu. Son rôle principal est de fournir le rythme aux applications Django, par exemple pour déclencher le calcul d'une stratégie, ou du rafraîchissement du prix affiché.
  * Connexion permanente au WebSocket Binance
  * Agrégation des trades en bougies multi-timeframe
  * Publication des signaux temporels sur Redis
  * Sauvegarde des bougies en PostgreSQL

- ##### **Terminal 3 : Moteur de Trading - Trading Engine (Tâche de gestion Django)**
   * **Commande** : `python manage.py run_trading_engine`
   * **Port** : Aucun (écoute Redis)
   * **Rôle** : Le "cerveau" du système. Ce service écoute les signaux émis par le _Heartbeat_ ET _webhooks_. Il prend les décisions de trading en exécutant la logique des stratégies actives.
   * **Responsabilités** :
	* Écouter DEUX sources : signaux Heartbeat ET webhooks
	* Charger et exécuter les stratégies Python
	* Traiter les webhooks avec logique métier
	* Gérer l'état des positions
	* Décider des ordres à passer
	* Communiquer avec Terminal 5 pour exécution

- ##### **Terminal 4 : Frontend (Vite)**
   * **Commande** : `npm run dev`
	* **Port** : 5173 (dev) ou 80/443 (production)
	  * **Rôle** : Sert l'interface utilisateur développée en Vue.js. C'est ce que l'utilisateur voit et avec quoi il interagit dans son navigateur. Elle se connecte au serveur Daphne (Terminal 1) via WebSocket pour recevoir les données en temps réel.
	  * **Responsabilités** :
	    * Communication avec Terminal 1 (API + WebSocket)
	    * Affichage temps réel des données
	    * Gestion locale de l'état UI (Pinia)

- ##### **Terminal 5 : Native Exchange Gateway**
   * **Commande** : `python manage.py run_native_exchange_service`
   * **Fichier de démarrage** : `Start2 - Terminal 5 _ Native Exchange Service.bat`
   * **Port** : Aucun (écoute Redis)
   * **Rôle** : Le "hub" centralisé pour toutes les connexions aux exchanges avec APIs natives. Maintient des connexions lazy loading et communique avec les autres services via Redis. Enregistre toutes les demandes des applications (Trading Manuel, Wenhook, Trading Bot, Terminal 7) AVEC les réponses des exchanges dans la DB
   * **Responsabilités** :
	* Exécuter les **ordres** de trading
	* Récupérer les **balances** et **positions**
	* Tester les connexions pour User Account
	* Charger les marchés à la demande pour User Account
	* Proposer des **données unifiée** aux autres services, Terminaux et applications Django de Aristobot.
		- Communication native avec les Exchanges
		- Communication unifiée avec le reste des applications (conversion multi Exchanges).
	* **Enregistrer dans la DB**, table `trade`, toutes les demandes d'exécution d'ordre (achat, vente, modification, suppression, insertion), **avec** la réponse de l'Exchange. Toutes les données reçues de l'Exchange doivent être enregistrées **avec** la demande initiale complète, incluant l'identifiant du demandeur ("Trading Manuel", "Webhooks", "Trading Bot", "Terminal 7") ainsi qu'un TimeStamp. Les données unifiées sont utilisées.

	  **⚠️ DIRECTIVE API NATIVES:** Voir [@DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) RÈGLE #4 pour implémentation COMPLÈTE obligatoire des APIs natives (TOUS paramètres, TOUTES fonctionnalités).
  * ##### **Développement de Terminal 5**
      * @_bmad-output/planning-artifacts/Terminal5_Exchange_Gateway.md  # Architecture complète Terminal 5 (Party Mode 2026-01-21)

- ##### **Terminal 6 : Service Webhook Receiver (NOUVEAU)**
    - **Commande** : `python manage.py run_webhook_receiver`
    - **Port** : 8888 (configurable)
    - **Rôle** :
    	- Recevoir les webhooks HTTP POST, Serveur HTTP léger (FastAPI/aiohttp)
    	- Valider le token d'authentification
    	- Publier immédiatement sur Redis
    	- Répondre rapidement (200 OK)
    	- réception 24/7 des webhooks
    	- AUCUNE logique métier
    	- SAUVEGARDE le webhook dans la base de données Postgresql
	  
	  **Fonctionnement avec TERMINAL 6**   
	  ```ascii
	                        TradingView
	                            ↓   (HTTP POST port 80/443)
	                     [Firewall NAT 80→8888]
	           				   ↓
	      ┌──────────────────────────────────────────────────────────────────────────┐
	      │   Terminal 6: Webhook Receiver Service                                          │
	      │   • Serveur HTTP minimaliste (aiohttp port 8888)                                │
	      │   • AUCUNE logique métier                                                       │
	      │   • Juste recevoir → valider token → publier Redis → Sauvegarde dans Postgresql │
	      │   •                                                                             │
	      └────────────────────┬─────────────────────────────────────────────────────┘
	                             │ Redis: 'webhook_raw'
	                             ↓
	      ┌───────────────────────────────────────────────────────────┐
	      │   Backend Django App: apps/webhooks/                            │
	      │   • NE TOURNE PAS dans un terminal séparé                       │
	      │   • Fait partie de Terminal 1 (Daphne)                          │
	      │   • Fournit les APIs REST pour le frontend                      │
	      │   • /api/webhooks/history/ (GET)                                │
	      │   • /api/webhooks/stats/ (GET)                                  │
	      │   • /api/webhooks/positions/ (GET)                              │
	      │   • WebSocket consumers pour updates temps réel                 │
	      └───────────────────────────────────────────────────────────┘
	                           ↑ Lit la DB
	      ┌───────────────────────────────────────────────────────────┐
	      │   Terminal 3: Trading Engine (MODIFIÉ)                          │
	      │   • Écoute Redis 'webhook_raw' ET 'heartbeat'                   │
	      │   • NOUVELLE responsabilité: Traiter les webhooks               │
	      │   • Validation métier des webhooks                              │
	      │   • Gestion état positions (WebhookState)                       │
	      │   • Décision trading → envoi ordres vers Terminal 5             │
	      │   • Sauvegarde en DB (tables webhooks, trades)                  │
	      └────────────────────┬──────────────────────────────────────┘
	                             │ Redis: 'exchange_requests'
	                             ↓
	      ┌───────────────────────────────────────────────────────────┐
	      │   Terminal 5: Exchange Gateway                                   │
	      │   • Exécute les ordres                                          │
	      │   • Retourne confirmations                                      │
	      └───────────────────────────────────────────────────────────┘
	  ```
- ##### **Terminal 7 : Service de suivi des ordres**
  * **Commande** : `python manage.py run_???`
  * **Port** : Aucun (écoute Redis)
  * **Rôle** : Il recherche les ordres qui ont été FILL et met à jours la DB à chaque signal. Il est responsable des calculs P&L, rendements et autres statistiques. Il communique les résultats par websocket avec les applications qui demande des informations. Ce service écoute les signaux émis par le `Heartbeat`, qui sert de déclencheur pour l'exécution des processus. 
  * **Responsabilités** :
	- Le signal est l'horloge système, toute les 10 secondes
	- Charger les ordres ouverts des exchanges, vérifier leur présences dans la DB table `trade` (enregistrés lors de la création par Terminal 5). S'ils n'existent pas les ajouter dans la DB (ces ordre pourraient avoir été passés directement depuis l'interface native de l'Exchange). Renseigner la colonne "ordre_existant" avec "Ajouté par Terminal 7"
	- Charger les ordres exécutés
	- Comparer avec l'état précédent (est-ce qu'il y a des ordres ouverts qui ont été FILL ? ou partiellement FILL ?)
		- Oui
			- Enregistrer dans la DB, table `trade` les ordres FIll, les identifier et les lier à, ou modifier, l'enregistrement correspondant AVEC la réponse de l'Exchange. TOUTES les informations reçue de l'Exchange doivent être enregistrées au format unifié Aristobot (conversion multi Exchanges).
			- calculer le P&L
		- Non
			- ne rien faire
	- Communiquer avec Terminal 5 via Redis pour exécution des demandes
	  
	  **ARCHITECTURE Block**
	  ```ascii
	                    
	  +-----------------+         +---------------------------------------+
	  |     REDIS       |----+----| Terminal 1                            |
	  | (Communication  |    |    | > daphne ...                          |
	  |  inter-process) |    |    | SERVEUR WEB & WEBSOCKET (Standardiste)|
	  | • heartbeat     |    |    +---------------------------------------+
	  | • exchange_reqs |    |    
	  | • exchange_resp |    |    +---------------------------------------+
	  | • websockets    |    +----| Terminal 2                            |
	  | • webhooks      |    |    | > python manage.py run_heartbeat      |
	  +-----------------+    |    | HEARTBEAT                             |
	                     |    +---------------------------------------+
	                     |    
	                     |    +---------------------------------------+
	                     +----| Terminal 3                            |
	                     |    | > python manage.py run_trading_engine |
	                     |    | TRADING ENGINE                        |
	                     |    +---------------------------------------+
	                     |    
	                     |    +---------------------------------------+
	                     +----| Terminal 4                            |
	                     |    | > npm run dev                         |
	                     |    | FRONTEND (Vue.js) - (Cockpit)         |
	                     |    +---------------------------------------+
	                     |    
	                     |    +---------------------------------------+
	                     +----| Terminal 5                            |
	                     |    | > python manage.py run_exchange_service|
	                     |    | EXCHANGE GATEWAY                      |
	                     |    +---------------------------------------+
	                     |    
	                     |    +---------------------------------------+
	                     +----| Terminal 6                            |
	                     |    | > python manage.py run_webhook_receiver|
	                     |    | WEBHOOK RECEIVER                      |
	                     |    +---------------------------------------+
	                     |    
	                     |    +---------------------------------------+
	                     +----| Terminal 7                            |
	                          | (Réservé)                             |
	                          |                                       |
	                          +---------------------------------------+
	  ```
	  ```ascii
	                  ARCHITECTURE COMPLÈTE ARISTOBOT3.1 - 6 TERMINAUX
	  
	  ┌─────────────────────────────────────────────────────────────────────────┐
	  │                     SOURCES EXTERNES                                    │
	  ├─────────────────────────────────────────────────────────────────────────┤
	  │  • TradingView (Webhooks)                                              │
	  │  • Binance WebSocket (Market Data)                                     │
	  │  • Exchange APIs (Natives)                                             │
	  └─────────────────────────────────────────────────────────────────────────┘
	                  ↓                    ↓                    ↓
	  
	  ┌─────────────────────────────────────────────────────────────────────────┐
	  │                          COUCHE RÉCEPTION                              │
	  ├─────────────────────────────────────────────────────────────────────────┤
	  │                                                                         │
	  │  Terminal 2: Heartbeat          Terminal 6: Webhook Receiver           │
	  │  • WebSocket Binance            • HTTP Server (port 8888)              │
	  │  • Signaux temporels            • Réception TradingView                │
	  │  • Bougies OHLCV                • Validation token                     │
	  │  └→ Redis: 'heartbeat'          └→ Redis: 'webhook_raw'               │
	  │                                                                         │
	  └─────────────────────────────────────────────────────────────────────────┘
	                  ↓                                      ↓
	  
	  ┌─────────────────────────────────────────────────────────────────────────┐
	  │                       COUCHE TRAITEMENT                                │
	  ├─────────────────────────────────────────────────────────────────────────┤
	  │                                                                         │
	  │              Terminal 3: Trading Engine                                │
	  │              • Écoute Redis: 'heartbeat' + 'webhook_raw'              │
	  │              • Exécution stratégies Python                            │
	  │              • Traitement webhooks                                    │
	  │              • Gestion des positions                                  │
	  │              • Décisions de trading                                   │
	  │              └→ Redis: 'exchange_requests'                            │
	  │                                                                         │
	  └─────────────────────────────────────────────────────────────────────────┘
	                                      ↓
	  
	  ┌─────────────────────────────────────────────────────────────────────────┐
	  │                        COUCHE EXÉCUTION                                │
	  ├─────────────────────────────────────────────────────────────────────────┤
	  │                                                                        │
	  │              Terminal 5: Exchange Gateway Centralisé                   │
	  │              • Gestion instances exchanges                             │
	  │              • Exécution ordres                                        │
	  │              • Rate limiting                                           │
	  │              • Cache symboles                                          │
	  │              └→ Redis: 'exchange_responses'                            │
	  │                                                                        │
	  └------------------------------------------------------------------------┘
	                                      ↓
	  
	  ┌------------------------------------------------------------------------┐
	  │                      COUCHE PRÉSENTATION                               │
	  ├------------------------------------------------------------------------┤
	  │                                                                        │
	  │  Terminal 1: Daphne (Django)        Terminal 4: Frontend (Vue.js)      │
	  │  • API REST                          • Interface utilisateur           │
	  │  • WebSocket Server                  • Dashboard temps réel            │
	  │  • Authentification                  • Graphiques & monitoring         │
	  │  • Backend apps/*                    • Gestion des stratégies          │
	  │                                                                        │
	  └------------------------------------------------------------------------┘
	  
	  ┌─────────────────────────────────────────────────────────────────┐
	  │                         COUCHE DONNÉES                                 │
	  ├─────────────────────────────────────────────────────────────────┤
	  │  PostgreSQL                          Redis                             │
	  │  • Persistance complète              • Pub/Sub inter-process           │
	  │  • Multi-tenant                      • Cache temporaire                │
	  │  • Historique trades                 • Channels:                       │
	  │  • Stratégies & positions            - heartbeat                       │
	  │                                       - webhook_raw                    │
	  │                                       - exchange_requests/responses    │
	  │                                       - websockets                     │
	  └─────────────────────────────────────────────────────────────────────────┘
	  ```
- ### 3.1 Le Service Heartbeat (Terminal 2) - Le Cœur du Système
  
  Le **Heartbeat** est le service le plus fondamental. Il fonctionne comme le métronome de l'application, captant le rythme du marché et le propageant à l'ensemble du système.
  
  * **Fonctionnement détaillé** :
	- 1.**Connexion Directe à Binance** : Au démarrage, le script `run_heartbeat.py` établit une connexion WebSocket **native** avec Binance. Ce choix est stratégique : il garantit la plus faible latence possible et une indépendance totale vis-à-vis de toute librairie tierce pour cette tâche vitale.
	- 1. **Signaux Multi-Timeframe** : Le service ingère le flux continu de transactions et les agrège en temps réel pour construire des bougies OHLCV sur les unités de temps suivantes : **1m, 3m, 5m, 10m, 15m, 1h, 2h, 4h**.
	  2. **Double Diffusion via Django Channels** :
	  
	  * **Canal `StreamBrut`** : Chaque message brut reçu de Binance est immédiatement publié sur ce canal. Son seul but est de permettre à l'interface `Heartbeat` d'afficher le Stream brut en temps réel à l'utilisateur pour un simple but de contrôle de fonctionnement.
	  * **Canal `Heartbeat`** : C'est le canal le plus important. Dès qu'une bougie (pour n'importe quelle timeframe) est clôturée, un message structuré (un "signal") est envoyé sur ce canal. C'est ce signal qui déclenchera les actions du Moteur de Trading. Ce signal est simplement "1m, 3m, 5m, 10m, 15m, 1h, 2h, 4h".
	    4.**Persistance des Données** : Chaque bougie clôturée est systématiquement enregistrée dans la table `candles_Heartbeat` de la base de données PostgreSQL et les dates/heure/min du démarrage et de l'arrêt de l'application aristobot dans la table  `heartbeat_status`,
	  * **Rôle** : Fournir un flux constant et fiable de signaux.
	  * **Backend** :
	  
	  * Au démarrage de l'application, enregistre dans la table `heartbeat_status`,  `last_ApplicationStart` la date/heur/min du système
	  * A l'arrêt de l'application, enregistre dans la table `heartbeat_status`,  `last_ApplicationStop`  la date/heur/min du système
	  * S'abonne aux channels `StreamBrut` et `Heartbeat` pour relayer les informations au frontend via WebSocket.
	  * `StreamBrut` -> Publie les données brute reçue du websocket de Binance
	  * `Heartbeat` ->  Publie Le signal (1min, 5min, etc.) et la date/heure/min du traitement
	  * Enregistre dans la DB `Candles_Heartbeat` Les données traitées
	  * **A implémenter plus tard...**
	  
	    * Vérifie la cohésion du Stream `Heartbeat` en vérifiant qu'il ne manque pas de bougies depuis le lancement de l'application. -> A implémenter plus tard
	  * **Frontend** : Visualiser l'état du service Heartbeat.
	  
	  * Affiche le flux de données `StreamBrut` brutes en temps réel dans une liste défilante de 60 lignes nommée "Stream Temps Reel". Le but est simplement de voir le stream passer, pour le plaisir...
	  * Publie en temps réel le signal `Heartbeat`  + AA.MM.DD_HH:MM  dans des case pour chaque timeframe. Les cases sont des listes défilante qui affichent les 20 derniers éléments visibles sur 60, le plus récent en haut. A l'initialisation, les cases sont alimentées par les 60 données les plus récentes lue de la  DB `Candles_Heartbeat` , ces lignes sont affichées en orange, puis dès que les signaux arrivent sur `Heartbeat`, ils sont affiché en premier de la liste et en vert
	  * **DB** :
	  * Lecture de la table `heartbeat_status` pour afficher l'état de connexion du service.
	  * Enregistre dans la table `candles_Heartbeat` l'`ìd` de `hertbeat_status`, la date/heure/minute de l'enregistrement `DHM-RECEPTION`, la date/heure/minute de la bougie reçue `DHM-CANDLE`, le type de signal publié `SignalType` ("1m, 3m, 5m, 10m, 15m, 1h, 2h, 4h")
	  * Enregistre dans la table `hertbeat_status` `last_ApplicationStart` et  `last_ApplicationStop`
- ### 3.2 Le Cerveau : Le Moteur de Trading (Trading Engine - Terminal 3)
  Le **Trading Engine** est le service qui prend les décisions. Il est totalement réactif et ne fait rien tant qu'il n'est pas stimulé par le Heartbeat.
  
  **Rôle** : Évaluer les stratégies et exécuter les ordres de trading.
  
  **Workflow détaillé** :
  
  1. **Initialisation au démarrage** : Le Trading Engine utilise le Service  **Exchange Gateway centralisé** (Terminal 5) pour toutes les interactions avec les Exchanges
  2. **À l'écoute du Cœur** : Le service `run_trading_engine.py` est abonné au canal `Heartbeat` et attend passivement les signaux.
  3. **Réaction au Signal** : Le moteur consulte la table `active_strategies` en base de données pour trouver toutes les stratégies qui correspondent aux critères du signal :
    * La stratégie est-elle active (`is_active = True`) ?
    * La date/heure actuelle est-elle dans la plage de validité (entre `start_date` et `end_date`) ?
    * L'unité de temps de la stratégie correspond-elle à celle du signal (ex: `15m`) ?
  4. **Exécution de la Logique** : Pour chaque stratégie correspondante, le moteur :
   * A) Récupère les toutes les bougies à la stratégie par l'**Exchange Gateway centralisé** (Terminal 5)**
   * B) Chargement dynamique de la stratégie:
     * Charge le code Python de la stratégie depuis la table `strategies`, puis l'exécute en mémoire via `exec()` dans un **espace de noms local isolé** (ex. un dictionnaire temporaire de type `local_vars`). Cette isolation garantit que le code de l'utilisateur n'interfère pas avec les variables du moteur lui-même.
     * Une fois le code exécuté, le moteur **parcourt les objets définis** dans cet espace local pour identifier, à l'aide de `issubclass`, la classe qui hérite de la base `Strategy`. Cette classe devient alors la stratégie active
   * C) Le moteur instancie dynamiquement cette classe, en lui passant les données nécessaires (`candles`, `balance`, etc.). L'instance obtenue expose alors les méthodes de décision (`should_long()`, `should_short()`, etc.), qui peuvent être appelées directement pour déterminer s'il faut prendre une position ou non.
   * D) Exécute la logique de la stratégie (`should_long()`, etc.).
  5. **Interaction avec les Brokers** : Si une stratégie décide d'ouvrir ou de fermer une position, le moteur utilise l'**Exchange Gateway Centralisé**  pour communiquer avec le broker de l'utilisateur et passer les ordres (y compris les Stop Loss et Take Profit).
  6. **Surveillance Continue** : Indépendamment des signaux, le moteur vérifie également à intervalle régulier (toutes les minutes) l'état des trades ouverts pour s'assurer que les TP/SL n'ont pas été atteints
  7. **Gestion Concurrente** : Grâce à `asyncio`, si un signal déclenche 10 stratégies en même temps, le moteur peut les traiter de manière quasi-simultanée, évitant ainsi tout goulot d'étranglement.
- ##### **Heartbeat  a été intégré dans `apps/core` (voir -> 3.1) lors de l'implémentation initiale**
  
  * **Service** : `apps/core/management/commands/run_heartbeat.py`
  * **Modèles** : `HeartbeatStatus` dans `apps/core/models.py`
  * **Consumer** : WebSocket dans `apps/core/consumers.py`
- ### **3.3 Architecture Exchange Gateway (Terminal 5) - Service Centralisé via Redis**

	  ⚠️ **ARCHITECTURE DÉTAILLÉE** : Voir [Terminal5_Exchange_Gateway.md](_bmad-output/planning-artifacts/Terminal5_Exchange_Gateway.md) pour documentation complète avec décisions Party Mode (2026-01-21)

	- **L'Exchange Gateway Centralisé** (Terminal 5) est le hub unique pour toutes les interactions avec les exchanges. Il garantit une utilisation optimale des connexions et le respect strict des rate limits.

	  **Principe de fonctionnement :**
	  
	  * **Service dédié** : Processus indépendant qui maintient toutes les connexions aux exchanges
	  * **Option B : 1 instance par type d'exchange** : Dictionnaire `{'bitget': BitgetClient, 'binance': BinanceClient}` avec injection dynamique credentials
	  * **Communication Redis** : Interface standardisée via channels Redis
	- `exchange_requests` : User Account/Trading Manual → Terminal 5
	- `exchange_responses` : Terminal 5 → services clients
	  * **Architecture hybride** : CCXT métadonnées (catalogue exchanges) + Exchange Gateway natif (toutes connexions réelles)
- #### **FICHIERS CONSTITUTIFS**
  1. Fichier Principal de Service
	- backend/apps/core/management/commands/run_exchange_service.py
		- Rôle : Point d'entrée du service (commande Django)
		- Fonction : Boucle principale d'écoute des requêtes Redis
		- Handlers : 11 types de requêtes (balance, ordres, tickers, etc.)
		  
		  1. Gestionnaire Exchange Gateway
	- backend/apps/core/services/exchange_manager.py
		- Rôle : Singleton pour gérer les instances d'exchanges
		- Fonction : Création/réutilisation des connexions exchanges
		- Optimisation : Préchargement des brokers actifs
		  
		  1. Client Exchange Gateway
	- backend/apps/core/services/exchange_client.py
		- Rôle : Interface de communication pour les autres modules
		- Fonction : Envoi de requêtes au service via Redis
		- Pattern : Request/Response asynchrone avec UUID
		  
		  1. A compléter
		  
		  2. A compléter
- #### **Channels Redis :**
  Communication inter-processus
  
  exchange_requests  : User Account/Trading Manual/Trading Engine/Webhooks/Backtest → Terminal 5
  exchange_responses : Terminal 5 → User Account/Trading Manual/Trading Engine/Webhooks/Backtestheartbeat         : Terminal 2 → Terminal 3 (existant)
  webhook_raw       : Terminal 6 → Terminal 3 (existant)
  websockets        : Tous services → Terminal 1 → Frontend (existant)
- #### **FLUX DE COMMUNICATION:**
  1. heartbeat
	- Publié par : Terminal 2 (Heartbeat)
	- Écouté par : Terminal 3 (Trading Engine)
	- Contenu : Signaux de clôture de bougies (1m, 5m, 15m, etc.)
	  2. webhook_raw
	- Publié par : Terminal 6 (Webhook Receiver)
	- Écouté par : Terminal 3 (Trading Engine)
	- Contenu : Webhooks bruts avec timestamp
	  3. exchange_requests
	- Publié par : User Account (tests), Trading Manual (ordres), Trading Engine (stratégies), Webhooks (signaux), Backtest (données)
	- Écouté par : Terminal 5 (Exchange Gateway)
	- Contenu : Tests connexion, ordres à exécuter, demandes balance/marchés
	  4. exchange_responses
	- Publié par : Terminal 5 (Exchange Gateway)
	- Écouté par : User Account, Trading Manual, Trading Engine, Webhooks, Backtest
	- Contenu : Résultats tests, confirmations ordres, balances, marchés
	  5. websockets
	- Publié par : Tous les terminaux
	- Écouté par : Terminal 1 (Daphne) → Frontend
	- Contenu : Updates temps réel pour l'UI
- #### **Documentation APIs Natives**
    * Bitget API -> https://bitgetlimited.github.io/apidoc/en/spot
    * Binance API -> https://binance-docs.github.io/apidocs/spot/en/
    * KuCoin API -> https://docs.kucoin.com/#general
      
  * **Backend :** Le backend est chargé de mettre a disposition les fonctionnalités broker (Exchange) nécessaire au fonctionnement des applications Django à l'aide des APIs natives des exchanges + CCXT pour métadonnées.
    * **CCXT (métadonnées uniquement)** : `ccxt.exchanges`, `requiredCredentials`, `describe()` - AUCUNE connexion réelle
    * L'**Exchange Gateway** charge les connexions **à la demande** (lazy loading) et maintient un pool des connexions récemment utilisées
    * **Chargement des marchés déplacé vers User Account** : lors de validation broker + bouton "[MAJ Paires]"
    * L'application **4.2. User Account (`apps/accounts`)** utilise _CCXT métadonnées_ + _Terminal 5_ pour tests de connexion et chargement marchés.
    * L'application **4.3. Trading Manuel (`apps/trading_manual`)** utilisent _ExchangeClient_ pour ses opérations. (voir dans la section backend de l'application les besoins)
    * L'application **4.5. Stratégies (`apps/strategies`)** utilise ExchangeClient pour ses opération. (voir dans la section backend de l'application les besoins)
    * L'application **4.7. Webhooks (`apps/webhooks`)** utilise _ExchangeClient_ pour ses opération. (voir dans la section backend de l'application les besoins)
  
  * **Frontend :** 
  * Barre de statut affiche le nombre de marchés chargés **par broker** 
  * **Suppression du status global** "Chargement Service xxx%" (plus de préchargement)
  * **Click sur broker individuel** dans User Account lance mise à jour des marchés
  * **Indicateurs par broker** : "Broker X: 1,247 paires chargées" ou "Chargement..."
    
  * **DB :**
  * Table `exchange_symbols` mise à jour **par broker individuel** depuis User Account
  * **Chargement déclenché** : validation broker OU bouton "[MAJ Paires]"
  * **Granularité fine** : mise à jour par broker au lieu de batch global
- #### **3.3.1 Nouvelles Actions Terminal 5**
  
  Terminal 5 expose de nouvelles actions pour supporter User Account :
  
  * **Action `test_connection`** : Test connexion API keys via clients natifs pour validation broker
  * **Action `load_markets`** : Chargement marchés en arrière-plan avec progression WebSocket  
  * **Communication bidirectionnelle** : Terminal 5 ↔ User Account via Redis + WebSocket
  
  **Détails d'implémentation** : Voir `Aristobot3.1_ExchangeGateway.md`
  
  **Améliorations:**  Ne pas lancer de développement ni de plan…
  * Que faire si les signaux n'arrivent plus ?
  * Les données de marché (`candles`) sont lues localement depuis la base, garantissant des temps de réponse rapides, même pour des fenêtres larges (jusqu'à 200 bougies ou plus). Le solde (`balance`) est quant à lui récupéré en temps réel auprès du broker via API, afin de toujours refléter la réalité à l'instant du signal.
  * Que faire si plus d'une bougie est récupérée pour calculer la stratégie ? Cela veut dire qu'une partie de l'application était plantée ?
  * S'il devait y avoir une incohérence dans la suite des bougies et la plage de date (bougie manquante par ex.), le signaler dans la barre de status et l'enregistrer dans une table d'alerte ? Recharger la plage ? stopper le trading ?
  * 🔄 **Exécution parallèle sécurisée** : Le moteur exécute en parallèle la récupération des bougies via le broker (`A`, avec les APIs natives asynchrones) et le chargement dynamique du code Python de la stratégie depuis la base (`B`, via `exec()` dans un espace isolé). Ces deux opérations étant indépendantes, elles sont lancées simultanément avec `asyncio.gather()`, ce qui réduit significativement la latence. L'instanciation de la stratégie (`C`) n'intervient qu'une fois les deux résultats disponibles. Ce processus est sûr, à condition de gérer les erreurs d'exécution du code utilisateur (via `try/except`) et de veiller à une synchronisation correcte des données.
- ## 4. Description Détaillée des Applications Django
  
  Chaque application Django est un module spécialisé, interagissant avec les autres et la base de données.
- #### 4.1. **User Account (`apps/accounts` - Terminal 1)**
	- **Rôle** : Gérer le compte utilisateur, leurs paramètres de sécurité et leurs configurations personnelles4
	- **Description** :
		- **Gestion des Brokers:** L'interface permettra un CRUD complet des comptes brokers via une **fenêtre modale**. Lors de l'ajout ou de la modification d'un broker, une **vérification de la validité des clés API** sera effectuée en temps réel en tentant une connexion via les APIs natives. Si la connexion réussit, le solde du compte peut être affiché pour confirmation avant de sauvegarder.
		- **Mise à jour des Paires de Trading** : Un bouton "[MAJ Paires de trading]" sera disponible pour chaque broker. Au clic, un processus asynchrone en arrière-plan chargera (via APIs natives) toutes les paires de trading disponibles pour cet exchange et les stockera dans une table partagée. `-> voir 3.3 Architecture Exchange Gateway`. * Les nouveaux brokers ajoutés dans l'application en cours de route depuis "User Account" sont chargés après la vérification du compte.
		- **Configuration IA** : L'utilisateur peut choisir entre "OpenRouter" (nécessitant une clé API) et "Ollama" (avec une URL suggérée par défaut : `http://localhost:11434`). Des interrupteurs ON/OFF permettent d'activer l'un ou l'autre (activer l'un désactive l'autre). Si les deux sont sur OFF, l'assistant IA dans l'application `Stratégies` sera désactivé. Doit permettre la sélection du modèle
		    * **Paramètres d'Affichage** :
		        * **Thème** : Un sélecteur pour basculer entre le mode sombre (obligatoirement avec des couleurs néon) et un mode clair.
		        * **Fuseau Horaire** : Un sélecteur pour afficher toutes les dates et heures de l'application soit en **UTC**, soit dans le **fuseau horaire local** du navigateur. Le choix est stocké dans le profil utilisateur
		        * 
		  * **Backend** :
		    * Gère l'enregistrement de nouveaux Exchanges (Brokers) CRUD.
		    * **Les Exchanges disponibles sont fournis par CCXT** (`ccxt.exchanges`) - métadonnées uniquement
		    * **Les champs requis sont fournis par CCXT** (`exchange.requiredCredentials`) - consultation uniquement
		      ```python
		        import ccxt
		        # Liste des exchanges disponibles
		        exchanges = ccxt.exchanges
		        
		        # Champs requis pour chaque exchange  
		        exchange = ccxt.okx()
		        required_fields = exchange.requiredCredentials
		      ```
		    * **Test de connexion via Terminal 5** (Exchange Gateway centralisé) - connexion réelle avec feedback temps réel
		    * **Chargement des marchés intégré dans User Account** :
		        * **Automatique** : après validation réussie d'un broker (arrière-plan avec WebSocket progression)
		        * **Manuel** : bouton "[MAJ Paires de trading]" par broker individuel
		    * Gère l'enregistrement et l'envoi des préférences utilisateur.
		    * **Note technique** : Architecture hybride - CCXT pour catalogue + Terminal 5 pour connexions + User Account pour gestion marchés
		    
		  * **Frontend** : Fournit les interfaces pour :
		  * Changer son mot de passe.
		  * Gérer ses comptes de brokers (CRUD via une fenêtre modale).
		    * La modale affiche la liste des brokers **fournie par CCXT métadonnées**
		    * Pour la création, modification, la modale affiche les `requiredCredentials` **via CCXT**
		    * **Test de connexion temps réel** avec indicateur de progression et feedback immédiat
		    * **Chargement automatique des marchés** après validation réussie (progression WebSocket)
		  * **Bouton "[MAJ Paires de trading]"** par broker individuel avec progression temps réel
		  * **Bouton "[Par défaut]"** pour définir l'Exchange par défaut proposé dans les autres applications
		  * Définir un broker par défaut.
		  * Configurer la connexion à une IA (OpenRouter ou Ollama) avec clé API/URL et un switch ON/OFF.
		  * Gérer les paramètres d'affichage décrits.
		  * **Capacités Exchange**
		    * Un bouton "Capacités" lance une modale décrivant les capacités de l'Exchange sélectionné, sur chaque ligne d'Exchange
		    
		  * **DB** : Interagit principalement
		    * Table `users` (étendue du modèle Django
		    * Table `brokers`.
		    * Table `exchange_symbols
		    * `
		  * **Script d'Initialisation** : La commande `python manage.py init_aristobot` sera créée. Son unique rôle sera de créer les utilisateurs "dev" et "dac" en base de données pour faciliter le premier lancement.
- #### 4.3. **Trading Manuel (`apps/trading_manual` - Terminal 1)**
  
  * **Rôle** : Permettre à l'utilisateur de passer des ordres manuellement, comme il le ferait sur la plateforme d'un exchange.
  * **Description** :  Le broker par défaut de l'utilisateur est proposé à l'utilisateur. Il peut choisir à l'aide d'une scroll list le broker avec lequel il veut travailler. La zone de saisie de trade sera ergonomique : si l'utilisateur saisit une quantité, la valeur en USD est calculée ; s'il saisit un montant en USD, la quantité d'actifs est calculée. La liste des symboles disponibles sera **filtrée par un dispositif de sélection "USDT (oui/non), USDC (oui/non), Tous(oui/non), fonction de recherche** pour une meilleure utilisabilité.  Dans le cas de "Tous", tous les assets sont disponibles à la recherche.
  
  * **Backend** : Utilise  **Exchange Gateway centralisé** (Terminal 5) pour toutes les interactions avec les exchanges. Effectue tous les calculs, accès DB, accès brokers (Exchange Gateway) nécessaire au fonctionnement du frontend. Communication avec le frontend par Websocket.
  * **Connexion** au broker sélectionné.
  * **Symboles disponibles**
      * Récupère la liste des symboles pour le brocker
      * Réponses aux filtres
  * **Récupération** de la balance et des positions en cours.
      * Utiliser 
  * **Passer un ordre**
      * Passage d'ordres (marché, limite et tous les autres types). Exécution asynchrone pour éviter les timeouts HTTP
  * Récupère le marché depuis **ExchangeClient**
  
  * **Ordres ouverts et ordres fermés**
      * Récupère les ordres ouverts
      * Supprimer des ordres ouverts 
      * Modifier des ordres ouverts
  
  * **Zone Trades récents**
      * Lecture des données directement depuis la DB
        
  * **Note technique** : Utilise **ExchangeClient** (service centralisé)
    
    
  * **Frontend** : Affiche par Websocket les données du Backend. Tous les calculs, validations, accès aux bocker, DB est fait par le Backend.
  * La liste des brokers configurés par l'utilisateur pour choix.
      * Liste box de sélection dans le menu
  * **Zones d'affichage**
      * **Portfolio**
          * Affiche le portefeuille d'actifs avec les totaux du broker sélectionné
          * Affiche la valeur total   
      * **Symboles disponibles**
          * Une zone de sélection de l'asset selon description.
      * **Passer un ordre**
          * avec calcul automatique de la quantité ↔ valeur en USD.
          * Des boutons "Achat" et "Vente".
          * Bouton Valider
          * Bouton Exécuter
          * Cadre _trade-summary_ AU-DESSUS des boutons valider et exécuter (Zone pour afficher différents messages par exemple résumé du trade calculé, message de confirmation de l'Exchange, etc.)
          * Cadre _validation-status_ EN-DESSOUS (statut de validation orange/vert avec timer)
  
      * **Ordres ouverts et fermés**
          * Voir l'historique complet des ordres (ouverts + fermés) via le toggle "Historique"
          * 
          * Bouton "Supprimer" sur chaque lignes d'ordres ouverts
          * Bouton "Modifier" sur chaque lignes d'ordres ouverts
              * Exécution Exchange Gateway en thread séparé avec mise à jour DB automatique
                  * Mode Historique : (30 derniers jours, fix dans le code)
	* Tri automatique par date (plus récent en premier)
	* Chargement intelligent selon le mode sélectionné
	  * Gestion d'état réactive : Variables orderViewMode, closedOrders, ordersLoading
	  * Propriété calculée currentOrdersList : Fusion dynamique des listes d'ordres
	  * Mise à jour automatique : Rechargement des bonnes données après exécution/annulation
	  * **Zone Trades récents**
	  * Afficher AA-MM-JJ HH:MM:SS, Symbole, Type, Side, Quantité, Prix/Trigger, Total, Status, P&L
	  * Ce sont les enregistrements de tous les trades passés. Terminal 5 est le maître d'ouvr pour ces opérations.
	  
	  
	  * **REDIS** : Terminal 5 enregistre chaque transaction manuelle dans la table `trades`. Il est **Important** de renseigner dans le champ adhoc que c'est un "Trade Manuel" et passer un TimeStamp avec le reste de la demande d'exécution d'ordre.
- ##### 4.3.1 Ordre SL, TP, OCO (Rafactoring)
  * **But**: Ajouter les types d'ordres nécessaire au trading. Documentation des APIs natives des exchanges
   
  * **Backend** :Utilise  **Exchange Gateway centralisé** (Terminal 5) pour toutes les interactions avec les exchanges. Effectue tous les calculs, accès DB, accès brokers (Exchange Gateway) nécessaire au fonctionnement du frontend. Communication avec le frontend par Websocket. S'inspirer du code existant, ne pas supprimer de fonctionnalités.
     * Passer un order Stop Loss, en mode asynchrone (non bloquant)
     * Passer un order Take Profit, en mode asynchrone (non bloquant)
     * Passer un order Stop Loss, en mode asynchrone (non bloquant)
       
  * **Fontend**: Refaire la zone "Passer un ordre". Inclure les nouveaux éléments (sans supprimer les actuels), agrandir la colonne de manière à utiliser 50% de l'écran. Les 2 autres colonnes se partagent les 50% restant à part égale (25% chaque une).
     * Sélectionner le type d'ordre à passer (SL, TP, OCO, sans supprimer Market et Limit)
     * Afficher les champs nécessaire en fonction du type d'ordres saisi
       
  * **DB**
    * rien a faire
- #### 4.4. **Trading BOT (`apps/trading_engine` - Terminal 1)**
  
  * **Rôle** : Gère le cycle de vie des stratégies actives. Il ne fait aucun calcul de trading lui-même (c'est le rôle du _Trading Engine_), mais il met à jour la base de données pour que le moteur sache quoi faire.
  * **Description** :
  
  * **Comportement des Boutons** :
    * **Bouton "Stop"** : Cette action est une **désactivation sécurisée**. Elle met à jour la date de fin de la stratégie active à une date passée (`01.01.01`) ET bascule son champ `is_active` à `False`. Si un trade est actuellement ouvert pour cette stratégie, une **boîte de dialogue de confirmation** avertira l'utilisateur avant de procéder.
    * **Bouton "Vendre"** : Déclenche une vente immédiate au prix du marché pour la position ouverte par une stratégie, sans pour autant désactiver la stratégie elle-même.
    * **Bouton "Suspendre" (Amélioration)** : Il est suggéré d'ajouter un bouton pour suspendre temporairement une stratégie (en basculant simplement `is_active` à `False`), ce qui permettrait de la réactiver plus tard sans devoir reconfigurer les dates.
  * **Backend** : Activer, désactiver et surveiller les stratégies de trading automatisées.
  * **Frontend** : Permet à l'utilisateur de :
  
  * Sélectionner une stratégie, un broker, un symbole et une plage de dates de fonctionnement et l'activer par un sélecteur `is_active` à `True`.
  * Voir la liste des stratégies actuellement actives.
  * Visualiser les 10 derniers trades et le P\&L (Profit & Loss) pour chaque stratégie active.
  * **DB** : L'interface principale pour la table `active_strategies` (CRUD). Lit la table `trades` pour afficher l'historique récent.
- #### 4.5. **Stratégies (`apps/strategies` - Terminal 1)**
  
  * **Rôle** : L'atelier de création et de gestion des stratégies de trading.
  * **Description** : L'utilisateur modifie le template de base en ajoutant des conditions a l'aide de fonctions fournie par la librairie Python "Pandas TA Classic" ->  `pip install -U git+https://github.com/xgboosted/pandas-ta-classic`
  * **Template de Base** : Toute nouvelle stratégie sera créée à partir d'un template de base. Ce code sera affiché dans l'éditeur de l'interface.
  
  ```python
  # Template de base pour une nouvelle stratégie
  class MaNouvelleStrategie(Strategy):
      def __init__(self, candles, balance, position=None):
          self.candles = candles
          self.balance = balance
          self.position = position
  
      def should_long(self) -> bool:
          # Décide si on doit acheter
          return False
  
      def should_short(self) -> bool:
          # Pour le futures trading uniquement
          return False
  
      def calculate_position_size(self) -> float:
          # Calcule la taille de la position
          return 0.0
  
      def calculate_stop_loss(self) -> float:
          # Calcule le stop loss
          return 0.0
  
      def calculate_take_profit(self) -> float:
          # Calcule le take profit
          return 0.0
  ```
  
  Exemple d'implémentation par l'utilisateur du croisement EMA 10 / EMA 20
  
  ```
  import pandas_ta as ta
  
  class MaNouvelleStrategie(Strategy):
    def __init__(self, candles, balance, position=None):
        self.candles = candles
        self.balance = balance
        self.position = position
  
        # On suppose que candles est un DataFrame Pandas avec au moins la colonne 'close'
        self.candles["ema10"] = ta.ema(self.candles["close"], length=10)
        self.candles["ema20"] = ta.ema(self.candles["close"], length=20)
  
    def should_long(self) -> bool:
        """
        Buy signal : EMA 10 crosses above EMA 20
        """
        if len(self.candles) < 21:
            return False  # Pas assez de données
  
        ema10_now = self.candles["ema10"].iloc[-1]
        ema10_prev = self.candles["ema10"].iloc[-2]
  
        ema20_now = self.candles["ema20"].iloc[-1]
        ema20_prev = self.candles["ema20"].iloc[-2]
  
        # Croisement haussier : ema10 vient de passer au-dessus de ema20
        return ema10_prev < ema20_prev and ema10_now > ema20_now
  
    def should_short(self) -> bool:
        """
        Sell signal (optionnel pour spot) : EMA 10 crosses below EMA 20
        """
        if len(self.candles) < 21:
            return False
  
        ema10_now = self.candles["ema10"].iloc[-1]
        ema10_prev = self.candles["ema10"].iloc[-2]
  
        ema20_now = self.candles["ema20"].iloc[-1]
        ema20_prev = self.candles["ema20"].iloc[-2]
  
        return ema10_prev > ema20_prev and ema10_now < ema20_now
  
    def calculate_position_size(self) -> float:
        # Par exemple 10% du capital
        return self.balance * 0.1
  
    def calculate_stop_loss(self) -> float:
        # Stop à -2% par exemple
        return 0.02
  
    def calculate_take_profit(self) -> float:
        # TP à +4% par exemple
        return 0.04
  ```
  
  📌 Remarques importantes
  
  * `self.candles` doit être un **DataFrame Pandas** avec une colonne `'close'`.
  * Le croisement est vérifié entre **la bougie précédente** (`iloc[-2]`) et **la bougie actuelle** (`iloc[-1]`).
  * 
  * **Backend** : Gère le CRUD des stratégies. Fournit une fonctionnalité clé : un endpoint d'API qui reçoit le code Python d'une stratégie et le valide syntaxiquement avant de l'enregistrer.
  
  * **Frontend** :
  
  * Affiche la liste des stratégies de l'utilisateur (CRUD).
  * Fournit un éditeur de code pour écrire ou modifier la logique d'une stratégie en Python, basé sur un template prédéfini.
  * Intègre un "assistant IA" qui permet à l'utilisateur de décrire sa logique en langage naturel pour aider à générer le code.
  * Un bouton "Tester la syntaxe" envoie le code au backend pour validation.
  * **DB** : Gère les enregistrements de la table `strategies`.
- #### 4.6. **Backtest (`apps/backtest` - Terminal 1)**
  
  * **Rôle** : Simuler l'exécution d'une stratégie sur des données historiques pour en évaluer la performance potentielle.
  * **Description** : Permet de lancer un backtest en sélectionnant une stratégie, une plage de dates, un symbole, un timeframe et un montant de départ. Affiche les résultats : statistiques de performance (gains, drawdown, etc.) et la liste de tous les trades simulés. Les données de bougies historiques sont dans la `candles` avec le Broker identifié. Ainsi, si d'autres utilisateurs et d'autres stratégies ont besoin de ces données elles sont accessible. Eviter de backtester sur les bougies d'un autre broker que celui sélectionner pour la stratégie. Si les bougies n'existent pas, elles sont chargées avec l'**Exchange Gateway centralisé** (Terminal 5).
  * **Backend** :
  
  * Charge les données de bougies historiques.
  * Exécute la logique de la stratégie sélectionnée sur cette plage de données.
  * Envoie le résultat du test: Nb de trades gagnants perdant, Plus grande perte, Gain/perte total, etc…
  * Envoie la liste des trades avec toutes les données (heure d'achat/vente, calcul du gain, évolution du solde)
  * Envoie des mises à jour en temps réel de progression du test en cours (en %) au frontend via WebSocket.
  * Gère la possibilité de l'interruption du calcul par l'utilisateur
  * Gère la possibilité de l'interruption par l'utilisateur du chargement des bougies
  * Pour les fees -> Documentation des APIs natives des exchanges
  * **Frontend** : Permet à l'utilisateur:
  
  * De sélectionner modifier créer ou effacer une stratégie (Code du template avec assistant IA)
  * De sélectionner le broker, l'asset, le timeframe et la plage de date début/fin et un montant en Quantité
  * De lancer le backtest
  * D'interrompre le backtest
  * D'interrompre le chargement des bougies durant le chargement
  * D'afficher les résultats du backtest (liste des trades et statistiques)
  * **DB** : Lit la table `candles` et enregistre les résultats finaux dans la table `backtest_results`.
- #### 4.7. **Webhooks (`apps/webhooks` - Terminal 1)**
  * **Rôle** : Traiter les signaux de trading reçu de services externes (ex: TradingView) et les exécuter. C'est un point d'entrée alternatif pour l'automatisation.
  
  * **Justification** : Cette application fournit un moyen de déclencher des trades basé sur des **signaux externes**, par opposition aux stratégies qui sont basées sur des **calculs internes**. C'est une distinction fondamentale qui justifie son existence en tant que module séparé. Les applications "Trading Manuel" et "Trading Bot" peuvent accéder au même compte, pour modifier manuellement une position ou par une stratégie de suivi par exemple.
  
  * **Backend** : Utilise  **Exchange Gateway centralisé** (Terminal 5) pour toutes les interactions avec les exchanges. Effectue tous les calculs, accès DB, accès brokers (Exchange Gateway) nécessaire au fonctionnement du frontend. Communication avec le frontend par Websocket. **Toutes les opérations sont faites de manière asynchrone et non bloquante**.
    * **S'abonne au canal** dédié au wenhooks de REDIS et lis les messages fourni par **Service Webhook receiver** (Terminal 6). Les message  "webhook" de Tradingview sont formatés en JSON.
    * **Enregistre** tous les webhooks reçu dans la DB le webhook
    * **Vérifie la cohérence** des webhooks reçus. Le champ `Interval` indique la fréquence attendue. Les webhooks arrivent normalement à la clôture d'une bougie TradingView, et le champ `Action` précise ce qu'il faut faire (ou `PING` si rien). Un signal _Heartbeat_ est publié chaque minute sur Redis, il contient l'heure exacte de la bougie et sert de référence plutôt que l'horloge système. À chaque minute, on regarde si l'heure Redis correspond à un intervalle prévu + 1 minute. Cela évite de tester trop tôt. Exemple : pour un intervalle de 5 minutes, un webhook attendu à 11h15 sera contrôlé à 11h16. Si le webhook est trouvé en DB, tout va bien. Sinon, insérer un enregistrement avec `Action = "MISS"` et l'heure où il aurait dû arriver. Ainsi, on garde une trace complète des webhooks reçus et manquants, et on peut mesurer la gravité des pertes éventuelles. 
    * **Analyse** le message et effectue les opérations en fonction du contenu de **`Action`**. Prépare un ordre pour l'Exchange sélectionné (`UserExchangeID` = `ìd`) en fonction du type d'action envoyée dans le JSON (`Action`) par l'ExchangeClient (Terminal 5)
        * `Action` = PING
            * ne rien faire
        * `Action` = BuyMarket ou SellMarket
            * Ordre au marché, quantité pondérée avec `PourCent`
        * `Action` = BuyLimit, SellLimit
            * Ordre de vente limite, quantité pondérée avec `PourCent`
        * `Action` = MAJ
            * Mise à jours des ordres pour le Take Profit et Stop Loss aux prix respectifs de PrixSL et PrixTP, quantité pondérée avec `PourCent`. Pour cela, effacer les anciens ordres et les remplacer par les nouveaux.
    * **Exécute l'ordre** préparé par ExchangeClient.
    * **Enregistre dans la** DB trade l'ordre passé **_avec_** la réponse `Status_ExchangeClient` reçu de l'exchange
    * **Calculer la vente** (pertes/profit) et mettre à jour la DB trade
        * P\&L réalisé = (Prix vente - Prix moyen achat) × Quantité vendue
        * Se fait lors d'une action vente, limite ou market peu importe la quantité vendue.
        * Met à jours la DB `trade` l'enregistrement en cours avec les résultats des calculs.
    * * **Calculer le trade en cours** (pertes/profit) et mettre à jour la DB trade
        * Un trade complet est constitué de tous les enregistrements entre le premier achat (qui suit une vente à 100%) et une vente à 100%.
        * P\&L réalisé = moyenne des enregistrements constituant le trade. _Voici en exemple:_
            * 10.10.2025, 10h, vente, qunatité 100% -> fermeture de l'ancien trade
            * 10.10.2025, 11h, achat, quantité 66%  -> Ouverture du trade. 66% des USDT disponibles
            * 10.10.2025, 
                    * 
        * Se fait lors d'une action vente, limite ou market.
        * Met à jours la DB `trade` l'enregistrement en cours avec les résultats des calculs.
        
        
    * **Envoyer les données à afficher** au frontend (par websocket) 
        * Pour la zone "**Ordres effectués**", le faire à chaque modification de la DB `trade`
            * Si USTD est le seule asset:
                * on considère qu'il n'y a pas de trade en cours, donc la liste est vide et le front end devra afficher "pas de position ouverte"
            * S'il il y un autre asset,
                * Envoyer toutes les dernières enregistrements de la db `trade` jusqu'à trouver la dernière vente 100%*. Un trade est constitué de tous les enregistrements entre le premier achat (qui suit une vente à 100%) et une vente à 100%.
  
    * Pour la zone "**Webhooks**"
        * A Chaque modification de la DB webhooks, envoyer par websocket les données à afficher au frontend
            * Pour la zone Webhooks reçus
            * 
            * Pour la zone liste des gains
            * Parcourir la table trade, champ
        * Envoyer les données de la zone **"webhooks"** si une pression sur le bouton "WebHookRefresh" du frontent est faite.
        * Envoyer les données de la zone "**Ordres effectués**" si une pression sur le bouton "TradeEnCourRefresh" du frontent est faite.
        * Envoyer les données de la zone webhooks si une pression sur le bouton "WebHookRefresh" du frontent est fait.
  
  * **Frontend** :
    * La transmission des données pour chaques zones se fait par websocket. Le backend envoie les données. Le backend fait les calculs.
    * Zone "**Webhooks**": Affiche un journal des webhooks reçus.
        * Status ExchangeClient, Date, Heure, Min, Exchange, Asset, action, PourCent, Prix, et tous les champs nécessaires au contôle et visualisation. **`Status_ExchangeClient`** est la réponse de l'exchange à l'ordre passé par le backend
        * si `Action` = "MISS" afficher la ligne d'une autre couleur (erreur)
        * Un bouton pour le rafraîchissement des données est affiché (WebHookRefresh)
    * Zone "**Ordres effectués**": Affiche les ordres passés.
        * Affiche la liste des ordres (Date, Heure, Min, `Action` effectuée, Position du TP avec quantité prévue, position du SL avec quantité prévue), montant Gain/Perte. Si la liste est vide, afficher "Pas d'ordres à afficher"
        *  Un bouton pour le rafraîchissement des données est affiché (TradeEnCourRefresh)
  
  * **DB** : Enregistre chaque webhook reçu dans la table `webhooks` et les trades correspondants dans la table `trades`.
  
  
  * **Exemple de webhook JSON** :
  ````
  json\_msg = '{' +
     '"Symbol": "' + syminfo.ticker + '", ' +
     '"Exchange": "' + syminfo.prefix + '", ' +
     '"Currency": "' + syminfo.currency + '", ' +
     '"BaseCurrency": "' + str.tostring(syminfo.basecurrency) + '", ' +
     '"Interval": "' + timeframe.period + '", ' +
     '"Open": ' + str.tostring(open) + ', ' +
     '"High": ' + str.tostring(high) + ', ' +
     '"Low": ' + str.tostring(low) + ', ' +
     '"Close": ' + str.tostring(close) + ', ' +
     '"Volume": ' + str.tostring(volume) + ', ' +
     '"BarTime": ' +  f\_timeIso(time) + ', ' +
     '"Action": ' + Action + ', ' +                              // Type d'action : BuyMarket, SellMarket, BuyLimit, SellLimit, MAJ, PING
     '"Prix": ' +  str.tostring(Prix) + ', ' +                   // Prix auquel placer l'ordre  (BuyMarket, SellMarket, BuyLimit, SellLimit)
     '"PrixSL": ' +  str.tostring(PrixSL) + ', ' +               // Prix pour le stop Loss (ordre limite)
     '"PrixTP": ' +  str.tostring(PrixTP) + ', ' +               // Prix pour le TakeProfit (ordre limite)
     '"PourCent": ' +  str.tostring(PourCent) + ', ' +           // % de quntité à exécuter
     '"UserID": ' +  str.tostring(UserID) + ', ' +               // UserID pour sauveggarder les trades dans la DB
     '"IndicateurName": ' + IndicateurName + ', ' +              // Nom de l'indicateur 
     '"UserExchangeID": ' + str.tostring(exchangeId) + '}'       // UserExchangeID indique quel Exchange utiliser
     
  
  // Exemple pour l'envoi de l'alerte JSON par Tradingview
  alert(json\_msg, alert.freq\_once\_per\_bar\_close)
  ````
- ##### **4.7.1. Evolution future**
  **Ne pas developer maintenant**, ce ne sont que des idées
    * **Test si l'exchange désiré est actif**. Pour cela, vérifier dans la table `brokers`, si le champ `TypeDeTrading` **est égal** à "Webhooks".
    	* **Si c'est le cas**:
        
        * **Si ce n'est pas le cas**, afficher dans la liste des webhooks que l'exchange n'est pas activé !
            * SURTOUT, ne pas passer d'ordres !!!
- #### 4.8. **Statistiques (`apps/stats` - Terminal 1)**
  
  * **Rôle** : Fournir une vue d'ensemble de la performance de trading de l'utilisateur.
  * **Backend** : Agrège les données de la table `trades` pour calculer diverses métriques :
  
  * Évolution globale du solde.
  * Performance par stratégie individuelle.
  * Performance par source de webhook.
  * **Frontend** : Affiche les données sous forme de graphiques et de tableaux de bord, avec la possibilité de filtrer par compte de broker.
  * **DB** : Lit intensivement la table `trades`.
- ## 5. Architecture Détaillée de la Base de Données
  
  Les relations entre les tables sont cruciales pour le bon fonctionnement de l'application. La structure est conçue pour être multi-locataire (_multi-tenant_), où la plupart des données sont isolées par `user_id`.
  
  ```ascii
  +-----------+       +-----------+       +---------------------+
  |   users   |------>|  brokers  |<------|  active_strategies  |
  +-----------+       +-----------+       +---------------------+
      |                   |                         |
      |                   |                         |
      +----------+        +------------------+      |
      |          |                           |      |
      |          +-------------------------->|  trades  |<--+
      |                                      |      |      |
      |                                      +------+      |
      v                                                    |
  +------------+                                         +-----------+
  | strategies |----------------------------------------->| webhooks  |
  +------------+                                         +-----------+
      |                                                      |
      v                                                      v
  +------------------+      +-----------+            +----------------+
  | backtest_results |      |  candles  |            | webhook_trades |
  +------------------+      +-----------+            +----------------+
                                |
                          +-------------+
                          | debug_mode  |  <-- (singleton système)
                          +-------------+
                                |
                        +-----------------+
                        | heartbeat_status|  <-- (monitoring système)
                        +-----------------+
                                |
                        +------------------+
                        | exchange_symbols |  <-- (partagé tous users)
                        +------------------+
  ```
- ### Tables Principales
- #### `users`
  
  * **Description** : Étend le modèle utilisateur standard de Django pour stocker les configurations spécifiques à l'application.
  * **Champs Clés** : `id`, `username`, `password`, `default_broker_id` (FK vers `brokers`), `ai_provider`, `ai_api_key` (chiffré), `display_timezone`.
  * **Relations** : Un utilisateur a plusieurs `brokers`, plusieurs `strategies`, plusieurs `trades`, etc.
- #### `brokers`
  
  * **Description** : Stocke les informations de connexion aux différents comptes de brokers pour chaque utilisateur.
  * **Champs Clés** : `id`, `user_id` (FK vers `users`), `name`, `exchange`, `api_key` (chiffré), `api_secret` (chiffré), `api_password` (chiffré, optionnel), `is_default`, `is_testnet`, `is_active`. `is_active`
  * **Relations** : Liée à un `user`. Un broker peut être associé à plusieurs `active_strategies` et `trades`.
  * **Statut** : ✅ Implémentée
- #### `strategies`
  
  * **Description** : Contient le code source et les métadonnées des stratégies de trading créées par les utilisateurs.
  * **Champs Clés** : `id`, `user_id` (FK vers `users`), `name`, `description`, `code` (texte Python), `timeframe`.
  * **Relations** : Liée à un `user`. Une stratégie peut être utilisée dans plusieurs `active_strategies` et `backtest_results`.
  * **Statut** : 🔄 À implémenter
- #### `active_strategies`
  
  * **Description** : Table de liaison qui représente l'activation d'une `strategy` sur un `broker` pour un `symbol` donné, pendant une période définie.
  * **Champs Clés** : `id`, `user_id` (FK), `strategy_id` (FK), `broker_id` (FK), `symbol`, `timeframe`, `start_date`, `end_date`, `is_active`.
  * **Relations** : Fait le lien entre `users`, `strategies` et `brokers`.
  * **Statut** : 🔄 À implémenter
- #### `candle`
  
  * **Description** : Stocke les données de marché OHLCV. Cette table est partagée mais filtrée par broker\_id.
  * **Champs Clés** : `id`, `broker_id` (FK), `symbol`, `timeframe`, `open_time`, `close_time`, `open_price`, `high_price`, `low_price`, `close_price`, `volume`.
  * **Relations** : Utilisée par le _Heartbeat_, _Backtest_ et _Stratégies_.
  * **Index** : Sur (`broker_id`, `symbol`, `timeframe`, `close_time`) pour performances optimales.
  * **Statut** : 🔄 À implémenter
- #### `candles_HeartBeat`
  
  * **Description** : Stocke les signaux reçu de HeartBeat
  * **Champs Clés** : `id`, `DHM-RECEPTION`, `DHM-CANDLE`, `SignalType`
  * **Relations** : Utilisée par le _Heartbeat_, _Stratégies_.
  * **Index** : Sur (`broker_id`, `symbol`, `timeframe`, `close_time`) pour performances optimales.
  * **Statut** : 🔄 À implémenter
- #### `trades`
  
  * **Description** : Journal central de toutes les transactions exécutées, qu'elles soient manuelles, automatiques ou via webhook.
  * **Champs Clés** : `id`, `user_id` (FK), `broker_id` (FK), `strategy_id` (FK, nullable), `webhook_id` (FK, nullable), `symbol`, `side`, `quantity`, `price`, `status`, `profit_loss`, `source` (manual/strategy/webhook), `Status_ExchangeClient` (Réponse de l'exchange).
  * **Relations** : La table la plus connectée, source principale pour les statistiques.
  * **Statut** : 🔄 À implémenter
- #### `positions`
  
  * **Description** : Positions ouvertes actuelles (déjà dans `core.models`).
  * **Champs Clés** : `id`, `user_id`, `broker_id`, `symbol`, `side`, `quantity`, `entry_price`, `current_price`, `stop_loss`, `take_profit`, `unrealized_pnl`, `status`.
  * **Statut** : ✅ Implémentée
- #### `webhooks`
  
  * **Description** : Enregistre chaque appel webhook reçu pour traçabilité et débogage.
  * **Champs Clés** : `id`, `user_id` (FK), `source`, `payload` (JSON), `processed`, `created_at`, `Status_ExchangeClient`.
  * **Relations** : Liée à un `user` et peut générer des `trades`.
  * **Statut** : 🔄 À implémenter
- #### `backtest_results`
  
  * **Description** : Stocke les résultats synthétiques de chaque simulation de backtest.
  * **Champs Clés** : `id`, `user_id` (FK), `strategy_id` (FK), `broker_id` (FK), `symbol`, `timeframe`, `start_date`, `end_date`, `initial_amount`, `final_amount`, `total_trades`, `winning_trades`, `losing_trades`, `max_drawdown`, `sharpe_ratio`, `trades_detail` (JSON).
  * **Relations** : Liée à `users`, `strategies` et `brokers`.
  * **Statut** : 🔄 À implémenter
- #### `heartbeat_status`
  
  * **Description** : Une table simple pour surveiller l'état du service Heartbeat.
  * **Champs Clés** : `ìd`, `is_connected`, `last_ApplicationStart`, `last_error`, `symbols_monitored` (JSON).
  * **Relations** : Aucune. Table de monitoring interne.
  * **Statut** : ✅ Implémentée
- #### `debug_mode`
  
  * **Description** : Singleton pour gérer l'état du mode développement.
  * **Champs Clés** : `id` (toujours 1), `is_active`, `updated_at`.
  * **Relations** : Aucune. Configuration système.
  * **Statut** : ✅ Implémentée
- #### `exchange_symbols`
  
  * **Description** : Liste des symboles/marchés disponibles par exchange (table partagée).
  * **Champs Clés** : `exchange`, `symbol`, `base`, `quote`, `active`, `type` (spot/future), `min_amount`, `max_amount`, `price_precision`.
  * **Relations** : Aucune. Données de référence partagées.
  * **Index** : Sur (`exchange`, `active`) et (`symbol`).
  * **Statut** : ✅ Implémentée
- ### Précisions sur les Tables et Relations
  
  * **Multi-tenant** : Toutes les données utilisateur sont isolées par `user_id`. Seules `exchange_symbols`, `heartbeat_status` et `debug_mode` sont partagées.
  * **Chiffrement** : Les clés API dans `brokers` et `users` sont chiffrées avec Fernet + SECRET\_KEY Django.
  * **Cascade** : La suppression d'un user supprime en cascade ses brokers, strategies, trades, etc.
  * **Performance** : Index stratégiques sur les champs de filtrage fréquents (user\_id, broker\_id, symbol, timeframe).
  * **`users`** : En plus des champs standards, elle contiendra `display_timezone` ('UTC' ou 'Europe/Paris', par exemple) et les configurations de l'IA.
  * **`brokers`** : Le champ `exchange` sera un choix restreint basé sur les exchanges supportés nativement.
  * **`trades`** : C'est la table la plus importante pour l'analyse. Les champs `strategy_id` et `webhook_id` sont `nullable=True` pour permettre d'enregistrer les trades manuels qui ne proviennent d'aucune automatisation. Un historique complet de **toutes les tentatives de trades, y compris les échecs**, sera conservé pour le débogage.
  * **`candles`** : C'est une table de données brutes, optimisée pour des lectures rapides. Des **index** sur (`symbol`, `timeframe`, `close_time`, `broker_id`) seront cruciaux pour les performances des backtests. Le broker doit être identifié par son propre champ
  * **`active_strategies`** et **`strategies`** : Il est clair que `strategies` est le "modèle" (le code), et `active_strategies` est "l'instance en cours d'exécution" de ce modèle avec des paramètres concrets (broker, symbole, dates).
- ## 6. Points Non Classés et Futurs Développements
  
  Cette section regroupe les idées et les points de discussion qui n'ont pas encore été pleinement intégrés dans le plan de développement initial mais qui doivent être conservés pour référence future.
  
  * **Cohérence du Heartbeat** : L'idée d'une vérification de la "cohésion" des bougies reçues a été mentionnée. Cela pourrait impliquer de vérifier la régularité des timestamps des bougies stockées en base de données pour détecter d'éventuelles interruptions du service. À développer ultérieurement.
  * **Gestion Avancée du Mode Testnet** : Les APIs natives supportent les environnements de test (sandbox) pour certains brokers. Il faudra explorer comment gérer les cas où un broker n'offre pas de mode testnet. L'interface pourrait désactiver le switch "Testnet" pour ce broker ou afficher un avertissement clair. *La gestion du mode Testnet pour les brokers qui ne le supportent pas reste à définir. La solution la plus simple pour une V1 serait de désactiver le switch "Mode Testnet" sur l'interface si les capacités de l'exchange ne le supportent pas. C'est une approche pragmatique qui correspond à la philosophie du projet.
  * **Partage de Stratégies** : L'idée d'un système de partage de stratégies entre utilisateurs a été évoquée. Cela nécessiterait des modifications importantes du modèle de données (ex: table de liaison, permissions) et est considéré comme une fonctionnalité pour une version future.
  * **Gestion des Positions Ouvertes** : Il pourrait être pertinent d'ajouter une table dédiée `positions` pour suivre l'état actuel d'un trade ouvert (quantité, prix d'entrée, P\&L latent) plutôt que de le déduire de la table `trades`. C'est un point d'amélioration de l'architecture à considérer.
  
  * **#### 4.2.02 Paramètre websocket/Stratégie/OFF (`apps/auth_custom`)**
    * **Rôle** : Possibilité d'activer/désactiver le compte Exchange pour le mode  Webhook ou Stratégie ou OFF. Le trading Manuel doit toujours être possible (modifier les trades automatiques) sauf sur OFF. L'application Stratégie l'utilise si `TypeDeTrading`="Stratégie". L'application "Webhooks" ne l'utilise que si `TypeDeTrading`="Webhooks". L'application "Trading Manuel" ne l'utilise pas si `TypeDeTrading`="OFF"
    * **Backend** :
      * Enregistre les paramètre dans la DB 
    * **Frontend** :
        * Sur chaque ligne Exchange, une sélectbox affiche les  possibilités. Par défaut initialiser sur "
    * **DB** :
        * Tenir à jours le champ `TypeDeTrading` de la table `brokers`
            * Valeurs possibles: "OFF" ou "Stratégie" ou "Webhooks".
- ### 6.5. **Architecture Haute Disponibilité : Redondance Heartbeat et Redis**
  
  Cette section décrit une évolution future possible pour transformer Aristobot3.1 en système ultra-résilient, en conservant l'esprit "vibe coding" mais avec une robustesse de niveau professionnel.
- #### **Concept : Dual-Heartbeat pour Continuité Garantie**
  
  Le service **Heartbeat étant critique** (source unique des signaux de marché), une panne réseau ou serveur provoque l'arrêt complet du trading. La solution : **2 services Heartbeat indépendants** sur des infrastructures séparées.
  
  **Principe** :
- **Heartbeat-Primary** : Service principal sur serveur/réseau 1
- **Heartbeat-Secondary** : Service de secours sur serveur/réseau 2
- **Déduplication intelligente** dans le Trading Engine pour éviter les ordres doublons
- #### **Architecture Redondante Complète**
  
  ```ascii
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │                              INFRASTRUCTURE REDONDANTE                                  │
  └─────────────────────────────────────────────────────────────────────────────────────────┘
  
    VPS OVH Gravelines (Datacenter 1)          VPS OVH Strasbourg (Datacenter 2)
   ┌─────────────────────────────────┐        ┌─────────────────────────────────┐
   │  Terminal A1: Heartbeat-Primary │        │  Terminal B1: Heartbeat-Secondary│
   │  Terminal A2: Redis-Primary     │        │  Terminal B2: Redis-Secondary   │
   │  Terminal A3: Exchange-Gateway  │        │  Terminal B3: Exchange-Backup   │
   │  Terminal A4: Trading Engine    │        │  Terminal B4: (Standby)         │
   │  Terminal A5: Frontend          │        │  Terminal B5: (Standby)         │
   └─────────────────────────────────┘        └─────────────────────────────────┘
              │                                              │
          Fibre Orange                                   Fibre Free
              │                                              │
              └──────────────── BINANCE ───────────────────┘
                            WebSocket API
                        
   ┌─────────────────────────────────────────────────────────────────────────────────────┐
   │                              COMMUNICATION REDIS                                    │
   │  • heartbeat_primary    (Serveur 1 → Trading Engine)                              │
   │  • heartbeat_secondary  (Serveur 2 → Trading Engine)                              │
   │  • exchange_requests   (Trading Engine → Exchange Gateway)                        │
   │  • exchange_responses  (Exchange Gateway → Trading Engine)                        │
   │  • websockets          (Tous → Frontend) [existant]                              │
   └─────────────────────────────────────────────────────────────────────────────────────┘
  ````
- #### **Gestion de la Déduplication des Signaux**
  
  **Problématique** : Les 2 services Heartbeat vont publier les mêmes signaux avec quelques millisecondes d'écart.
  
  **Solution** : Chaque signal inclut un **ID unique** basé sur le timestamp exact de clôture de bougie :
  
  ```python
  # Format des signaux Heartbeat redondants
  signal_primary = {
    'timeframe': '5m',
    'timestamp': '2025-08-12T14:32:15.000Z',
    'candle_close_time': 1723474335000,  # Timestamp bougie Binance (unique)
    'source': 'primary',
    'signal_id': f"5m_{1723474335000}",  # ID unique pour déduplication
    'server_location': 'gravelines'
  }
  
  signal_secondary = {
    'timeframe': '5m', 
    'timestamp': '2025-08-12T14:32:15.067Z',  # 67ms plus tard
    'candle_close_time': 1723474335000,       # MÊME timestamp bougie
    'source': 'secondary',
    'signal_id': f"5m_{1723474335000}",       # MÊME ID → sera ignoré
    'server_location': 'strasbourg'
  }
  ```
  
  **Logique dans Trading Engine** :
  
  ```python
  # Déduplication + failover automatique
  processed_signals = set()
  last_primary_signal = time.time()
  
  async def handle_heartbeat_signal(signal):
    signal_id = signal['signal_id']
    source = signal['source']
  
    # Déduplication
    if signal_id in processed_signals:
        logger.debug(f"⏭️ Signal déjà traité: {signal_id}")
        return
  
    # Traitement du signal
    processed_signals.add(signal_id)
  
    if source == 'primary':
        last_primary_signal = time.time()
        logger.info(f"📊 Signal PRIMARY: {signal['timeframe']}")
    else:
        # N'utiliser secondary QUE si primary silent depuis >30s
        if time.time() - last_primary_signal > 30:
            logger.warning(f"🔄 FAILOVER! Signal SECONDARY: {signal['timeframe']}")
        else:
            logger.debug(f"⏭️ Secondary ignoré (primary actif)")
            return
  
    # Exécuter les stratégies
    await process_trading_strategies(signal)
  ```
- #### **Scénarios de Résilience**
  
  **1. Fonctionnement Normal** :
  
  ```
  ✅ Primary publie signal → Trading Engine traite
  ⏭️ Secondary publie signal → Trading Engine ignore (déjà traité)
  ```
  
  **2. Panne Serveur 1** :
  
  ```
  ❌ Primary silent depuis 35s
  🔄 Secondary publie signal → Trading Engine bascule automatiquement  
  ✅ Trading continue sans interruption
  ```
  
  **3. Panne Réseau Serveur 1** :
  
  ```
  ❌ Primary perd connexion Binance
  ✅ Secondary (autre FAI) maintient connexion
  🔄 Failover automatique en 30s
  ```
  
  **4. Panne Redis Primary** :
  
  ```
  ❌ Redis-Primary plante
  🔄 Configuration pointe vers Redis-Secondary
  ✅ Communication rétablie automatiquement
  ```
- #### **Implémentation Progressive**
  
  **Phase 1 : Redis Dual (Simple)**
  
  ```bash
  # Serveur 1
  docker run -d --name redis-main -p 6379:6379 redis:alpine
  
  # Serveur 2  
  docker run -d --name redis-backup -p 6379:6379 redis:alpine \
    redis-server --slaveof SERVEUR1_IP 6379
  ```
  
  **Phase 2 : Heartbeat Dual (Module additionnel)**
  
  * Dupliquer `run_heartbeat.py` → `run_heartbeat_secondary.py`
  * Ajouter `source: 'secondary'` dans les signaux
  * Modifier Trading Engine pour gestion dual-source
  
  **Phase 3 : Exchange Gateway Dual (Paranoia mode)**
  
  * Exchange Gateway backup sur serveur 2
  * Load balancing automatique
- #### **Monitoring Vibe DevOps**
  
  **Dashboard Simple** (ajout à la barre de statut) :
  
  ```
  🟢 Heartbeat Primary: ACTIF (67ms)
  🟡 Heartbeat Secondary: ACTIF (134ms) 
  🟢 Redis Primary: ACTIF
  🟢 Redis Secondary: SYNC (2ms lag)
  🟢 Exchange Gateway: 5 brokers chargés
  ```
  
  **Alerting Discord** :
  
  ```python
  if primary_down_since > 30:
    webhook_discord("🚨 FAILOVER: Heartbeat Primary DOWN, Secondary prend le relais")
  
  if both_heartbeat_down:
    webhook_discord("🔥 ALERTE CRITIQUE: Tous les Heartbeat DOWN - TRADING ARRÊTÉ")
  ```
- #### **Coût Total Architecture Redondante**
  
  **Infrastructure** :
  
  * **2 VPS OVH** : 6€/mois
  * **2 connexions internet différentes** : Inclus
  * **Surveillance Uptime Kuma** : Gratuit
  * **Webhook Discord** : Gratuit
  
  **Temps de développement** :
  
  * Redis dual : **2h**
  * Heartbeat dual : **4h**
  * Monitoring : **2h**
  * **Total : 1 weekend** ☕
- #### **Résultat Final**
  
  **Aristobot3.1 Redondant** :
  
  * ✅ **Résiste** aux pannes serveur, réseau, FAI
  * ✅ **Continuité trading** garantie 99.9%
  * ✅ **Zero maintenance** en fonctionnement normal
  * ✅ **Garde l'esprit vibe coding** : pas de Kubernetes, juste Docker + Redis
  * ✅ **Monitoring fun** : Discord notifications + dashboard simple
  
  **Philosophy** : _"2 servers, 2 connections, 0 downtime, 1 weekend of work"_ 🎯
  
  _**Note** : Cette architecture représente l'évolution naturelle d'Aristobot3.1 vers un système professionnel tout en conservant sa simplicité de développement et de maintenance._
- ## 7. Instructions pour le Développement avec l'IA
- ### Fichier `.claude-instructions`
  
  Ce fichier à la racine du projet est tenu à jour et contient les directives pour guider l'IA :
- ### Prompt Type
  
  ```
  Contexte : Aristobot3, App [Nom de l'app]
  Objectif : [Ce que doit faire la fonctionnalité]
  Logique Backend : [Endpoints, modèles, services]
  Interface Frontend : [Composants Vue, style attendu]
  Contraintes : [Limites techniques, ex: utiliser l'Exchange Gateway Service]
  ```