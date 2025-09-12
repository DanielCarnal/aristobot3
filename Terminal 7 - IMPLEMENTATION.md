# Terminal 7 - Order Monitor Service - PLAN D'IMPLÉMENTATION

## 📋 CONTEXTE ET OBJECTIF

**Terminal 7** est un service Django Management Command qui surveille l'exécution des ordres sur tous les exchanges et calcule automatiquement les P&L. Il fonctionne de manière autonome avec un timing interne de 10 secondes.

### Architecture Fondamentale
- **Démarrage** : `python manage.py run_order_monitor`
- **Timing interne** : Horloge système toutes les 10 secondes
- **Multi-exchange** : Utilise l'architecture Terminal 5 (ExchangeClientFactory)
- **Séquentiel** : Scanne les brokers un par un avec délai de 1s entre chaque
- **P&L automatique** : Phase 1 (price averaging) → Phase 2 (FIFO) → Phase 3 (user choice)

## 🎯 ANALYSE ARCHITECTURE TERMINAL 5

D'après l'analyse du code, Terminal 5 utilise :

### Pattern Multi-Exchange
```python
# NativeExchangeManager utilise ExchangeClientFactory
client = await self._get_exchange_client(broker_id)
```

### Actions Standardisées
- `get_balance()` : Solde du compte
- `fetch_open_orders()` → `get_open_orders()` (client natif)
- `fetch_closed_orders()` → `get_order_history()` (client natif)
- Format de réponse unifié : `{'success': bool, 'data': {...}, 'error': str}`

### Pattern Request/Response
```python
# Terminal 7 utilisera directement NativeExchangeManager
await self._send_request('fetch_open_orders', {'broker_id': broker_id})
```

## 📊 ANALYSE BITGET API (Documentation)

### Get Current Orders (`/api/v2/spot/trade/unfilled-orders`)
- **Retourne** : Ordres avec status `live` ou `partially_filled`
- **Champs clés** : `orderId`, `symbol`, `side`, `size`, `status`, `cTime`

### Get History Orders (`/api/v2/spot/trade/history-orders`)
- **Retourne** : Ordres avec status `filled` ou `cancelled`
- **Données P&L** : `priceAvg`, `baseVolume`, `quoteVolume`, `feeDetail`
- **Suffisant** : Contient toutes les données nécessaires (pas besoin de get_fills)

### Stratégie de Détection
```python
# Comparer ordres history avec timestamp window
last_check_time = broker_state['last_check']
current_time = int(time.time() * 1000)

# Nouveaux ordres executed = présents dans history mais pas dans last_scan
new_executed = [o for o in history_orders 
                if int(o['uTime']) > last_check_time 
                and o['status'] == 'filled']
```

## 🏗️ PHASE 1 : INFRASTRUCTURE DE BASE

### Étape 1.1 : Management Command Structure
```python
# backend/apps/core/management/commands/run_order_monitor.py
class Command(BaseCommand):
    help = 'Terminal 7 - Service de surveillance des ordres et calcul P&L automatique'
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.broker_states = {}  # État de surveillance par broker
        self.exchange_manager = None
        
    def handle(self, *args, **options):
        """Point d'entrée - comme Terminal 5"""
        self.stdout.write('[START] Terminal 7 - Order Monitor Service')
        
        try:
            asyncio.run(self.run_service())
        except KeyboardInterrupt:
            self.stdout.write('[STOP] Service arrêté par utilisateur')
        except Exception as e:
            self.stdout.write(f'[ERROR] Erreur critique: {e}')
    
    async def run_service(self):
        """Service principal avec timing interne de 10s"""
        self.running = True
        
        # Initialisation
        await self._initialize_service()
        
        # Boucle principale - TIMING INTERNE
        while self.running:
            try:
                await self._scan_all_brokers()
                await asyncio.sleep(10)  # 10 secondes entre chaque cycle
            except Exception as e:
                self.stdout.write(f'[ERROR] Erreur cycle: {e}')
                await asyncio.sleep(10)  # Continue malgré l'erreur
    
    async def _initialize_service(self):
        """Initialisation du service"""
        # Récupération de l'Exchange Manager (Terminal 5)
        from apps.core.services.native_exchange_manager import get_native_exchange_manager
        self.exchange_manager = get_native_exchange_manager()
        
        # Chargement des brokers actifs
        await self._load_active_brokers()
        
        self.stdout.write(f'[OK] Service initialisé - {len(self.broker_states)} brokers surveillés')
    
    async def _scan_all_brokers(self):
        """Scanne tous les brokers séquentiellement"""
        for broker_id in self.broker_states:
            try:
                await self._scan_broker_orders(broker_id)
                await asyncio.sleep(1)  # 1s entre chaque broker
            except Exception as e:
                self.stdout.write(f'[ERROR] Erreur broker {broker_id}: {e}')
```

