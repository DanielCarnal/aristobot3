# -*- coding: utf-8 -*-
"""
Test de l'API symbols/filtered/ directement
"""

import os
import django
import requests

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

def test_symbols_api():
    """Teste l'API symbols/filtered/ comme le ferait le frontend"""
    print("=== TEST API SYMBOLS/FILTERED ===")
    
    from apps.brokers.models import Broker
    
    # Récupérer un broker Bitget actif
    bitget_broker = Broker.objects.filter(exchange__iexact='bitget', is_active=True).first()
    if not bitget_broker:
        print("[ERROR] Aucun broker Bitget trouvé")
        return
    
    print(f"[BROKER] {bitget_broker.name} (ID: {bitget_broker.id})")
    
    # Simuler la requête frontend
    base_url = "http://localhost:8000"
    api_url = f"{base_url}/api/trading-manual/symbols/filtered/"
    
    # Paramètres comme le frontend
    params = {
        'broker_id': bitget_broker.id,
        'usdt': 'true',
        'usdc': 'false',
        'all': 'false',
        'search': '',
        'page_size': 200
    }
    
    try:
        # Test avec session (pour auth)
        session = requests.Session()
        
        # Essai avec cookies de session Django si disponibles
        print(f"[API] GET {api_url}")
        print(f"[PARAMS] {params}")
        
        response = session.get(api_url, params=params)
        
        print(f"[STATUS] {response.status_code}")
        print(f"[HEADERS] {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            symbols = data.get('symbols', [])
            print(f"[SUCCESS] {len(symbols)} symboles récupérés")
            print(f"[FIRST_5] {symbols[:5]}")
        elif response.status_code == 401:
            print("[AUTH] Authentication required - test avec Django shell")
        else:
            print(f"[ERROR] {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

def test_symbols_django_direct():
    """Test direct via Django sans HTTP"""
    print("\n=== TEST DJANGO DIRECT ===")
    
    from apps.brokers.models import Broker
    from apps.trading_manual.views import SymbolFilteredView
    from django.contrib.auth import get_user_model
    from django.test import RequestFactory
    
    User = get_user_model()
    
    # Récupérer un broker et user
    bitget_broker = Broker.objects.filter(exchange__iexact='bitget', is_active=True).first()
    if not bitget_broker:
        print("[ERROR] Aucun broker Bitget trouvé")
        return
        
    user = bitget_broker.user
    print(f"[USER] {user.username}")
    print(f"[BROKER] {bitget_broker.name} (ID: {bitget_broker.id})")
    
    # Créer une requête factice
    factory = RequestFactory()
    request = factory.get('/api/trading-manual/symbols/filtered/', {
        'broker_id': bitget_broker.id,
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
        print(f"[SUCCESS] {len(symbols)} symboles récupérés (total: {total})")
        print(f"[FIRST_5] {symbols[:5]}")
    else:
        print(f"[ERROR] {response.status_code}: {response.data}")

if __name__ == '__main__':
    test_symbols_api()
    test_symbols_django_direct()