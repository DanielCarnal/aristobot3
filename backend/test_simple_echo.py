# -*- coding: utf-8 -*-
"""
TEST ECHO SIMPLE - Vérifier si le service natif répond à quoi que ce soit
"""

import asyncio
import json

async def test_echo_service():
    print("=== TEST ECHO SIMPLE ===")
    
    # Configuration Django
    import os
    import django
    
    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
        django.setup()
    
    try:
        from apps.core.services.redis_fallback import get_redis_client
        redis_client = await get_redis_client()
        await redis_client.ping()
        print("[OK] Redis connecté")
        
        # Message PING ultra-simple
        ping_msg = {
            'request_id': 'PING_TEST_123',
            'action': 'PING',
            'params': {'test': True}
        }
        
        print("[PING] Envoi message PING...")
        await redis_client.rpush('ccxt_requests', json.dumps(ping_msg))
        
        # Attendre réponse
        for i in range(50):  # 5s max
            response_data = await redis_client.get('ccxt_response_PING_TEST_123')
            if response_data:
                print(f"[PONG] REPONSE RECUE: {response_data}")
                break
            await asyncio.sleep(0.1)
        else:
            print("[TIMEOUT] Aucune réponse au PING")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_echo_service())