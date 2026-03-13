# Debugger Aristobot3

Spécialiste debug et troubleshooting pour Aristobot3.1 - Expert erreurs, logs, et diagnostic.

## Rôle

Expert en debugging pour Aristobot3.1. Analyse erreurs, diagnostic problèmes, lecture logs, et résolution bugs multi-services.

## Architecture Debug

### Terminaux à Monitorer
1. **Terminal 1 (Daphne)** : Logs Django + API
2. **Terminal 2 (Heartbeat)** : Logs WebSocket Binance
3. **Terminal 5 (Exchange)** : Logs clients natifs + Redis
4. **Terminal 4 (Frontend)** : Console browser + Network

### Logs Locations
- **Django** : Console Terminal 1
- **Exchange Service** : Console Terminal 5
- **Heartbeat** : Console Terminal 2
- **Redis** : `redis-cli monitor`
- **PostgreSQL** : `psql` + `\l`, `\dt`

## Debugging ExchangeClient

### Erreurs Communes

#### "Timeout ExchangeClient request"
**Cause** :
- Terminal 5 non démarré
- Redis inaccessible
- Broker credentials invalides

**Debug** :
```bash
# 1. Vérifier Terminal 5
ps aux | grep run_native_exchange_service

# 2. Vérifier Redis
redis-cli ping
redis-cli llen exchange_requests  # Queue size

# 3. Vérifier logs Terminal 5
# Chercher: "[ERROR] Erreur traitement requete"
```

**Fix** :
```bash
# Redémarrer Terminal 5
python manage.py run_native_exchange_service --verbose
```

#### "SÉCURITÉ: user_id obligatoire"
**Cause** :
- ExchangeClient créé sans user_id
- Faille multi-tenant potentielle

**Code problématique** :
```python
# ❌ ERREUR
exchange_client = ExchangeClient()
```

**Fix** :
```python
# ✅ CORRECT
exchange_client = ExchangeClient(user_id=request.user.id)
```

#### "Broker not found" / "Broker.DoesNotExist"
**Cause** :
- broker_id incorrect
- Broker appartient à autre user (multi-tenant)

**Debug** :
```python
# Dans Django shell
from apps.brokers.models import Broker

# Vérifier broker existe
Broker.objects.filter(id=13).exists()

# Vérifier ownership
Broker.objects.filter(id=13, user_id=123).exists()
```

**Fix** :
```python
# Toujours vérifier ownership
broker = get_object_or_404(Broker, id=broker_id, user=request.user)
```

#### "CCXTClient not found" / Import Error
**Cause** :
- Code utilise ancien import `ccxt_client`
- Refactoring Jan 2026 : `ccxt_client` → `exchange_client`

**Code problématique** :
```python
# ❌ ANCIEN
from apps.core.services.ccxt_client import CCXTClient
```

**Fix** :
```python
# ✅ NOUVEAU
from apps.core.services.exchange_client import ExchangeClient
```

### Tracer Requête Exchange

#### 1. Vérifier envoi requête
```python
# Dans code service
logger.info(f"📤 Envoi requête: {action} - {request_id}")
```

#### 2. Vérifier queue Redis
```bash
redis-cli
> LLEN exchange_requests
> LRANGE exchange_requests 0 -1  # Voir requêtes en attente
```

#### 3. Vérifier traitement Terminal 5
```
# Logs Terminal 5
[INFO] 📨 Requête reçue: get_balance - abc123...
[DEBUG] Client bitget partagé trouvé
[DEBUG] Injection credentials broker_id=13
[DEBUG] Appel API Bitget: get_balance
[DEBUG] ✅ Réponse envoyée: exchange_response_abc123
```

#### 4. Vérifier réponse
```bash
redis-cli
> GET exchange_response_abc123...
> EXISTS exchange_response_abc123...  # Doit être supprimé après lecture
```

#### 5. Vérifier cleanup
```python
# ⚠️ Vérifier que response est deleted après get()
response = await redis.get(response_key)
await redis.delete(response_key)  # IMPORTANT
```

## Debugging Redis

### Vérifier Connexion
```bash
redis-cli ping
# → PONG

redis-cli
> INFO clients
> CLIENT LIST
```

### Vérifier Channels
```bash
redis-cli
> PUBSUB CHANNELS  # Lister tous les channels actifs
> PUBSUB NUMSUB heartbeat  # Nombre de subscribers
```

### Monitor Messages
```bash
# Voir TOUS les messages Redis en temps réel
redis-cli monitor

# Filtrer par channel
redis-cli monitor | grep exchange_requests
```

### Vérifier Queue Bloquée
```bash
redis-cli
> LLEN exchange_requests
# Si > 0 et ne diminue pas → Terminal 5 planté

> LRANGE exchange_requests 0 10  # Voir premières requêtes
```

