#!/usr/bin/env python
"""
Diagnostic du comportement des marchés CCXT
Vérifier pourquoi KuCoin recharge ses marchés
"""
import os
import sys
import django
import asyncio
import time
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.brokers.models import Broker
from apps.core.services.ccxt_manager import CCXTManager

async def debug_markets_behavior():
    print("DIAGNOSTIC COMPORTEMENT MARCHES CCXT")
    print("=" * 60)
    
    try:
        broker_13 = await django.contrib.auth.models.User.objects.aget(id=13)
        broker_15 = await django.contrib.auth.models.User.objects.aget(id=15)
    except:
        from asgiref.sync import sync_to_async
        broker_13 = await sync_to_async(Broker.objects.get)(id=13)
        broker_15 = await sync_to_async(Broker.objects.get)(id=15)
    
    for broker in [broker_13, broker_15]:
        print(f"\n=== BROKER {broker.id}: {broker.name} ({broker.exchange}) ===")
        
        try:
            # 1. Obtenir l'exchange depuis le manager
            exchange = await CCXTManager.get_exchange(broker)
            
            # 2. Vérifier l'état des marchés
            print(f"1. État initial de exchange.markets:")
            if hasattr(exchange, 'markets') and exchange.markets:
                markets_count = len(exchange.markets)
                print(f"   OK {markets_count} marches en cache")
                sample_markets = list(exchange.markets.keys())[:5]
                print(f"   Echantillon: {sample_markets}")
            else:
                print(f"   ERROR Aucun marche en cache (markets = {getattr(exchange, 'markets', 'undefined')})")
            
            # 3. Test d'accès aux marchés (ce que fait get_markets)
            print(f"\n2. Test accès exchange.markets (simulation get_markets):")
            start_time = time.time()
            
            markets_access = exchange.markets
            access_duration = time.time() - start_time
            
            if markets_access:
                print(f"   OK Acces immediat: {access_duration:.3f}s")
                print(f"   Marches disponibles: {len(markets_access)}")
            else:
                print(f"   ERROR Aucun marche accessible: {access_duration:.3f}s")
            
            # 4. Forcer un fetch_markets et comparer
            print(f"\n3. Test fetch_markets() direct:")
            start_time = time.time()
            
            fetched_markets = await exchange.fetch_markets()
            fetch_duration = time.time() - start_time
            
            print(f"   Duree fetch: {fetch_duration:.3f}s")
            print(f"   Marches fetches: {len(fetched_markets) if fetched_markets else 0}")
            
            # 5. Comparer cache vs fetch
            if markets_access and fetched_markets:
                cache_count = len(markets_access)
                fetch_count = len(fetched_markets)
                print(f"\n4. Comparaison cache vs fetch:")
                print(f"   Cache: {cache_count} marches")
                print(f"   Fetch: {fetch_count} marches")
                
                if cache_count != fetch_count:
                    print(f"   WARNING DIFFERENCE detectee! ({abs(cache_count - fetch_count)} marches)")
                else:
                    print(f"   OK Coherence cache/fetch")
            
            # 6. Vérifier les propriétés internes CCXT
            print(f"\n5. Proprietes internes CCXT:")
            print(f"   markets_by_id: {'OK' if hasattr(exchange, 'markets_by_id') and exchange.markets_by_id else 'ERROR'}")
            print(f"   symbols: {'OK' if hasattr(exchange, 'symbols') and exchange.symbols else 'ERROR'}")
            print(f"   currencies: {'OK' if hasattr(exchange, 'currencies') and exchange.currencies else 'ERROR'}")
            
            # 7. Vérifier si load_markets a été appelé
            print(f"\n6. État load_markets:")
            if hasattr(exchange, 'loaded_markets'):
                print(f"   loaded_markets: {exchange.loaded_markets}")
            else:
                print(f"   loaded_markets: propriété non disponible")
                
            # 8. Test spécifique exchanges lents
            if broker.exchange in ['kucoin', 'okx', 'gate']:
                print(f"\n7. Tests spécifiques {broker.exchange}:")
                
                # Test sous-compte
                if broker.subaccount_name:
                    print(f"   Sous-compte configure: {broker.subaccount_name}")
                    print(f"   WARNING Les sous-comptes peuvent affecter la mise en cache")
                
                # Test rate limit
                if hasattr(exchange, 'rateLimit'):
                    print(f"   Rate limit: {exchange.rateLimit}ms")
                
                # Test options
                if hasattr(exchange, 'options'):
                    relevant_options = {k: v for k, v in exchange.options.items() 
                                       if k in ['sandboxMode', 'defaultType', 'defaultSubAccount']}
                    print(f"   Options: {relevant_options}")
            
            print(f"\n{'='*50}")
                
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_markets_behavior())