# -*- coding: utf-8 -*-
"""
Test des capacités de l'exchange Bitget via CCXT
"""
import asyncio
import json
import uuid
import redis.asyncio as redis

async def test_bitget_capabilities():
    """Test des capacités disponibles sur Bitget"""
    print("Test capacités Bitget")
    print("=" * 50)
    
    try:
        # 1. Connexion Redis
        print("1. Test connexion Redis...")
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await redis_client.ping()
        print("OK Redis connecté")
        
        # 2. Récupérer les capacités de l'exchange
        print("\n2. Test get_markets pour voir les capacités...")
        request_id = str(uuid.uuid4())
        request = {
            'request_id': request_id,
            'action': 'get_markets',
            'params': {'broker_id': 13},
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await redis_client.rpush('ccxt_requests', json.dumps(request))
        
        response_key = f"ccxt_response_{request_id}"
        
        for i in range(100):  # 10s
            response_data = await redis_client.get(response_key)
            if response_data:
                response = json.loads(response_data)
                if response.get('success'):
                    markets = response.get('data', {})
                    
                    # Regarder les infos sur BTC/USDT
                    btc_market = markets.get('BTC/USDT')
                    if btc_market:
                        print("Infos marché BTC/USDT:")
                        print(f"   Active: {btc_market.get('active')}")
                        print(f"   Type: {btc_market.get('type')}")
                        print(f"   Spot: {btc_market.get('spot')}")
                        print(f"   Future: {btc_market.get('future')}")
                        print(f"   Option: {btc_market.get('option')}")
                        print(f"   Contract: {btc_market.get('contract')}")
                        
                        limits = btc_market.get('limits', {})
                        print(f"   Limites amount: {limits.get('amount')}")
                        print(f"   Limites price: {limits.get('price')}")
                        print(f"   Limites cost: {limits.get('cost')}")
                    
                await redis_client.delete(response_key)
                break
            await asyncio.sleep(0.1)
        
        await redis_client.close()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Vérification des capacités de Bitget")
    print("Pour comprendre pourquoi certains ordres ne sont pas visibles")
    print()
    asyncio.run(test_bitget_capabilities())