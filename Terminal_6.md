# Terminal 6 - Webhook Receiver Service

## Vue d'Ensemble

Le Terminal 6 est un service dédié à la réception des webhooks externes (principalement TradingView). Il s'agit d'un serveur HTTP ultra-léger qui tourne indépendamment de Django/Daphne, suivant le principe de séparation des responsabilités et l'architecture découplée d'Aristobot3.

## Architecture Complète avec Tous les Terminaux

```ascii
                    ARCHITECTURE COMPLÈTE ARISTOBOT3 - 6 TERMINAUX
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                     SOURCES EXTERNES                                    │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  • TradingView (Webhooks)                                              │
    │  • Binance WebSocket (Market Data)                                     │
    │  • Exchanges APIs (CCXT)                                               │
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
    │              └→ Redis: 'ccxt_requests'                               │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
                                        ↓
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        COUCHE EXÉCUTION                                │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │              Terminal 5: Service CCXT Centralisé                       │
    │              • Gestion instances exchanges                             │
    │              • Exécution ordres                                        │
    │              • Rate limiting                                           │
    │              • Cache symboles                                          │
    │              └→ Redis: 'ccxt_responses'                              │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
                                        ↓
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      COUCHE PRÉSENTATION                               │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  Terminal 1: Daphne (Django)        Terminal 4: Frontend (Vue.js)      │
    │  • API REST                          • Interface utilisateur           │
    │  • WebSocket Server                  • Dashboard temps réel            │
    │  • Authentification                  • Graphiques & monitoring         │
    │  • Backend apps/*                    • Gestion des stratégies          │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         COUCHE DONNÉES                                 │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  PostgreSQL                          Redis                             │
    │  • Persistance complète              • Pub/Sub inter-process           │
    │  • Multi-tenant                      • Cache temporaire                │
    │  • Historique trades                 • Channels:                       │
    │  • Stratégies & positions            - heartbeat                       │
    │                                       - webhook_raw                    │
    │                                       - ccxt_requests/responses        │
    │                                       - websockets                     │
    └─────────────────────────────────────────────────────────────────────────┘
```

## Rôle et Responsabilités de Chaque Terminal

### Terminal 1 : Serveur Web Django (Daphne)
- **Commande** : `daphne aristobot.asgi:application`
- **Port** : 8000
- **Responsabilités** :
  - Servir l'API REST pour toutes les applications Django
  - Gérer l'authentification et les sessions
  - Maintenir les connexions WebSocket avec les clients
  - Exécuter le code des apps Django (accounts, brokers, strategies, etc.)
  - NE PAS recevoir directement les webhooks externes

### Terminal 2 : Service Heartbeat
- **Commande** : `python manage.py run_heartbeat`
- **Port** : Aucun (client WebSocket vers Binance)
- **Responsabilités** :
  - Connexion permanente au WebSocket Binance
  - Agrégation des trades en bougies multi-timeframe
  - Publication des signaux temporels sur Redis
  - Sauvegarde des bougies en PostgreSQL
  - Totalement indépendant du reste

### Terminal 3 : Trading Engine
- **Commande** : `python manage.py run_trading_engine`
- **Port** : Aucun (écoute Redis)
- **Responsabilités** :
  - Écouter DEUX sources : signaux Heartbeat ET webhooks
  - Charger et exécuter les stratégies Python
  - Traiter les webhooks avec logique métier
  - Gérer l'état des positions
  - Décider des ordres à passer
  - Communiquer avec Terminal 5 pour exécution

### Terminal 4 : Frontend Vue.js
- **Commande** : `npm run dev`
- **Port** : 5173 (dev) ou 80/443 (production)
- **Responsabilités** :
  - Interface utilisateur complète
  - Communication avec Terminal 1 (API + WebSocket)
  - Affichage temps réel des données
  - Gestion locale de l'état UI (Pinia)

### Terminal 5 : Service CCXT Centralisé
- **Commande** : `python manage.py run_ccxt_service`
- **Port** : Aucun (écoute Redis)
- **Responsabilités** :
  - Maintenir une instance CCXT par exchange
  - Gérer le rate limiting
  - Exécuter les ordres de trading
  - Récupérer les balances et positions
  - Mettre à jour les symboles disponibles

### Terminal 6 : Webhook Receiver Service (NOUVEAU)
- **Commande** : `python manage.py run_webhook_receiver`
- **Port** : 8888 (configurable)
- **Responsabilités** :
  - Recevoir les webhooks HTTP POST
  - Valider le token d'authentification
  - Publier immédiatement sur Redis
  - Répondre rapidement (200 OK)
  - AUCUNE logique métier
  - AUCUN accès à la base de données

## Structure des Fichiers Mise à Jour

