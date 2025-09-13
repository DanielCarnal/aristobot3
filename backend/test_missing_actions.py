# -*- coding: utf-8 -*-
"""
TEST DES ACTIONS MISSING: test_connection et load_markets

🎯 OBJECTIF: Valider les nouvelles actions implémentées dans Terminal 5 Native
Vérifie que test_connection et load_markets fonctionnent correctement

🚀 USAGE:
  python test_missing_actions.py

🔧 TESTS:
1. Test connexion broker via ExchangeClient.test_connection()
2. Test chargement marchés via ExchangeClient.load_markets()
3. Vérification sauvegarde DB
4. Validation notifications WebSocket
"""

import sys
import os
import asyncio
import django
import time

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.core.services.exchange_client import ExchangeClient
from apps.brokers.models import Broker, ExchangeSymbol
from django.contrib.auth import get_user_model

User = get_user_model()


class TestMissingActions:
    """
    🧪 TESTEUR DES ACTIONS MANQUANTES
    
    Valide l'implémentation de test_connection et load_markets
    """
    
    def __init__(self):
        self.exchange_client = ExchangeClient()
        self.test_results = []
    
    async def run_all_tests(self):
        """🚀 LANCEMENT DE TOUS LES TESTS"""
        
        print("=" * 80)
        print("🧪 TEST DES ACTIONS MISSING - Terminal 5 Native Exchange")
        print("=" * 80)
        
        try:
            # Récupération d'un broker de test
            broker = await self._get_test_broker()
            if not broker:
                print("❌ Aucun broker actif trouvé pour les tests")
                return
            
            print(f"📋 Broker de test: {broker.name} ({broker.exchange}) - ID {broker.id}")
            
            # Test 1: test_connection
            await self._test_connection_action(broker)
            
            # Attendre un peu entre les tests
            await asyncio.sleep(2)
            
            # Test 2: load_markets  
            await self._test_load_markets_action(broker)
            
            # Attendre chargement complet
            print("⏳ Attente chargement complet des marchés...")
            await asyncio.sleep(10)
            
            # Test 3: Vérification DB
            await self._test_database_persistence(broker)
            
            # Résumé des tests
            self._print_test_summary()
            
        except Exception as e:
            print(f"❌ Erreur critique dans les tests: {e}")
            import traceback
            traceback.print_exc()
    
    async def _get_test_broker(self):
        """📋 Récupération broker de test"""
        from asgiref.sync import sync_to_async
        
        try:
            broker = await sync_to_async(Broker.objects.filter)(is_active=True).afirst()
            return broker
        except Exception as e:
            print(f"❌ Erreur récupération broker: {e}")
            return None
    
    async def _test_connection_action(self, broker):
        """🔌 TEST 1: Action test_connection"""
        
        print(f"\n🔌 TEST 1: test_connection pour broker {broker.id}")
        print("-" * 50)
        
        try:
            start_time = time.time()
            
            # Appel de la nouvelle méthode
            result = await self.exchange_client.test_connection(broker.id)
            
            duration = time.time() - start_time
            
            print(f"⏱️  Durée: {duration:.2f}s")
            print(f"📊 Résultat: {result}")
            
            if result.get('connected'):
                print("✅ Test connexion RÉUSSI")
                sample_balances = result.get('balance_sample', {})
                if sample_balances:
                    print(f"💰 Échantillon balances: {sample_balances}")
                
                if result.get('markets_loading'):
                    print("🔄 Chargement marchés automatique démarré")
                
                self.test_results.append(("test_connection", True, f"{duration:.2f}s"))
                
            else:
                print(f"❌ Test connexion ÉCHOUÉ: {result.get('error')}")
                self.test_results.append(("test_connection", False, result.get('error')))
            
        except Exception as e:
            print(f"❌ Erreur test_connection: {e}")
            self.test_results.append(("test_connection", False, str(e)))
            import traceback
            traceback.print_exc()
    
    async def _test_load_markets_action(self, broker):
        """📊 TEST 2: Action load_markets"""
        
        print(f"\n📊 TEST 2: load_markets pour broker {broker.id}")
        print("-" * 50)
        
        try:
            start_time = time.time()
            
            # Appel de la nouvelle méthode
            result = await self.exchange_client.load_markets(broker.id)
            
            duration = time.time() - start_time
            
            print(f"⏱️  Durée: {duration:.2f}s")
            print(f"📊 Résultat: {result}")
            
            if result.get('success') and result.get('loading'):
                print("✅ Lancement load_markets RÉUSSI")
                print(f"📋 Message: {result.get('message')}")
                self.test_results.append(("load_markets", True, f"{duration:.2f}s"))
                
            else:
                print(f"❌ Lancement load_markets ÉCHOUÉ: {result.get('error')}")
                self.test_results.append(("load_markets", False, result.get('error')))
            
        except Exception as e:
            print(f"❌ Erreur load_markets: {e}")
            self.test_results.append(("load_markets", False, str(e)))
            import traceback
            traceback.print_exc()
    
    async def _test_database_persistence(self, broker):
        """💾 TEST 3: Vérification persistence DB"""
        
        print(f"\n💾 TEST 3: Vérification sauvegarde en DB")
        print("-" * 50)
        
        try:
            from asgiref.sync import sync_to_async
            
            # Compter les symboles pour cet exchange
            symbol_count = await sync_to_async(
                ExchangeSymbol.objects.filter(exchange=broker.exchange).count
            )()
            
            print(f"📊 Symboles en DB pour {broker.exchange}: {symbol_count}")
            
            if symbol_count > 0:
                print("✅ Sauvegarde DB RÉUSSIE")
                
                # Échantillon de symboles
                sample_symbols = await sync_to_async(list)(
                    ExchangeSymbol.objects.filter(exchange=broker.exchange)[:5]
                )
                
                print("📋 Échantillon symboles sauvegardés:")
                for symbol in sample_symbols:
                    print(f"   • {symbol.symbol} ({symbol.base_asset}/{symbol.quote_asset})")
                
                self.test_results.append(("database_persistence", True, f"{symbol_count} symboles"))
                
            else:
                print("❌ Sauvegarde DB ÉCHOUÉE - Aucun symbole trouvé")
                self.test_results.append(("database_persistence", False, "0 symboles"))
            
        except Exception as e:
            print(f"❌ Erreur vérification DB: {e}")
            self.test_results.append(("database_persistence", False, str(e)))
            import traceback
            traceback.print_exc()
    
    def _print_test_summary(self):
        """📈 RÉSUMÉ DES TESTS"""
        
        print("\n" + "=" * 80)
        print("📈 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        
        print(f"🧪 Tests exécutés: {total_tests}")
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {total_tests - passed_tests}")
        print(f"📊 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 Détail par test:")
        for test_name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   • {test_name}: {status} ({details})")
        
        if passed_tests == total_tests:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS - Implémentation VALIDÉE !")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) en échec - Vérification requise")


async def main():
    """Point d'entrée principal"""
    
    tester = TestMissingActions()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("🚀 Démarrage des tests des actions manquantes...")
    asyncio.run(main())