# -*- coding: utf-8 -*-
"""
TEST SERVICE NATIF EN PRODUCTION
Envoie une requête get_balance pour valider le service
"""

import asyncio
import json
import uuid

async def test_native_service():
    print("=== TEST SERVICE NATIF ===")
    
    # Configuration Django AVANT imports
    import os
    import django
    
    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
        django.setup()
    
    # Import Redis
    try:
        from apps.core.services.redis_fallback import get_redis_client
        redis_client = await get_redis_client()
        await redis_client.ping()
        print("[OK] Redis connecté")
    except Exception as e:
        print(f"[ERROR] Redis: {e}")
        return
    
    # Vérifier broker disponible
    try:
        from apps.brokers.models import Broker
        from asgiref.sync import sync_to_async
        
        brokers = await sync_to_async(list)(Broker.objects.filter(is_active=True))
        if not brokers:
            print("[ERROR] Aucun broker actif trouvé")
            return
        
        # Chercher un broker Bitget de préférence
        bitget_broker = None
        for b in brokers:
            if b.exchange.lower() == 'bitget':
                bitget_broker = b
                break
        
        if bitget_broker:
            broker = bitget_broker
            print(f"[OK] Broker Bitget trouvé: {broker.name}")
        else:
            broker = brokers[0]
            print(f"[WARNING] Pas de broker Bitget, utilise: {broker.name} ({broker.exchange})")
        
    except Exception as e:
        print(f"[ERROR] Broker: {e}")
        return
    
    # Préparer requête
    request_id = str(uuid.uuid4())
    request = {
        'request_id': request_id,
        'action': 'get_balance',
        'params': {
            'broker_id': broker.id
        },
        'timestamp': asyncio.get_event_loop().time()
    }
    
    print(f"[TEST] Envoi requête get_balance pour broker {broker.id}...")
    
    try:
        # Vérifier queue avant
        queue_len_before = await redis_client.llen('ccxt_requests')
        print(f"[DEBUG] Queue ccxt_requests avant: {queue_len_before} éléments")
        
        # Envoyer requête
        await redis_client.rpush('ccxt_requests', json.dumps(request))
        
        # Vérifier queue après
        queue_len_after = await redis_client.llen('ccxt_requests')
        print(f"[OK] Requête envoyée: {request_id[:8]}...")
        print(f"[DEBUG] Queue ccxt_requests après: {queue_len_after} éléments")
        
        # Attendre un peu et re-vérifier
        await asyncio.sleep(1)
        queue_len_processing = await redis_client.llen('ccxt_requests')
        print(f"[DEBUG] Queue ccxt_requests après 1s: {queue_len_processing} éléments")
        
        # Attendre réponse (polling)
        response_key = f"ccxt_response_{request_id}"
        
        for i in range(100):  # 10 secondes max
            response_data = await redis_client.get(response_key)
            if response_data:
                response = json.loads(response_data)
                
                print(f"[OK] Réponse reçue après {i*0.1:.1f}s:")
                print(f"  Success: {response['success']}")
                if response['success']:
                    balances = response.get('data', {})
                    print(f"  Balances: {len(balances)} devises")
                    
                    # Afficher quelques balances non-nulles
                    non_zero = []
                    for currency, balance in balances.items():
                        if float(balance.get('free', 0)) > 0:
                            non_zero.append(f"{currency}: {balance['free']}")
                    
                    if non_zero:
                        print(f"  Non-zero: {', '.join(non_zero[:3])}")
                    else:
                        print("  Toutes les balances à zéro")
                else:
                    print(f"  Error: {response.get('error')}")
                
                return response
            
            await asyncio.sleep(0.1)
        
        print("[TIMEOUT] Pas de réponse après 10s")
        return None
        
    except Exception as e:
        print(f"[ERROR] Test: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await redis_client.close()

if __name__ == '__main__':
    asyncio.run(test_native_service())