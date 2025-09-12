# -*- coding: utf-8 -*-
"""
TEST SUPPORT MULTI-EXCHANGE - Validation Terminal 7

🎯 OBJECTIF: Vérifier que tous les exchanges sont maintenant supportés
Teste la création des clients Bitget, Binance et Kraken

Usage:
  python test_exchanges_support.py
"""

import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import django
django.setup()

from apps.core.services.base_exchange_client import ExchangeClientFactory

def test_exchange_support():
    """Test support des exchanges pour Terminal 7"""
    
    print("🧪 TEST SUPPORT MULTI-EXCHANGE pour Terminal 7")
    print("=" * 60)
    
    # Liste des exchanges requis
    required_exchanges = ['bitget', 'binance', 'kraken']
    
    # Test 1: Vérifier la liste des exchanges supportés
    supported_exchanges = ExchangeClientFactory.list_supported_exchanges()
    
    print(f"📋 Exchanges supportés: {supported_exchanges}")
    
    # Test 2: Vérifier chaque exchange
    all_supported = True
    
    for exchange in required_exchanges:
        try:
            # Tentative de création d'un client avec des credentials de test
            client = ExchangeClientFactory.create_client(
                exchange_name=exchange,
                api_key='test_key',
                api_secret='test_secret',
                api_passphrase='test_passphrase',
                is_testnet=True
            )
            
            print(f"✅ {exchange.upper()}: Client créé avec succès ({client.__class__.__name__})")
            
        except ValueError as e:
            print(f"❌ {exchange.upper()}: {e}")
            all_supported = False
        except Exception as e:
            print(f"⚠️  {exchange.upper()}: Erreur inattendue - {e}")
            all_supported = False
    
    # Résultat final
    print("\n" + "=" * 60)
    if all_supported:
        print("🎉 TOUS LES EXCHANGES SUPPORTÉS!")
        print("✅ Terminal 7 peut maintenant fonctionner avec Bitget, Binance et Kraken")
        print("✅ Le problème de support multi-exchange est résolu")
    else:
        print("❌ CERTAINS EXCHANGES MANQUENT")
        print("⚠️  Terminal 7 ne peut pas fonctionner correctement")
    
    print("=" * 60)
    
    return all_supported

if __name__ == "__main__":
    test_exchange_support()