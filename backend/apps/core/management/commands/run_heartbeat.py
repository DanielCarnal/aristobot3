# -*- coding: utf-8 -*-
import asyncio
import json
import websockets
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from django.utils import timezone
from apps.core.models import HeartbeatStatus, CandleHeartbeat
from loguru import logger
from apps.core.services.loguru_config import setup_loguru


class Command(BaseCommand):
    help = 'Run Binance WebSocket heartbeat service avec persistance'

    def __init__(self):
        super().__init__()
        self.heartbeat_status = None

    def handle(self, *args, **options):
        setup_loguru("terminal2")
        self.stdout.write('Starting Enhanced Heartbeat service...')

        self.heartbeat_status, created = HeartbeatStatus.objects.get_or_create(
            id=1,
            defaults={
                'is_connected': False,
                'symbols_monitored': ['BTCUSDT']
            }
        )

        self.heartbeat_status.record_start()
        logger.info(
            "Service Heartbeat demarre",
            start_time=self.heartbeat_status.last_application_start.isoformat()
        )

        try:
            asyncio.run(self.run_heartbeat())
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            logger.error("Erreur critique", error=str(e))
            self.shutdown()

    def shutdown(self):
        if self.heartbeat_status:
            self.heartbeat_status.record_stop()
            logger.info(
                "Service Heartbeat arrete",
                stop_time=self.heartbeat_status.last_application_stop.isoformat()
            )

    async def run_heartbeat(self):
        channel_layer = get_channel_layer()

        stream_url = (
            "wss://stream.binance.com:9443/ws/"
            "btcusdt@kline_1m/btcusdt@kline_3m/btcusdt@kline_5m/"
            "btcusdt@kline_15m/btcusdt@kline_1h/btcusdt@kline_4h"
        )

        while True:
            try:
                async with websockets.connect(stream_url) as websocket:
                    logger.info("Connexion WebSocket Binance etablie")
                    self.heartbeat_status.is_connected = True
                    await sync_to_async(self.heartbeat_status.save)()

                    async for message in websocket:
                        await self.process_message(message, channel_layer)

            except Exception as e:
                logger.warning(
                    "Perte connexion WebSocket Binance",
                    error=str(e),
                    reconnect_delay="5s"
                )
                self.heartbeat_status.is_connected = False
                self.heartbeat_status.last_error = str(e)
                await sync_to_async(self.heartbeat_status.save)()
                await asyncio.sleep(5)

    async def process_message(self, message, channel_layer):
        try:
            data = json.loads(message)

            # Diffuser le stream brut vers le frontend
            await channel_layer.group_send(
                "stream",
                {"type": "stream_message", "message": data}
            )

            # Traiter les bougies fermees
            if 'k' in data and data['k']['x']:
                await self.process_closed_candle(data, channel_layer)

        except Exception as e:
            logger.error("Erreur traitement message WebSocket", error=str(e))

    async def process_closed_candle(self, data, channel_layer):
        k = data['k']
        dhm_reception = timezone.now()
        dhm_candle = timezone.datetime.fromtimestamp(k['T'] / 1000, tz=timezone.utc)

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

        # Sauvegarde en base de donnees
        try:
            await sync_to_async(CandleHeartbeat.objects.create)(
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

            logger.bind(
                symbol=k['s'],
                timeframe=k['i'],
                close_price=kline_data['close_price'],
                candle_time=dhm_candle.isoformat(),
            ).info(f"Signal {k['i']} sauve: {k['s']} @ {kline_data['close_price']}")

        except Exception as e:
            logger.bind(symbol=k['s'], timeframe=k['i']).error(
                "Erreur sauvegarde signal DB", error=str(e)
            )

        # Diffuser le signal Heartbeat vers Terminal 3 et Frontend
        await channel_layer.group_send(
            "heartbeat",
            {"type": "heartbeat_message", "message": kline_data}
        )
