# GUIDE DU DEVELOPPEUR : Aristobot V3

## 1. Philosophie et Cadre du Projet

Aristobot V3 est un bot de trading de cryptomonnaies personnel, développé sous une philosophie pragmatique de **"vibe coding"**.

* **Principes Directeurs** :
    * **Fun > Perfection** : Le plaisir de développer prime sur la perfection technique.
    * **Shipping > Process** : Livrer des fonctionnalités fonctionnelles rapidement.
    * **Pragmatique > Enterprise** : Des solutions simples pour un projet à échelle humaine.
    * **Itération Rapide** : Des cycles de développement courts pour un feedback immédiat.

* **Limites et Contraintes Fondamentales** :
    * **Utilisateurs** : Strictement limité à 5 utilisateurs.
    * **Stratégies** : Limité à 20 stratégies actives simultanément.
    * **Environnement de Développement** : Conda avec Python 3.11, en utilisant VS Code et des assistants IA.
    * **Stack Technique** : L'architecture est **non négociable**.
        * **Backend** : Django 4.2.15 + Django Channels
        * **Frontend** : Vue.js 3 (Composition API uniquement)
        * **ServeurASGI:** Daphne
        * **Base de Données** : **PostgreSQL est la source de vérité unique** pour toutes les données. MongoDB est formellement exclu.
        * **Communication Temps Réel** : Redis (pour Django Channels)
    * **Librairies Python** :
        * Analyse Technique: **Pandas TA Classic - A Technical Analysis Library in Python 3** (https://github.com/xgboosted/pandas-ta-classic)
        * Accès aux marchés (Brocker) **CCXT – CryptoCurrency eXchange Trading Library** (https://github.com/ccxt/ccxt)
    * **Parallélisme** : Les calculs concurrents (notamment pour les stratégies) seront gérés exclusivement par **`asyncio`**. L'utilisation de Celery est exclue pour rester simple.
    * **Gestion des Instances CCXT** : Une approche **singleton** sera utilisée. Un service centralisé en mémoire (ex: un dictionnaire global dans `apps/core/services/ccxt_manager.py`) gardera une seule instance de connexion par `user_id` et `broker_id` pour respecter les recommandations de CCXT et gérer efficacement les **rate limits**.
    * **Validation des Données** : La validation se fera à la fois côté client (pour une meilleure expérience utilisateur) et côté serveur via les **serializers Django Rest Framework** (pour la sécurité et l'intégrité).
    * **Format des Erreurs** : Les messages d'erreur retournés par l'API seront **techniques et en français** (ex: "Erreur de connexion à Binance : Invalid API Key"), pour faciliter le débogage.
    * **Les clés API doivent être chiffrées**, en utilisant la `SECRET_KEY` de Django comme clé de chiffrement pour plus de simplicité.
    * 
### Structure des Fichiers

```
Aristobot3/
├── backend/
│   ├── aristobot/              # Configuration Django principale
│   │   ├── settings.py, urls.py, asgi.py, routing.py
│   ├── apps/
│   │   ├── core/              # Services partagés, Heartbeat, Mixins
│   │   │   ├── management/commands/
│   │   │   │   └── run_heartbeat.py
│   │   │   ├── consumers.py   # WebSocket publishers
│   │   │   └── models.py
│   │   ├── accounts/          # Gestion utilisateurs
│   │   ├── brokers/           # Gestion des brokers
│   │   ├── market_data/       # Stockage des bougies et symboles
│   │   ├── strategies/        # CRUD des stratégies
│   │   ├── trading_engine/    # Logique d'exécution des trades
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
├── .env.example
├── .gitignore
├── .claude-instructions
└── README.md
```
## 2. Expérience Utilisateur (Frontend)

### Layout Global

* **Structure** : Une barre latérale (**Sidebar**) fixe à gauche, un bandeau supérieur (**Header**) fixe contenant la barre de statut, et une zone principale de contenu scrollable.

* **Menu Principal** (dans la Sidebar) :

  * Heartbeat
  * Trading manuel
  * Trading BOT
  * Stratégies
  * Backtest
  * Webhooks
  * Statistiques
  * Mon Compte

* **Barre de Statut** (dans le Header) :

  * **Heartbeat Actif/Inactif** : Une pastille visuelle (verte/rouge).
  * **Heartbeat Cohérent/Non Cohérent** : Indicateur de la régularité des données (à développer ultérieurement).
  * **Stratégies Live** : Indique si une ou plusieurs stratégies sont en cours d'exécution.
  * **Mode Testnet** : Affiche un avertissement visuel (couleur inversée, bordure rouge) si le mode Testnet est activé.

### Design System

* **Style Général** : Thème sombre "crypto" inspiré de Binance/TradingView. Utilisation de **cards avec fond sombre et une subtile bordure luminescente**.

* **Couleurs Néon** :

  * `#00D4FF` (Bleu Électrique - Primaire)
  * `#00FF88` (Vert Néon - Succès)
  * `#FF0055` (Rouge Trading - Danger)

* **Responsive** : "Desktop first", l'UI est optimisée pour des grands écrans.

## 3. Démarrage et Architecture des Services

L'application est conçue pour fonctionner comme un écosystème de services interdépendants qui démarrent indépendamment et communiquent entre eux.

### Processus de Lancement : La "Checklist de Décollage"

Pour que l'application soit pleinement opérationnelle, **quatre terminaux distincts** doivent être lancés.
Ces services forment l'épine dorsale de l'application et fonctionnent en arrière-plan, indépendamment de la présence d'un utilisateur connecté à l'interface web.

1. **Terminal 1 : Serveur Web + WebSocket (Daphne)**

   * **Commande** : `daphne aristobot.asgi:application`
   * **Rôle** : C'est le serveur principal. Il gère toutes les requêtes HTTP (pour l'API REST et le service des pages web) et maintient les connexions WebSocket ouvertes avec les clients (navigateurs). C'est la porte d'entrée de toute l'application.

2. **Terminal 2 : Service Heartbeat (Tâche de gestion Django)**

   * **Commande** : `python manage.py run_heartbeat`
   * **Rôle** : Le "cœur" du système. Ce service se connecte directement au flux WebSocket de Binance pour écouter les données du marché en temps réel. Il est totalement indépendant et fonctionne en continu.

3. **Terminal 3 : Moteur de Trading (Tâche de gestion Django)**

   * **Commande** : `python manage.py run_trading_engine`
   * **Rôle** : Le "cerveau" du système. Ce service écoute les signaux émis par le _Heartbeat_ et prend les décisions de trading en exécutant la logique des stratégies actives.

4. **Terminal 4 : Frontend (Vite)**

   * **Commande** : `npm run dev`
   * **Rôle** : Sert l'interface utilisateur développée en Vue.js. C'est ce que l'utilisateur voit et avec quoi il interagit dans son navigateur. Elle se connecte au serveur Daphne (Terminal 1) via WebSocket pour recevoir les données en temps réel.

```ascii
      Terminal 1                      Terminal 2                         Terminal 3                       Terminal 4
+-----------------------+     +--------------------------+      +--------------------------+      +-----------------------+
|  > daphne ...         |     |  > python manage.py      |      |  > python manage.py      |      |  > npm run dev        |
|                       |     |    run_heartbeat         |      |    run_trading_engine    |      |                       |
|   SERVEUR WEB & WSS   |     |                          |      |                          |      |   INTERFACE UTILISATEUR |
|   (Le standardiste)   |     |    HEARTBEAT SERVICE     |      |    TRADING ENGINE        |      |   (Le cockpit)          |
+-----------------------+     +--------------------------+      +--------------------------+      +-----------------------+
           ^                             |                                  |                                 ^
           |                             | (Publie sur Redis)               | (Écoute Redis)                  |
           +-----------------------------+----------------------------------+---------------------------------+
                                         |
                                  +----------------+
                                  |     REDIS      |
                                  | (Le système    |
                                  |    nerveux)    |
                                  +----------------+
```

### 3.1 Le Cœur du Système : Le Service Heartbeat

Le **Heartbeat** est le service le plus fondamental. Il fonctionne comme le métronome de l'application, captant le rythme du marché et le propageant à l'ensemble du système.

*   **Rôle** : Fournir un flux constant et fiable de signaux.
*   **Fonctionnement détaillé** :
    1.  **Connexion Directe à Binance** : Au démarrage, le script `run_heartbeat.py` établit une connexion WebSocket **native** avec Binance. Ce choix est stratégique : il garantit la plus faible latence possible et une indépendance totale vis-à-vis de la librairie CCXT pour cette tâche vitale.
    2.  **Signaux Multi-Timeframe** : Le service ingère le flux continu de transactions et les agrège en temps réel pour construire des bougies OHLCV sur les unités de temps suivantes : **1m, 3m, 5m, 10m, 15m, 1h, 2h, 4h**.
    3.  **Double Diffusion via Django Channels** :
        *   **Canal `StreamBrut`** : Chaque message brut reçu de Binance est immédiatement publié sur ce canal. Son seul but est de permettre à l'interface `Heartbeat` d'afficher l'activité du marché en temps réel à l'utilisateur pour un simple but de contôle de fonctionnement.
        *   **Canal `Heartbeat`** : C'est le canal le plus important. Dès qu'une bougie (pour n'importe quelle timeframe) est clôturée, un message structuré (un "signal") est envoyé sur ce canal. C'est ce signal qui déclenchera les actions du Moteur de Trading. Ce signal est simplement "1m, 3m, 5m, 10m, 15m, 1h, 2h, 4h". 
    4.  **Persistance des Données** : Chaque bougie clôturée est systématiquement enregistrée dans la table `candles_Heartbeat` de la base de données PostgreSQL.

### 3.2 Le Cerveau : Le Moteur de Trading (Trading Engine)

Le **Trading Engine** est le service qui prend les décisions. Il est totalement réactif et ne fait rien tant qu'il n'est pas stimulé par le Heartbeat.

**Rôle** : Évaluer les stratégies et exécuter les ordres de trading.

**Workflow détaillé** :

1. **À l'écoute du Cœur** : Le service `run_trading_engine.py` est abonné au canal `Heartbeat` et attend passivement les signaux.

2. **Réaction au Signal** : Le moteur consulte la table `active_strategies` en base de données pour trouver toutes les stratégies qui correspondent aux critères du signal :
> > > > > > * La stratégie est-elle active (`is_active = True`) ?
> > > > > > * La date/heure actuelle est-elle dans la plage de validité (entre `start_date` et `end_date`) ?
> > > > > > * L'unité de temps de la stratégie correspond-elle à celle du signal (ex: `15m`) ?

1. **Exécution de la Logique** : Pour chaque stratégie correspondante, le moteur :
    * A) Récupère les toutes les bougies à la stratégie par un appel au brocker via la librairie CCXT
    * B)Chargement dynamque de la stratégie:
        * Charge le code Python de la stratégie depuis la table `strategies`, puis l’exécute en mémoire via `exec()` dans un **espace de noms local isolé** (ex. un dictionnaire temporaire de type `local_vars`). Cette isolation garantit que le code de l'utilisateur n'interfère pas avec les variables du moteur lui-même.
        * Une fois le code exécuté, le moteur **parcourt les objets définis** dans cet espace local pour identifier, à l’aide de `issubclass`, la classe qui hérite de la base `Strategy`. Cette classe devient alors la stratégie active
    * C) Le moteur instancie dynamiquement cette classe, en lui passant les données nécessaires (`candles`, `balance`, etc.). L’instance obtenue expose alors les méthodes de décision (`should_long()`, `should_short()`, etc.), qui peuvent être appelées directement pour déterminer s’il faut prendre une position ou non.
    * D) Exécute la logique de la stratégie (`should_long()`, etc.).
