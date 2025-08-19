# -*- coding: utf-8 -*-
"""
Test création Trade pour diagnostiquer le problème
"""
import os
import django
import asyncio
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.brokers.models import Broker
from apps.trading_manual.models import Trade
from asgiref.sync import sync_to_async

User = get_user_model()

async def test_trade_creation():
    """Test création d'un Trade"""
    print("Test création Trade")
    print("=" * 50)
    
    try:
        # 1. Récupérer user et broker
        print("1. Récupération user et broker...")
        user = await sync_to_async(User.objects.get)(username='dev')
        broker = await sync_to_async(Broker.objects.get)(id=13)
        print(f"OK User: {user.username}, Broker: {broker.name}")
        
        # 2. Créer un Trade de test
        print("\n2. Création Trade...")
        import time
        start_time = time.time()
        
        trade_data = {
            'user': user,
            'broker': broker,
            'trade_type': 'manual',
            'symbol': 'FET/USDT',
            'side': 'sell',
            'order_type': 'limit',
            'quantity': Decimal('2.00000000'),
            'price': Decimal('7.00000000'),
            'total_value': Decimal('14.00000000'),
            'status': 'pending'
        }
        
        trade = await sync_to_async(Trade.objects.create)(**trade_data)
        creation_time = time.time() - start_time
        
        print(f"OK Trade créé: ID {trade.id} en {creation_time:.3f}s")
        print(f"   {trade.side.upper()} {trade.quantity} {trade.symbol} @ {trade.price}")
        
        # 3. Supprimer le Trade de test
        print("\n3. Suppression Trade de test...")
        await sync_to_async(trade.delete)()
        print("OK Trade supprimé")
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_trade_creation())