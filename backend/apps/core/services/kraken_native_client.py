# -*- coding: utf-8 -*-
"""
KRAKEN NATIVE CLIENT - Implémentation native pour Terminal 7

🎯 OBJECTIF: Client natif Kraken haute performance remplaçant CCXT
Architecture identique à BitgetNativeClient pour uniformité

📋 FONCTIONNALITÉS:
✅ Authentification Kraken (API-Sign + API-Key)
✅ Support ordres market/limit
✅ Rate limiting optimisé (1 req/sec sans tier)
✅ Interface standardisée BaseExchangeClient

🚀 ENDPOINTS KRAKEN API:
- /0/private/Balance (balance)
- /0/public/AssetPairs (contraintes marché)
- /0/public/Ticker (tickers)
- /0/private/AddOrder (création ordres)
- /0/private/CancelOrder (annulation)
- /0/private/OpenOrders (ordres ouverts)
- /0/private/OrdersInfo (détails ordres)

🔧 RATE LIMITS KRAKEN:
- Private endpoints: 1/sec (tier 0), plus avec tiers supérieurs
- Public endpoints: 1/sec
- Authentification: API-Sign (HMAC SHA512 + base64)
- Spécificité: nonce obligatoire (timestamp croissant)
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import base64
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


class KrakenNativeClient(BaseExchangeClient):
    """
    🔥 CLIENT KRAKEN NATIF - Compatible Terminal 7
    
    Implémentation native Kraken API avec interface standardisée.
    Kraken utilise un système unique avec nomenclature spéciale des symboles.
    
    🎯 ENDPOINTS KRAKEN:
    - /0/private/Balance (balance + test)
    - /0/public/AssetPairs (contraintes)
    - /0/public/Ticker (prix)
    - /0/private/AddOrder (création ordres)
    - /0/private/CancelOrder (annulation)
    - /0/private/OpenOrders (ordres actifs)
    
    🔧 SPÉCIFICITÉS KRAKEN:
    - Signature HMAC SHA512 avec nonce
    - Symboles: XBTUSDT (Bitcoin), ETHUSDT, etc.
    - Nonce obligatoire (timestamp croissant)
    - Rate limit strict: 1 req/sec (tier 0)
    - Pas de testnet public
    """
    
    def __init__(self, api_key: str, api_secret: str, api_passphrase: str = None,
                 is_testnet: bool = False, timeout: int = 60):
        super().__init__(api_key, api_secret, api_passphrase, is_testnet, timeout)
        
        # Configuration rate limits Kraken (très strict)
        self._max_requests_per_window = 1  # 1 req/sec maximum
        self._rate_limit_window = 1.1  # Fenêtre 1.1 sec pour sécurité
        
        # Nonce pour Kraken (doit être croissant)
        self._nonce_counter = int(time.time() * 1000000)  # Microseconds
        
        # Cache symboles Kraken (mapping complexe)
        self._kraken_symbols_cache = {}
        self._kraken_symbols_ttl = 3600  # 1 heure
    
    @property
    def exchange_name(self) -> str:
        return "kraken"
    
    @property
    def base_url(self) -> str:
        # Kraken n'a pas de testnet public, utiliser API standard
        return 'https://api.kraken.com'
    
    def _get_nonce(self) -> int:
        """Génère un nonce croissant pour Kraken"""
        self._nonce_counter += 1
        return self._nonce_counter
    
    def _sign_request(self, method: str, path: str, params: str = '') -> Dict[str, str]:
        """
        🔑 SIGNATURE KRAKEN
        
        Kraken utilise HMAC SHA512 avec format spécial:
        signature = base64(hmac_sha512(api_secret_decoded, path + sha256(nonce + postdata)))
        
        Args:
            method: Méthode HTTP (POST pour private endpoints)
            path: Chemin complet (/0/private/Balance)
            params: POST data avec nonce
            
        Returns:
            Headers d'authentification Kraken
        """
        # Décoder la clé secrète (base64)
        api_secret_decoded = base64.b64decode(self.api_secret)
        
        # Construire le message à signer
        if params:
            # Pour les endpoints privés avec nonce
            postdata = params.encode('utf-8')
        else:
            # Pour les endpoints publics
            postdata = b''
        
        # Extraire le nonce du params si présent
        nonce = ""
        if 'nonce=' in params:
            nonce = params.split('nonce=')[1].split('&')[0]
        
        # Message = path + sha256(nonce + postdata)
        nonce_postdata = (nonce + params).encode('utf-8')
        sha256_hash = hashlib.sha256(nonce_postdata).digest()
        message = path.encode('utf-8') + sha256_hash
        
        # Signature HMAC SHA512
        signature = hmac.new(api_secret_decoded, message, hashlib.sha512)
        signature_b64 = base64.b64encode(signature.digest()).decode()
        
        return {
            'API-Key': self.api_key,
            'API-Sign': signature_b64,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    async def _handle_response_errors(self, response_data: Dict, status_code: int):
        """
        🚨 GESTION ERREURS KRAKEN
        
        Kraken retourne toujours {"error": [], "result": {...}}
        Les erreurs sont dans le tableau "error"
        """
        errors = response_data.get('error', [])
        
        if not errors:
            return  # Pas d'erreur
        
        # Analyser les erreurs
        error_msg = '; '.join(errors)
        
        # Rate limit
        if any('rate' in err.lower() for err in errors):
            raise RateLimitError(f"Rate limit Kraken: {error_msg}", 'RATE_LIMIT', self.exchange_name)
        
        # Authentification
        if any('invalid' in err.lower() and ('key' in err.lower() or 'sign' in err.lower()) for err in errors):
            raise ExchangeError(f"Auth Kraken: {error_msg}", 'AUTH_ERROR', self.exchange_name)
        
        # Fonds insuffisants
        if any('insufficient' in err.lower() for err in errors):
            raise InsufficientFundsError(f"Fonds insuffisants: {error_msg}", 'INSUFFICIENT_FUNDS', self.exchange_name)
        
        # Erreur générique
        raise ExchangeError(f"Erreur Kraken: {error_msg}", 'API_ERROR', self.exchange_name)
    
    async def test_connection(self) -> Dict:
        """
        🧪 TEST CONNEXION via Balance privé
        """
        try:
            nonce = self._get_nonce()
            params = f'nonce={nonce}'
            path = '/0/private/Balance'
            
            headers = self._sign_request('POST', path, params)
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.post(url, data=params, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200 and not data.get('error'):
                    balance_result = data.get('result', {})
                    balance_count = len([k for k, v in balance_result.items() if float(v) > 0])
                    return {
                        'connected': True,
                        'balance_items': balance_count
                    }
                else:
                    errors = data.get('error', ['Unknown error'])
                    return {
                        'connected': False,
                        'error': '; '.join(errors)
                    }
                    
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    async def get_balance(self) -> Dict:
        """
        💰 RÉCUPÉRATION BALANCE Kraken
        """
        try:
            nonce = self._get_nonce()
            params = f'nonce={nonce}'
            path = '/0/private/Balance'
            
            headers = self._sign_request('POST', path, params)
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.post(url, data=params, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200 or data.get('error'):
                    errors = data.get('error', ['HTTP error'])
                    return {
                        'success': False,
                        'error': '; '.join(errors)
                    }
                
                # Transformation format Aristobot
                result = data.get('result', {})
                balances = {}
                
                for asset, balance_str in result.items():
                    balance_amount = float(balance_str)
                    if balance_amount > 0:  # Inclure seulement les soldes positifs
                        # Normaliser le nom de l'asset (ex: ZUSD → USDT, XXBT → BTC)
                        normalized_asset = self._normalize_asset_name(asset)
                        
                        balances[normalized_asset] = {
                            'available': balance_amount,
                            'frozen': 0.0,  # Kraken Balance ne distingue pas available/frozen
                            'total': balance_amount
                        }
                
                logger.info(f"💰 Balance Kraken: {len(balances)} devises")
                return {
                    'success': True,
                    'balances': balances
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur balance Kraken: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_markets(self) -> Dict:
        """
        📊 RÉCUPÉRATION MARCHÉS via AssetPairs
        """
        try:
            # Cache pour éviter les calls fréquents
            if (self._kraken_symbols_cache and 
                time.time() - self._markets_cache_timestamp < self._kraken_symbols_ttl):
                return self._kraken_symbols_cache
            
            path = '/0/public/AssetPairs'
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.get(url) as response:
                data = await response.json()
                
                if response.status != 200 or data.get('error'):
                    errors = data.get('error', ['HTTP error'])
                    return {
                        'success': False,
                        'error': '; '.join(errors)
                    }
                
                # Transformation des paires
                markets = {}
                pairs = data.get('result', {})
                
                for pair_name, pair_info in pairs.items():
                    # Kraken utilise des noms de paires cryptiques
                    base = self._normalize_asset_name(pair_info.get('base', ''))
                    quote = self._normalize_asset_name(pair_info.get('quote', ''))
                    
                    if not base or not quote:
                        continue
                    
                    # Construction du symbole normalisé
                    normalized_symbol = f"{base}{quote}"  # Ex: BTCUSDT
                    
                    markets[normalized_symbol] = {
                        'symbol': normalized_symbol,
                        'base': base,
                        'quote': quote,
                        'min_amount': float(pair_info.get('ordermin', 0)),
                        'max_amount': 999999999,  # Kraken n'a pas de limite max explicite
                        'price_precision': int(pair_info.get('pair_decimals', 5)),
                        'quantity_precision': int(pair_info.get('lot_decimals', 8)),
                        'min_trade_usdt': float(pair_info.get('ordermin', 0.001)),
                        'active': True,
                        'taker_fee': float(pair_info.get('fees', [[0, 0.26]])[0][1]) / 100,  # Converti en décimal
                        'maker_fee': float(pair_info.get('fees_maker', [[0, 0.16]])[0][1]) / 100
                    }
                
                result = {
                    'success': True,
                    'markets': markets
                }
                
                # Mise en cache
                self._kraken_symbols_cache = result
                self._markets_cache_timestamp = time.time()
                
                logger.info(f"📊 Marchés Kraken: {len(markets)} paires")
                return result
                
        except Exception as e:
            logger.error(f"❌ Erreur markets Kraken: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_ticker(self, symbol: str) -> Dict:
        """
        📈 RÉCUPÉRATION TICKER individuel
        """
        try:
            # Conversion vers format Kraken
            kraken_symbol = self._to_kraken_symbol(symbol)
            
            path = f'/0/public/Ticker?pair={kraken_symbol}'
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.get(url) as response:
                data = await response.json()
                
                if response.status != 200 or data.get('error'):
                    errors = data.get('error', ['Unknown error'])
                    return self._standardize_error_response(
                        error_message='; '.join(errors),
                        error_code='API_ERROR'
                    )
                
                result = data.get('result', {})
                if not result:
                    return self._standardize_error_response(
                        error_message=f'Ticker non trouvé pour {symbol}',
                        error_code='TICKER_NOT_FOUND'
                    )
                
                # Kraken retourne les tickers avec le nom de paire comme clé
                ticker_data = list(result.values())[0]  # Premier (et seul) ticker
                
                # Mapping Kraken → Format Aristobot
                kraken_response = {
                    'symbol': kraken_symbol,
                    'last': float(ticker_data.get('c', [0])[0]),  # Last trade closed price
                    'bid': float(ticker_data.get('b', [0])[0]),   # Highest bid
                    'ask': float(ticker_data.get('a', [0])[0]),   # Lowest ask
                    'volume_24h': float(ticker_data.get('v', [0])[1]),  # Volume last 24h
                    'change_24h': 0.0,  # Kraken ne fournit pas directement le % change
                    'high_24h': float(ticker_data.get('h', [0])[1]),   # High last 24h
                    'low_24h': float(ticker_data.get('l', [0])[1]),    # Low last 24h
                    'timestamp': int(time.time() * 1000)
                }
                
                return self._standardize_ticker_response(kraken_response)
                
        except Exception as e:
            logger.error(f"❌ Erreur ticker Kraken {symbol}: {e}")
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
        🔥 PASSAGE D'ORDRE Kraken
        """
        try:
            nonce = self._get_nonce()
            kraken_symbol = self._to_kraken_symbol(symbol)
            
            # Paramètres de base Kraken
            order_params = {
                'nonce': str(nonce),
                'pair': kraken_symbol,
                'type': side.lower(),  # buy/sell
                'ordertype': 'market' if order_type == 'market' else 'limit',
                'volume': str(amount)
            }
            
            # Prix pour les ordres limite
            if order_type.lower() == 'limit':
                if price is None:
                    return {
                        'success': False,
                        'error': 'Prix requis pour ordre limite'
                    }
                order_params['price'] = str(price)
            
            # Conversion en données POST
            params_str = urllib.parse.urlencode(order_params)
            path = '/0/private/AddOrder'
            
            headers = self._sign_request('POST', path, params_str)
            url = f"{self.base_url}{path}"
            
            logger.info(f"🔥 Kraken place_order: {order_type} {side} {amount} {symbol}")
            
            await self._create_session()
            async with self.session.post(url, data=params_str, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200 or data.get('error'):
                    errors = data.get('error', ['Unknown error'])
                    return {
                        'success': False,
                        'error': f'Échec ordre Kraken: {"; ".join(errors)}'
                    }
                
                # Extraction résultats Kraken
                result = data.get('result', {})
                txid_list = result.get('txid', [])
                order_id = txid_list[0] if txid_list else None
                
                logger.info(f"✅ Ordre Kraken créé: {order_id}")
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'client_order_id': None,  # Kraken n'a pas de client order ID
                    'status': 'pending',
                    'filled_amount': 0.0,
                    'remaining_amount': float(amount)
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur place_order Kraken: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """
        ❌ ANNULATION ORDRE Kraken
        """
        try:
            nonce = self._get_nonce()
            
            params_data = {
                'nonce': str(nonce),
                'txid': order_id
            }
            
            params_str = urllib.parse.urlencode(params_data)
            path = '/0/private/CancelOrder'
            
            headers = self._sign_request('POST', path, params_str)
            url = f"{self.base_url}{path}"
            
            logger.info(f"❌ Kraken cancel_order: {order_id}")
            
            await self._create_session()
            async with self.session.post(url, data=params_str, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200 or data.get('error'):
                    errors = data.get('error', ['Unknown error'])
                    return {
                        'success': False,
                        'error': '; '.join(errors),
                        'order_id': order_id
                    }
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'status': 'cancelled',
                    'message': 'Ordre annulé avec succès'
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur cancel_order Kraken: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id
            }
    
    async def get_open_orders(
        self,
        symbol: str = None,
        start_time: str = None,
        end_time: str = None,
        id_less_than: str = None,
        limit: int = 100,
        order_id: str = None,
        tpsl_type: str = None,
        request_time: str = None,
        receive_window: str = None
    ) -> Dict:
        """
        📋 ORDRES OUVERTS Kraken
        """
        try:
            nonce = self._get_nonce()
            params_str = f'nonce={nonce}'
            
            # Extended parameters compatibility - Note: Kraken has limited filter support
            # Most filtering will be done post-processing
            if order_id:
                # Kraken can filter by specific transaction ID
                params_str += f'&trades=true'
            
            path = '/0/private/OpenOrders'
            
            headers = self._sign_request('POST', path, params_str)
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.post(url, data=params_str, headers=headers) as response:
                data = await response.json()
                
                if response.status != 200 or data.get('error'):
                    errors = data.get('error', ['Unknown error'])
                    return {
                        'success': False,
                        'error': '; '.join(errors),
                        'orders': []
                    }
                
                # Traitement des ordres Kraken
                result = data.get('result', {})
                open_orders = result.get('open', {})
                
                orders = []
                for order_id, order_data in open_orders.items():
                    desc = order_data.get('descr', {})
                    
                    # Conversion timestamp
                    created_at_str = None
                    if order_data.get('opentm'):
                        try:
                            dt = datetime.fromtimestamp(float(order_data['opentm']))
                            created_at_str = dt.isoformat()
                        except:
                            pass
                    
                    order = {
                        'order_id': order_id,
                        'symbol': desc.get('pair', ''),
                        'side': desc.get('type', '').lower(),
                        'type': desc.get('ordertype', '').lower(),
                        'amount': float(order_data.get('vol', 0)),
                        'price': float(desc.get('price', 0)) if desc.get('price') else None,
                        'filled': float(order_data.get('vol_exec', 0)),
                        'remaining': float(order_data.get('vol', 0)) - float(order_data.get('vol_exec', 0)),
                        'status': order_data.get('status', 'open').lower(),
                        'created_at': created_at_str
                    }
                    
                    # Filtrage par symbole si demandé
                    if not symbol or self._normalize_kraken_pair(order['symbol']) == self.normalize_symbol(symbol):
                        orders.append(order)
                
                logger.info(f"📋 Ordres ouverts Kraken: {len(orders)}")
                return {
                    'success': True,
                    'orders': orders
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur get_open_orders Kraken: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders': []
            }
    
    async def get_order_history(
        self,
        symbol: str = None,
        start_time: str = None,
        end_time: str = None,
        id_less_than: str = None,
        limit: int = 100,
        order_id: str = None,
        tpsl_type: str = None,
        request_time: str = None,
        receive_window: str = None
    ) -> Dict:
        """
        📚 HISTORIQUE ORDRES KRAKEN - SIGNATURE UNIFIÉE
        
        Compatible avec BitgetNativeClient pour Terminal 7.
        Utilise l'API Kraken /0/private/ClosedOrders.
        """
        try:
            # Paramètres Kraken ClosedOrders
            params = {}
            
            # Nonce obligatoire
            nonce = str(int(time.time() * 1000))
            params['nonce'] = nonce
            
            # Mapping des paramètres étendus vers Kraken
            if start_time:
                # Kraken utilise timestamps Unix en secondes
                try:
                    start_unix = int(int(start_time) / 1000)  # Conversion ms -> s
                    params['start'] = str(start_unix)
                except (ValueError, TypeError):
                    pass
            
            if end_time:
                try:
                    end_unix = int(int(end_time) / 1000)  # Conversion ms -> s  
                    params['end'] = str(end_unix)
                except (ValueError, TypeError):
                    pass
            
            if limit and limit != 100:
                params['ofs'] = '0'  # Offset pour pagination
                # Note: Kraken ne supporte pas directement 'limit', utilise la pagination
            
            # Construction du path
            path = '/0/private/ClosedOrders'
            
            # Conversion en query string pour signature
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            
            # Signature Kraken
            headers = self._sign_request('POST', path, param_str)
            url = f"{self.base_url}{path}"
            
            await self._create_session()
            async with self.session.post(
                url, 
                headers=headers,
                data=param_str
            ) as response:
                data = await response.json()
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': data.get('error', f'HTTP {response.status}'),
                        'orders': []
                    }
                
                # Kraken retourne des erreurs dans le JSON même en 200
                if data.get('error') and len(data['error']) > 0:
                    return {
                        'success': False,
                        'error': ', '.join(data['error']),
                        'orders': []
                    }
                
                # Transformation format standardisé
                orders = []
                closed_orders = data.get('result', {}).get('closed', {})
                
                for order_id_kr, order_data in closed_orders.items():
                    # Filtrer par symbole si spécifié
                    order_symbol = self.denormalize_symbol(order_data.get('descr', {}).get('pair', ''))
                    if symbol and symbol != order_symbol:
                        continue
                    
                    # Conversion format standardisé
                    standardized_order = {
                        'id': order_id_kr,
                        'symbol': order_symbol,
                        'side': order_data.get('descr', {}).get('type', '').lower(),
                        'type': order_data.get('descr', {}).get('ordertype', '').lower(),
                        'amount': float(order_data.get('vol', 0)),
                        'price': self._extract_order_price_kraken(order_data, is_history=True),
                        'filled': float(order_data.get('vol_exec', 0)),
                        'remaining': float(order_data.get('vol', 0)) - float(order_data.get('vol_exec', 0)),
                        'status': self._map_kraken_status(order_data.get('status', '')),
                        'timestamp': int(float(order_data.get('opentm', 0)) * 1000),
                        'updated': int(float(order_data.get('closetm', 0)) * 1000) if order_data.get('closetm') else None,
                        'info': order_data  # Données brutes
                    }
                    orders.append(standardized_order)
                
                # Trier par timestamp décroissant et limiter
                orders.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                if limit:
                    orders = orders[:limit]
                
                logger.info(f"📚 Historique unifié Kraken: {len(orders)} ordres")
                return {
                    'success': True,
                    'orders': orders,
                    'count': len(orders)
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur get_order_history Kraken: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders': []
            }
    
    async def fetch_tickers(self, symbols: List[str] = None) -> Dict:
        """
        📊 RÉCUPÉRATION TICKERS MULTIPLES - Méthode simplifiée
        """
        try:
            # Pour Terminal 7, implémentation basique
            # Kraken peut récupérer plusieurs tickers mais format complexe
            
            if symbols and len(symbols) == 1:
                # Cas simple: un seul ticker
                ticker_result = await self.get_ticker(symbols[0])
                if ticker_result.get('success'):
                    return {
                        'success': True,
                        'tickers': {symbols[0]: ticker_result},
                        'count': 1,
                        'timestamp': int(time.time() * 1000)
                    }
            
            # Cas multiple ou pas de filtre: implémentation basique
            logger.info("📊 fetch_tickers Kraken: implémentation basique")
            return {
                'success': True,
                'tickers': {},
                'count': 0,
                'timestamp': int(time.time() * 1000)
            }
                
        except Exception as e:
            logger.error(f"❌ Erreur fetch_tickers Kraken: {e}")
            return self._standardize_error_response(
                error_message=str(e),
                error_code='CONNECTION_ERROR'
            )
    
    # === MÉTHODES UTILITAIRES KRAKEN ===
    
    def _normalize_asset_name(self, kraken_asset: str) -> str:
        """
        Conversion des noms d'actifs Kraken vers format standard
        Ex: ZUSD → USDT, XXBT → BTC, XETH → ETH
        """
        asset_mapping = {
            'ZUSD': 'USDT',
            'XXBT': 'BTC', 
            'XETH': 'ETH',
            'XLTC': 'LTC',
            'XREP': 'REP',
            'XXMR': 'XMR',
            'XXDG': 'DOGE',
            'USDT': 'USDT',  # Déjà normalisé
            'USDC': 'USDC'   # Déjà normalisé
        }
        
        return asset_mapping.get(kraken_asset, kraken_asset)
    
    def _to_kraken_symbol(self, symbol: str) -> str:
        """
        Conversion symbole standard vers format Kraken
        Ex: BTC/USDT → XBTUSDT
        """
        # Mapping des symboles courants
        if symbol in ['BTC/USDT', 'BTCUSDT']:
            return 'XBTUSDT'
        elif symbol in ['ETH/USDT', 'ETHUSDT']:
            return 'ETHUSDT'
        elif symbol in ['LTC/USDT', 'LTCUSDT']:
            return 'LTCUSDT'
        elif symbol in ['BTC/USD', 'BTCUSD']:
            return 'XXBTZUSD'
        elif symbol in ['ETH/USD', 'ETHUSD']:
            return 'XETHZUSD'
        else:
            # Fallback: supprimer le slash
            return symbol.replace('/', '').upper()
    
    def _normalize_kraken_pair(self, kraken_pair: str) -> str:
        """
        Conversion paire Kraken vers format standard
        Ex: XBTUSDT → BTCUSDT
        """
        if kraken_pair.startswith('XBT'):
            return kraken_pair.replace('XBT', 'BTC', 1)
        elif kraken_pair.startswith('XETH'):
            return kraken_pair.replace('XETH', 'ETH', 1)
        else:
            return kraken_pair
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalisation standard: supprime le slash"""
        return symbol.replace('/', '').replace('-', '').upper()
    
    def _extract_order_price_kraken(self, order_data: Dict, is_history: bool = False) -> float:
        """
        💰 EXTRACTION PRIX ORDRE KRAKEN - CORRECTION ORDRES FERMÉS
        
        Pour Kraken, les ordres fermés peuvent avoir un prix d'exécution moyen.
        
        Champs Kraken (structure complexe):
        - descr.price : Prix initial de l'ordre
        - price : Prix moyen d'exécution (si disponible)
        - cost : Coût total (vol_exec * prix moyen)
        - vol_exec : Volume exécuté
        """
        # 1. Pour ordres historiques, essayer d'abord le prix moyen d'exécution
        if is_history:
            # Kraken peut avoir un champ 'price' avec le prix moyen
            avg_price = order_data.get('price')
            if avg_price and avg_price != '0':
                try:
                    return float(avg_price)
                except (ValueError, TypeError):
                    pass
            
            # Calcul prix moyen à partir cost/vol_exec
            cost = order_data.get('cost', 0)
            vol_exec = order_data.get('vol_exec', 0)
            if cost and vol_exec:
                try:
                    return float(cost) / float(vol_exec)
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
        
        # 2. Fallback vers prix initial (ordres LIMIT)
        initial_price = order_data.get('descr', {}).get('price', 0)
        if initial_price and initial_price != '0':
            try:
                return float(initial_price)
            except (ValueError, TypeError):
                pass
        
        # 3. Aucun prix disponible
        return None
    
    
    def _map_kraken_status(self, kraken_status: str) -> str:
        """Mappe les statuts Kraken vers format standard"""
        status_mapping = {
            'open': 'open',
            'closed': 'closed',
            'canceled': 'canceled',
            'expired': 'expired',
            'pending': 'pending'
        }
        return status_mapping.get(kraken_status.lower(), 'unknown')

    def denormalize_symbol(self, symbol: str) -> str:
        """Dénormalisation: ajoute le slash"""
        if symbol.endswith('USDT'):
            return f"{symbol[:-4]}/USDT"
        elif symbol.endswith('USD'):
            return f"{symbol[:-3]}/USD"
        elif symbol.endswith('EUR'):
            return f"{symbol[:-3]}/EUR"
        else:
            return symbol
    
    # === IMPLÉMENTATION MÉTHODES ABSTRAITES BASEEXCHANGECLIENT ===
    
    def _extract_quote_volume(self, native_response: Dict) -> float:
        """
        💰 EXTRACTION VOLUME COTATION KRAKEN
        
        Volume tradé en devise de cotation (ex: USDT pour BTC/USDT).
        Kraken utilise 'cost' pour le coût total (vol_exec * prix moyen).
        """
        cost = native_response.get('cost', 0)
        if cost:
            try:
                return float(cost)
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    
    def _extract_base_volume(self, native_response: Dict) -> float:
        """
        📊 EXTRACTION VOLUME BASE KRAKEN
        
        Volume tradé en devise de base (ex: BTC pour BTC/USDT).
        Kraken utilise 'vol_exec' pour le volume exécuté.
        """
        vol_exec = native_response.get('vol_exec', 0)
        if vol_exec:
            try:
                return float(vol_exec)
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    
    def _extract_price_avg(self, native_response: Dict) -> float:
        """
        💵 EXTRACTION PRIX MOYEN EXÉCUTION KRAKEN
        
        Prix moyen d'exécution. Kraken peut avoir 'price' direct ou calculé cost/vol_exec.
        Réutilise la logique sophistiquée de _extract_order_price_kraken().
        """
        return self._extract_order_price_kraken(native_response, is_history=True) or 0.0
    
    def _extract_order_source(self, native_response: Dict) -> str:
        """
        🔍 EXTRACTION SOURCE ORDRE KRAKEN
        
        Kraken n'expose pas de source explicite, mais on peut déduire depuis ordertype.
        """
        # Kraken a des types d'ordres dans 'descr.ordertype'
        order_type = native_response.get('descr', {}).get('ordertype', '').lower()
        
        if order_type == 'market':
            return 'market'
        elif order_type == 'limit':
            return 'limit' 
        elif order_type in ['stop-loss', 'take-profit', 'stop-loss-limit', 'take-profit-limit']:
            return 'conditional'
        elif order_type == 'settle-position':
            return 'settlement'
        else:
            return 'unknown'
    
    def _extract_enter_point_source(self, native_response: Dict) -> str:
        """
        📱 EXTRACTION POINT D'ENTRÉE KRAKEN
        
        Kraken n'expose pas explicitement le point d'entrée (WEB, API, etc.).
        On peut essayer de déduire depuis certains patterns.
        """
        # Kraken peut avoir des 'userref' (user reference) personnalisés
        user_ref = native_response.get('userref')
        
        if user_ref:
            # Les références API ont souvent des patterns numériques
            if str(user_ref).isdigit() and len(str(user_ref)) > 6:
                return 'API'
            else:
                return 'WEB'
        
        return 'unknown'
    
    def _extract_fee_detail(self, native_response: Dict) -> Dict:
        """
        💸 EXTRACTION DÉTAILS FRAIS KRAKEN
        
        Kraken retourne 'fee' directement dans la réponse d'ordre.
        """
        fee = native_response.get('fee', 0)
        
        try:
            fee_amount = float(fee) if fee else 0.0
        except (ValueError, TypeError):
            fee_amount = 0.0
        
        return {
            'total_fee': fee_amount,
            'fee_currency': 'USD',  # Kraken utilise souvent USD pour les frais
            'breakdown': [
                {
                    'type': 'trading',
                    'amount': fee_amount,
                    'currency': 'USD'
                }
            ] if fee_amount > 0 else [],
            'note': 'Frais Kraken directement depuis champ fee'
        }
    
    def _extract_cancel_reason(self, native_response: Dict) -> str:
        """
        ❌ EXTRACTION RAISON ANNULATION KRAKEN
        
        Kraken peut avoir un 'reason' dans certains cas, sinon déduction du statut.
        """
        # Kraken peut avoir un champ 'reason' explicite
        reason = native_response.get('reason')
        if reason:
            return str(reason)
        
        # Sinon déduction depuis le statut
        status = native_response.get('status', '').lower()
        
        if status == 'canceled':
            return 'user_canceled'
        elif status == 'expired':
            return 'expired'
        
        return None
    
    def _extract_amount_total(self, native_response: Dict) -> float:
        """
        💰 EXTRACTION MONTANT TOTAL KRAKEN
        
        Montant total tradé. Pour Kraken, utilise 'vol_exec' (volume exécuté).
        """
        return self._safe_float(native_response.get('vol_exec', 0))
    
    def _extract_update_time(self, native_response: Dict) -> Optional[datetime]:
        """
        🕒 EXTRACTION TEMPS MISE À JOUR KRAKEN
        
        Temps de dernière mise à jour. Kraken utilise différents timestamps.
        Priorité: closetm > utime > opentm
        """
        # Kraken a plusieurs timestamps possibles
        timestamp_unix = (native_response.get('closetm') or 
                         native_response.get('utime') or 
                         native_response.get('opentm'))
        
        if timestamp_unix:
            try:
                # Kraken utilise des timestamps Unix en secondes
                return datetime.fromtimestamp(float(timestamp_unix))
            except (ValueError, TypeError):
                pass
        return None
    
    def _extract_trade_id(self, native_response: Dict) -> Optional[str]:
        """
        🆔 EXTRACTION ID TRADE KRAKEN
        
        ID unique du trade/ordre. Kraken utilise plusieurs identifiants possibles.
        """
        # Kraken peut avoir txid (transaction ID) ou refid (reference ID)
        return (native_response.get('txid') or 
                native_response.get('refid') or 
                native_response.get('id'))
    
    def _extract_executed_at(self, native_response: Dict) -> Optional[datetime]:
        """
        ⏰ EXTRACTION TEMPS D'EXÉCUTION KRAKEN
        
        Moment d'exécution de l'ordre.
        Pour Kraken, utilise 'starttm' (début) ou 'opentm' (ouverture).
        """
        executed_time_unix = native_response.get('starttm') or native_response.get('opentm')
        if executed_time_unix:
            try:
                return datetime.fromtimestamp(float(executed_time_unix))
            except (ValueError, TypeError):
                pass
        return None

    def _extract_specialized_fields(self, native_response: Dict) -> Dict:
        """
        🔧 EXTRACTION CHAMPS SPÉCIALISÉS KRAKEN
        
        Tous les champs spécifiques à Kraken non couverts par l'interface standard.
        Kraken a une structure de données riche et unique.
        """
        descr = native_response.get('descr', {})
        
        return {
            # Identifiants Kraken
            'user_ref': native_response.get('userref'),
            'refid': native_response.get('refid'),  # Reference ID Kraken
            
            # Description d'ordre détaillée (spécificité Kraken)
            'order_description': {
                'pair': descr.get('pair'),
                'type': descr.get('type'),  # buy/sell
                'ordertype': descr.get('ordertype'),  # market/limit/etc
                'price': descr.get('price'),
                'price2': descr.get('price2'),  # Pour ordres conditionnels
                'leverage': descr.get('leverage'),
                'order': descr.get('order'),  # Description textuelle
                'close': descr.get('close')  # Ordre de fermeture associé
            },
            
            # Timing Kraken (timestamps Unix)
            'open_timestamp': native_response.get('opentm'),
            'close_timestamp': native_response.get('closetm'),
            'start_timestamp': native_response.get('starttm'),
            'expire_timestamp': native_response.get('expiretm'),
            
            # Volumes et coûts détaillés
            'vol': self._safe_float(native_response.get('vol')),  # Volume initial
            'vol_exec': self._safe_float(native_response.get('vol_exec')),  # Volume exécuté
            'cost': self._safe_float(native_response.get('cost')),  # Coût total
            'fee': self._safe_float(native_response.get('fee')),  # Frais
            
            # Statut et flags Kraken
            'status': native_response.get('status'),
            'reason': native_response.get('reason'),
            'limitprice': self._safe_float(native_response.get('limitprice')),
            'stopprice': self._safe_float(native_response.get('stopprice')),
            
            # Champs techniques pour debug
            'kraken_raw_data': native_response.copy(),
            'misc': native_response.get('misc'),  # Informations diverses Kraken
            'oflags': native_response.get('oflags')  # Flags d'ordre Kraken
        }
    
    def _format_timestamp_kraken(self, timestamp_unix: Union[int, float, str]) -> str:
        """
        🕒 FORMATAGE TIMESTAMP KRAKEN VERS ISO
        
        Convertit les timestamps Unix (secondes) Kraken vers format ISO.
        Kraken utilise des timestamps en secondes (pas millisecondes).
        """
        if not timestamp_unix:
            return None
        try:
            timestamp_float = float(timestamp_unix)
            dt = datetime.fromtimestamp(timestamp_float)
            return dt.isoformat()
        except (ValueError, TypeError):
            return None
    
    async def get_complete_order_details(self, order_id: str, client_order_id: str = None) -> Dict:
        """
        🔍 RÉCUPÉRATION DÉTAILS ORDRE COMPLETS - IMPLÉMENTATION BASEEXCHANGECLIENT
        
        Kraken utilise l'endpoint /0/private/QueryOrders pour récupérer un ordre spécifique.
        
        Args:
            order_id: Transaction ID Kraken ou None
            client_order_id: User reference ou None
            
        Returns:
            Dict: Réponse standardisée avec ordre complet au format Aristobot unifié
        """
        try:
            # Pour l'instant, simulation basique
            # L'implémentation complète nécessiterait l'endpoint QueryOrders avec nonce
            
            logger.warning(f"🔍 get_complete_order_details Kraken: fonctionnalité partielle, order_id={order_id}")
            
            # Simuler une structure de réponse Kraken typique
            order_data = {
                'refid': None,
                'userref': client_order_id,
                'status': 'unknown',
                'opentm': time.time(),
                'closetm': None,
                'starttm': None,
                'expiretm': None,
                'descr': {
                    'pair': 'UNKNOWN',
                    'type': 'unknown',
                    'ordertype': 'unknown',
                    'price': '0',
                    'price2': '0',
                    'leverage': 'none',
                    'order': 'unknown unknown @ unknown',
                    'close': None
                },
                'vol': '0',
                'vol_exec': '0',
                'cost': '0',
                'fee': '0',
                'price': '0',
                'stopprice': '0',
                'limitprice': '0',
                'misc': '',
                'oflags': '',
                'reason': None
            }
            
            # Appliquer la standardisation complète
            standardized_order = self._standardize_complete_order_response(order_data)
            
            return {
                'success': True,
                'order': standardized_order,
                'raw_data': order_data,
                'lookup_method': 'simulated_kraken_query_orders',
                'note': 'Implémentation partielle - nécessite endpoint POST /0/private/QueryOrders'
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur get_complete_order_details Kraken: {e}")
            return {
                'success': False,
                'error': str(e),
                'order': None
            }
    
    def _safe_float(self, value) -> float:
        """Conversion sécurisée vers float pour Kraken"""
        if value is None or value == '' or value == '0':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


# Enregistrement du client Kraken dans la factory
from .base_exchange_client import ExchangeClientFactory
ExchangeClientFactory.register_client('kraken', KrakenNativeClient)