2. **Interaction avec les Brokers** : Si une stratégie décide d'ouvrir ou de fermer une position, le moteur utilise la librairie **CCXT** pour communiquer avec le broker de l'utilisateur et passer les ordres (y compris les Stop Loss et Take Profit).
3. **Surveillance Continue** : Indépendamment des signaux, le moteur vérifie également à intervalle régulier (toutes les minutes) l'état des trades ouverts pour s'assurer que les TP/SL n'ont pas été atteints
4. **Gestion Concurrente** : Grâce à `asyncio`, si un signal déclenche 10 stratégies en même temps, le moteur peut les traiter de manière quasi-simultanée, évitant ainsi tout goulot d'étranglement.

***Commentaire AI :*** Cette architecture découplée est très robuste. Le Heartbeat se contente de donner le tempo, et le Trading Engine d'y réagir. Si le Trading Engine plante, le Heartbeat continue de collecter les données. Si le Heartbeat se déconnecte, le Trading Engine attend simplement le prochain signal. C'est un excellent design.*
>
***Améliorations:***  Ne pas lancer de développement ni de plan...
* Que faire si les signaux n'arrivent plus ?
* Les données de marché (`candles`) sont lues localement depuis la base, garantissant des temps de réponse rapides, même pour des fenêtres larges (jusqu’à 200 bougies ou plus). Le solde (`balance`) est quant à lui récupéré en temps réel auprès du broker via API, afin de toujours refléter la réalité à l’instant du signal.
* Que faire si plus d'une bougie est récupérée pour calculer la stratégie ? Cela veut dire qu'une partie de l'application était plantée ?
* S'il devait y avoir une incohérence dans la suite des bougies et la plage de date (bougie manquante par ex.), le signaler dans la barre de status et l'enregistrer dans une table d'alerte ? Recharger la plage ? stopper le trading ?
* 🔄 **Exécution parallèle sécurisée** : Le moteur exécute en parallèle la récupération des bougies via le broker (`A`, avec `ccxt.async_support`) et le chargement dynamique du code Python de la stratégie depuis la base (`B`, via `exec()` dans un espace isolé). Ces deux opérations étant indépendantes, elles sont lancées simultanément avec `asyncio.gather()`, ce qui réduit significativement la latence. L’instanciation de la stratégie (`C`) n’intervient qu’une fois les deux résultats disponibles. Ce processus est sûr, à condition de gérer les erreurs d’exécution du code utilisateur (via `try/except`) et de veiller à une synchronisation correcte des données.


