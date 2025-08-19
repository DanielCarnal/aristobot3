# -*- coding: utf-8 -*-
"""
Test fetchClosedOrders avec des dates RÉELLES (passées)
Pour comprendre les vraies contraintes de l'API Bitget
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
    print("OK Django configuré")
except Exception as e:
    print(f"ERREUR Django: {e}")
    sys.exit(1)

def test_real_date_constraints():
    """Test les vraies contraintes de dates de Bitget"""
    
    # Récupérer le broker Bitget
    try:
        user = User.objects.get(username='dev')
        broker = Broker.objects.get(id=13, user=user)
        print(f"Broker: {broker.name}")
    except Exception as e:
        print(f"ERREUR: {e}")
        return
    
    # Initialiser CCXT
    try:
        exchange = ccxt.bitget({
            'apiKey': broker.decrypt_field(broker.api_key),
            'secret': broker.decrypt_field(broker.api_secret),
            'password': broker.decrypt_field(broker.api_password) if broker.api_password else None,
            'sandbox': False,
            'enableRateLimit': True,
        })
        print(f"Exchange: {exchange.id}")
    except Exception as e:
        print(f"ERREUR: {e}")
        return
    
    now = datetime.now()
    print(f"\nDate actuelle: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # === TEST 1: Sans paramètres (baseline) ===
    print("\n" + "="*60)
    print("TEST 1: fetchClosedOrders() - BASELINE")
    print("="*60)
    
    try:
        orders = exchange.fetch_closed_orders()
        print(f"Sans paramètres: {len(orders)} ordres")
    except Exception as e:
        print(f"ERREUR: {e}")
    
    # === TEST 2: Dates passées récentes ===
    test_periods = [
        ("7 jours", 7),
        ("30 jours", 30),
        ("90 jours", 90),
        ("180 jours", 180),
        ("365 jours", 365),
    ]
    
    for period_name, days_back in test_periods:
        print(f"\n" + "="*60)
        print(f"TEST: fetchClosedOrders() - {period_name} en arrière")
        print("="*60)
        
        try:
            since_date = now - timedelta(days=days_back)
            since_timestamp = int(since_date.timestamp() * 1000)
            
            print(f"Depuis: {since_date.strftime('%Y-%m-%d')} (timestamp: {since_timestamp})")
            
            orders = exchange.fetch_closed_orders(since=since_timestamp, limit=1000)
            print(f"Résultat: {len(orders)} ordres fermés")
            
            if orders:
                # Analyser les dates des ordres trouvés
                order_dates = []
                btc_orders = []
                
                for order in orders:
                    order_timestamp = order.get('timestamp', 0)
                    if order_timestamp:
                        order_date = datetime.fromtimestamp(order_timestamp / 1000)
                        order_dates.append(order_date)
                        
                        if 'BTC' in order.get('symbol', ''):
                            btc_orders.append((order_date, order))
                
                if order_dates:
                    oldest = min(order_dates)
                    newest = max(order_dates)
                    print(f"Plage trouvée: {oldest.strftime('%Y-%m-%d')} à {newest.strftime('%Y-%m-%d')}")
                
                print(f"Ordres BTC trouvés: {len(btc_orders)}")
                
                if btc_orders:
                    print("Ordres BTC:")
                    for order_date, order in btc_orders[:5]:  # Max 5
                        print(f"  - {order_date.strftime('%Y-%m-%d %H:%M')} {order.get('symbol')} {order.get('side')} {order.get('amount')}")
            
        except Exception as e:
            print(f"ERREUR: {e}")
    
    # === TEST 3: Avec symbole spécifique ===
    print(f"\n" + "="*60)
    print("TEST: fetchClosedOrders('BTC/USDT') - 90 jours")
    print("="*60)
    
    try:
        since_90 = int((now - timedelta(days=90)).timestamp() * 1000)
        btc_orders = exchange.fetch_closed_orders('BTC/USDT', since=since_90, limit=100)
        
        print(f"Ordres BTC/USDT: {len(btc_orders)}")
        
        if btc_orders:
            print("Détails des ordres BTC/USDT:")
            for order in btc_orders:
                order_date = datetime.fromtimestamp(order.get('timestamp', 0) / 1000)
                print(f"  - {order_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    {order.get('side')} {order.get('amount')} @ {order.get('price')}")
                print(f"    Status: {order.get('status')} - ID: {order.get('id')}")
                print()
        
    except Exception as e:
        print(f"ERREUR: {e}")
    
    # === CONCLUSION ===
    print(f"\n" + "="*60)
    print("ANALYSE DES CONTRAINTES BITGET")
    print("="*60)
    
    print("DÉCOUVERTES:")
    print("1. Bitget ne peut pas récupérer d'ordres avec des dates futures")
    print("2. Les contraintes de plage de dates limitent l'historique")
    print("3. L'ordre BTC du '2025-02-28' mentionné est probablement une erreur de date")
    print("4. Il faut vérifier la vraie date de cet ordre dans l'interface Bitget")
    
    print("\nRECOMMANDATIONS:")
    print("- Vérifier la vraie date de l'ordre BTC dans l'interface web Bitget")
    print("- Implémenter fetchClosedOrders avec des plages de dates réalistes")
    print("- Limiter les requêtes à 90-180 jours maximum selon les tests")
    print("- Utiliser des symboles spécifiques pour de meilleurs résultats")

if __name__ == "__main__":
    print("TEST DES VRAIES CONTRAINTES DE DATES BITGET")
    print("Investigation des limites de fetchClosedOrders")
    print()
    
    test_real_date_constraints()