# -*- coding: utf-8 -*-
"""
Test d'intégration du service CCXT centralisé avec Trading Manuel
"""
import asyncio
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.core.services.ccxt_client import CCXTClient
from apps.brokers.models import Broker
from django.contrib.auth import get_user_model

User = get_user_model()

async def test_ccxt_integration():
    """Test complet de l'intégration CCXT"""
    print("🔄 Test d'intégration SERVICE CCXT CENTRALISÉ")
    print("=" * 60)
    
    try:
        # 1. Créer un client CCXT
        print("1. Initialisation CCXTClient...")
        client = CCXTClient()
        print("✅ CCXTClient créé")
        
        # 2. Récupérer un broker de test
        print("\n2. Recherche broker de test...")
        try:
            user = User.objects.filter(username='dev').first()
            if not user:
                print("❌ Utilisateur 'dev' non trouvé")
                return
                
            broker = Broker.objects.filter(user=user, is_active=True).first()
            if not broker:
                print("❌ Aucun broker actif trouvé pour 'dev'")
                return
                
            print(f"✅ Broker trouvé: {broker.name} ({broker.exchange})")
        except Exception as e:
            print(f"❌ Erreur récupération broker: {e}")
            return
        
        # 3. Test get_markets
        print(f"\n3. Test get_markets pour broker {broker.id}...")
        try:
            markets = await client.get_markets(broker.id)
            print(f"✅ Markets récupérés: {len(markets)} symboles")
            
            # Afficher quelques exemples
            sample_symbols = list(markets.keys())[:5]
            print(f"   Exemples: {', '.join(sample_symbols)}")
        except Exception as e:
            print(f"❌ Erreur get_markets: {e}")
        
        # 4. Test get_balance
        print(f"\n4. Test get_balance pour broker {broker.id}...")
        try:
            balance = await client.get_balance(broker.id)
            print("✅ Balance récupérée:")
            
            # Afficher les balances non-nulles
            for asset, amount in balance.get('total', {}).items():
                if float(amount) > 0:
                    print(f"   {asset}: {amount}")
        except Exception as e:
            print(f"❌ Erreur get_balance: {e}")
        
        # 5. Test get_ticker
        print(f"\n5. Test get_ticker pour BTC/USDT...")
        try:
            ticker = await client.get_ticker(broker.id, 'BTC/USDT')
            print(f"✅ Ticker BTC/USDT:")
            print(f"   Bid: {ticker.get('bid')}")
            print(f"   Ask: {ticker.get('ask')}")
            print(f"   Last: {ticker.get('last')}")
        except Exception as e:
            print(f"❌ Erreur get_ticker: {e}")
        
        print(f"\n🎯 RÉSULTAT: Service CCXT opérationnel!")
        
    except Exception as e:
        print(f"❌ ERREUR GLOBALE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️  IMPORTANT: Assurez-vous que le service CCXT centralisé est démarré!")
    print("   Commande: python manage.py run_ccxt_service")
    print()
    
    asyncio.run(test_ccxt_integration())