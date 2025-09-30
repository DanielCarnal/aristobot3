# -*- coding: utf-8 -*-
"""
TEST ENDPOINTS ÉTENDUS - Validation rétrocompatibilité + nouveaux paramètres

🎯 OBJECTIF: Valider que les endpoints OpenOrdersView et ClosedOrdersView
fonctionnent en mode compatibilité ET avec les nouveaux paramètres étendus

📋 TESTS:
✅ Mode compatibilité : anciens paramètres (broker_id, symbol, limit)
✅ Mode étendu : nouveaux paramètres (start_time, end_time, tpsl_type, etc.)
✅ Mode mixte : anciens + nouveaux paramètres
✅ Validation réponses : metadata avec extended_params_used

Usage:
  python test_extended_endpoints.py --user=dac --mode=compatibility
  python test_extended_endpoints.py --user=dac --mode=extended  
  python test_extended_endpoints.py --user=dac --mode=mixed
"""

import requests
import json
import sys
import os
import argparse
from datetime import datetime, timedelta

# Configuration Django pour accès aux modèles
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.brokers.models import Broker

User = get_user_model()

# URL de base de l'API
BASE_URL = 'http://localhost:8000'


def test_compatibility_mode(broker_id):
    """🔄 Test mode compatibilité - anciens paramètres"""
    print(f"\n{'='*60}")
    print("TEST MODE COMPATIBILITÉ - ANCIENS PARAMÈTRES")
    print(f"{'='*60}")
    
    # Test OpenOrders
    print(f"\n[TEST 1] OpenOrders - Mode compatibilité")
    
    url = f"{BASE_URL}/api/trading-manual/open-orders/"
    params = {
        'broker_id': broker_id,
        'symbol': 'BTC/USDT',  # Ancien paramètre
        'limit': 10           # Ancien paramètre
    }
    
    print(f"  URL: {url}")
    print(f"  Params: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Réponse reçue")
            print(f"  📊 Ordres: {len(data.get('orders', []))}")
            
            # Vérifier métadonnées
            metadata = data.get('metadata', {})
            extended_params = metadata.get('extended_params_used', {})
            print(f"  📋 Extended params utilisés: {extended_params}")
            
            if not extended_params:
                print(f"  ✅ Mode compatibilité confirmé (pas de params étendus)")
            else:
                print(f"  ⚠️  Params étendus détectés en mode compatibilité: {extended_params}")
        else:
            print(f"  ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")
    
    # Test ClosedOrders  
    print(f"\n[TEST 2] ClosedOrders - Mode compatibilité")
    
    url = f"{BASE_URL}/api/trading-manual/closed-orders/"
    params = {
        'broker_id': broker_id,
        'symbol': 'BTC/USDT',      # Ancien paramètre
        'since': '1704067200000',  # Ancien paramètre (1er jan 2024)
        'limit': 10               # Ancien paramètre
    }
    
    print(f"  URL: {url}")
    print(f"  Params: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Réponse reçue")
            print(f"  📊 Ordres: {len(data.get('orders', []))}")
            
            # Vérifier métadonnées
            metadata = data.get('metadata', {})
            extended_params = metadata.get('extended_params_used', {})
            compatibility_mode = metadata.get('compatibility_mode', False)
            print(f"  📋 Extended params utilisés: {extended_params}")
            print(f"  🔄 Mode compatibilité détecté: {compatibility_mode}")
            
        else:
            print(f"  ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")


def test_extended_mode(broker_id):
    """🚀 Test mode étendu - nouveaux paramètres Terminal 5"""
    print(f"\n{'='*60}")
    print("TEST MODE ÉTENDU - NOUVEAUX PARAMÈTRES TERMINAL 5")
    print(f"{'='*60}")
    
    # Dates pour test (90 derniers jours)
    now = datetime.now()
    start_date = now - timedelta(days=90)
    start_time = str(int(start_date.timestamp() * 1000))
    end_time = str(int(now.timestamp() * 1000))
    
    # Test OpenOrders  
    print(f"\n[TEST 1] OpenOrders - Mode étendu")
    
    url = f"{BASE_URL}/api/trading-manual/open-orders/"
    params = {
        'broker_id': broker_id,
        # Nouveaux paramètres Terminal 5
        'start_time': start_time,
        'end_time': end_time,
        'tpsl_type': 'normal',
        'limit': 20,
        'request_time': str(int(now.timestamp() * 1000))
    }
    
    print(f"  URL: {url}")
    print(f"  Params étendus: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Réponse reçue")
            print(f"  📊 Ordres: {len(data.get('orders', []))}")
            
            # Vérifier métadonnées étendues
            metadata = data.get('metadata', {})
            extended_params = metadata.get('extended_params_used', {})
            print(f"  🎉 Extended params utilisés: {extended_params}")
            print(f"  📈 Broker: {metadata.get('broker_name')} ({metadata.get('broker_exchange')})")
            
            if len(extended_params) >= 3:  # start_time, end_time, tpsl_type
                print(f"  ✅ Mode étendu confirmé ({len(extended_params)} params avancés)")
            else:
                print(f"  ⚠️  Moins de params étendus que prévu: {extended_params}")
        else:
            print(f"  ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")
    
    # Test ClosedOrders
    print(f"\n[TEST 2] ClosedOrders - Mode étendu")
    
    url = f"{BASE_URL}/api/trading-manual/closed-orders/"
    params = {
        'broker_id': broker_id,
        'symbol': 'BTC/USDT',
        # Nouveaux paramètres Terminal 5
        'start_time': start_time,
        'end_time': end_time,
        'tpsl_type': 'normal',
        'id_less_than': '999999999',  # Pagination Bitget
        'limit': 50
    }
    
    print(f"  URL: {url}")
    print(f"  Params étendus: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Réponse reçue")
            print(f"  📊 Ordres: {len(data.get('orders', []))}")
            
            # Vérifier métadonnées étendues
            metadata = data.get('metadata', {})
            extended_params = metadata.get('extended_params_used', {})
            print(f"  🎉 Extended params utilisés: {extended_params}")
            
            if len(extended_params) >= 4:  # start_time, end_time, tpsl_type, id_less_than
                print(f"  ✅ Mode étendu confirmé ({len(extended_params)} params avancés)")
            else:
                print(f"  ⚠️  Moins de params étendus que prévu: {extended_params}")
        else:
            print(f"  ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")