```
Aristobot3/
├── backend/
│   ├── aristobot/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── routing.py
│   │
│   ├── apps/
│   │   ├── core/
│   │   │   ├── management/commands/
│   │   │   │   ├── run_heartbeat.py         # Terminal 2
│   │   │   │   └── run_ccxt_service.py      # Terminal 5
│   │   │   ├── services/
│   │   │   │   ├── ccxt_manager.py
│   │   │   │   ├── ccxt_client.py
│   │   │   │   └── symbol_updater.py
│   │   │   ├── consumers.py
│   │   │   └── models.py
│   │   │
│   │   ├── accounts/
│   │   ├── brokers/
│   │   ├── market_data/
│   │   ├── strategies/
│   │   │
│   │   ├── trading_engine/
│   │   │   ├── management/commands/
│   │   │   │   └── run_trading_engine.py    # Terminal 3 (MODIFIÉ)
│   │   │   ├── services/
│   │   │   │   ├── strategy_executor.py
│   │   │   │   └── webhook_processor.py     # NOUVEAU
│   │   │   └── models.py
│   │   │
│   │   ├── trading_manual/
│   │   │
│   │   ├── webhooks/                        # APPLICATION WEBHOOKS
│   │   │   ├── management/
│   │   │   │   └── commands/
│   │   │   │       └── run_webhook_receiver.py  # Terminal 6 (NOUVEAU)
│   │   │   ├── services/
│   │   │   │   ├── webhook_validator.py
│   │   │   │   ├── position_tracker.py
│   │   │   │   └── coherence_checker.py
│   │   │   ├── models.py                    # Webhook, WebhookState
│   │   │   ├── serializers.py
│   │   │   ├── views.py                     # API REST monitoring
│   │   │   ├── consumers.py                 # WebSocket updates
│   │   │   └── urls.py
│   │   │
│   │   ├── backtest/
│   │   └── stats/
│   │
│   ├── requirements.txt                     # MISE À JOUR NÉCESSAIRE
│   └── manage.py
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── HeartbeatView.vue
│   │   │   ├── TradingManualView.vue
│   │   │   ├── TradingBotView.vue
│   │   │   ├── StrategiesView.vue
│   │   │   ├── WebhooksView.vue            # NOUVEAU
│   │   │   ├── BacktestView.vue
│   │   │   ├── StatsView.vue
│   │   │   └── AccountView.vue
│   │   ├── components/
│   │   ├── api/
│   │   ├── websocket/
│   │   └── design-system/
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   ├── ARISTOBOT3.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── Terminal_6.md                       # CE FICHIER
│   ├── MODULE1_IMPLEMENTATION.md
│   ├── MODULE2_IMPLEMENTATION.md
│   ├── MODULE3_IMPLEMENTATION.md
│   └── MODULE4_WEBHOOKS.md                 # À CRÉER
│
├── .env
├── .env.example
├── .gitignore
├── .claude-instructions
└── README.md
```

## Flux de Communication Inter-Terminaux

### Channels Redis

1. **`heartbeat`**
   - Publié par : Terminal 2 (Heartbeat)
   - Écouté par : Terminal 3 (Trading Engine)
   - Contenu : Signaux de clôture de bougies (1m, 5m, 15m, etc.)

2. **`webhook_raw`**
   - Publié par : Terminal 6 (Webhook Receiver)
   - Écouté par : Terminal 3 (Trading Engine)
   - Contenu : Webhooks bruts avec timestamp

3. **`ccxt_requests`**
   - Publié par : Terminal 3 (Trading Engine)
   - Écouté par : Terminal 5 (Service CCXT)
   - Contenu : Ordres à exécuter, demandes de balance

4. **`ccxt_responses`**
   - Publié par : Terminal 5 (Service CCXT)
   - Écouté par : Terminal 3 (Trading Engine)
   - Contenu : Confirmations d'ordres, balances

5. **`websockets`**
   - Publié par : Tous les terminaux
   - Écouté par : Terminal 1 (Daphne) → Frontend
   - Contenu : Updates temps réel pour l'UI

## Configuration Réseau et Sécurité

### Configuration NAT pour les Webhooks

TradingView n'accepte que les ports 80 (HTTP) ou 443 (HTTPS). Le Terminal 6 écoute sur le port 8888. Deux solutions :

#### Option 1 : iptables (Linux)
```bash
# Redirection port 80 vers 8888
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8888
```

#### Option 2 : Nginx (Recommandé)
```nginx
server {
    listen 80;
    server_name webhook.votredomaine.com;
    
    location /webhook {
        proxy_pass http://localhost:8888;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Sécurité du Terminal 6

1. **Token d'authentification** : Header `X-Webhook-Token` vérifié
2. **Pas d'accès DB** : Aucune connexion PostgreSQL
3. **Code minimal** : ~50 lignes, surface d'attaque réduite
4. **Timeout rapide** : Réponse en <100ms
5. **Rate limiting** : Peut être ajouté si nécessaire

## Librairies Python Supplémentaires

### Pour requirements.txt

```python
# Existantes (déjà dans le projet)
Django==4.2.15
channels==4.0.0
channels-redis==4.1.0
redis==5.0.0
ccxt==4.1.22
djangorestframework==3.14.0
daphne==4.0.0
cryptography==41.0.0
python-dotenv==1.0.0
psycopg2-binary==2.9.9