## 4. Description Détaillée des Applications Django

Chaque application Django est un module spécialisé, interagissant avec les autres et la base de données.

#### 4.1. **Heartbeat (`apps/heartbeat`)**
* **Rôle** : Visualiser l'état du service Heartbeat.
* **Backend** : S'abonne aux channels `StreamBrut` et `Heartbeat` pour relayer les informations au frontend via WebSocket.
    * `StreamBrut` -> Données (brut) transmis au frontend par websocket
    * `Heartbeat` ->  Le signal (1min, 5min, etc.) et la date, heure et min du moment de l'envoi est transmis par websocket au frontend
    * Enregistre dans la DB les signaux `Heartbeat` avec la date, heure et min du moment de l'envoi.
* **Frontend** : Affiche le flux de données brutes en temps réel dans une liste en haut de la page. Les bougies de clôture sont affichées en vert. Affiche en temps réel le signal `Heartbeat`  + AA.MM.DD_HH:MM dans des case pour chaque timeframe. Les cases sont des listes scrollable qui affichent les 20 derniers éléments visibles sur 60, le plus réçent en haut.
* **DB** : Lit la table `heartbeat_status` pour afficher l'état de connexion du service.

#### 4.2. **User Account (`apps/accounts`)**
**Rôle** : Gérer les utilisateurs, leurs paramètres de sécurité et leurs configurations personnelles
**Description** :
    * **Gestion des Brokers** : L'interface permettra un CRUD complet des comptes brokers via une **fenêtre modale**. Lors de l'ajout ou de la modification d'un broker, une **vérification de la validité des clés API** sera effectuée en temps réel en tentant une connexion via CCXT. Si la connexion réussit, le solde du compte peut être affiché pour confirmation avant de sauvegarder.
    * **Mise à jour des Paires de Trading** : Un bouton "[MAJ Paires de trading]" sera disponible pour chaque broker. Au clic, un processus asynchrone en arrière-plan chargera (via CCXT) toutes les paires de trading disponibles pour cet exchange et les stockera dans une table partagée.
    * **Configuration IA** : L'utilisateur peut choisir entre "OpenRouter" (nécessitant une clé API) et "Ollama" (avec une URL suggérée par défaut : `http://localhost:11434`). Des interrupteurs ON/OFF permettent d'activer l'un ou l'autre (activer l'un désactive l'autre). Si les deux sont sur OFF, l'assistant IA dans l'application `Stratégies` sera désactivé.
    * **Paramètres d'Affichage** :
        * **Thème** : Un sélecteur pour basculer entre le mode sombre (obligatoirement avec des couleurs néon) et un mode clair.
        * **Fuseau Horaire** : Un sélecteur pour afficher toutes les dates et heures de l'application soit en **UTC**, soit dans le **fuseau horaire local** du navigateur. Le choix est stocké dans le profil utilisateur.
    * **Mode de Développement** : Lorsque la variable d'environnement `DEBUG_ARISTOBOT=True` est active, l'application **contourne l'écran de connexion** et connecte automatiquement un utilisateur "dev" qui existe en base de données. Cet utilisateur a un accès inconditionnel à toutes les données de tous les utilisateurs pour faciliter le développement et les tests par une IA. Si un utilisateur se déconnecte manuellement en mode `DEBUG_ARISTOBOT=True`, il est automatiquement reconnecté en tant que "dev".

