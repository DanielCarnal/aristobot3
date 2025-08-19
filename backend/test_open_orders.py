# -*- coding: utf-8 -*-
"""
Test spécifique pour les ordres ouverts
"""
import asyncio
import json
import uuid
import redis.asyncio as redis

async def test_open_orders():
    """Test récupération des ordres ouverts"""
    print("Test recuperation ordres ouverts")
    print("=" * 50)
    
    try:
        # 1. Connexion Redis
        print("1. Test connexion Redis...")
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await redis_client.ping()
        print("Redis connecte")
        
        # 2. Test fetch_open_orders
        print("\n2. Test fetch_open_orders...")
        request_id = str(uuid.uuid4())
        request = {
            'request_id': request_id,
            'action': 'fetch_open_orders',
            'params': {'broker_id': 13},  # Broker Bitget d'après les logs
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await redis_client.rpush('ccxt_requests', json.dumps(request))
        print(f"Requete envoyee: fetch_open_orders pour broker_id=13")
        
        # 3. Attendre réponse
        print(f"\n3. Attente réponse (30s max)...")
        response_key = f"ccxt_response_{request_id}"
        
        for i in range(300):  # 30s
            response_data = await redis_client.get(response_key)
            if response_data:
                response = json.loads(response_data)
                print(f"Reponse recue apres {i*0.1:.1f}s:")
                print(f"   Success: {response.get('success')}")
                
                if response.get('success'):
                    orders = response.get('data', [])
                    print(f"   Nombre d'ordres ouverts: {len(orders)}")
                    
                    if orders:
                        print("\n   Details des ordres:")
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
                            print()
                    else:
                        print("   Aucun ordre ouvert trouve")
                        
                else:
                    print(f"   Erreur: {response.get('error')}")
                    
                await redis_client.delete(response_key)
                break
            
            if i % 50 == 0:  # Log toutes les 5s
                print(f"   Attente... {i*0.1:.1f}s")
            
            await asyncio.sleep(0.1)
        else:
            print("Timeout - pas de reponse")
            
        await redis_client.close()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Assurez-vous que le service CCXT est demarre!")
    print("Test pour broker_id=13 (Bitget)")
    print()
    asyncio.run(test_open_orders())