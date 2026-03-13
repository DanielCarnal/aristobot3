# Strategies Expert - Aristobot3

Expert stratégies de trading pour Aristobot3.1 - Spécialiste Pandas TA Classic et logique de trading.

## Rôle

Expert en développement de stratégies de trading automatiques pour Aristobot3.1. Maîtrise de Pandas TA Classic, patterns de stratégies, et backtesting.

## Architecture Stratégies

### Modules Concernés
- **Module 5** : Stratégies (CRUD, éditeur code) - 🚧 Planned
- **Module 7** : Trading Engine (exécution) - 🚧 Placeholder
- **Module 6** : Backtest (simulation) - 🚧 Planned

### Template de Base
```python
class MaStrategie(Strategy):
    """Template de base pour stratégies Aristobot3"""

    def __init__(self, candles, balance, position=None):
        self.candles = candles      # DataFrame Pandas avec OHLCV
        self.balance = balance      # Dict balance exchange
        self.position = position    # Position ouverte ou None

    def should_long(self) -> bool:
        """Décide si on doit acheter (position longue)"""
        # Retourner True pour acheter
        return False

    def should_short(self) -> bool:
        """Décide si on doit vendre à découvert (futures only)"""
        # Retourner True pour shorter
        return False

    def calculate_position_size(self) -> float:
        """Calcule la taille de position en USD"""
        # Ex: 10% du capital
        return self.balance['USDT']['available'] * 0.1

    def calculate_stop_loss(self) -> float:
        """Calcule le stop loss en pourcentage"""
        # Ex: -2%
        return 0.02

    def calculate_take_profit(self) -> float:
        """Calcule le take profit en pourcentage"""
        # Ex: +4%
        return 0.04
```

## Pandas TA Classic

### Installation
```bash
pip install -U git+https://github.com/xgboosted/pandas-ta-classic
```

### Import
```python
import pandas_ta as ta
```

### Indicateurs Disponibles

#### Moving Averages
```python
# Simple Moving Average
df['sma20'] = ta.sma(df['close'], length=20)

# Exponential Moving Average
df['ema10'] = ta.ema(df['close'], length=10)
df['ema20'] = ta.ema(df['close'], length=20)

# Weighted Moving Average
df['wma'] = ta.wma(df['close'], length=20)
```

#### Momentum
```python
# RSI (Relative Strength Index)
df['rsi'] = ta.rsi(df['close'], length=14)

# MACD
macd = ta.macd(df['close'])
df['macd'] = macd['MACD_12_26_9']
df['macd_signal'] = macd['MACDs_12_26_9']
df['macd_hist'] = macd['MACDh_12_26_9']

# Stochastic
stoch = ta.stoch(df['high'], df['low'], df['close'])
df['stoch_k'] = stoch['STOCHk_14_3_3']
df['stoch_d'] = stoch['STOCHd_14_3_3']
```

#### Volatility
```python
# Bollinger Bands
bbands = ta.bbands(df['close'], length=20, std=2)
df['bb_upper'] = bbands['BBU_20_2.0']
df['bb_middle'] = bbands['BBM_20_2.0']
df['bb_lower'] = bbands['BBL_20_2.0']

# ATR (Average True Range)
df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
```

#### Volume
```python
# OBV (On-Balance Volume)
df['obv'] = ta.obv(df['close'], df['volume'])

# VWAP (Volume Weighted Average Price)
df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
```

## Exemples de Stratégies

### 1. Croisement EMA 10/20
```python
import pandas_ta as ta

class CrossoverEMA(Strategy):
    """Stratégie croisement EMA 10 au-dessus EMA 20"""

    def __init__(self, candles, balance, position=None):
        self.candles = candles
        self.balance = balance
        self.position = position

        # Calculer indicateurs
        self.candles['ema10'] = ta.ema(self.candles['close'], length=10)
        self.candles['ema20'] = ta.ema(self.candles['close'], length=20)

    def should_long(self) -> bool:
        """Buy: EMA 10 croise au-dessus EMA 20"""
        if len(self.candles) < 21:
            return False

        ema10_now = self.candles['ema10'].iloc[-1]
        ema10_prev = self.candles['ema10'].iloc[-2]
        ema20_now = self.candles['ema20'].iloc[-1]
        ema20_prev = self.candles['ema20'].iloc[-2]

        # Croisement haussier
        return ema10_prev < ema20_prev and ema10_now > ema20_now

    def should_short(self) -> bool:
        """Sell: EMA 10 croise en-dessous EMA 20"""
        if len(self.candles) < 21:
            return False

        ema10_now = self.candles['ema10'].iloc[-1]
        ema10_prev = self.candles['ema10'].iloc[-2]
        ema20_now = self.candles['ema20'].iloc[-1]
        ema20_prev = self.candles['ema20'].iloc[-2]

        # Croisement baissier
        return ema10_prev > ema20_prev and ema10_now < ema20_now

    def calculate_position_size(self) -> float:
        return self.balance['USDT']['available'] * 0.1

    def calculate_stop_loss(self) -> float:
        return 0.02  # -2%

    def calculate_take_profit(self) -> float:
        return 0.04  # +4%
```

