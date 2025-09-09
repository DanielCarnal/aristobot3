# -*- coding: utf-8 -*-
"""
VÉRIFIER SI LE SERVICE NATIF TOURNE ENCORE
"""
import asyncio
import json

async def check_service():
    print("=== VÉRIFICATION SERVICE NATIF ===")
    
    # Configuration Django
    import os
    import django
    
    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
        django.setup()
    
    # Redis
    try:
        from apps.core.services.redis_fallback import get_redis_client
        redis_client = await get_redis_client()
        await redis_client.ping()
        print("[OK] Redis connecté")
        
        # Vérifier queue
        queue_len = await redis_client.llen('ccxt_requests')
        print(f"[INFO] Queue ccxt_requests: {queue_len} éléments")
        
        # Injecter message de test direct
        test_msg = {'test': 'ping', 'timestamp': asyncio.get_event_loop().time()}
        await redis_client.rpush('ccxt_requests', json.dumps(test_msg))
        print("[INFO] Message test injecté")
        
        # Vérifier après 2s
        await asyncio.sleep(2)
        queue_len_after = await redis_client.llen('ccxt_requests')
        print(f"[INFO] Queue après 2s: {queue_len_after} éléments")
        
        if queue_len_after < queue_len + 1:
            print("[OK] Service semble consommer les messages")
        else:
            print("[ERROR] Service ne consomme pas les messages")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_service())