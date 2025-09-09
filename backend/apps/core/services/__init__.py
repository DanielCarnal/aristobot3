# -*- coding: utf-8 -*-
# Legacy CCXT imports (preserved for backward compatibility)
from .ccxt_manager import CCXTManager

# Native Exchange Architecture - New imports
from .base_exchange_client import BaseExchangeClient, ExchangeClientFactory
from .bitget_native_client import BitgetNativeClient
from .native_exchange_manager import NativeExchangeManager, get_native_exchange_manager
from .exchange_client import ExchangeClient, get_global_exchange_client

# Compatibility aliases for seamless migration
from .exchange_client import CCXTClient, get_global_ccxt_client

__all__ = [
    # Legacy CCXT
    'CCXTManager',
    
    # Native Exchange Architecture
    'BaseExchangeClient', 'ExchangeClientFactory',
    'BitgetNativeClient',
    'NativeExchangeManager', 'get_native_exchange_manager',
    'ExchangeClient', 'get_global_exchange_client',
    
    # Compatibility aliases
    'CCXTClient', 'get_global_ccxt_client'
]
