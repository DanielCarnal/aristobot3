from django.urls import re_path
from apps.core import consumers
from apps.trading_manual import consumers as trading_consumers

websocket_urlpatterns = [
    re_path(r'ws/heartbeat/$', consumers.HeartbeatConsumer.as_asgi()),
    re_path(r'ws/stream/$', consumers.StreamConsumer.as_asgi()),
    re_path(r'ws/backtest/$', consumers.BacktestConsumer.as_asgi()),
    re_path(r'ws/trading-manual/$', trading_consumers.TradingManualConsumer.as_asgi()),
    re_path(r'ws/open-orders/$', trading_consumers.OpenOrdersConsumer.as_asgi()),
    re_path(r'ws/trading-notifications/$', trading_consumers.TradingNotificationsConsumer.as_asgi()),
]