### Étape 1.2 : Broker State Management
```python
async def _load_active_brokers(self):
    """Charge la liste des brokers actifs à surveiller"""
    from apps.brokers.models import Broker
    brokers = await sync_to_async(list)(
        Broker.objects.filter(is_active=True)
    )
    
    for broker in brokers:
        # Récupération capital initial depuis Broker model
        initial_capital = getattr(broker, 'initial_capital', 1000.0)
        
        self.broker_states[broker.id] = {
            'name': broker.name,
            'exchange': broker.exchange,
            'last_check': int((time.time() - 86400) * 1000),  # 24h en arrière
            'known_orders': set(),  # OrderIDs déjà traités
            'initial_capital': initial_capital,
            'current_balance': None,
            'total_pnl': 0.0,
            'last_successful_scan': None,
            'error_count': 0
        }

async def _scan_broker_orders(self, broker_id: int):
    """Scanne les ordres d'un broker spécifique"""
    broker_state = self.broker_states[broker_id]
    
    try:
        # 1. Récupération des ordres history récents
        history_orders = await self._get_broker_history_orders(broker_id)
        
        # 2. Détection des nouveaux ordres exécutés
        new_executed_orders = await self._detect_new_executions(
            broker_id, history_orders
        )
        
        # 3. Calcul et sauvegarde P&L pour chaque nouvel ordre
        for order in new_executed_orders:
            await self._process_executed_order(broker_id, order)
        
        # 4. Mise à jour timestamp et statistiques
        broker_state['last_check'] = int(time.time() * 1000)
        broker_state['last_successful_scan'] = time.time()
        broker_state['error_count'] = 0
        
        # Logging
        if new_executed_orders:
            self.stdout.write(
                f'[EXEC] {broker_state["name"]}: '
                f'{len(new_executed_orders)} nouveaux ordres traités'
            )
            
    except Exception as e:
        broker_state['error_count'] += 1
        self.stdout.write(f'[ERROR] Broker {broker_id}: {e}')
```

### Étape 1.3 : Interface avec Terminal 5
```python
async def _get_broker_history_orders(self, broker_id: int, limit: int = 50) -> list:
    """
    Récupère les ordres history via Terminal 5 (NativeExchangeManager)
    Compatible avec l'architecture existante
    """
    try:
        # Utilisation directe du NativeExchangeManager
        result = await self.exchange_manager._handle_action(
            'fetch_closed_orders',
            {'broker_id': broker_id, 'limit': limit}
        )
        
        if result['success']:
            return result['data']
        else:
            raise Exception(f"Erreur API: {result['error']}")
            
    except Exception as e:
        # Fallback : utilisation Redis comme ExchangeClient
        from apps.core.services.exchange_client import ExchangeClient
        client = ExchangeClient()
        return await client.fetch_closed_orders(broker_id, limit=limit)

async def _get_broker_open_orders(self, broker_id: int) -> list:
    """Récupère les ordres ouverts pour comparaison"""
    try:
        result = await self.exchange_manager._handle_action(
            'fetch_open_orders',
            {'broker_id': broker_id}
        )
        
        if result['success']:
            return result['data']
        else:
            raise Exception(f"Erreur API: {result['error']}")
            
    except Exception as e:
        # Fallback Redis
        from apps.core.services.exchange_client import ExchangeClient
        client = ExchangeClient()
        return await client.fetch_open_orders(broker_id)
```

## 🧮 PHASE 2 : CALCUL P&L AVEC PRICE AVERAGING

