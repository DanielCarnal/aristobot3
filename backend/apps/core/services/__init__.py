# -*- coding: utf-8 -*-
"""
SERVICES CORE ARISTOBOT3.1 - NATIVE EXCHANGE ARCHITECTURE

🎯 ARCHITECTURE MODERNE:
- Clients natifs par exchange (Bitget, Binance, Kraken)
- NativeExchangeManager centralisé
- ExchangeClient compatible avec ancienne interface CCXT

✅ NETTOYAGE CCXT COMPLET:
- CCXTManager supprimé (obsolète)
- ccxt_client supprimé (obsolète)  
- Migration 100% terminée vers architecture native
"""

# Native Exchange Architecture - Core services
from .base_exchange_client import BaseExchangeClient, ExchangeClientFactory
from .bitget_native_client import BitgetNativeClient
from .binance_native_client import BinanceNativeClient
from .kraken_native_client import KrakenNativeClient
from .native_exchange_manager import NativeExchangeManager, get_native_exchange_manager
from .exchange_client import ExchangeClient, get_global_exchange_client

# Compatibility aliases pour migration transparente
from .exchange_client import CCXTClient, get_global_ccxt_client

# Utilities
from .redis_fallback import get_redis_client

__all__ = [
    # Native Exchange Architecture
    'BaseExchangeClient', 'ExchangeClientFactory',
    'BitgetNativeClient', 'BinanceNativeClient', 'KrakenNativeClient',
    'NativeExchangeManager', 'get_native_exchange_manager',
    'ExchangeClient', 'get_global_exchange_client',
    
    # Compatibility aliases (pour modules existants)
    'CCXTClient', 'get_global_ccxt_client',
    
    # Utilities
    'get_redis_client'
]
