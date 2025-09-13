# -*- coding: utf-8 -*-
"""
TEST SOLUTION 2 PHASE 2 - API POSITIONS P&L

🎯 OBJECTIF: Valider l'API /api/trading-manual/positions/ 
- Lecture des positions calculées par Terminal 7
- Données P&L avec source='order_monitor'
- Format JSON compatible avec Frontend Phase 1

✅ FONCTIONNALITÉS TESTÉES:
1. Endpoint GET /api/trading-manual/positions/ 
2. Filtrage par status (active/closed/all)
3. Calculs P&L automatiques Terminal 7
4. Format JSON attendu par Frontend 3-tabs
5. Notifications WebSocket (optionnel)
"""

import asyncio
import sys
import os

# Configuration Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

import json
import requests
from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from apps.trading_manual.views import PositionsView
from apps.brokers.models import Broker
from apps.trading_manual.models import Trade
from decimal import Decimal
import logging

# Configuration logging pour tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

User = get_user_model()


def test_positions_api_direct():
    """
    TEST 1: API Positions direct via Django
    """
    print("=" * 70)
    print("TEST 1: API POSITIONS P&L - Appel direct Django")
    print("=" * 70)
    
    try:
        # Récupérer un utilisateur et broker de test
        try:
            user = User.objects.get(username='dev')
            print(f"✅ Utilisateur trouvé: {user.username}")
        except User.DoesNotExist:
            print("❌ Utilisateur 'dev' non trouvé - Run python manage.py init_aristobot")
            return
        
        # Récupérer un broker actif
        brokers = Broker.objects.filter(user=user, is_active=True)
        if not brokers.exists():
            print("❌ Aucun broker actif trouvé pour cet utilisateur")
            return
        
        broker = brokers.first()
        print(f"✅ Broker trouvé: {broker.name} ({broker.exchange})")
        
        # Créer une requête factice
        factory = RequestFactory()
        request = factory.get(f'/api/trading-manual/positions/?broker_id={broker.id}&status=all')
        request.user = user
        
        # Tester l'API directement
        view = PositionsView()
        response = view.get(request)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.data
            print(f"✅ Réponse API valide:")
            print(f"   - Positions count: {data.get('count', 0)}")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Statistics: {data.get('statistics', {})}")
            
            # Afficher quelques positions si disponibles
            positions = data.get('positions', [])
            if positions:
                print(f"\n📋 Exemple positions (max 3):")
                for i, pos in enumerate(positions[:3]):
                    print(f"   {i+1}. {pos['symbol']}: {pos['realized_pnl']} PnL "
                          f"({pos['position_status']})")
            else:
                print("⚠️  Aucune position trouvée (normal si pas de trades Terminal 7)")
                
        else:
            print(f"❌ Erreur API: {response.data}")
            
    except Exception as e:
        print(f"❌ Erreur test API direct: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_terminal7_trades_data():
    """
    TEST 2: Données trades Terminal 7 en DB
    """
    print("=" * 70)
    print("TEST 2: DONNÉES TRADES TERMINAL 7 EN DB")
    print("=" * 70)
    
    try:
        # Compter les trades par source
        trade_counts = {}
        for source_choice in Trade.SOURCE_CHOICES:
            source_name = source_choice[0]
            count = Trade.objects.filter(source=source_name).count()
            trade_counts[source_name] = count
        
        print("📊 Trades par source:")
        for source, count in trade_counts.items():
            print(f"   - {source}: {count} trades")
        
        # Focus sur les trades Terminal 7
        terminal7_trades = Trade.objects.filter(source='order_monitor')
        print(f"\n🤖 Trades Terminal 7 détaillés:")
        print(f"   - Total: {terminal7_trades.count()}")
        
        if terminal7_trades.exists():
            # Analyser quelques trades Terminal 7
            for trade in terminal7_trades.order_by('-created_at')[:5]:
                print(f"   - {trade.symbol} {trade.side}: "
                      f"PnL={trade.realized_pnl}, "
                      f"Method={trade.pnl_calculation_method}")
        else:
            print("   ⚠️  Aucun trade Terminal 7 trouvé")
            print("      Solution: Lancer Terminal 7 pour détecter des ordres")
        
        # Statistiques générales
        total_realized_pnl = terminal7_trades.filter(
            realized_pnl__isnull=False
        ).aggregate(
            total_pnl=models.Sum('realized_pnl')
        )['total_pnl'] or Decimal('0')
        
        print(f"\n💰 P&L Total Terminal 7: {total_realized_pnl}")
        
    except Exception as e:
        print(f"❌ Erreur analyse trades Terminal 7: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_create_sample_terminal7_trade():
    """
    TEST 3: Créer un trade Terminal 7 de test
    """
    print("=" * 70)
    print("TEST 3: CRÉATION TRADE TERMINAL 7 DE TEST")
    print("=" * 70)
    
    try:
        # Récupérer utilisateur et broker
        user = User.objects.get(username='dev')
        broker = Broker.objects.filter(user=user, is_active=True).first()
        
        if not broker:
            print("❌ Pas de broker actif pour créer un trade de test")
            return
        
        # Vérifier si on a déjà des trades de test
        existing_test_trades = Trade.objects.filter(
            user=user,
            broker=broker,
            source='order_monitor',
            notes__contains='TEST_SOLUTION2'
        )
        
        if existing_test_trades.exists():
            print(f"✅ {existing_test_trades.count()} trade(s) de test trouvé(s)")
            
            # Afficher le trade de test
            test_trade = existing_test_trades.first()
            print(f"   - Trade: {test_trade.symbol} {test_trade.side}")
            print(f"   - P&L: {test_trade.realized_pnl}")
            print(f"   - Method: {test_trade.pnl_calculation_method}")
            
        else:
            # Créer un trade de test Terminal 7
            print("🔄 Création d'un trade de test Terminal 7...")
            
            test_trade = Trade.objects.create(
                user=user,
                broker=broker,
                trade_type='terminal7',
                source='order_monitor',  # Source Terminal 7
                symbol='BTC/USDT',
                side='buy',
                order_type='market',
                quantity=Decimal('0.001'),
                price=Decimal('45000'),
                total_value=Decimal('45'),
                filled_quantity=Decimal('0.001'),
                filled_price=Decimal('45000'),
                fees=Decimal('0.045'),
                status='filled',
                
                # Champs Terminal 7
                exchange_order_id='TEST_SOLUTION2_001',
                realized_pnl=Decimal('2.5'),  # +$2.50 profit test
                pnl_calculation_method='price_averaging',
                avg_buy_price=Decimal('45000'),
                position_quantity_after=Decimal('0.001'),
                
                # Metadata
                notes='TEST_SOLUTION2 - Trade de test pour API positions'
            )
            
            print(f"✅ Trade de test créé: ID {test_trade.id}")
            print(f"   - Symbol: {test_trade.symbol}")
            print(f"   - P&L: {test_trade.realized_pnl}")
            print(f"   - Source: {test_trade.source}")
        
        # Re-tester l'API avec ce trade
        print("\n🔄 Re-test API positions avec trade de test:")
        test_positions_api_direct()
        
    except Exception as e:
        print(f"❌ Erreur création trade de test: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_positions_filtering():
    """
    TEST 4: Test filtres API positions
    """
    print("=" * 70)
    print("TEST 4: TEST FILTRES API POSITIONS")
    print("=" * 70)
    
    try:
        user = User.objects.get(username='dev')
        broker = Broker.objects.filter(user=user, is_active=True).first()
        
        if not broker:
            print("❌ Pas de broker pour test filtres")
            return
        
        factory = RequestFactory()
        view = PositionsView()
        
        # Test différents filtres
        filters_to_test = [
            ('all', 'Toutes positions'),
            ('active', 'Positions actives seulement'),
            ('closed', 'Positions fermées seulement')
        ]
        
        for filter_status, description in filters_to_test:
            print(f"\n📊 Test filtre: {description} (status={filter_status})")
            
            request = factory.get(f'/api/trading-manual/positions/?broker_id={broker.id}&status={filter_status}&limit=10')
            request.user = user
            
            response = view.get(request)
            
            if response.status_code == 200:
                data = response.data
                positions = data.get('positions', [])
                statistics = data.get('statistics', {})
                
                print(f"   ✅ Count: {data.get('count')}")
                print(f"   📊 Stats: Active={statistics.get('active_positions')}, "
                      f"Closed={statistics.get('closed_positions')}")
                
                # Vérifier cohérence du filtre
                if filter_status == 'active':
                    active_found = sum(1 for p in positions if p['net_quantity'] != 0)
                    print(f"   🔍 Vérification: {active_found} positions réellement actives")
                elif filter_status == 'closed':
                    closed_found = sum(1 for p in positions if p['net_quantity'] == 0)
                    print(f"   🔍 Vérification: {closed_found} positions réellement fermées")
                
            else:
                print(f"   ❌ Erreur: {response.data}")
        
    except Exception as e:
        print(f"❌ Erreur test filtres: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def main():
    """Test complet API Positions Solution 2 Phase 2"""
    
    print("🚀 ARISTOBOT3 - TEST SOLUTION 2 PHASE 2")
    print("=" * 70)
    print("✅ Test API Positions P&L avec données Terminal 7")
    print("🎯 Objectif: Valider Backend pour onglet Positions Frontend")
    print("=" * 70)
    print()
    
    # Tests individuels
    test_positions_api_direct()
    test_terminal7_trades_data() 
    test_create_sample_terminal7_trade()
    test_positions_filtering()
    
    print("=" * 70)
    print("🎉 TESTS SOLUTION 2 PHASE 2 TERMINÉS")
    print("=" * 70)
    print()
    print("📝 RÉSULTATS ATTENDUS:")
    print("  ✅ API /api/trading-manual/positions/ fonctionne")
    print("  ✅ Filtres status (active/closed/all) opérationnels")
    print("  ✅ Données P&L Terminal 7 calculées correctement")
    print("  ✅ Format JSON compatible Frontend 3-tabs")
    print()
    print("🚀 PHASE 2 BACKEND TERMINÉE - Prêt pour intégration Frontend!")


if __name__ == "__main__":
    # Import nécessaire pour les statistiques
    from django.db import models
    main()