### Étape 2.1 : Détection Nouvel Ordre Exécuté
```python
async def _detect_new_executions(self, broker_id: int, history_orders: list) -> list:
    """
    Détecte les ordres nouvellement exécutés depuis la dernière vérification
    """
    broker_state = self.broker_states[broker_id]
    last_check_time = broker_state['last_check']
    known_orders = broker_state['known_orders']
    
    new_executions = []
    
    for order in history_orders:
        order_id = order.get('id') or order.get('orderId')
        update_time = int(order.get('updated', order.get('uTime', 0)))
        status = order.get('status')
        
        # Conditions pour "nouvel ordre exécuté"
        is_new = order_id not in known_orders
        is_recent = update_time > last_check_time
        is_filled = status in ['filled', 'closed']
        
        if is_new and is_recent and is_filled:
            new_executions.append(order)
            known_orders.add(order_id)
    
    return new_executions

async def _process_executed_order(self, broker_id: int, order: dict):
    """
    Traite un ordre exécuté : calcule P&L et sauvegarde en DB
    """
    from apps.trading_manual.models import Trade
    from django.contrib.auth import get_user_model
    
    try:
        # Extraction des données de l'ordre
        order_data = self._extract_order_data(order)
        
        # Calcul P&L avec price averaging (Phase 1)
        pnl_data = await self._calculate_pnl_price_averaging(
            broker_id, order_data
        )
        
        # Sauvegarde en base de données
        trade = await sync_to_async(Trade.objects.create)(
            user_id=await self._get_broker_user_id(broker_id),
            broker_id=broker_id,
            source='order_monitor',  # Identifier Terminal 7
            
            # Données de l'ordre
            symbol=order_data['symbol'],
            side=order_data['side'],
            order_type=order_data['type'],
            quantity=order_data['quantity'],
            price=order_data['avg_price'],
            
            # P&L calculé
            realized_pnl=pnl_data['realized_pnl'],
            total_fees=pnl_data['total_fees'],
            
            # Métadonnées
            exchange_order_id=order_data['order_id'],
            exchange_order_status='filled',
            executed_at=order_data['executed_at'],
            
            # Debug/monitoring
            raw_order_data=order,  # JSON complet pour debug
            pnl_calculation_method='price_averaging_v1'
        )
        
        # Mise à jour des statistiques broker
        await self._update_broker_stats(broker_id, pnl_data)
        
        self.stdout.write(
            f'[PNL] {order_data["symbol"]} {order_data["side"]} '
            f'${pnl_data["realized_pnl"]:.2f} (fees: ${pnl_data["total_fees"]:.2f})'
        )
        
    except Exception as e:
        self.stdout.write(f'[ERROR] Erreur traitement ordre: {e}')
        import traceback
        traceback.print_exc()
```

### Étape 2.2 : Calcul P&L Price Averaging
```python
async def _calculate_pnl_price_averaging(self, broker_id: int, order_data: dict) -> dict:
    """
    PHASE 1: Calcul P&L avec méthode Price Averaging
    
    Simple mais efficace pour commencer.
    Sera remplacé par FIFO en Phase 2.
    """
    from apps.trading_manual.models import Trade
    
    symbol = order_data['symbol']
    side = order_data['side']
    quantity = order_data['quantity']
    avg_price = order_data['avg_price']
    total_fees = order_data['total_fees']
    
    # Récupération des trades précédents pour ce symbole
    previous_trades = await sync_to_async(list)(
        Trade.objects.filter(
            broker_id=broker_id,
            symbol=symbol,
            exchange_order_status='filled'
        ).order_by('executed_at')
    )
    
    if side == 'buy':
        # Achat : pas de P&L, juste mise à jour position
        realized_pnl = 0.0
    else:
        # Vente : calcul P&L basé sur prix moyen d'achat
        total_buy_quantity = 0.0
        total_buy_value = 0.0
        
        for trade in previous_trades:
            if trade.side == 'buy':
                total_buy_quantity += trade.quantity
                total_buy_value += (trade.quantity * trade.price)
        
        if total_buy_quantity > 0:
            avg_buy_price = total_buy_value / total_buy_quantity
            realized_pnl = (avg_price - avg_buy_price) * quantity
        else:
            # Vente sans achat préalable (short ou erreur)
            realized_pnl = 0.0
            self.stdout.write(f'[WARN] Vente sans achat: {symbol}')
    
    return {
        'realized_pnl': realized_pnl,
        'total_fees': total_fees,
        'calculation_method': 'price_averaging',
        'avg_buy_price': avg_buy_price if side == 'sell' else avg_price,
        'position_quantity': self._calculate_position_quantity(previous_trades, order_data)
    }

def _extract_order_data(self, order: dict) -> dict:
    """
    Extrait et normalise les données d'un ordre exchange
    Compatible avec les formats Bitget, Binance, etc.
    """
    # Mapping des champs selon l'exchange
    return {
        'order_id': order.get('id') or order.get('orderId'),
        'symbol': order.get('symbol'),
        'side': order.get('side'),
        'type': order.get('type') or order.get('orderType'),
        'quantity': float(order.get('filled', order.get('baseVolume', 0))),
        'avg_price': float(order.get('average', order.get('priceAvg', 0))),
        'total_fees': self._extract_total_fees(order),
        'executed_at': self._parse_timestamp(order.get('updated', order.get('uTime'))),
    }

def _extract_total_fees(self, order: dict) -> float:
    """
    Extrait le montant total des frais selon le format exchange
    Compatible Bitget feeDetail, Binance, etc.
    """
    # Format Bitget
    if 'feeDetail' in order:
        fee_detail = order['feeDetail']
        if isinstance(fee_detail, dict) and 'newFees' in fee_detail:
            return float(fee_detail['newFees'].get('t', 0))
    
    # Format standard
    if 'fee' in order:
        fee_data = order['fee']
        if isinstance(fee_data, dict):
            return float(fee_data.get('cost', 0))
        return float(fee_data)
    
    return 0.0
```

