import asyncio
import json
import websockets
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class Command(BaseCommand):
    help = 'Run Binance WebSocket heartbeat service'

    def handle(self, *args, **options):
        self.stdout.write('Starting Binance Heartbeat service...')
        asyncio.run(self.run_heartbeat())

    async def run_heartbeat(self):
        channel_layer = get_channel_layer()
        
        # Binance WebSocket stream URL for multiple symbols and timeframes
        stream_url = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m/btcusdt@kline_3m/btcusdt@kline_5m/btcusdt@kline_15m/btcusdt@kline_1h/btcusdt@kline_4h"
        
        while True:
            try:
                async with websockets.connect(stream_url) as websocket:
                    self.stdout.write('Connected to Binance WebSocket')
                    
                    async for message in websocket:
                        data = json.loads(message)
                        
                        # Send raw stream data
                        await channel_layer.group_send(
                            "stream",
                            {
                                "type": "stream_message",
                                "message": data
                            }
                        )
                        
                        # Process kline data for heartbeat
                        if 'k' in data and data['k']['x']:  # Closed candle
                            kline_data = {
                                'symbol': data['k']['s'],
                                'timeframe': data['k']['i'],
                                'open_time': data['k']['t'],
                                'close_time': data['k']['T'],
                                'open_price': float(data['k']['o']),
                                'close_price': float(data['k']['c']),
                                'high_price': float(data['k']['h']),
                                'low_price': float(data['k']['l']),
                                'volume': float(data['k']['v']),
                                'is_closed': data['k']['x']
                            }
                            
                            # Send heartbeat signal
                            await channel_layer.group_send(
                                "heartbeat",
                                {
                                    "type": "heartbeat_message",
                                    "message": kline_data
                                }
                            )
                            
                            self.stdout.write(f'Heartbeat: {kline_data["symbol"]} {kline_data["timeframe"]} closed at {kline_data["close_price"]}')
                        
            except Exception as e:
                self.stdout.write(f'WebSocket error: {e}')
                await asyncio.sleep(5)  # Wait before reconnecting