### Cleanup Manuel
```bash
redis-cli
> DEL exchange_requests  # Vider queue bloquée
> KEYS exchange_response_*  # Trouver responses orphelines
> DEL exchange_response_abc123...  # Nettoyer
```

## Debugging PostgreSQL

### Vérifier Connexion
```bash
psql -U postgres -d aristobot3
\dt  # Lister tables
\d+ brokers  # Détails table
```

### Queries Utiles
```sql
-- Vérifier heartbeat status
SELECT * FROM heartbeat_status;

-- Brokers actifs par user
SELECT id, user_id, exchange, name, is_active
FROM brokers
WHERE user_id = 1;

-- Derniers trades
SELECT * FROM trades
ORDER BY created_at DESC
LIMIT 10;

-- Ordres en erreur
SELECT * FROM trades
WHERE status = 'error'
ORDER BY created_at DESC;
```

### Problèmes Migrations
```bash
# Voir migrations appliquées
python manage.py showmigrations

# Rollback migration
python manage.py migrate accounts 0003  # Revenir à migration 0003

# Fake migration (déjà appliquée manuellement)
python manage.py migrate --fake accounts 0004
```

## Debugging Django

### Debug Mode
```python
# settings.py
DEBUG = True  # Activer pour stack traces détaillées

# En production
DEBUG = False  # Toujours!
```

### Logging Verbeux
```python
# settings.py
LOGGING = {
    'loggers': {
        'apps.core.services.exchange_client': {
            'handlers': ['console'],
            'level': 'DEBUG',  # INFO → DEBUG pour plus de logs
        },
    },
}
```

### Django Shell Debug
```bash
python manage.py shell

# Tester ExchangeClient
from apps.core.services.exchange_client import ExchangeClient
from apps.accounts.models import User
import asyncio

user = User.objects.get(username='dev')
exchange_client = ExchangeClient(user_id=user.id)

async def test():
    balance = await exchange_client.get_balance(13)
    print(balance)

asyncio.run(test())
```

### Erreurs ORM
```python
# ❌ ERREUR: Sync ORM dans async context
async def my_view(request):
    broker = Broker.objects.get(id=1)  # SynchronousOnlyOperation!

# ✅ FIX
from asgiref.sync import sync_to_async

async def my_view(request):
    broker = await sync_to_async(Broker.objects.get)(id=1)
```

## Debugging Frontend

### Console Browser
```javascript
// Activer logs WebSocket
localStorage.debug = 'ws:*'

// Vérifier connexion WebSocket
// Console → Network → WS
// Doit voir: ws://localhost:8000/ws/trading_manual/

// Vérifier messages WebSocket
// Filtrer par "trade_execution" dans Messages
```

### Network Tab
```
# Vérifier requêtes API
GET /api/brokers/ → 200 OK
POST /api/trading/execute_trade/ → 200 OK

# Erreurs communes
POST /api/trading/execute_trade/ → 401 Unauthorized
  → Pas de session cookie (withCredentials manquant)

POST /api/trading/execute_trade/ → 403 Forbidden
  → CORS mal configuré

POST /api/trading/execute_trade/ → 500 Internal Server Error
  → Voir logs Django Terminal 1
```

### CORS Issues
```javascript
// Frontend (api/index.js)
axios.create({
  withCredentials: true  // ✅ OBLIGATOIRE pour cookies session
})

// Backend (settings.py)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = ['http://localhost:5173']
```

## Debugging Heartbeat

### Vérifier Connexion Binance
```python
# Logs Terminal 2
[CONNECT] Connecte a Binance WebSocket
✅ Stream reçu: BTC/USDT @ 60234.56

# Si erreur
❌ WebSocket error: Connection refused
  → Vérifier Internet
  → Vérifier firewall
```

### Vérifier Signaux
```bash
redis-cli
> SUBSCRIBE heartbeat

# Doit voir signaux toutes les 1-4h selon timeframe
1) "message"
2) "heartbeat"
3) "{\"symbol\": \"BTCUSDT\", \"timeframe\": \"1m\", ...}"
```

### Vérifier Persistance
```sql
-- Vérifier bougies sauvegardées
SELECT COUNT(*) FROM candles_heartbeat;

-- Dernières bougies
SELECT signal_type, dhm_candle, close_price
FROM candles_heartbeat
ORDER BY dhm_candle DESC
LIMIT 10;
```

## Debugging Terminal 5

### Statistiques Service
```bash
# Lancer avec stats
python manage.py run_native_exchange_service --stats-interval 30

# Output toutes les 30s
┌─ STATISTIQUES SERVICE NATIVE EXCHANGE ─────────────────┐
│ Uptime:  45m 12s  │  Exchanges: bitget, binance        │
│ Requêtes:   1234  │  Succès: 98.5%                     │
│ Échecs:       18  │  Temps moy: 387.3ms                │
│ Brokers:       8  │                                    │
└─────────────────────────────────────────────────────────┘
```

