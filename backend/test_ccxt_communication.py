# -*- coding: utf-8 -*-
"""
Script de test pour valider la communication avec le service CCXT centralisé
Usage: python test_ccxt_communication.py
"""
import os
import sys
import django
import asyncio
import logging

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.core.services.ccxt_client import CCXTClient
from apps.brokers.models import Broker

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ccxt_communication():
    """Test complet de la communication CCXT"""
    
    print("🧪 Test de communication CCXT centralisé")
    print("=" * 50)
    
    client = CCXTClient()
    
    try:
        # Test 1: Préchargement des brokers
        print("1️⃣ Test préchargement brokers...")
        try:
            result = await client.preload_all_brokers()
            success_count, error_count = result
            print(f"   ✅ Préchargement: {success_count} succès, {error_count} erreurs")
        except Exception as e:
            print(f"   ❌ Erreur préchargement: {e}")
        
        # Test 2: Vérifier si des brokers existent
        print("2️⃣ Vérification brokers en base...")
        try:
            brokers = await Broker.objects.filter(is_active=True).aall()
            broker_count = len(brokers)
            print(f"   📊 {broker_count} broker(s) actif(s) trouvé(s)")
            
            if broker_count == 0:
                print("   ⚠️ Aucun broker configuré - tests limités")
                return
            
            # Test avec le premier broker
            test_broker = brokers[0]
            print(f"   🔄 Test avec broker: {test_broker.name} (ID: {test_broker.id})")
            
            # Test 3: Récupération balance
            print("3️⃣ Test récupération balance...")
            try:
                balance = await client.get_balance(test_broker.id)
                print(f"   ✅ Balance récupérée: {len(balance)} devises")
                
                # Afficher quelques devises principales
                main_currencies = ['USDT', 'BTC', 'ETH', 'USD', 'EUR']
                for currency in main_currencies:
                    if currency in balance and balance[currency]['total'] > 0:
                        total = balance[currency]['total']
                        print(f"      💰 {currency}: {total}")
                        
            except Exception as e:
                print(f"   ❌ Erreur balance: {e}")
            
            # Test 4: Récupération bougies (test limité)
            print("4️⃣ Test récupération bougies...")
            try:
                # Utiliser un symbole commun
                test_symbol = 'BTC/USDT'
                candles = await client.get_candles(
                    test_broker.id, 
                    test_symbol, 
                    '1m', 
                    limit=5
                )
                print(f"   ✅ {len(candles)} bougies récupérées pour {test_symbol}")
                
                # Afficher la dernière bougie
                if candles:
                    last_candle = candles[-1]
                    timestamp, open_price, high, low, close, volume = last_candle
                    print(f"      📊 Dernière bougie: Close={close}, Volume={volume}")
                    
            except Exception as e:
                print(f"   ❌ Erreur bougies: {e}")
                
        except Exception as e:
            print(f"   ❌ Erreur accès base: {e}")
    
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    
    print("=" * 50)
    print("🏁 Test terminé")

async def test_timeout_handling():
    """Test de gestion des timeouts"""
    print("\n🕐 Test gestion timeout...")
    
    client = CCXTClient()
    
    try:
        # Simuler une requête qui pourrait timeout
        # (si le service CCXT n'est pas démarré)
        start_time = asyncio.get_event_loop().time()
        await client.preload_all_brokers()
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"   ✅ Requête réussie en {elapsed:.2f}s")
        
    except Exception as e:
        print(f"   ⚠️ Timeout ou erreur (normal si service non démarré): {e}")

if __name__ == '__main__':
    print("🚀 Démarrage tests CCXT...")
    print("⚠️ Assurez-vous que le service CCXT est démarré:")
    print("   python manage.py run_ccxt_service")
    print()
    
    # Lancer les tests
    asyncio.run(test_ccxt_communication())
    asyncio.run(test_timeout_handling())