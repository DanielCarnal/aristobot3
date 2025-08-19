#!/usr/bin/env python
"""
Diagnostic simple des brokers 13 vs 15
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.brokers.models import Broker

def main():
    print("DIAGNOSTIC BROKERS - Comparaison 13 vs 15")
    print("=" * 60)
    
    try:
        broker_13 = Broker.objects.get(id=13)
        broker_15 = Broker.objects.get(id=15)
        
        print(f"\nBROKER 13: {broker_13.name}")
        print(f"   Exchange: {broker_13.exchange}")
        print(f"   Active: {broker_13.is_active}")
        print(f"   Testnet: {broker_13.is_testnet}")
        print(f"   Subaccount: {broker_13.subaccount_name or 'N/A'}")
        print(f"   Last connection: {broker_13.last_connection_test}")
        print(f"   Last success: {broker_13.last_connection_success}")
        
        print(f"\nBROKER 15: {broker_15.name}")
        print(f"   Exchange: {broker_15.exchange}")
        print(f"   Active: {broker_15.is_active}")
        print(f"   Testnet: {broker_15.is_testnet}")
        print(f"   Subaccount: {broker_15.subaccount_name or 'N/A'}")
        print(f"   Last connection: {broker_15.last_connection_test}")
        print(f"   Last success: {broker_15.last_connection_success}")
        
        print(f"\nCOMPARAISON:")
        print(f"   Exchange: {broker_13.exchange} vs {broker_15.exchange}")
        print(f"   Testnet: {broker_13.is_testnet} vs {broker_15.is_testnet}")
        print(f"   Active: {broker_13.is_active} vs {broker_15.is_active}")
        
        if broker_13.exchange != broker_15.exchange:
            print(f"   DIFFERENCE: Exchanges differents!")
        if broker_13.is_testnet != broker_15.is_testnet:
            print(f"   DIFFERENCE: Modes differents!")
        if broker_13.is_active != broker_15.is_active:
            print(f"   DIFFERENCE: Status actifs differents!")
            
        # Test direct CCXT (sans service Redis)
        print(f"\nTEST CCXT DIRECT:")
        
        try:
            client_13 = broker_13.get_ccxt_client()
            print(f"   Broker 13: Client CCXT cree avec succes ({client_13.__class__.__name__})")
        except Exception as e:
            print(f"   Broker 13: ERREUR creation client - {e}")
            
        try:
            client_15 = broker_15.get_ccxt_client()
            print(f"   Broker 15: Client CCXT cree avec succes ({client_15.__class__.__name__})")
        except Exception as e:
            print(f"   Broker 15: ERREUR creation client - {e}")
        
    except Broker.DoesNotExist as e:
        print(f"ERROR: Broker introuvable - {e}")

if __name__ == "__main__":
    main()