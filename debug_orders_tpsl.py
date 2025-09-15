# -*- coding: utf-8 -*-
"""
SCRIPT DIAGNOSTIC - POURQUOI LES ORDRES TP/SL NE S'AFFICHENT PAS

🎯 OBJECTIF: Identifier pourquoi les ordres TP/SL n'apparaissent pas dans "Ordres ouverts"

📊 TESTS À EFFECTUER:
1. Vérifier si l'endpoint Bitget retourne tous les types d'ordres
2. Analyser la structure des données retournées
3. Tester le mapping des types d'ordres
4. Vérifier le flux Terminal 5 → TradingService → Frontend

🔧 COMMANDE:
python debug_orders_tpsl.py --user=dac --broker=bitget
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

from apps.brokers.models import Broker
from apps.core.services.native_exchange_manager import get_native_exchange_manager
from apps.core.services.exchange_client import ExchangeClient
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

User = get_user_model()


class OrdersTPSLDiagnostic:
    def __init__(self):
        self.manager = None
        self.exchange_client = None
    
    async def run_full_diagnostic(self, username: str = 'dac', broker_name: str = 'bitget'):
        """
        🔍 DIAGNOSTIC COMPLET ORDRES TP/SL
        """
        print("=" * 80)
        print("🔍 DIAGNOSTIC ORDRES TP/SL MANQUANTS")
        print("=" * 80)
        
        try:
            # 1. Setup utilisateur et broker
            print("\n📋 1. SETUP UTILISATEUR ET BROKER")
            user = await sync_to_async(User.objects.get)(username=username)
            print(f"✅ Utilisateur: {user.username} (ID: {user.id})")
            
            # Trouver le broker Bitget de cet utilisateur
            brokers = await sync_to_async(list)(
                Broker.objects.filter(user=user, exchange__iexact=broker_name, is_active=True)
            )
            
            if not brokers:
                print(f"❌ Aucun broker {broker_name} actif trouvé pour {username}")
                return
            
            broker = brokers[0]
            print(f"✅ Broker: {broker.name} (ID: {broker.id}, Exchange: {broker.exchange})")
            
            # 2. Test direct via client natif
            print(f"\n🔌 2. TEST DIRECT CLIENT NATIF {broker.exchange.upper()}")
            await self._test_native_client_direct(broker)
            
            # 3. Test via Terminal 5 (NativeExchangeManager)
            print(f"\n🏭 3. TEST VIA TERMINAL 5 (NATIVE EXCHANGE MANAGER)")
            await self._test_terminal5_flow(broker)
            
            # 4. Test via ExchangeClient (couche compatibilité)
            print(f"\n🔄 4. TEST VIA EXCHANGE CLIENT (COUCHE COMPATIBILITÉ)")
            await self._test_exchange_client_flow(broker)
            
            # 5. Test flux complet Trading Manual
            print(f"\n📱 5. TEST FLUX COMPLET TRADING MANUAL")
            await self._test_trading_manual_flow(user, broker)
            
        except Exception as e:
            print(f"❌ Erreur diagnostic: {e}")
            import traceback
            traceback.print_exc()
    
    async def _test_native_client_direct(self, broker):
        """Test direct du client natif Bitget"""
        try:
            from apps.core.services.bitget_native_client import BitgetNativeClient
            
            print("   🔌 Création client Bitget natif...")
            client = BitgetNativeClient(
                api_key=broker.decrypt_field(broker.api_key),
                api_secret=broker.decrypt_field(broker.api_secret),
                api_passphrase=broker.decrypt_field(broker.api_password) if broker.api_password else None,
                is_testnet=broker.is_testnet
            )
            
            print("   📋 Récupération ordres ouverts directs...")
            result = await client.get_open_orders()
            
            if result['success']:
                orders = result['orders']
                print(f"   ✅ {len(orders)} ordres ouverts récupérés")
                
                if orders:
                    print("   📊 ANALYSE DES TYPES D'ORDRES:")
                    type_counts = {}
                    for order in orders:
                        order_type = order.get('type', 'unknown')
                        type_counts[order_type] = type_counts.get(order_type, 0) + 1
                        
                        # Afficher détails des 3 premiers ordres
                        if len([o for o in orders if orders.index(o) < 3]) <= 3:
                            print(f"     - Ordre {order.get('order_id', 'N/A')[:8]}...")
                            print(f"       Type: {order_type}")
                            print(f"       Side: {order.get('side', 'N/A')}")
                            print(f"       Symbol: {order.get('symbol', 'N/A')}")
                            print(f"       Status: {order.get('status', 'N/A')}")
                            print(f"       Prix: {order.get('price', 'N/A')}")
                    
                    print(f"   📈 RÉCAPITULATIF TYPES: {type_counts}")
                    
                    # Chercher spécifiquement les TP/SL
                    tp_sl_orders = [o for o in orders if any(keyword in o.get('type', '').lower() 
                                                           for keyword in ['stop', 'take', 'profit', 'loss', 'tp', 'sl'])]
                    
                    if tp_sl_orders:
                        print(f"   🎯 {len(tp_sl_orders)} ordres TP/SL trouvés!")
                        for order in tp_sl_orders:
                            print(f"     - TP/SL: {order.get('type')} | {order.get('side')} | {order.get('symbol')}")
                    else:
                        print("   ⚠️ AUCUN ordre TP/SL trouvé dans les types")
                        
                        # Debug: afficher les données brutes de Bitget pour le premier ordre
                        print("   🔍 DEBUG - Structure brute premier ordre:")
                        if orders:
                            raw_order = orders[0]
                            for key, value in raw_order.items():
                                print(f"       {key}: {value} ({type(value).__name__})")
                else:
                    print("   ⚠️ Aucun ordre ouvert trouvé")
            else:
                print(f"   ❌ Erreur client natif: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Erreur test client natif: {e}")
            import traceback
            traceback.print_exc()
    
    async def _test_terminal5_flow(self, broker):
        """Test via Terminal 5 (NativeExchangeManager)"""
        try:
            print("   🏭 Initialisation Terminal 5...")
            self.manager = get_native_exchange_manager()
            
            print("   📋 Requête fetch_open_orders via Terminal 5...")
            result = await self.manager._handle_action('fetch_open_orders', {'broker_id': broker.id})
            
            if result['success']:
                orders = result['data']
                print(f"   ✅ Terminal 5: {len(orders)} ordres récupérés")
                
                if orders:
                    # Analyser les types
                    type_counts = {}
                    for order in orders:
                        order_type = order.get('type', 'unknown')
                        type_counts[order_type] = type_counts.get(order_type, 0) + 1
                    
                    print(f"   📈 Types via Terminal 5: {type_counts}")
                else:
                    print("   ⚠️ Aucun ordre via Terminal 5")
            else:
                print(f"   ❌ Erreur Terminal 5: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Erreur test Terminal 5: {e}")
            import traceback
            traceback.print_exc()
    
    async def _test_exchange_client_flow(self, broker):
        """Test via ExchangeClient (couche compatibilité)"""
        try:
            print("   🔄 Initialisation ExchangeClient...")
            self.exchange_client = ExchangeClient()
            
            print("   📋 Requête fetch_open_orders via ExchangeClient...")
            orders = await self.exchange_client.fetch_open_orders(broker.id)
            
            print(f"   ✅ ExchangeClient: {len(orders)} ordres récupérés")
            
            if orders:
                # Analyser les types
                type_counts = {}
                for order in orders:
                    order_type = order.get('type', 'unknown')
                    type_counts[order_type] = type_counts.get(order_type, 0) + 1
                
                print(f"   📈 Types via ExchangeClient: {type_counts}")
            else:
                print("   ⚠️ Aucun ordre via ExchangeClient")
                
        except Exception as e:
            print(f"   ❌ Erreur test ExchangeClient: {e}")
            import traceback
            traceback.print_exc()
    
    async def _test_trading_manual_flow(self, user, broker):
        """Test du flux complet Trading Manual"""
        try:
            print("   📱 Test TradingService...")
            from apps.trading_manual.services.trading_service import TradingService
            
            service = TradingService(user, broker)
            
            print("   📋 Récupération ordres ouverts via TradingService...")
            orders = await service.get_open_orders()
            
            print(f"   ✅ TradingService: {len(orders)} ordres récupérés")
            
            if orders:
                # Analyser les types
                type_counts = {}
                for order in orders:
                    order_type = order.get('type', 'unknown')
                    type_counts[order_type] = type_counts.get(order_type, 0) + 1
                
                print(f"   📈 Types via TradingService: {type_counts}")
                
                # Test du formatOrderType du frontend
                print("   🎨 Test formatOrderType (simulation frontend):")
                for order in orders[:3]:  # Premiers 3 ordres
                    frontend_type = self._simulate_format_order_type(order)
                    print(f"     - Ordre {order.get('order_id', 'N/A')[:8]}... :")
                    print(f"       Type brut: {order.get('type', 'unknown')}")
                    print(f"       Type formaté: {frontend_type['label']} ({frontend_type['class']})")
            else:
                print("   ⚠️ Aucun ordre via TradingService")
                
        except Exception as e:
            print(f"   ❌ Erreur test TradingService: {e}")
            import traceback
            traceback.print_exc()
    
    def _simulate_format_order_type(self, order):
        """Simule la fonction formatOrderType du frontend"""
        order_type = order.get('type', order.get('order_type', order.get('orderType', 'unknown')))
        
        type_map = {
            'market': {'label': 'MARKET', 'class': 'type-market'},
            'limit': {'label': 'LIMIT', 'class': 'type-limit'},
            'stop_loss': {'label': 'STOP LOSS', 'class': 'type-stop-loss'},
            'take_profit': {'label': 'TAKE PROFIT', 'class': 'type-take-profit'},
            'stop_limit': {'label': 'STOP LIMIT', 'class': 'type-stop-limit'},
            'sl_tp_combo': {'label': 'SL+TP', 'class': 'type-combo'},
            'stop': {'label': 'STOP', 'class': 'type-stop-loss'},
            'take_profit_limit': {'label': 'TP LIMIT', 'class': 'type-take-profit'},
            'stop_loss_limit': {'label': 'SL LIMIT', 'class': 'type-stop-loss'},
            'oco': {'label': 'OCO', 'class': 'type-combo'},
            'trigger': {'label': 'TRIGGER', 'class': 'type-trigger'},
            'unknown': {'label': 'AUTRE', 'class': 'type-unknown'}
        }
        
        normalized_type = str(order_type).lower()
        return type_map.get(normalized_type, type_map['unknown'])


async def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnostic ordres TP/SL manquants')
    parser.add_argument('--user', default='dac', help='Nom utilisateur')
    parser.add_argument('--broker', default='bitget', help='Nom du broker')
    
    args = parser.parse_args()
    
    diagnostic = OrdersTPSLDiagnostic()
    await diagnostic.run_full_diagnostic(args.user, args.broker)
    
    print("\n" + "=" * 80)
    print("🎯 DIAGNOSTIC TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())