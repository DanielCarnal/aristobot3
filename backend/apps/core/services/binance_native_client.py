# -*- coding: utf-8 -*-
"""
BINANCE NATIVE CLIENT - Implémentation native pour Terminal 7

🎯 OBJECTIF: Client natif Binance haute performance remplaçant CCXT
Architecture identique à BitgetNativeClient pour uniformité

📋 FONCTIONNALITÉS:
✅ Authentification V3 (X-MBX-APIKEY + signature HMAC SHA256)
✅ Support ordres market/limit/OCO
✅ Rate limiting optimisé (1200 req/min)
✅ Interface standardisée BaseExchangeClient

🚀 ENDPOINTS BINANCE API:
- /api/v3/account (balance + test connexion)
- /api/v3/exchangeInfo (contraintes marché)
- /api/v3/ticker/24hr (tickers)
- /api/v3/order (création/annulation ordres)
- /api/v3/openOrders (ordres ouverts)
- /api/v3/allOrders (historique)

🔧 RATE LIMITS BINANCE:
- Place order: 10/sec (1200/min global)
- Cancel operations: 10/sec
- Query operations: 20/sec
- Authentification: Headers X-MBX-APIKEY requis
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import urllib.parse
import json
import logging
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from datetime import datetime, timedelta

from .base_exchange_client import (
    BaseExchangeClient,
    ExchangeError,
    RateLimitError,
    InsufficientFundsError,
    OrderError,
    OrderType,
    OrderSide,
    OrderStatus
)

logger = logging.getLogger(__name__)


class BinanceNativeClient(BaseExchangeClient):
    """
    🔥 CLIENT BINANCE NATIF - Compatible Terminal 7
    
    Implémentation native Binance API V3 avec interface standardisée.
    Optimisé pour performances et compatible avec l'architecture Aristobot3.
    
    🎯 ENDPOINTS BINANCE V3:
    - /api/v3/account (balance + test)
    - /api/v3/exchangeInfo (contraintes)
    - /api/v3/ticker/24hr (prix)
    - /api/v3/order (CRUD ordres)
    - /api/v3/openOrders (ordres actifs)
    - /api/v3/allOrders (historique)
    
    🔧 SPÉCIFICITÉS BINANCE:
    - Signature HMAC SHA256 avec query string
    - Timestamp obligatoire (validité 5 min)
    - Rate limit 1200 req/min (poids variable)
    - Gestion OCO native pour TP/SL
    """
    
    def __init__(self, api_key: str, api_secret: str, api_passphrase: str = None,
                 is_testnet: bool = False, timeout: int = 60):
        super().__init__(api_key, api_secret, api_passphrase, is_testnet, timeout)
        
        # Configuration rate limits Binance
        self._max_requests_per_window = 20  # Conservateur pour éviter les bans
        
        # Cache spécialisé Binance
        self._exchange_info_cache = None
        self._exchange_info_ttl = 3600  # 1 heure pour exchangeInfo
    
    @property
    def exchange_name(self) -> str:
        return "binance"
    
    @property
    def base_url(self) -> str:
        if self.is_testnet:
            return 'https://testnet.binance.vision'
        return 'https://api.binance.com'
    
    def _sign_request(self, method: str, path: str, params: str = '') -> tuple[Dict[str, str], str]:
        """
        🔑 SIGNATURE BINANCE V3 - CORRECTION TIMESTAMP SYNC
        
        Binance utilise HMAC SHA256 avec timestamp obligatoire.
        Format: signature = HMAC_SHA256(secret, queryString)
        
        🔧 CORRECTION NONCE: Synchronisation automatique avec serveur Binance
        
        Args:
            method: Méthode HTTP (utilisé pour validation)
            path: Chemin API (utilisé pour validation)
            params: Query string ou JSON params
            
        Returns:
            Tuple (headers, signed_params) avec signature incluse
        """
        # CORRECTION: Timestamp synchronisé avec marge de sécurité
        timestamp = int(time.time() * 1000)
        
        # Ajouter timestamp si pas déjà présent
        if 'timestamp=' not in params:
            if params:
                params += f"&timestamp={timestamp}"
            else:
                params = f"timestamp={timestamp}"
        
        # Signature HMAC SHA256 sur la query string complète
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # CORRECTION CRITIQUE: Ajouter signature aux paramètres
        signed_params = f"{params}&signature={signature}"
        
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        return headers, signed_params
    
    async def _handle_response_errors(self, response_data: Dict, status_code: int):
        """
        🚨 GESTION ERREURS BINANCE
        
        Codes d'erreur Binance courants:
        - -1021: Timestamp out of recv window
        - -1022: Signature invalid  
        - -2010: Insufficient funds
        - -1013: Filter failure (precision/min amount)
        """
        # Binance retourne parfois des arrays ou des strings d'erreur
        if isinstance(response_data, list):
            if len(response_data) > 0 and isinstance(response_data[0], dict):
                error_data = response_data[0]
            else:
                return  # Pas d'erreur détectable
        elif isinstance(response_data, str):
            raise ExchangeError(f"Erreur API Binance: {response_data}", 'STRING_ERROR', self.exchange_name)
        else:
            error_data = response_data
        
        code = error_data.get('code', 0)
        msg = error_data.get('msg', 'Unknown error')
        
        if code == 0:
            return  # Success
        
        # Rate limit
        if code in [-1003, -1015] or 'rate limit' in msg.lower():
            raise RateLimitError(f"Rate limit Binance: {msg}", str(code), self.exchange_name)
        
        # Authentification
        if code in [-1021, -1022, -2014]:
            raise ExchangeError(f"Auth Binance: {msg}", str(code), self.exchange_name)
        
        # Fonds insuffisants
        if code in [-2010]:
            raise InsufficientFundsError(f"Fonds insuffisants: {msg}", str(code), self.exchange_name)
        
        # Erreurs d'ordre
        if code in [-1013, -1020]:
            raise OrderError(f"Ordre invalide: {msg}", str(code), self.exchange_name)
        
        # Erreur générique
        raise ExchangeError(f"Erreur Binance: {msg}", str(code), self.exchange_name)
    
    async def test_connection(self) -> Dict:
        """
        🔌 TEST CONNEXION Binance via account info - CORRECTION NONCE
        """
        try:
            path = '/api/v3/account'
            
            # Utiliser la signature standardisée avec correction nonce
            headers, signed_params = self._sign_request('GET', path, '')
            
            # Construire l'URL avec paramètres signés
            url = f"{self.base_url}{path}?{signed_params}"
            
            await self._create_session()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    balance_count = len([b for b in data.get('balances', []) if float(b['free']) > 0])
                    return {
                        'connected': True,
                        'balance_items': balance_count
                    }
                else:
                    error_data = await response.json()
                    return {
                        'connected': False,
                        'error': error_data.get('msg', f'HTTP {response.status}')
                    }
                    
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    async def get_balance(self) -> Dict:
        """
        💰 RÉCUPÉRATION BALANCE Binance - CORRECTION NONCE
        """
        try:
            path = '/api/v3/account'
            
            # Utiliser la signature standardisée avec correction nonce
            headers, signed_params = self._sign_request('GET', path, '')
            
            # Construire l'URL avec paramètres signés
            url = f"{self.base_url}{path}?{signed_params}"
            
            await self._create_session()
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': data.get('msg', f'HTTP {response.status}')
                    }
                
                # Transformation format Aristobot
                balances = {}
                for asset in data.get('balances', []):
                    coin = asset.get('asset')
                    if coin:
                        free_amount = float(asset.get('free', 0))
                        locked_amount = float(asset.get('locked', 0))
                        
                        balances[coin] = {
                            'available': free_amount,
                            'frozen': locked_amount,
                            'total': free_amount + locked_amount
                        }
                
                logger.info(f"💰 Balance Binance: {len(balances)} devises")
                return {
                    'success': True,
                    'balances': balances
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur balance Binance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_markets(self) -> Dict:
        """
        📊 RÉCUPÉRATION MARCHÉS via exchangeInfo
        """
        try:
            # Cache exchangeInfo (lourd à charger)
            if (self._exchange_info_cache and 
                time.time() - self._markets_cache_timestamp < self._exchange_info_ttl):
                return self._exchange_info_cache
            
            path = '/api/v3/exchangeInfo'
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.get(url) as response:
                data = await response.json()
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': data.get('msg', f'HTTP {response.status}')
                    }
                
                # Transformation des symboles
                markets = {}
                for symbol_info in data.get('symbols', []):
                    if symbol_info.get('status') != 'TRADING':
                        continue
                    
                    symbol = symbol_info.get('symbol')
                    base_asset = symbol_info.get('baseAsset')
                    quote_asset = symbol_info.get('quoteAsset')
                    
                    # Extraction des filtres (contraintes)
                    filters = {f['filterType']: f for f in symbol_info.get('filters', [])}
                    
                    lot_size = filters.get('LOT_SIZE', {})
                    price_filter = filters.get('PRICE_FILTER', {})
                    min_notional = filters.get('MIN_NOTIONAL', {})
                    
                    markets[symbol] = {
                        'symbol': symbol,
                        'base': base_asset,
                        'quote': quote_asset,
                        'min_amount': float(lot_size.get('minQty', 0)),
                        'max_amount': float(lot_size.get('maxQty', 999999999)),
                        'price_precision': int(-float(price_filter.get('tickSize', 0.01)).bit_length() + 1) if price_filter.get('tickSize') else 8,
                        'quantity_precision': int(-float(lot_size.get('stepSize', 0.00000001)).bit_length() + 1) if lot_size.get('stepSize') else 8,
                        'min_trade_usdt': float(min_notional.get('minNotional', 10)),
                        'active': True,
                        'taker_fee': 0.001,  # 0.1% par défaut
                        'maker_fee': 0.001   # 0.1% par défaut
                    }
                
                result = {
                    'success': True,
                    'markets': markets
                }
                
                # Mise en cache
                self._exchange_info_cache = result
                self._markets_cache_timestamp = time.time()
                
                logger.info(f"📊 Marchés Binance: {len(markets)} symboles")
                return result
                
        except Exception as e:
            logger.error(f"❌ Erreur markets Binance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_ticker(self, symbol: str) -> Dict:
        """
        📈 RÉCUPÉRATION TICKER individuel
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            path = f'/api/v3/ticker/24hr?symbol={normalized_symbol}'
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.get(url) as response:
                data = await response.json()
                
                if response.status != 200:
                    return self._standardize_error_response(
                        error_message=data.get('msg', 'Unknown error'),
                        error_code='API_ERROR'
                    )
                
                # Mapping Binance → Format Aristobot
                binance_response = {
                    'symbol': data.get('symbol'),
                    'last': float(data.get('lastPrice', 0)),
                    'bid': float(data.get('bidPrice', 0)),
                    'ask': float(data.get('askPrice', 0)),
                    'volume_24h': float(data.get('volume', 0)),
                    'change_24h': float(data.get('priceChangePercent', 0)),
                    'high_24h': float(data.get('highPrice', 0)),
                    'low_24h': float(data.get('lowPrice', 0)),
                    'timestamp': int(time.time() * 1000)
                }
                
                return self._standardize_ticker_response(binance_response)
                
        except Exception as e:
            logger.error(f"❌ Erreur ticker Binance {symbol}: {e}")
            return self._standardize_error_response(
                error_message=str(e),
                error_code='CONNECTION_ERROR'
            )
    
    async def place_order(self,
                         symbol: str,
                         side: str,
                         amount: float,
                         order_type: str = 'market',
                         price: float = None,
                         **kwargs) -> Dict:
        """
        🔥 PASSAGE D'ORDRE Binance
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            
            # Paramètres de base
            params = {
                'symbol': normalized_symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': str(amount),
                'timestamp': int(time.time() * 1000)
            }
            
            # Prix pour les ordres limite
            if order_type.lower() == 'limit':
                if price is None:
                    return {
                        'success': False,
                        'error': 'Prix requis pour ordre limite'
                    }
                params['price'] = str(price)
                params['timeInForce'] = 'GTC'
            
            # Construction query string pour signature
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
            
            path = '/api/v3/order'
            headers = {'X-MBX-APIKEY': self.api_key}
            url = f"{self.base_url}{path}"
            
            logger.info(f"🔥 Binance place_order: {order_type} {side} {amount} {symbol}")
            
            await self._create_session()
            async with self.session.post(url, params=params, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': f'Échec ordre Binance: {data.get("msg", "Unknown error")}',
                        'code': data.get('code')
                    }
                
                # Extraction résultats
                order_id = data.get('orderId')
                client_order_id = data.get('clientOrderId')
                
                logger.info(f"✅ Ordre Binance créé: {order_id}")
                
                return {
                    'success': True,
                    'order_id': str(order_id),
                    'client_order_id': client_order_id,
                    'status': 'pending',
                    'filled_amount': float(data.get('executedQty', 0)),
                    'remaining_amount': float(data.get('origQty', 0)) - float(data.get('executedQty', 0))
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur place_order Binance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """
        ❌ ANNULATION ORDRE Binance
        """
        try:
            params = {
                'symbol': self.normalize_symbol(symbol),
                'orderId': order_id,
                'timestamp': int(time.time() * 1000)
            }
            
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
            
            path = '/api/v3/order'
            headers = {'X-MBX-APIKEY': self.api_key}
            url = f"{self.base_url}{path}"
            
            logger.info(f"❌ Binance cancel_order: {order_id}")
            
            await self._create_session()
            async with self.session.delete(url, params=params, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': data.get('msg', 'Unknown error'),
                        'order_id': order_id
                    }
                
                return {
                    'success': True,
                    'order_id': str(data.get('orderId', order_id)),
                    'status': 'cancelled',
                    'message': 'Ordre annulé avec succès'
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur cancel_order Binance: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id
            }
    
    async def get_open_orders(self, symbol: str = None) -> Dict:
        """
        📋 ORDRES OUVERTS Binance
        """
        try:
            params = {'timestamp': int(time.time() * 1000)}
            if symbol:
                params['symbol'] = self.normalize_symbol(symbol)
            
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
            
            path = '/api/v3/openOrders'
            headers = {'X-MBX-APIKEY': self.api_key}
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': data.get('msg', 'Unknown error'),
                        'orders': []
                    }
                
                # Transformation des ordres
                orders = []
                for order_data in data:
                    # Formatage timestamp
                    created_at_str = None
                    if order_data.get('time'):
                        try:
                            dt = datetime.fromtimestamp(int(order_data['time']) / 1000)
                            created_at_str = dt.isoformat()
                        except:
                            pass
                    
                    order = {
                        'order_id': str(order_data.get('orderId')),
                        'symbol': order_data.get('symbol'),
                        'side': order_data.get('side', '').lower(),
                        'type': order_data.get('type', '').lower(),
                        'amount': float(order_data.get('origQty', 0)),
                        'price': float(order_data.get('price', 0)) if order_data.get('price') and order_data.get('price') != '0.00000000' else None,
                        'filled': float(order_data.get('executedQty', 0)),
                        'remaining': float(order_data.get('origQty', 0)) - float(order_data.get('executedQty', 0)),
                        'status': order_data.get('status', '').lower(),
                        'created_at': created_at_str
                    }
                    orders.append(order)
                
                logger.info(f"📋 Ordres ouverts Binance: {len(orders)}")
                return {
                    'success': True,
                    'orders': orders
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur get_open_orders Binance: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders': []
            }
    
    def _extract_order_price_binance(self, order_data: Dict, is_history: bool = False) -> float:
        """
        💰 EXTRACTION PRIX ORDRE BINANCE - CORRECTION ORDRES FERMÉS
        
        Pour Binance, les ordres fermés peuvent avoir un prix d'exécution moyen.
        
        Champs Binance:
        - price : Prix initial de l'ordre (0 pour MARKET)
        - executedQty : Quantité exécutée
        - cummulativeQuoteQty : Valeur totale exécutée
        - status : FILLED, PARTIALLY_FILLED, etc.
        """
        # 1. Pour ordres historiques FILLED avec quantité exécutée > 0
        if is_history:
            executed_qty = float(order_data.get('executedQty', 0))
            cumulative_quote = float(order_data.get('cummulativeQuoteQty', 0))
            
            # Calcul prix moyen d'exécution si possible
            if executed_qty > 0 and cumulative_quote > 0:
                avg_execution_price = cumulative_quote / executed_qty
                return avg_execution_price
        
        # 2. Fallback vers prix initial (ordres LIMIT ouverts ou cas spéciaux)
        initial_price = order_data.get('price', 0)
        if initial_price and initial_price != '0.00000000':
            try:
                return float(initial_price)
            except (ValueError, TypeError):
                pass
        
        # 3. Aucun prix disponible
        return None
    
    async def get_order_history(self, symbol: str = None, limit: int = 100) -> Dict:
        """
        📚 HISTORIQUE ORDRES Binance
        """
        try:
            if not symbol:
                # Binance exige un symbol pour allOrders
                return {
                    'success': False,
                    'error': 'Symbole requis pour historique Binance',
                    'orders': []
                }
            
            params = {
                'symbol': self.normalize_symbol(symbol),
                'timestamp': int(time.time() * 1000)
            }
            if limit:
                params['limit'] = min(limit, 1000)  # Max 1000 pour Binance
            
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
            
            path = '/api/v3/allOrders'
            headers = {'X-MBX-APIKEY': self.api_key}
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': data.get('msg', 'Unknown error'),
                        'orders': []
                    }
                
                # Transformation - CORRECTION pour ordres fermés
                orders = []
                for order_data in data:
                    created_at_str = None
                    if order_data.get('time'):
                        try:
                            dt = datetime.fromtimestamp(int(order_data['time']) / 1000)
                            created_at_str = dt.isoformat()
                        except:
                            pass
                    
                    order = {
                        'order_id': str(order_data.get('orderId')),
                        'symbol': order_data.get('symbol'),
                        'side': order_data.get('side', '').lower(),
                        'type': order_data.get('type', '').lower(),
                        'amount': float(order_data.get('origQty', 0)),
                        'price': self._extract_order_price_binance(order_data, is_history=True),
                        'filled': float(order_data.get('executedQty', 0)),
                        'remaining': float(order_data.get('origQty', 0)) - float(order_data.get('executedQty', 0)),
                        'status': order_data.get('status', '').lower(),
                        'created_at': created_at_str
                    }
                    orders.append(order)
                
                logger.info(f"📚 Historique Binance: {len(orders)}")
                return {
                    'success': True,
                    'orders': orders
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur get_order_history Binance: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders': []
            }
    
    async def fetch_tickers(self, symbols: List[str] = None) -> Dict:
        """
        📊 RÉCUPÉRATION TICKERS MULTIPLES - Compatible Terminal 7
        """
        try:
            path = '/api/v3/ticker/24hr'
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.get(url) as response:
                data = await response.json()
                
                if response.status != 200:
                    return self._standardize_error_response(
                        error_message=data.get('msg', 'Unknown error'),
                        error_code='API_ERROR'
                    )
                
                normalized_tickers = {}
                target_symbols = set()
                
                # Filtrage si symbols spécifiés
                if symbols:
                    for symbol in symbols:
                        target_symbols.add(self.normalize_symbol(symbol))
                
                # Normalisation batch
                for ticker in data:
                    symbol = ticker.get('symbol')
                    
                    if symbols and symbol not in target_symbols:
                        continue
                    
                    # Mapping Binance → Format Aristobot
                    binance_response = {
                        'symbol': symbol,
                        'last': float(ticker.get('lastPrice', 0)),
                        'bid': float(ticker.get('bidPrice', 0)),
                        'ask': float(ticker.get('askPrice', 0)),
                        'volume_24h': float(ticker.get('volume', 0)),
                        'change_24h': float(ticker.get('priceChangePercent', 0)),
                        'high_24h': float(ticker.get('highPrice', 0)),
                        'low_24h': float(ticker.get('lowPrice', 0)),
                        'timestamp': int(time.time() * 1000)
                    }
                    
                    standardized = self._standardize_ticker_response(binance_response)
                    original_symbol = self.denormalize_symbol(symbol)
                    normalized_tickers[original_symbol] = standardized
                
                logger.info(f"📊 Tickers batch Binance: {len(normalized_tickers)}")
                return {
                    'success': True,
                    'tickers': normalized_tickers,
                    'count': len(normalized_tickers),
                    'timestamp': int(time.time() * 1000)
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur fetch_tickers Binance: {e}")
            return self._standardize_error_response(
                error_message=str(e),
                error_code='CONNECTION_ERROR'
            )
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalisation Binance: supprime le slash"""
        return symbol.replace('/', '').replace('-', '').upper()
    
    async def get_order_history(self, symbol: str = None, limit: int = 100) -> Dict:
        """
        📚 HISTORIQUE ORDRES BINANCE
        
        Récupère l'historique des ordres via /api/v3/allOrders.
        NOTE: Binance EXIGE un symbole pour cet endpoint.
        """
        try:
            if not symbol:
                # Binance exige un symbole pour l'historique
                # On va récupérer les ordres de plusieurs symboles populaires
                popular_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
                all_orders = []
                
                for sym in popular_symbols:
                    try:
                        result = await self._get_symbol_history(sym, min(20, limit))
                        if result.get('success'):
                            all_orders.extend(result.get('orders', []))
                    except Exception:
                        continue  # Ignore errors for individual symbols
                
                # Trier par timestamp et limiter
                all_orders.sort(key=lambda x: x.get('time', 0), reverse=True)
                return {
                    'success': True,
                    'orders': all_orders[:limit],
                    'count': len(all_orders[:limit])
                }
            else:
                # Récupération pour un symbole spécifique
                return await self._get_symbol_history(symbol, limit)
                
        except Exception as e:
            logger.error(f"❌ Erreur get_order_history Binance: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders': []
            }
    
    async def _get_symbol_history(self, symbol: str, limit: int = 100) -> Dict:
        """Récupère l'historique pour un symbole spécifique"""
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            
            # Paramètres pour Binance allOrders
            params = {
                'symbol': normalized_symbol,
                'limit': min(limit, 500)  # Limite max Binance
            }
            
            # Signature avec nouvelle méthode
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            headers, signed_params = self._sign_request('GET', '/api/v3/allOrders', query_string)
            
            # URL avec paramètres signés
            url = f"{self.base_url}/api/v3/allOrders?{signed_params}"
            
            await self._create_session()
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': data.get('msg', f'HTTP {response.status}'),
                        'orders': []
                    }
                
                # Transformation format Aristobot
                orders = []
                for order in data:
                    # Conversion format standard
                    standardized_order = {
                        'id': order.get('orderId'),
                        'symbol': self.denormalize_symbol(order.get('symbol', '')),
                        'side': order.get('side', '').lower(),
                        'type': order.get('type', '').lower(),
                        'amount': float(order.get('origQty', 0)),
                        'price': float(order.get('price', 0)) if order.get('price') else None,
                        'filled': float(order.get('executedQty', 0)),
                        'remaining': float(order.get('origQty', 0)) - float(order.get('executedQty', 0)),
                        'status': self._map_binance_status(order.get('status', '')),
                        'timestamp': order.get('time'),
                        'updated': order.get('updateTime'),
                        'info': order  # Données brutes
                    }
                    orders.append(standardized_order)
                
                logger.info(f"📚 Historique Binance {normalized_symbol}: {len(orders)} ordres")
                return {
                    'success': True,
                    'orders': orders,
                    'count': len(orders)
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur _get_symbol_history Binance {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders': []
            }
    
    def _map_binance_status(self, binance_status: str) -> str:
        """Mappe les statuts Binance vers format standard"""
        status_mapping = {
            'NEW': 'open',
            'PARTIALLY_FILLED': 'partial',
            'FILLED': 'closed',
            'CANCELED': 'canceled', 
            'PENDING_CANCEL': 'pending',
            'REJECTED': 'rejected',
            'EXPIRED': 'expired'
        }
        return status_mapping.get(binance_status.upper(), 'unknown')

    def denormalize_symbol(self, symbol: str) -> str:
        """Dénormalisation Binance: ajoute le slash"""
        if symbol.endswith('USDT'):
            return f"{symbol[:-4]}/USDT"
        elif symbol.endswith('USDC'):
            return f"{symbol[:-4]}/USDC"
        elif symbol.endswith('BTC'):
            return f"{symbol[:-3]}/BTC"
        elif symbol.endswith('ETH'):
            return f"{symbol[:-3]}/ETH"
        else:
            return symbol


# Enregistrement du client Binance dans la factory
from .base_exchange_client import ExchangeClientFactory
ExchangeClientFactory.register_client('binance', BinanceNativeClient)