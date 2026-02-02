# Terminal 5 - Exchange Gateway Architecture

**Version:** 2.0
**Date:** 2026-01-21
**Statut:** Architecture validée via Party Mode (John PM, Winston Architect, Barry Dev, Murat TEA, Dr. Quinn Problem Solver)
**Contexte:** Décisions architecturales pour Aristobot3 Modules 4-8

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Format Unifié](#format-unifié)
3. [Architecture Service Centralisé](#architecture-service-centralisé)
4. [Système de Paramètres 3 Niveaux](#système-de-paramètres-3-niveaux)
5. [Gestion Kraken userref](#gestion-kraken-userref)
6. [Normalisation des Statuts](#normalisation-des-statuts)
7. [Stockage Dual](#stockage-dual)
8. [Monitoring & Opérations](#monitoring--opérations)
9. [Tests & Validation](#tests--validation)
10. [Extensibilité](#extensibilité)
11. [Exemples de Code](#exemples-de-code)

---

## Vue d'ensemble

### Objectif
Terminal 5 est le **hub centralisé** pour toutes les interactions avec les exchanges via APIs natives. Il fournit une **couche d'abstraction** qui :
- Convertit les requêtes unifiées → appels natifs spécifiques
- Normalise les réponses natives → format unifié Aristobot
- Garantit la cohérence multi-exchange
- Optimise les performances (~3x plus rapide que CCXT)

### Responsabilités
- ✅ Gestion pool de clients natifs (Bitget, Binance, Kraken)
- ✅ Injection dynamique des credentials par requête
- ✅ Conversion format bidirectionnelle (Aristobot ↔ Native)
- ✅ Rate limiting optimisé par exchange
- ✅ Persistance complète (format unifié + réponse brute)
- ✅ Monitoring et observabilité

### Exchanges Supportés
- **Bitget** (45%) - Client natif principal
- **Binance** (35%) - Client natif
- **Kraken** (20%) - Client natif avec gestion spéciale `userref`

---

## Format Unifié

### Principe
Format **CCXT-inspiré** avec **extensions Aristobot** pour le multi-tenant et la traçabilité.

### Champs Standard

#### Requête Unifiée
```python
unified_request = {
    # === CCXT-inspired (compatibilité) ===
    "symbol": "BTC/USDT",           # Format CCXT standard
    "side": "buy",                   # buy/sell
    "type": "limit",                 # market/limit/stop_loss/take_profit
    "quantity": 0.1,                 # Quantité d'actif
    "price": 43000.0,                # Prix (obligatoire pour limit)

    # === Extensions Aristobot (multi-tenant + traçabilité) ===
    "user_id": 1,                    # Utilisateur propriétaire
    "broker_id": 5,                  # Broker utilisé
    "source": "manual",              # manual/strategy/webhook

    # === Level 1 Critical Parameters ===
    "client_order_id": "ARISTO_1_1706000000_abc123",  # Idempotence
    "time_in_force": "GTC",          # GTC/IOC/FOK
    "reduce_only": False,            # Position reduction uniquement
    "stop_price": 42000.0,           # Prix trigger stop
    "position_side": "LONG",         # LONG/SHORT (futures)
    "margin_mode": "isolated",       # isolated/cross (futures)

    # === Level 2 Important Parameters ===
    "stop_loss_price": 41000.0,      # Stop loss associé
    "take_profit_price": 45000.0,    # Take profit associé

    # === Level 3 Exotic Parameters ===
    "extra_params": {
        "bitget_specific_flag": True,
        "custom_tag": "strategy_v2"
    }
}
```

#### Réponse Unifiée
```python
unified_response = {
    # === Champs Aristobot ===
    "user_id": 1,
    "broker_id": 5,
    "source": "manual",
    "request_id": "uuid-1234",
    "timestamp": "2026-01-21T14:32:15.000Z",

    # === Champs CCXT-inspired ===
    "id": "1234567890",              # ID exchange natif
    "client_order_id": "ARISTO_1_1706000000_abc123",
    "symbol": "BTC/USDT",
    "side": "buy",
    "type": "limit",
    "quantity": 0.1,
    "price": 43000.0,
    "filled": 0.05,                  # Quantité exécutée
    "remaining": 0.05,               # Quantité restante
    "status": "open",                # Statut normalisé Aristobot
    "native_status": "NEW",          # Statut original exchange
    "fee": 0.0004,                   # Frais de trading
    "fee_currency": "USDT",
    "trades": [],                    # Liste des exécutions partielles

    # === Métadonnées ===
    "exchange": "binance",
    "created_at": "2026-01-21T14:32:15.000Z",
    "updated_at": "2026-01-21T14:32:15.000Z"
}
```

### Principes Clés
1. **Compatibilité CCXT** : Facilite migration depuis CCXT
2. **Extensions Aristobot** : Multi-tenant, traçabilité, source
3. **Préservation complète** : Aucun champ tronqué
4. **Cohérence** : Tous les exchanges retournent le même format

---

## Architecture Service Centralisé

### Option B Validée : 1 Instance par Type d'Exchange

#### Principe
Au lieu de créer une instance par `(user_id, broker_id)`, Terminal 5 maintient **1 seul client natif par type d'exchange** et injecte les credentials dynamiquement.

```python
# ❌ ANCIEN (1 instance par user/broker)
exchange_pool = {
    (1, 5): BitgetNativeClient(user1_broker5_keys),
    (1, 6): BitgetNativeClient(user1_broker6_keys),
    (2, 7): BitgetNativeClient(user2_broker7_keys),
}

# ✅ NOUVEAU (1 instance par type)
exchange_pool = {
    'bitget': BitgetNativeClient(),
    'binance': BinanceNativeClient(),
    'kraken': KrakenNativeClient(),
}

# Injection credentials dynamique
def execute_request(broker_id, request):
    broker = get_broker(broker_id)
    client = exchange_pool[broker.exchange]

    # Injection temporaire credentials
    client.inject_credentials(
        api_key=broker.api_key,
        api_secret=broker.api_secret,
        api_password=broker.api_password  # Si nécessaire
    )

    result = client.execute(request)
    return result
```

#### Avantages
- ✅ **Performance** : Chargement initial 3x plus rapide (1 instance bitget au lieu de 10)
- ✅ **Mémoire** : Consommation réduite
- ✅ **Maintenance** : Un seul point de configuration par exchange
- ✅ **Rate Limiting** : Gestion globale par exchange

#### Affichage Optimisé
```
Premier broker:  bitget/1             → Loading → OK (35s)
Deuxième broker: bitget/Aristobot2-v1 → SHARED (0s instantané)
```

#### Implémentation
```python
class NativeExchangeManager:
    def __init__(self):
        self.exchange_instances = {}  # {'bitget': BitgetClient, ...}
        self.broker_cache = {}        # Cache brokers actifs

    async def get_client(self, broker_id: int):
        """Récupère client avec injection credentials"""
        broker = await self._get_broker(broker_id)

        # Obtenir ou créer l'instance exchange
        if broker.exchange not in self.exchange_instances:
            self.exchange_instances[broker.exchange] = \
                ExchangeClientFactory.create(broker.exchange)

        client = self.exchange_instances[broker.exchange]

        # Injection credentials pour cette requête
        client.set_credentials(
            api_key=decrypt(broker.api_key),
            api_secret=decrypt(broker.api_secret),
            api_password=decrypt(broker.api_password) if broker.api_password else None
        )

        return client
```

---

## Système de Paramètres 3 Niveaux

### Objectif
Gérer la diversité des paramètres entre exchanges tout en maintenant la cohérence.

### Level 1 : Critical Parameters (Obligatoires)

**11 paramètres critiques** supportés par tous les exchanges :

```python
CRITICAL_PARAMS = [
    'client_order_id',   # Idempotence (OBLIGATOIRE)
    'symbol',            # Paire trading
    'side',              # buy/sell
    'type',              # market/limit/stop
    'quantity',          # Quantité
    'price',             # Prix (si limit)
    'time_in_force',     # GTC/IOC/FOK
    'reduce_only',       # Réduction position uniquement
    'stop_price',        # Prix trigger
    'position_side',     # LONG/SHORT (futures)
    'margin_mode',       # isolated/cross (futures)
]
```

**Règle** : Si un exchange ne supporte pas un paramètre Level 1, **refuser l'ordre** avec erreur explicite.

```python
if not exchange_supports(param) and param in CRITICAL_PARAMS:
    raise UnsupportedParameterError(
        f"Exchange {exchange_name} ne supporte pas {param} (Critical Level 1)"
    )
```

### Level 2 : Important Parameters (Best-Effort)

Paramètres importants mais non critiques :

```python
IMPORTANT_PARAMS = [
    'stop_loss_price',   # Stop loss associé
    'take_profit_price', # Take profit associé
    'trailing_delta',    # Trailing stop delta
    'iceberg_qty',       # Quantité iceberg
]
```

**Règle** : Mapper si supporté, sinon **log warning** et continuer.

```python
if not exchange_supports(param) and param in IMPORTANT_PARAMS:
    logger.warning(f"⚠️ {exchange_name} ne supporte pas {param} - Ignoré")
```

### Level 3 : Exotic Parameters (Passthrough)

Paramètres spécifiques à un exchange :

```python
# Exemple : Ordre Bitget avec flag spécial
request = {
    'symbol': 'BTC/USDT',
    'side': 'buy',
    'type': 'limit',
    'quantity': 0.1,
    'price': 43000,

    'extra_params': {
        'force': 'gtc',              # Bitget specific
        'clientOid': 'custom_123',   # Override client_order_id
        'presetTakeProfitPrice': 45000,  # Bitget TP
    }
}
```

**Règle** : Passer directement à l'API native sans validation.

```python
# Fusion avec extra_params
native_params = {**critical_params, **important_params, **extra_params}
```

---

## Gestion Kraken userref

### Problème
- **Bitget/Binance** : `client_order_id` = string (max 128 chars)
- **Kraken** : `userref` = int32 (max 2,147,483,647)

### Solution : Hash + Cache Redis

#### Algorithme
```python
import hashlib
import redis

KRAKEN_USERREF_MAX = 2147483647

def generate_kraken_userref(client_order_id: str) -> int:
    """
    Convertit string client_order_id → int32 userref
    Gère collisions avec cache Redis
    """
    # Hash SHA256 → int32
    hash_bytes = hashlib.sha256(client_order_id.encode()).digest()
    userref = int.from_bytes(hash_bytes[:4], 'big') % KRAKEN_USERREF_MAX

    # Vérifier collision dans Redis
    redis_client = get_redis_client()
    cache_key = f"kraken_userref:{userref}"
    existing = redis_client.get(cache_key)

    if existing and existing != client_order_id:
        # Collision détectée - incrémenter
        logger.warning(
            f"⚠️ Collision Kraken userref {userref}: "
            f"{existing} vs {client_order_id}"
        )
        userref = (userref + 1) % KRAKEN_USERREF_MAX

    # Sauvegarder mapping (TTL 30 jours)
    redis_client.setex(cache_key, 2592000, client_order_id)

    # Mapping inverse pour récupération
    redis_client.setex(
        f"kraken_client_order_id:{client_order_id}",
        2592000,
        userref
    )

    return userref

def reverse_kraken_userref(userref: int) -> str:
    """Récupère client_order_id depuis userref"""
    redis_client = get_redis_client()
    return redis_client.get(f"kraken_userref:{userref}")
```

#### Intégration Terminal 5
```python
class KrakenNativeClient(BaseExchangeClient):
    def place_order(self, request):
        # Conversion client_order_id → userref
        client_order_id = request['client_order_id']
        userref = generate_kraken_userref(client_order_id)

        # Appel API Kraken
        kraken_request = {
            'pair': self._convert_symbol(request['symbol']),
            'type': request['side'],
            'ordertype': request['type'],
            'volume': request['quantity'],
            'userref': userref,  # int32
        }

        response = self.api.add_order(**kraken_request)

        # Réponse unifiée avec client_order_id original
        return {
            'client_order_id': client_order_id,  # String original
            'native_userref': userref,           # int32 Kraken
            'id': response['txid'][0],
            # ... autres champs
        }
```

#### Risques & Mitigations
- **Collision** : Probabilité faible (1/2^32), détection + incrémentation
- **Cache perdu** : Redis persistence + backup si Redis flush
- **TTL expiré** : 30 jours largement suffisant pour ordres (max quelques jours)

---

## Normalisation des Statuts

### Problème
Chaque exchange a ses propres statuts :

```python
# Bitget
'new', 'partial-fill', 'full-fill', 'cancelled', 'expired'

# Binance
'NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'PENDING_CANCEL', 'REJECTED', 'EXPIRED'

# Kraken
'pending', 'open', 'closed', 'canceled', 'expired'
```

### Solution : Mapping Vers Standard Aristobot

#### Statuts Standard
```python
ARISTOBOT_STATUSES = [
    'open',       # Ordre actif (NEW, pending, partial-fill)
    'closed',     # Ordre complètement exécuté (FILLED, full-fill, closed)
    'cancelled',  # Ordre annulé (CANCELED, canceled, cancelled)
    'UNKNOWN',    # Statut inconnu (fallback)
]
```

#### Tables de Mapping
```python
STATUS_MAPPING = {
    'bitget': {
        'new': 'open',
        'partial-fill': 'open',
        'full-fill': 'closed',
        'cancelled': 'cancelled',
        'expired': 'cancelled',
    },
    'binance': {
        'NEW': 'open',
        'PARTIALLY_FILLED': 'open',
        'FILLED': 'closed',
        'CANCELED': 'cancelled',
        'PENDING_CANCEL': 'open',  # Encore actif
        'REJECTED': 'cancelled',
        'EXPIRED': 'cancelled',
    },
    'kraken': {
        'pending': 'open',
        'open': 'open',
        'closed': 'closed',
        'canceled': 'cancelled',
        'expired': 'cancelled',
    },
}
```

#### Implémentation
```python
def normalize_status(exchange: str, native_status: str) -> str:
    """
    Normalise statut natif → statut Aristobot standard
    Gère statuts inconnus avec alertes
    """
    mapping = STATUS_MAPPING.get(exchange, {})

    if native_status in mapping:
        return mapping[native_status]
    else:
        # Statut inconnu - Log + Alert
        logger.warning(
            f"🚨 UNKNOWN STATUS: {exchange} returned '{native_status}'"
        )

        # Alert Discord pour investigation
        send_discord_alert(
            f"🆕 Nouveau statut {exchange}: `{native_status}`\n"
            f"Ajouter mapping dans STATUS_MAPPING"
        )

        # Retourner UNKNOWN (ne pas crash)
        return 'UNKNOWN'
```

#### Gestion "UNKNOWN"
- **Interface** : Afficher badge orange "STATUT INCONNU"
- **DB** : Stocker `status='UNKNOWN'` + `native_status` dans raw_response
- **Investigation** : Discord alert → dev vérifie → ajoute mapping → redéploie

---

## Stockage Dual

### Principe
**Stocker 2 formats** pour flexibilité maximale :

1. **Format unifié** : Champs normalisés pour logique applicative
2. **raw_response** : Réponse brute JSONB pour audit/debug

### Schéma PostgreSQL
```sql
-- Table trades avec stockage dual
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    broker_id INTEGER NOT NULL,
    source VARCHAR(20) NOT NULL,  -- manual/strategy/webhook

    -- === Format Unifié (colonnes typées) ===
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL,
    type VARCHAR(20) NOT NULL,
    quantity NUMERIC(20, 8) NOT NULL,
    price NUMERIC(20, 8),
    filled NUMERIC(20, 8),
    status VARCHAR(20) NOT NULL,  -- Statut normalisé
    client_order_id VARCHAR(128) NOT NULL,
    exchange_order_id VARCHAR(128),

    -- === Raw Response (JSONB) ===
    raw_response JSONB NOT NULL,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT unique_client_order_id UNIQUE (client_order_id)
);

-- Index GIN pour recherches JSONB rapides
CREATE INDEX idx_raw_response_gin ON trades USING GIN (raw_response);

-- Index spécifiques JSONB
CREATE INDEX idx_raw_clientoid ON trades ((raw_response->>'clientOid'));
CREATE INDEX idx_raw_native_status ON trades ((raw_response->>'status'));
```

### Exemples de Requêtes

#### Recherche par client_order_id natif
```sql
-- Bitget clientOid
SELECT * FROM trades
WHERE raw_response->>'clientOid' = 'ARISTO_1_1706000000_abc';

-- Kraken userref
SELECT * FROM trades
WHERE (raw_response->'userref')::int = 1234567;
```

#### Audit complet d'un ordre
```sql
SELECT
    id,
    symbol,
    side,
    status,                        -- Statut normalisé
    raw_response->>'status' AS native_status,  -- Statut original
    raw_response                   -- Réponse complète
FROM trades
WHERE client_order_id = 'ARISTO_1_1706000000_abc';
```

#### Statistiques par exchange
```sql
SELECT
    raw_response->>'exchange' AS exchange,
    COUNT(*) AS total_orders,
    AVG(filled::numeric / quantity::numeric) AS avg_fill_rate
FROM trades
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY raw_response->>'exchange';
```

### Sauvegarde Terminal 5
```python
async def save_trade_response(unified_response, native_response):
    """
    Sauvegarde format dual : unifié (colonnes) + brut (JSONB)
    """
    trade = await Trade.objects.create(
        # Format unifié (colonnes typées)
        user_id=unified_response['user_id'],
        broker_id=unified_response['broker_id'],
        source=unified_response['source'],
        symbol=unified_response['symbol'],
        side=unified_response['side'],
        type=unified_response['type'],
        quantity=unified_response['quantity'],
        price=unified_response.get('price'),
        filled=unified_response.get('filled', 0),
        status=unified_response['status'],  # Normalisé
        client_order_id=unified_response['client_order_id'],
        exchange_order_id=unified_response.get('id'),

        # Raw response JSONB (réponse exchange brute)
        raw_response=native_response
    )

    logger.info(
        f"✅ Trade sauvegardé: {trade.client_order_id} "
        f"(status={trade.status}, native={native_response.get('status')})"
    )

    return trade
```

---

## Monitoring & Opérations

### Logs Rotatifs

#### Configuration Python
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_terminal5_logging():
    """
    Logs rotatifs : 10MB max, 5 fichiers backup
    """
    logger = logging.getLogger('terminal5')
    logger.setLevel(logging.INFO)

    # Handler rotatif
    handler = RotatingFileHandler(
        'logs/terminal5.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,          # 5 fichiers historiques
        encoding='utf-8'
    )

    # Format détaillé
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(request_id)s] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Utilisation avec UUID traçage
logger = setup_terminal5_logging()
logger.info(
    f"📤 Ordre reçu",
    extra={'request_id': request['request_id']}
)
```

#### Fichiers Générés
```
logs/
├── terminal5.log           # Actuel
├── terminal5.log.1         # Backup 1 (10MB)
├── terminal5.log.2         # Backup 2 (10MB)
├── terminal5.log.3         # Backup 3 (10MB)
├── terminal5.log.4         # Backup 4 (10MB)
└── terminal5.log.5         # Backup 5 (10MB) - Plus ancien
```

### Redis Heartbeat (Monitoring Hybride)

#### Principe
Chaque terminal publie son heartbeat → Watchdog surveille → Auto-défense locale pour dépendances critiques

#### Publication Heartbeat
```python
import redis
import time
import asyncio

class TerminalHeartbeat:
    def __init__(self, terminal_name: str):
        self.terminal_name = terminal_name
        self.redis_client = redis.Redis(decode_responses=True)

    async def start(self):
        """Publie heartbeat toutes les 10s"""
        while True:
            try:
                self.redis_client.setex(
                    f"terminal_heartbeat:{self.terminal_name}",
                    30,  # TTL 30s
                    int(time.time())
                )
                logger.debug(f"💓 Heartbeat {self.terminal_name} publié")
            except Exception as e:
                logger.error(f"❌ Erreur heartbeat: {e}")

            await asyncio.sleep(10)

# Utilisation Terminal 5
heartbeat = TerminalHeartbeat('terminal5')
asyncio.create_task(heartbeat.start())
```

#### Health Check Dashboard
```python
def check_terminals_health() -> dict:
    """
    Vérifie santé de tous les terminaux
    Retourne statut + dernier heartbeat
    """
    redis_client = redis.Redis(decode_responses=True)

    terminals = [
        'terminal1',  # Daphne
        'terminal2',  # Heartbeat
        'terminal3',  # Trading Engine
        'terminal5',  # Exchange Gateway
        'terminal7',  # Order Monitor
    ]

    status = {}
    current_time = time.time()

    for terminal in terminals:
        last_seen = redis_client.get(f"terminal_heartbeat:{terminal}")

        if last_seen:
            age = current_time - int(last_seen)

            if age < 30:
                status[terminal] = {"status": "🟢 UP", "age": f"{age:.0f}s"}
            elif age < 60:
                status[terminal] = {"status": "🟡 STALE", "age": f"{age:.0f}s"}
            else:
                status[terminal] = {"status": "🔴 DOWN", "age": f"{age:.0f}s"}
        else:
            status[terminal] = {"status": "🔴 DOWN", "age": "N/A"}

    return status

# Endpoint API Django
@api_view(['GET'])
def terminals_health_view(request):
    return Response(check_terminals_health())
```

#### Auto-Défense Locale (Monitoring Hybride)
```python
class TradingEngine:
    """
    Terminal 3 surveille ses dépendances critiques
    """
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.critical_dependencies = ['heartbeat', 'terminal5']

    async def check_dependencies(self):
        """Vérifie dépendances toutes les 30s"""
        while True:
            for dep in self.critical_dependencies:
                if not self._is_alive(dep):
                    await self._handle_dependency_failure(dep)

            await asyncio.sleep(30)

    def _is_alive(self, terminal: str) -> bool:
        """Vérifie si terminal est actif"""
        last_seen = self.redis_client.get(f"terminal_heartbeat:{terminal}")

        if not last_seen:
            return False

        age = time.time() - int(last_seen)
        return age < 60

    async def _handle_dependency_failure(self, terminal: str):
        """Gère défaillance dépendance"""
        if terminal == 'heartbeat':
            logger.error("🔴 HEARTBEAT DOWN - Pause stratégies")
            await self.pause_all_strategies()

        elif terminal == 'terminal5':
            logger.error("🔴 TERMINAL 5 DOWN - Mode dégradé")
            await self.enable_degraded_mode()
```

#### Table de Dépendances
```
Terminal 1 (Daphne)      → [Redis, PostgreSQL]
Terminal 2 (Heartbeat)   → [Binance WebSocket, Redis]
Terminal 3 (Trading Eng) → [Heartbeat, Terminal 5, Redis]  ← Surveille actif
Terminal 5 (Exchange)    → [Redis, PostgreSQL]
Terminal 7 (Monitor)     → [Terminal 5, PostgreSQL]         ← Surveille actif
```

### Watchdog Externe

#### Script Python Simple
```python
#!/usr/bin/env python3
"""
Watchdog Terminal - Surveillance et redémarrage automatique
"""
import subprocess
import time
import redis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('watchdog')

TERMINALS = {
    'terminal5': {
        'cmd': ['python', 'manage.py', 'run_native_exchange_service'],
        'cwd': '/path/to/aristobot3/backend',
    },
    'terminal7': {
        'cmd': ['python', 'manage.py', 'run_terminal7'],
        'cwd': '/path/to/aristobot3/backend',
    },
    # Ajouter autres terminaux...
}

def check_terminal_alive(terminal_name: str) -> bool:
    """Vérifie si terminal est actif via Redis heartbeat"""
    try:
        redis_client = redis.Redis(decode_responses=True)
        last_seen = redis_client.get(f"terminal_heartbeat:{terminal_name}")

        if not last_seen:
            return False

        age = time.time() - int(last_seen)
        return age < 60  # Max 60s sans heartbeat
    except Exception as e:
        logger.error(f"❌ Erreur vérification {terminal_name}: {e}")
        return False

def restart_terminal(terminal_name: str):
    """Redémarre un terminal"""
    config = TERMINALS[terminal_name]

    try:
        # Démarrer processus en arrière-plan
        process = subprocess.Popen(
            config['cmd'],
            cwd=config['cwd'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        logger.info(f"🔄 {terminal_name} redémarré (PID: {process.pid})")

        # Alert Discord
        send_discord_alert(
            f"🔄 **Watchdog**: {terminal_name} redémarré automatiquement"
        )

    except Exception as e:
        logger.error(f"❌ Erreur redémarrage {terminal_name}: {e}")
        send_discord_alert(
            f"🚨 **CRITICAL**: Impossible de redémarrer {terminal_name}\n"
            f"Erreur: {e}"
        )

def main():
    """Boucle principale watchdog"""
    logger.info("🐕 Watchdog Aristobot démarré")

    while True:
        for terminal_name in TERMINALS:
            if not check_terminal_alive(terminal_name):
                logger.warning(f"💀 {terminal_name} DOWN - Redémarrage...")
                restart_terminal(terminal_name)

        time.sleep(30)  # Vérification toutes les 30s

if __name__ == '__main__':
    main()
```

#### Démarrage Watchdog
```bash
# Lancer en arrière-plan
nohup python watchdog.py > logs/watchdog.log 2>&1 &

# Ou avec systemd (Linux)
sudo systemctl start aristobot-watchdog
```

---

## Tests & Validation

### Approche Pragmatique (5 Utilisateurs)

#### Validation Manuelle + Monitoring Continu
Plutôt que des tests automatisés complexes, approche **validation checklist + observabilité**.

#### Checklist Validation Par Exchange

**Template** :
```markdown
# ✅ Checklist Validation Exchange: [EXCHANGE_NAME]

## Phase 1 : Connexion
- [ ] Test connexion API keys valides
- [ ] Test connexion API keys invalides (erreur attendue)
- [ ] Vérification rate limiting (pas de ban)

## Phase 2 : Ordres Simples
- [ ] Ordre market buy (petit montant testnet)
- [ ] Ordre market sell
- [ ] Ordre limit buy
- [ ] Ordre limit sell
- [ ] Vérification format unifié retourné

## Phase 3 : Ordres Avancés
- [ ] Ordre stop loss
- [ ] Ordre take profit
- [ ] Ordre avec time_in_force=IOC
- [ ] Ordre avec reduce_only=True (futures)

## Phase 4 : Opérations
- [ ] Fetch open orders
- [ ] Fetch closed orders
- [ ] Cancel order
- [ ] Edit order (si supporté)

## Phase 5 : Normalisation
- [ ] Vérifier tous les statuts natifs mappés
- [ ] Tester statut inconnu (log warning attendu)
- [ ] Vérifier raw_response sauvegardé JSONB

## Phase 6 : Idempotence
- [ ] Envoyer 2x même client_order_id
- [ ] Vérifier rejet duplicate (ou même ordre)

## Phase 7 : Edge Cases
- [ ] Symbole invalide (erreur attendue)
- [ ] Quantité trop faible (erreur min_amount)
- [ ] Balance insuffisant (erreur attendue)
- [ ] Network timeout (retry ou erreur)

✅ **Validation terminée** : [DATE]
```

#### Unit Tests Sur Mocks (Pas d'API Réels)
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_bitget_client():
    """Mock BitgetNativeClient"""
    client = Mock()
    client.place_order.return_value = {
        'orderId': '1234567890',
        'clientOid': 'ARISTO_1_1706000000_abc',
        'status': 'new',
        # ... autres champs
    }
    return client

def test_place_order_format_conversion(mock_bitget_client):
    """Test conversion format unifié → Bitget natif"""
    unified_request = {
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'type': 'limit',
        'quantity': 0.1,
        'price': 43000,
        'client_order_id': 'ARISTO_TEST_123',
    }

    # Appel Terminal 5
    result = terminal5.execute_order(unified_request, mock_bitget_client)

    # Vérifications
    assert result['client_order_id'] == 'ARISTO_TEST_123'
    assert result['symbol'] == 'BTC/USDT'
    assert result['status'] == 'open'  # Normalisé depuis 'new'

def test_status_normalization():
    """Test mapping statuts natifs → Aristobot"""
    assert normalize_status('bitget', 'new') == 'open'
    assert normalize_status('binance', 'FILLED') == 'closed'
    assert normalize_status('kraken', 'canceled') == 'cancelled'
    assert normalize_status('bitget', 'unknown_status') == 'UNKNOWN'

def test_kraken_userref_generation():
    """Test génération userref Kraken"""
    client_order_id = 'ARISTO_1_1706000000_abc'
    userref = generate_kraken_userref(client_order_id)

    assert isinstance(userref, int)
    assert 0 <= userref < KRAKEN_USERREF_MAX

    # Vérifier cache Redis
    cached = reverse_kraken_userref(userref)
    assert cached == client_order_id
```

#### Extension Monitoring Terminal 7
Terminal 7 (Order Monitor) peut valider format en continu :

```python
class Terminal7FormatValidator:
    """Validation format en temps réel"""

    REQUIRED_FIELDS = [
        'user_id', 'broker_id', 'source',
        'symbol', 'side', 'type', 'status',
        'client_order_id',
    ]

    async def validate_trade_format(self, trade):
        """Valide qu'un trade respecte format unifié"""
        errors = []

        # Vérifier champs requis
        for field in self.REQUIRED_FIELDS:
            if not hasattr(trade, field) or getattr(trade, field) is None:
                errors.append(f"Champ manquant: {field}")

        # Vérifier statut normalisé
        if trade.status not in ARISTOBOT_STATUSES:
            errors.append(f"Statut invalide: {trade.status}")

        # Vérifier raw_response présent
        if not trade.raw_response:
            errors.append("raw_response JSONB manquant")

        # Log erreurs
        if errors:
            logger.error(
                f"❌ FORMAT INVALIDE trade {trade.id}: {errors}"
            )
            send_discord_alert(
                f"🚨 **Format invalide** trade {trade.id}:\n"
                f"```\n{chr(10).join(errors)}\n```"
            )

        return len(errors) == 0
```

---

## Extensibilité

### Ajout d'un Nouvel Exchange

#### Processus 5 Étapes

**1. Créer Client Natif**
```python
# backend/apps/core/services/exchanges/my_exchange_client.py
from .base_exchange_client import BaseExchangeClient

class MyExchangeNativeClient(BaseExchangeClient):
    """Client natif pour My Exchange"""

    def __init__(self):
        super().__init__()
        self.name = 'myexchange'
        self.base_url = 'https://api.myexchange.com'

    def set_credentials(self, api_key, api_secret, api_password=None):
        """Injection credentials"""
        self.api_key = api_key
        self.api_secret = api_secret

    async def place_order(self, request):
        """Implémentation ordre natif"""
        # Conversion format unifié → natif
        native_request = {
            'symbol': self._convert_symbol(request['symbol']),
            'side': request['side'].upper(),
            'type': request['type'],
            'quantity': request['quantity'],
            'price': request.get('price'),
            'clientOrderId': request['client_order_id'],
        }

        # Appel API
        response = await self._post('/v1/order', native_request)

        # Conversion réponse native → format unifié
        return self._normalize_order_response(response)

    def _convert_symbol(self, symbol: str) -> str:
        """BTCUSDT ou BTC/USDT selon exchange"""
        return symbol.replace('/', '')

    def _normalize_order_response(self, native_response):
        """Conversion réponse → format unifié"""
        return {
            'id': native_response['orderId'],
            'client_order_id': native_response['clientOrderId'],
            'symbol': native_response['symbol'],
            'status': self._normalize_status(native_response['status']),
            'native_status': native_response['status'],
            # ... autres champs
        }

    def _normalize_status(self, native_status):
        """Mapping statuts"""
        mapping = {
            'NEW': 'open',
            'FILLED': 'closed',
            'CANCELLED': 'cancelled',
        }
        return mapping.get(native_status, 'UNKNOWN')
```

**2. Enregistrer Factory**
```python
# backend/apps/core/services/base_exchange_client.py
class ExchangeClientFactory:
    CLIENTS = {
        'bitget': BitgetNativeClient,
        'binance': BinanceNativeClient,
        'kraken': KrakenNativeClient,
        'myexchange': MyExchangeNativeClient,  # NOUVEAU
    }

    @classmethod
    def create(cls, exchange_name: str):
        client_class = cls.CLIENTS.get(exchange_name)
        if not client_class:
            raise ValueError(f"Exchange non supporté: {exchange_name}")
        return client_class()
```

**3. Ajouter Mapping Statuts**
```python
# backend/apps/core/services/native_exchange_manager.py
STATUS_MAPPING = {
    'bitget': {...},
    'binance': {...},
    'kraken': {...},
    'myexchange': {  # NOUVEAU
        'NEW': 'open',
        'PARTIAL': 'open',
        'FILLED': 'closed',
        'CANCELLED': 'cancelled',
        'REJECTED': 'cancelled',
    },
}
```

**4. Valider Checklist**
Exécuter checklist validation manuelle (voir section Tests & Validation)

**5. Mettre à Jour Documentation**
```markdown
### Exchanges Supportés
- **Bitget** (45%) - Client natif principal
- **Binance** (35%) - Client natif
- **Kraken** (20%) - Client natif avec gestion spéciale `userref`
- **MyExchange** (NEW) - Client natif ajouté [DATE]
```

#### Considérations Spéciales

**Gestion ID Format Spécial** (comme Kraken userref) :
```python
# Si nouvel exchange a contrainte similaire
if exchange_name == 'myexchange' and requires_int_id:
    client_order_id = generate_exchange_specific_id(
        request['client_order_id']
    )
```

**Paramètres Exotiques** :
```python
# Ajouter dans extra_params si besoin
if exchange_name == 'myexchange':
    native_request.update(request.get('extra_params', {}))
```

---

## Exemples de Code

### Exemple Complet : Place Order

#### Terminal 5 Handler
```python
async def handle_place_order(request):
    """
    Handler complet place_order avec toute la logique
    """
    request_id = request['request_id']
    user_id = request['user_id']
    broker_id = request['params']['broker_id']

    try:
        # 1. Récupérer broker avec décryptage
        broker = await get_broker(broker_id, user_id)

        # 2. Obtenir client exchange avec injection credentials
        client = await exchange_manager.get_client(broker_id)

        # 3. Préparer requête unifiée
        unified_request = {
            'user_id': user_id,
            'broker_id': broker_id,
            'source': request['params'].get('source', 'manual'),
            'symbol': request['params']['symbol'],
            'side': request['params']['side'],
            'type': request['params']['type'],
            'quantity': request['params']['amount'],
            'price': request['params'].get('price'),
            'client_order_id': request['params'].get('client_order_id',
                generate_client_order_id(user_id)),
            'time_in_force': request['params'].get('time_in_force', 'GTC'),
            'extra_params': request['params'].get('extra_params', {}),
        }

        # 4. Exécuter ordre via client natif
        native_response = await client.place_order(unified_request)

        # 5. Normaliser réponse
        unified_response = {
            **unified_request,
            'id': native_response['orderId'],
            'status': normalize_status(broker.exchange, native_response['status']),
            'native_status': native_response['status'],
            'filled': native_response.get('filledQty', 0),
            'remaining': unified_request['quantity'] - native_response.get('filledQty', 0),
            'created_at': native_response['createdAt'],
        }

        # 6. Sauvegarder en DB (dual storage)
        await save_trade_response(unified_response, native_response)

        # 7. Retourner succès
        return {
            'success': True,
            'data': unified_response
        }

    except Exception as e:
        logger.error(
            f"❌ Erreur place_order {request_id}: {e}",
            extra={'request_id': request_id}
        )

        return {
            'success': False,
            'error': str(e)
        }
```

### Exemple : Réconciliation Terminal 7

#### Détection Ordres Manquants
```python
async def reconcile_orders(broker_id: int):
    """
    Réconciliation ordres : DB vs Exchange
    Détecte ordres créés directement sur exchange
    """
    # 1. Charger ordres ouverts depuis exchange
    exchange_orders = await exchange_client.fetch_open_orders(broker_id)

    # 2. Charger ordres ouverts depuis DB
    db_orders = await Trade.objects.filter(
        broker_id=broker_id,
        status='open'
    ).values_list('exchange_order_id', flat=True)

    db_order_ids = set(db_orders)

    # 3. Identifier ordres manquants en DB
    missing_orders = []
    for order in exchange_orders:
        if order['id'] not in db_order_ids:
            missing_orders.append(order)

    # 4. Ajouter ordres manquants avec flag spécial
    for order in missing_orders:
        await Trade.objects.create(
            broker_id=broker_id,
            user_id=get_broker_user(broker_id),
            source='external',  # Flag spécial
            symbol=order['symbol'],
            side=order['side'],
            type=order['type'],
            quantity=order['quantity'],
            price=order.get('price'),
            status=normalize_status(broker.exchange, order['status']),
            exchange_order_id=order['id'],
            client_order_id=order.get('clientOrderId', f"EXT_{order['id']}"),
            raw_response=order,
            note="Ordre ajouté par Terminal 7 (créé directement sur exchange)"
        )

        logger.info(
            f"📌 Ordre externe ajouté: {order['id']} - {order['symbol']}"
        )

    return len(missing_orders)
```

---

## Résumé Décisions Architecturales

### ✅ Validations Finales

| Aspect | Décision | Validé Par |
|--------|----------|------------|
| **Format** | CCXT-inspiré + extensions Aristobot | Winston, Dr. Quinn |
| **Architecture** | Option B : 1 instance/exchange type | Winston, Barry |
| **Stockage** | Dual : Unifié + raw_response JSONB | Winston |
| **Paramètres** | 3 niveaux (Critical/Important/Exotic) | Dr. Quinn |
| **Kraken userref** | Hash SHA256 + cache Redis 30j | Dr. Quinn |
| **Statuts** | Mapping + "UNKNOWN" fallback | Winston |
| **Logs** | RotatingFileHandler 10MB x5 | Barry |
| **Monitoring** | Redis heartbeat + watchdog hybride | Barry, Winston |
| **Tests** | Validation manuelle + monitoring continu | Murat |
| **Extensibilité** | Hard-coding routing (pas plugin) | Winston |

### 🎯 Bénéfices Architecture

1. **Performance** : ~3x plus rapide que CCXT
2. **Cohérence** : Format unifié tous exchanges
3. **Auditabilité** : Stockage dual (unifié + brut)
4. **Résilience** : Monitoring hybride + auto-défense
5. **Maintenabilité** : Hard-coding routing pour 4-5 exchanges
6. **Extensibilité** : Processus clair ajout nouveaux exchanges
7. **Observabilité** : Logs rotatifs + Redis heartbeat + Discord alerts

---

**FIN DOCUMENTATION TERMINAL 5**

---

**Prochaines étapes** :
1. ✅ Mettre à jour `Aristobot3_1.md` section 3.3
2. ✅ Mettre à jour `IMPLEMENTATION_PLAN.md` MODULE 2
3. ✅ Ajouter import dans `CLAUDE.md`
4. 🔄 Retourner au workflow PRD Step 3 → [C] continuer Step 4
