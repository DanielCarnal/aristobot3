# -*- coding: utf-8 -*-
"""
Test du problème Portfolio vide - basé sur nos sessions debug précédentes
"""

import os
import django
import asyncio

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

async def test_portfolio_issue():
    """Test du problème de portfolio vide"""
    print("=== TEST PROBLÈME PORTFOLIO VIDE ===")
    
    from django.contrib.auth import get_user_model
    from apps.brokers.models import Broker
    from apps.trading_manual.services.portfolio_service import PortfolioService
    from apps.trading_manual.services.trading_service import TradingService
    from asgiref.sync import sync_to_async
    
    User = get_user_model()
    
    try:
        # Récupérer utilisateur dev et broker 13 (async)
        dev_user = await sync_to_async(User.objects.get)(username='dev')
        broker_13 = await sync_to_async(Broker.objects.get)(id=13, user=dev_user)
        
        print(f"[USER] {dev_user.username}")
        print(f"[BROKER] {broker_13.name} (ID: {broker_13.id}, Exchange: {broker_13.exchange})")
        
        # Test 1: PortfolioService.get_portfolio_summary()
        print(f"\n=== TEST 1: PortfolioService.get_portfolio_summary() ===")
        try:
            portfolio_service = PortfolioService(dev_user, broker_13)
            print(f"[SERVICE] PortfolioService créé")
            
            portfolio = await portfolio_service.get_portfolio_summary()
            print(f"[PORTFOLIO SUCCESS] {portfolio}")
            
            if 'balance' in portfolio and portfolio['balance']:
                print(f"[BALANCE] Récupérée avec succès")
                total_balance = portfolio['balance'].get('total', {})
                print(f"[ASSETS] {len(total_balance)} assets trouvés: {list(total_balance.keys())}")
                
                # Vérifier les montants
                for asset, amount in total_balance.items():
                    if float(amount) > 0:
                        print(f"  - {asset}: {amount}")
                        
            else:
                print(f"[BALANCE ERROR] Balance vide ou manquante")
                
            if 'total_value_usd' in portfolio:
                print(f"[TOTAL VALUE] ${portfolio['total_value_usd']}")
            else:
                print(f"[TOTAL VALUE ERROR] Total value manquante")
                
        except Exception as e:
            print(f"[PORTFOLIO ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: TradingService.get_balance() direct pour comparaison
        print(f"\n=== TEST 2: TradingService.get_balance() pour comparaison ===")
        try:
            trading_service = TradingService(dev_user, broker_13)
            balance = await trading_service.get_balance()
            print(f"[DIRECT BALANCE SUCCESS] {balance}")
            
            if 'balances' in balance:
                print(f"[BALANCES] Format natif reçu")
                balances = balance['balances']
                for asset, data in balances.items():
                    if data.get('total', 0) > 0:
                        print(f"  - {asset}: disponible={data.get('available', 0)}, total={data.get('total', 0)}")
            else:
                print(f"[BALANCES ERROR] Format inattendu: {list(balance.keys())}")
                
        except Exception as e:
            print(f"[DIRECT BALANCE ERROR] {e}")
            import traceback
            traceback.print_exc()
            
        # Test 3: Comparaison format réponse
        print(f"\n=== TEST 3: Analyse format réponse ===")
        try:
            # Portfolio Service attend format CCXT legacy: balance['total']
            # Service natif retourne: balance['balances'][asset]['total']
            
            # Vérification de la structure
            trading_service = TradingService(dev_user, broker_13)
            native_balance = await trading_service.get_balance()
            
            if 'balances' in native_balance:
                print(f"[FORMAT NATIF] Reçu format natif avec 'balances'")
                print(f"[FORMAT ATTENDU] PortfolioService attend format CCXT avec 'total'")
                print(f"[PROBLÈME IDENTIFIÉ] Incompatibilité format réponse!")
                
                # Montrer la différence
                print(f"\n[NATIF] Structure: {{'balances': {{'USDT': {{'available': X, 'total': Y}}, ...}}}}")
                print(f"[CCXT LEGACY] Structure attendue: {{'total': {{'USDT': Y, ...}}}}")
            else:
                print(f"[FORMAT] Format inconnu: {list(native_balance.keys())}")
                
        except Exception as e:
            print(f"[FORMAT ERROR] {e}")
            
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        print(f"[TRACEBACK] {traceback.format_exc()}")

if __name__ == '__main__':
    asyncio.run(test_portfolio_issue())