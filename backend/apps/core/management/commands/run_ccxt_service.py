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
        # ARCHITECTURE UNIFIÉE - une seule méthode place_order pour tous les types
        self.request_handlers = {
            'get_balance': self._handle_get_balance,
            'get_candles': self._handle_get_candles,
            'place_order': self._handle_place_order,  # ✅ GÈRE TOUS LES TYPES D'ORDRES
            'get_markets': self._handle_get_markets,
            'get_ticker': self._handle_get_ticker,
            'fetch_tickers': self._handle_fetch_tickers,
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
        """NOUVELLE ARCHITECTURE - Passe un ordre avec intelligence CCXT native"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        import time
        
        start_time = time.time()
        logger.info(f"🚀 PLACE_ORDER CCXT NATIVE: {params}")
        
        # Extraction paramètres
        broker_id = params['broker_id']
        symbol = params['symbol']
        side = params['side']
        amount = params['amount']
        order_type = params.get('type', 'market')
        price = params.get('price')
        
        # Paramètres avancés CCXT natifs
        stop_loss_price = params.get('stop_loss_price')
        take_profit_price = params.get('take_profit_price')
        trigger_price = params.get('trigger_price')
        
        try:
            # 1. Récupération broker + exchange
            broker = await sync_to_async(Broker.objects.get)(id=broker_id)
            exchange = await CCXTManager.get_exchange(broker)
            
            # 2. INTELLIGENCE CCXT - Détecter type de marché et capacités (CORRECTION MAJEURE)
            logger.info(f"🔍 DEBUG: exchange.has type = {type(exchange.has)}")
            
            # ÉTAPE 1: Déterminer le type de marché (SPOT vs SWAP)
            try:
                # Charger les marchés si pas déjà fait
                if not hasattr(exchange, 'markets') or not exchange.markets:
                    await exchange.load_markets()
                
                market_info = exchange.markets.get(symbol)
                if market_info:
                    is_spot = market_info.get('spot', False)
                    is_swap = market_info.get('swap', False)
                    market_type = market_info.get('type', 'unknown')
                    logger.info(f"🔍 Marché {symbol}: type={market_type}, spot={is_spot}, swap={is_swap}")
                else:
                    logger.warning(f"⚠️ Impossible de déterminer le type de marché pour {symbol}")
                    is_spot, is_swap, market_type = True, False, 'spot'  # Défaut SPOT
            except Exception as e:
                logger.warning(f"⚠️ Erreur détection type marché: {e}, assume SPOT")
                is_spot, is_swap, market_type = True, False, 'spot'
            
            # ÉTAPE 2: Adapter la stratégie selon SPOT vs SWAP
            if isinstance(exchange.has, dict):
                # Capacités générales
                has_stop_loss_api = exchange.has.get('createStopLossOrder', False)
                has_take_profit_api = exchange.has.get('createTakeProfitOrder', False)
                has_sl_tp_combo = exchange.has.get('createOrderWithTakeProfitAndStopLoss', False)
                has_trigger = exchange.has.get('createTriggerOrder', False)
                
                # BITGET LOGIC: SPOT utilise triggerPrice, SWAP utilise APIs spécialisées
                if is_spot:
                    # SPOT: Utiliser triggerPrice même si APIs spécialisées existent
                    use_specialized = False
                    use_trigger = has_trigger
                    logger.info(f"🔍 SPOT {symbol}: Utiliser triggerPrice={use_trigger}")
                elif is_swap:
                    # SWAP: Utiliser APIs spécialisées si disponibles
                    use_specialized = has_stop_loss_api or has_take_profit_api
                    use_trigger = has_trigger and not use_specialized
                    logger.info(f"🔍 SWAP {symbol}: APIs spécialisées={use_specialized}, fallback trigger={use_trigger}")
                else:
                    # Défaut: essayer spécialisé puis trigger
                    use_specialized = has_stop_loss_api or has_take_profit_api
                    use_trigger = has_trigger
                    logger.info(f"🔍 Type inconnu {symbol}: spécialisé={use_specialized}, trigger={use_trigger}")
            else:
                logger.warning(f"⚠️ exchange.has n'est pas un dict: {type(exchange.has)}")
                use_specialized = False
                use_trigger = False
            
            logger.info(f"🔍 Exchange {broker.exchange} stratégie pour {market_type}:")
            logger.info(f"   - Utiliser APIs spécialisées: {use_specialized}")
            logger.info(f"   - Utiliser triggerPrice: {use_trigger}")
            
            # 3. STRATÉGIE EXÉCUTION adaptée SPOT vs SWAP
            ccxt_params = {}
            
            if order_type == 'stop_loss':
                if use_specialized and is_swap:
                    # SWAP MARKETS - APIs spécialisées Bitget 
                    logger.info(f"🎯 BITGET SWAP - Stop Loss via create_stop_loss_order: {stop_loss_price}")
                    result = await exchange.create_stop_loss_order(symbol, 'market', side, amount, None, stop_loss_price)
                    
                    # Gestion des réponses boolean pour APIs spécialisées
                    if isinstance(result, bool):
                        logger.info(f"🔄 API spécialisée SWAP Stop Loss retourne bool: {result}")
                        standardized_result = {
                            'id': f"bitget_swap_sl_{int(time.time())}",
                            'symbol': symbol,
                            'type': 'stop_loss',
                            'side': side,
                            'amount': amount,
                            'price': None,
                            'stopPrice': stop_loss_price,
                            'status': 'created' if result else 'failed',
                            'timestamp': int(time.time() * 1000),
                            'info': {'success': result, 'specialized_api': 'create_stop_loss_order', 'market_type': 'swap'}
                        }
                        return standardized_result
                    return result
                    
                elif use_trigger:
                    # SPOT MARKETS - Structure imbriquée Bitget (issue CCXT #21487)
                    logger.info(f"🎯 BITGET SPOT - Stop Loss structure imbriquée: {stop_loss_price}")
                    ccxt_params = {
                        'stopLoss': {
                            'triggerPrice': stop_loss_price,
                            'price': stop_loss_price
                        }
                    }
                    # EXÉCUTION IMMÉDIATE avec structure imbriquée
                    order_result = await exchange.create_order(symbol, 'market', side, amount, None, ccxt_params)
                    
                    # Gestion des réponses boolean 
                    if isinstance(order_result, bool):
                        logger.info(f"🔄 Stop Loss SPOT structure imbriquée retourne bool: {order_result}")
                        standardized_result = {
                            'id': f"bitget_spot_sl_{int(time.time())}",
                            'symbol': symbol,
                            'type': 'stop_loss',
                            'side': side,
                            'amount': amount,
                            'price': None,
                            'stopPrice': stop_loss_price,
                            'status': 'created' if order_result else 'failed',
                            'timestamp': int(time.time() * 1000),
                            'info': {'success': order_result, 'nested_structure': True, 'market_type': 'spot'}
                        }
                        return standardized_result
                    return order_result
                else:
                    raise Exception(f"Exchange {broker.exchange} ne supporte ni APIs spécialisées ni triggerPrice pour {market_type}")
                    
            elif order_type == 'take_profit':
                if use_specialized and is_swap:
                    # SWAP MARKETS - APIs spécialisées Bitget
                    logger.info(f"🎯 BITGET SWAP - Take Profit via create_take_profit_order: {take_profit_price}")
                    result = await exchange.create_take_profit_order(symbol, 'market', side, amount, None, take_profit_price)
                    
                    # Gestion des réponses boolean pour APIs spécialisées
                    if isinstance(result, bool):
                        logger.info(f"🔄 API spécialisée SWAP Take Profit retourne bool: {result}")
                        standardized_result = {
                            'id': f"bitget_swap_tp_{int(time.time())}",
                            'symbol': symbol,
                            'type': 'take_profit',
                            'side': side,
                            'amount': amount,
                            'price': None,
                            'takeProfitPrice': take_profit_price,
                            'status': 'created' if result else 'failed',
                            'timestamp': int(time.time() * 1000),
                            'info': {'success': result, 'specialized_api': 'create_take_profit_order', 'market_type': 'swap'}
                        }
                        return standardized_result
                    return result
                    
                elif use_trigger:
                    # SPOT MARKETS - Structure imbriquée Bitget (issue CCXT #21487)
                    logger.info(f"🎯 BITGET SPOT - Take Profit structure imbriquée: {take_profit_price}")
                    ccxt_params = {
                        'takeProfit': {
                            'triggerPrice': take_profit_price,
                            'price': take_profit_price
                        }
                    }
                    # EXÉCUTION IMMÉDIATE avec structure imbriquée
                    order_result = await exchange.create_order(symbol, 'market', side, amount, None, ccxt_params)
                    
                    # Gestion des réponses boolean
                    if isinstance(order_result, bool):
                        logger.info(f"🔄 Take Profit SPOT structure imbriquée retourne bool: {order_result}")
                        standardized_result = {
                            'id': f"bitget_spot_tp_{int(time.time())}",
                            'symbol': symbol,
                            'type': 'take_profit',
                            'side': side,
                            'amount': amount,
                            'price': None,
                            'takeProfitPrice': take_profit_price,
                            'status': 'created' if order_result else 'failed',
                            'timestamp': int(time.time() * 1000),
                            'info': {'success': order_result, 'nested_structure': True, 'market_type': 'spot'}
                        }
                        return standardized_result
                    return order_result
                else:
                    raise Exception(f"Exchange {broker.exchange} ne supporte ni APIs spécialisées ni triggerPrice pour {market_type}")
                    
            elif order_type == 'sl_tp_combo':
                if use_specialized and is_swap:
                    # SWAP MARKETS - Combo spécialisé Bitget
                    logger.info(f"🎯 BITGET SWAP - SL+TP Combo via create_order_with_take_profit_and_stop_loss")
                    result = await exchange.create_order_with_take_profit_and_stop_loss(
                        symbol, 'market', side, amount, None, take_profit_price, stop_loss_price
                    )
                    
                    # Gestion des réponses boolean pour APIs spécialisées
                    if isinstance(result, bool):
                        logger.info(f"🔄 API spécialisée SWAP SL+TP Combo retourne bool: {result}")
                        standardized_result = {
                            'id': f"bitget_swap_combo_{int(time.time())}",
                            'symbol': symbol,
                            'type': 'sl_tp_combo',
                            'side': side,
                            'amount': amount,
                            'price': None,
                            'stopLossPrice': stop_loss_price,
                            'takeProfitPrice': take_profit_price,
                            'status': 'created' if result else 'failed',
                            'timestamp': int(time.time() * 1000),
                            'info': {'success': result, 'specialized_api': 'create_order_with_take_profit_and_stop_loss', 'market_type': 'swap'}
                        }
                        return standardized_result
                    return result
                    
                elif is_spot:
                    # SPOT MARKETS - Pas de combo possible, erreur explicite
                    raise Exception(
                        f"SPOT {symbol}: SL+TP Combo non supporté sur marchés SPOT Bitget. "
                        f"Créez des ordres Stop Loss et Take Profit séparés."
                    )
                else:
                    raise Exception(
                        f"Exchange {broker.exchange} ne supporte pas SL+TP Combo pour {market_type}"
                    )
                    
            elif order_type == 'stop_limit':
                if has_trigger:
                    ccxt_params['triggerPrice'] = trigger_price
                    if broker.exchange.lower() == 'bitget':
                        order_type = 'limit'  # Bitget mapping
                    logger.info(f"✅ Stop Limit: triggerPrice={trigger_price}")
                else:
                    raise Exception(f"Exchange {broker.exchange} ne supporte pas les ordres Stop Limit")
            
            # 4. Exécution CCXT : ordres génériques (Market, Limit, Stop Limit)
            if order_type in ['market', 'limit', 'stop_limit']:
                logger.info(f"🎯 Exécution CCXT générique: {symbol} {order_type} {side} {amount} @ {price}")
                logger.info(f"🎯 Paramètres: {ccxt_params}")
                
                order_result = await exchange.create_order(symbol, order_type, side, amount, price, ccxt_params)
            else:
                # Les ordres spécialisés (stop_loss, take_profit, sl_tp_combo) 
                # ont déjà été traités et returned ci-dessus
                raise Exception(f"Type d'ordre non géré: {order_type}")
            
            total_time = time.time() - start_time
            
            # VALIDATION TYPE RETOUR CCXT ET CONVERSION GARANTIE
            if isinstance(order_result, bool):
                logger.warning(f"⚠️ CCXT retourne bool au lieu d'objet: {order_result}")
                # Construire réponse standard pour compatibilité
                standardized_order = {
                    'id': f"bitget_bool_{int(time.time())}",
                    'symbol': symbol,
                    'type': order_type,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'status': 'created' if order_result else 'failed',
                    'timestamp': int(time.time() * 1000),
                    'info': {'success': order_result, 'original_response': order_result}
                }
                logger.info(f"🔄 Bool converti en dict: {standardized_order}")
                return standardized_order
            
            # Si c'est déjà un dict, retourner tel quel
            order_id = order_result.get('id', 'unknown') if isinstance(order_result, dict) else str(order_result)
            logger.info(f"✅ PLACE_ORDER SUCCESS: ID={order_id} ({total_time:.3f}s)")
            
            return order_result
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ PLACE_ORDER ERROR ({total_time:.3f}s): {e}")
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
    
    async def _handle_fetch_tickers(self, params):
        """Récupère les tickers pour plusieurs symboles en une requête"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbols = params['symbols']
        
        logger.info(f"🔄 Handler fetch_tickers: broker {broker_id}, symbols {symbols}")
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier que l'exchange supporte fetchTickers
        if not exchange.has['fetchTickers']:
            raise Exception(f"Exchange {exchange.name} ne supporte pas fetchTickers")
        
        tickers = await exchange.fetchTickers(symbols)
        logger.info(f"✅ Récupérés {len(tickers)} tickers via fetchTickers")
        return tickers
    
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
        
        # Convertir since en int si c'est une string
        if since and isinstance(since, str):
            try:
                since = int(since)
            except ValueError:
                logger.warning(f"Paramètre 'since' invalide: {since}, ignoré")
                since = None
        
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
    
    async def _handle_place_stop_loss_order(self, params):
        """Place un ordre Stop Loss"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        side = params['side']
        amount = params['amount']
        stop_loss_price = params['stop_loss_price']
        order_type = params.get('type', 'market')  # market ou limit
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier support Stop Loss
        if not exchange.has.get('createStopLossOrder', False):
            raise Exception(f"Exchange {broker.exchange} ne supporte pas createStopLossOrder")
        
        # Paramètres selon le type
        if order_type == 'market':
            result = await exchange.create_stop_loss_order(
                symbol, 'market', side, amount, None, stop_loss_price
            )
        else:  # limit
            price = params.get('price')
            if not price:
                raise Exception("Prix requis pour Stop Loss limite")
            result = await exchange.create_stop_loss_order(
                symbol, 'limit', side, amount, price, stop_loss_price
            )
        
        return result
    
    async def _handle_place_take_profit_order(self, params):
        """Place un ordre Take Profit"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        side = params['side']
        amount = params['amount']
        take_profit_price = params['take_profit_price']
        order_type = params.get('type', 'market')
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier support Take Profit
        if not exchange.has.get('createTakeProfitOrder', False):
            raise Exception(f"Exchange {broker.exchange} ne supporte pas createTakeProfitOrder")
        
        # Paramètres selon le type
        if order_type == 'market':
            result = await exchange.create_take_profit_order(
                symbol, 'market', side, amount, None, take_profit_price
            )
        else:  # limit
            price = params.get('price')
            if not price:
                raise Exception("Prix requis pour Take Profit limite")
            result = await exchange.create_take_profit_order(
                symbol, 'limit', side, amount, price, take_profit_price
            )
        
        return result
    
    async def _handle_place_sl_tp_combo_order(self, params):
        """Place un ordre avec Stop Loss + Take Profit combiné"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        side = params['side']
        amount = params['amount']
        stop_loss_price = params['stop_loss_price']
        take_profit_price = params['take_profit_price']
        price = params.get('price')  # Optionnel pour market
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier support SL+TP combo
        if not exchange.has.get('createOrderWithTakeProfitAndStopLoss', False):
            raise Exception(f"Exchange {broker.exchange} ne supporte pas createOrderWithTakeProfitAndStopLoss")
        
        # Déterminer le type d'ordre
        order_type = 'market' if price is None else 'limit'
        
        result = await exchange.create_order_with_take_profit_and_stop_loss(
            symbol, order_type, side, amount, price, take_profit_price, stop_loss_price
        )
        
        return result
    
    async def _handle_place_stop_limit_order(self, params):
        """Place un ordre Stop Limit"""
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        side = params['side']
        amount = params['amount']
        price = params['price']
        trigger_price = params['trigger_price']
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        # Vérifier support Stop Limit
        if not exchange.has.get('createStopLimitOrder', False):
            raise Exception(f"Exchange {broker.exchange} ne supporte pas createStopLimitOrder")
        
        result = await exchange.create_stop_limit_order(
            symbol, side, amount, price, trigger_price
        )
        
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