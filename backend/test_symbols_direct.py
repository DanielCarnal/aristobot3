# -*- coding: utf-8 -*-
"""
Test direct de la méthode get_available_symbols
"""

import os
import django
import asyncio

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

async def test_symbols_method():
    """Test direct de TradingService.get_available_symbols"""
    print("=== TEST DIRECT get_available_symbols ===")
    
    from django.contrib.auth import get_user_model
    from apps.brokers.models import Broker
    from apps.trading_manual.services.trading_service import TradingService
    
    User = get_user_model()
    
    try:
        # Récupérer utilisateur dev et broker 13
        dev_user = User.objects.get(username='dev')
        broker_13 = Broker.objects.get(id=13, user=dev_user)
        
        print(f"[USER] {dev_user.username}")
        print(f"[BROKER] {broker_13.name} (ID: {broker_13.id}, Exchange: {broker_13.exchange})")
        
        # Créer le service
        trading_service = TradingService(dev_user, broker_13)
        print(f"[SERVICE] TradingService créé")
        
        # Tester avec les mêmes filtres que le frontend
        filters = {
            'usdt': True,
            'usdc': False,
            'all': False,
            'search': ''
        }
        
        print(f"[FILTERS] {filters}")
        print(f"[TEST] Appel get_available_symbols...")
        
        # TIMEOUT personnalisé pour éviter le hang
        import asyncio
        result = await asyncio.wait_for(
            trading_service.get_available_symbols(filters, 1, 200),
            timeout=10.0  # 10 secondes max
        )
        
        print(f"[SUCCESS] {len(result['symbols'])} symboles récupérés")
        print(f"[TOTAL] {result['total']} total")
        print(f"[PREMIERS] {result['symbols'][:5]}")
        
    except asyncio.TimeoutError:
        print("[TIMEOUT] La méthode get_available_symbols a pris plus de 10 secondes!")
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        print(f"[TRACEBACK] {traceback.format_exc()}")

if __name__ == '__main__':
    asyncio.run(test_symbols_method())