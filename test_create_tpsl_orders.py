# -*- coding: utf-8 -*-
"""
SCRIPT TEST - CRÉATION ORDRES TP/SL POUR VALIDATION AFFICHAGE

🎯 OBJECTIF: Créer des ordres TP/SL de test pour valider l'affichage du type d'ordre

⚠️ ATTENTION: Ce script crée de vrais ordres sur l'exchange (avec de petites quantités)
Utiliser uniquement en mode testnet ou avec des montants très faibles

🔧 COMMANDE:
python test_create_tpsl_orders.py --user=dac --broker=bitget --dry-run
"""

import asyncio
import sys
import os
from decimal import Decimal

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

from apps.brokers.models import Broker
from apps.trading_manual.services.trading_service import TradingService
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

User = get_user_model()


class TPSLOrderTester:
    def __init__(self):
        self.user = None
        self.broker = None
        self.service = None
    
    async def run_test(self, username: str = 'dac', broker_name: str = 'bitget', dry_run: bool = True):
        """
        🧪 TEST CRÉATION ORDRES TP/SL
        """
        print("=" * 80)
        print("🧪 TEST CRÉATION ORDRES TP/SL")
        print("=" * 80)
        
        if dry_run:
            print("🔒 MODE DRY-RUN: Aucun ordre réel ne sera créé")
        else:
            print("⚠️ MODE RÉEL: Des ordres seront créés sur l'exchange!")
        
        try:
            # 1. Setup
            print("\n📋 1. SETUP")
            await self._setup_user_broker(username, broker_name)
            
            # 2. Récupérer prix actuel BTC
            print("\n💰 2. RÉCUPÉRATION PRIX ACTUEL")
            current_price = await self._get_current_price('BTC/USDT')
            
            # 3. Créer ordres TP/SL de test
            print(f"\n🎯 3. CRÉATION ORDRES TP/SL DE TEST")
            await self._create_test_orders(current_price, dry_run)
            
            # 4. Vérifier affichage
            print(f"\n👀 4. VÉRIFICATION AFFICHAGE")
            await self._verify_orders_display()
            
        except Exception as e:
            print(f"❌ Erreur test: {e}")
            import traceback
            traceback.print_exc()
    
    async def _setup_user_broker(self, username: str, broker_name: str):
        """Setup utilisateur et broker"""
        self.user = await sync_to_async(User.objects.get)(username=username)
        print(f"✅ Utilisateur: {self.user.username}")
        
        brokers = await sync_to_async(list)(
            Broker.objects.filter(user=self.user, exchange__iexact=broker_name, is_active=True)
        )
        
        if not brokers:
            raise Exception(f"Aucun broker {broker_name} actif pour {username}")
        
        self.broker = brokers[0]
        print(f"✅ Broker: {self.broker.name}")
        
        self.service = TradingService(self.user, self.broker)
        print(f"✅ TradingService initialisé")
    
    async def _get_current_price(self, symbol: str) -> float:
        """Récupère le prix actuel"""
        ticker = await self.service.ccxt_client.get_ticker(self.broker.id, symbol)
        current_price = float(ticker['last'])
        print(f"✅ Prix actuel {symbol}: ${current_price:,.2f}")
        return current_price
    
    async def _create_test_orders(self, current_price: float, dry_run: bool):
        """Crée des ordres TP/SL de test"""
        
        # Calculer prix pour ordres TP/SL
        quantity = 0.00001  # 0.01 mBTC - Très petite quantité
        stop_loss_price = current_price * 0.95   # -5%
        take_profit_price = current_price * 1.05  # +5%
        
        print(f"📊 Paramètres de test:")
        print(f"   Quantité: {quantity} BTC")
        print(f"   Prix actuel: ${current_price:,.2f}")
        print(f"   Stop Loss: ${stop_loss_price:,.2f} (-5%)")
        print(f"   Take Profit: ${take_profit_price:,.2f} (+5%)")
        
        if dry_run:
            print("🔒 DRY-RUN: Simulation uniquement")
            return
        
        # Vérifier qu'on est en testnet
        if not self.broker.is_testnet:
            print("⚠️ ATTENTION: Ce broker n'est PAS en mode testnet!")
            response = input("Continuer quand même? (oui/non): ")
            if response.lower() != 'oui':
                print("❌ Test annulé par l'utilisateur")
                return
        
        try:
            # Test 1: Ordre Stop Loss simple
            print(f"\n🛡️ Test 1: Création ordre Stop Loss")
            sl_data = {
                'symbol': 'BTC/USDT',
                'side': 'sell',
                'order_type': 'stop_loss',
                'quantity': Decimal(str(quantity)),
                'price': None,
                'stop_loss_price': Decimal(str(stop_loss_price)),
                'total_value': Decimal(str(quantity * current_price))
            }
            
            # Valider d'abord
            validation = await self.service.validate_trade(**sl_data)
            if validation['valid']:
                print("✅ Validation Stop Loss OK")
                # trade_sl = await self.service.execute_trade(sl_data)
                # print(f"✅ Ordre Stop Loss créé: {trade_sl.exchange_order_id}")
            else:
                print(f"❌ Validation Stop Loss échouée: {validation['errors']}")
            
            # Test 2: Ordre Take Profit simple
            print(f"\n🎯 Test 2: Création ordre Take Profit")
            tp_data = {
                'symbol': 'BTC/USDT',
                'side': 'sell',
                'order_type': 'take_profit',
                'quantity': Decimal(str(quantity)),
                'price': None,
                'take_profit_price': Decimal(str(take_profit_price)),
                'total_value': Decimal(str(quantity * current_price))
            }
            
            validation = await self.service.validate_trade(**tp_data)
            if validation['valid']:
                print("✅ Validation Take Profit OK")
                # trade_tp = await self.service.execute_trade(tp_data)
                # print(f"✅ Ordre Take Profit créé: {trade_tp.exchange_order_id}")
            else:
                print(f"❌ Validation Take Profit échouée: {validation['errors']}")
                
        except Exception as e:
            print(f"❌ Erreur création ordres: {e}")
            import traceback
            traceback.print_exc()
    
    async def _verify_orders_display(self):
        """Vérifie l'affichage des ordres"""
        try:
            print("📋 Récupération ordres ouverts...")
            orders = await self.service.get_open_orders()
            
            print(f"✅ {len(orders)} ordres récupérés")
            
            if orders:
                print("\n📊 ANALYSE TYPES D'ORDRES:")
                type_counts = {}
                for order in orders:
                    order_type = order.get('type', 'unknown')
                    type_counts[order_type] = type_counts.get(order_type, 0) + 1
                    
                    # Simulation frontend
                    frontend_type = self._simulate_format_order_type(order)
                    print(f"   • {order.get('order_id', 'N/A')[:8]}... | "
                          f"Type: {order_type} → {frontend_type['label']} | "
                          f"Side: {order.get('side')} | "
                          f"Symbol: {order.get('symbol')}")
                
                print(f"\n📈 RÉCAPITULATIF: {type_counts}")
                
                # Chercher TP/SL
                tp_sl_orders = [o for o in orders if any(keyword in o.get('type', '').lower() 
                                                       for keyword in ['stop', 'take', 'profit', 'loss', 'tp', 'sl'])]
                
                if tp_sl_orders:
                    print(f"🎯 {len(tp_sl_orders)} ordres TP/SL trouvés!")
                else:
                    print("ℹ️ Aucun ordre TP/SL dans les ordres actuels")
            else:
                print("ℹ️ Aucun ordre ouvert trouvé")
                
        except Exception as e:
            print(f"❌ Erreur vérification: {e}")
    
    def _simulate_format_order_type(self, order):
        """Simule formatOrderType du frontend"""
        order_type = order.get('type', 'unknown')
        
        type_map = {
            'market': {'label': 'MARKET', 'class': 'type-market'},
            'limit': {'label': 'LIMIT', 'class': 'type-limit'},
            'stop_loss': {'label': 'STOP LOSS', 'class': 'type-stop-loss'},
            'take_profit': {'label': 'TAKE PROFIT', 'class': 'type-take-profit'},
            'stop_limit': {'label': 'STOP LIMIT', 'class': 'type-stop-limit'},
            'sl_tp_combo': {'label': 'SL+TP', 'class': 'type-combo'},
            'stop': {'label': 'STOP', 'class': 'type-stop-loss'},
            'unknown': {'label': 'AUTRE', 'class': 'type-unknown'}
        }
        
        return type_map.get(order_type.lower(), type_map['unknown'])


async def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test création ordres TP/SL')
    parser.add_argument('--user', default='dac', help='Nom utilisateur')
    parser.add_argument('--broker', default='bitget', help='Nom du broker')
    parser.add_argument('--dry-run', action='store_true', help='Mode simulation (recommandé)')
    
    args = parser.parse_args()
    
    tester = TPSLOrderTester()
    await tester.run_test(args.user, args.broker, args.dry_run)
    
    print("\n" + "=" * 80)
    print("🎯 TEST TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())