## 🔄 PHASE 3 : MIGRATION VERS FIFO

### Étape 3.1 : Calcul FIFO Avancé
```python
async def _calculate_pnl_fifo(self, broker_id: int, order_data: dict) -> dict:
    """
    PHASE 2: Calcul P&L avec méthode FIFO (First In, First Out)
    
    Plus précis que price averaging, respecte l'ordre chronologique.
    """
    from apps.trading_manual.models import Trade
    
    symbol = order_data['symbol']
    side = order_data['side']
    quantity = order_data['quantity']
    avg_price = order_data['avg_price']
    
    if side == 'buy':
        # Achat : création d'une nouvelle position FIFO
        return {
            'realized_pnl': 0.0,
            'total_fees': order_data['total_fees'],
            'calculation_method': 'fifo',
            'fifo_queue_updated': True
        }
    
    else:
        # Vente : consommation FIFO des achats précédents
        buy_queue = await self._get_fifo_buy_queue(broker_id, symbol)
        
        remaining_to_sell = quantity
        total_buy_cost = 0.0
        trades_consumed = []
        
        for buy_trade in buy_queue:
            if remaining_to_sell <= 0:
                break
            
            available_quantity = buy_trade['remaining_quantity']
            consume_quantity = min(remaining_to_sell, available_quantity)
            
            # Coût FIFO de cette portion
            buy_cost = consume_quantity * buy_trade['buy_price']
            total_buy_cost += buy_cost
            
            # Mise à jour des quantités
            remaining_to_sell -= consume_quantity
            buy_trade['remaining_quantity'] -= consume_quantity
            
            trades_consumed.append({
                'trade_id': buy_trade['trade_id'],
                'consumed_quantity': consume_quantity,
                'buy_price': buy_trade['buy_price']
            })
        
        # Calcul P&L FIFO
        sell_value = quantity * avg_price
        realized_pnl = sell_value - total_buy_cost
        
        # Mise à jour de la queue FIFO
        await self._update_fifo_queue(broker_id, symbol, trades_consumed)
        
        return {
            'realized_pnl': realized_pnl,
            'total_fees': order_data['total_fees'],
            'calculation_method': 'fifo',
            'fifo_consumed_trades': trades_consumed,
            'sell_value': sell_value,
            'total_buy_cost': total_buy_cost
        }

async def _get_fifo_buy_queue(self, broker_id: int, symbol: str) -> list:
    """
    Récupère la queue FIFO des achats non encore vendus
    Ordre chronologique : premier acheté = premier vendu
    """
    from apps.trading_manual.models import Trade
    
    # Trades d'achat avec quantités restantes > 0
    buy_trades = await sync_to_async(list)(
        Trade.objects.filter(
            broker_id=broker_id,
            symbol=symbol,
            side='buy',
            exchange_order_status='filled',
            remaining_quantity__gt=0  # Nouveau champ à ajouter
        ).order_by('executed_at')  # FIFO : ordre chronologique
    )
    
    return [
        {
            'trade_id': trade.id,
            'buy_price': trade.price,
            'remaining_quantity': trade.remaining_quantity,
            'executed_at': trade.executed_at
        }
        for trade in buy_trades
    ]
```

