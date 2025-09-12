# -*- coding: utf-8 -*-
"""
Test de l'exécution complète d'un ordre - Validation + Exécution
"""

import os
import django
import asyncio

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

async def test_complete_order_flow():
    """Test complet: validation + exécution d'ordre"""
    print("=== TEST EXECUTION COMPLETE ORDRE ===")
    
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
        
        # Test 1: Validation ordre réaliste (très petite quantité)
        print(f"\n=== TEST 1: Validation ordre BTC micro ===")
        symbol = 'BTC/USDT'
        side = 'buy'
        quantity = 0.00001  # Très petite quantité BTC
        order_type = 'market'
        
        validation = await trading_service.validate_trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type
        )
        
        print(f"[VALIDATION] valid={validation['valid']}")
        if validation['errors']:
            print(f"[ERRORS] {validation['errors']}")
        if validation['valid']:
            print(f"[PRICE] Prix actuel: ${validation.get('current_price', 'N/A')}")
            estimated_cost = quantity * validation.get('current_price', 0)
            print(f"[COST] Coût estimé: ${estimated_cost:.2f}")
        
        # Test 2: Préparation données trade
        if validation['valid']:
            print(f"\n=== TEST 2: Préparation trade_data ===")
            
            trade_data = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'order_type': order_type,
                'price': None,  # Market order
                'total_value': quantity * validation['current_price'],
                'stop_loss_price': None,
                'take_profit_price': None,
                'trigger_price': None
            }
            
            print(f"[TRADE_DATA] {trade_data}")
            
            # Test 3: TEST D'EXECUTION (ATTENTION : ORDRE RÉEL !)
            print(f"\n=== TEST 3: SIMULATION EXECUTION ===")
            print(f"ATTENTION: Ceci serait un ORDRE REEL sur {broker_13.exchange}")
            print(f"Quantite: {quantity} BTC (environ ${trade_data['total_value']:.2f})")
            print(f"Mode: {order_type.upper()}")
            
            # Pour la sécurité, on ne va PAS exécuter réellement
            print(f"EXECUTION SKIPPEE pour securite")
            print(f"Le code semble pret a executer l'ordre")
            
            # DECOMMENTER CI-DESSOUS POUR EXECUTION REELLE (A TES RISQUES !)
            # try:
            #     print(f"Debut execution...")
            #     trade_result = await trading_service.execute_trade(trade_data)
            #     print(f"Trade execute: ID {trade_result.id}")
            #     print(f"Status: {trade_result.status}")
            # except Exception as e:
            #     print(f"Erreur execution: {e}")
        else:
            print(f"\nValidation echouee, pas d'execution possible")
                
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        print(f"[TRACEBACK] {traceback.format_exc()}")

if __name__ == '__main__':
    asyncio.run(test_complete_order_flow())