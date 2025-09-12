# -*- coding: utf-8 -*-
"""
Test du problème de validation dans TradingService - Format incompatible
"""

import os
import django
import asyncio

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

async def test_trading_validation():
    """Test du problème de validation - format balance incompatible"""
    print("=== TEST VALIDATION TRADING MANUEL ===")
    
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
        
        # Test 1: Récupération directe balance pour voir le format
        print(f"\n=== TEST 1: Format balance reçu ===")
        trading_service = TradingService(dev_user, broker_13)
        balance = await trading_service.get_balance()
        print(f"[FORMAT BALANCE] {balance}")
        
        # Test 2: validate_trade avec un ordre simple
        print(f"\n=== TEST 2: validate_trade BUY BTC/USDT ===")
        try:
            validation = await trading_service.validate_trade(
                symbol='BTC/USDT',
                side='buy', 
                quantity=0.0001,  # Petite quantité
                order_type='market',
                price=None
            )
            print(f"[VALIDATION SUCCESS] {validation}")
        except Exception as e:
            print(f"[VALIDATION ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: validate_trade avec ordre limite
        print(f"\n=== TEST 3: validate_trade LIMIT BTC/USDT ===")
        try:
            validation = await trading_service.validate_trade(
                symbol='BTC/USDT',
                side='buy', 
                quantity=0.0001,
                order_type='limit',
                price=50000  # Prix limite artificiel
            )
            print(f"[VALIDATION LIMIT SUCCESS] {validation}")
        except Exception as e:
            print(f"[VALIDATION LIMIT ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        # Test 4: Analyser le problème de format
        print(f"\n=== TEST 4: Analyse format problématique ===")
        print(f"[FORMAT RECU] Structure: {list(balance.keys()) if balance else 'None'}")
        if balance and 'BTC' in balance:
            print(f"[BTC DATA] {balance['BTC']}")
        if balance and 'USDT' in balance:
            print(f"[USDT DATA] {balance['USDT']}")
        
        print(f"\n[FORMAT ATTENDU] Structure: {{'free': {{'BTC': X}}, 'total': {{'BTC': Y}}}}")
        print(f"[PROBLEME IDENTIFIE] validate_trade utilise format CCXT legacy mais reçoit format natif!")
                
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        print(f"[TRACEBACK] {traceback.format_exc()}")

if __name__ == '__main__':
    asyncio.run(test_trading_validation())