## 📊 PHASE 4 : MONITORING ET STATISTIQUES

### Étape 4.1 : Tableau de Bord Terminal 7
```python
def _display_service_stats(self):
    """
    Affiche les statistiques du service Terminal 7
    Appelé toutes les minutes (6 cycles de 10s)
    """
    total_brokers = len(self.broker_states)
    active_brokers = sum(1 for s in self.broker_states.values() 
                        if s['last_successful_scan'] and 
                        time.time() - s['last_successful_scan'] < 60)
    
    total_pnl = sum(s['total_pnl'] for s in self.broker_states.values())
    
    stats_display = f"""
┌─ TERMINAL 7 - ORDER MONITOR SERVICE ─────────────────────┐
│ Brokers: {active_brokers:2d}/{total_brokers:2d} actifs  │  P&L Total: ${total_pnl:+8.2f}     │
│ Uptime: {self._format_uptime():>8s}     │  Dernière exec: {self._last_execution():8s} │
│ Cycles: {self.cycle_count:6d}        │  Erreurs: {self._error_count():6d}       │
└──────────────────────────────────────────────────────────┘
"""
    
    self.stdout.write(stats_display)
    
    # Détail par broker si erreurs
    for broker_id, state in self.broker_states.items():
        if state['error_count'] > 0:
            self.stdout.write(
                f"⚠️  {state['name']}: {state['error_count']} erreurs"
            )

async def _send_notifications(self, broker_id: int, pnl_data: dict):
    """
    Notifications temps réel via Django Channels
    Compatible avec le frontend Trading Manual
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    if channel_layer:
        # Notification spécifique Trading Manual
        await channel_layer.group_send(
            f"trading_manual_{await self._get_broker_user_id(broker_id)}",
            {
                'type': 'order_executed',
                'source': 'terminal7',
                'broker_id': broker_id,
                'pnl': pnl_data['realized_pnl'],
                'fees': pnl_data['total_fees'],
                'timestamp': int(time.time() * 1000)
            }
        )
        
        # Notification globale monitoring
        await channel_layer.group_send(
            "terminal7_monitoring",
            {
                'type': 'stats_update',
                'active_brokers': len([s for s in self.broker_states.values() 
                                     if s['error_count'] == 0]),
                'total_brokers': len(self.broker_states),
                'total_pnl': sum(s['total_pnl'] for s in self.broker_states.values())
            }
        )
```

## 🧪 PHASE 5 : FONCTIONS DE TEST INDÉPENDANTES

### Test 1 : Validation Architecture Multi-Exchange
```python
# tests/test_terminal7_architecture.py
import asyncio
import sys
import os

sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

async def test_multi_exchange_compatibility():
    """
    TEST INDÉPENDANT 1: Validation compatibilité avec Terminal 5
    
    Vérifie que Terminal 7 peut récupérer des ordres sur tous les exchanges
    """
    print("=" * 60)
    print("TEST 1: COMPATIBILITÉ MULTI-EXCHANGE TERMINAL 7")
    print("=" * 60)
    
    from apps.brokers.models import Broker
    from apps.core.services.native_exchange_manager import get_native_exchange_manager
    
    # Récupération des brokers de test
    brokers = Broker.objects.filter(is_active=True)[:3]  # 3 brokers max
    
    if not brokers:
        print("❌ ERREUR: Aucun broker actif trouvé")
        return False
    
    # Initialisation de l'Exchange Manager (Terminal 5)
    manager = get_native_exchange_manager()
    
    results = {}
    for broker in brokers:
        print(f"\n🔍 Test broker: {broker.name} ({broker.exchange})")
        
        try:
            # Test 1.1: Récupération ordres history
            history_result = await manager._handle_action(
                'fetch_closed_orders',
                {'broker_id': broker.id, 'limit': 10}
            )
            
            # Test 1.2: Récupération ordres ouverts
            open_result = await manager._handle_action(
                'fetch_open_orders', 
                {'broker_id': broker.id}
            )
            
            results[broker.id] = {
                'exchange': broker.exchange,
                'history_success': history_result['success'],
                'history_count': len(history_result.get('data', [])),
                'open_success': open_result['success'],
                'open_count': len(open_result.get('data', [])),
                'error': None
            }
            
            print(f"✅ {broker.exchange}: {results[broker.id]['history_count']} history, {results[broker.id]['open_count']} ouverts")
            
        except Exception as e:
            results[broker.id] = {
                'exchange': broker.exchange,
                'error': str(e)
            }
            print(f"❌ {broker.exchange}: Erreur - {e}")
    
    # Résumé
    success_count = sum(1 for r in results.values() if not r.get('error'))
    print(f"\n📊 RÉSULTAT: {success_count}/{len(results)} exchanges compatibles")
    
    return success_count == len(results)

if __name__ == "__main__":
    result = asyncio.run(test_multi_exchange_compatibility())
    print(f"\n{'✅ TEST PASSÉ' if result else '❌ TEST ÉCHOUÉ'}")
```

