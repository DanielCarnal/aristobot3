# -*- coding: utf-8 -*-
"""
Script de test COMPLET pour analyser toutes les méthodes d'ordres Bitget via CCXT
Utilise la DB Django pour récupérer les informations du broker
Version sans emoji pour compatibilité Windows
"""
import os
import sys
import django
import ccxt
from datetime import datetime, timedelta

# Configuration Django
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, 'backend')
sys.path.insert(0, backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

try:
    django.setup()
    from apps.brokers.models import Broker
    from django.contrib.auth import get_user_model
    User = get_user_model()
    print("OK Django configuré avec succès")
except Exception as e:
    print(f"ERREUR configuration Django: {e}")
    print(f"Script dir: {script_dir}")
    print(f"Backend dir: {backend_dir}")
    sys.exit(1)

def print_separator(title):
    """Affiche un séparateur visuel"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def format_order(order, index=None):
    """Formate un ordre pour l'affichage"""
    prefix = f"  Ordre {index+1}:" if index is not None else "  Ordre:"
    
    print(prefix)
    print(f"    ID: {order.get('id', 'N/A')}")
    print(f"    Symbol: {order.get('symbol', 'N/A')}")
    print(f"    Side: {order.get('side', 'N/A')}")
    print(f"    Type: {order.get('type', 'N/A')}")
    print(f"    Amount: {order.get('amount', 'N/A')}")
    print(f"    Price: {order.get('price', 'N/A')}")
    print(f"    Status: {order.get('status', 'N/A')}")
    print(f"    Filled: {order.get('filled', 'N/A')}")
    print(f"    Remaining: {order.get('remaining', 'N/A')}")
    
    # Formatage de la date
    timestamp = order.get('timestamp')
    if timestamp:
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
            print(f"    Date: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            print(f"    Timestamp: {timestamp}")
    else:
        print(f"    Date: N/A")
    
    print(f"    Info brute: {str(order.get('info', {}))[:100]}...")
    print()

def get_broker_from_db(broker_id=None, user_username='dev'):
    """Récupère les informations du broker depuis la DB Django"""
    try:
        # Récupérer l'utilisateur
        user = User.objects.get(username=user_username)
        print(f"OK Utilisateur trouvé: {user.username}")
        
        # Récupérer les brokers de l'utilisateur
        brokers = Broker.objects.filter(user=user)
        print(f"OK {len(brokers)} broker(s) trouvé(s) pour {user.username}")
        
        for broker in brokers:
            print(f"   - Broker ID {broker.id}: {broker.name} ({broker.exchange})")
        
        # Sélectionner le broker
        if broker_id:
            try:
                broker = Broker.objects.get(id=broker_id, user=user)
            except Broker.DoesNotExist:
                print(f"ERREUR Broker ID {broker_id} non trouvé")
                return None
        else:
            # Prendre le premier broker Bitget
            bitget_brokers = brokers.filter(exchange='bitget')
            if not bitget_brokers.exists():
                print("ERREUR Aucun broker Bitget trouvé")
                return None
            broker = bitget_brokers.first()
        
        print(f"SELECTION Broker: {broker.name} (ID: {broker.id})")
        print(f"   Exchange: {broker.exchange}")
        print(f"   API Key: {broker.api_key[:8]}..." if broker.api_key else "   API Key: Non configurée")
        
        return broker
        
    except User.DoesNotExist:
        print(f"ERREUR Utilisateur '{user_username}' non trouvé")
        return None
    except Exception as e:
        print(f"ERREUR récupération broker: {e}")
        return None

def test_bitget_orders(broker_id=None, user_username='dev'):
    """Test complet des méthodes d'ordres Bitget"""
    
    print_separator("RÉCUPÉRATION BROKER DEPUIS DB")
    
    # Récupérer le broker depuis la DB
    broker = get_broker_from_db(broker_id, user_username)
    if not broker:
        return
    
    # Vérifier que les clés API sont configurées
    if not all([broker.api_key, broker.api_secret, broker.api_password]):
        print("ERREUR: Clés API manquantes dans le broker:")
        print(f"   - API Key: {'OK' if broker.api_key else 'MANQUANT'}")
        print(f"   - API Secret: {'OK' if broker.api_secret else 'MANQUANT'}")
        print(f"   - API Password: {'OK' if broker.api_password else 'MANQUANT'}")
        print("\nConfigurez les clés API dans l'interface Aristobot")
        return
    
    try:
        # Initialiser CCXT avec les données du broker
        exchange_class = getattr(ccxt, broker.exchange.lower())
        exchange = exchange_class({
            'apiKey': broker.decrypt_field(broker.api_key),
            'secret': broker.decrypt_field(broker.api_secret),
            'password': broker.decrypt_field(broker.api_password) if broker.api_password else None,  # Bitget utilise 'password' pour la passphrase
            'sandbox': broker.is_testnet if hasattr(broker, 'is_testnet') else False,
            'enableRateLimit': True,
        })
        
        print_separator("INITIALISATION CCXT BITGET")
        print(f"Exchange initialisé: {exchange.id}")
        print(f"   Version CCXT: {ccxt.__version__}")
        
        # 1. Tester les capacités
        print_separator("CAPACITÉS DE L'EXCHANGE")
        capabilities = {
            'fetchOpenOrders': exchange.has.get('fetchOpenOrders', False),
            'fetchClosedOrders': exchange.has.get('fetchClosedOrders', False), 
            'fetchMyTrades': exchange.has.get('fetchMyTrades', False),
            'fetchOrders': exchange.has.get('fetchOrders', False),
        }
        
        for method, supported in capabilities.items():
            status = "OK" if supported else "NON SUPPORTÉ"
            print(f"   {status} {method}: {supported}")
        
        # 2. Test fetchOpenOrders (référence actuelle)
        print_separator("TEST fetchOpenOrders (ACTUEL)")
        try:
            open_orders = exchange.fetch_open_orders()
            print(f"fetchOpenOrders réussie")
            print(f"   Nombre d'ordres ouverts: {len(open_orders)}")
            
            if open_orders:
                print("\n   Détails des ordres ouverts:")
                for i, order in enumerate(open_orders):
                    format_order(order, i)
            else:
                print("   Aucun ordre ouvert trouvé")
                
        except Exception as e:
            print(f"ERREUR fetchOpenOrders: {e}")
        
        # 3. Test fetchClosedOrders
        if capabilities['fetchClosedOrders']:
            print_separator("TEST fetchClosedOrders")
            
            # Test sans paramètres
            try:
                closed_orders = exchange.fetch_closed_orders()
                print(f"fetchClosedOrders réussie (sans paramètres)")
                print(f"   Nombre d'ordres fermés: {len(closed_orders)}")
                
                if closed_orders:
                    print("\n   Premiers ordres fermés:")
                    for i, order in enumerate(closed_orders[:5]):  # Afficher seulement les 5 premiers
                        format_order(order, i)
                        
                    if len(closed_orders) > 5:
                        print(f"   ... et {len(closed_orders) - 5} autres ordres")
                        
                else:
                    print("   Aucun ordre fermé trouvé")
                    
            except Exception as e:
                print(f"ERREUR fetchClosedOrders: {e}")
            
            # Test avec date ancienne pour trouver l'ordre BTC
            try:
                print(f"\n   Test avec date ancienne (depuis 2024-01-01)...")
                since_date = datetime(2024, 1, 1)
                since_timestamp = int(since_date.timestamp() * 1000)
                
                old_closed_orders = exchange.fetch_closed_orders(since=since_timestamp, limit=1000)
                print(f"fetchClosedOrders avec date ancienne réussie")
                print(f"   Nombre d'ordres depuis 2024: {len(old_closed_orders)}")
                
                # Chercher spécifiquement les ordres BTC
                btc_orders = [order for order in old_closed_orders if 'BTC' in order.get('symbol', '')]
                print(f"   Ordres BTC trouvés: {len(btc_orders)}")
                
                if btc_orders:
                    print("\n   Ordres BTC fermés:")
                    for i, order in enumerate(btc_orders):
                        format_order(order, i)
                        
            except Exception as e:
                print(f"ERREUR fetchClosedOrders avec date: {e}")
        
        # 4. Test fetchMyTrades
        if capabilities['fetchMyTrades']:
            print_separator("TEST fetchMyTrades")
            
            try:
                # Test général
                my_trades = exchange.fetch_my_trades(limit=100)
                print(f"fetchMyTrades réussie")
                print(f"   Nombre de trades: {len(my_trades)}")
                
                if my_trades:
                    print("\n   Premiers trades:")
                    for i, trade in enumerate(my_trades[:3]):  # Afficher seulement les 3 premiers
                        print(f"    Trade {i+1}:")
                        print(f"      ID: {trade.get('id', 'N/A')}")
                        print(f"      Symbol: {trade.get('symbol', 'N/A')}")
                        print(f"      Side: {trade.get('side', 'N/A')}")
                        print(f"      Amount: {trade.get('amount', 'N/A')}")
                        print(f"      Price: {trade.get('price', 'N/A')}")
                        
                        timestamp = trade.get('timestamp')
                        if timestamp:
                            dt = datetime.fromtimestamp(timestamp / 1000)
                            print(f"      Date: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                        print()
                        
                    if len(my_trades) > 3:
                        print(f"   ... et {len(my_trades) - 3} autres trades")
                
            except Exception as e:
                print(f"ERREUR fetchMyTrades: {e}")
                
            # Test spécifique pour BTC/USDT
            try:
                print(f"\n   Test fetchMyTrades pour BTC/USDT...")
                btc_trades = exchange.fetch_my_trades('BTC/USDT', limit=50)
                print(f"fetchMyTrades BTC/USDT réussie")
                print(f"   Nombre de trades BTC: {len(btc_trades)}")
                
                if btc_trades:
                    print("\n   Derniers trades BTC:")
                    for i, trade in enumerate(btc_trades[-3:]):  # Les 3 derniers
                        print(f"    Trade BTC {i+1}:")
                        print(f"      Date: {datetime.fromtimestamp(trade.get('timestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"      Side: {trade.get('side', 'N/A')}")
                        print(f"      Amount: {trade.get('amount', 'N/A')}")
                        print(f"      Price: {trade.get('price', 'N/A')}")
                        print()
                        
            except Exception as e:
                print(f"ERREUR fetchMyTrades BTC/USDT: {e}")
        
        # 5. Résumé et recommandations
        print_separator("RÉSUMÉ ET RECOMMANDATIONS")
        
        print("RÉSUMÉ DES TESTS:")
        working_methods = [method for method, supported in capabilities.items() if supported]
        print(f"   Méthodes supportées: {', '.join(working_methods)}")
        
        print(f"\nRECOMMANDATIONS POUR ARISTOBOT:")
        print(f"   1. Conserver fetchOpenOrders pour les ordres actifs")
        
        if capabilities['fetchClosedOrders']:
            print(f"   2. Ajouter fetchClosedOrders pour voir les ordres fermés/annulés")
            print(f"      - Permet de voir l'historique des ordres")
            print(f"      - Probablement où se trouve l'ordre BTC ancien")
            
        if capabilities['fetchMyTrades']:
            print(f"   3. Ajouter fetchMyTrades pour l'historique complet")
            print(f"      - Donne les transactions réellement exécutées")
            print(f"      - Complémentaire aux ordres fermés")
            
        print(f"\nSTRATÉGIE D'IMPLÉMENTATION SUGGÉRÉE:")
        print(f"   - Interface avec toggle: 'Ordres ouverts' / 'Historique complet'")
        print(f"   - Historique = fetchOpenOrders + fetchClosedOrders")
        print(f"   - Optionnel: section séparée 'Mes trades' avec fetchMyTrades")
        
    except Exception as e:
        print(f"ERREUR GÉNÉRALE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("SCRIPT DE TEST CCXT BITGET COMPLET")
    print("Utilise la base de données Django pour récupérer les informations du broker")
    print()
    
    # Paramètres du test
    # Vous pouvez spécifier un broker_id spécifique ou laisser None pour auto-sélection
    BROKER_ID = 13  # Changez selon vos besoins, ou None pour auto
    USER_USERNAME = 'dev'  # Changez selon vos besoins
    
    print(f"Configuration du test:")
    print(f"   - Broker ID: {BROKER_ID if BROKER_ID else 'Auto-sélection'}")
    print(f"   - Utilisateur: {USER_USERNAME}")
    print()
    
    test_bitget_orders(BROKER_ID, USER_USERNAME)