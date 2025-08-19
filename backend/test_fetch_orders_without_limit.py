# -*- coding: utf-8 -*-
"""
Test fetch_open_orders sans limite pour voir tous les ordres
"""
import asyncio
import json
import uuid
import redis.asyncio as redis

async def test_fetch_all_orders():
    """Test récupération de TOUS les ordres ouverts"""
    print("Test fetch_open_orders sans limite")
    print("=" * 50)
    
    try:
        # 1. Connexion Redis
        print("1. Test connexion Redis...")
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await redis_client.ping()
        print("OK Redis connecté")
        
        # 2. Test fetch_open_orders SANS limite
        print("\n2. Test fetch_open_orders SANS limite...")
        request_id = str(uuid.uuid4())
        request = {
            'request_id': request_id,
            'action': 'fetch_open_orders',
            'params': {'broker_id': 13},  # Pas de limit ni since
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await redis_client.rpush('ccxt_requests', json.dumps(request))
        print(f"Requête envoyée: fetch_open_orders SANS limite")
        
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
                    print(f"   Nombre total d'ordres ouverts: {len(orders)}")
                    
                    if orders:
                        print("\n   Détails de TOUS les ordres:")
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
                                import datetime
                                dt = datetime.datetime.fromtimestamp(order.get('timestamp') / 1000)
                                print(f"       Date: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                            print()
                    else:
                        print("   Aucun ordre ouvert trouvé")
                        
                else:
                    print(f"   Erreur: {response.get('error')}")
                    
                await redis_client.delete(response_key)
                break
            
            if i % 50 == 0:  # Log toutes les 5s
                print(f"   Attente... {i*0.1:.1f}s")
            
            await asyncio.sleep(0.1)
        else:
            print("Timeout - pas de réponse")
            
        await redis_client.close()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Test pour voir TOUS les ordres ouverts sur Bitget")
    print("Sans limitation de nombre ou de date")
    print()
    asyncio.run(test_fetch_all_orders())