### 2. RSI Oversold/Overbought
```python
import pandas_ta as ta

class RSIStrategy(Strategy):
    """Stratégie RSI survendu/suracheté"""

    def __init__(self, candles, balance, position=None):
        self.candles = candles
        self.balance = balance
        self.position = position

        # RSI
        self.candles['rsi'] = ta.rsi(self.candles['close'], length=14)

    def should_long(self) -> bool:
        """Buy: RSI < 30 (survendu)"""
        if len(self.candles) < 15:
            return False

        rsi = self.candles['rsi'].iloc[-1]
        return rsi < 30

    def should_short(self) -> bool:
        """Sell: RSI > 70 (suracheté)"""
        if len(self.candles) < 15:
            return False

        rsi = self.candles['rsi'].iloc[-1]
        return rsi > 70

    def calculate_position_size(self) -> float:
        return self.balance['USDT']['available'] * 0.15

    def calculate_stop_loss(self) -> float:
        # Stop loss dynamique basé sur ATR
        atr = ta.atr(
            self.candles['high'],
            self.candles['low'],
            self.candles['close'],
            length=14
        ).iloc[-1]

        current_price = self.candles['close'].iloc[-1]
        stop_loss_price = current_price - (2 * atr)

        return abs(stop_loss_price - current_price) / current_price

    def calculate_take_profit(self) -> float:
        return 0.05  # +5%
```

### 3. Bollinger Bands Breakout
```python
import pandas_ta as ta

class BollingerBreakout(Strategy):
    """Stratégie breakout Bollinger Bands"""

    def __init__(self, candles, balance, position=None):
        self.candles = candles
        self.balance = balance
        self.position = position

        # Bollinger Bands
        bbands = ta.bbands(self.candles['close'], length=20, std=2)
        self.candles['bb_upper'] = bbands['BBU_20_2.0']
        self.candles['bb_middle'] = bbands['BBM_20_2.0']
        self.candles['bb_lower'] = bbands['BBL_20_2.0']

    def should_long(self) -> bool:
        """Buy: Prix touche bande inférieure"""
        if len(self.candles) < 21:
            return False

        close = self.candles['close'].iloc[-1]
        bb_lower = self.candles['bb_lower'].iloc[-1]

        return close <= bb_lower

    def should_short(self) -> bool:
        """Sell: Prix touche bande supérieure"""
        if len(self.candles) < 21:
            return False

        close = self.candles['close'].iloc[-1]
        bb_upper = self.candles['bb_upper'].iloc[-1]

        return close >= bb_upper

    def calculate_position_size(self) -> float:
        return self.balance['USDT']['available'] * 0.12

    def calculate_stop_loss(self) -> float:
        # Stop loss à la bande du milieu
        close = self.candles['close'].iloc[-1]
        bb_middle = self.candles['bb_middle'].iloc[-1]

        return abs(bb_middle - close) / close

    def calculate_take_profit(self) -> float:
        # Take profit à la bande opposée
        close = self.candles['close'].iloc[-1]
        bb_upper = self.candles['bb_upper'].iloc[-1]

        return abs(bb_upper - close) / close
```

## Exécution par Trading Engine

### Chargement Dynamique
```python
# Trading Engine charge code depuis DB
strategy_code = Strategy.objects.get(id=123).code

# Exécution dans namespace isolé
local_vars = {}
exec(strategy_code, {}, local_vars)

# Trouver classe Strategy
strategy_class = None
for name, obj in local_vars.items():
    if isinstance(obj, type) and issubclass(obj, Strategy):
        strategy_class = obj
        break

# Instancier avec données
strategy_instance = strategy_class(candles, balance, position)

# Exécuter logique
if strategy_instance.should_long():
    # Passer ordre via ExchangeClient
    pass
```

### Accès Données via ExchangeClient

**Important** : Trading Engine utilise ExchangeClient (pas CCXT direct)

```python
from apps.core.services.exchange_client import ExchangeClient

# Initialiser client
exchange_client = ExchangeClient(user_id=strategy.user_id)

# Récupérer balance
balance = await exchange_client.get_balance(broker_id)

# Récupérer bougies (via Terminal 5)
candles = await exchange_client.get_candles(
    broker_id,
    symbol='BTC/USDT',
    timeframe='15m',
    limit=200
)

# Convertir en DataFrame Pandas
import pandas as pd
df = pd.DataFrame(candles)

# Passer à stratégie
strategy = StrategyClass(df, balance, position)
```

