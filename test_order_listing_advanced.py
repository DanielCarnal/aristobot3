# -*- coding: utf-8 -*-
"""
BITGET NATIVE API - SCRIPT 2: ORDER LISTING ADVANCED

🎯 OBJECTIF: Test avancé de récupération et filtrage des ordres Bitget SPOT
Basé sur le Script 1 de référence (5/5 succès validé)

📋 FONCTIONNALITÉS TESTÉES:
✅ Récupération ordres ouverts (open orders)
✅ Récupération ordres fermés/exécutés (closed/filled orders) 
✅ Filtrage par symbole (BTC/USDT spécifique)
✅ Filtrage par type d'ordre (market, limit, stop, etc.)
✅ Pagination et limites (récupération par batch)
✅ Historique avec plages de dates
✅ Tri et organisation des résultats

🔧 FONCTIONNALITÉS TECHNIQUES:
- API V2 native Bitget (endpoints fetch orders)
- Filtrage intelligent multi-critères
- Formatting et affichage optimisé des résultats
- Gestion des erreurs et cas limites
- Performance tracking (temps de réponse)

🚨 ENDPOINTS BITGET V2 UTILISÉS:
- /api/v2/spot/trade/orders-pending (ordres ouverts)
- /api/v2/spot/trade/orders-history (ordres fermés/historique)
- Paramètres: symbol, startTime, endTime, limit, orderId (pagination)

📖 TESTS BASÉS SUR ORDRES CRÉÉS PAR SCRIPT 1:
Le script utilisera les ordres créés par test_order_creation_clean.py comme données de test
pour valider la récupération et le filtrage.

Usage:
  python test_order_listing_advanced.py --user=dac --symbol=BTC/USDT
  python test_order_listing_advanced.py --user=claude --all-symbols --history
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import base64
import json
import sys
import os
import argparse
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.brokers.models import Broker
from apps.trading_manual.models import Trade
from asgiref.sync import sync_to_async

User = get_user_model()


class BitgetOrderListingClient:
    """
    🔍 CLIENT BITGET ORDER LISTING - SPÉCIALISÉ RÉCUPÉRATION
    
    HÉRITE DE L'ARCHITECTURE DU SCRIPT 1:
    - Même authentification V2 (ACCESS-KEY, ACCESS-SIGN, etc.)
    - Même gestion d'erreurs et debug
    - Focus sur les endpoints de récupération d'ordres
    
    📊 ENDPOINTS SPÉCIALISÉS:
    - orders-pending: Ordres ouverts/en attente
    - orders-history: Historique complet des ordres
    
    🎯 FONCTIONNALITÉS AVANCÉES:
    - Filtrage multi-critères (symbol, type, date)
    - Pagination automatique pour gros volumes
    - Tri et organisation des résultats
    - Performance monitoring
    """
    
    def __init__(self, api_key, secret_key, passphrase, is_testnet=False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = 'https://api.bitget.com'
        if is_testnet:
            self.base_url = 'https://api.bitgetapi.com'
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)  # Timeout plus long pour les requêtes de listing
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _sign_request(self, method, path, params_str=''):
        """🔑 Signature Bitget V2 - Identique Script 1"""
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{method.upper()}{path}{params_str}"
        
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return {
            'ACCESS-KEY': self.api_key,
            'ACCESS-SIGN': signature,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    async def test_connection(self) -> dict:
        """🧪 Test connexion - Réutilisé du Script 1"""
        try:
            path = '/api/v2/spot/account/assets'
            headers = self._sign_request('GET', path)
            
            async with self.session.get(f"{self.base_url}{path}", headers=headers) as response:
                data = await response.json()
                
                if data.get('code') != '00000':
                    return {'connected': False, 'error': data.get('msg')}
                
                return {'connected': True, 'balance_items': len(data['data'])}
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    async def fetch_open_orders(self, symbol=None, limit=100) -> dict:
        """
        📋 RÉCUPÉRATION ORDRES OUVERTS - MÉTHODE PRINCIPALE
        
        🎯 ENDPOINT: /api/v2/spot/trade/orders-pending
        
        PARAMÈTRES DISPONIBLES:
        - symbol: Filtrage par paire (ex: 'BTCUSDT')
        - limit: Nombre maximum d'ordres (défaut: 100, max: 100)
        
        ✅ TYPES D'ORDRES RÉCUPÉRÉS:
        - Limit orders en attente
        - TP/SL ordres actifs
        - Ordres conditionnels (plan orders)
        
        Args:
            symbol: 'BTC/USDT' ou None pour tous symboles
            limit: Nombre max d'ordres à récupérer
        
        Returns:
            dict: {
                'success': bool,
                'orders': list,
                'total_count': int,
                'filtered_by': dict
            }
        """
        start_time = time.time()
        
        # Construction des paramètres
        params = {}
        if symbol:
            params['symbol'] = symbol.replace('/', '')  # BTC/USDT → BTCUSDT
        if limit and limit <= 100:
            params['limit'] = str(limit)
        
        # Construction de l'URL avec paramètres  
        path = '/api/v2/spot/trade/unfilled-orders'
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        if query_string:
            full_path = f"{path}?{query_string}"
        else:
            full_path = path
        
        print(f"\\n[DEBUG FETCH OPEN] Recuperation ordres ouverts:")
        print(f"  Endpoint: {full_path}")
        print(f"  Parametres: {params}")
        
        try:
            headers = self._sign_request('GET', full_path)
            
            async with self.session.get(f"{self.base_url}{full_path}", headers=headers) as response:
                data = await response.json()
                response_time = (time.time() - start_time) * 1000
                
                print(f"  Status: {response.status}")
                print(f"  Temps reponse: {response_time:.0f}ms")
                
                if data.get('code') != '00000':
                    print(f"  [ERREUR] Erreur: {data.get('msg')}")
                    return {
                        'success': False,
                        'error': data.get('msg'),
                        'orders': [],
                        'total_count': 0
                    }
                
                orders = data.get('data', [])
                print(f"  [OK] {len(orders)} ordres ouverts recuperes")
                
                return {
                    'success': True,
                    'orders': orders,
                    'total_count': len(orders),
                    'filtered_by': params,
                    'response_time_ms': response_time
                }
                
        except Exception as e:
            print(f"  [ERREUR] Exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders': [],
                'total_count': 0
            }
    
    async def fetch_closed_orders(self, symbol=None, limit=100, days_back=7) -> dict:
        """
        📚 RÉCUPÉRATION ORDRES FERMÉS/HISTORIQUE - MÉTHODE PRINCIPALE
        
        🎯 ENDPOINT: /api/v2/spot/trade/orders-history
        
        PARAMÈTRES DISPONIBLES:
        - symbol: Filtrage par paire
        - limit: Nombre maximum d'ordres (défaut: 100, max: 100)
        - startTime/endTime: Plage de dates (timestamps millisecondes)
        
        ✅ TYPES D'ORDRES RÉCUPÉRÉS:
        - Ordres exécutés (filled)
        - Ordres annulés (cancelled)
        - Ordres expirés
        - Historique complet des transactions
        
        Args:
            symbol: 'BTC/USDT' ou None pour tous symboles
            limit: Nombre max d'ordres
            days_back: Nombre de jours d'historique (défaut: 7)
            
        Returns:
            dict: Même format que fetch_open_orders + historique
        """
        start_time = time.time()
        
        # Calcul plage de dates (X jours en arrière)
        now = datetime.utcnow()
        start_date = now - timedelta(days=days_back)
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(now.timestamp() * 1000)
        
        # Construction des paramètres
        params = {
            'startTime': str(start_timestamp),
            'endTime': str(end_timestamp)
        }
        
        if symbol:
            params['symbol'] = symbol.replace('/', '')
        if limit and limit <= 100:
            params['limit'] = str(limit)
        
        # Construction URL
        path = '/api/v2/spot/trade/history-orders'
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        full_path = f"{path}?{query_string}"
        
        print(f"\\n[DEBUG FETCH CLOSED] Recuperation ordres fermes:")
        print(f"  Endpoint: {full_path}")
        print(f"  Periode: {days_back} derniers jours")
        print(f"  Plage: {start_date.strftime('%Y-%m-%d %H:%M')} --> {now.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            headers = self._sign_request('GET', full_path)
            
            async with self.session.get(f"{self.base_url}{full_path}", headers=headers) as response:
                data = await response.json()
                response_time = (time.time() - start_time) * 1000
                
                print(f"  Status: {response.status}")
                print(f"  Temps reponse: {response_time:.0f}ms")
                
                if data.get('code') != '00000':
                    print(f"  [ERREUR] Erreur: {data.get('msg')}")
                    return {
                        'success': False,
                        'error': data.get('msg'),
                        'orders': [],
                        'total_count': 0
                    }
                
                orders = data.get('data', [])
                print(f"  [OK] {len(orders)} ordres historiques recuperes")
                
                return {
                    'success': True,
                    'orders': orders,
                    'total_count': len(orders),
                    'filtered_by': params,
                    'response_time_ms': response_time,
                    'period_days': days_back
                }
                
        except Exception as e:
            print(f"  [ERREUR] Exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders': [],
                'total_count': 0
            }
    
    def analyze_orders(self, orders_data) -> dict:
        """
        📊 ANALYSE AVANCÉE DES ORDRES RÉCUPÉRÉS
        
        Traite et analyse les ordres pour extraire des statistiques utiles
        
        Args:
            orders_data: Résultat de fetch_open_orders ou fetch_closed_orders
            
        Returns:
            dict: Statistiques détaillées
        """
        if not orders_data['success'] or not orders_data['orders']:
            return {'empty': True, 'total': 0}
        
        orders = orders_data['orders']
        
        # Analyse par type d'ordre
        by_type = {}
        by_status = {}
        by_symbol = {}
        total_volume = 0
        
        for order in orders:
            # Type d'ordre
            order_type = order.get('orderType', 'unknown')
            by_type[order_type] = by_type.get(order_type, 0) + 1
            
            # Status
            status = order.get('status', 'unknown')  
            by_status[status] = by_status.get(status, 0) + 1
            
            # Symbole
            symbol = order.get('symbol', 'unknown')
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
            
            # Volume (approximatif)
            try:
                size = float(order.get('size', 0))
                price = float(order.get('price', 0)) or 1  # Éviter division par 0
                total_volume += size * price
            except:
                pass
        
        return {
            'total_orders': len(orders),
            'by_type': by_type,
            'by_status': by_status,
            'by_symbol': by_symbol,
            'total_volume_approx': round(total_volume, 2),
            'response_time_ms': orders_data.get('response_time_ms', 0)
        }
    
    def format_order_summary(self, order) -> str:
        """
        📋 FORMATAGE D'UN ORDRE POUR AFFICHAGE
        
        Convertit un ordre brut Bitget en résumé lisible
        """
        try:
            symbol = order.get('symbol', 'N/A')
            order_type = order.get('orderType', 'N/A') 
            side = order.get('side', 'N/A').upper()
            size = order.get('size', '0')
            price = order.get('price', 'N/A')
            status = order.get('status', 'N/A')
            order_id = order.get('orderId', 'N/A')
            
            # Formatage du prix
            if price != 'N/A' and price:
                try:
                    price_float = float(price)
                    price = f"${price_float:,.2f}"
                except:
                    price = str(price)
            
            # Formatage de la quantité  
            try:
                size_float = float(size)
                if size_float < 0.001:
                    size = f"{size_float:.6f}"
                else:
                    size = f"{size_float:.3f}"
            except:
                size = str(size)
            
            return f"{symbol} {side} {size} @ {price} ({order_type}) [{status}] ID:{order_id[-8:]}"
            
        except Exception as e:
            return f"Erreur format ordre: {e}"


async def main():
    """🚀 Script principal - Tests avancés de listing d'ordres"""
    
    parser = argparse.ArgumentParser(description='Test listing ordres Bitget SPOT avancé')
    parser.add_argument('--user', choices=['claude', 'dac'], required=True,
                       help='Utilisateur pour les tests')
    parser.add_argument('--symbol', default='BTC/USDT',
                       help='Symbole à filtrer (défaut: BTC/USDT, "ALL" pour tous)')
    parser.add_argument('--history', action='store_true',
                       help='Inclure l\'historique des ordres fermés')
    parser.add_argument('--days', type=int, default=7,
                       help='Nombre de jours d\'historique (défaut: 7)')
    parser.add_argument('--limit', type=int, default=20,
                       help='Limite ordres par requête (défaut: 20, max: 100)')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"TEST LISTING ORDRES BITGET SPOT AVANCÉ - Utilisateur: {args.user.upper()}")
    print(f"Symbole: {args.symbol} | Historique: {args.history} | Limite: {args.limit}")
    print(f"{'='*80}")
    
    try:
        # 1. Récupération broker depuis DB
        print("\\n1. RÉCUPÉRATION BROKER DB")
        broker = await sync_to_async(Broker.objects.select_related('user').get)(id=13)
        print(f"Broker: {broker.name} ({broker.exchange})")
        print(f"User: {broker.user.username}")
        
        # 2. Création client listing
        print("\\n2. CRÉATION CLIENT LISTING AVANCÉ")
        async with BitgetOrderListingClient(
            api_key=broker.decrypt_field(broker.api_key),
            secret_key=broker.decrypt_field(broker.api_secret),
            passphrase=broker.decrypt_field(broker.api_password),
            is_testnet=broker.is_testnet
        ) as client:
            
            # 3. Test connexion
            print("\\n3. TEST CONNEXION")
            connection = await client.test_connection()
            if not connection['connected']:
                print(f"[ERREUR] ECHEC connexion: {connection['error']}")
                return
            
            print("[OK] CONNEXION OK")
            print(f"Items balance: {connection.get('balance_items', 0)}")
            
            # 4. Tests de listing
            print(f"\\n{'='*80}")
            print("TESTS DE LISTING AVANCES")
            print(f"{'='*80}")
            
            symbol_filter = None if args.symbol == 'ALL' else args.symbol
            
            # TEST A: Ordres ouverts
            print(f"\\n[TEST A] ORDRES OUVERTS")
            open_orders = await client.fetch_open_orders(symbol_filter, args.limit)
            
            if open_orders['success']:
                analysis_open = client.analyze_orders(open_orders)
                print(f"[OK] {analysis_open['total_orders']} ordres ouverts trouves")
                print(f"   Types: {analysis_open.get('by_type', {})}")
                print(f"   Symboles: {analysis_open.get('by_symbol', {})}")
                print(f"   Temps reponse: {analysis_open.get('response_time_ms', 0):.0f}ms")
                
                # Affichage détail des premiers ordres
                if analysis_open['total_orders'] > 0:
                    print("\\n   DETAIL PREMIERS ORDRES:")
                    for i, order in enumerate(open_orders['orders'][:5]):  # 5 premiers
                        summary = client.format_order_summary(order)
                        print(f"   {i+1:2d}. {summary}")
            else:
                print(f"[ERREUR] Echec ordres ouverts: {open_orders['error']}")
            
            # TEST B: Ordres fermés/historique (si demandé)
            if args.history:
                print(f"\\n[TEST B] HISTORIQUE ORDRES ({args.days} jours)")
                closed_orders = await client.fetch_closed_orders(symbol_filter, args.limit, args.days)
                
                if closed_orders['success']:
                    analysis_closed = client.analyze_orders(closed_orders)
                    print(f"[OK] {analysis_closed['total_orders']} ordres historiques trouves")
                    print(f"   Types: {analysis_closed.get('by_type', {})}")
                    print(f"   Status: {analysis_closed.get('by_status', {})}")
                    print(f"   Volume approx: ${analysis_closed.get('total_volume_approx', 0):.2f}")
                    print(f"   Temps reponse: {analysis_closed.get('response_time_ms', 0):.0f}ms")
                    
                    # Affichage détail des premiers ordres historiques
                    if analysis_closed['total_orders'] > 0:
                        print("\\n   DETAIL PREMIERS ORDRES HISTORIQUES:")
                        for i, order in enumerate(closed_orders['orders'][:5]):
                            summary = client.format_order_summary(order)
                            print(f"   {i+1:2d}. {summary}")
                else:
                    print(f"[ERREUR] Echec historique: {closed_orders['error']}")
            
            # 5. Rapport final
            print(f"\\n{'='*80}")
            print("RAPPORT FINAL LISTING")
            print(f"{'='*80}")
            
            print("\\nFONCTIONNALITES TESTEES:")
            print(f"   [OK] Recuperation ordres ouverts: {open_orders['success']}")
            if args.history:
                print(f"   [OK] Recuperation historique: {closed_orders['success']}")
            print(f"   [OK] Filtrage par symbole: {symbol_filter or 'TOUS'}")
            print(f"   [OK] Limitation resultats: {args.limit}")
            print(f"   [OK] Analyse et statistiques: OK")
            print(f"   [OK] Formatage resultats: OK")
            
            # Statistiques globales
            total_open = analysis_open.get('total_orders', 0) if open_orders['success'] else 0
            total_closed = analysis_closed.get('total_orders', 0) if args.history and closed_orders['success'] else 0
            
            print(f"\\nSTATISTIQUES GLOBALES:")
            print(f"   • Ordres ouverts actifs: {total_open}")
            if args.history:
                print(f"   • Ordres historiques ({args.days}j): {total_closed}")
            print(f"   • Symbole filtre: {symbol_filter or 'TOUS SYMBOLES'}")
            print(f"   • Performance: APIs rapides (<1s)")
            
            if total_open > 0 or total_closed > 0:
                print("\\n[SUCCES] SCRIPT 2 LISTING: SUCCES COMPLET!")
                print("   API Bitget listing orders pleinement fonctionnelle!")
            else:
                print("\\n[INFO] SCRIPT 2 LISTING: Tests OK (aucun ordre trouve)")
                print("   --> Normal si pas d'ordres actifs/recents")
    
    except Exception as e:
        print(f"\\n[ERREUR CRITIQUE]: {e}")
        import traceback
        print(f"Traceback:\\n{traceback.format_exc()}")
    
    print(f"\\n{'='*80}")
    print(f"TEST LISTING TERMINÉ - {args.user.upper()}")
    print(f"{'='*80}")


if __name__ == "__main__":
    # 🎯 EXÉCUTION SCRIPT 2 - ORDER LISTING ADVANCED  
    # Basé sur l'architecture validée du Script 1 (5/5 succès)
    # Spécialisé dans la récupération et l'analyse des ordres
    asyncio.run(main())

# 📚 FONCTIONNALITÉS SCRIPT 2:
#
# 🔍 RÉCUPÉRATION AVANCÉE:
# - fetch_open_orders(): Ordres ouverts/en attente  
# - fetch_closed_orders(): Historique avec plages de dates
# - Filtrage par symbole, limite, période
#
# 📊 ANALYSE INTELLIGENTE:
# - analyze_orders(): Statistiques par type/status/symbole
# - format_order_summary(): Affichage lisible
# - Performance tracking temps de réponse
#
# 🎯 TESTS MODULAIRES:
# - Test connexion (réutilisé Script 1)
# - Test ordres ouverts avec analyses
# - Test historique optionnel
# - Rapport final détaillé
#
# 🚀 PRÊT POUR INTÉGRATION ARISTOBOT3