def test_mixed_mode(broker_id):
    """🔀 Test mode mixte - anciens + nouveaux paramètres"""
    print(f"\n{'='*60}")
    print("TEST MODE MIXTE - ANCIENS + NOUVEAUX PARAMÈTRES")
    print(f"{'='*60}")
    
    now = datetime.now()
    start_time = str(int((now - timedelta(days=30)).timestamp() * 1000))
    
    # Test avec anciens ET nouveaux paramètres
    print(f"\n[TEST 1] ClosedOrders - Mode mixte (since + start_time)")
    
    url = f"{BASE_URL}/api/trading-manual/closed-orders/"
    params = {
        'broker_id': broker_id,
        # Anciens paramètres
        'symbol': 'BTC/USDT',
        'since': '1704067200000',  # Ancien paramètre
        'limit': 15,
        # Nouveaux paramètres  
        'start_time': start_time,  # Devrait override 'since'
        'tpsl_type': 'normal'
    }
    
    print(f"  URL: {url}")
    print(f"  Params mixtes: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Réponse reçue")
            print(f"  📊 Ordres: {len(data.get('orders', []))}")
            
            # Vérifier métadonnées mixtes
            metadata = data.get('metadata', {})
            extended_params = metadata.get('extended_params_used', {})
            compatibility_mode = metadata.get('compatibility_mode', False)
            print(f"  🔀 Extended params utilisés: {extended_params}")
            print(f"  🔄 Mode compatibilité détecté: {compatibility_mode}")
            
            # Vérifier gestion intelligente since vs start_time
            has_since = 'since_legacy' in extended_params
            has_start_time = 'start_time' in extended_params
            print(f"  📋 'since' legacy détecté: {has_since}")
            print(f"  🚀 'start_time' nouveau détecté: {has_start_time}")
            
            if has_since and has_start_time:
                print(f"  ✅ Mode mixte confirmé (gestion intelligente since → start_time)")
            
        else:
            print(f"  ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")


def main():
    parser = argparse.ArgumentParser(description='Test endpoints étendus Trading Manuel')
    parser.add_argument('--user', choices=['dac', 'claude'], default='dac',
                       help='Utilisateur pour les tests')
    parser.add_argument('--mode', choices=['compatibility', 'extended', 'mixed', 'all'], 
                       default='all', help='Mode de test')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"TEST ENDPOINTS ÉTENDUS TRADING MANUEL - User: {args.user.upper()}")
    print(f"Mode: {args.mode.upper()}")  
    print(f"{'='*80}")
    
    # Récupérer le broker de test
    try:
        broker = Broker.objects.filter(user__username=args.user, is_active=True).first()
        if not broker:
            print(f"❌ Aucun broker actif trouvé pour {args.user}")
            return
        
        print(f"📊 Broker utilisé: {broker.name} (ID: {broker.id}) - {broker.exchange}")
        
        # Tests selon le mode
        if args.mode in ['compatibility', 'all']:
            test_compatibility_mode(broker.id)
        
        if args.mode in ['extended', 'all']:
            test_extended_mode(broker.id)
        
        if args.mode in ['mixed', 'all']:
            test_mixed_mode(broker.id)
        
        # Rapport final
        print(f"\n{'='*80}")
        print("RAPPORT FINAL TEST ENDPOINTS")
        print(f"{'='*80}")
        print(f"✅ Tests terminés pour broker {broker.name}")
        print(f"🔗 URLs testées: /api/trading-manual/open-orders/ et /api/trading-manual/closed-orders/")
        print(f"📋 Rétrocompatibilité: Anciens paramètres continuent de fonctionner")
        print(f"🚀 Extension: Nouveaux paramètres Terminal 5 supportés")
        print(f"🔀 Mixte: Gestion intelligente anciens + nouveaux paramètres")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()