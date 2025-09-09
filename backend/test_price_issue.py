# -*- coding: utf-8 -*-
"""
Test du problème de prix - erreur 'last' key
"""

import os
import django
import asyncio

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

async def test_price_issue():
    """Test du problème de récupération de prix"""
    print("=== TEST PROBLÈME PRIX 'last' key ===")
    
    from django.contrib.auth import get_user_model
    from apps.brokers.models import Broker
    from apps.trading_manual.services.trading_service import TradingService
    from asgiref.sync import sync_to_async
    
    User = get_user_model()
    
    try:
        # Récupérer utilisateur dev et broker 13 (async)
        dev_user = await sync_to_async(User.objects.get)(username='dev')
        broker_13 = await sync_to_async(Broker.objects.get)(id=13, user=dev_user)
        
        print(f"[USER] {dev_user.username}")
        print(f"[BROKER] {broker_13.name} (ID: {broker_13.id}, Exchange: {broker_13.exchange})")
        
        # Créer le service
        trading_service = TradingService(dev_user, broker_13)
        print(f"[SERVICE] TradingService créé")
        
        # Test 1: get_ticker direct via CCXTClient
        print(f"\n=== TEST 1: get_ticker direct ===")
        try:
            ticker = await trading_service.ccxt_client.get_ticker(broker_13.id, 'BTC/USDT')
            print(f"[TICKER RAW] {ticker}")
            print(f"[TICKER TYPE] {type(ticker)}")
            
            if ticker and 'last' in ticker:
                print(f"[TICKER SUCCESS] Prix BTC/USDT = {ticker['last']}")
            elif ticker and 'price' in ticker:
                print(f"[TICKER NATIVE] Prix BTC/USDT = {ticker['price']} (format natif)")
            else:
                print(f"[TICKER ERROR] Structure inattendue: {list(ticker.keys()) if ticker else 'None'}")
                
        except Exception as e:
            print(f"[TICKER ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: calculate_trade_value qui cause l'erreur
        print(f"\n=== TEST 2: calculate_trade_value (APRÈS NORMALISATION) ===")
        try:
            result = await trading_service.calculate_trade_value('BTC/USDT', quantity=0.001)
            print(f"[CALC SUCCESS] {result}")
            print(f"[FORMAT] Type result: {type(result)}")
            if 'current_price' in result:
                print(f"[PRICE] current_price trouvé: {result['current_price']}")
            else:
                print(f"[KEYS] Keys disponibles: {list(result.keys())}")
        except Exception as e:
            print(f"[CALC ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: get_tickers pour portfolio  
        print(f"\n=== TEST 3: get_tickers portfolio (APRÈS NORMALISATION) ===")
        try:
            prices = await trading_service.get_portfolio_prices(['BTC', 'ETH'])
            print(f"[PORTFOLIO SUCCESS] {prices}")
            if prices:
                print(f"[PORTFOLIO DETAILS] Assets avec prix:")
                for asset, price in prices.items():
                    print(f"  - {asset}: ${price}")
            else:
                print(f"[PORTFOLIO EMPTY] Aucun prix récupéré")
        except Exception as e:
            print(f"[PORTFOLIO ERROR] {e}")
            import traceback
            traceback.print_exc()
            
        # Test 4: NOUVEAU - Test direct fetch_tickers
        print(f"\n=== TEST 4: fetch_tickers direct ===")
        try:
            tickers_result = await trading_service.ccxt_client.get_tickers(broker_13.id, ['BTC/USDT', 'ETH/USDT'])
            print(f"[TICKERS SUCCESS] {tickers_result}")
            print(f"[TICKERS TYPE] {type(tickers_result)}")
            if isinstance(tickers_result, dict) and 'BTC/USDT' in tickers_result:
                btc_ticker = tickers_result['BTC/USDT']
                print(f"[BTC TICKER] Structure: {btc_ticker}")
                if 'last' in btc_ticker:
                    print(f"[BTC PRICE] Prix BTC standardisé: {btc_ticker['last']}")
        except Exception as e:
            print(f"[TICKERS ERROR] {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        print(f"[TRACEBACK] {traceback.format_exc()}")

if __name__ == '__main__':
    asyncio.run(test_price_issue())