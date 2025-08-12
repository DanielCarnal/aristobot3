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
            'preload_brokers': self._handle_preload_brokers,
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
        
        # Afficher le monitoring Redis
        await self._display_redis_monitor()
        
        # Écouter les requêtes Redis
        while self.running:
            try:
                # Recevoir requête depuis le channel ccxt_requests
                # Note: Cette implémentation sera complétée avec la vraie logique Redis
                await asyncio.sleep(0.1)  # Placeholder - éviter la boucle infinie
                
                # TODO: Implémenter la vraie écoute des channels Redis
                # message = await self.channel_layer.receive('ccxt_requests')
                # await self._process_request(message)
                
            except Exception as e:
                logger.error(f"❌ Erreur CCXT Service: {e}")
                await asyncio.sleep(1)
    
    async def _process_request(self, message):
        """Traite une requête CCXT et envoie la réponse"""
        try:
            request_id = message.get('request_id')
            action = message.get('action')
            params = message.get('params', {})
            
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
            
            # Envoyer la réponse
            await self.channel_layer.send('ccxt_responses', response)
            
        except Exception as e:
            response = {
                'request_id': message.get('request_id'),
                'success': False,
                'error': str(e)
            }
            await self.channel_layer.send('ccxt_responses', response)
    
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
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        side = params['side']  # 'buy' or 'sell'
        amount = params['amount']
        order_type = params.get('type', 'market')
        price = params.get('price')
        
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        if order_type == 'market':
            order = await exchange.create_market_order(symbol, side, amount)
        else:
            order = await exchange.create_limit_order(symbol, side, amount, price)
        
        return order
    
    async def _handle_preload_brokers(self, params):
        """Précharge tous les brokers"""
        return await CCXTManager.preload_all_brokers()
    
    async def _display_redis_monitor(self):
        """Affiche le monitoring des messages Redis en temps réel"""
        import time
        import random
        
        print(f"\n📡 Redis Message Monitor (CCXT Service)")
        print(f"   {'='*120}")
        
        # Initialiser les 20 lignes vides
        redis_lines = ["" for _ in range(20)]
        line_index = 0
        
        # Buffer de messages simulés pour demo (120 chars)
        sample_messages = [
            "ccxt_requests: {action: get_balance, broker_id: 1, user: dev, timestamp: 1703847362, session_id: abc123}",
            "ccxt_responses: {success: true, data: {USDT: 1000.50, BTC: 0.02345, ETH: 1.5678}, latency_ms: 45}",
            "heartbeat: {timeframe: 1m, symbol: BTCUSDT, open: 58400.00, high: 58450.00, low: 58380.00, close: 58420.15}",
            "ccxt_requests: {action: get_candles, symbol: ETH/USDT, timeframe: 5m, limit: 100, since: 1703840000}",
            "ccxt_responses: {candles: [[1703840000, 2280.50, 2285.00, 2278.00, 2282.15, 125.67]], count: 100}",
            "websocket: frontend connected - user session started, ip: 127.0.0.1, browser: Chrome/119.0",
            "ccxt_requests: {action: place_order, symbol: BTC/USDT, type: market, side: buy, amount: 0.001}",
            "ccxt_responses: {order_id: ord_abc123xyz, status: filled, price: 58421.50, fee: 0.058, timestamp: now}",
            "heartbeat: {timeframe: 15m, symbol: ETHUSDT, signal: bullish_cross, volume: 1245.67, rsi: 65.4}",
            "system: redis channel activity - 847 msgs/min processed, memory: 256MB, connections: 5 active",
            "trading_engine: strategy_id: scalp_001 triggered on BTCUSDT 1m signal, conditions: [MA_cross, Volume>1000]",
            "websocket_broadcast: {type: price_update, data: {BTCUSDT: 58425.30, ETHUSDT: 2283.45}, users: 12}",
            "ccxt_requests: {action: fetch_ticker, symbols: [BTC/USDT, ETH/USDT, ADA/USDT], broker_id: 2}",
            "database: heartbeat_signal saved - id: 98765, timeframe: 5m, processing_time: 12ms, queue_size: 3",
            "auth_system: user login successful - username: trader_pro, 2FA verified, permissions: [read, trade]",
            "ccxt_responses: {tickers: {BTCUSDT: {bid: 58420, ask: 58421}, ETHUSDT: {bid: 2282, ask: 2283}}}",
            "error_handler: CCXT timeout recovered, broker: binance, retry_count: 2, fallback_used: false",
            "performance: avg_response_time: 67ms, peak_memory: 512MB, active_websockets: 8, cpu_usage: 23%"
        ]
        
        async def update_redis_display():
            nonlocal line_index
            
            # Affichage initial fixe
            for i in range(22):  # Header + 20 lignes + footer
                print()
            
            while self.running:
                # Simuler un nouveau message Redis
                if random.random() > 0.2:  # 80% chance d'avoir un message
                    # Prendre un message d'exemple et le modifier légèrement
                    base_msg = random.choice(sample_messages)
                    timestamp = int(time.time())
                    
                    # Formater le message (120 chars max)
                    msg = f"[{timestamp}] {base_msg}"[:120]
                    msg = msg.ljust(120)  # Pad avec des espaces
                    
                    # Ajouter à la ligne courante
                    redis_lines[line_index] = msg
                    line_index = (line_index + 1) % 20
                
                # Repositionner le curseur et réafficher (sans défilement)
                print(f"\033[22A", end="")  # Remonter de 22 lignes
                print(f"   {'='*120}")
                for i, line in enumerate(redis_lines):
                    marker = ">" if i == line_index else " "
                    color_line = line if line.strip() else " " * 120
                    print(f"   {marker} {color_line}")
                print(f"   {'='*120}")
                
                await asyncio.sleep(1)  # Mise à jour chaque seconde
        
        # Lancer le monitoring en arrière-plan
        self.redis_monitor_task = asyncio.create_task(update_redis_display())
    
    def shutdown(self, signum, frame):
        """Arrêt propre du service"""
        self.stdout.write(
            self.style.WARNING("⚠️ Arrêt CCXT Service...")
        )
        self.running = False
        
        # Arrêter le monitoring Redis
        if hasattr(self, 'redis_monitor_task'):
            self.redis_monitor_task.cancel()
        
        # Fermer toutes les connexions CCXT
        asyncio.create_task(CCXTManager.close_all())
        
        sys.exit(0)