# -*- coding: utf-8 -*-
"""
Debug communication Redis entre CCXTClient et Service CCXT
"""
import asyncio
import json
import uuid
import redis.asyncio as redis

async def test_redis_communication():
    """Test direct de la communication Redis"""
    print("🔧 Test communication Redis CCXT")
    print("=" * 50)
    
    try:
        # 1. Connexion Redis
        print("1. Test connexion Redis...")
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await redis_client.ping()
        print("✅ Redis connecté")
        
        # 2. Test envoi requête
        print("\n2. Test envoi requête...")
        request_id = str(uuid.uuid4())
        request = {
            'request_id': request_id,
            'action': 'get_balance',
            'params': {'broker_id': 15},
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await redis_client.rpush('ccxt_requests', json.dumps(request))
        print(f"✅ Requête envoyée: {request_id}")
        
        # 3. Vérifier queue
        print("\n3. Vérification queue Redis...")
        queue_length = await redis_client.llen('ccxt_requests')
        print(f"📋 Queue length: {queue_length}")
        
        # 4. Attendre réponse
        print(f"\n4. Attente réponse (30s max)...")
        response_key = f"ccxt_response_{request_id}"
        
        for i in range(300):  # 30s
            response_data = await redis_client.get(response_key)
            if response_data:
                response = json.loads(response_data)
                print(f"✅ Réponse reçue après {i*0.1:.1f}s:")
                print(f"   Success: {response.get('success')}")
                if response.get('success'):
                    print(f"   Data keys: {list(response.get('data', {}).keys())}")
                else:
                    print(f"   Error: {response.get('error')}")
                await redis_client.delete(response_key)
                break
            
            if i % 50 == 0:  # Log toutes les 5s
                print(f"   ⏳ Attente... {i*0.1:.1f}s")
            
            await asyncio.sleep(0.1)
        else:
            print("❌ Timeout - pas de réponse")
            
        # 5. État final queue
        final_queue_length = await redis_client.llen('ccxt_requests')
        print(f"\n📋 Queue finale: {final_queue_length}")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Assurez-vous que le service CCXT est démarré!")
    print()
    asyncio.run(test_redis_communication())