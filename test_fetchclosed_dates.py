# -*- coding: utf-8 -*-
"""
Test fetchClosedOrders avec différentes stratégies de dates
Basé sur la documentation Bitget pour comprendre les contraintes
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

def test_fetchclosed_strategies():
    """Test différentes stratégies pour fetchClosedOrders"""
    
    # Récupérer le broker Bitget
    try:
        user = User.objects.get(username='dev')
        broker = Broker.objects.get(id=13, user=user)
        print(f"Broker sélectionné: {broker.name} (Bitget)")
    except Exception as e:
        print(f"ERREUR récupération broker: {e}")
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
        print(f"Exchange initialisé: {exchange.id}")
    except Exception as e:
        print(f"ERREUR init exchange: {e}")
        return
    
    # Date cible: 2025-02-28 (ordre BTC manquant)
    target_date = datetime(2025, 2, 28)
    target_timestamp = int(target_date.timestamp() * 1000)
    
    print(f"\nRecherche de l'ordre BTC du {target_date.strftime('%Y-%m-%d')}")
    print(f"Timestamp cible: {target_timestamp}")
    
    # === STRATÉGIE 1: fetchClosedOrders sans paramètres ===
    print("\n" + "="*60)
    print("STRATÉGIE 1: fetchClosedOrders() sans paramètres")
    print("="*60)
    
    try:
        closed_orders = exchange.fetch_closed_orders()
        print(f"Résultat: {len(closed_orders)} ordres fermés")
        
        if closed_orders:
            print("Premiers ordres fermés:")
            for i, order in enumerate(closed_orders[:3]):
                order_date = datetime.fromtimestamp(order.get('timestamp', 0) / 1000)
                print(f"  {i+1}. {order.get('symbol')} - {order_date.strftime('%Y-%m-%d %H:%M')} - {order.get('id')}")
        else:
            print("Aucun ordre fermé trouvé")
            
    except Exception as e:
        print(f"ERREUR: {e}")
    
    # === STRATÉGIE 2: Dates récentes (derniers 30 jours) ===
    print("\n" + "="*60)
    print("STRATÉGIE 2: fetchClosedOrders() derniers 30 jours")
    print("="*60)
    
    try:
        since_30_days = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
        print(f"Depuis: {datetime.fromtimestamp(since_30_days/1000).strftime('%Y-%m-%d')}")
        
        closed_orders = exchange.fetch_closed_orders(since=since_30_days)
        print(f"Résultat: {len(closed_orders)} ordres fermés")
        
        # Chercher spécifiquement BTC
        btc_orders = [order for order in closed_orders if 'BTC' in order.get('symbol', '')]
        print(f"Ordres BTC trouvés: {len(btc_orders)}")
        
        if btc_orders:
            print("Ordres BTC fermés:")
            for order in btc_orders:
                order_date = datetime.fromtimestamp(order.get('timestamp', 0) / 1000)
                print(f"  - {order.get('symbol')} {order.get('side')} {order.get('amount')} @ {order.get('price')}")
                print(f"    Date: {order_date.strftime('%Y-%m-%d %H:%M:%S')} - ID: {order.get('id')}")
        
    except Exception as e:
        print(f"ERREUR: {e}")
    
    # === STRATÉGIE 3: Période spécifique autour du 2025-02-28 ===
    print("\n" + "="*60)
    print("STRATÉGIE 3: Période février 2025 (autour du 28/02)")
    print("="*60)
    
    try:
        # Début février 2025
        feb_start = int(datetime(2025, 2, 1).timestamp() * 1000)
        # Fin février 2025  
        feb_end = int(datetime(2025, 3, 1).timestamp() * 1000)
        
        print(f"Période: {datetime.fromtimestamp(feb_start/1000).strftime('%Y-%m-%d')} à {datetime.fromtimestamp(feb_end/1000).strftime('%Y-%m-%d')}")
        
        # Test avec since seulement
        closed_orders = exchange.fetch_closed_orders(since=feb_start, limit=1000)
        print(f"Résultat: {len(closed_orders)} ordres fermés")
        
        # Filtrer dans la période février
        feb_orders = []
        for order in closed_orders:
            order_timestamp = order.get('timestamp', 0)
            if feb_start <= order_timestamp <= feb_end:
                feb_orders.append(order)
        
        print(f"Ordres dans la période février: {len(feb_orders)}")
        
        # Chercher BTC dans cette période
        btc_feb_orders = [order for order in feb_orders if 'BTC' in order.get('symbol', '')]
        print(f"Ordres BTC en février: {len(btc_feb_orders)}")
        
        if btc_feb_orders:
            print("TROUVÉ! Ordres BTC en février 2025:")
            for order in btc_feb_orders:
                order_date = datetime.fromtimestamp(order.get('timestamp', 0) / 1000)
                print(f"  *** {order.get('symbol')} {order.get('side')} {order.get('amount')} @ {order.get('price')}")
                print(f"      Date: {order_date.strftime('%Y-%m-%d %H:%M:%S')} - ID: {order.get('id')}")
                print(f"      Status: {order.get('status')}")
        
    except Exception as e:
        print(f"ERREUR: {e}")
    
    # === STRATÉGIE 4: fetchClosedOrders pour BTC/USDT spécifiquement ===
    print("\n" + "="*60)
    print("STRATÉGIE 4: fetchClosedOrders('BTC/USDT')")
    print("="*60)
    
    try:
        # Test avec symbole spécifique
        since_jan = int(datetime(2025, 1, 1).timestamp() * 1000)
        closed_btc_orders = exchange.fetch_closed_orders('BTC/USDT', since=since_jan, limit=100)
        print(f"Résultat BTC/USDT: {len(closed_btc_orders)} ordres fermés")
        
        if closed_btc_orders:
            print("Ordres BTC/USDT fermés depuis janvier 2025:")
            for order in closed_btc_orders:
                order_date = datetime.fromtimestamp(order.get('timestamp', 0) / 1000)
                print(f"  - {order.get('side')} {order.get('amount')} @ {order.get('price')}")
                print(f"    Date: {order_date.strftime('%Y-%m-%d %H:%M:%S')} - ID: {order.get('id')}")
                print(f"    Status: {order.get('status')}")
                
                # Vérifier si c'est notre ordre du 28/02
                if order_date.strftime('%Y-%m-%d') == '2025-02-28':
                    print("    *** VOICI L'ORDRE MANQUANT DU 28/02! ***")
        
    except Exception as e:
        print(f"ERREUR: {e}")
    
    # === RÉSUMÉ ===
    print("\n" + "="*60)
    print("RÉSUMÉ ET RECOMMANDATIONS")
    print("="*60)
    
    print("Conclusions de l'analyse:")
    print("1. fetchOpenOrders ne montre que les ordres vraiment 'ouverts' (non exécutés)")
    print("2. fetchClosedOrders permet de récupérer l'historique des ordres fermés/exécutés")
    print("3. La contrainte de date semble limiter les requêtes trop anciennes")
    print("4. Il faut probablement utiliser fetchClosedOrders avec un symbole spécifique")
    
    print("\nPour implémenter dans Aristobot:")
    print("- Ajouter un toggle 'Ordres ouverts' / 'Historique'")
    print("- Historique = fetchOpenOrders() + fetchClosedOrders(symbol, since=recent)")
    print("- Utiliser fetchClosedOrders('BTC/USDT') pour voir l'ordre du 28/02")

if __name__ == "__main__":
    print("TEST AVANCÉ fetchClosedOrders avec stratégies de dates")
    print("Recherche de l'ordre BTC/USDT du 2025-02-28")
    print()
    
    test_fetchclosed_strategies()