# -*- coding: utf-8 -*-
"""
EXCHANGE CLIENT - Interface unifiée pour les opérations exchange

🎯 OBJECTIF: Interface unique pour toutes les interactions avec les exchanges
Utilise les clients natifs (BitgetNativeClient) via NativeExchangeManager

🔧 ARCHITECTURE:
- ExchangeClient: Interface client pour les apps Django
- NativeExchangeManager: Pool de connexions natives (Terminal 5)
- Communication Redis: exchange_requests/exchange_responses
- Tous les timeouts et retry logic gérés

✅ UTILISÉ PAR:
- TradingService (apps/trading_manual/services.py)
- Trading Engine (apps/trading_engine)
- Backtest (apps/backtest)
- Webhooks (apps/webhooks)
- User Account APIs (apps/accounts)

🚀 UTILISATION:
  from apps.core.services.exchange_client import ExchangeClient
  client = ExchangeClient(user_id=request.user.id)
  balance = await client.get_balance(broker_id)
"""

import asyncio
import uuid
import json
import logging
from typing import Any, Dict, Optional, List

from .redis_fallback import get_redis_client

logger = logging.getLogger(__name__)

# Instance globale (préférer ExchangeClient(user_id=...) pour sécurité multi-tenant)
_global_exchange_client = None


