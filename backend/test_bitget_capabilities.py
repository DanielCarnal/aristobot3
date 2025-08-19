# -*- coding: utf-8 -*-
"""
Test des capacités Bitget pour fetchOpenOrders
"""
import ccxt

def test_bitget_capabilities():
    """Test des capacités de l'exchange Bitget"""
    print("🔧 Test capacités Bitget")
    print("=" * 50)
    
    try:
        # Créer une instance Bitget (sans clés API)
        exchange = ccxt.bitget()
        
        print(f"📊 Exchange: {exchange.name}")
        print(f"📊 ID: {exchange.id}")
        
        # Vérifier les capacités
        print("\n📋 Capacités fetchOpenOrders:")
        has_fetch_open_orders = exchange.has.get('fetchOpenOrders', False)
        print(f"   fetchOpenOrders: {has_fetch_open_orders}")
        
        print("\n📋 Autres capacités importantes:")
        important_capabilities = [
            'fetchBalance', 'fetchTicker', 'fetchOrderBook',
            'createOrder', 'createLimitOrder', 'createMarketOrder',
            'cancelOrder', 'editOrder', 'fetchOrder', 'fetchOrders',
            'fetchOpenOrders', 'fetchClosedOrders'
        ]
        
        for cap in important_capabilities:
            status = exchange.has.get(cap, False)
            print(f"   {cap}: {'✅' if status else '❌'} {status}")
        
        print(f"\n📊 Rate Limit: {exchange.rateLimit}ms")
        
        # Vérifier les markets (sans clés API)
        print(f"\n📊 Test loadMarkets...")
        try:
            markets = exchange.load_markets()
            print(f"   ✅ {len(markets)} marchés chargés")
            
            # Vérifier BTC/USDT
            if 'BTC/USDT' in markets:
                btc_market = markets['BTC/USDT']
                print(f"   📊 BTC/USDT trouvé:")
                print(f"      Base: {btc_market['base']}")
                print(f"      Quote: {btc_market['quote']}")
                print(f"      Active: {btc_market['active']}")
            else:
                print("   ❌ BTC/USDT non trouvé")
                print(f"   📋 Premiers marchés: {list(markets.keys())[:5]}")
                
        except Exception as e:
            print(f"   ❌ Erreur loadMarkets: {e}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bitget_capabilities()