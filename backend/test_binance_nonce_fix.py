# -*- coding: utf-8 -*-
"""
TEST BINANCE NONCE FIX - Validation correction Invalid nonce

🎯 OBJECTIF: Valider la correction du problème "EAPI:Invalid nonce" 
sur le client Binance natif

🔧 CORRECTIONS TESTEES:
- Signature standardisée avec _sign_request()
- Timestamp synchronisé automatiquement
- Headers et paramètres signés correctement

📋 TESTS:
1. Test connexion basique
2. Test balance (méthode complète)
3. Validation format signature
"""

import asyncio
import sys
import os

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

from apps.core.services.binance_native_client import BinanceNativeClient
from apps.brokers.models import Broker
from asgiref.sync import sync_to_async


async def test_binance_nonce_fix():
    """
    🧪 TEST COMPLET CORRECTION NONCE BINANCE
    """
    print("=" * 70)
    print("   TEST CORRECTION BINANCE NONCE - EAPI:Invalid nonce")
    print("=" * 70)
    
    try:
        # 1. Récupérer broker Binance depuis DB
        print("\n[1] Récupération broker Binance...")
        broker = await sync_to_async(Broker.objects.filter(exchange='binance').first)()
        
        if not broker:
            print("❌ Aucun broker Binance trouvé!")
            return False
            
        print(f"✅ Broker trouvé: {broker.name} ({broker.exchange})")
        
        # 2. Créer client Binance natif avec credentials
        print("\n[2] Création client Binance natif...")
        client = BinanceNativeClient(
            api_key=broker.decrypt_field(broker.api_key),
            api_secret=broker.decrypt_field(broker.api_secret),
            is_testnet=broker.is_testnet
        )
        print(f"✅ Client créé: {client.exchange_name}")
        print(f"   Testnet: {client.is_testnet}")
        print(f"   Base URL: {client.base_url}")
        
        # 3. Test signature standardisée
        print("\n[3] Test signature standardisée...")
        headers, signed_params = client._sign_request('GET', '/api/v3/account', '')
        print(f"✅ Headers: {list(headers.keys())}")
        print(f"✅ Params signés: {signed_params[:50]}...")
        print(f"   Contient timestamp: {'timestamp=' in signed_params}")
        print(f"   Contient signature: {'signature=' in signed_params}")
        
        # 4. Test connexion (méthode critique)
        print("\n[4] Test connexion Binance...")
        result = await client.test_connection()
        
        if result['connected']:
            print("✅ CONNEXION RÉUSSIE!")
            print(f"   Items balance: {result.get('balance_items', 0)}")
        else:
            print("❌ CONNEXION ÉCHOUÉE!")
            print(f"   Erreur: {result.get('error', 'Inconnue')}")
            
        # 5. Test balance complète (si connexion OK)
        if result['connected']:
            print("\n[5] Test balance complète...")
            balance_result = await client.get_balance()
            
            if balance_result['success']:
                balances = balance_result['balances']
                non_zero_balances = {k: v for k, v in balances.items() 
                                   if v['total'] > 0}
                
                print("✅ BALANCE RÉCUPÉRÉE!")
                print(f"   Total devises: {len(balances)}")
                print(f"   Balances non-zéro: {len(non_zero_balances)}")
                
                # Afficher quelques balances
                for coin, balance in list(non_zero_balances.items())[:3]:
                    print(f"   {coin}: {balance['total']:.8f}")
                    
            else:
                print("❌ ERREUR BALANCE!")
                print(f"   Erreur: {balance_result.get('error', 'Inconnue')}")
        
        # 6. Fermer proprement la session
        if hasattr(client, 'session') and client.session:
            await client.session.close()
    
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("   TEST TERMINÉ")
    print("=" * 70)
    
    return result['connected'] if 'result' in locals() else False


if __name__ == "__main__":
    success = asyncio.run(test_binance_nonce_fix())
    
    if success:
        print("\n🎉 CORRECTION NONCE VALIDÉE - Binance fonctionnel!")
        exit(0)
    else:
        print("\n💥 CORRECTION ÉCHOUÉE - Vérifier la signature")
        exit(1)