class ExchangeClient:
    """
    🔄 CLIENT EXCHANGE UNIFIÉ

    Interface unique pour toutes les opérations exchange.
    Utilise NativeExchangeManager (Terminal 5) pour les performances natives.

    🎯 MÉTHODES DISPONIBLES:
    - get_balance(broker_id)
    - place_order(broker_id, symbol, side, amount, order_type, price, **kwargs)
    - place_market_order(broker_id, symbol, side, amount)
    - place_limit_order(broker_id, symbol, side, amount, price)
    - cancel_order(broker_id, order_id, symbol)
    - edit_order(broker_id, order_id, symbol, **kwargs)
    - fetch_open_orders(broker_id, symbol, since, limit)
    - fetch_closed_orders(broker_id, symbol, since, limit)
    - get_markets(broker_id)
    - get_ticker(broker_id, symbol)
    - get_tickers(broker_id, symbols)
    - preload_all_brokers()

    🛡️ ORDRES AVANCÉS:
    - place_stop_loss_order()
    - place_take_profit_order()
    """
    
    def __init__(self, user_id: int = None):
        self.channel_layer = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        # Configuration Redis
        self._redis_client = None
        
        # 🔒 NOUVEAU: Stockage user_id pour sécurité multi-tenant
        self._user_id = user_id
        
        # Définir cette instance comme globale pour compatibilité
        global _global_exchange_client
        _global_exchange_client = self
    
    async def _get_redis_client(self):
        """Récupération client Redis avec cache"""
        if not self._redis_client:
            self._redis_client = await get_redis_client()
        return self._redis_client
    
    async def _send_request(self, action: str, params: Dict, user_id: int = None) -> Any:
        """
        📤 ENVOI REQUÊTE - Via Terminal 5 + SÉCURITÉ MULTI-TENANT
        
        NOUVEAUTÉ: Ajout user_id obligatoire pour sécurité Terminal 5.
        Empêche accès non autorisé aux brokers d'autres utilisateurs.
        """
        request_id = str(uuid.uuid4())
        
        # SÉCURITÉ: Utiliser user_id du constructeur ou passé explicitement
        if not user_id:
            user_id = self._user_id
        
        # SÉCURITÉ: user_id obligatoire pour éviter faille multi-tenant
        if not user_id and 'broker_id' in params:
            raise ValueError(f"SÉCURITÉ: user_id obligatoire pour action {action} avec broker_id")
        
        # Log spécial pour place_order (compatibilité)
        if action == 'place_order':
            logger.info(f"🔥 ExchangeClient._send_request PLACE_ORDER START: {action} - {request_id[:8]}... - {params}")
        
        # Construction de la requête avec user_id pour sécurité
        request = {
            'request_id': request_id,
            'action': action,
            'params': params,
            'user_id': user_id,  # 🔒 NOUVEAU: Sécurité multi-tenant
            'trace_id': getattr(self, 'trace_id', None),  # Propagation trace causale vers T5
            'timestamp': asyncio.get_event_loop().time()
        }
        
        try:
            redis_client = await self._get_redis_client()
            
            # Test connexion
            await redis_client.ping()
            
            # Envoi de la requête via Redis (standard Redis)
            await redis_client.rpush('exchange_requests', json.dumps(request))
            logger.info(f"📤 Requête envoyée: {action} - {request_id[:8]}...")
            
            # Attendre la réponse avec polling (méthode standard Redis)
            response_key = f"exchange_response_{request_id}"
            
            # Timeouts spécifiques selon l'action (standard Redis)
            timeout_iterations = 600  # 60s par défaut
            
            if action in ['get_balance', 'get_markets']:
                timeout_iterations = 900  # 90s pour les opérations plus longues
            elif action in ['place_order', 'cancel_order', 'edit_order']:
                timeout_iterations = 1200  # 120s pour les ordres
            
            # Polling de la réponse (logique standard Redis)
            for i in range(timeout_iterations):
                response_data = await redis_client.get(response_key)
                if response_data:
                    response = json.loads(response_data)
                    await redis_client.delete(response_key)  # Nettoyer
                    
                    logger.info(f"📥 Réponse reçue: {action} - {request_id[:8]}... après {i*0.1:.1f}s")
                    
                    if response['success']:
                        # 🔧 FIX: Pour create_and_execute_trade, retourner la réponse complète
                        if action == 'create_and_execute_trade':
                            return response  # Réponse complète avec 'success', 'data', 'trade_id'
                        else:
                            return response['data']  # Comportement standard pour autres actions
                    else:
                        raise Exception(response['error'])
                
                await asyncio.sleep(0.1)
            
            # Timeout (gestion standard Redis)
            timeout_seconds = timeout_iterations * 0.1
            logger.error(f"⏰ Timeout ExchangeClient: {action} - {request_id[:8]}... après {timeout_seconds:.0f}s")
            raise Exception(f"Timeout ExchangeClient request {action}")
            
        except Exception as e:
            if "Timeout" not in str(e) and "ping" not in str(e).lower():
                logger.error(f"❌ Erreur Redis ExchangeClient {action}: {e}")
            raise
        finally:
            # Nettoyer
            try:
                if redis_client:
                    await redis_client.close()
            except:
                pass
    
    # === MÉTHODES PRINCIPALES ===
    
    async def get_balance(self, broker_id: int) -> Dict:
        """💰 Récupère le solde d'un broker - Via Terminal 5"""
        return await self._send_request('get_balance', {'broker_id': broker_id})
    
    async def get_candles(self, broker_id: int, symbol: str, 
                         timeframe: str, limit: int = 100) -> list:
        """📊 Récupère des bougies OHLCV - Via Terminal 5"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'limit': limit
        }
        return await self._send_request('get_candles', params)
    
    async def place_order(self, broker_id: int, symbol: str, side: str, 
                         amount: float, order_type: str = 'market', 
                         price: float = None, **advanced_params) -> Dict:
        """🔥 MÉTHODE UNIFIÉE - Via Terminal 5.place_order()"""
        logger.info(f"🔥 ExchangeClient.place_order UNIFIÉ: {order_type} {side} {amount} {symbol}")
        
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'type': order_type,
            'price': price,
        }
        
        # Ajouter les paramètres avancés (standard Redis)
        params.update(advanced_params)
        
        logger.info(f"🔥 ExchangeClient: Envoi place_order UNIFIÉ avec params: {params}")
        return await self._send_request('place_order', params)
    
    async def place_market_order(self, broker_id: int, symbol: str, 
                                side: str, amount: float) -> Dict:
        """📈 Ordre au marché - WRAPPER via Terminal 5"""
        return await self.place_order(broker_id, symbol, side, amount, 'market')
    
    async def place_limit_order(self, broker_id: int, symbol: str, 
                               side: str, amount: float, price: float) -> Dict:
        """📊 Ordre limite - WRAPPER via Terminal 5"""
        return await self.place_order(broker_id, symbol, side, amount, 'limit', price)
    
    async def get_markets(self, broker_id: int) -> Dict:
        """🏪 Récupère les marchés disponibles - Via Terminal 5"""
        return await self._send_request('get_markets', {'broker_id': broker_id})
    
    async def get_ticker(self, broker_id: int, symbol: str) -> Dict:
        """📈 Récupère le ticker d'un symbole - Via Terminal 5"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol
        }
        return await self._send_request('get_ticker', params)
    
    async def preload_all_brokers(self) -> tuple:
        """⚡ Préchargement de tous les brokers - Via Terminal 5"""
        return await self._send_request('preload_brokers', {})
    
    async def fetch_open_orders(self, broker_id: int, symbol: str = None, 
                               since: int = None, limit: int = None,
                               start_time: str = None, end_time: str = None, 
                               id_less_than: str = None, order_id: str = None,
                               tpsl_type: str = None, request_time: str = None,
                               receive_window: str = None) -> list:
        """📋 Récupère les ordres ouverts - Via Terminal 5 + PARAMÈTRES ÉTENDUS"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'since': since,
            'limit': limit,
            # NOUVEAUX PARAMÈTRES ÉTENDUS TERMINAL 5
            'start_time': start_time,
            'end_time': end_time,
            'id_less_than': id_less_than,
            'order_id': order_id,
            'tpsl_type': tpsl_type,
            'request_time': request_time,
            'receive_window': receive_window
        }
        # Supprimer les paramètres None (standard Redis)
        params = {k: v for k, v in params.items() if v is not None}
        return await self._send_request('fetch_open_orders', params)
    
    async def fetch_closed_orders(self, broker_id: int, symbol: str = None, 
                                 since: int = None, limit: int = None,
                                 start_time: str = None, end_time: str = None, 
                                 id_less_than: str = None, order_id: str = None,
                                 tpsl_type: str = None, request_time: str = None,
                                 receive_window: str = None) -> list:
        """📚 Récupère les ordres fermés - Via Terminal 5 + PARAMÈTRES ÉTENDUS"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'since': since,
            'limit': limit,
            # NOUVEAUX PARAMÈTRES ÉTENDUS TERMINAL 5
            'start_time': start_time,
            'end_time': end_time,
            'id_less_than': id_less_than,
            'order_id': order_id,
            'tpsl_type': tpsl_type,
            'request_time': request_time,
            'receive_window': receive_window
        }
        # Supprimer les paramètres None (standard Redis)
        params = {k: v for k, v in params.items() if v is not None}
        return await self._send_request('fetch_closed_orders', params)
    
    async def cancel_order(self, broker_id: int, order_id: str, symbol: str = None) -> Dict:
        """❌ Annule un ordre - Via Terminal 5"""
        params = {
            'broker_id': broker_id,
            'order_id': order_id,
            'symbol': symbol
        }
        # Supprimer les paramètres None (standard Redis)
        params = {k: v for k, v in params.items() if v is not None}
        return await self._send_request('cancel_order', params)
    
    async def edit_order(self, broker_id: int, order_id: str, symbol: str,
                        order_type: str = 'limit', side: str = None, 
                        amount: float = None, price: float = None) -> Dict:
        """🔧 Modifie un ordre - Via Terminal 5"""
        params = {
            'broker_id': broker_id,
            'order_id': order_id,
            'symbol': symbol,
            'type': order_type,
            'side': side,
            'amount': amount,
            'price': price
        }
        # Supprimer les paramètres None (standard Redis)
        params = {k: v for k, v in params.items() if v is not None}
        return await self._send_request('edit_order', params)
    
    async def get_tickers(self, broker_id: int, symbols: list[str]) -> Dict:
        """📊 Tickers multiples - Via Terminal 5"""
        logger.info(f"🔄 ExchangeClient.get_tickers appelé: broker {broker_id}, symbols {symbols}")
        params = {
            'broker_id': broker_id,
            'symbols': symbols
        }
        return await self._send_request('fetch_tickers', params)
    
    # === NOUVELLES MÉTHODES USER ACCOUNT ===
    
    async def test_connection(self, broker_id: int) -> Dict:
        """
        🔌 TEST CONNEXION - NOUVEAU POUR USER ACCOUNT
        
        Teste la connexion API keys d'un broker via clients natifs.
        Utilisé par User Account pour valider les credentials.
        """
        logger.info(f"🔌 ExchangeClient.test_connection: broker {broker_id}")
        params = {'broker_id': broker_id}
        return await self._send_request('test_connection', params)
    
    async def load_markets(self, broker_id: int) -> Dict:
        """
        📊 CHARGEMENT MARCHÉS - NOUVEAU POUR USER ACCOUNT
        
        Lance le chargement des marchés en arrière-plan pour un broker.
        Utilisé par User Account bouton "[MAJ Paires]".
        """
        logger.info(f"📊 ExchangeClient.load_markets: broker {broker_id}")
        params = {'broker_id': broker_id}
        return await self._send_request('load_markets', params)
    
    # === WRAPPERS RÉTROCOMPATIBILITÉ (standard Redis) ===
    
    async def place_stop_loss_order(self, broker_id: int, symbol: str, 
                                   side: str, amount: float, stop_loss_price: float) -> Dict:
        """
        🛡️ WRAPPER RÉTROCOMPATIBILITÉ - Ordre Stop Loss
        Conservé pour Trading Engine, Webhooks, Backtest modules
        """
        return await self.place_order(
            broker_id, symbol, side, amount, 'stop_loss',
            stop_loss_price=stop_loss_price
        )
    
    async def place_take_profit_order(self, broker_id: int, symbol: str, 
                                     side: str, amount: float, take_profit_price: float) -> Dict:
        """
        🎯 WRAPPER RÉTROCOMPATIBILITÉ - Ordre Take Profit  
        Conservé pour Trading Engine, Webhooks, Backtest modules
        """
        return await self.place_order(
            broker_id, symbol, side, amount, 'take_profit',
            take_profit_price=take_profit_price
        )
    
    # === MÉTHODES UTILITAIRES ===
    
    async def handle_response(self, response: Dict):
        """
        🔄 Traite une réponse - STUB

        Méthode placeholder - NativeExchangeManager gère les réponses directement.
        """
        pass


