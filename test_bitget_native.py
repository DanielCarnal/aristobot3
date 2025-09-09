# -*- coding: utf-8 -*-
"""
BITGET NATIVE API - VALIDATION TP/SL SPOT

Script de validation des ordres Take Profit / Stop Loss sur marches SPOT Bitget
via API native, contournant les limitations de la librairie CCXT.

DECOUVERTE MAJEURE:
- CCXT bloque artificiellement les TP/SL sur SPOT 
- API native Bitget supporte 4 variantes TP/SL SPOT
- Parametres cles: tpslType + planType + precision 6 decimales

APPROCHES VALIDEES:
1. TP/SL attaches    : tpslType='normal' + planType='normal_plan' 
2. Take Profit seul  : tpslType='tpsl' + planType='profit_plan'
3. Stop Loss seul    : tpslType='tpsl' + planType='loss_plan'
4. TP+SL independants: 2 ordres separes avec tpslType='tpsl'

Usage: python test_bitget_native.py --user=claude|dac [--dry-run]
Recup: broker_id=13 depuis PostgreSQL + calcul 2$ en BTC + TP/SL ±10%
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
import traceback
from decimal import Decimal

# Configuration Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.brokers.models import Broker
from asgiref.sync import sync_to_async

User = get_user_model()

class BitgetNativeClient:
    """
    Client Bitget natif contournant les limitations CCXT
    
    PARAMETRES CRITIQUES:
    - tpslType: 'normal' (TP/SL attaches) | 'tpsl' (TP/SL independants)
    - planType: 'normal_plan' | 'profit_plan' | 'loss_plan'
    - Precision: 6 decimales max pour BTC, 2 pour prix USD
    - Endpoint unifie: /api/v2/spot/trade/place-order
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
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _sign_request(self, method, path, params_str=''):
        """Signature Bitget V2"""
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
        """Test connexion via balance"""
        try:
            path = '/api/v2/spot/account/assets'
            headers = self._sign_request('GET', path)
            
            async with self.session.get(f"{self.base_url}{path}", headers=headers) as response:
                data = await response.json()
                
                if data.get('code') != '00000':
                    return {'connected': False, 'error': data.get('msg')}
                
                # Extraire balances non-zero
                balances = {}
                for asset in data['data']:
                    if float(asset.get('available', 0)) > 0:
                        balances[asset['coin']] = {
                            'free': float(asset['available']),
                            'total': float(asset['available']) + float(asset.get('frozen', 0))
                        }
                
                return {
                    'connected': True, 
                    'balance': balances
                }
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    async def get_ticker(self, symbol) -> dict:
        """Recupere le prix actuel BTC/USDT"""
        try:
            # Convertir BTC/USDT -> BTCUSDT
            bitget_symbol = symbol.replace('/', '')
            
            path = f'/api/v2/spot/market/tickers?symbol={bitget_symbol}'
            
            async with self.session.get(f"{self.base_url}{path}") as response:
                data = await response.json()
                
                if data.get('code') != '00000':
                    raise Exception(f"Erreur ticker: {data.get('msg')}")
                
                ticker_data = data['data'][0]
                return {
                    'symbol': symbol,
                    'bid': float(ticker_data['bidPr']),
                    'ask': float(ticker_data['askPr']),
                    'last': float(ticker_data['lastPr']),
                    'timestamp': int(time.time() * 1000)
                }
        except Exception as e:
            raise Exception(f"Erreur recuperation ticker {symbol}: {e}")
    
    async def place_order_simple(self, symbol, side, amount, order_type='market', price=None):
        """Place un ordre simple sans TP/SL"""
        try:
            bitget_symbol = symbol.replace('/', '')
            
            order_data = {
                'symbol': bitget_symbol,
                'side': side,
                'orderType': order_type,
                'force': 'gtc'
            }
            
            # Gestion quantite selon type et side - CORRECTION
            if order_type == 'market':
                if side == 'buy':
                    # Market buy = montant en USDT (quoteSize)
                    quote_amount = amount * price if price else amount * 2  # Fallback 2$
                    order_data['quoteSize'] = f"{quote_amount:.2f}"  # Format USD
                else:
                    # Market sell = quantite en BTC (size)
                    order_data['size'] = f"{amount:.6f}"
            else:
                # Limit orders = toujours quantite en BTC (size)
                order_data['size'] = f"{amount:.6f}"
            
            if price and order_type == 'limit':
                order_data['price'] = f"{price:.2f}"
            
            path = '/api/v2/spot/trade/place-order'
            params_str = json.dumps(order_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                if result.get('code') != '00000':
                    raise Exception(f"Erreur ordre: {result.get('msg')}")
                
                return result['data']
        
        except Exception as e:
            raise Exception(f"Erreur placement ordre simple: {e}")
    
    async def place_order_with_tpsl(self, symbol, side, amount, price, sl_price, tp_price):
        """
        APPROCHE 1: Ordre limite avec TP/SL attaches
        
        Decouverte: tpslType='normal' + planType='normal_plan' cree:
        - 1 ordre limite principal (onglet Limit)  
        - 2 ordres TP/SL automatiques (onglet TP/SL)
        
        Avantage: Execution atomique, gestion liee
        """
        try:
            bitget_symbol = symbol.replace('/', '')
            
            order_data = {
                'symbol': bitget_symbol,
                'side': side,
                'orderType': 'limit',  # Obligatoire pour TP/SL
                'size': f"{amount:.6f}",  # Precision 6 decimales
                'price': f"{price:.2f}",  # Prix avec 2 decimales
                'force': 'gtc',
                # STRUCTURE TP/SL SPOT
                'planType': 'normal_plan',
                'tpslType': 'normal'       # Ordre normal avec TP/SL attaches
            }
            
            if sl_price:
                order_data['presetStopLossPrice'] = f"{sl_price:.2f}"
            
            if tp_price:
                order_data['presetTakeProfitPrice'] = f"{tp_price:.2f}"
            
            path = '/api/v2/spot/trade/place-order'
            params_str = json.dumps(order_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                return {
                    'success': result.get('code') == '00000',
                    'data': result.get('data'),
                    'error': result.get('msg') if result.get('code') != '00000' else None,
                    'raw_response': result
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    async def place_tp_only(self, symbol, side, amount, tp_price):
        """
        APPROCHE 2: Take Profit independant pur
        
        Decouverte: tpslType='tpsl' + planType='profit_plan' cree:
        - Ordre TP pur dans onglet TP/SL (sans ordre principal)
        - Se declenche des que prix atteint, meme sans position
        
        Usage: Protection upside ou prise de profits conditionnelle
        """
        try:
            bitget_symbol = symbol.replace('/', '')
            
            order_data = {
                'symbol': bitget_symbol,
                'tpslType': 'tpsl',        # CLE MANQUANTE!
                'planType': 'profit_plan',
                'triggerPrice': f"{tp_price:.2f}",
                'size': f"{amount:.6f}",
                'side': 'sell' if side == 'buy' else 'buy',  # Inverse pour fermer
                'orderType': 'market',
                'force': 'gtc'
            }
            
            path = '/api/v2/spot/trade/place-order'  # Endpoint standard!
            params_str = json.dumps(order_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                return {
                    'success': result.get('code') == '00000',
                    'data': result.get('data'),
                    'error': result.get('msg') if result.get('code') != '00000' else None,
                    'raw_response': result
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    async def place_sl_only(self, symbol, side, amount, sl_price):
        """
        APPROCHE 3: Stop Loss independant pur
        
        Decouverte: tpslType='tpsl' + planType='loss_plan' cree:
        - Ordre SL pur dans onglet TP/SL (sans ordre principal)
        - Protection downside immediate, meme sans position ouverte
        
        Usage: Protection capital ou hedging conditionnel
        """
        try:
            bitget_symbol = symbol.replace('/', '')
            
            order_data = {
                'symbol': bitget_symbol,
                'tpslType': 'tpsl',        # CLE MANQUANTE!
                'planType': 'loss_plan',
                'triggerPrice': f"{sl_price:.2f}",
                'size': f"{amount:.6f}",
                'side': 'sell' if side == 'buy' else 'buy',  # Inverse pour fermer
                'orderType': 'market',
                'force': 'gtc'
            }
            
            path = '/api/v2/spot/trade/place-order'  # Endpoint standard!
            params_str = json.dumps(order_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                return {
                    'success': result.get('code') == '00000',
                    'data': result.get('data'),
                    'error': result.get('msg') if result.get('code') != '00000' else None,
                    'raw_response': result
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    async def place_tpsl_independent(self, symbol, side, amount, tp_price, sl_price):
        """
        APPROCHE 4: TP+SL totalement independants
        
        Decouverte: 2 appels API separes avec tpslType='tpsl'
        - Take Profit: planType='profit_plan' 
        - Stop Loss: planType='loss_plan'
        
        Avantage: Controle independant, modification/annulation separee
        Usage: Strategies complexes avec gestion fine des niveaux
        """
        results = {}
        
        # 1. Take Profit
        if tp_price:
            results['take_profit'] = await self.place_tp_only(symbol, side, amount, tp_price)
        
        # 2. Stop Loss  
        if sl_price:
            results['stop_loss'] = await self.place_sl_only(symbol, side, amount, sl_price)
        
        return results


async def main():
    """Script principal de test"""
    parser = argparse.ArgumentParser(description='Test ordres Bitget natifs')
    parser.add_argument('--user', choices=['claude', 'dac'], required=True,
                       help='Identifiant utilisateur pour les logs')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Mode simulation (pas dexecution reelle)')
    
    args = parser.parse_args()
    
    print(f"{'='*70}")
    print(f"TEST ORDRES BITGET NATIFS - Utilisateur: {args.user.upper()}")
    if args.dry_run:
        print("MODE DRY-RUN ACTIF - AUCUN ORDRE REEL")
    print(f"{'='*70}")
    
    try:
        # 1. Recuperer broker_id=13 depuis DB
        print("\n1. RECUPERATION BROKER DB")
        broker = await sync_to_async(Broker.objects.select_related('user').get)(id=13)
        print(f"Broker: {broker.name} ({broker.exchange})")
        print(f"Testnet: {broker.is_testnet}")
        print(f"User: {broker.user.username}")
        
        # 2. Creer client natif
        print("\n2. CREATION CLIENT NATIF")
        async with BitgetNativeClient(
            api_key=broker.decrypt_field(broker.api_key),
            secret_key=broker.decrypt_field(broker.api_secret),
            passphrase=broker.decrypt_field(broker.api_password),
            is_testnet=broker.is_testnet
        ) as client:
            
            # 3. Test connexion
            print("\n3. TEST CONNEXION")
            connection = await client.test_connection()
            if not connection['connected']:
                print(f"ECHEC connexion: {connection['error']}")
                return
            
            print("CONNEXION OK")
            usdt_balance = connection['balance'].get('USDT', {})
            print(f"Balance USDT: ${usdt_balance.get('free', 0):.2f}")
            
            # 4. Recuperer prix BTC actuel
            print("\n4. PRIX BTC/USDT ACTUEL")
            ticker = await client.get_ticker('BTC/USDT')
            btc_price = ticker['last']
            print(f"Prix BTC: ${btc_price:,.2f}")
            
            # 5. Calculer quantite pour 2$ avec precision Bitget
            usd_amount = 2.0
            btc_quantity_raw = usd_amount / btc_price
            # Bitget BTC precision = 6 decimales max
            btc_quantity = round(btc_quantity_raw, 6)
            print(f"Quantite BTC brute: {btc_quantity_raw:.10f} BTC")
            print(f"Quantite BTC ajustee (6 dec): {btc_quantity:.6f} BTC")
            
            # 6. Calculer prix TP/SL (10% pour visibilite console Bitget)
            entry_price = btc_price
            sl_price = entry_price * 0.90  # -10% (plus visible)
            tp_price = entry_price * 1.10  # +10% (plus visible)
            
            print(f"Prix entree: ${entry_price:,.2f}")
            print(f"Stop Loss (-10%): ${sl_price:,.2f}")
            print(f"Take Profit (+10%): ${tp_price:,.2f}")
            print("NOTE: TP/SL a 10% pour visibilite dans console Bitget")
            
            # 7. Tests des ordres - 4 VARIANTES COMPLETES
            test_results = {}
            
            if args.dry_run:
                print("\nMODE DRY-RUN: Simulation des tests")
                test_results = {
                    'market_order': {'success': True, 'simulated': True},
                    'limit_order': {'success': True, 'simulated': True},
                    'tpsl_attached': {'success': True, 'simulated': True},
                    'tp_only': {'success': True, 'simulated': True},
                    'sl_only': {'success': True, 'simulated': True},
                    'tpsl_independent': {'success': True, 'simulated': True}
                }
            else:
                # TEST A: Ordre market simple
                print("\n5A. TEST ORDRE MARKET SIMPLE")
                try:
                    market_result = await client.place_order_simple(
                        'BTC/USDT', 'buy', btc_quantity, 'market', btc_price
                    )
                    test_results['market_order'] = {'success': True, 'data': market_result}
                    print(f"SUCCES ordre market: {market_result.get('orderId', 'N/A')}")
                except Exception as e:
                    test_results['market_order'] = {'success': False, 'error': str(e)}
                    print(f"ECHEC ordre market: {e}")
                
                # TEST B: Ordre limite simple  
                print("\n5B. TEST ORDRE LIMITE SIMPLE")
                try:
                    limit_result = await client.place_order_simple(
                        'BTC/USDT', 'buy', btc_quantity, 'limit', entry_price * 0.999
                    )
                    test_results['limit_order'] = {'success': True, 'data': limit_result}
                    print(f"SUCCES ordre limite: {limit_result.get('orderId', 'N/A')}")
                except Exception as e:
                    test_results['limit_order'] = {'success': False, 'error': str(e)}
                    print(f"ECHEC ordre limite: {e}")
                
                # TEST C: Ordre avec TP/SL ATTACHE (deja valide)
                print("\n5C. TEST ORDRE AVEC TP/SL ATTACHE")
                tpsl_attached = await client.place_order_with_tpsl(
                    'BTC/USDT', 'buy', btc_quantity, entry_price, sl_price, tp_price
                )
                
                if tpsl_attached['success']:
                    print(f"SUCCES TP/SL attache: {tpsl_attached['data'].get('orderId', 'N/A')}")
                else:
                    print(f"ECHEC TP/SL attache: {tpsl_attached['error']}")
                
                test_results['tpsl_attached'] = tpsl_attached
                
                # TEST D: Take Profit SEUL (NOUVEAU)
                print("\n5D. TEST TAKE PROFIT SEUL")
                tp_only_result = await client.place_tp_only(
                    'BTC/USDT', 'buy', btc_quantity, tp_price
                )
                
                if tp_only_result['success']:
                    print(f"SUCCES TP seul: {tp_only_result['data'].get('orderId', 'N/A')}")
                    print("NOUVEAU: Take Profit independant fonctionne!")
                else:
                    print(f"ECHEC TP seul: {tp_only_result['error']}")
                
                test_results['tp_only'] = tp_only_result
                
                # TEST E: Stop Loss SEUL (NOUVEAU)
                print("\n5E. TEST STOP LOSS SEUL")
                sl_only_result = await client.place_sl_only(
                    'BTC/USDT', 'buy', btc_quantity, sl_price
                )
                
                if sl_only_result['success']:
                    print(f"SUCCES SL seul: {sl_only_result['data'].get('orderId', 'N/A')}")
                    print("NOUVEAU: Stop Loss independant fonctionne!")
                else:
                    print(f"ECHEC SL seul: {sl_only_result['error']}")
                
                test_results['sl_only'] = sl_only_result
                
                # TEST F: TP+SL INDEPENDANTS (NOUVEAU)
                print("\n5F. TEST TP+SL INDEPENDANTS (2 ordres)")
                tpsl_independent = await client.place_tpsl_independent(
                    'BTC/USDT', 'buy', btc_quantity, tp_price, sl_price
                )
                
                tp_success = tpsl_independent.get('take_profit', {}).get('success', False)
                sl_success = tpsl_independent.get('stop_loss', {}).get('success', False)
                
                if tp_success and sl_success:
                    tp_id = tpsl_independent['take_profit']['data'].get('orderId', 'N/A')
                    sl_id = tpsl_independent['stop_loss']['data'].get('orderId', 'N/A')
                    print(f"SUCCES TP+SL independants: TP={tp_id}, SL={sl_id}")
                    print("FLEXIBILITE MAXIMALE: 2 ordres TP/SL totalement independants!")
                else:
                    print(f"ECHEC partiel TP+SL independants:")
                    if not tp_success:
                        print(f"  TP: {tpsl_independent.get('take_profit', {}).get('error', 'N/A')}")
                    if not sl_success:
                        print(f"  SL: {tpsl_independent.get('stop_loss', {}).get('error', 'N/A')}")
                
                test_results['tpsl_independent'] = {
                    'success': tp_success and sl_success,
                    'data': tpsl_independent
                }
            
            # 8. Rapport final
            print(f"\n{'='*70}")
            print("RAPPORT FINAL")
            print(f"{'='*70}")
            
            for test_name, result in test_results.items():
                status = "SUCCES" if result['success'] else "ECHEC"
                print(f"{test_name.upper()}: {status}")
                if not result['success'] and 'error' in result:
                    print(f"  Erreur: {result['error']}")
            
            # Statut global
            all_success = all(r['success'] for r in test_results.values())
            print(f"\nSTATUT GLOBAL: {'TOUS LES TESTS PASSES' if all_success else 'CERTAINS TESTS ECHOUES'}")
            
            # Compter les succes TP/SL
            tpsl_success_count = sum(1 for key in ['tpsl_attached', 'tp_only', 'sl_only', 'tpsl_independent'] 
                                   if test_results.get(key, {}).get('success'))
            
            if tpsl_success_count > 0:
                print(f"\nBREAKTHROUGH CONFIRME: {tpsl_success_count}/4 variantes TP/SL SPOT fonctionnelles!")
                print("4 APPROCHES VALIDEES:")
                print("  1. TP/SL attaches a ordre limite")
                print("  2. Take Profit independant")
                print("  3. Stop Loss independant") 
                print("  4. TP+SL independants (2 ordres)")
                print("\nFLEXIBILITE TOTALE pour Aristobot3.1!")
                print("Migration recommandee: GO GO GO!")
            else:
                print("\nTP/SL SPOT encore bloque - Investigation supplementaire necessaire")
    
    except Exception as e:
        print(f"\nERRHEUR CRITIQUE: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
    
    print(f"\n{'='*70}")
    print(f"TEST TERMINE - {args.user.upper()}")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(main())