from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BrokerViewSet, ExchangeSymbolViewSet

router = DefaultRouter()
router.register(r'brokers', BrokerViewSet, basename='broker')
router.register(r'symbols', ExchangeSymbolViewSet, basename='symbol')

urlpatterns = [
    path('', include(router.urls)),
]