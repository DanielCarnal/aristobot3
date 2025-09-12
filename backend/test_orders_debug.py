# -*- coding: utf-8 -*-
"""
Test debug des ordres ouverts et fermés - Zone Ordres ouverts vide
"""

import os
import django
import asyncio

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

async def test_orders_debug():
    """Test debug ordres ouverts et fermés"""
    print("=== TEST DEBUG ORDRES ===")
    
    from django.contrib.auth import get_user_model
    from apps.brokers.models import Broker
    from apps.trading_manual.services.trading_service import TradingService
    from asgiref.sync import sync_to_async
    
    User = get_user_model()
    
    try:
        # Récupérer utilisateur dev et broker 13
        dev_user = await sync_to_async(User.objects.get)(username='dev')
        broker_13 = await sync_to_async(Broker.objects.get)(id=13, user=dev_user)
        
        print(f"[USER] {dev_user.username}")
        print(f"[BROKER] {broker_13.name} (ID: {broker_13.id}, Exchange: {broker_13.exchange})")
        
        # Initialiser TradingService
        trading_service = TradingService(dev_user, broker_13)
        
        # Test 1: Récupération ordres ouverts
        print(f"\n=== TEST 1: fetch_open_orders via Exchange Gateway ===")
        try:
            open_orders = await trading_service.get_open_orders()
            print(f"[OPEN ORDERS SUCCESS] Récupérés: {len(open_orders)} ordres")
            
            if open_orders:
                print(f"[FIRST ORDER] {open_orders[0]}")
                for i, order in enumerate(open_orders[:3]):  # Afficher max 3 ordres
                    print(f"  [{i+1}] {order.get('symbol')} {order.get('side')} {order.get('amount')} @ {order.get('price')} - Status: {order.get('status')}")
            else:
                print(f"[NO ORDERS] Aucun ordre ouvert trouvé")
                
        except Exception as e:
            print(f"[OPEN ORDERS ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Récupération ordres fermés (30 derniers jours)
        print(f"\n=== TEST 2: fetch_closed_orders via Exchange Gateway ===")
        try:
            # 30 derniers jours
            since_30_days = int((__import__('time').time() - (30 * 24 * 60 * 60)) * 1000)
            closed_orders = await trading_service.get_closed_orders(since=since_30_days, limit=10)
            print(f"[CLOSED ORDERS SUCCESS] Récupérés: {len(closed_orders)} ordres fermés")
            
            if closed_orders:
                print(f"[FIRST CLOSED ORDER] {closed_orders[0]}")
                for i, order in enumerate(closed_orders[:3]):  # Afficher max 3 ordres
                    print(f"  [{i+1}] {order.get('symbol')} {order.get('side')} {order.get('amount')} @ {order.get('price')} - Status: {order.get('status')}")
            else:
                print(f"[NO CLOSED ORDERS] Aucun ordre fermé trouvé")
                
        except Exception as e:
            print(f"[CLOSED ORDERS ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Vérification Exchange Gateway direct
        print(f"\n=== TEST 3: Test direct Exchange Gateway ===")
        try:
            # Test direct du ccxt_client
            balance = await trading_service.ccxt_client.get_balance(broker_13.id)
            print(f"[BALANCE TEST] Exchange Gateway réponse: {len(balance)} assets")
            
            # Test capabilities
            print(f"[EXCHANGE] {broker_13.exchange} - capabilities à vérifier")
            
        except Exception as e:
            print(f"[EXCHANGE GATEWAY ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        # Test 4: Vérification si Exchange supporte fetch_open_orders
        print(f"\n=== TEST 4: Verification capabilities Exchange ===")
        try:
            import ccxt
            exchange_class = getattr(ccxt, broker_13.exchange)
            exchange_instance = exchange_class()
            
            has_open_orders = exchange_instance.has.get('fetchOpenOrders', False)
            has_closed_orders = exchange_instance.has.get('fetchClosedOrders', False) or exchange_instance.has.get('fetchOrders', False)
            
            print(f"[CAPABILITIES] fetchOpenOrders: {has_open_orders}")
            print(f"[CAPABILITIES] fetchClosedOrders/fetchOrders: {has_closed_orders}")
            
            if not has_open_orders:
                print(f"⚠️ PROBLEME: {broker_13.exchange} ne supporte pas fetchOpenOrders!")
            if not has_closed_orders:
                print(f"⚠️ PROBLEME: {broker_13.exchange} ne supporte pas fetchClosedOrders!")
                
        except Exception as e:
            print(f"[CAPABILITIES ERROR] {e}")
            
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        print(f"[TRACEBACK] {traceback.format_exc()}")

if __name__ == '__main__':
    asyncio.run(test_orders_debug())