* **Backend** : Gère l'authentification (login/logout), l'enregistrement de nouveaux utilisateurs (CRUD), et le stockage des préférences.

* **Frontend** : Fournit les interfaces pour :
    * Changer son mot de passe.
    * Gérer ses comptes de brokers (CRUD via une fenêtre modale).
    * Définir un broker par défaut.
    * Configurer la connexion à une IA (OpenRouter ou Ollama) avec clé API/URL et un switch ON/OFF.
    * Gérer les paramètres d'affichage décrits.
    
* **DB** : Interagit principalement avec la table `users` (étendue du modèle Django) et la table `brokers`.

* **Script d'Initialisation** : La commande `python manage.py init_aristobot` sera créée. Son unique rôle sera de créer les utilisateurs "dev" et "dac" en base de données pour faciliter le premier lancement.

#### 4.3. **Trading Manuel (`apps/trading_manual`)**
* **Rôle** : Permettre à l'utilisateur de passer des ordres manuellement, comme il le ferait sur la plateforme d'un exchange.
* **Description** :  Le brocker par défaut de l'utilisateur est proposé à l'utilisateur. Il peut choisir à l'aide d'une scroll list le brocker ave lequel il veut travailler. La zone de saisie de trade sera ergonomique : si l'utilisateur saisit une quantité, la valeur en USD est calculée ; s'il saisit un montant en USD, la quantité d'actifs est calculée. La liste des symboles disponibles sera **configurable, avec pagination et fonction de recherche** pour une meilleure utilisabilité. 

