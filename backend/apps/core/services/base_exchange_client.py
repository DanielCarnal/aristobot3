# -*- coding: utf-8 -*-
"""
BASE EXCHANGE CLIENT - Architecture native pour remplacer CCXT

🎯 OBJECTIF: Interface unifiée pour tous les exchanges natifs
Remplace progressivement la dépendance CCXT avec des clients natifs optimisés

📋 ARCHITECTURE:
- BaseExchangeClient: Interface abstraite commune
- ExchangeClientFactory: Factory pattern pour créer les clients
- Gestion uniforme des erreurs, rate limits, authentification
- Interface 100% compatible avec CCXTClient existant

🔧 EXCHANGES SUPPORTÉS:
- BitgetNativeClient: Implémentation native Bitget (priorité 1)  
- Extensible: Binance, Kraken, etc. (futur)

💡 AVANTAGES NATIVE vs CCXT:
- Performance: ~3x plus rapide (pas d'abstraction CCXT)
- Fonctionnalités: Accès complet aux API spécialisées
- Fiabilité: Contrôle total sur rate limiting et retry logic
- Maintenance: Indépendance des bugs/limitations CCXT
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import base64
import json
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Types d'ordres standardisés"""
    MARKET = "market"
    LIMIT = "limit" 
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    OCO = "oco"  # One-Cancels-Other


class OrderSide(Enum):
    """Côtés d'ordre standardisés"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Status d'ordre standardisés"""
    PENDING = "pending"
    OPEN = "open" 
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ExchangeError(Exception):
    """Exception de base pour erreurs exchange"""
    def __init__(self, message: str, code: str = None, exchange: str = None):
        self.message = message
        self.code = code
        self.exchange = exchange
        super().__init__(f"[{exchange or 'EXCHANGE'}] {message}")


class RateLimitError(ExchangeError):
    """Exception pour dépassement rate limit"""
    pass


class InsufficientFundsError(ExchangeError):  
    """Exception pour fonds insuffisants"""
    pass


class OrderError(ExchangeError):
    """Exception pour erreurs d'ordre"""
    pass


