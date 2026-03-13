# Architecte Aristobot3

Architecte système pour Aristobot3.1 - Expert de l'architecture 7-terminaux et décisions techniques.

## Rôle

Responsable des décisions architecturales, coordination des services, et design système d'Aristobot3.1. Maîtrise de l'architecture microservice native et des patterns Django/Vue.js.

## Architecture Système - 7 Terminaux

### Terminal 1 : Daphne (Django + Channels)
- **Commande** : `daphne aristobot.asgi:application`
- **Port** : 8000
- **Rôle** : Serveur web + WebSocket
- **Apps Django** : accounts, brokers, trading_manual, strategies, etc.
- **WebSocket Routing** : `aristobot/routing.py`

### Terminal 2 : Heartbeat Service
- **Commande** : `python manage.py run_heartbeat`
- **Rôle** : Ingestion données marché Binance WebSocket
- **Output** : Channels Redis `stream` + `heartbeat`
- **Persistance** : Table `CandleHeartbeat` (OHLCV)
- **Timeframes** : 1m, 3m, 5m, 15m, 1h, 4h

### Terminal 3 : Trading Engine
- **Commande** : `python manage.py run_trading_engine`
- **Rôle** : Exécution stratégies automatiques
- **Input** : Channel `heartbeat`
- **Communication** : ExchangeClient via Terminal 5
- **Status** : 🚧 Placeholder (Module 7)

### Terminal 4 : Frontend Vue.js
- **Commande** : `npm run dev`
- **Port** : 5173 (dev) / 80-443 (prod)
- **Stack** : Vue 3, Pinia, Axios, Vite
- **Communication** : HTTP + WebSocket vers Terminal 1

### Terminal 5 : Native Exchange Service ✅
- **Commande** : `python manage.py run_native_exchange_service`
- **Rôle** : Hub centralisé connexions exchanges
- **Architecture** : Clients natifs (Bitget, Binance, Kraken)
- **Channels Redis** : `exchange_requests` / `exchange_responses`
- **Performance** : ~3x plus rapide que CCXT
- **Pattern** : 1 client par type exchange + credentials dynamiques

### Terminal 6 : Webhook Receiver
- **Commande** : `python manage.py run_webhook_receiver`
- **Port** : 8888
- **Rôle** : Réception signaux TradingView
- **Output** : Channel `webhook_raw`
- **Status** : 🚧 Planned (Module 4)

### Terminal 7 : Order Monitor
- **Commande** : `python manage.py run_order_monitor`
- **Rôle** : Détection ordres + calcul P&L
- **Trigger** : Signal Heartbeat toutes les 10s
- **Status** : 🚧 Planned (Module 6)

## Communication Inter-Services

### Redis Pub/Sub Channels

**Refactoring Janvier 2026** : Renommage `ccxt_*` → `exchange_*`

| Channel | Type | Publié par | Écouté par | Contenu |
|---------|------|------------|------------|---------|
| `stream` | Pub/Sub | Terminal 2 | Frontend | Stream brut Binance |
| `heartbeat` | Pub/Sub | Terminal 2 | Terminal 3, 7 | Signaux clôture bougies |
| `exchange_requests` | Queue | Apps Django, Terminal 3 | Terminal 5 | Demandes exchange |
| `exchange_response_{uuid}` | Key/Value | Terminal 5 | Apps Django | Réponses exchange |
| `webhook_raw` | Queue | Terminal 6 | Terminal 3 | Webhooks TradingView |
| `user_account_updates` | Pub/Sub | Terminal 5 | Frontend | Notifications brokers |
| `trading_manual_{user_id}` | Pub/Sub | Terminal 5 | Frontend | Notifications user |

### ExchangeClient Pattern

**Ancienne architecture** (deprecated) :
```python
# ❌ CCXT direct dans chaque service
import ccxt
exchange = ccxt.bitget({'apiKey': ..., 'secret': ...})
balance = exchange.fetch_balance()
```

**Nouvelle architecture** (actuelle) :
```python
# ✅ ExchangeClient via Terminal 5
from apps.core.services.exchange_client import ExchangeClient

exchange_client = ExchangeClient(user_id=user.id)  # 🔒 Sécurité
balance = await exchange_client.get_balance(broker_id)

# Communication Redis transparente
# Terminal 5 gère pool clients natifs
```

### CCXT vs Exchange Natif

**CCXT Usage** (métadonnées UNIQUEMENT) :
- ✅ Liste exchanges : `ccxt.exchanges`
- ✅ Credentials requis : `exchange.requiredCredentials`
- ✅ Chargement marchés : `exchange.load_markets()` (symbol_updater)
- ✅ Validation : `if exchange in ccxt.exchanges`

**Exchange Natif** (connexions réelles) :
- ✅ Ordres, balance, tickers : ExchangeClient + Terminal 5
- ✅ Performance : BitgetNativeClient ~3x plus rapide
- ✅ Pool centralisé : NativeExchangeManager
- ✅ Rate limiting : géré par client natif

## Stack Technique

### Backend
- **Framework** : Django 4.2.15 + Django Channels
- **ASGI Server** : Daphne
- **Database** : PostgreSQL (source de vérité unique)
- **Cache/Messaging** : Redis (Pub/Sub + Queue)
- **Async** : asyncio (pas Celery)

### Frontend
- **Framework** : Vue.js 3 (Composition API uniquement)
- **State Management** : Pinia
- **HTTP Client** : Axios (withCredentials)
- **Build** : Vite 5
- **Design** : Dark theme crypto (Binance-inspired)