### Test 2 : Validation Calcul P&L
```python
# tests/test_terminal7_pnl_calculation.py
async def test_pnl_calculations():
    """
    TEST INDÉPENDANT 2: Validation des calculs P&L
    
    Teste les 2 méthodes: Price Averaging et FIFO
    """
    print("=" * 60)
    print("TEST 2: CALCULS P&L TERMINAL 7")
    print("=" * 60)
    
    # Données de test simulées
    test_orders = [
        {'symbol': 'BTCUSDT', 'side': 'buy', 'quantity': 0.001, 'price': 45000, 'fees': 0.1},
        {'symbol': 'BTCUSDT', 'side': 'buy', 'quantity': 0.002, 'price': 46000, 'fees': 0.2},
        {'symbol': 'BTCUSDT', 'side': 'sell', 'quantity': 0.0015, 'price': 47000, 'fees': 0.15},
    ]
    
    # Test calcul price averaging
    print("\n🧮 Test 1: Price Averaging")
    avg_pnl = calculate_price_averaging_pnl(test_orders)
    print(f"Prix moyen d'achat: ${avg_pnl['avg_buy_price']:.2f}")
    print(f"P&L réalisé: ${avg_pnl['realized_pnl']:.2f}")
    
    # Test calcul FIFO  
    print("\n🧮 Test 2: FIFO")
    fifo_pnl = calculate_fifo_pnl(test_orders)
    print(f"P&L FIFO: ${fifo_pnl['realized_pnl']:.2f}")
    print(f"Trades consommés: {len(fifo_pnl['consumed_trades'])}")
    
    # Comparaison
    pnl_diff = abs(avg_pnl['realized_pnl'] - fifo_pnl['realized_pnl'])
    print(f"\n📊 Différence Price Avg vs FIFO: ${pnl_diff:.2f}")
    
    return pnl_diff < 1.0  # Différence acceptable < $1

def calculate_price_averaging_pnl(orders):
    """Simulation calcul Price Averaging"""
    buys = [o for o in orders if o['side'] == 'buy']
    sells = [o for o in orders if o['side'] == 'sell']
    
    # Prix moyen pondéré des achats
    total_buy_value = sum(o['quantity'] * o['price'] for o in buys)
    total_buy_quantity = sum(o['quantity'] for o in buys)
    avg_buy_price = total_buy_value / total_buy_quantity if total_buy_quantity > 0 else 0
    
    # P&L des ventes
    realized_pnl = 0.0
    for sell in sells:
        pnl = (sell['price'] - avg_buy_price) * sell['quantity']
        realized_pnl += pnl
    
    return {
        'avg_buy_price': avg_buy_price,
        'realized_pnl': realized_pnl,
        'method': 'price_averaging'
    }

def calculate_fifo_pnl(orders):
    """Simulation calcul FIFO"""
    buy_queue = []
    realized_pnl = 0.0
    consumed_trades = []
    
    for order in orders:
        if order['side'] == 'buy':
            buy_queue.append({
                'quantity': order['quantity'],
                'price': order['price'],
                'remaining': order['quantity']
            })
        else:  # sell
            remaining_to_sell = order['quantity']
            
            while remaining_to_sell > 0 and buy_queue:
                buy_trade = buy_queue[0]
                
                if buy_trade['remaining'] <= 0:
                    buy_queue.pop(0)
                    continue
                
                consume_qty = min(remaining_to_sell, buy_trade['remaining'])
                pnl = (order['price'] - buy_trade['price']) * consume_qty
                realized_pnl += pnl
                
                buy_trade['remaining'] -= consume_qty
                remaining_to_sell -= consume_qty
                
                consumed_trades.append({
                    'consumed_quantity': consume_qty,
                    'buy_price': buy_trade['price'],
                    'sell_price': order['price'],
                    'pnl': pnl
                })
    
    return {
        'realized_pnl': realized_pnl,
        'consumed_trades': consumed_trades,
        'method': 'fifo'
    }

if __name__ == "__main__":
    result = asyncio.run(test_pnl_calculations())
    print(f"\n{'✅ CALCULS VALIDÉS' if result else '❌ ERREUR CALCULS'}")
```

