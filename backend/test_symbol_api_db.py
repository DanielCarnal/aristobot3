# -*- coding: utf-8 -*-
"""
Test API symbols depuis base de données (nouvelle architecture)
"""

import os
import django
import asyncio

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

from apps.trading_manual.services.trading_service import TradingService
from apps.brokers.models import Broker
from django.contrib.auth import get_user_model

User = get_user_model()

async def test_symbols_from_db():
    """Teste la récupération des symboles depuis la DB"""
    print("=== TEST API SYMBOLS DEPUIS BASE ===")
    
    # Récupérer un broker Bitget (avec sync_to_async pour tout)
    from asgiref.sync import sync_to_async
    
    @sync_to_async
    def get_bitget_broker():
        return Broker.objects.select_related('user').filter(
            exchange__iexact='bitget', 
            is_active=True
        ).first()
    
    bitget_broker = await get_bitget_broker()
    if not bitget_broker:
        print("[ERROR] Aucun broker Bitget trouvé")
        return
    
    user = bitget_broker.user
    print(f"[BROKER] {bitget_broker.name} - {bitget_broker.exchange}")
    
    # Créer le service
    trading_service = TradingService(user, bitget_broker)
    
    # Test 1: Tous les symboles
    print("\n--- TEST 1: Tous les symboles ---")
    result = await trading_service.get_available_symbols({'all': True})
    print(f"Total symboles 'all': {result['total']}")
    print(f"Premiers 5: {result['symbols'][:5]}")
    
    # Test 2: USDT seulement
    print("\n--- TEST 2: USDT seulement ---")
    result = await trading_service.get_available_symbols({'usdt': True})
    print(f"Total symboles USDT: {result['total']}")
    print(f"Premiers 5: {result['symbols'][:5]}")
    
    # Test 3: Recherche
    print("\n--- TEST 3: Recherche 'BTC' ---")
    result = await trading_service.get_available_symbols({'usdt': True, 'search': 'BTC'})
    print(f"Symboles contenant 'BTC': {result['total']}")
    print(f"Résultats: {result['symbols'][:10]}")

if __name__ == '__main__':
    asyncio.run(test_symbols_from_db())