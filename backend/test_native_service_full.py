# -*- coding: utf-8 -*-
"""
TEST COMPLET SERVICE NATIF - Validation avec vraie requête get_balance
"""

import asyncio
import json

async def test_native_service_complete():
    print("=== TEST COMPLET SERVICE NATIF ===")
    
    # Configuration Django
    import os
    import django
    
    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
        django.setup()
    
    try:
        from apps.core.services.redis_fallback import get_redis_client
        from apps.brokers.models import Broker
        
        redis_client = await get_redis_client()
        await redis_client.ping()
        print("[OK] Redis connecte")
        
        # Récupération d'un broker Bitget actif (avec sync_to_async)
        from asgiref.sync import sync_to_async
        bitget_broker = await sync_to_async(
            lambda: Broker.objects.filter(
                exchange__iexact='bitget', 
                is_active=True
            ).first()
        )()
        
        if not bitget_broker:
            print("[ERROR] Aucun broker Bitget actif trouve")
            return
        
        print(f"[BROKER] Utilisation broker: {bitget_broker.name} (ID: {bitget_broker.id})")
        
        # Message get_balance réel
        balance_msg = {
            'request_id': 'BALANCE_TEST_456',
            'action': 'get_balance',
            'params': {'broker_id': bitget_broker.id}
        }
        
        print("[BALANCE] Envoi requete get_balance...")
        await redis_client.rpush('ccxt_requests', json.dumps(balance_msg))
        
        # Attendre réponse (timeout plus long pour get_balance)
        for i in range(100):  # 10s max
            response_data = await redis_client.get('ccxt_response_BALANCE_TEST_456')
            if response_data:
                response = json.loads(response_data)
                print(f"[BALANCE] REPONSE RECUE:")
                print(f"  Success: {response.get('success')}")
                print(f"  Processing time: {response.get('processing_time_ms', 0):.1f}ms")
                
                if response.get('success'):
                    balances_data = response.get('data', {})
                    print(f"  Data structure: {type(balances_data)}")
                    
                    # Structure attendue: {'balances': {...}} ou directement {...}
                    if isinstance(balances_data, dict):
                        balances = balances_data.get('balances', balances_data)
                        
                        if isinstance(balances, dict):
                            # Filtrer les balances non-zéro
                            non_zero = {}
                            for currency, balance_info in balances.items():
                                if isinstance(balance_info, dict):
                                    # Structure: {"available": "123.45", "frozen": "0", ...}
                                    available = float(balance_info.get('available', 0))
                                    if available > 0:
                                        non_zero[currency] = balance_info
                                elif isinstance(balance_info, (str, int, float)):
                                    # Structure simple: {"BTC": "0.001"}
                                    if float(balance_info) > 0:
                                        non_zero[currency] = balance_info
                            
                            print(f"  Balances non-zero: {len(non_zero)} devises")
                            for currency, balance in list(non_zero.items())[:5]:  # Afficher 5 max
                                if isinstance(balance, dict):
                                    available = balance.get('available', '0')
                                    print(f"    {currency}: {available} (+ {balance.get('frozen', '0')} frozen)")
                                else:
                                    print(f"    {currency}: {balance}")
                        else:
                            print(f"  Balances type: {type(balances)} = {balances}")
                    else:
                        print(f"  Unexpected data type: {type(balances_data)} = {balances_data}")
                else:
                    print(f"  Error: {response.get('error')}")
                break
            
            if i % 10 == 0:  # Log tous les 1s
                print(f"[BALANCE] Attente reponse... {i/10:.0f}s")
            
            await asyncio.sleep(0.1)
        else:
            print("[TIMEOUT] Aucune reponse get_balance apres 10s")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_native_service_complete())