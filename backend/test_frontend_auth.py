# -*- coding: utf-8 -*-
"""
Test pour simuler exactement ce que fait le frontend
"""

import os
import django
import requests

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

def test_frontend_auth_flow():
    """Simule exactement le flow d'authentification du frontend"""
    print("=== SIMULATION FRONTEND AUTH FLOW ===")
    
    # Étape 1: Créer une session comme le ferait le navigateur
    session = requests.Session()
    
    # Étape 2: Récupérer le token CSRF (comme le frontend)
    print("[1] Récupération token CSRF...")
    try:
        csrf_response = session.get('http://localhost:8000/api/auth/csrf-token/')
        print(f"    Status: {csrf_response.status_code}")
        csrf_cookies = dict(csrf_response.cookies)
        print(f"    CSRF Cookies: {csrf_cookies}")
    except Exception as e:
        print(f"    [ERROR] Erreur CSRF: {e}")
        return
    
    # Étape 3: Vérifier le status d'auth (comme checkAuth())
    print("\n[2] Vérification status auth...")
    try:
        auth_response = session.get('http://localhost:8000/api/auth/status/')
        print(f"    Status: {auth_response.status_code}")
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            print(f"    User: {auth_data.get('user')}")
            print(f"    Debug: {auth_data.get('debug')}")
        else:
            print(f"    Pas authentifié: {auth_response.text[:200]}")
    except Exception as e:
        print(f"    [ERROR] Erreur status: {e}")
    
    # Étape 4: Si pas auth, essayer debug login
    print("\n[3] Tentative debug login...")
    try:
        # Simuler debug login (comme debugLogin())
        debug_response = session.post(
            'http://localhost:8000/api/auth/debug-login/',
            json={}
        )
        print(f"    Status: {debug_response.status_code}")
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print(f"    Debug login OK: {debug_data.get('user')}")
        else:
            print(f"    Debug login échoué: {debug_response.text[:200]}")
    except Exception as e:
        print(f"    [ERROR] Erreur debug login: {e}")
    
    # Étape 5: Vérifier à nouveau le status après login
    print("\n[4] Re-vérification status après login...")
    try:
        auth_response2 = session.get('http://localhost:8000/api/auth/status/')
        print(f"    Status: {auth_response2.status_code}")
        if auth_response2.status_code == 200:
            auth_data2 = auth_response2.json()
            print(f"    User après login: {auth_data2.get('user')}")
            user_id = auth_data2.get('user', {}).get('id') if auth_data2.get('user') else None
            print(f"    User ID: {user_id}")
        else:
            print(f"    Toujours pas authentifié: {auth_response2.text[:200]}")
            return
    except Exception as e:
        print(f"    [ERROR] Erreur re-check: {e}")
        return
    
    # Étape 6: Test de l'API symbols avec la session authentifiée
    print("\n[5] Test API symbols avec session authentifiée...")
    try:
        symbols_response = session.get(
            'http://localhost:8000/api/trading-manual/symbols/filtered/',
            params={
                'broker_id': 13,
                'usdt': 'true',
                'usdc': 'false', 
                'all': 'false',
                'search': '',
                'page_size': 200
            }
        )
        
        print(f"    Status: {symbols_response.status_code}")
        print(f"    Headers: {dict(symbols_response.headers)}")
        
        if symbols_response.status_code == 200:
            data = symbols_response.json()
            symbols = data.get('symbols', [])
            total = data.get('total', 0)
            print(f"    [SUCCESS] {len(symbols)} symboles récupérés (total: {total})")
            if symbols:
                print(f"    Premiers symboles: {symbols[:3]}")
            else:
                print("    [PROBLÈME] Liste symbols vide malgré status 200!")
        elif symbols_response.status_code == 403:
            print(f"    [AUTH ERROR] 403: {symbols_response.text}")
        else:
            print(f"    [ERROR] {symbols_response.status_code}: {symbols_response.text[:200]}")
            
    except Exception as e:
        print(f"    [ERROR] Erreur test symbols: {e}")

if __name__ == '__main__':
    test_frontend_auth_flow()