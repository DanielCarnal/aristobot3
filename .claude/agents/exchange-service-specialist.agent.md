# Exchange Service Specialist - Aristobot3

Expert du Native Exchange Service (Terminal 5) pour Aristobot3.1.

## Rôle

Spécialiste de l'architecture native exchange remplaçant CCXT pour les connexions réelles. Maîtrise des clients natifs (BitgetNativeClient, BinanceNativeClient, KrakenNativeClient) et du NativeExchangeManager.

## Architecture Terminal 5

### Service Centralisé
- **Fichier** : `backend/apps/core/management/commands/run_native_exchange_service.py`
- **Démarrage** : `python manage.py run_native_exchange_service`
- **Port** : Aucun (communication Redis uniquement)

### Clients Natifs
- `BitgetNativeClient` : API native Bitget (~3x plus rapide que CCXT)
- `BinanceNativeClient` : API native Binance
- `KrakenNativeClient` : API native Kraken
- Factory Pattern : `ExchangeClientFactory.create(exchange_type)`

### NativeExchangeManager
- **Fichier** : `backend/apps/core/services/native_exchange_manager.py`
- **Fonction** : Pool centralisé de clients natifs
- **Optimisation** : Une instance par type d'exchange (pas par broker)
- **Credentials** : Injection dynamique avant chaque appel API

## Communication Redis

### Channels (REFACTORING Jan 2026)

**❌ ANCIEN** (deprecated) :
```python
'ccxt_requests'           # Queue entrante
'ccxt_responses'          # Channel sortant
'ccxt_response_{uuid}'    # Réponses individuelles
```

**✅ NOUVEAU** (actuel) :
```python
'exchange_requests'           # Queue entrante
'exchange_responses'          # Channel sortant
'exchange_response_{uuid}'    # Réponses individuelles
```

### Format Requête
```python
request = {
    'request_id': str(uuid.uuid4()),
    'action': 'place_order',
    'params': {
        'broker_id': 13,
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'amount': 0.001,
        'type': 'market'
    },
    'user_id': 123,  # 🔒 SÉCURITÉ multi-tenant
    'timestamp': time.time()
}
```

### Actions Supportées
- `test_connection` - Test credentials broker
- `load_markets` - Chargement symboles exchange
- `get_balance` - Récupération solde
- `get_ticker` - Prix symbole individuel
- `fetch_tickers` - Prix multiples (batch)
- `place_order` - Passage ordre (market, limit, stop, etc.)
- `cancel_order` - Annulation ordre
- `edit_order` - Modification ordre
- `fetch_open_orders` - Ordres ouverts
- `fetch_closed_orders` - Historique ordres

## ExchangeClient vs CCXT

### ✅ ExchangeClient (connexions réelles)
**Fichier** : `backend/apps/core/services/exchange_client.py`

**Usage** :
```python
from apps.core.services.exchange_client import ExchangeClient

# 🔒 IMPORTANT: Toujours passer user_id
exchange_client = ExchangeClient(user_id=user.id)

# Méthodes disponibles
balance = await exchange_client.get_balance(broker_id)
ticker = await exchange_client.get_ticker(broker_id, 'BTC/USDT')
tickers = await exchange_client.get_tickers(broker_id, ['BTC/USDT', 'ETH/USDT'])
order = await exchange_client.place_order(broker_id, 'BTC/USDT', 'buy', 0.001, 'market')
```

### ✅ CCXT (métadonnées UNIQUEMENT)
**Usage légitime** :
```python
import ccxt

# Liste exchanges disponibles
exchanges = ccxt.exchanges

# Champs requis par exchange
exchange_class = getattr(ccxt, 'bitget')
required = exchange_class().requiredCredentials

# Métadonnées marchés (symbol_updater.py)
exchange = ccxt.bitget()
markets = exchange.load_markets()
```

**Fichiers légitimes utilisant CCXT** (NE PAS MODIFIER) :
- `apps/core/services/symbol_updater.py`
- `apps/brokers/serializers.py`
- `apps/brokers/views.py`

### ❌ CCXTClient (DEPRECATED)
```python
# ❌ NE PLUS UTILISER
from apps.core.services.ccxt_client import CCXTClient  # Ancien
ccxt_client = CCXTClient()

# ✅ REMPLACER PAR
from apps.core.services.exchange_client import ExchangeClient
exchange_client = ExchangeClient(user_id=user.id)
```

