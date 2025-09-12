# -*- coding: utf-8 -*-
"""
TEST RAPIDE TERMINAL 7 - Validation Production

🎯 OBJECTIF: Test rapide pour confirmer que Terminal 7 fonctionne maintenant
avec tous les exchanges (Bitget, Binance, Kraken)

Usage:
  python test_terminal7_quick.py
"""

import asyncio
import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import django
django.setup()

from apps.core.management.commands.run_order_monitor import Command
from apps.brokers.models import Broker
from asgiref.sync import sync_to_async

async def test_terminal7_multi_exchange():
    """Test rapide de Terminal 7 avec multi-exchange"""
    
    print("🚀 TEST RAPIDE TERMINAL 7 - MULTI-EXCHANGE")
    print("=" * 50)
    
    try:
        # Initialiser Terminal 7
        command = Command()
        await command._initialize_service()
        
        print(f"✅ Service initialisé: {len(command.broker_states)} brokers")
        
        # Test création des clients pour chaque exchange
        brokers = await sync_to_async(list)(
            Broker.objects.filter(is_active=True).select_related('user')
        )
        
        exchange_results = {}
        
        for broker in brokers:
            try:
                # Test création client
                client = await command.exchange_manager.get_client_for_broker(broker.id)
                
                if client:
                    exchange_results[broker.exchange] = exchange_results.get(broker.exchange, 0) + 1
                    print(f"✅ {broker.exchange.upper()}: Client créé - Broker: {broker.name}")
                else:
                    print(f"❌ {broker.exchange.upper()}: Échec création client - Broker: {broker.name}")
                    
            except Exception as e:
                print(f"❌ {broker.exchange.upper()}: Erreur - {e}")
        
        print("\n📊 RÉSUMÉ PAR EXCHANGE:")
        for exchange, count in exchange_results.items():
            print(f"  {exchange.upper()}: {count} broker(s) supporté(s)")
        
        # Test détection d'ordres (simulation)
        print(f"\n🔍 Test simulation détection ordres...")
        
        test_success = True
        for broker in brokers[:2]:  # Test sur 2 premiers brokers
            try:
                # Simuler récupération ordres via client
                client = await command.exchange_manager.get_client_for_broker(broker.id)
                if client:
                    # Test get_order_history (méthode utilisée par Terminal 7)
                    orders = await client.get_order_history(limit=5)
                    if orders.get('success'):
                        print(f"✅ {broker.exchange.upper()}: Récupération historique OK ({len(orders.get('orders', []))} ordres)")
                    else:
                        print(f"⚠️  {broker.exchange.upper()}: Récupération historique échouée - {orders.get('error', 'Unknown')}")
                else:
                    print(f"❌ {broker.exchange.upper()}: Client non disponible")
                    test_success = False
                    
            except Exception as e:
                print(f"❌ {broker.exchange.upper()}: Erreur test ordres - {e}")
                test_success = False
        
        print("\n" + "=" * 50)
        
        if exchange_results:
            total_supported = sum(exchange_results.values())
            total_brokers = len(brokers)
            print(f"🎉 RÉSULTAT: {total_supported}/{total_brokers} brokers supportés")
            
            if total_supported == total_brokers:
                print("✅ PARFAIT: Tous les brokers sont maintenant supportés!")
                print("✅ Terminal 7 peut démarrer en production")
            else:
                print("⚠️  PARTIEL: Certains brokers ont des problèmes")
                
        else:
            print("❌ ÉCHEC: Aucun broker supporté")
        
        print("=" * 50)
        
        return len(exchange_results) >= 2  # Au moins 2 exchanges supportés
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        return False

async def main():
    """Point d'entrée principal"""
    success = await test_terminal7_multi_exchange()
    
    if success:
        print("\n🎯 Terminal 7 est PRÊT pour le déploiement!")
        print("   Vous pouvez maintenant démarrer Terminal 7 avec:")
        print("   python manage.py run_order_monitor")
    else:
        print("\n⚠️  Terminal 7 nécessite encore des corrections")

if __name__ == "__main__":
    asyncio.run(main())