# -*- coding: utf-8 -*-
"""
SERVICES CORE ARISTOBOT3.1 - NATIVE EXCHANGE ARCHITECTURE

🎯 ARCHITECTURE:
- Clients natifs par exchange (Bitget, Binance, Kraken)
- NativeExchangeManager centralisé (Terminal 5)
- ExchangeClient interface unifiée
- Communication Redis: exchange_requests/exchange_responses
"""

# Native Exchange Architecture - Core services
from .base_exchange_client import BaseExchangeClient, ExchangeClientFactory
from .bitget_native_client import BitgetNativeClient
from .binance_native_client import BinanceNativeClient
from .kraken_native_client import KrakenNativeClient
from .native_exchange_manager import NativeExchangeManager, get_native_exchange_manager
from .exchange_client import ExchangeClient, get_global_exchange_client

# ⚠️ DEPRECATED: Aliases pour rétrocompatibilité temporaire (à supprimer)
from .exchange_client import CCXTClient, get_global_ccxt_client

# Utilities
from .redis_fallback import get_redis_client

__all__ = [
    # Native Exchange Architecture
    'BaseExchangeClient', 'ExchangeClientFactory',
    'BitgetNativeClient', 'BinanceNativeClient', 'KrakenNativeClient',
    'NativeExchangeManager', 'get_native_exchange_manager',
    'ExchangeClient', 'get_global_exchange_client',

    # ⚠️ DEPRECATED: Aliases rétrocompatibilité
    'CCXTClient', 'get_global_ccxt_client',

    # Utilities
    'get_redis_client'
]
