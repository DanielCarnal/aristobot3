# -*- coding: utf-8 -*-
"""
Client CCXT - Interface pour communiquer avec le service centralisé CCXT
Utilisé par Trading Engine, Trading Manuel, Backtest, etc.
"""
import asyncio
import uuid
import json
import logging
from channels.layers import get_channel_layer
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Instance globale pour gérer les réponses
_global_ccxt_client = None

class CCXTClient:
    """
    Client pour communiquer avec le service CCXT centralisé via Redis
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        # Définir cette instance comme globale
        global _global_ccxt_client
        _global_ccxt_client = self
    
    async def _send_request(self, action: str, params: Dict) -> Any:
        """Envoie une requête au service CCXT et attend la réponse"""
        request_id = str(uuid.uuid4())
        
        # Log spécial pour place_order
        if action == 'place_order':
            logger.info(f"🔥 CCXTClient._send_request PLACE_ORDER START: {action} - {request_id[:8]}... - {params}")
        
        # Créer une Future pour attendre la réponse
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[request_id] = future
        
        # Envoyer la requête
        request = {
            'request_id': request_id,
            'action': action,
            'params': params,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        # Envoyer la requête via Redis directement
        import json
        from .redis_fallback import get_redis_client
        
        try:
            redis_client = await get_redis_client()
            
            # Test connexion
            await redis_client.ping()
            
            # Envoyer la requête
            await redis_client.rpush('ccxt_requests', json.dumps(request))
            logger.info(f"📤 Requête envoyée: {action} - {request_id[:8]}...")
            
            # Attendre la réponse
            response_key = f"ccxt_response_{request_id}"
            
            # Polling pour la réponse (timeout 60s pour les opérations longues)
            timeout_iterations = 600  # 60s = 600 * 0.1s
            
            # Timeout spécifique selon l'action
            if action in ['get_balance', 'get_markets']:
                timeout_iterations = 900  # 90s pour les opérations plus longues
            elif action in ['place_order', 'cancel_order', 'edit_order']:
                timeout_iterations = 1200  # 120s pour les ordres (Bitget peut être lent)
            
            for i in range(timeout_iterations):
                response_data = await redis_client.get(response_key)
                if response_data:
                    response = json.loads(response_data)
                    await redis_client.delete(response_key)  # Nettoyer
                    
                    logger.info(f"📥 Réponse reçue: {action} - {request_id[:8]}... après {i*0.1:.1f}s")
                    
                    if response['success']:
                        return response['data']
                    else:
                        raise Exception(response['error'])
                
                await asyncio.sleep(0.1)
            
            # Timeout
            timeout_seconds = timeout_iterations * 0.1
            logger.error(f"⏰ Timeout CCXT: {action} - {request_id[:8]}... après {timeout_seconds:.0f}s")
            raise Exception(f"Timeout CCXT request {action}")
            
        except Exception as e:
            if "Timeout" not in str(e) and "ping" not in str(e).lower():
                logger.error(f"❌ Erreur Redis CCXT {action}: {e}")
            raise
        finally:
            # Nettoyer
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            try:
                await redis_client.close()
            except:
                pass
    
    async def handle_response(self, response: Dict):
        """Traite une réponse reçue du service CCXT"""
        request_id = response.get('request_id')
        if request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                future.set_result(response)
    
    async def get_balance(self, broker_id: int) -> Dict:
        """Récupère le solde d'un broker"""
        return await self._send_request('get_balance', {'broker_id': broker_id})
    
    async def get_candles(self, broker_id: int, symbol: str, 
                         timeframe: str, limit: int = 100) -> list:
        """Récupère des bougies OHLCV"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'limit': limit
        }
        return await self._send_request('get_candles', params)
    
    async def place_market_order(self, broker_id: int, symbol: str, 
                                side: str, amount: float) -> Dict:
        """Passe un ordre au marché"""
        logger.info(f"🔥 CCXTClient.place_market_order appelé: {side} {amount} {symbol}")
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'type': 'market'
        }
        logger.info(f"🔥 CCXTClient: Envoi place_order avec params: {params}")
        return await self._send_request('place_order', params)
    
    async def place_limit_order(self, broker_id: int, symbol: str, 
                               side: str, amount: float, price: float) -> Dict:
        """Passe un ordre limite"""
        logger.info(f"🔥 CCXTClient.place_limit_order appelé: {side} {amount} {symbol} @ {price}")
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'type': 'limit'
        }
        logger.info(f"🔥 CCXTClient: Envoi place_order avec params: {params}")
        return await self._send_request('place_order', params)
    
    async def get_markets(self, broker_id: int) -> Dict:
        """Récupère les marchés disponibles pour un broker"""
        return await self._send_request('get_markets', {'broker_id': broker_id})
    
    async def get_ticker(self, broker_id: int, symbol: str) -> Dict:
        """Récupère le ticker (prix) d'un symbole"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol
        }
        return await self._send_request('get_ticker', params)
    
    async def preload_all_brokers(self) -> tuple:
        """Demande le préchargement de tous les brokers"""
        return await self._send_request('preload_brokers', {})
    
    async def fetch_open_orders(self, broker_id: int, symbol: str = None, 
                               since: int = None, limit: int = None) -> list:
        """Récupère les ordres ouverts pour un broker"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'since': since,
            'limit': limit
        }
        # Supprimer les paramètres None
        params = {k: v for k, v in params.items() if v is not None}
        return await self._send_request('fetch_open_orders', params)
    
    async def fetch_closed_orders(self, broker_id: int, symbol: str = None, 
                                 since: int = None, limit: int = None) -> list:
        """Récupère les ordres fermés/exécutés pour un broker"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'since': since,
            'limit': limit
        }
        # Supprimer les paramètres None
        params = {k: v for k, v in params.items() if v is not None}
        return await self._send_request('fetch_closed_orders', params)
    
    async def cancel_order(self, broker_id: int, order_id: str, symbol: str = None) -> Dict:
        """Annule un ordre ouvert"""
        params = {
            'broker_id': broker_id,
            'order_id': order_id,
            'symbol': symbol
        }
        # Supprimer les paramètres None
        params = {k: v for k, v in params.items() if v is not None}
        return await self._send_request('cancel_order', params)
    
    async def edit_order(self, broker_id: int, order_id: str, symbol: str,
                        order_type: str = 'limit', side: str = None, 
                        amount: float = None, price: float = None) -> Dict:
        """Modifie un ordre ouvert"""
        params = {
            'broker_id': broker_id,
            'order_id': order_id,
            'symbol': symbol,
            'type': order_type,
            'side': side,
            'amount': amount,
            'price': price
        }
        # Supprimer les paramètres None
        params = {k: v for k, v in params.items() if v is not None}
        return await self._send_request('edit_order', params)

def get_global_ccxt_client():
    """Récupère l'instance globale de CCXTClient"""
    return _global_ccxt_client