def get_global_exchange_client(user_id: int = None):
    """
    🌍 RÉCUPÈRE L'INSTANCE GLOBALE

    ATTENTION: Préférer l'instanciation directe avec user_id pour sécurité multi-tenant:

    ❌ PAS SÉCURISÉ: get_global_exchange_client()
    ✅ SÉCURISÉ: ExchangeClient(user_id=request.user.id)
    """
    global _global_exchange_client
    
    # Réutiliser instance existante SI user_id identique
    if (_global_exchange_client is not None and 
        hasattr(_global_exchange_client, '_user_id') and 
        _global_exchange_client._user_id == user_id):
        return _global_exchange_client
    
    # Créer nouvelle instance avec user_id
    if user_id:
        logger.warning(f"🔒 Création ExchangeClient global avec user_id {user_id} - Préférer instanciation directe")
        _global_exchange_client = ExchangeClient(user_id=user_id)
    else:
        logger.warning(f"⚠️ ExchangeClient global SANS user_id - Risque sécurité multi-tenant")
        _global_exchange_client = ExchangeClient()
    
    return _global_exchange_client


# === ALIAS RÉTROCOMPATIBILITÉ ===
# Pour migration transparente depuis CCXTClient
CCXTClient = ExchangeClient
get_global_ccxt_client = get_global_exchange_client