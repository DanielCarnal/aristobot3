# -*- coding: utf-8 -*-
"""
Test specifique API avec broker ID 13 (celui utilise par le frontend)
"""

import os
import django

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

def test_broker_13_django_direct():
    """Test direct via Django pour broker 13"""
    print("=== TEST BROKER 13 DJANGO DIRECT ===")
    
    from apps.brokers.models import Broker
    from apps.trading_manual.views import SymbolFilteredView
    from django.contrib.auth import get_user_model
    from django.test import RequestFactory
    
    User = get_user_model()
    
    # Utiliser le broker 13 que le frontend utilise
    try:
        broker_13 = Broker.objects.get(id=13)
        user = broker_13.user
        print(f"[USER] {user.username}")
        print(f"[BROKER] {broker_13.name} (ID: {broker_13.id}, Exchange: {broker_13.exchange})")
        print(f"[ACTIVE] {broker_13.is_active}")
        
    except Broker.DoesNotExist:
        print("[ERROR] Broker ID 13 non trouve")
        return
    
    # Créer une requête factice pour broker 13
    factory = RequestFactory()
    request = factory.get('/api/trading-manual/symbols/filtered/', {
        'broker_id': 13,  # Utiliser le broker 13 exact
        'usdt': True,
        'usdc': False,
        'all': False,
        'search': '',
        'page_size': 200
    })
    request.user = user
    
    # Appeler la vue
    view = SymbolFilteredView()
    response = view.get(request)
    
    print(f"[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        symbols = response.data.get('symbols', [])
        total = response.data.get('total', 0)
        print(f"[SUCCESS] {len(symbols)} symboles recuperes (total: {total})")
        if symbols:
            print(f"[FIRST_5] {symbols[:5]}")
        else:
            print("[PROBLEME] Liste symbols vide malgre status 200!")
    else:
        print(f"[ERROR] {response.status_code}: {response.data}")

if __name__ == '__main__':
    test_broker_13_django_direct()