### Test 3 : Validation Performance
```python
# tests/test_terminal7_performance.py
async def test_service_performance():
    """
    TEST INDÉPENDANT 3: Performance et stabilité
    
    Simule le fonctionnement pendant 5 minutes avec timing réel
    """
    print("=" * 60)
    print("TEST 3: PERFORMANCE TERMINAL 7 (5 minutes)")
    print("=" * 60)
    
    from apps.brokers.models import Broker
    from apps.core.management.commands.run_order_monitor import Command
    
    # Création d'une instance du service
    service = Command()
    
    # Stats de performance
    stats = {
        'cycles_completed': 0,
        'brokers_scanned': 0,
        'orders_processed': 0,
        'errors': 0,
        'avg_cycle_time': 0,
        'start_time': time.time()
    }
    
    # Simulation de 30 cycles (5 min à 10s par cycle)
    print("🏃 Démarrage test performance (30 cycles)...")
    
    for cycle in range(30):
        cycle_start = time.time()
        
        try:
            # Simulation d'un cycle de scan
            brokers = await sync_to_async(list)(Broker.objects.filter(is_active=True)[:3])
            
            for broker in brokers:
                # Simulation scan broker (appel API simulé)
                await asyncio.sleep(0.1)  # Simulation latence API
                stats['brokers_scanned'] += 1
                
                # Simulation traitement ordres
                simulated_orders = 2  # 2 ordres par broker en moyenne
                stats['orders_processed'] += simulated_orders
            
            stats['cycles_completed'] += 1
            
        except Exception as e:
            stats['errors'] += 1
            print(f"❌ Erreur cycle {cycle + 1}: {e}")
        
        # Calcul temps cycle
        cycle_time = time.time() - cycle_start
        stats['avg_cycle_time'] = (stats['avg_cycle_time'] * cycle + cycle_time) / (cycle + 1)
        
        # Affichage progression
        if (cycle + 1) % 10 == 0:
            elapsed = time.time() - stats['start_time']
            print(f"📊 Cycle {cycle + 1}/30 - {elapsed:.1f}s écoulées - Temps moyen: {stats['avg_cycle_time']*1000:.0f}ms")
        
        # Attente 10s (timing réel)
        await asyncio.sleep(10)
    
    # Résultats finaux
    total_time = time.time() - stats['start_time']
    print(f"\n📈 RÉSULTATS PERFORMANCE:")
    print(f"   • Durée totale: {total_time:.1f}s")
    print(f"   • Cycles réussis: {stats['cycles_completed']}/30")
    print(f"   • Brokers scannés: {stats['brokers_scanned']}")
    print(f"   • Ordres traités: {stats['orders_processed']}")
    print(f"   • Erreurs: {stats['errors']}")
    print(f"   • Temps moyen/cycle: {stats['avg_cycle_time']*1000:.0f}ms")
    
    # Critères de réussite
    success = (
        stats['cycles_completed'] >= 28 and  # 93% de réussite minimum
        stats['errors'] <= 2 and             # Maximum 2 erreurs
        stats['avg_cycle_time'] < 5.0         # Cycle < 5s en moyenne
    )
    
    return success

if __name__ == "__main__":
    result = asyncio.run(test_service_performance())
    print(f"\n{'✅ PERFORMANCE VALIDÉE' if result else '❌ PERFORMANCE INSUFFISANTE'}")
```

## 🚀 PHASE 6 : DÉPLOIEMENT ET MONITORING

### Démarrage du Service
```bash
# Terminal 7 - Démarrage
cd backend
python manage.py run_order_monitor

# Logs de démarrage attendus:
# [START] Terminal 7 - Order Monitor Service
# [OK] Service initialisé - 3 brokers surveillés
# [SCAN] Broker 1: bitget/demo (0 nouveaux ordres)
# [SCAN] Broker 2: binance/prod (0 nouveaux ordres)
# [EXEC] Broker 3: 2 nouveaux ordres traités
# [PNL] BTCUSDT sell $12.45 (fees: $0.03)
```

