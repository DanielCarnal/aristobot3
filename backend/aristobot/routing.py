from django.urls import re_path
from apps.core import consumers

websocket_urlpatterns = [
    re_path(r'ws/heartbeat/$', consumers.HeartbeatConsumer.as_asgi()),
    re_path(r'ws/stream/$', consumers.StreamConsumer.as_asgi()),
    re_path(r'ws/backtest/$', consumers.BacktestConsumer.as_asgi()),
]