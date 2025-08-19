# -*- coding: utf-8 -*-
"""
Service centralisé CCXT - Processus indépendant (Terminal 5)
Gère toutes les connexions CCXT et répond aux requêtes via Redis
"""
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from apps.core.services.ccxt_manager import CCXTManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Service centralisé CCXT - Gère toutes les connexions exchanges'
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.channel_layer = get_channel_layer()
        self.request_handlers = {
            'get_balance': self._handle_get_balance,
            'get_candles': self._handle_get_candles,
            'place_order': self._handle_place_order,
            'get_markets': self._handle_get_markets,
            'get_ticker': self._handle_get_ticker,
            'preload_brokers': self._handle_preload_brokers,
            'fetch_open_orders': self._handle_fetch_open_orders,
            'fetch_closed_orders': self._handle_fetch_closed_orders,
            'cancel_order': self._handle_cancel_order,
            'edit_order': self._handle_edit_order,
        }
    
    def handle(self, *args, **options):
        # Gestion arrêt propre
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        self.stdout.write(
            self.style.SUCCESS("CCXT Service centralise demarre\n")
        )
        
        asyncio.run(self.run_service())
    
    async def run_service(self):
        """Boucle principale du service CCXT"""
        
        # Précharger tous les brokers actifs
        await CCXTManager.preload_all_brokers()
        
        # Afficher l'header du monitoring Redis
        await self._display_redis_monitor()
        
        # Écouter les requêtes Redis directement
        from apps.core.services.redis_fallback import get_redis_client
        
        try:
            redis_client = await get_redis_client()
            await redis_client.ping()
            print("✅ Connexion Redis établie")
            logger.info("✅ Connexion Redis établie")
        except Exception as e:
            print(f"❌ Erreur connexion Redis: {e}")
            logger.error(f"❌ Erreur connexion Redis: {e}")
            self.running = False
            return
        
        print("🔄 Écoute des requêtes Redis...")
        last_queue_check = 0
        
        while self.running:
            try:
                # Vérifier périodiquement le statut de la queue (toutes les 10s)
                import time
                current_time = time.time()
                if current_time - last_queue_check > 10:
                    await self._check_redis_queue_status(redis_client)
                    last_queue_check = current_time
                
                # Écouter le channel Redis directement
                result = await redis_client.blpop('ccxt_requests', timeout=1)
                
                if result:
                    _, message_json = result
                    message = json.loads(message_json)
                    
                    # Capturer le timestamp de début
                    import time
                    start_time = time.time()
                    
                    # Afficher le message reçu formaté avec focus sur place_order
                    action = message.get('action')
                    request_id = message.get('request_id')
                    params = message.get('params', {})
                    
                    if action == 'place_order':
                        # Log spécial pour place_order avec tous les détails
                        request_msg = f"🔥 INCOMING PLACE_ORDER: {request_id[:8]}... - broker_id:{params.get('broker_id')} - {params.get('side')} {params.get('amount')} {params.get('symbol')} - type:{params.get('type', 'market')}"
                        if params.get('price'):
                            request_msg += f" @ {params.get('price')}"
                        print(f"[{int(time.time())}] {request_msg}")
                        logger.info(request_msg)
                    else:
                        # Log normal pour les autres actions
                        request_msg = f"📨 Requête: {action} - {request_id[:8]}... - params: {params}"
                        print(self._format_message(request_msg))
                    
                    await self._process_request_redis(message, redis_client, start_time)
                
            except Exception as e:
                print(f"❌ Erreur CCXT Service: {e}")
                logger.error(f"❌ Erreur CCXT Service: {e}")
                await asyncio.sleep(1)
        
        await redis_client.close()
    
    async def _process_request_redis(self, message, redis_client, start_time):
        """Traite une requête CCXT et envoie la réponse via Redis direct"""
        try:
            request_id = message.get('request_id')
            action = message.get('action')
            params = message.get('params', {})
            
            import time
            
            # Exécuter l'action
            if action in self.request_handlers:
                result = await self.request_handlers[action](params)
                response = {
                    'request_id': request_id,
                    'success': True,
                    'data': result
                }
            else:
                response = {
                    'request_id': request_id,
                    'success': False,
                    'error': f'Action inconnue: {action}'
                }
            
            # Envoyer la réponse via Redis
            response_key = f"ccxt_response_{request_id}"
            await redis_client.setex(response_key, 30, json.dumps(response))
            
            # Calculer le temps de réponse
            end_time = time.time()
            response_time = round(end_time - start_time, 3)  # 3 décimales
            
            # Afficher la réponse formatée avec temps
            if response.get('success'):
                response_msg = f"✅ Réponse: {action} - {request_id[:8]}... - success: true - {response_time}s"
            else:
                response_msg = f"❌ Réponse: {action} - {request_id[:8]}... - error: {response.get('error')} - {response_time}s"
            print(self._format_message(response_msg))
            
        except Exception as e:
            response = {
                'request_id': message.get('request_id'),
                'success': False,
                'error': str(e)
            }
            response_key = f"ccxt_response_{message.get('request_id')}"
            await redis_client.setex(response_key, 30, json.dumps(response))
            
            # Calculer le temps de réponse même en cas d'erreur
            end_time = time.time()
            response_time = round(end_time - start_time, 3)
            
            # Afficher l'erreur formatée avec temps
            error_msg = f"💥 Exception: {message.get('action')} - {message.get('request_id')[:8]}... - error: {str(e)} - {response_time}s"
            print(self._format_message(error_msg))
    
    async def _handle_get_balance(self, params):
        """Récupère le solde d'un broker"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        balance = await exchange.fetch_balance()
        return balance
    
    async def _handle_get_candles(self, params):
        """Récupère des bougies OHLCV"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        timeframe = params['timeframe']
        limit = params.get('limit', 100)
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    
    async def _handle_place_order(self, params):
        """Passe un ordre de trading"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        import time
        
        # Log détaillé de la requête place_order
        start_time = time.time()
        print(f"🔥 PLACE_ORDER START: {params}")
        logger.info(f"🔥 PLACE_ORDER START: {params}")
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        side = params['side']  # 'buy' or 'sell'
        amount = params['amount']
        order_type = params.get('type', 'market')
        price = params.get('price')
        
        try:
            # 1. Récupération broker
            db_start = time.time()
            broker = await sync_to_async(Broker.objects.get)(id=broker_id)
            db_time = time.time() - db_start
            print(f"🔥 PLACE_ORDER - Broker récupéré: {broker.name} ({db_time:.3f}s)")
            
            # 2. Récupération exchange
            exchange_start = time.time()
            exchange = await CCXTManager.get_exchange(broker)
            exchange_time = time.time() - exchange_start
            print(f"🔥 PLACE_ORDER - Exchange récupéré: {exchange.id} ({exchange_time:.3f}s)")
            
            # 3. Vérification des capacités
            if order_type == 'market' and not exchange.has.get('createMarketOrder', False):
                raise Exception(f"Exchange {broker.exchange} ne supporte pas les ordres au marché")
            elif order_type == 'limit' and not exchange.has.get('createLimitOrder', False):
                raise Exception(f"Exchange {broker.exchange} ne supporte pas les ordres limites")
            
            # 4. Passage de l'ordre
            order_start = time.time()
            if order_type == 'market':
                print(f"🔥 PLACE_ORDER - Ordre marché: {side} {amount} {symbol}")
                order = await exchange.create_market_order(symbol, side, amount)
            else:
                print(f"🔥 PLACE_ORDER - Ordre limite: {side} {amount} {symbol} @ {price}")
                order = await exchange.create_limit_order(symbol, side, amount, price)
            
            order_time = time.time() - order_start
            total_time = time.time() - start_time
            
            print(f"🔥 PLACE_ORDER SUCCESS - Order ID: {order.get('id')} ({order_time:.3f}s order, {total_time:.3f}s total)")
            logger.info(f"🔥 PLACE_ORDER SUCCESS - Order ID: {order.get('id')} ({total_time:.3f}s)")
            
            return order
            
        except Exception as e:
            total_time = time.time() - start_time
            print(f"🔥 PLACE_ORDER ERROR après {total_time:.3f}s: {e}")
            logger.error(f"🔥 PLACE_ORDER ERROR après {total_time:.3f}s: {e}")
            raise
    
    async def _handle_get_markets(self, params):
        """Récupère les marchés disponibles pour un broker"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Les marchés sont déjà chargés lors de l'initialisation
        markets = exchange.markets
        return markets
    
    async def _handle_get_ticker(self, params):
        """Récupère le ticker (prix) d'un symbole"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        ticker = await exchange.fetch_ticker(symbol)
        return ticker
    
    async def _handle_preload_brokers(self, params):
        """Précharge tous les brokers"""
        return await CCXTManager.preload_all_brokers()
    
    async def _handle_fetch_open_orders(self, params):
        """Récupère les ordres ouverts pour un broker"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbol = params.get('symbol')  # Optionnel, pour un symbole spécifique
        since = params.get('since')    # Optionnel
        limit = params.get('limit')    # Optionnel
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier que l'exchange supporte fetchOpenOrders
        if not exchange.has.get('fetchOpenOrders', False):
            raise Exception(f"Exchange {broker.exchange} ne supporte pas fetchOpenOrders")
        
        open_orders = await exchange.fetch_open_orders(symbol, since, limit)
        return open_orders
    
    async def _handle_fetch_closed_orders(self, params):
        """Récupère les ordres fermés/exécutés pour un broker"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbol = params.get('symbol')  # Optionnel, pour un symbole spécifique
        since = params.get('since')    # Optionnel
        limit = params.get('limit')    # Optionnel
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier que l'exchange supporte fetchClosedOrders
        if not exchange.has.get('fetchClosedOrders', False):
            raise Exception(f"Exchange {broker.exchange} ne supporte pas fetchClosedOrders")
        
        closed_orders = await exchange.fetch_closed_orders(symbol, since, limit)
        return closed_orders
    
    async def _handle_cancel_order(self, params):
        """Annule un ordre ouvert"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        order_id = params['order_id']
        symbol = params.get('symbol')  # Requis pour certains exchanges
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier que l'exchange supporte cancelOrder
        if not exchange.has.get('cancelOrder', False):
            raise Exception(f"Exchange {broker.exchange} ne supporte pas cancelOrder")
        
        result = await exchange.cancel_order(order_id, symbol)
        return result
    
    async def _handle_edit_order(self, params):
        """Modifie un ordre ouvert (si supporté par l'exchange)"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        order_id = params['order_id']
        symbol = params['symbol']
        order_type = params.get('type', 'limit')
        side = params.get('side')
        amount = params.get('amount')
        price = params.get('price')
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier que l'exchange supporte editOrder
        if not exchange.has.get('editOrder', False):
            raise Exception(f"Exchange {broker.exchange} ne supporte pas editOrder")
        
        result = await exchange.edit_order(order_id, symbol, order_type, side, amount, price)
        return result
    
    def _format_message(self, message):
        """Formate un message pour l'affichage avec limite de 160 caractères"""
        import time
        
        timestamp = int(time.time())
        formatted_msg = f"[{timestamp}] {message}"
        
        # Si le message dépasse 160 caractères
        if len(formatted_msg) > 160:
            # Prendre les 95 premiers + " .|. " + les 60 derniers
            first_part = formatted_msg[:95]
            last_part = formatted_msg[-60:]
            return f"{first_part} .|. {last_part}"
        
        return formatted_msg
    
    async def _display_redis_monitor(self):
        """Affiche le monitoring des messages Redis en temps réel"""
        print(f"\n📡 Redis Message Monitor (CCXT Service) - Logs au fil de l'eau")
        print(f"{'='*80}")
        print("En attente des messages Redis...")
    
    async def _check_redis_queue_status(self, redis_client):
        """Vérifie le statut de tous les canaux Redis et affiche les métriques"""
        try:
            # 1. Files de messages (listes)
            queue_stats = []
            
            # Vérifier ccxt_requests avec détails supplémentaires
            ccxt_queue_length = await redis_client.llen('ccxt_requests')
            if ccxt_queue_length > 0:
                queue_stats.append(f"ccxt_requests: {ccxt_queue_length}")
                
                # Si il y a des messages en attente, les afficher
                if ccxt_queue_length > 0:
                    # Peek les premiers messages sans les retirer
                    pending_messages = await redis_client.lrange('ccxt_requests', 0, min(ccxt_queue_length-1, 4))
                    print(f"⚠️  ATTENTION: {ccxt_queue_length} messages en attente dans ccxt_requests!")
                    for idx, msg in enumerate(pending_messages):
                        try:
                            parsed = json.loads(msg)
                            action = parsed.get('action', 'unknown')
                            req_id = parsed.get('request_id', 'no-id')[:8]
                            print(f"   Message {idx+1}: {action} - {req_id}...")
                        except:
                            print(f"   Message {idx+1}: [non-parsable]")
                    if ccxt_queue_length > 5:
                        print(f"   ... et {ccxt_queue_length - 5} autres messages")
            
            # Vérifier autres files potentielles
            for queue_name in ['heartbeat_queue', 'stream_queue', 'backtest_queue', 'trading_queue']:
                try:
                    length = await redis_client.llen(queue_name)
                    if length > 0:
                        queue_stats.append(f"{queue_name}: {length}")
                except:
                    pass  # File n'existe pas
            
            # 2. Canaux Pub/Sub
            pubsub_stats = []
            try:
                # Lister tous les canaux actifs
                channels = await redis_client.execute_command('PUBSUB', 'CHANNELS')
                if channels:
                    # Obtenir le nombre d'abonnés pour chaque canal
                    channel_names = [ch.decode() if isinstance(ch, bytes) else str(ch) for ch in channels]
                    if channel_names:
                        numsub_result = await redis_client.execute_command('PUBSUB', 'NUMSUB', *channel_names)
                        # numsub_result = [channel1, count1, channel2, count2, ...]
                        for i in range(0, len(numsub_result), 2):
                            channel = numsub_result[i].decode() if isinstance(numsub_result[i], bytes) else str(numsub_result[i])
                            subscribers = numsub_result[i + 1]
                            # Afficher TOUS les canaux, même avec 0 abonnés
                            pubsub_stats.append(f"{channel}: {subscribers} sub")
                else:
                    # Vérifier les canaux connus même s'ils ne sont pas actifs
                    known_channels = ['heartbeat', 'stream', 'backtest', 'trading-manual']
                    numsub_result = await redis_client.execute_command('PUBSUB', 'NUMSUB', *known_channels)
                    for i in range(0, len(numsub_result), 2):
                        channel = numsub_result[i].decode() if isinstance(numsub_result[i], bytes) else str(numsub_result[i])
                        subscribers = numsub_result[i + 1]
                        if subscribers >= 0:  # Afficher même si 0 abonnés
                            pubsub_stats.append(f"{channel}: {subscribers} sub")
            except Exception as e:
                pubsub_stats.append(f"pubsub_error: {str(e)}")
            
            # 3. Clés temporaires (réponses)
            response_keys = await redis_client.keys('ccxt_response_*')
            pending_responses = len(response_keys)
            
            # 4. Autres clés importantes
            other_keys = []
            for pattern in ['heartbeat_*', 'stream_*', 'session_*', 'cache_*']:
                try:
                    keys = await redis_client.keys(pattern)
                    if keys:
                        other_keys.append(f"{pattern}: {len(keys)}")
                except:
                    pass
            
            # Construire le message de statut
            status_parts = []
            
            if queue_stats:
                status_parts.append(f"Queues: {', '.join(queue_stats)}")
            
            if pubsub_stats:
                status_parts.append(f"PubSub: {', '.join(pubsub_stats)}")
            
            if pending_responses > 0:
                status_parts.append(f"Responses: {pending_responses} pending")
            
            if other_keys:
                status_parts.append(f"Keys: {', '.join(other_keys)}")
            
            # Afficher TOUJOURS le statut, même si vide
            if status_parts:
                status_msg = f"📊 Redis Status: {' | '.join(status_parts)}"
                print(self._format_message(status_msg))
            else:
                # Si pas d'activité, indiquer que Redis est vide/inactif
                status_msg = "📊 Redis Status: Aucune activité détectée"
                print(self._format_message(status_msg))
                
        except Exception as e:
            error_msg = f"⚠️  Erreur vérification Redis complète: {str(e)}"
            print(self._format_message(error_msg))
    
    def shutdown(self, signum, frame):
        """Arrêt propre du service"""
        self.stdout.write(
            self.style.WARNING("⚠️ Arrêt CCXT Service...")
        )
        self.running = False
        
        
        # Fermer toutes les connexions CCXT
        asyncio.create_task(CCXTManager.close_all())
        
        sys.exit(0)