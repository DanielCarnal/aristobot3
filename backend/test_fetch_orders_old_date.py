# -*- coding: utf-8 -*-
"""
Test fetch_open_orders avec une date très ancienne pour voir tous les ordres
"""
import asyncio
import json
import uuid
import redis.asyncio as redis
from datetime import datetime

async def test_fetch_orders_old_date():
    """Test récupération ordres avec date ancienne"""
    print("Test fetch_open_orders avec date ancienne")
    print("=" * 50)
    
    try:
        # 1. Connexion Redis
        print("1. Test connexion Redis...")
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await redis_client.ping()
        print("OK Redis connecté")
        
        # 2. Test avec date très ancienne (2024-01-01)
        print("\n2. Test fetch_open_orders avec since=2024-01-01...")
        since_timestamp = int(datetime(2024, 1, 1).timestamp() * 1000)  # En millisecondes
        print(f"Since timestamp: {since_timestamp} ({datetime.fromtimestamp(since_timestamp/1000)})")
        
        request_id = str(uuid.uuid4())
        request = {
            'request_id': request_id,
            'action': 'fetch_open_orders',
            'params': {
                'broker_id': 13,
                'since': since_timestamp,
                'limit': 1000  # Grande limite
            },
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await redis_client.rpush('ccxt_requests', json.dumps(request))
        print(f"Requête envoyée: fetch_open_orders avec since={since_timestamp}")
        
        # 3. Attendre réponse
        print(f"\n3. Attente réponse (30s max)...")
        response_key = f"ccxt_response_{request_id}"
        
        for i in range(300):  # 30s
            response_data = await redis_client.get(response_key)
            if response_data:
                response = json.loads(response_data)
                print(f"Réponse reçue après {i*0.1:.1f}s:")
                print(f"   Success: {response.get('success')}")
                
                if response.get('success'):
                    orders = response.get('data', [])
                    print(f"   Nombre d'ordres avec date ancienne: {len(orders)}")
                    
                    if orders:
                        print("\n   Détails des ordres trouvés:")
                        for idx, order in enumerate(orders):
                            print(f"     Ordre {idx+1}:")
                            print(f"       ID: {order.get('id')}")
                            print(f"       Symbol: {order.get('symbol')}")
                            print(f"       Side: {order.get('side')}")
                            print(f"       Type: {order.get('type')}")
                            print(f"       Amount: {order.get('amount')}")
                            print(f"       Price: {order.get('price')}")
                            print(f"       Status: {order.get('status')}")
                            print(f"       Timestamp: {order.get('timestamp')}")
                            # Convertir timestamp si disponible
                            if order.get('timestamp'):
                                dt = datetime.fromtimestamp(order.get('timestamp') / 1000)
                                print(f"       Date: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                            print()
                    else:
                        print("   Aucun ordre trouvé avec date ancienne")
                        
                else:
                    print(f"   Erreur: {response.get('error')}")
                    
                await redis_client.delete(response_key)
                break
            
            if i % 50 == 0:  # Log toutes les 5s
                print(f"   Attente... {i*0.1:.1f}s")
            
            await asyncio.sleep(0.1)
        else:
            print("Timeout - pas de réponse")
        
        # 4. Test spécifique pour BTC/USDT
        print(f"\n4. Test fetch_open_orders pour BTC/USDT seulement...")
        request_id2 = str(uuid.uuid4())
        request2 = {
            'request_id': request_id2,
            'action': 'fetch_open_orders',
            'params': {
                'broker_id': 13,
                'symbol': 'BTC/USDT',
                'since': since_timestamp,
                'limit': 1000
            },
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await redis_client.rpush('ccxt_requests', json.dumps(request2))
        print(f"Requête envoyée: fetch_open_orders pour BTC/USDT")
        
        response_key2 = f"ccxt_response_{request_id2}"
        
        for i in range(300):  # 30s
            response_data = await redis_client.get(response_key2)
            if response_data:
                response = json.loads(response_data)
                print(f"Réponse BTC reçue après {i*0.1:.1f}s:")
                print(f"   Success: {response.get('success')}")
                
                if response.get('success'):
                    orders = response.get('data', [])
                    print(f"   Ordres BTC/USDT trouvés: {len(orders)}")
                    
                    if orders:
                        for idx, order in enumerate(orders):
                            print(f"     Ordre BTC {idx+1}: ID={order.get('id')} Date={datetime.fromtimestamp(order.get('timestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        print("   Aucun ordre BTC/USDT trouvé")
                else:
                    print(f"   Erreur BTC: {response.get('error')}")
                    
                await redis_client.delete(response_key2)
                break
            
            await asyncio.sleep(0.1)
            
        await redis_client.close()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Test pour récupérer ordres anciens avec paramètre 'since'")
    print("Recherche de l'ordre BTC du 2025-02-28")
    print()
    asyncio.run(test_fetch_orders_old_date())