# NOUVELLES pour Terminal 6
aiohttp==3.9.1          # Serveur HTTP asynchrone léger
aioredis==2.0.1         # Client Redis asynchrone
uvloop==0.19.0          # Event loop optimisé (optionnel mais recommandé)
```

### Installation
```bash
pip install aiohttp aioredis uvloop
```

## Interaction Backend Webhooks avec Terminal 3

### Clarification Important

L'application Django `apps/webhooks/` **N'EST PAS** un terminal séparé. Elle fait partie de Terminal 1 (Daphne) et sert uniquement à :

1. **Fournir les APIs REST** pour le frontend
   - GET `/api/webhooks/history/` - Historique des webhooks
   - GET `/api/webhooks/positions/` - Positions ouvertes
   - GET `/api/webhooks/stats/` - Statistiques

2. **Gérer les WebSocket** pour updates temps réel
   - Consumer pour push des nouveaux webhooks
   - Updates des positions en temps réel

3. **Modèles Django** pour la persistance
   - Table `webhooks` : Historique complet
   - Table `webhook_states` : État des positions
   - Table `webhook_trades` : Trades exécutés

### Flux d'Interaction

```
1. Terminal 6 reçoit webhook → publie sur Redis 'webhook_raw'
2. Terminal 3 écoute Redis → traite le webhook
3. Terminal 3 sauvegarde en DB (tables webhooks, trades)
4. Terminal 3 publie update sur Redis 'websockets'
5. Terminal 1 (Django) push update au Frontend via WebSocket
6. Frontend peut aussi faire GET sur API REST pour historique
```

### Séparation des Responsabilités

- **Terminal 6** : Réception pure, aucune logique
- **Terminal 3** : TOUTE la logique métier webhooks
- **apps/webhooks/** : Interface de consultation uniquement
- **Frontend** : Affichage et monitoring

## Avantages de cette Architecture

### 1. Isolation et Robustesse
- Chaque terminal peut crasher sans affecter les autres
- Redémarrage indépendant des services
- Pas de single point of failure

### 2. Scalabilité
- Terminal 6 peut être répliqué (load balancing)
- Terminal 3 peut traiter en parallèle
- Redis gère naturellement la pression

### 3. Debugging Facilité
- Logs séparés par terminal
- Flux de données traçable
- Tests unitaires par composant

### 4. Performance
- Terminal 6 ultra-rapide (aiohttp)
- Pas d'impact sur Django/Daphne
- Traitement asynchrone complet

### 5. Vibe Coding
- Chaque terminal = une responsabilité claire
- Code simple et focalisé
- Facile à comprendre et maintenir

## Ordre de Démarrage Recommandé

```bash
# 1. Base de données et cache
systemctl start postgresql
systemctl start redis

# 2. Services de réception (peuvent tourner sans le reste)
python manage.py run_heartbeat          # Terminal 2
python manage.py run_webhook_receiver   # Terminal 6

# 3. Service d'exécution
python manage.py run_ccxt_service       # Terminal 5

# 4. Cerveau du système
python manage.py run_trading_engine     # Terminal 3

# 5. Interface
daphne aristobot.asgi:application      # Terminal 1
npm run dev                             # Terminal 4
```

## Points d'Attention pour l'Implémentation

1. **Gestion des erreurs** : Terminal 6 doit TOUJOURS répondre 200 OK à TradingView
2. **Idempotence** : Un webhook dupliqué ne doit pas créer deux ordres
3. **Cohérence** : Vérifier les webhooks manqués (PING)
4. **État des positions** : Table `webhook_states` pour tracker
5. **Isolation broker** : Respecter `TypeDeTrading` = "Webhooks"
6. **Monitoring** : Dashboard pour voir l'état de chaque terminal

## Prochaines Étapes

1. Créer le fichier `run_webhook_receiver.py` (Terminal 6)
2. Modifier `run_trading_engine.py` pour écouter les webhooks
3. Créer les modèles Django (Webhook, WebhookState)
4. Implémenter les APIs REST et WebSocket
5. Créer la vue Frontend WebhooksView.vue
6. Tester avec TradingView Webhook Tester
7. Configurer le NAT firewall/nginx

## Conclusion

Le Terminal 6 suit parfaitement la philosophie d'Aristobot3 : simple, focalisé, robuste. Avec cette architecture à 6 terminaux, chaque composant a une responsabilité unique et claire, facilitant le développement, le debugging et la maintenance. C'est du pur "vibe coding" : pragmatique et efficace !
