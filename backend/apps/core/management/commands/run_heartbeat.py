import asyncio
import json
import websockets
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.utils import timezone
from apps.core.models import HeartbeatStatus, CandleHeartbeat
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run Binance WebSocket heartbeat service avec persistance'

    def __init__(self):
        super().__init__()
        self.heartbeat_status = None
        
    def handle(self, *args, **options):
        self.stdout.write('Starting Enhanced Heartbeat service...')
        
        # Initialiser ou récupérer le statut
        self.heartbeat_status, created = HeartbeatStatus.objects.get_or_create(
            id=1,  # Singleton
            defaults={
                'is_connected': False,
                'symbols_monitored': ['BTCUSDT']
            }
        )
        
        # Enregistrer le démarrage
        self.heartbeat_status.record_start()
        self.stdout.write(
            self.style.SUCCESS(f'[OK] Heartbeat demarre a {self.heartbeat_status.last_application_start}')
        )
        
        try:
            asyncio.run(self.run_heartbeat())
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur critique: {e}'))
            self.shutdown()

    def shutdown(self):
        """Arrêt propre du service"""
        if self.heartbeat_status:
            self.heartbeat_status.record_stop()
            self.stdout.write(
                self.style.WARNING(f'[STOP] Heartbeat arrete a {self.heartbeat_status.last_application_stop}')
            )

    async def run_heartbeat(self):
        """Boucle principale du Heartbeat avec persistance"""
        channel_layer = get_channel_layer()
        
        # URL WebSocket Binance multi-timeframes
        stream_url = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m/btcusdt@kline_3m/btcusdt@kline_5m/btcusdt@kline_15m/btcusdt@kline_1h/btcusdt@kline_4h"
        
        while True:
            try:
                async with websockets.connect(stream_url) as websocket:
                    self.stdout.write('[CONNECT] Connecte a Binance WebSocket')
                    self.heartbeat_status.is_connected = True
                    await sync_to_async(self.heartbeat_status.save)()
                    
                    async for message in websocket:
                        await self.process_message(message, channel_layer)
                        
            except Exception as e:
                self.stdout.write(f'WebSocket error: {e}')
                self.heartbeat_status.is_connected = False
                self.heartbeat_status.last_error = str(e)
                await sync_to_async(self.heartbeat_status.save)()
                await asyncio.sleep(5)

    async def process_message(self, message, channel_layer):
        """Traite un message WebSocket avec sauvegarde"""
        try:
            data = json.loads(message)
            
            # Diffuser le stream brut (existant)
            await channel_layer.group_send(
                "stream",
                {
                    "type": "stream_message",
                    "message": data
                }
            )
            
            # Traiter les bougies fermées
            if 'k' in data and data['k']['x']:  # Bougie fermée
                await self.process_closed_candle(data, channel_layer)
                
        except Exception as e:
            logger.error(f"Erreur traitement message: {e}")

    async def process_closed_candle(self, data, channel_layer):
        """Traite une bougie fermée avec sauvegarde DB"""
        k = data['k']
        dhm_reception = timezone.now()
        dhm_candle = timezone.datetime.fromtimestamp(k['T'] / 1000, tz=timezone.utc)
        
        # Préparer les données
        kline_data = {
            'symbol': k['s'],
            'timeframe': k['i'],
            'open_time': k['t'],
            'close_time': k['T'],
            'open_price': float(k['o']),
            'close_price': float(k['c']),
            'high_price': float(k['h']),
            'low_price': float(k['l']),
            'volume': float(k['v']),
            'is_closed': k['x'],
            'dhm_reception': dhm_reception.isoformat(),
            'dhm_candle': dhm_candle.isoformat()
        }
        
        # SAUVEGARDE EN BASE (NOUVEAU) - Version async
        try:
            candle_signal = await sync_to_async(CandleHeartbeat.objects.create)(
                heartbeat_status=self.heartbeat_status,
                dhm_reception=dhm_reception,
                dhm_candle=dhm_candle,
                signal_type=k['i'],
                symbol=k['s'],
                open_price=kline_data['open_price'],
                high_price=kline_data['high_price'],
                low_price=kline_data['low_price'],
                close_price=kline_data['close_price'],
                volume=kline_data['volume']
            )
            
            logger.info(f"[SAVE] Signal sauve: {candle_signal}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde signal: {e}")
        
        # Diffuser le signal Heartbeat (existant + enrichi)
        await channel_layer.group_send(
            "heartbeat",
            {
                "type": "heartbeat_message",
                "message": kline_data
            }
        )
        
        self.stdout.write(
            f'[SIGNAL] {kline_data["symbol"]} {kline_data["timeframe"]} @ {kline_data["close_price"]} '
            f'[Sauve en DB]'
        )