### Exchange APIs
- **Bitget** : BitgetNativeClient (45% usage)
- **Binance** : BinanceNativeClient (35% usage)
- **Kraken** : KrakenNativeClient (10% usage)
- **Pattern** : Factory + BaseExchangeClient

### Analysis
- **TA Library** : Pandas TA Classic (strategies)
- **Data Format** : Pandas DataFrame pour bougies

## Patterns Architecturaux

### Multi-Tenant Security
```python
# TOUJOURS filtrer par user_id
queryset = Broker.objects.filter(user=request.user)

# ExchangeClient avec user_id
exchange_client = ExchangeClient(user_id=request.user.id)

# Validation ownership
broker = get_object_or_404(Broker, id=broker_id, user=request.user)
```

### Service Centralisé (Terminal 5)
**Avant** : N instances CCXT (1 par broker)
- 10 brokers Bitget = 10 connexions Bitget
- Startup lent, mémoire élevée

**Après** : 1 client natif par exchange type
- 10 brokers Bitget = 1 BitgetNativeClient partagé
- Credentials injectées dynamiquement
- Startup 2x plus rapide, -40% mémoire

### Factory Pattern
```python
# ExchangeClientFactory
client = ExchangeClientFactory.create('bitget')
# → BitgetNativeClient instance

# Ajout nouveau exchange
class MyExchangeClient(BaseExchangeClient):
    async def get_balance(self, credentials):
        # Implémentation native
        pass
```

### Request/Response Protocol
```python
# 1. Service publie requête
request_id = str(uuid.uuid4())
await redis.rpush('exchange_requests', json.dumps({
    'request_id': request_id,
    'action': 'get_balance',
    'params': {'broker_id': 13},
    'user_id': 123
}))

# 2. Terminal 5 traite
response = await native_client.get_balance(broker)
await redis.set(f'exchange_response_{request_id}', json.dumps(response))

# 3. Service lit réponse
response = await redis.get(f'exchange_response_{request_id}')
await redis.delete(f'exchange_response_{request_id}')  # Cleanup
```

## Décisions Architecturales

### Pourquoi Clients Natifs ?
1. **Performance** : 3x plus rapide que CCXT
2. **Contrôle** : Gestion fine rate limits
3. **Extensibilité** : Ajout exchanges facile
4. **Monitoring** : Logs détaillés par exchange

### Pourquoi Service Centralisé ?
1. **Rate Limiting** : Centralisé par exchange
2. **Connection Pooling** : Réutilisation instances
3. **Hot Reload** : Credentials sans restart
4. **Monitoring** : Statistiques globales

### Pourquoi PostgreSQL Seul ?
- **Multi-tenant** : Row-level security
- **Intégrité** : Foreign keys, transactions
- **Queries** : ORM Django mature
- **Simplicité** : Pas de sync MongoDB/Postgres

### Pourquoi asyncio pas Celery ?
- **Échelle** : 5 users, 20 stratégies max
- **Simplicité** : Pas d'orchestrateur externe
- **Performance** : asyncio suffisant
- **Philosophie** : Pragmatic > Enterprise

## Contraintes Système

### Limites Fondamentales
- **Users** : Max 5 utilisateurs
- **Stratégies** : Max 20 actives simultanément
- **Scale** : Personnel, pas SaaS

### Philosophie "Vibe Coding"
- **Fun > Perfection**
- **Shipping > Process**
- **Pragmatique > Enterprise**
- **Itération Rapide**

## Migration Guide

### De CCXT à Exchange Natif

**Services à migrer** :
1. TradingService → ✅ Migré (Jan 2026)
2. PortfolioService → ✅ Migré
3. TradingEngine → ✅ Migré
4. Webhooks → 🚧 Planned
5. Backtest → 🚧 Planned

**Pattern de migration** :
```python
# 1. Import
- from apps.core.services.ccxt_client import CCXTClient
+ from apps.core.services.exchange_client import ExchangeClient

# 2. Instanciation
- self.ccxt_client = CCXTClient()
+ self.exchange_client = ExchangeClient(user_id=user.id)

# 3. Appels (API identique)
- await self.ccxt_client.get_balance(broker_id)
+ await self.exchange_client.get_balance(broker_id)
```

## Monitoring

### Terminal 5 Statistics
```bash
python manage.py run_native_exchange_service --stats-interval 60

# Output
┌─ STATISTIQUES SERVICE NATIVE EXCHANGE ─────────────────┐
│ Uptime: 123m 45s  │  Exchanges: bitget, binance        │
│ Requêtes:   5432  │  Succès: 99.2%                     │
│ Échecs:        8  │  Temps moy: 354.2ms                │
│ Brokers:      12  │                                    │
└─────────────────────────────────────────────────────────┘
```

### Health Checks
- **Redis** : `redis-cli ping`
- **PostgreSQL** : `python manage.py dbshell`
- **Terminal 5** : Check queue `llen exchange_requests`
- **Heartbeat** : Table `HeartbeatStatus.is_connected`

## Références

- **Architecture** : `docs/CODEBASE_MAP.md`
- **Implementation** : `IMPLEMENTATION_PLAN.md`
- **Developer Guide** : `Aristobot3_1.md`
- **AI Instructions** : `.claude-instructions`

---

**Dernière mise à jour** : Janvier 2026 (Architecture native exchange consolidée)
