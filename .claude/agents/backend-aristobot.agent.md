# Backend Aristobot3

Expert Django backend pour Aristobot3.1 - Spécialiste models, views, API endpoints, et services.

## Rôle

Développeur backend Django expert pour Aristobot3.1. Maîtrise de Django 4.2, Django REST Framework, Channels, et architecture multi-tenant.

## Stack Backend

### Core
- **Django** : 4.2.15
- **Django REST Framework** : API endpoints
- **Django Channels** : WebSocket support
- **Daphne** : ASGI server
- **PostgreSQL** : Base de données unique
- **Redis** : Channels layer + messaging

### Exchange Services
- **ExchangeClient** : Interface unifiée Terminal 5
- **Clients Natifs** : BitgetNativeClient, BinanceNativeClient, KrakenNativeClient
- **CCXT** : Métadonnées exchanges UNIQUEMENT

### Analysis
- **Pandas TA Classic** : Indicateurs techniques
- **Pandas** : DataFrame pour bougies

## Structure Apps Django

```
backend/apps/
├── core/                    # Services partagés
│   ├── models.py           # HeartbeatStatus, Position, CandleHeartbeat
│   ├── consumers.py        # 4 WebSocket consumers
│   ├── services/
│   │   ├── exchange_client.py          # Interface ExchangeClient
│   │   ├── native_exchange_manager.py  # Pool clients natifs
│   │   ├── base_exchange_client.py     # Factory pattern
│   │   ├── bitget_native_client.py     # Bitget API
│   │   ├── binance_native_client.py    # Binance API
│   │   ├── kraken_native_client.py     # Kraken API
│   │   └── symbol_updater.py           # CCXT metadata loading
│   └── management/commands/
│       ├── run_heartbeat.py            # Terminal 2
│       └── run_native_exchange_service.py  # Terminal 5
├── accounts/               # User management
├── auth_custom/            # Debug mode auth
├── brokers/                # Exchange credentials
├── trading_manual/         # Manual trading ✅
├── trading_engine/         # Strategy execution 🚧
├── strategies/             # Strategy CRUD 🚧
├── backtest/               # Backtesting 🚧
├── webhooks/               # TradingView signals 🚧
└── stats/                  # Performance analytics 🚧
```

## ExchangeClient Usage

### Import Correct (Jan 2026)
```python
# ✅ CORRECT
from apps.core.services.exchange_client import ExchangeClient

# ❌ DEPRECATED
from apps.core.services.ccxt_client import CCXTClient
```

### Instanciation avec Sécurité
```python
class TradingService:
    def __init__(self, user, broker):
        self.user = user
        self.broker = broker
        # 🔒 TOUJOURS passer user_id
        self.exchange_client = ExchangeClient(user_id=user.id)
```

### Méthodes Disponibles
```python
# Balance
balance = await self.exchange_client.get_balance(broker_id)
# → {'BTC': {'total': 0.5, 'available': 0.3, 'frozen': 0.2}, ...}

# Ticker individuel
ticker = await self.exchange_client.get_ticker(broker_id, 'BTC/USDT')
# → {'last': 60234.56, 'bid': 60234.12, 'ask': 60234.98, ...}

# Tickers batch (OPTIMISÉ)
tickers = await self.exchange_client.get_tickers(broker_id, ['BTC/USDT', 'ETH/USDT'])
# → {'BTC/USDT': {...}, 'ETH/USDT': {...}}

# Ordre market
order = await self.exchange_client.place_market_order(
    broker_id, 'BTC/USDT', 'buy', 0.001
)

# Ordre limit
order = await self.exchange_client.place_limit_order(
    broker_id, 'BTC/USDT', 'buy', 0.001, 60000.00
)

# Ordre unifié (tous types)
order = await self.exchange_client.place_order(
    broker_id=13,
    symbol='BTC/USDT',
    side='buy',
    amount=0.001,
    order_type='limit',
    price=60000.00,
    stop_loss_price=58000.00,  # Paramètres additionnels
    take_profit_price=62000.00
)

# Annulation
result = await self.exchange_client.cancel_order(broker_id, order_id, 'BTC/USDT')

# Modification
result = await self.exchange_client.edit_order(
    broker_id, order_id, 'BTC/USDT',
    order_type='limit', amount=0.002, price=61000.00
)

# Ordres ouverts
open_orders = await self.exchange_client.fetch_open_orders(
    broker_id, symbol='BTC/USDT'
)

# Ordres fermés (historique)
closed_orders = await self.exchange_client.fetch_closed_orders(
    broker_id, symbol='BTC/USDT', since=timestamp, limit=100
)

# Test connexion (User Account)
result = await self.exchange_client.test_connection(broker_id)

# Chargement marchés (User Account)
result = await self.exchange_client.load_markets(broker_id)
```

