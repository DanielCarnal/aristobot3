# -*- coding: utf-8 -*-
"""
Test spécifique pour l'exécution des trades
"""
import asyncio
import json
import uuid
import redis.asyncio as redis

async def test_execute_trade():
    """Test d'exécution d'un trade"""
    print("Test execution trade - simulation place_order")
    print("=" * 50)
    
    try:
        # 1. Connexion Redis
        print("1. Test connexion Redis...")
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await redis_client.ping()
        print("✅ Redis connecté")
        
        # 2. Test place_order (simulate what execute_trade should send)
        print("\n2. Test place_order...")
        request_id = str(uuid.uuid4())
        request = {
            'request_id': request_id,
            'action': 'place_order',
            'params': {
                'broker_id': 13,  # Broker Bitget d'après les logs
                'symbol': 'BTC/USDT',
                'side': 'buy',
                'amount': 0.001,  # Petite quantité pour test
                'type': 'market'
            },
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await redis_client.rpush('ccxt_requests', json.dumps(request))
        print(f"✅ Requête envoyée: place_order BTC/USDT")
        print(f"📊 Paramètres: {request['params']}")
        
        # 3. Attendre réponse
        print(f"\n3. Attente réponse (120s max)...")
        response_key = f"ccxt_response_{request_id}"
        
        for i in range(1200):  # 120s
            response_data = await redis_client.get(response_key)
            if response_data:
                response = json.loads(response_data)
                print(f"✅ Réponse reçue après {i*0.1:.1f}s:")
                print(f"   Success: {response.get('success')}")
                
                if response.get('success'):
                    order = response.get('data', {})
                    print(f"   Order ID: {order.get('id')}")
                    print(f"   Symbol: {order.get('symbol')}")
                    print(f"   Side: {order.get('side')}")
                    print(f"   Amount: {order.get('amount')}")
                    print(f"   Price: {order.get('price')}")
                    print(f"   Status: {order.get('status')}")
                    print(f"   Filled: {order.get('filled')}")
                else:
                    print(f"   Erreur: {response.get('error')}")
                    
                await redis_client.delete(response_key)
                break
            
            if i % 100 == 0:  # Log toutes les 10s
                print(f"   Attente... {i*0.1:.1f}s")
            
            await asyncio.sleep(0.1)
        else:
            print("❌ Timeout - pas de réponse en 120s")
            
        await redis_client.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️  ATTENTION: Ce test va passer un vrai ordre sur Bitget!")
    print("Assurez-vous que le service CCXT est démarré!")
    print("Test pour broker_id=13 (Bitget)")
    print()
    
    # Demander confirmation
    confirm = input("Continuer avec le test (tapez 'oui'): ")
    if confirm.lower() == 'oui':
        asyncio.run(test_execute_trade())
    else:
        print("Test annulé")