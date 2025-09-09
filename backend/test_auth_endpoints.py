# -*- coding: utf-8 -*-
"""
Test simple des endpoints d'authentification Django
"""

import os
import django

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

def test_auth_endpoints():
    """Test direct des vues Django d'authentification"""
    print("=== TEST ENDPOINTS AUTHENTIFICATION ===")
    
    from django.test import RequestFactory, Client
    from django.contrib.auth import get_user_model
    from apps.brokers.models import Broker
    
    User = get_user_model()
    
    # Utiliser Django test client
    client = Client()
    
    print("[1] Test endpoint status sans auth...")
    response = client.get('/api/auth/status/')
    print(f"    Status: {response.status_code}")
    print(f"    Content: {response.content.decode('utf-8')[:200]}")
    
    print("\n[2] Test debug config...")
    response = client.get('/api/auth/debug-config/')
    print(f"    Status: {response.status_code}")
    print(f"    Content: {response.content.decode('utf-8')[:200]}")
    
    print("\n[3] Test debug login...")
    response = client.post('/api/auth/debug-login/', content_type='application/json')
    print(f"    Status: {response.status_code}")
    print(f"    Content: {response.content.decode('utf-8')[:200]}")
    
    # Vérifier si on est maintenant connecté
    print("\n[4] Re-test status après debug login...")
    response = client.get('/api/auth/status/')
    print(f"    Status: {response.status_code}")
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode('utf-8'))
        print(f"    User: {data.get('user')}")
        user_id = data.get('user', {}).get('id') if data.get('user') else None
        
        if user_id:
            # Maintenant test symbols API avec utilisateur connecté
            print(f"\n[5] Test symbols API avec user {user_id}...")
            response = client.get('/api/trading-manual/symbols/filtered/', {
                'broker_id': 13,
                'usdt': 'true',
                'usdc': 'false',
                'all': 'false',
                'search': '',
                'page_size': 200
            })
            
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                data = json.loads(response.content.decode('utf-8'))
                symbols = data.get('symbols', [])
                print(f"    [SUCCESS] {len(symbols)} symboles trouvés")
                if len(symbols) == 0:
                    print("    [PROBLÈME] Liste vide!")
                else:
                    print(f"    Premiers: {symbols[:3]}")
            else:
                print(f"    [ERROR] {response.status_code}: {response.content.decode('utf-8')[:200]}")
    
    print("\n[6] Vérification directe broker 13...")
    try:
        dev_user = User.objects.get(username='dev')
        broker_13 = Broker.objects.get(id=13, user=dev_user)
        print(f"    Broker 13 OK: {broker_13.name} ({broker_13.exchange})")
        print(f"    Active: {broker_13.is_active}")
        print(f"    User: {broker_13.user.username}")
    except Exception as e:
        print(f"    [ERROR] Broker 13: {e}")

if __name__ == '__main__':
    test_auth_endpoints()