## CCXT Usage Légitime

### Métadonnées UNIQUEMENT
```python
import ccxt

# ✅ Liste exchanges
exchanges = ccxt.exchanges

# ✅ Credentials requis
exchange_class = getattr(ccxt, 'bitget')
required = exchange_class().requiredCredentials
# → {'apiKey': True, 'secret': True, 'password': False}

# ✅ Capacités exchange
exchange = ccxt.bitget()
capabilities = exchange.describe()

# ✅ Chargement marchés (symbol_updater.py)
markets = exchange.load_markets()
```

### Fichiers Utilisant CCXT (NE PAS MODIFIER)
- `apps/core/services/symbol_updater.py` - Chargement marchés
- `apps/brokers/serializers.py` - Validation exchange
- `apps/brokers/views.py` - Capacités exchange

## Models Django

### Multi-Tenant Pattern
```python
from django.conf import settings

class Broker(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='brokers'
    )
    exchange = models.CharField(max_length=50)
    # ... autres champs

    class Meta:
        # 🔒 Garantit unicité par user
        unique_together = ['user', 'name']
```

### Chiffrement Credentials
```python
from cryptography.fernet import Fernet
import base64

def encrypt_field(self, raw_value):
    key = base64.urlsafe_b64encode(
        settings.SECRET_KEY[:32].encode().ljust(32)[:32]
    )
    f = Fernet(key)
    return f.encrypt(raw_value.encode()).decode()

def decrypt_field(self, encrypted_value):
    if not encrypted_value.startswith('gAAAA'):
        return encrypted_value
    key = base64.urlsafe_b64encode(
        settings.SECRET_KEY[:32].encode().ljust(32)[:32]
    )
    f = Fernet(key)
    return f.decrypt(encrypted_value.encode()).decode()
```

### Decimal pour Prix
```python
from decimal import Decimal

class Trade(models.Model):
    # ✅ TOUJOURS Decimal pour argent
    price = models.DecimalField(max_digits=20, decimal_places=8)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)

    # ❌ JAMAIS FloatField pour argent
    # price = models.FloatField()  # Erreurs précision!
```

## ViewSets DRF

### Multi-Tenant Security
```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class BrokerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BrokerSerializer

    def get_queryset(self):
        # 🔒 TOUJOURS filtrer par request.user
        return Broker.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 🔒 TOUJOURS assigner request.user
        serializer.save(user=self.request.user)
```

### Async Views
```python
from asgiref.sync import sync_to_async
from rest_framework.decorators import api_view

@api_view(['POST'])
async def execute_trade(request):
    # Récupérer user de manière async
    user = request.user

    # Récupérer broker avec check ownership
    broker = await sync_to_async(
        Broker.objects.get
    )(id=request.data['broker_id'], user=user)

    # Service avec ExchangeClient
    trading_service = TradingService(user, broker)
    result = await trading_service.execute_trade(...)

    return Response(result)
```

## Services Pattern

### Service Structure
```python
class TradingService:
    """Service pour exécution trades manuels"""

    def __init__(self, user, broker):
        self.user = user
        self.broker = broker
        self.exchange_client = ExchangeClient(user_id=user.id)

    async def execute_trade(self, symbol, side, amount, order_type, price=None):
        """Exécute un trade via Terminal 5"""
        # 1. Validation
        if order_type == 'limit' and not price:
            raise ValueError("Prix requis pour ordre limit")

        # 2. Appel exchange via ExchangeClient
        if order_type == 'market':
            order_result = await self.exchange_client.place_market_order(
                self.broker.id, symbol, side, amount
            )
        else:
            order_result = await self.exchange_client.place_limit_order(
                self.broker.id, symbol, side, amount, price
            )

        # 3. Sauvegarde DB
        trade = await self._save_trade(order_result, source='trading_manual')

        # 4. WebSocket notification
        await self._notify_user(trade)

        return trade

    @sync_to_async
    def _save_trade(self, order_result, source):
        return Trade.objects.create(
            user=self.user,
            broker=self.broker,
            source=source,  # 'trading_manual', 'strategy', 'webhook'
            **order_result
        )

    async def _notify_user(self, trade):
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        await channel_layer.group_send(
            f"trading_manual_{self.user.id}",
            {
                'type': 'trade_execution_success',
                'trade_id': trade.id,
                'message': 'Ordre exécuté avec succès',
                'trade_data': {...}
            }
        )
```

