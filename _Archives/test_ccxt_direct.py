# -*- coding: utf-8 -*-
"""
Test CCXT direct sans architecture - Broker 13, BTC/USDT, Stop Loss
"""
import os
import sys
import django
import asyncio
import ccxt.async_support as ccxt
from decimal import Decimal

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.brokers.models import Broker
from cryptography.fernet import Fernet
from django.conf import settings

async def test_bitget_stop_loss():
    """Test Stop Loss direct avec CCXT sans notre architecture"""
    
    try:
        # 1. Récupérer broker 13 depuis DB (version async)
        print("Recuperation broker 13...")
        from asgiref.sync import sync_to_async
        broker = await sync_to_async(Broker.objects.get)(id=13)
        print(f"Broker trouve: {broker.name} ({broker.exchange})")
        
        # 2. TEMPORAIRE - demander credentials direct (fatigue)
        print("Pour ce test, j'ai besoin des credentials Bitget:")
        print("API Key:")
        api_key = input().strip()
        print("Secret:")
        api_secret = input().strip() 
        print("Passphrase:")
        api_password = input().strip()
        
        # 3. Creer instance CCXT directe
        if broker.exchange.lower() == 'bitget':
            exchange = ccxt.bitget({
                'apiKey': api_key,
                'secret': api_secret,
                'password': api_password,
                'sandbox': broker.is_testnet,
                'enableRateLimit': True,
            })
        else:
            print(f"Exchange {broker.exchange} non supporte dans ce test")
            return
        
        # 4. Charger les marches
        print("Chargement des marches...")
        await exchange.load_markets()
        
        # 5. Verifier le marche BTC/USDT
        symbol = 'BTC/USDT'
        if symbol not in exchange.markets:
            print(f"Symbole {symbol} non trouve")
            return
            
        market = exchange.markets[symbol]
        print(f"Marche {symbol}: type={market.get('type')}, spot={market.get('spot')}")
        
        # 6. Recuperer le prix actuel
        ticker = await exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        print(f"Prix actuel {symbol}: {current_price}")
        
        # 7. Calculer la quantite pour 3$
        amount_usd = 3.0
        quantity = amount_usd / current_price
        print(f"Quantite calculee pour 3$: {quantity:.8f} BTC")
        
        # 8. TEST 1: Structure imbriquee comme dans les issues GitHub
        print("\nTEST 1: Structure imbriquee stopLoss")
        stop_loss_price = 101000  # Prix demande
        
        params = {
            'stopLoss': {
                'triggerPrice': stop_loss_price,
                'price': stop_loss_price
            }
        }
        
        print(f"Test create_order avec params: {params}")
        
        try:
            result = await exchange.create_order(symbol, 'market', 'sell', quantity, None, params)
            print(f"TEST 1 SUCCES: {result}")
        except Exception as e:
            print(f"TEST 1 ECHEC: {e}")
        
        # 9. TEST 2: Structure alternative (flat)
        print("\nTEST 2: Structure plate stopLossPrice")
        
        params2 = {
            'stopLossPrice': stop_loss_price
        }
        
        print(f"Test create_order avec params: {params2}")
        
        try:
            result2 = await exchange.create_order(symbol, 'market', 'sell', quantity, None, params2)
            print(f"TEST 2 SUCCES: {result2}")
        except Exception as e:
            print(f"TEST 2 ECHEC: {e}")
        
        # 10. TEST 3: API specialisee create_stop_loss_order
        print("\nTEST 3: API specialisee create_stop_loss_order")
        
        try:
            result3 = await exchange.create_stop_loss_order(symbol, 'market', 'sell', quantity, None, stop_loss_price)
            print(f"TEST 3 SUCCES: {result3}")
        except Exception as e:
            print(f"TEST 3 ECHEC: {e}")
        
        # 11. Verifier les capacites de l'exchange
        print(f"\nExchange capabilities:")
        print(f"   - has.createStopLossOrder: {exchange.has.get('createStopLossOrder', False)}")
        print(f"   - has.createTakeProfitOrder: {exchange.has.get('createTakeProfitOrder', False)}")
        print(f"   - has.createTriggerOrder: {exchange.has.get('createTriggerOrder', False)}")
        
        await exchange.close()
        
    except Exception as e:
        print(f"Erreur globale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Test CCXT direct - Broker 13, BTC/USDT, Stop Loss")
    asyncio.run(test_bitget_stop_loss())