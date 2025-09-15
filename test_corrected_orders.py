# -*- coding: utf-8 -*-
"""
TEST RAPIDE - VALIDATION CORRECTION ORDRES TP/SL

🎯 OBJECTIF: Valider que la correction du client Bitget fonctionne
"""

import asyncio
import sys
import os

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

from apps.brokers.models import Broker
from apps.core.services.bitget_native_client import BitgetNativeClient
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

User = get_user_model()


async def test_corrected_orders():
    """Test rapide de la correction"""
    print("🔍 TEST CORRECTION ORDRES TP/SL")
    print("=" * 50)
    
    # Setup broker
    user = await sync_to_async(User.objects.get)(username='dac')
    brokers = await sync_to_async(list)(
        Broker.objects.filter(user=user, exchange__iexact='bitget', is_active=True)
    )
    broker = brokers[0]
    
    print(f"✅ Test avec broker: {broker.name}")
    
    # Test client corrigé
    client = BitgetNativeClient(
        api_key=broker.decrypt_field(broker.api_key),
        api_secret=broker.decrypt_field(broker.api_secret),
        api_passphrase=broker.decrypt_field(broker.api_password) if broker.api_password else None,
        is_testnet=broker.is_testnet
    )
    
    result = await client.get_open_orders()
    
    if result['success']:
        orders = result['orders']
        print(f"✅ {len(orders)} ordres récupérés")
        
        # Analyser les types
        types = {}
        tpsl_count = 0
        
        for order in orders:
            order_type = order.get('type', 'unknown')
            types[order_type] = types.get(order_type, 0) + 1
            
            if order.get('is_tpsl_order'):
                tpsl_count += 1
                print(f"🎯 ORDRE TP/SL TROUVÉ:")
                print(f"   ID: {order.get('order_id')}")
                print(f"   Type: {order_type}")
                print(f"   Symbol: {order.get('symbol')}")
                print(f"   Side: {order.get('side')}")
                print(f"   TP Price: {order.get('preset_take_profit_price')}")
                print(f"   SL Price: {order.get('preset_stop_loss_price')}")
                print(f"   Trigger: {order.get('trigger_price')}")
        
        print(f"📊 Récapitulatif types: {types}")
        print(f"🎯 Ordres TP/SL: {tpsl_count}")
        
        if tpsl_count > 0:
            print("✅ CORRECTION RÉUSSIE ! Les ordres TP/SL sont maintenant récupérés !")
        else:
            print("ℹ️ Aucun ordre TP/SL actuellement ouvert (normal si pas d'ordres TP/SL)")
            
    else:
        print(f"❌ Erreur: {result['error']}")


if __name__ == "__main__":
    asyncio.run(test_corrected_orders())