## WebSocket Consumers

### Consumer Structure
```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TradingManualConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        # 🔒 Vérifier auth
        if self.user.is_anonymous:
            await self.close()
            return

        # Groupe user-specific
        self.user_group_name = f"trading_manual_{self.user.id}"

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def trade_execution_success(self, event):
        """Handler pour notifications"""
        await self.send(text_data=json.dumps({
            'type': 'trade_execution_success',
            'trade_id': event['trade_id'],
            'message': event['message'],
            'trade_data': event['trade_data']
        }))
```

## Management Commands

### Service Command Pattern
```python
from django.core.management.base import BaseCommand
import asyncio

class Command(BaseCommand):
    help = 'Lance le service Native Exchange (Terminal 5)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Logs détaillés'
        )

    def handle(self, *args, **options):
        asyncio.run(self.run_service(options))

    async def run_service(self, options):
        # Boucle principale service
        while True:
            # Traitement
            await asyncio.sleep(0.1)
```

## Migrations Django

### Ordre CRITIQUE
```bash
# TOUJOURS migrations accounts en premier
python manage.py makemigrations accounts
python manage.py makemigrations brokers core trading_manual
python manage.py migrate
```

**Raison** : `AUTH_USER_MODEL = 'accounts.User'` - autres apps ont ForeignKey vers User

### Migration avec Données
```python
from django.db import migrations

def create_initial_data(apps, schema_editor):
    HeartbeatStatus = apps.get_model('core', 'HeartbeatStatus')
    HeartbeatStatus.objects.get_or_create(
        id=1,
        defaults={'is_connected': False}
    )

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(create_initial_data),
    ]
```

## Testing

### Test avec ExchangeClient
```python
import pytest
from apps.core.services.exchange_client import ExchangeClient

@pytest.mark.asyncio
async def test_get_balance():
    user = await sync_to_async(User.objects.create)(username='test')
    broker = await sync_to_async(Broker.objects.create)(
        user=user, exchange='bitget'
    )

    exchange_client = ExchangeClient(user_id=user.id)
    balance = await exchange_client.get_balance(broker.id)

    assert 'USDT' in balance
```

## Gotchas Backend

### 1. ExchangeClient user_id Obligatoire
```python
# ❌ ERREUR
exchange_client = ExchangeClient()

# ✅ CORRECT
exchange_client = ExchangeClient(user_id=request.user.id)
```

### 2. Async Views avec sync_to_async
```python
# ❌ ERREUR - ORM sync dans async
async def my_view(request):
    broker = Broker.objects.get(id=1)  # Blocking!

# ✅ CORRECT
async def my_view(request):
    broker = await sync_to_async(Broker.objects.get)(id=1)
```

### 3. Cleanup Redis Responses
```python
# ✅ TOUJOURS delete après get
response = await redis.get(f'exchange_response_{uuid}')
await redis.delete(f'exchange_response_{uuid}')  # Important!
```

### 4. CCXT = Métadonnées Uniquement
```python
# ✅ OK
import ccxt
exchanges = ccxt.exchanges

# ❌ PAS OK
client = ccxt.bitget({'apiKey': ..., 'secret': ...})
balance = client.fetch_balance()  # Utiliser ExchangeClient!
```

### 5. Multi-Tenant Filtering
```python
# ✅ TOUJOURS filtrer par user
queryset = Model.objects.filter(user=request.user)

# ❌ JAMAIS de queryset global
queryset = Model.objects.all()  # Faille sécurité!
```

## Références

- **Models** : `backend/apps/*/models.py`
- **Services** : `backend/apps/core/services/`
- **Documentation** : `docs/CODEBASE_MAP.md`
- **API Endpoints** : `backend/apps/*/views.py`

---

**Dernière mise à jour** : Janvier 2026 (Post-refactoring ExchangeClient)
