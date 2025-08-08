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