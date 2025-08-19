#!/usr/bin/env python
"""
Script de diagnostic pour les timeouts du broker 15
Comparaison avec le broker 13 qui fonctionne bien
"""
import os
import sys
import django
import asyncio
import time
from datetime import datetime
from asgiref.sync import sync_to_async

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.brokers.models import Broker
from apps.core.services.ccxt_client import CCXTClient

class BrokerDiagnostic:
    def __init__(self):
        self.ccxt_client = CCXTClient()
        
    def print_broker_info(self, broker):
        """Affiche les informations d'un broker"""
        print(f"\nBROKER {broker.id}: {broker.name}")
        print(f"   Exchange: {broker.exchange}")
        print(f"   Active: {broker.is_active}")
        print(f"   Testnet: {broker.is_testnet}")
        print(f"   API Key: {'OK' if broker.api_key else 'MISSING'}")
        print(f"   API Secret: {'OK' if broker.api_secret else 'MISSING'}")
        print(f"   API Password: {'OK' if broker.api_password else 'MISSING'}")
        print(f"   Subaccount: {broker.subaccount_name or 'N/A'}")
        print(f"   Derniere connexion: {broker.last_connection_test or 'Jamais'}")
        print(f"   Derniere connexion reussie: {broker.last_connection_success}")
        
    async def test_broker_operations(self, broker_id):
        """Test les opérations CCXT pour un broker"""
        print(f"\nTEST OPERATIONS BROKER {broker_id}")
        
        operations = [
            ('get_ticker', {'symbol': 'BTC/USDT'}),
            ('get_markets', {}),
            ('get_balance', {})
        ]
        
        results = {}
        
        for operation, extra_params in operations:
            print(f"\n   Test {operation}...")
            start_time = time.time()
            
            try:
                params = {'broker_id': broker_id, **extra_params}
                
                if operation == 'get_ticker':
                    result = await self.ccxt_client.get_ticker(broker_id, 'BTC/USDT')
                elif operation == 'get_markets':
                    result = await self.ccxt_client.get_markets(broker_id)
                elif operation == 'get_balance':
                    result = await self.ccxt_client.get_balance(broker_id)
                
                duration = time.time() - start_time
                results[operation] = {
                    'success': True,
                    'duration': duration,
                    'data_size': len(str(result)) if result else 0
                }
                print(f"   SUCCESS {operation}: {duration:.1f}s (donnees: {results[operation]['data_size']} chars)")
                
            except Exception as e:
                duration = time.time() - start_time
                results[operation] = {
                    'success': False,
                    'duration': duration,
                    'error': str(e)
                }
                print(f"   ERROR {operation}: {duration:.1f}s - {e}")
        
        return results
    
    async def run_diagnosis(self):
        """Exécute le diagnostic complet"""
        print("DIAGNOSTIC BROKERS - Comparaison 13 vs 15")
        print("=" * 60)
        
        # Récupérer les brokers
        try:
            broker_13 = await sync_to_async(Broker.objects.get)(id=13)
            broker_15 = await sync_to_async(Broker.objects.get)(id=15)
        except Broker.DoesNotExist as e:
            print(f"ERROR Broker non trouve: {e}")
            return
        
        # Afficher les infos des brokers
        self.print_broker_info(broker_13)
        self.print_broker_info(broker_15)
        
        print(f"\nCOMPARAISON DES CONFIGURATIONS")
        print(f"   Exchange: {broker_13.exchange} vs {broker_15.exchange}")
        print(f"   Testnet: {broker_13.is_testnet} vs {broker_15.is_testnet}")
        print(f"   Subaccount: {broker_13.subaccount_name or 'N/A'} vs {broker_15.subaccount_name or 'N/A'}")
        
        # Test des opérations
        print(f"\nTESTS DE PERFORMANCE")
        
        # Broker 13 (référence)
        results_13 = await self.test_broker_operations(13)
        
        # Broker 15 (problématique)  
        results_15 = await self.test_broker_operations(15)
        
        # Analyse comparative
        print(f"\nANALYSE COMPARATIVE")
        print("=" * 60)
        
        for operation in ['get_ticker', 'get_markets', 'get_balance']:
            r13 = results_13.get(operation, {})
            r15 = results_15.get(operation, {})
            
            print(f"\n{operation.upper()}")
            
            if r13.get('success') and r15.get('success'):
                ratio = r15['duration'] / r13['duration'] if r13['duration'] > 0 else float('inf')
                print(f"   Broker 13: SUCCESS {r13['duration']:.1f}s")
                print(f"   Broker 15: SUCCESS {r15['duration']:.1f}s")
                print(f"   Ratio: {ratio:.1f}x {'LENT' if ratio > 2 else 'OK'}")
            else:
                print(f"   Broker 13: {'SUCCESS' if r13.get('success') else 'ERROR'} {r13.get('duration', 0):.1f}s")
                print(f"   Broker 15: {'SUCCESS' if r15.get('success') else 'ERROR'} {r15.get('duration', 0):.1f}s")
                if not r15.get('success'):
                    print(f"   ERROR 15: {r15.get('error', 'Unknown')}")
        
        # Recommandations
        print(f"\nRECOMMANDATIONS")
        print("=" * 60)
        
        # Analyser les patterns d'erreur
        failed_ops_15 = [op for op, result in results_15.items() if not result.get('success')]
        slow_ops_15 = [op for op, result in results_15.items() if result.get('success') and result.get('duration', 0) > 10]
        
        if failed_ops_15:
            print(f"Operations echouees sur Broker 15: {', '.join(failed_ops_15)}")
            print("   -> Verifier les credentials et la connectivite API")
        
        if slow_ops_15:
            print(f"Operations lentes sur Broker 15: {', '.join(slow_ops_15)}")
            print("   -> Augmenter les timeouts ou implementer un cache")
        
        # Comparer les exchanges
        if broker_13.exchange != broker_15.exchange:
            print(f"Exchanges differents: {broker_13.exchange} vs {broker_15.exchange}")
            print("   -> Performance variable selon l'API de l'exchange")
        
        if broker_13.is_testnet != broker_15.is_testnet:
            print(f"Modes differents: {'Testnet' if broker_13.is_testnet else 'Live'} vs {'Testnet' if broker_15.is_testnet else 'Live'}")
            print("   -> Les APIs testnet peuvent etre plus lentes")

if __name__ == "__main__":
    diagnostic = BrokerDiagnostic()
    asyncio.run(diagnostic.run_diagnosis())