* **Backend** : Utilise **CCXT** pour toutes les interactions avec les exchanges :
  * Connexion au broker sélectionné.
  * Récupération de la balance et des positions en cours.
  * Passage d'ordres (marché, limite).

* **Frontend** : Affiche :
  * La liste des brokers configurés par l'utilisateur.
  * Le portefeuille d'actifs avec les totaux.
  * Une zone de saisie de trade, avec calcul automatique de la quantité ↔ valeur en USD.
  * Des boutons "Achat" et "Vente".

* **DB** : Enregistre chaque transaction manuelle dans la table `trades`. **inportant** renseigner dans un champ que c'est un Trade Manuel.

#### 4.4. **Trading BOT (`apps/trading_engine`)**
* **Rôle** : Gère le cycle de vie des stratégies actives. Il ne fait aucun calcul de trading lui-même (c'est le rôle du _Trading Engine_), mais il met à jour la base de données pour que le moteur sache quoi faire.
* **Description** :
    * **Comportement des Boutons** :
        * **Bouton "Stop"** : Cette action est une **désactivation sécurisée**. Elle met à jour la date de fin de la stratégie active à une date passée (`01.01.01`) ET bascule son champ `is_active` à `False`. Si un trade est actuellement ouvert pour cette stratégie, une **boîte de dialogue de confirmation** avertira l'utilisateur avant de procéder.
        * **Bouton "Vendre"** : Déclenche une vente immédiate au prix du marché pour la position ouverte par une stratégie, sans pour autant désactiver la stratégie elle-même.
        * **Bouton "Suspendre" (Amélioration)** : Il est suggéré d'ajouter un bouton pour suspendre temporairement une stratégie (en basculant simplement `is_active` à `False`), ce qui permettrait de la réactiver plus tard sans devoir reconfigurer les dates.

* **Backend** : Activer, désactiver et surveiller les stratégies de trading automatisées.

* **Frontend** : Permet à l'utilisateur de :
  * Sélectionner une stratégie, un broker, un symbole et une plage de dates de fonctionnement et l'activer par un sélecteur `is_active` à `True`.
  * Voir la liste des stratégies actuellement actives.
  * Visualiser les 10 derniers trades et le P\&L (Profit & Loss) pour chaque stratégie active.

* **DB** : L'interface principale pour la table `active_strategies` (CRUD). Lit la table `trades` pour afficher l'historique récent.

#### 4.5. **Stratégies (`apps/strategies`)**
* **Rôle** : L'atelier de création et de gestion des stratégies de trading.
* **Description** : L'utilisateur modifie le template de base en ajoutant des conditions a l'aide de fonctions fournie par la librairie Python "Pandas TA Classic" ->  `pip install -U git+https://github.com/xgboosted/pandas-ta-classic`
   
*   **Template de Base** : Toute nouvelle stratégie sera créée à partir d'un template de base. Ce code sera affiché dans l'éditeur de l'interface.
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
Exemple d’implémentation par l'utilisateur du croisement EMA 10 / EMA 20
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
    *	 `self.candles` doit être un **DataFrame Pandas** avec une colonne `'close'`.
    *	 Le croisement est vérifié entre **la bougie précédente** (`iloc[-2]`) et **la bougie actuelle** (`iloc[-1]`).

* **Backend** : Gère le CRUD des stratégies. Fournit une fonctionnalité clé : un endpoint d'API qui reçoit le code Python d'une stratégie et le valide syntaxiquement avant de l'enregistrer.

* **Frontend** :
  * Affiche la liste des stratégies de l'utilisateur (CRUD).
  * Fournit un éditeur de code pour écrire ou modifier la logique d'une stratégie en Python, basé sur un template prédéfini.
  * Intègre un "assistant IA" qui permet à l'utilisateur de décrire sa logique en langage naturel pour aider à générer le code.
  * Un bouton "Tester la syntaxe" envoie le code au backend pour validation.

* **DB** : Gère les enregistrements de la table `strategies`.

#### 4.6. **Backtest (`apps/backtest`)**

* **Rôle** : Simuler l'exécution d'une stratégie sur des données historiques pour en évaluer la performance potentielle.

* **Description** : Permet de lancer un backtest en sélectionnant une stratégie, une plage de dates, un symbole, un timeframe et un montant de départ. Affiche les résultats : statistiques de performance (gains, drawdown, etc.) et la liste de tous les trades simulés. Les données de bougies historiques sont dans la `candles` avec le Brocker identifié. Ainsi, si d'autres utilisateurs et d'autres stratégies ont besoin de ces données elles sont accessible. Eviter de backtester sur les bougies d'un autre brocker que celui sélectionner pour la stratégie. Si les bougies n'existent pas, elles sont chargeé avec la librairie CCXT.

* **Backend** :
    * Charge les données de bougies historiques.
    * Exécute la logique de la stratégie sélectionnée sur cette plage de données.
    * Envoie le résultat du test: Nb de trades gagnants perdant, Plus grande perte, Gain/perte total, etc…
    * Envoie la liste des trades avec toutes les données (heure d'achat/vente, calcul du gain, évolution du solde)
    * Envoie des mises à jour en temps réel de progression du test en cours (en %) au frontend via WebSocket.
    * Gère la possibilité de l'interruption du calcul par l'utilisateur 
    * Gère la possibilité de l'interruption par l'utilisateur du chargement des bougies

* **Frontend** : Permet à l'utilisateur:
    * De sélectionner modifier créer ou effacer une stratégie (Code du template avec assistant IA)
    * De sélectionner le brocker, l'asset, le timeframe et la plage de date début/fin et un montant en Quantité
    * De lancer le backtest
    * D'interrompre le backtest
    * D'interrompre le chargement des bougies durant le chargement
    * D'afficher les résultats du backtest (liste des trades et statistiques)

* **DB** : Lit la table `candles` et enregistre les résultats finaux dans la table `backtest_results`.

#### 4.7. **Webhooks (`apps/webhooks`)
* **Rôle** : Recevoir des signaux de trading provenant de services externes (ex: TradingView) et les exécuter. C'est un point d'entrée alternatif pour l'automatisation.
* **Backend** : Fournit un endpoint d'API sécurisé qui écoute les requêtes webhook. Quand un signal valide est reçu, il le parse et utilise **CCXT** pour passer l'ordre correspondant.
* **Frontend** : Affiche un journal des webhooks reçus et le statut des ordres qui en ont résulté.
* **DB** : Enregistre chaque webhook reçu dans la table `webhooks` et les trades correspondants dans la table `trades`.

* **Justification** : Cette application fournit un moyen de déclencher des trades basé sur des **signaux externes**, par opposition aux stratégies qui sont basées sur des **calculs internes**. C'est une distinction fondamentale qui justifie son existence en tant que module séparé.
* 
#### 4.8. **Statistiques (`apps/stats`)**

* **Rôle** : Fournir une vue d'ensemble de la performance de trading de l'utilisateur.
* **Backend** : Agrège les données de la table `trades` pour calculer diverses métriques :
  * Évolution globale du solde.
  * Performance par stratégie individuelle.
  * Performance par source de webhook.
* **Frontend** : Affiche les données sous forme de graphiques et de tableaux de bord, avec la possibilité de filtrer par compte de broker.

* **DB** : Lit intensivement la table `trades`.

## 5. Architecture Détaillée de la Base de Données

Les relations entre les tables sont cruciales pour le bon fonctionnement de l'application.La structure est conçue pour être multi-locataire (_multi-tenant_), où la plupart des données sont isolées par `user_id`.

```ascii
+-----------+       +-----------+       +---------------------+
|   users   |------>|  brokers  |<------|  active_strategies  |
+-----------+       +-----------+       +---------------------+
      |                   |                         |
      |                   |                         |
      |                   +------------------+      |
      |                                      |      |
      +------------------------------------->|  trades  |<--+
      |                                      |      |      |
      |                                      +------+      |
      v                                                    |
+------------+                                         +-----------+
| strategies |----------------------------------------->| webhooks  |
+------------+                                         +-----------+
      |
      v
+------------------+      +-----------+
| backtest_results |      |  candles  |  <-- (utilisée par Backtest et Strategies)
+------------------+      +-----------+
```
#### `users` (Table Utilisateurs)

* **Description** : Étend le modèle utilisateur standard de Django pour stocker les configurations spécifiques à l'application.
* **Champs Clés** : `id`, `username`, `password`, `default_broker_id` (FK vers `brokers`), `ai_provider`, `ai_api_key` (chiffré), `display_timezone`.
* **Relations** : Un utilisateur a plusieurs `brokers`, plusieurs `strategies`, plusieurs `trades`, etc. C'est la table racine pour les données spécifiques à un utilisateur.

#### `brokers`

* **Description** : Stocke les informations de connexion aux différents comptes de brokers pour chaque utilisateur.
* **Champs Clés** : `id`, `user_id` (FK vers `users`), `name`, `exchange` (ex: 'binance'), `api_key` (chiffré), `api_secret` (chiffré), `is_default` (booléen).
* **Relations** : Liée à un `user`. Un broker peut être associé à plusieurs `active_strategies` et `trades`.

#### `strategies`

* **Description** : Contient le code source et les métadonnées des stratégies de trading créées par les utilisateurs.
* **Champs Clés** : `id`, `user_id` (FK vers `users`), `name`, `description`, `code` (champ texte contenant le code Python), `timeframe`.
* **Relations** : Liée à un `user`. Une stratégie peut être utilisée dans plusieurs `active_strategies` et `backtest_results`.

#### `active_strategies`

* **Description** : Table de liaison qui représente l'activation d'une `strategy` sur un `broker` pour un `symbol` donné, pendant une période définie. C'est cette table que le Trading Engine consulte.
* **Champs Clés** : `id`, `user_id` (FK), `strategy_id` (FK), `broker_id` (FK), `symbol`, `start_date`, `end_date`, `is_active` (booléen).
* **Relations** : Fait le lien entre `users`, `strategies` et `brokers`.

#### `candles` (Table Bougies)

* **Description** : Stocke les données de marché OHLCV. Cette table est partagée par tous les utilisateurs pour éviter la duplication de données.
* **Champs Clés** : `id`, `broker_id` (FK), `symbol`, `timeframe`, `open_time` (timestamp), `close_time`, `open_price`, `high_price`, `low_price`, `close_price`, `volume`, .
* **Relations** : Utilisée par le _Backtest_ et potentiellement par les _Stratégies_. C'est la seule table non-locataire majeure.

#### `trades`

* **Description** : Journal central de toutes les transactions exécutées, qu'elles soient manuelles, automatiques (via stratégie) ou externes (via webhook).
* **Champs Clés** : `id`, `user_id` (FK), `broker_id` (FK), `strategy_id` (FK, optionnel), `webhook_id` (FK, optionnel), `symbol`, `side` ('buy'/'sell'), `quantity`, `price`, `status`, `profit_loss`.
* **Relations** : La table la plus connectée, liée à `users`, `brokers`, potentiellement `active_strategies` et `webhooks`. Elle est la source de données principale pour l'application `Statistiques`.

#### `webhooks`

* **Description** : Enregistre chaque appel webhook reçu pour des raisons de traçabilité et de débogage.
* **Champs Clés** : `id`, `user_id` (FK), `source` (ex: 'tradingview'), `payload` (JSON), `processed` (booléen).
* **Relations** : Liée à un `user` et peut être liée à un `trade`.

#### `backtest_results`

* **Description** : Stocke les résultats synthétiques de chaque simulation de backtest exécutée.
* **Champs Clés** : `id`, `user_id` (FK), `strategy_id` (FK), `start_date`, `end_date`, `final_amount`, `total_trades`, `sharpe_ratio`, `trades_detail` (JSON).
* **Relations** : Liée à `users` et `strategies`.

#### `heartbeat_status` (Table Système)

* **Description** : Une table simple (probablement à une seule ligne) pour surveiller l'état du service Heartbeat.
* **Champs Clés** : `is_connected` (booléen), `last_heartbeat` (timestamp).
* **Relations** : Aucune. C'est une table de monitoring interne.

### Précisions sur les Tables et Relations

*   **`users`** : En plus des champs standards, elle contiendra `display_timezone` ('UTC' ou 'Europe/Paris', par exemple) et les configurations de l'IA.
*   **`brokers`** : Le champ `exchange` sera un choix restreint basé sur les exchanges supportés par CCXT.
*   **`trades`** : C'est la table la plus importante pour l'analyse. Les champs `strategy_id` et `webhook_id` sont `nullable=True` pour permettre d'enregistrer les trades manuels qui ne proviennent d'aucune automatisation. Un historique complet de **toutes les tentatives de trades, y compris les échecs**, sera conservé pour le débogage.
*   **`candles`** : C'est une table de données brutes, optimisée pour des lectures rapides. Des **index** sur (`symbol`, `timeframe`, `close_time`, `brocker_id`) seront cruciaux pour les performances des backtests. Le brocker doit être identifié par son proprechamp
*   **`active_strategies`** et **`strategies`** : Il est clair que `strategies` est le "modèle" (le code), et `active_strategies` est "l'instance en cours d'exécution" de ce modèle avec des paramètres concrets (broker, symbole, dates).

## 6. Points Non Classés et Futurs Développements

Cette section regroupe les idées et les points de discussion qui n'ont pas encore été pleinement intégrés dans le plan de développement initial mais qui doivent être conservés pour référence future.

* **Cohérence du Heartbeat** : L'idée d'une vérification de la "cohésion" des bougies reçues a été mentionnée. Cela pourrait impliquer de vérifier la régularité des timestamps des bougies stockées en base de données pour détecter d'éventuelles interruptions du service. À développer ultérieurement.
* **Gestion Avancée du Mode Testnet** : La librairie CCXT supporte les environnements de test (sandbox) pour certains brokers. Il faudra explorer comment gérer les cas où un broker n'offre pas de mode testnet. L'interface pourrait désactiver le switch "Testnet" pour ce broker ou afficher un avertissement clair. *La gestion du mode Testnet pour les brokers qui ne le supportent pas reste à définir. La solution la plus simple pour une V1 serait de désactiver le switch "Mode Testnet" sur l'interface si `exchange.features['sandbox']` (une propriété de CCXT) est `False` pour le broker sélectionné. C'est une approche pragmatique qui correspond à la philosophie du projet.
* **Partage de Stratégies** : L'idée d'un système de partage de stratégies entre utilisateurs a été évoquée. Cela nécessiterait des modifications importantes du modèle de données (ex: table de liaison, permissions) et est considéré comme une fonctionnalité pour une version future.
* **Gestion des Positions Ouvertes** : Il pourrait être pertinent d'ajouter une table dédiée `positions` pour suivre l'état actuel d'un trade ouvert (quantité, prix d'entrée, P\&L latent) plutôt que de le déduire de la table `trades`. C'est un point d'amélioration de l'architecture à considérer.

## 7. Instructions pour le Développement avec l'IA

### Fichier `.claude-instructions`

Ce fichier doit contenir les directives suivantes pour guider l'IA :

```
# Aristobot3 - Instructions Claude Code

Contexte : Bot de trading crypto personnel en Django/Vue.js pour 5 users max.
Approche pragmatique : shipping > perfection.

## Structure stricte
- Backend Django dans /backend/apps/
- Frontend Vue.js dans /frontend/src/
- Services auto-démarrés dans `apps/*/management/commands/`
- WebSocket via Django Channels

## Conventions de code
- Python : PEP 8, type hints. Code et commentaires en français. Docstrings intermédiaires.
- Vue 3 Composition API uniquement.

## Base de données
- PostgreSQL uniquement via Django ORM.

## À ne PAS faire
- Pas de microservices, Celery, MongoDB ou over-engineering.
```

### Prompt Type

```
Contexte : Aristobot3, App [Nom de l'app]
Objectif : [Ce que doit faire la fonctionnalité]
Logique Backend : [Endpoints, modèles, services]
Interface Frontend : [Composants Vue, style attendu]
Contraintes : [Limites techniques, ex: utiliser le CCXTService]
```