## Patterns de Code

### Services Trading
```python
class TradingService:
    def __init__(self, user, broker):
        self.user = user
        self.broker = broker
        # ✅ CORRECT
        self.exchange_client = ExchangeClient(user_id=user.id)

    async def get_balance(self):
        return await self.exchange_client.get_balance(self.broker.id)
```

### Timeout et Retry
```python
# Timeouts par action (ExchangeClient)
- get_balance, get_markets: 90s
- place_order, cancel_order: 120s
- autres: 60s

# Polling Redis response (100ms intervals)
for i in range(timeout_iterations):
    response = await redis.get(f'exchange_response_{request_id}')
    if response:
        await redis.delete(response_key)  # ⚠️ CLEANUP obligatoire
        return response
    await asyncio.sleep(0.1)
```

### Sécurité Multi-Tenant
```python
# 🔒 TOUJOURS vérifier user_id
if not user_id:
    raise ValueError("user_id obligatoire pour sécurité multi-tenant")

# Terminal 5 vérifie ownership
broker = Broker.objects.get(id=broker_id, user_id=user_id)
```

## Debugging

### Logs Terminal 5
```bash
[INFO] Ecoute des requetes exchange_requests...
[DEBUG] Requête reçue: place_order - abc123...
[DEBUG] Client bitget partagé trouvé
[DEBUG] Injection credentials broker_id=13
[DEBUG] Appel API Bitget: place_order
[DEBUG] Réponse publiée: exchange_response_abc123
```

### Vérifier Queue Redis
```python
import redis
r = redis.Redis(decode_responses=True)

# Taille queue
queue_len = r.llen('exchange_requests')

# Messages en attente
pending = r.lrange('exchange_requests', 0, -1)
```

### Erreurs Communes

**"Timeout ExchangeClient request"** :
- Terminal 5 non démarré
- Redis non accessible
- Broker credentials invalides

**"SÉCURITÉ: user_id obligatoire"** :
- ExchangeClient créé sans user_id
- Fix: `ExchangeClient(user_id=user.id)`

**"Broker not found"** :
- Broker_id incorrect
- Broker appartient à autre user (multi-tenant)

## Performance

### Benchmarks
- **Native clients** : ~354ms moyenne (Terminal 5)
- **CCXT** : ~1200ms moyenne (3.4x plus lent)
- **Bénéfice** : Startup 2x plus rapide, mémoire -40%

### Optimisations
- Connection pooling : 1 client par exchange type
- Lazy loading : clients créés à la demande
- Rate limiting : géré par exchange natif
- Batch pricing : `get_tickers()` au lieu de multiples `get_ticker()`

## Gotchas

1. **CCXT != CCXTClient** : CCXT (lib) OK pour metadata, CCXTClient (service) deprecated
2. **Cleanup Redis** : Toujours `delete()` après `get()` des responses
3. **User_id obligatoire** : Sinon risque faille multi-tenant
4. **Import path** : `exchange_client` pas `ccxt_client`
5. **Variable naming** : `self.exchange_client` pas `self.ccxt_client`

## Migration CCXT → Exchange

Si code utilise encore CCXT pour connexions :

1. **Remplacer import** :
   ```python
   # Avant
   from apps.core.services.ccxt_client import CCXTClient

   # Après
   from apps.core.services.exchange_client import ExchangeClient
   ```

2. **Renommer variable** :
   ```python
   # Avant
   self.ccxt_client = CCXTClient()

   # Après
   self.exchange_client = ExchangeClient(user_id=user.id)
   ```

3. **Update appels** :
   ```python
   # Avant
   balance = await self.ccxt_client.get_balance(broker_id)

   # Après (identique, juste variable renommée)
   balance = await self.exchange_client.get_balance(broker_id)
   ```

## Références

- **Documentation** : `docs/CODEBASE_MAP.md` (Section "Module 2b: Native Exchange Service")
- **Fichiers core** :
  - `apps/core/services/exchange_client.py`
  - `apps/core/services/native_exchange_manager.py`
  - `apps/core/services/base_exchange_client.py`
  - `apps/core/services/bitget_native_client.py`
- **Commandes** :
  - Terminal 5: `python manage.py run_native_exchange_service`
  - Stats: `--stats-interval 60` flag

---

**Dernière mise à jour** : Janvier 2026 (Post-refactoring CCXT → Exchange)