## Backtesting

### Structure Backtest
```python
class BacktestEngine:
    """Moteur de backtest pour stratégies"""

    def __init__(self, strategy, symbol, timeframe, start_date, end_date, initial_balance):
        self.strategy = strategy
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.balance = {'USDT': {'available': initial_balance}}
        self.position = None
        self.trades = []

    async def run(self):
        """Exécute le backtest"""
        # 1. Charger bougies historiques via ExchangeClient
        exchange_client = ExchangeClient(user_id=self.user_id)
        candles = await self._load_historical_candles(exchange_client)

        # 2. Itérer sur chaque bougie
        for i in range(200, len(candles)):  # Window de 200 bougies
            window = candles.iloc[i-200:i]

            # Instancier stratégie avec window
            strategy = self.strategy(window, self.balance, self.position)

            # Vérifier signaux
            if strategy.should_long() and not self.position:
                self._execute_buy(candles.iloc[i], strategy)

            elif strategy.should_short() and self.position:
                self._execute_sell(candles.iloc[i])

        # 3. Calculer statistiques
        return self._calculate_stats()

    def _execute_buy(self, candle, strategy):
        """Simule achat"""
        size = strategy.calculate_position_size()
        price = candle['close']
        quantity = size / price

        self.position = {
            'entry_price': price,
            'quantity': quantity,
            'stop_loss': price * (1 - strategy.calculate_stop_loss()),
            'take_profit': price * (1 + strategy.calculate_take_profit())
        }

        self.balance['USDT']['available'] -= size

    def _execute_sell(self, candle):
        """Simule vente"""
        price = candle['close']
        size = self.position['quantity'] * price

        pnl = size - (self.position['quantity'] * self.position['entry_price'])

        self.trades.append({
            'entry': self.position['entry_price'],
            'exit': price,
            'pnl': pnl,
            'pnl_pct': (price / self.position['entry_price'] - 1) * 100
        })

        self.balance['USDT']['available'] += size
        self.position = None
```

## Gotchas Stratégies

### 1. DataFrame Pandas requis
```python
# ✅ CORRECT
self.candles = pd.DataFrame(candles)  # DataFrame Pandas

# ❌ ERREUR
self.candles = candles  # Liste de dicts
```

### 2. Vérifier longueur données
```python
# ✅ TOUJOURS vérifier
if len(self.candles) < 21:
    return False  # Pas assez de données pour EMA 20

# ❌ Crash si pas assez de données
ema20 = ta.ema(self.candles['close'], length=20)  # IndexError!
```

### 3. iloc[-1] pour dernière valeur
```python
# ✅ CORRECT
current_price = self.candles['close'].iloc[-1]

# ❌ ERREUR
current_price = self.candles['close'][-1]  # Pandas warning
```

### 4. Croisements = comparaison avec bougie précédente
```python
# ✅ CORRECT - Vérifier croisement
ema10_now = self.candles['ema10'].iloc[-1]
ema10_prev = self.candles['ema10'].iloc[-2]

crossover = ema10_prev < ema20_prev and ema10_now > ema20_now

# ❌ ERREUR - Seulement position actuelle
crossover = self.candles['ema10'].iloc[-1] > self.candles['ema20'].iloc[-1]
```

### 5. ExchangeClient pour données (pas CCXT)
```python
# ✅ CORRECT
from apps.core.services.exchange_client import ExchangeClient
exchange_client = ExchangeClient(user_id=user.id)
candles = await exchange_client.get_candles(broker_id, symbol, timeframe)

# ❌ DEPRECATED
import ccxt
exchange = ccxt.bitget(...)
candles = exchange.fetch_ohlcv(symbol, timeframe)
```

## Ressources

### Documentation Pandas TA
- **GitHub** : https://github.com/xgboosted/pandas-ta-classic
- **Indicateurs** : 130+ indicateurs disponibles
- **Categories** : Overlap, Momentum, Volume, Volatility, Trend

### Trading Engine
- **Fichier** : `backend/apps/trading_engine/management/commands/run_trading_engine.py`
- **Status** : 🚧 Placeholder (Module 7)
- **Communication** : ExchangeClient via Terminal 5

### Backtest
- **Module** : `backend/apps/backtest/` - 🚧 Planned
- **Données** : Table `candles` PostgreSQL
- **Output** : Table `backtest_results`

---

**Dernière mise à jour** : Janvier 2026 (ExchangeClient pour données stratégies)
