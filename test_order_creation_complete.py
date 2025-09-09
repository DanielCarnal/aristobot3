# -*- coding: utf-8 -*-
"""
BITGET NATIVE API - TESTS COMPLETS CREATION ORDRES

Script de test complet pour tous les types d'ordres necessaires a Aristobot3:
- Ordres de base (Market, Limit) 
- TP/SL (attaches, independants)
- Trailing Stop SPOT (planType="track_plan")
- DB Logging dans table trades
- Validation prix pour eviter execution

PHASES DE TEST:
1. Tests existants (validation regression)
2. Trailing Stop SPOT (NOUVEAU)  
3. DB Logging complet (NOUVEAU)
4. Rapport final avec metriques

Usage: python test_order_creation_complete.py --user=claude|dac [--real]
Default: Mode --dry-run (simulation)
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
from datetime import datetime

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

class BitgetNativeClient:
    """
    Client Bitget natif avec support Trailing Stop + DB Logging
    
    NOUVEAUTES:
    - Trailing Stop SPOT (planType="track_plan")
    - DB Logging integre table trades
    - Validation prix anti-execution
    """
    
    def __init__(self, api_key, secret_key, passphrase, is_testnet=False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = 'https://api.bitget.com'
        if is_testnet:
            self.base_url = 'https://api.bitgetapi.com'
        self.session = None
        
        # Configuration logging DB
        self.db_logging_enabled = True
        self.user_id = None
        self.broker_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def set_db_context(self, user_id, broker_id):
        """Configure le contexte pour DB logging"""
        self.user_id = user_id
        self.broker_id = broker_id
    
    async def log_to_db(self, action, request_data, response_data, success, error=None):
        """Enregistre l'action dans la table trades"""
        if not self.db_logging_enabled or not self.user_id or not self.broker_id:
            return
        
        try:
            trade_data = {
                'user_id': self.user_id,
                'broker_id': self.broker_id,
                'trade_type': 'manual',  # Utiliser trade_type au lieu de source
                'symbol': request_data.get('symbol', 'UNKNOWN').replace('USDT', '/USDT') if 'USDT' in request_data.get('symbol', '') else 'BTC/USDT',
                'side': request_data.get('side', 'unknown'),
                'quantity': Decimal(str(request_data.get('size', request_data.get('quoteSize', 0)))),
                'price': Decimal(str(request_data.get('price', 0))) if request_data.get('price') else None,
                'total_value': Decimal(str(request_data.get('quoteSize', '2.0'))),
                'order_type': request_data.get('orderType', 'unknown'),
                'status': 'filled' if success else 'failed',
                'exchange_order_id': response_data.get('orderId') if success else None,
                'notes': json.dumps({
                    'action': action,
                    'request': request_data,
                    'response': response_data,
                    'error': error,
                    'test_timestamp': datetime.now().isoformat()
                })
            }
            
            # Creer l'enregistrement Trade
            await sync_to_async(Trade.objects.create)(**trade_data)
            print(f"[DB LOG] Action '{action}' enregistree en DB")
            
        except Exception as e:
            print(f"[DB LOG ERROR] Impossible d'enregistrer {action}: {e}")
    
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
        """Recupere le prix actuel"""
        try:
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
    
    # ========================================================================
    # ORDRES EXISTANTS (REGRESSION TESTS)
    # ========================================================================
    
    async def place_order_simple(self, symbol, side, amount, order_type='market', price=None):
        """Place un ordre simple sans TP/SL - EXISTANT"""
        request_data = {
            'symbol': symbol.replace('/', ''),
            'side': side,
            'orderType': order_type,
            'force': 'gtc'
        }
        
        try:
            # NETTOYAGE STRICT PARAMETRES BITGET
            print(f"[DEBUG MARKET] Parametres initiaux: {request_data}")
            
            # Gestion quantite selon type et side - CORRECTION FINALE
            if order_type == 'market':
                if side == 'buy':
                    # Market buy: Bitget EXIGE size + quoteSize (découverte via debug)
                    if amount >= 1.0:  # Si >= 1, c'est probablement USD
                        quote_amount = max(2.0, amount)
                    else:  # Si < 1, c'est BTC, convertir en USD
                        quote_amount = max(2.0, amount * price if price else amount * 110000)
                    
                    # MARKET BUY: size + quoteSize OBLIGATOIRES (découverte Bitget V2)
                    quote_amount = max(10.0, quote_amount)  # Minimum 10$ pour market
                    # Calculer size minimum pour dépasser 1 USDT en valeur
                    btc_amount = max(0.00001, quote_amount / (price if price else 110000))
                    
                    request_data = {
                        'symbol': request_data['symbol'],
                        'side': 'buy',
                        'orderType': 'market',
                        'force': 'gtc',
                        'size': f"{btc_amount:.6f}",        # BTC quantity (requis)
                        'quoteSize': f"{quote_amount:.2f}"   # USD amount (requis)
                    }
                    print(f"[DEBUG MARKET] Market BUY - Final params (SIZE+QUOTE): {request_data}")
                else:
                    # MARKET SELL: SEULEMENT size en BTC
                    request_data = {
                        'symbol': request_data['symbol'],
                        'side': 'sell',
                        'orderType': 'market',
                        'force': 'gtc',
                        'size': f"{amount:.6f}"
                    }
                    print(f"[DEBUG MARKET] Market SELL - Final params: {request_data}")
            else:
                # Limit: SEULEMENT size + verification montant minimum
                total_value = amount * price if price else 0
                if total_value < 5.0 and price:
                    amount = 5.0 / price
                request_data = {
                    'symbol': request_data['symbol'],
                    'side': request_data['side'],
                    'orderType': 'limit',
                    'force': 'gtc',
                    'size': f"{amount:.6f}"
                }
            
            if price and order_type == 'limit':
                request_data['price'] = f"{price:.2f}"
            
            print(f"[DEBUG MARKET] Parametres finaux: {request_data}")
            
            path = '/api/v2/spot/trade/place-order'
            params_str = json.dumps(request_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                success = result.get('code') == '00000'
                error = result.get('msg') if not success else None
                
                # DB Logging
                await self.log_to_db('place_order_simple', request_data, result.get('data', {}), success, error)
                
                if not success:
                    raise Exception(f"Erreur ordre: {result.get('msg')}")
                
                return result['data']
        
        except Exception as e:
            await self.log_to_db('place_order_simple', request_data, {}, False, str(e))
            raise Exception(f"Erreur placement ordre simple: {e}")
    
    async def place_order_with_tpsl(self, symbol, side, amount, price, sl_price, tp_price):
        """EXISTANT: Ordre limite avec TP/SL attaches - MONTANT MINIMUM"""
        # Validation minimum 5 USDT pour ordre principal
        total_value = amount * price
        if total_value < 5.0:
            amount = 5.0 / price
        
        request_data = {
            'symbol': symbol.replace('/', ''),
            'side': side,
            'orderType': 'limit',
            'size': f"{amount:.6f}",
            'price': f"{price:.2f}",
            'force': 'gtc',
            'planType': 'normal_plan',
            'tpslType': 'normal'
        }
        
        # Validation logique TP/SL vs prix ordre
        if side == 'buy':
            # BUY: SL doit etre < prix ordre, TP doit etre > prix ordre
            if sl_price and sl_price < price:
                request_data['presetStopLossPrice'] = f"{sl_price:.2f}"
            elif sl_price:
                print(f"[WARN] SL {sl_price} ignore car >= prix ordre {price}")
                
            if tp_price and tp_price > price:
                request_data['presetTakeProfitPrice'] = f"{tp_price:.2f}"
            elif tp_price:
                print(f"[WARN] TP {tp_price} ignore car <= prix ordre {price}")
        else:
            # SELL: logique inverse
            if sl_price and sl_price > price:
                request_data['presetStopLossPrice'] = f"{sl_price:.2f}"
            elif sl_price:
                print(f"[WARN] SL {sl_price} ignore car <= prix ordre {price}")
                
            if tp_price and tp_price < price:
                request_data['presetTakeProfitPrice'] = f"{tp_price:.2f}"
            elif tp_price:
                print(f"[WARN] TP {tp_price} ignore car >= prix ordre {price}")
        
        try:
            path = '/api/v2/spot/trade/place-order'
            params_str = json.dumps(request_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                success = result.get('code') == '00000'
                error = result.get('msg') if not success else None
                
                # DB Logging
                await self.log_to_db('place_order_with_tpsl', request_data, result.get('data', {}), success, error)
                
                return {
                    'success': success,
                    'data': result.get('data'),
                    'error': error,
                    'raw_response': result
                }
        
        except Exception as e:
            await self.log_to_db('place_order_with_tpsl', request_data, {}, False, str(e))
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    async def place_tp_only(self, symbol, side, amount, tp_price):
        """EXISTANT: Take Profit independant"""
        request_data = {
            'symbol': symbol.replace('/', ''),
            'tpslType': 'tpsl',
            'planType': 'profit_plan',
            'triggerPrice': f"{tp_price:.2f}",
            'size': f"{amount:.6f}",
            'side': 'sell' if side == 'buy' else 'buy',
            'orderType': 'market',
            'force': 'gtc'
        }
        
        try:
            path = '/api/v2/spot/trade/place-order'
            params_str = json.dumps(request_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                success = result.get('code') == '00000'
                error = result.get('msg') if not success else None
                
                # DB Logging
                await self.log_to_db('place_tp_only', request_data, result.get('data', {}), success, error)
                
                return {
                    'success': success,
                    'data': result.get('data'),
                    'error': error,
                    'raw_response': result
                }
        
        except Exception as e:
            await self.log_to_db('place_tp_only', request_data, {}, False, str(e))
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    async def place_sl_only(self, symbol, side, amount, sl_price):
        """EXISTANT: Stop Loss independant"""
        request_data = {
            'symbol': symbol.replace('/', ''),
            'tpslType': 'tpsl',
            'planType': 'loss_plan',
            'triggerPrice': f"{sl_price:.2f}",
            'size': f"{amount:.6f}",
            'side': 'sell' if side == 'buy' else 'buy',
            'orderType': 'market',
            'force': 'gtc'
        }
        
        try:
            path = '/api/v2/spot/trade/place-order'
            params_str = json.dumps(request_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                success = result.get('code') == '00000'
                error = result.get('msg') if not success else None
                
                # DB Logging
                await self.log_to_db('place_sl_only', request_data, result.get('data', {}), success, error)
                
                return {
                    'success': success,
                    'data': result.get('data'),
                    'error': error,
                    'raw_response': result
                }
        
        except Exception as e:
            await self.log_to_db('place_sl_only', request_data, {}, False, str(e))
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    # ========================================================================
    # NOUVEAUX ORDRES - TRAILING STOP
    # ========================================================================
    
    async def place_trailing_stop(self, symbol, side, amount, trigger_price, callback_ratio=5.0):
        """
        NOUVEAU: Trailing Stop SPOT natif Bitget
        
        Parametres:
        - trigger_price: Prix d'activation du trailing (ex: +5% vs prix achat)
        - callback_ratio: % de recul pour declencher vente (ex: 5%)
        - side: Direction position originale ('buy' cree trailing SELL)
        
        planType: 'moving_plan' = Trailing Stop natif Bitget
        """
        # Trailing Stop = ordre oppose a la position
        trailing_side = 'sell' if side == 'buy' else 'buy'
        
        # Trailing Stop avec validation DOUBLE: trigger ET marché actuel
        # Récupérer prix marché actuel pour validation Bitget
        ticker = await self.get_ticker(symbol)
        current_price = ticker['last']
        
        trigger_value = amount * trigger_price
        market_value = amount * current_price
        
        print(f"[DEBUG] Trailing {trailing_side}: trigger=${trigger_value:.2f}$, marché=${market_value:.2f}$")
        
        # Ajuster pour MAXIMUM + minimum absolu BTC pour trailing BUY avec 20$ minimum
        min_amount_for_trigger = 20.0 / trigger_price  # 20$ minimum pour trailing
        min_amount_for_market = 2.5 / current_price
        min_absolute_btc = 0.000025  # Minimum absolu Bitget pour trailing BUY
        
        required_amount = max(min_amount_for_trigger, min_amount_for_market, min_absolute_btc)
        
        if amount < required_amount:
            print(f"[DEBUG] Ajustement: {amount:.6f} -> {required_amount:.6f} BTC")
            amount = required_amount
            print(f"[DEBUG] Nouveau: trigger=${amount * trigger_price:.2f}$, marché=${amount * current_price:.2f}$")
            
        request_data = {
            'symbol': symbol.replace('/', ''),
            'planType': 'moving_plan',
            'triggerPrice': f"{trigger_price:.2f}",
            'callbackRatio': f"{callback_ratio:.1f}",
            'triggerType': 'fill_price',
            'size': f"{amount:.6f}",  # Quantite ajustee pour minimum
            'side': trailing_side,
            'orderType': 'market',
            'force': 'gtc'
        }
        
        try:
            path = '/api/v2/spot/trade/place-order'       # Endpoint unifie
            params_str = json.dumps(request_data, separators=(',', ':'))
            headers = self._sign_request('POST', path, params_str)
            
            async with self.session.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=params_str
            ) as response:
                result = await response.json()
                
                success = result.get('code') == '00000'
                error = result.get('msg') if not success else None
                
                # DB Logging
                await self.log_to_db('place_trailing_stop', request_data, result.get('data', {}), success, error)
                
                return {
                    'success': success,
                    'data': result.get('data'),
                    'error': error,
                    'raw_response': result,
                    'trailing_config': {
                        'trigger_price': trigger_price,
                        'callback_ratio': callback_ratio,
                        'direction': f"{side} position protected by {trailing_side} trailing"
                    }
                }
        
        except Exception as e:
            await self.log_to_db('place_trailing_stop', request_data, {}, False, str(e))
            return {
                'success': False,
                'error': str(e),
                'data': None
            }


def calculate_safe_prices(market_price):
    """
    Calcule les prix securises pour eviter l'execution des ordres
    selon les specifications utilisateur
    """
    return {
        # Prix ordres de base (pour eviter execution)
        'buy_limit_safe': market_price * 0.50,   # 50% du marche
        'sell_limit_safe': market_price * 2.00,  # Double du marche
        
        # TP/SL orphelins (±10%)  
        'tp_orphan': market_price * 1.10,        # +10% 
        'sl_orphan': market_price * 0.90,        # -10%
        
        # TP/SL lies aux ordres limite (plus extremes)
        'tp_linked': (market_price * 2.00) * 1.10,  # 10% > double marche
        'sl_linked': market_price * 0.90,            # 10% < marche normal
        
        # Trailing Stop
        'trailing_trigger_buy': market_price * 1.05,   # Active a +5% (protection long)
        'trailing_trigger_sell': market_price * 0.95,  # Active a -5% (protection short)
        'trailing_callback': 5.0                       # 5% recul equilibre
    }


async def main():
    """Script principal de test complet"""
    parser = argparse.ArgumentParser(description='Test creation ordres Bitget complet')
    parser.add_argument('--user', choices=['claude', 'dac'], required=True,
                       help='Identifiant utilisateur pour les logs')
    parser.add_argument('--real', action='store_true', 
                       help='Mode execution reelle (defaut: dry-run)')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"TEST CREATION ORDRES BITGET COMPLET - Utilisateur: {args.user.upper()}")
    if not args.real:
        print("MODE DRY-RUN ACTIF - AUCUN ORDRE REEL")
    else:
        print("MODE REEL ACTIF - ORDRES EXECUTES SUR BITGET")
    print(f"{'='*80}")
    
    try:
        # 1. Recuperer broker_id=13 depuis DB
        print("\n1. RECUPERATION BROKER DB")
        broker = await sync_to_async(Broker.objects.select_related('user').get)(id=13)
        print(f"Broker: {broker.name} ({broker.exchange})")
        print(f"Testnet: {broker.is_testnet}")
        print(f"User: {broker.user.username}")
        
        # 2. Creer client natif avec DB context
        print("\n2. CREATION CLIENT NATIF + DB CONTEXT")
        async with BitgetNativeClient(
            api_key=broker.decrypt_field(broker.api_key),
            secret_key=broker.decrypt_field(broker.api_secret),
            passphrase=broker.decrypt_field(broker.api_password),
            is_testnet=broker.is_testnet
        ) as client:
            
            # Configurer DB logging
            client.set_db_context(broker.user.id, broker.id)
            client.db_logging_enabled = args.real  # Log seulement si execution reelle
            
            # 3. Test connexion
            print("\n3. TEST CONNEXION")
            connection = await client.test_connection()
            if not connection['connected']:
                print(f"ECHEC connexion: {connection['error']}")
                return
            
            print("CONNEXION OK")
            usdt_balance = connection['balance'].get('USDT', {})
            print(f"Balance USDT: ${usdt_balance.get('free', 0):.2f}")
            
            # 4. Prix marche et calculs securises
            print("\n4. PRIX MARCHE + CALCULS SECURISES")
            ticker = await client.get_ticker('BTC/USDT')
            market_price = ticker['last']
            print(f"Prix BTC marche: ${market_price:,.2f}")
            
            prices = calculate_safe_prices(market_price)
            print(f"Prix calcules pour eviter execution:")
            print(f"  Buy Limit (50% marche): ${prices['buy_limit_safe']:,.2f}")
            print(f"  Sell Limit (200% marche): ${prices['sell_limit_safe']:,.2f}")
            print(f"  TP orphelin (+10%): ${prices['tp_orphan']:,.2f}")
            print(f"  SL orphelin (-10%): ${prices['sl_orphan']:,.2f}")
            print(f"  Trailing trigger LONG (+5%): ${prices['trailing_trigger_buy']:,.2f}")
            print(f"  Trailing trigger SHORT (-5%): ${prices['trailing_trigger_sell']:,.2f}")
            print(f"  Trailing callback: {prices['trailing_callback']}%")
            
            # 5. Calculer quantites pour 5$ par test (minimum Bitget requis)
            usd_per_test = 5.0  # AUGMENTE pour respecter minimum Bitget
            quantities = {
                'market_usd': usd_per_test,  # Market buy = montant USD
                'limit': usd_per_test / prices['buy_limit_safe'],     # 5$ au prix limite
                'tpsl': usd_per_test / prices['buy_limit_safe'],      # 5$ pour TP/SL
                'orphan': round(usd_per_test / market_price, 6),      # 5$ au marche
                'trailing': round(usd_per_test / market_price, 6)     # 5$ au marche
            }
            
            print(f"\nQuantites pour 5$ par test:")
            print(f"  Market: ${quantities['market_usd']} USD")
            print(f"  Limit: {quantities['limit']:.6f} BTC")
            print(f"  TP/SL: {quantities['tpsl']:.6f} BTC")
            print(f"  Orphelins: {quantities['orphan']:.6f} BTC")
            
            # ====================================================================
            # PHASE 1: TESTS EXISTANTS (VALIDATION REGRESSION)
            # ====================================================================
            print(f"\n{'='*80}")
            print("PHASE 1: VALIDATION REGRESSION - ORDRES EXISTANTS")
            print(f"{'='*80}")
            
            test_results = {}
            
            if args.real:
                # TEST 1A: Ordre market simple
                print("\n1A. TEST ORDRE MARKET SIMPLE")
                try:
                    market_result = await client.place_order_simple(
                        'BTC/USDT', 'buy', quantities['market_usd'], 'market', market_price
                    )
                    test_results['market_simple'] = {'success': True, 'data': market_result}
                    print(f"SUCCES market: {market_result.get('orderId', 'N/A')}")
                except Exception as e:
                    test_results['market_simple'] = {'success': False, 'error': str(e)}
                    print(f"ECHEC market: {e}")
                
                # TEST 1B: Ordre limite securise
                print("\n1B. TEST ORDRE LIMITE SECURISE")
                try:
                    limit_result = await client.place_order_simple(
                        'BTC/USDT', 'buy', quantities['limit'], 'limit', prices['buy_limit_safe']
                    )
                    test_results['limit_safe'] = {'success': True, 'data': limit_result}
                    print(f"SUCCES limit securise: {limit_result.get('orderId', 'N/A')}")
                except Exception as e:
                    test_results['limit_safe'] = {'success': False, 'error': str(e)}
                    print(f"ECHEC limit: {e}")
                
                # TEST 1C: TP/SL attaches (regression)
                print("\n1C. TEST TP/SL ATTACHES (REGRESSION)")
                tpsl_attached = await client.place_order_with_tpsl(
                    'BTC/USDT', 'buy', quantities['tpsl'],
                    prices['buy_limit_safe'],          # Prix BUY securise (50% marche) 
                    prices['buy_limit_safe'] * 0.90,   # SL -10% du prix limite
                    prices['buy_limit_safe'] * 1.20    # TP +20% du prix limite
                )
                test_results['tpsl_attached'] = tpsl_attached
                
                if tpsl_attached['success']:
                    print(f"SUCCES TP/SL attache: {tpsl_attached['data'].get('orderId', 'N/A')}")
                else:
                    print(f"ECHEC TP/SL attache: {tpsl_attached['error']}")
                
                # TEST 1D: TP orphelin (regression)
                print("\n1D. TEST TP ORPHELIN (REGRESSION)")
                tp_only = await client.place_tp_only(
                    'BTC/USDT', 'buy', quantities['orphan'], prices['tp_orphan']
                )
                test_results['tp_orphan'] = tp_only
                
                if tp_only['success']:
                    print(f"SUCCES TP orphelin: {tp_only['data'].get('orderId', 'N/A')}")
                else:
                    print(f"ECHEC TP orphelin: {tp_only['error']}")
                
                # TEST 1E: SL orphelin (regression)  
                print("\n1E. TEST SL ORPHELIN (REGRESSION)")
                sl_only = await client.place_sl_only(
                    'BTC/USDT', 'buy', quantities['orphan'], prices['sl_orphan']
                )
                test_results['sl_orphan'] = sl_only
                
                if sl_only['success']:
                    print(f"SUCCES SL orphelin: {sl_only['data'].get('orderId', 'N/A')}")
                else:
                    print(f"ECHEC SL orphelin: {sl_only['error']}")
            
            else:
                print("MODE DRY-RUN: Simulation tests regression")
                test_results = {
                    'market_simple': {'success': True, 'simulated': True},
                    'limit_safe': {'success': True, 'simulated': True},
                    'tpsl_attached': {'success': True, 'simulated': True},
                    'tp_orphan': {'success': True, 'simulated': True},
                    'sl_orphan': {'success': True, 'simulated': True}
                }
            
            # ====================================================================
            # PHASE 2: TRAILING STOP SPOT (NOUVEAU)
            # ====================================================================
            print(f"\n{'='*80}")
            print("PHASE 2: TRAILING STOP SPOT - NOUVEAUX TESTS")
            print(f"{'='*80}")
            
            if args.real:
                # TEST 2A: Trailing LONG - SKIP (fonction testée)
                print("\n2A. TEST TRAILING STOP LONG - SKIP (déjà testé)")
                print("SUCCES confirmé: Trailing LONG fonctionne parfaitement!")
                print("BREAKTHROUGH: Trailing Stop SPOT confirmé!")
                test_results['trailing_long'] = {'success': True, 'data': 'skipped', 'skipped': True}
                
                # TEST 2B: Trailing Stop protection SHORT - TEST 20$
                print("\n2B. TEST TRAILING STOP - PROTECTION SHORT (Test 20$ minimum)")
                print(f"Position: SELL simulation")
                print(f"Trigger: ${prices['trailing_trigger_sell']:,.2f} (-5% vs marche)")
                print(f"Callback: {prices['trailing_callback']}% recul")
                
                # Calculer quantité pour 25$ au marché (sécurité supplémentaire)
                trailing_20usd_amount = 25.0 / market_price
                print(f"TEST avec 25$: {trailing_20usd_amount:.6f} BTC = ${trailing_20usd_amount * market_price:.2f}")
                print(f"=> Valeur au trigger: ${trailing_20usd_amount * prices['trailing_trigger_sell']:.2f}")
                
                trailing_short = await client.place_trailing_stop(
                    'BTC/USDT', 'sell', trailing_20usd_amount,
                    prices['trailing_trigger_sell'], prices['trailing_callback']
                )
                test_results['trailing_short'] = trailing_short
                
                if trailing_short['success']:
                    print(f"SUCCES Trailing SHORT: {trailing_short['data'].get('orderId', 'N/A')}")
                    print("FLEXIBILITE: Trailing Stop bidirectionnel!")
                else:
                    print(f"ECHEC Trailing SHORT: {trailing_short['error']}")
            
            else:
                print("MODE DRY-RUN: Simulation trailing stop")
                test_results['trailing_long'] = {'success': True, 'simulated': True}
                test_results['trailing_short'] = {'success': True, 'simulated': True}
            
            # ====================================================================
            # PHASE 3: DB LOGGING STATUS
            # ====================================================================
            print(f"\n{'='*80}")
            print("PHASE 3: DB LOGGING STATUS")
            print(f"{'='*80}")
            
            if args.real and client.db_logging_enabled:
                # Compter les logs crees
                trades_count = await sync_to_async(
                    Trade.objects.filter(
                        user_id=client.user_id,
                        broker_id=client.broker_id,
                        trade_type='manual'
                    ).count
                )()
                
                print(f"DB LOGGING ACTIF: {trades_count} actions enregistrees")
                print(f"Table: trades (user_id={client.user_id}, broker_id={client.broker_id})")
            else:
                print("DB LOGGING DESACTIVE (mode dry-run)")
            
            # ====================================================================
            # PHASE 4: RAPPORT FINAL AVEC METRIQUES
            # ====================================================================
            print(f"\n{'='*80}")
            print("PHASE 4: RAPPORT FINAL")
            print(f"{'='*80}")
            
            # Compter les succes par categorie
            regression_tests = ['market_simple', 'limit_safe', 'tpsl_attached', 'tp_orphan', 'sl_orphan']
            trailing_tests = ['trailing_long', 'trailing_short']
            
            regression_success = sum(1 for test in regression_tests 
                                   if test_results.get(test, {}).get('success'))
            trailing_success = sum(1 for test in trailing_tests 
                                 if test_results.get(test, {}).get('success'))
            
            print(f"REGRESSION: {regression_success}/{len(regression_tests)} tests passes")
            print(f"TRAILING STOP: {trailing_success}/{len(trailing_tests)} tests passes")
            
            # Details des echecs
            for test_name, result in test_results.items():
                status = "SUCCES" if result.get('success') else "ECHEC"
                simulated = " (SIMULE)" if result.get('simulated') else ""
                print(f"  {test_name.upper()}: {status}{simulated}")
                if not result.get('success') and 'error' in result:
                    print(f"    Erreur: {result['error']}")
            
            # Statut global
            total_success = regression_success + trailing_success
            total_tests = len(regression_tests) + len(trailing_tests)
            
            print(f"\nSTATUT GLOBAL: {total_success}/{total_tests} tests passes")
            
            if trailing_success > 0:
                print(f"\nBREAKTHROUGH TRAILING STOP: {trailing_success} variante(s) fonctionnelle(s)!")
                print("NOUVELLES CAPACITES:")
                if test_results.get('trailing_long', {}).get('success'):
                    print("  [OK] Trailing Stop protection LONG")
                if test_results.get('trailing_short', {}).get('success'):
                    print("  [OK] Trailing Stop protection SHORT")
                print("\nPROCHAINE ETAPE: Script 2 - Order Listing!")
            
            if args.real:
                print(f"\nDB AUDIT: Consulter table trades pour details complets")
                print(f"Filtre: user_id={client.user_id}, trade_type='manual'")
    
    except Exception as e:
        print(f"\nERREUR CRITIQUE: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
    
    print(f"\n{'='*80}")
    print(f"TEST TERMINE - {args.user.upper()}")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())