class BaseExchangeClient(ABC):
    """
    🏗️ CLIENT EXCHANGE ABSTRAIT - INTERFACE COMMUNE
    
    Définit l'interface standardisée que tous les clients natifs doivent implémenter.
    
    🎯 MÉTHODES OBLIGATOIRES:
    - Authentification et connexion
    - Gestion des ordres (place, cancel, modify, list)
    - Récupération des balances et tickers
    - Gestion des symboles et contraintes de marché
    
    🔧 GESTION STANDARDISÉE:
    - Rate limiting automatique
    - Retry logic avec exponential backoff  
    - Conversion uniforme des réponses
    - Logging et debugging structuré
    """
    
    def __init__(self, 
                 api_key: str, 
                 api_secret: str, 
                 api_passphrase: str = None,
                 is_testnet: bool = False,
                 timeout: int = 60):
        """
        Initialisation du client exchange
        
        Args:
            api_key: Clé API de l'exchange
            api_secret: Secret API de l'exchange  
            api_passphrase: Passphrase (requis pour certains exchanges comme Bitget)
            is_testnet: True si utilisation de l'environnement de test
            timeout: Timeout en secondes pour les requêtes HTTP
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.is_testnet = is_testnet
        self.timeout = timeout
        
        # Session HTTP réutilisable
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self._request_timestamps = []  # Historique des timestamps de requêtes
        self._rate_limit_window = 1  # Fenêtre de 1 seconde
        self._max_requests_per_window = 10  # Par défaut, sera surchargé
        
        # Retry configuration
        self._max_retries = 3
        self._retry_delay = 1  # Délai initial en secondes
        
        # Cache pour optimiser les performances
        self._markets_cache: Optional[Dict] = None
        self._markets_cache_ttl = 300  # 5 minutes
        self._markets_cache_timestamp = 0
    
    @property
    @abstractmethod
    def exchange_name(self) -> str:
        """Nom de l'exchange (ex: 'bitget', 'binance')"""
        pass
    
    @property  
    @abstractmethod
    def base_url(self) -> str:
        """URL de base de l'API"""
        pass
    
    async def __aenter__(self):
        """Context manager - Ouverture session"""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager - Fermeture session"""
        await self._close_session()
    
    async def _create_session(self):
        """Création de la session HTTP avec configuration optimisée"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': f'Aristobot3-{self.exchange_name.title()}Client/1.0'}
            )
            logger.info(f"🔗 Session HTTP créée pour {self.exchange_name}")
    
    async def _close_session(self):
        """Fermeture propre de la session HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info(f"🔌 Session HTTP fermée pour {self.exchange_name}")
    
    @abstractmethod
    def _sign_request(self, method: str, path: str, params: str = '') -> Dict[str, str]:
        """
        Signature cryptographique de la requête (spécifique à chaque exchange)
        
        Args:
            method: Méthode HTTP (GET, POST)
            path: Chemin de l'endpoint  
            params: Paramètres de la requête (JSON string pour POST)
            
        Returns:
            Dict des headers d'authentification
        """
        pass
    
    async def _rate_limit_check(self):
        """Vérification et application du rate limiting"""
        now = time.time()
        
        # Nettoyer les anciens timestamps  
        self._request_timestamps = [
            ts for ts in self._request_timestamps 
            if now - ts < self._rate_limit_window
        ]
        
        # Vérifier la limite
        if len(self._request_timestamps) >= self._max_requests_per_window:
            wait_time = self._rate_limit_window - (now - self._request_timestamps[0])
            if wait_time > 0:
                logger.warning(f"⏳ Rate limit {self.exchange_name}: attente {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        # Enregistrer cette requête
        self._request_timestamps.append(now)
    
    async def _make_request(self, 
                           method: str, 
                           path: str, 
                           params: Dict = None, 
                           retries: int = None) -> Dict:
        """
        Exécution d'une requête HTTP avec retry logic et gestion d'erreurs
        
        Args:
            method: Méthode HTTP
            path: Chemin de l'endpoint
            params: Paramètres de la requête
            retries: Nombre de tentatives (None = utilise self._max_retries)
            
        Returns:
            Réponse JSON de l'API
            
        Raises:
            ExchangeError: En cas d'erreur API
            RateLimitError: En cas de dépassement rate limit
        """
        if retries is None:
            retries = self._max_retries
        
        params = params or {}
        await self._create_session()  # S'assurer que la session existe
        await self._rate_limit_check()
        
        # Construction de l'URL
        url = f"{self.base_url}{path}"
        
        # Préparation des paramètres
        if method.upper() == 'GET' and params:
            # Paramètres dans l'URL pour GET
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{query_string}"
            params_str = query_string
            data = None
        else:
            # Paramètres dans le body pour POST
            params_str = json.dumps(params) if params else ''
            data = params_str
        
        # Signature de la requête
        headers = self._sign_request(method, path, params_str)
        
        for attempt in range(retries + 1):
            try:
                start_time = time.time()
                
                async with self.session.request(
                    method.upper(),
                    url, 
                    headers=headers,
                    data=data if method.upper() == 'POST' else None
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    response_data = await response.json()
                    
                    # Logging de la requête
                    logger.debug(
                        f"📡 {self.exchange_name} {method.upper()} {path} "
                        f"-> {response.status} ({response_time:.0f}ms)"
                    )
                    
                    # Gestion des erreurs spécifiques à l'exchange
                    await self._handle_response_errors(response_data, response.status)
                    
                    return response_data
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(
                    f"🔄 {self.exchange_name} tentative {attempt + 1}/{retries + 1}: {e}"
                )
                
                if attempt < retries:
                    wait_time = self._retry_delay * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(wait_time)
                else:
                    raise ExchangeError(f"Échec requête après {retries + 1} tentatives", exchange=self.exchange_name)
    
    @abstractmethod 
    async def _handle_response_errors(self, response_data: Dict, status_code: int):
        """
        Gestion des erreurs spécifiques à l'exchange (à implémenter par chaque client)
        
        Args:
            response_data: Réponse JSON de l'API
            status_code: Code de statut HTTP
            
        Raises:
            ExchangeError: Pour erreurs génériques
            RateLimitError: Pour rate limit dépassé
            InsufficientFundsError: Pour fonds insuffisants  
            OrderError: Pour erreurs d'ordre
        """
        pass
    
    # === MÉTHODES DE NORMALISATION FORMAT ARISTOBOT UNIFIÉ ===
    
    def _standardize_ticker_response(self, native_response: Dict) -> Dict:
        """
        🎯 NORMALISE TICKER vers FORMAT ARISTOBOT UNIFIÉ
        
        Convertit la réponse native de l'exchange vers le format standardisé Aristobot.
        Doit être adapté dans chaque client selon le format natif de l'exchange.
        """
        # Format de base - à surcharger dans chaque client
        return {
            'success': True,
            'symbol': native_response.get('symbol'),
            'last': float(native_response.get('last', 0)),
            'bid': float(native_response.get('bid', 0)),
            'ask': float(native_response.get('ask', 0)),
            'volume_24h': float(native_response.get('volume_24h', 0)),
            'change_24h': float(native_response.get('change_24h', 0)),
            'high_24h': float(native_response.get('high_24h', 0)),
            'low_24h': float(native_response.get('low_24h', 0)),
            'timestamp': native_response.get('timestamp', int(time.time() * 1000))
        }
    
    def _standardize_balance_response(self, native_response: Dict) -> Dict:
        """
        🎯 NORMALISE BALANCE vers FORMAT ARISTOBOT UNIFIÉ
        """
        # Format de base - à surcharger dans chaque client
        return {
            'success': True,
            'free': native_response.get('free', {}),
            'used': native_response.get('used', {}),
            'total': native_response.get('total', {}),
            'timestamp': native_response.get('timestamp', int(time.time() * 1000))
        }
    
    def _standardize_order_response(self, native_response: Dict) -> Dict:
        """
        🎯 NORMALISE ORDER vers FORMAT ARISTOBOT UNIFIÉ
        """
        # Format de base - à surcharger dans chaque client
        return {
            'success': True,
            'id': native_response.get('id'),
            'client_order_id': native_response.get('client_order_id'),
            'symbol': native_response.get('symbol'),
            'type': native_response.get('type', 'market'),
            'side': native_response.get('side'),
            'amount': float(native_response.get('amount', 0)),
            'filled': float(native_response.get('filled', 0)),
            'remaining': float(native_response.get('remaining', 0)),
            'price': float(native_response.get('price', 0)) if native_response.get('price') else None,
            'average': float(native_response.get('average', 0)) if native_response.get('average') else None,
            'status': self._normalize_order_status(native_response.get('status')),
            'fee': {
                'cost': float(native_response.get('fee', {}).get('cost', 0)),
                'currency': native_response.get('fee', {}).get('currency', 'USDT')
            },
            'timestamp': native_response.get('timestamp', int(time.time() * 1000)),
            'updated': native_response.get('updated', int(time.time() * 1000))
        }
    
    def _standardize_orders_response(self, native_orders: List[Dict]) -> Dict:
        """
        🎯 NORMALISE ORDERS LIST vers FORMAT ARISTOBOT UNIFIÉ
        """
        normalized_orders = []
        for order in native_orders:
            normalized_orders.append(self._standardize_order_response(order))
        
        return {
            'success': True,
            'orders': normalized_orders,
            'total': len(normalized_orders),
            'timestamp': int(time.time() * 1000)
        }
    
    def _standardize_markets_response(self, native_markets: Dict) -> Dict:
        """
        🎯 NORMALISE MARKETS vers FORMAT ARISTOBOT UNIFIÉ
        """
        # Format de base - à surcharger dans chaque client
        return {
            'success': True,
            'markets': native_markets,
            'count': len(native_markets),
            'timestamp': int(time.time() * 1000)
        }
    
    def _standardize_test_connection_response(self, native_response: Dict) -> Dict:
        """
        🎯 NORMALISE TEST_CONNECTION vers FORMAT ARISTOBOT UNIFIÉ
        """
        return {
            'success': True,
            'connected': native_response.get('connected', False),
            'exchange': self.exchange_name,
            'user_info': native_response.get('user_info', {}),
            'balance_sample': native_response.get('balance_sample', {}),
            'timestamp': int(time.time() * 1000)
        }
    
    def _standardize_error_response(self, error_message: str, error_code: str = None, 
                                   exchange_error: Dict = None) -> Dict:
        """
        🎯 NORMALISE ERROR vers FORMAT ARISTOBOT UNIFIÉ
        """
        return {
            'success': False,
            'error': error_message,
            'error_code': error_code or 'UNKNOWN_ERROR',
            'exchange_error': exchange_error or {},
            'timestamp': int(time.time() * 1000)
        }
    
    def _normalize_order_status(self, native_status: str) -> str:
        """
        🎯 NORMALISE ORDER STATUS vers format standardisé
        
        Convertit le status natif de l'exchange vers les status Aristobot.
        À surcharger dans chaque client selon la terminologie de l'exchange.
        """
        # Mapping de base - à surcharger dans chaque client
        status_mapping = {
            'new': 'open',
            'open': 'open',
            'filled': 'filled',
            'cancelled': 'cancelled',
            'canceled': 'cancelled',
            'rejected': 'failed',
            'expired': 'cancelled',
            'partial': 'partially_filled',
            'partially_filled': 'partially_filled'
        }
        
        return status_mapping.get(native_status.lower() if native_status else '', 'open')
    
    # === MÉTHODES D'INTERFACE OBLIGATOIRES ===
    
    @abstractmethod
    async def test_connection(self) -> Dict:
        """
        Test de connexion à l'exchange
        
        Returns:
            {'connected': bool, 'balance_items': int, 'error': str}
        """
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict:
        """
        Récupération des balances du compte
        
        Returns:
            {
                'success': bool,
                'balances': {
                    'USDT': {'available': float, 'frozen': float, 'total': float},
                    'BTC': {'available': float, 'frozen': float, 'total': float},
                    ...
                }
            }
        """
        pass
    
    @abstractmethod
    async def get_markets(self) -> Dict:
        """
        Récupération des marchés disponibles avec contraintes
        
        Returns:
            {
                'success': bool,
                'markets': {
                    'BTCUSDT': {
                        'symbol': str,
                        'base': str, 'quote': str,
                        'min_amount': float, 'max_amount': float,
                        'price_precision': int, 'quantity_precision': int,
                        'min_trade_usdt': float,
                        'active': bool
                    },
                    ...
                }
            }
        """
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """
        Prix actuel d'un symbole
        
        Args:
            symbol: Symbole (format unifié 'BTC/USDT')
            
        Returns:
            {
                'success': bool,
                'symbol': str,
                'price': float,
                'bid': float, 'ask': float,
                'volume_24h': float,
                'change_24h': float
            }
        """
        pass
    
    @abstractmethod 
    async def place_order(self, 
                         symbol: str, 
                         side: str, 
                         amount: float,
                         order_type: str = 'market',
                         price: float = None,
                         **kwargs) -> Dict:
        """
        Passage d'ordre unifié
        
        Args:
            symbol: Symbole au format 'BTC/USDT'
            side: 'buy' ou 'sell'
            amount: Quantité (base currency pour limit/sell, quote pour market buy)
            order_type: 'market', 'limit', 'stop_loss', 'take_profit'
            price: Prix (obligatoire pour limit orders)
            **kwargs: Paramètres avancés (stop_loss_price, take_profit_price, etc.)
            
        Returns:
            {
                'success': bool,
                'order_id': str,
                'client_order_id': str,
                'status': str,
                'filled_amount': float,
                'remaining_amount': float
            }
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """
        Annulation d'ordre
        
        Args:
            symbol: Symbole de l'ordre
            order_id: ID de l'ordre à annuler
            
        Returns:
            {
                'success': bool,
                'order_id': str,
                'status': str,
                'message': str
            }
        """
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: str = None) -> Dict:
        """
        Récupération des ordres ouverts
        
        Args:
            symbol: Filtre par symbole (None = tous)
            
        Returns:
            {
                'success': bool,
                'orders': [
                    {
                        'order_id': str, 'symbol': str, 'side': str,
                        'type': str, 'amount': float, 'price': float,
                        'filled': float, 'remaining': float, 'status': str,
                        'created_at': datetime
                    },
                    ...
                ]
            }
        """
        pass
    
    @abstractmethod
    async def get_order_history(self, symbol: str = None, limit: int = 100) -> Dict:
        """
        Historique des ordres (fermés/annulés)
        
        Args:
            symbol: Filtre par symbole
            limit: Nombre maximum d'ordres
            
        Returns:
            Même format que get_open_orders
        """
        pass
    
    # === MÉTHODES UTILITAIRES ===
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalise un symbole au format exchange
        
        Args:
            symbol: Symbole au format 'BTC/USDT' ou 'BTCUSDT'
            
        Returns:
            Symbole au format de l'exchange
        """
        return symbol.replace('/', '')  # Par défaut, supprimer le slash
    
    def format_amount(self, amount: Union[float, str, Decimal], precision: int) -> str:
        """
        Formatage d'un montant avec la précision requise
        
        Args:
            amount: Montant à formater
            precision: Nombre de décimales
            
        Returns:
            Montant formaté en string
        """
        if isinstance(amount, str):
            amount = float(amount)
        return f"{amount:.{precision}f}".rstrip('0').rstrip('.')
    
    def format_price(self, price: Union[float, str, Decimal], precision: int) -> str:
        """
        Formatage d'un prix avec la précision requise
        
        Args:
            price: Prix à formater  
            precision: Nombre de décimales
            
        Returns:
            Prix formaté en string
        """
        return self.format_amount(price, precision)
    
    async def get_market_constraints(self, symbol: str) -> Optional[Dict]:
        """
        Récupération des contraintes de marché pour un symbole
        
        Args:
            symbol: Symbole au format 'BTC/USDT'
            
        Returns:
            Contraintes du marché ou None si non trouvé
        """
        markets_data = await self.get_markets()
        if markets_data['success']:
            normalized_symbol = self.normalize_symbol(symbol)
            return markets_data['markets'].get(normalized_symbol)
        return None


class ExchangeClientFactory:
    """
    🏭 FACTORY POUR CRÉER LES CLIENTS EXCHANGE
    
    Centralise la création des différents clients natifs selon l'exchange demandé.
    Permet l'extension future avec de nouveaux exchanges.
    """
    
    _clients = {}  # Cache des classes de clients
    
    @classmethod
    def register_client(cls, exchange_name: str, client_class):
        """
        Enregistrement d'un nouveau client exchange
        
        Args:
            exchange_name: Nom de l'exchange ('bitget', 'binance', etc.)
            client_class: Classe du client héritant de BaseExchangeClient
        """
        cls._clients[exchange_name.lower()] = client_class
        logger.info(f"📝 Client {exchange_name} enregistré")
    
    @classmethod
    def create_client(cls, 
                     exchange_name: str,
                     api_key: str,
                     api_secret: str, 
                     api_passphrase: str = None,
                     is_testnet: bool = False,
                     **kwargs) -> BaseExchangeClient:
        """
        Création d'un client exchange
        
        Args:
            exchange_name: Nom de l'exchange
            api_key: Clé API
            api_secret: Secret API
            api_passphrase: Passphrase (si requis)
            is_testnet: Mode testnet
            **kwargs: Paramètres additionnels
            
        Returns:
            Instance du client exchange
            
        Raises:
            ValueError: Si l'exchange n'est pas supporté
        """
        exchange_key = exchange_name.lower()
        
        if exchange_key not in cls._clients:
            available = ', '.join(cls._clients.keys())
            raise ValueError(f"Exchange '{exchange_name}' non supporté. Disponibles: {available}")
        
        client_class = cls._clients[exchange_key]
        return client_class(
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
            is_testnet=is_testnet,
            **kwargs
        )
    
    @classmethod
    def list_supported_exchanges(cls) -> List[str]:
        """
        Liste des exchanges supportés
        
        Returns:
            Liste des noms d'exchanges supportés
        """
        return list(cls._clients.keys())