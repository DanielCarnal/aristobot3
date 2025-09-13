import json
from channels.generic.websocket import AsyncWebsocketConsumer


class HeartbeatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("heartbeat", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("heartbeat", self.channel_name)

    async def receive(self, text_data):
        pass

    async def heartbeat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("stream", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("stream", self.channel_name)

    async def receive(self, text_data):
        pass

    async def stream_message(self, event):
        await self.send(text_data=json.dumps(event['message']))


class BacktestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("backtest", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("backtest", self.channel_name)

    async def receive(self, text_data):
        pass

    async def backtest_progress(self, event):
        await self.send(text_data=json.dumps(event['message']))


class UserAccountConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer pour User Account - Notifications marchés et tests connexion
    """
    async def connect(self):
        await self.channel_layer.group_add("user_account_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("user_account_updates", self.channel_name)

    async def receive(self, text_data):
        pass

    async def markets_loaded(self, event):
        """Notification succès chargement marchés"""
        await self.send(text_data=json.dumps({
            'type': 'markets_loaded',
            'broker_id': event['broker_id'],
            'exchange_name': event['exchange_name'],
            'market_count': event['market_count'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))

    async def markets_error(self, event):
        """Notification erreur chargement marchés"""
        await self.send(text_data=json.dumps({
            'type': 'markets_error',
            'broker_id': event['broker_id'],
            'error': event['error'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))