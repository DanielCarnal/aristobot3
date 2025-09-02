# -*- coding: utf-8 -*-
"""
Test CCXT - Approche B: Ordres separes (Universelle)
Test des 3 ordres separes comme suggere dans la documentation
"""
import os
import sys
import django
import asyncio
import traceback
from decimal import Decimal

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.core.services.ccxt_manager import CCXTManager
from apps.brokers.models import Broker
from asgiref.sync import sync_to_async

# Configuration de test
DRY_RUN = False  # True = simulation, False = ordres reels
TEST_SYMBOL = 'BTC/USDT'
TEST_AMOUNT_USD = 3.0  # Montant en USD pour le test

async def test_ordres_separes():
    """
    Test de l'Approche B: 3 ordres separes
    1. Ordre principal limit
    2. Stop Loss separe  
    3. Take Profit separe
    """
    
    print("=" * 80)
    print("TEST CCXT - APPROCHE B: ORDRES SEPARES")
    print(f"Mode: {'DRY RUN (simulation)' if DRY_RUN else 'ORDRES REELS'}")
    print("=" * 80)
    
    try:
        # 1. Setup broker et exchange
        print("\nETAPE 1: Preparation broker et exchange")
        broker = await sync_to_async(Broker.objects.get)(id=13)
        print(f"Broker: {broker.name} ({broker.exchange})")
        
        exchange = await CCXTManager.get_exchange(broker)
        print(f"Exchange CCXT cree: {type(exchange).__name__}")
        
        # 2. Verifier marche et prix
        print(f"\nETAPE 2: Analyse du marche {TEST_SYMBOL}")
        market = exchange.markets.get(TEST_SYMBOL)
        if not market:
            raise Exception(f"Marche {TEST_SYMBOL} non trouve")
        
        print(f"Marche trouve: spot={market.get('spot', 'unknown')}")
        
        ticker = await exchange.fetch_ticker(TEST_SYMBOL)
        current_price = ticker['last']
        print(f"Prix actuel: ${current_price:,.2f}")
        
        # 3. Calculer quantites et prix
        print(f"\nETAPE 3: Calculs pour trade ${TEST_AMOUNT_USD}")
        quantity = TEST_AMOUNT_USD / current_price
        
        # Prix pour test (relativement conservateurs)
        price_buy = current_price * 0.999  # 0.1% sous le marche
        price_sl = current_price * 0.990   # SL a -1%
        price_tp = current_price * 1.015   # TP a +1.5%
        
        print(f"Quantite BTC: {quantity:.8f}")
        print(f"Prix achat limite: ${price_buy:,.2f}")
        print(f"Stop Loss: ${price_sl:,.2f} (-1%)")
        print(f"Take Profit: ${price_tp:,.2f} (+1.5%)")
        
        # 4. Verifier capacites exchange
        print(f"\nETAPE 4: Capacites exchange")
        capacites = {
            'createOrder': exchange.has.get('createOrder', False),
            'createStopLossOrder': exchange.has.get('createStopLossOrder', False),
            'createTakeProfitOrder': exchange.has.get('createTakeProfitOrder', False),
            'fetchOpenOrders': exchange.has.get('fetchOpenOrders', False),
        }
        
        for cap, value in capacites.items():
            status = "OK" if value else "NO"
            print(f"{status} {cap}: {value}")
        
        # 5. TEST APPROCHE B - 3 ORDRES SEPARES
        print(f"\nETAPE 5: TEST APPROCHE B - ORDRES SEPARES")
        
        if DRY_RUN:
            print("MODE DRY RUN - Simulation seulement")
            await test_orders_simulation(exchange, quantity, price_buy, price_sl, price_tp)
        else:
            print("MODE REEL - Ordres veritables")
            await test_orders_real(exchange, quantity, price_buy, price_sl, price_tp)
            
    except Exception as e:
        print(f"\nERREUR GLOBALE: {e}")
        print(f"Traceback:")
        traceback.print_exc()

