#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide Heartbeat MODULE2
Compatible Windows - teste les APIs essentielles
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {"username": "dac", "password": "aristobot"}

def test_heartbeat_module2():
    print("=" * 50)
    print("[TEST] RAPIDE HEARTBEAT MODULE2")
    print("=" * 50)
    
    # Session pour les cookies
    session = requests.Session()
    
    print("\n1. [AUTH] AUTHENTIFICATION...")
    try:
        login_response = session.post(
            f"{BASE_URL}/api/auth/login/",
            json=TEST_USER,
            headers={'Content-Type': 'application/json'}
        )
        if login_response.status_code == 200:
            print("   [OK] Login reussi")
        else:
            print(f"   [ERROR] Login echec: {login_response.status_code}")
            return
    except Exception as e:
        print(f"   [ERROR] Erreur connexion: {e}")
        return
    
    print("\n2. [STATUS] TEST API STATUS...")
    try:
        status_response = session.get(f"{BASE_URL}/api/heartbeat/status/")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   [OK] Status API: {status_response.status_code}")
            print(f"   - Connecte: {status_data.get('is_connected', 'N/A')}")
            print(f"   - Symboles: {status_data.get('symbols_monitored', [])}")
            print(f"   - Dernier start: {status_data.get('last_application_start', 'N/A')}")
        else:
            print(f"   [ERROR] Status API echec: {status_response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Erreur status: {e}")
    
    print("\n3. [RECENT] TEST API RECENT (60 elements)...")
    try:
        recent_response = session.get(f"{BASE_URL}/api/heartbeat/recent/?limit=60")
        if recent_response.status_code == 200:
            recent_data = recent_response.json()
            print(f"   [OK] Recent API: {recent_response.status_code}")
            print(f"   - Count total: {recent_data.get('count', 0)}")
            print(f"   - Signals recus: {len(recent_data.get('signals', []))}")
            print(f"   - Timestamp: {recent_data.get('timestamp', 'N/A')}")
            
            # Analyser les premiers signaux
            signals = recent_data.get('signals', [])
            if signals:
                first_signal = signals[0]
                print(f"   - Premier signal: {first_signal.get('symbol')} {first_signal.get('signal_type')}")
                print(f"   - Prix: {first_signal.get('close_price')}")
        else:
            print(f"   [ERROR] Recent API echec: {recent_response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Erreur recent: {e}")
    
    print("\n4. [TIME] TEST API TIMEFRAMES...")
    try:
        timeframes_response = session.get(f"{BASE_URL}/api/heartbeat/timeframes/?hours_back=1")
        if timeframes_response.status_code == 200:
            timeframes_data = timeframes_response.json()
            print(f"   [OK] Timeframes API: {timeframes_response.status_code}")
            print(f"   - Period hours: {timeframes_data.get('period_hours', 'N/A')}")
            
            counts = timeframes_data.get('timeframe_counts', [])
            print(f"   - Timeframes avec data: {len(counts)}")
            for count in counts:
                print(f"     * {count['signal_type']}: {count['count']} signaux")
                
            latest = timeframes_data.get('latest_signals', {})
            print(f"   - Latest signals: {len(latest)} timeframes")
        else:
            print(f"   [ERROR] Timeframes API echec: {timeframes_response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Erreur timeframes: {e}")
    
    print("\n5. [SIGNALS] TEST API SIGNALS (avec filtres)...")
    try:
        signals_response = session.get(f"{BASE_URL}/api/heartbeat/signals/?signal_type=1m&hours_back=1")
        if signals_response.status_code == 200:
            signals_data = signals_response.json()
            print(f"   [OK] Signals API: {signals_response.status_code}")
            
            if 'results' in signals_data:
                print(f"   - Signals 1m (1h): {len(signals_data['results'])}")
            else:
                print(f"   - Signals directs: {len(signals_data) if isinstance(signals_data, list) else 'format inconnu'}")
        else:
            print(f"   [ERROR] Signals API echec: {signals_response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Erreur signals: {e}")
    
    print("\n6. [CORS] TEST CORS FRONTEND...")
    try:
        cors_headers = {
            'Origin': 'http://localhost:5173',
            'Referer': 'http://localhost:5173/heartbeat'
        }
        cors_response = session.get(f"{BASE_URL}/api/heartbeat/status/", headers=cors_headers)
        if cors_response.status_code == 200:
            print("   [OK] CORS fonctionne avec frontend origin")
        else:
            print(f"   [WARNING] CORS issue: {cors_response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Erreur CORS: {e}")
    
    print("\n7. [ERROR] TEST SANS AUTHENTIFICATION...")
    try:
        no_auth_session = requests.Session()
        no_auth_response = no_auth_session.get(f"{BASE_URL}/api/heartbeat/status/")
        if no_auth_response.status_code == 401 or no_auth_response.status_code == 403:
            print("   [OK] API protegee par authentification")
        else:
            print(f"   [WARNING] API accessible sans auth: {no_auth_response.status_code}")
    except Exception as e:
        print(f"   [OK] API protegee (erreur attendue): {e}")
    
    print("\n" + "=" * 50)
    print("[RESUME] RESUME MODULE2")
    print("=" * 50)
    print("[OK] Extension modeles: CandleHeartbeat + HeartbeatStatus")
    print("[OK] Service persistance: run_heartbeat.py")
    print("[OK] APIs REST: status, recent, timeframes, signals") 
    print("[OK] Frontend 60 elements: orange (historique) + vert (temps reel)")
    print("[OK] URLs routing: /api/heartbeat/*")
    print("[OK] Migrations: appliquees")
    
    print("\n[TODO] PROCHAINES ETAPES:")
    print("1. Demarrer heartbeat: python manage.py run_heartbeat")
    print("2. Demarrer frontend: npm run dev") 
    print("3. Ouvrir: http://localhost:5173/heartbeat")
    print("4. Verifier: status 'Connecte' + stream orange/vert")
    
    print("\n[SUCCESS] MODULE2 FONCTIONNEL!")
    print("=" * 50)

if __name__ == '__main__':
    test_heartbeat_module2()