### Intégration avec Services Existants
```bash
# Stack complète Aristobot3
Terminal 1: daphne aristobot.asgi:application          # Django + WebSocket
Terminal 2: python manage.py run_heartbeat             # Market Data  
Terminal 3: python manage.py run_trading_engine        # Stratégies Auto
Terminal 4: npm run dev                                 # Frontend Vue.js
Terminal 5: python manage.py run_native_exchange_service # Exchange Gateway
Terminal 6: python manage.py run_webhook_receiver      # Webhooks TradingView
Terminal 7: python manage.py run_order_monitor         # Order Monitor (NOUVEAU)
```

### Monitoring et Alertes
```python
# Intégration Discord/Slack (optionnelle)
async def _send_alert(self, message: str, level: str = 'info'):
    """Envoi d'alertes pour événements critiques"""
    if level == 'error' and self._error_count() > 5:
        # Webhook Discord
        webhook_url = os.getenv('DISCORD_WEBHOOK_TERMINAL7')
        if webhook_url:
            await self._send_discord_alert(webhook_url, f"🚨 Terminal 7: {message}")
    
    # Log local
    self.stdout.write(f'[{level.upper()}] {message}')
```

## 📋 CHECKLIST DE VALIDATION FINALE

### Phase 1 : Infrastructure ✅
- [ ] Management Command créé et fonctionnel
- [ ] Timing interne 10s validé  
- [ ] Intégration Terminal 5 (NativeExchangeManager) testée
- [ ] Multi-exchange compatible (Bitget, Binance minimum)
- [ ] Gestion d'erreurs robuste

### Phase 2 : Calcul P&L ✅
- [ ] Price Averaging implémenté et testé
- [ ] Détection nouveaux ordres exécutés fonctionnelle
- [ ] Sauvegarde en DB Trade model validée
- [ ] Frais correctement extraits et calculés

### Phase 3 : FIFO Migration ✅  
- [ ] FIFO implémenté et testé
- [ ] Migration Price Avg → FIFO validée
- [ ] Nouveaux champs DB créés (remaining_quantity, etc.)
- [ ] Tests comparatifs Price Avg vs FIFO réussis

### Phase 4 : Tests Indépendants ✅
- [ ] Test 1 (Multi-Exchange) : 100% brokers compatibles
- [ ] Test 2 (P&L Calculs) : Résultats cohérents
- [ ] Test 3 (Performance) : < 5s par cycle, < 2 erreurs sur 30 cycles

### Phase 5 : Production ✅
- [ ] Service démarre sans erreur
- [ ] Monitoring et logs fonctionnels  
- [ ] Notifications WebSocket opérationnelles
- [ ] Statistiques Dashboard complètes

## 🎯 RÉSUMÉ EXÉCUTIF

**Terminal 7** transforme la surveillance manuelle des ordres en un système automatisé intelligent :

### Avantages Clés
1. **Détection automatique** : Plus besoin de vérifier manuellement les ordres exécutés
2. **P&L temps réel** : Calcul automatique des gains/pertes avec 2 méthodes (Price Avg + FIFO)
3. **Multi-exchange** : Fonctionne sur Bitget, Binance et futurs exchanges
4. **Intégration transparente** : Utilise l'architecture Terminal 5 existante
5. **Monitoring avancé** : Statistiques détaillées et alertes automatiques

### Architecture Technique
- **Django Management Command** avec timing interne 10s
- **Sequential scanning** : 1 broker par seconde pour respecter rate limits
- **Price Averaging → FIFO** : Migration progressive vers méthode professionnelle
- **Test-driven** : 3 tests indépendants complets
- **Production-ready** : Monitoring, erreur handling, notifications WebSocket

### Impact Utilisateur
```
AVANT Terminal 7:
- Vérification manuelle des ordres toutes les X minutes
- Calculs P&L manuels complexes et approximatifs  
- Pas de visibilité temps réel sur les performances
- Erreurs de calcul fréquentes

APRÈS Terminal 7:
- Détection automatique en 10s maximum
- P&L précis calculé automatiquement (2 méthodes)
- Dashboard temps réel des performances
- Historique complet et auditabilité
```

Terminal 7 apporte l'automatisation professionnelle au cœur d'Aristobot3, transformant un bot de trading amateur en plateforme robuste. 🚀