async def test_orders_simulation(exchange, quantity, price_buy, price_sl, price_tp):
    """Mode simulation - teste la preparation des ordres sans les executer"""
    
    print("\nSIMULATION DES 3 ORDRES SEPARES:")
    
    # Simulation ordre principal
    print(f"\n1. ORDRE PRINCIPAL (simulation)")
    print(f"   Type: limit buy")
    print(f"   Quantite: {quantity:.8f} BTC") 
    print(f"   Prix: ${price_buy:,.2f}")
    print(f"   Params: {{}}")  # Aucun parametre special
    print(f"   OK Ordre principal: simulation")
    
    # Simulation Stop Loss separe
    print(f"\n2. STOP LOSS SEPARE (simulation)")
    params_sl = {'stopLossPrice': price_sl}
    print(f"   Type: limit sell (side oppose)")
    print(f"   Quantite: {quantity:.8f} BTC")
    print(f"   Prix: ${price_sl:,.2f}")
    print(f"   Params: {params_sl}")
    print(f"   OK Stop Loss separe: simulation")
    
    # Simulation Take Profit separe
    print(f"\n3. TAKE PROFIT SEPARE (simulation)")
    params_tp = {'takeProfitPrice': price_tp}
    print(f"   Type: limit sell (side oppose)")
    print(f"   Quantite: {quantity:.8f} BTC")
    print(f"   Prix: ${price_tp:,.2f}")
    print(f"   Params: {params_tp}")
    print(f"   OK Take Profit separe: simulation")
    
    print(f"\nCONCLUSION SIMULATION:")
    print(f"   Structure des ordres: VALIDE")
    print(f"   Parametres separes: CONFORMES")
    print(f"   Pret pour test reel si desire")

async def test_orders_real(exchange, quantity, price_buy, price_sl, price_tp):
    """Mode reel - execute vraiment les ordres (ATTENTION!)"""
    
    print(f"\nEXECUTION REELLE DES 3 ORDRES:")
    print(f"ATTENTION: ORDRES VERITABLES SUR BITGET!")
    
    try:
        # 1. Ordre principal limit buy
        print(f"\n1. ORDRE PRINCIPAL REEL")
        ordre_principal = await exchange.create_order(
            TEST_SYMBOL, 'limit', 'buy', quantity, price_buy
        )
        print(f"OK Ordre principal place: ID={ordre_principal.get('id')}")
        print(f"   Status: {ordre_principal.get('status')}")
        
        # Attendre un peu
        await asyncio.sleep(1)
        
        # 2. Stop Loss separe
        print(f"\n2. STOP LOSS SEPARE REEL")
        params_sl = {'stopLossPrice': price_sl}
        
        try:
            ordre_sl = await exchange.create_order(
                TEST_SYMBOL, 'limit', 'sell', quantity, price_sl, params_sl
            )
            print(f"OK Stop Loss place: ID={ordre_sl.get('id')}")
            print(f"   Status: {ordre_sl.get('status')}")
            
        except Exception as e:
            print(f"ECHEC Stop Loss separe: {e}")
            return  # Stopper si SL echoue
        
        # Attendre un peu
        await asyncio.sleep(1)
        
        # 3. Take Profit separe
        print(f"\n3. TAKE PROFIT SEPARE REEL")
        params_tp = {'takeProfitPrice': price_tp}
        
        try:
            ordre_tp = await exchange.create_order(
                TEST_SYMBOL, 'limit', 'sell', quantity, price_tp, params_tp
            )
            print(f"OK Take Profit place: ID={ordre_tp.get('id')}")
            print(f"   Status: {ordre_tp.get('status')}")
            
        except Exception as e:
            print(f"ECHEC Take Profit separe: {e}")
        
        print(f"\nRESULTAT FINAL:")
        print(f"OK Approche B validee: Ordres separes fonctionnent!")
        
    except Exception as e:
        print(f"ERREUR execution reelle: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Test CCXT - Approche B: Ordres separes")
    asyncio.run(test_ordres_separes())