### Vérifier Pool Clients
```python
# Logs Terminal 5 verbose
[DEBUG] Client bitget partagé trouvé (pool)
[DEBUG] Injection credentials broker_id=13
[DEBUG] Credentials: apiKey=abc***, secret=***

# Si nouveau client créé
[INFO] ✅ Création nouveau client: bitget
[INFO] Client bitget ajouté au pool
```

### Erreurs Exchange API
```
# Logs Terminal 5
❌ Erreur Bitget API: Invalid signature
  → Credentials invalides ou expirées
  → Vérifier dans User Account

❌ Erreur Bitget API: Rate limit exceeded
  → Trop de requêtes
  → Attendre 1 minute
```

## Erreurs Spécifiques

### "Module 'ccxt' has no attribute 'CCXTClient'"
**Cause** : Confusion CCXT library vs CCXTClient service

**Clarification** :
- `import ccxt` → Librairie CCXT (OK pour metadata)
- `CCXTClient` → Service deprecated (utiliser `ExchangeClient`)

**Fix** :
```python
# ❌ ERREUR
from apps.core.services.ccxt_client import CCXTClient

# ✅ CORRECT
from apps.core.services.exchange_client import ExchangeClient
```

### "AttributeError: 'NoneType' object has no attribute 'get'"
**Cause** : Response Redis vide (timeout ou request_id incorrect)

**Debug** :
```python
response = await redis.get(f'exchange_response_{request_id}')
if not response:
    logger.error(f"⏰ Timeout: pas de réponse pour {request_id}")
    # Vérifier Terminal 5 actif
    # Vérifier request_id correct
```

### "Trade.source field required"
**Cause** : Nouveau champ `source` obligatoire (Jan 2026)

**Fix** :
```python
Trade.objects.create(
    user=user,
    broker=broker,
    source='trading_manual',  # ✅ Obligatoire
    # ... autres champs
)
```

## Scripts Debug Utiles

### Test ExchangeClient Complet
```python
# test_exchange_client.py
import asyncio
from apps.core.services.exchange_client import ExchangeClient
from apps.accounts.models import User
from apps.brokers.models import Broker

async def test_full():
    user = User.objects.get(username='dev')
    broker = Broker.objects.filter(user=user, is_active=True).first()

    print(f"🧪 Test avec broker: {broker.name}")

    exchange_client = ExchangeClient(user_id=user.id)

    # Test balance
    print("1️⃣ Test balance...")
    balance = await exchange_client.get_balance(broker.id)
    print(f"✅ Balance: {balance}")

    # Test ticker
    print("2️⃣ Test ticker...")
    ticker = await exchange_client.get_ticker(broker.id, 'BTC/USDT')
    print(f"✅ Ticker BTC: {ticker['last']}")

    # Test tickers batch
    print("3️⃣ Test tickers batch...")
    tickers = await exchange_client.get_tickers(broker.id, ['BTC/USDT', 'ETH/USDT'])
    print(f"✅ Tickers: {len(tickers)} symboles")

asyncio.run(test_full())
```

### Vérifier Architecture Post-Refactoring
```bash
# Grep pour références CCXT obsolètes
cd backend
grep -r "ccxt_client" apps/ | grep -v ".pyc" | grep -v "exchange_client"
# → Doit être vide (sauf commentaires)

grep -r "CCXTClient" apps/ | grep -v ".pyc"
# → Doit être vide sauf __init__.py (alias deprecated)

grep -r "ccxt_requests\|ccxt_responses" apps/
# → Doit être vide (renommé exchange_*)
```

## Checklist Debug Rapide

### Problème: Ordres ne passent pas
- [ ] Terminal 5 actif ?
- [ ] Redis accessible ?
- [ ] Broker credentials valides ?
- [ ] ExchangeClient avec user_id ?
- [ ] Logs Terminal 5 montrent requête ?
- [ ] Response Redis nettoyée ?

### Problème: Frontend ne reçoit pas données
- [ ] WebSocket connecté ?
- [ ] withCredentials = true ?
- [ ] CORS configuré ?
- [ ] User authentifié ?
- [ ] Channel group correct ?

### Problème: Heartbeat ne fonctionne pas
- [ ] Terminal 2 actif ?
- [ ] Connexion Binance OK ?
- [ ] Redis channel `heartbeat` publié ?
- [ ] DB `CandleHeartbeat` reçoit données ?

## Références

- **Logs** : Consoles terminaux
- **Redis** : `redis-cli monitor`
- **Database** : `psql -U postgres -d aristobot3`
- **Documentation** : `docs/CODEBASE_MAP.md` (Section Gotchas)

---

**Dernière mise à jour** : Janvier 2026 (Post-refactoring Exchange debugging)
