# -*- coding: utf-8 -*-
"""
Service principal pour le trading manuel
"""
import logging
from datetime import datetime
from apps.core.services.ccxt_client import CCXTClient

logger = logging.getLogger(__name__)


class TradingService:
    """Service principal pour le trading manuel"""
    
    def __init__(self, user, broker):
        self.user = user
        self.broker = broker
        self.ccxt_client = CCXTClient()
    
    async def get_balance(self):
        """Récupère le solde du broker"""
        return await self.ccxt_client.get_balance(self.broker.id)
    
    async def get_available_symbols(self, filters=None, page=1, page_size=100):
        """Récupère les symboles disponibles depuis CCXTClient avec filtrage"""
        
        # Récupération depuis CCXTClient (pas de DB)
        markets = await self.ccxt_client.get_markets(self.broker.id)
        symbols = list(markets.keys())
        
        # Filtrage par quote assets
        if filters:
            if not filters.get('all', False):
                filtered_symbols = []
                if filters.get('usdt', False):
                    filtered_symbols.extend([s for s in symbols if s.endswith('/USDT')])
                if filters.get('usdc', False):
                    filtered_symbols.extend([s for s in symbols if s.endswith('/USDC')])
                symbols = filtered_symbols
            
            # Filtrage par recherche
            if filters.get('search'):
                search_term = filters['search'].lower()
                symbols = [s for s in symbols if search_term in s.lower()]
        
        # Virtual scroll - pas de vraie pagination, on retourne tout
        total = len(symbols)
        
        return {
            'symbols': symbols,
            'total': total,
            'page': 1,
            'has_next': False
        }
        
    
    async def validate_trade(self, symbol, side, quantity, order_type, price=None):
        """Valide un trade avant exécution"""
        errors = []
        
        # Vérifier que le symbole existe
        try:
            ticker = await self.ccxt_client.get_ticker(self.broker.id, symbol)
            if ticker['last'] is None:
                errors.append(f"Prix non disponible pour {symbol}")
                return {'valid': False, 'errors': errors}
            current_price = float(ticker['last'])
        except Exception as e:
            errors.append(f"Symbole {symbol} invalide ou inaccessible: {str(e)}")
            return {'valid': False, 'errors': errors}
        
        # Vérifier la balance suffisante
        try:
            balance = await self.ccxt_client.get_balance(self.broker.id)
            
            if side == 'buy':
                # Pour un achat, vérifier USDT disponible - convertir tout en float
                used_price = float(price if price else current_price)
                quantity_float = float(quantity)
                required_amount = quantity_float * used_price
                available_usdt = float(balance.get('free', {}).get('USDT', 0))
                
                if required_amount > available_usdt:
                    errors.append(f"Balance USDT insuffisante: {available_usdt:.2f} < {required_amount:.2f}")
            
            elif side == 'sell':
                # Pour une vente, vérifier l'asset disponible - convertir en float
                asset = symbol.split('/')[0]  # BTC pour BTC/USDT
                available_asset = float(balance.get('free', {}).get(asset, 0))
                quantity_float = float(quantity)
                
                if quantity_float > available_asset:
                    errors.append(f"Balance {asset} insuffisante: {available_asset:.8f} < {quantity_float:.8f}")
                    
        except Exception as e:
            errors.append(f"Erreur vérification balance: {str(e)}")
        
        # Validation des paramètres
        quantity_float = float(quantity) if quantity is not None else 0
        if quantity_float <= 0:
            errors.append("La quantité doit être positive")
            
        # Debug: afficher les valeurs pour comprendre l'erreur
        print(f"DEBUG: order_type={order_type}, price={price}, type(price)={type(price)}")
        
        if order_type == 'limit':
            if price is None:
                errors.append("Le prix est requis pour un ordre limite")
            else:
                price_float = float(price) if price is not None else 0
                if price_float <= 0:
                    errors.append(f"Le prix doit être positif pour un ordre limite (reçu: {price_float})")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'current_price': current_price if 'current_price' in locals() else None
        }
    
    async def execute_trade(self, trade_data):
        """Exécute un trade et sauvegarde en DB avec logs complets"""
        from apps.trading_manual.models import Trade
        from asgiref.sync import sync_to_async
        import time
        
        start_time = time.time()
        logger.info(f"🚀 Début exécution trade: {trade_data}")
        
        # Créer l'objet Trade en DB (status = pending)
        logger.info(f"💾 Création Trade en DB...")
        db_start = time.time()
        trade = await sync_to_async(Trade.objects.create)(
            user=self.user,
            broker=self.broker,
            trade_type='manual',
            symbol=trade_data['symbol'],
            side=trade_data['side'],
            order_type=trade_data['order_type'],
            quantity=trade_data['quantity'],
            price=trade_data.get('price'),
            total_value=trade_data['total_value'],
            status='pending'
        )
        db_create_time = time.time() - db_start
        logger.info(f"✅ Trade créé en DB: ID {trade.id} ({db_create_time:.2f}s)")
        
        try:
            # Log début d'exécution
            db_time = time.time() - start_time
            logger.info(f"🔄 Exécution trade {trade.id}: {trade.side} {trade.quantity} {trade.symbol} (DB: {db_time:.2f}s)")
            
            # Envoyer l'ordre via CCXTClient
            ccxt_start = time.time()
            if trade.order_type == 'market':
                order_result = await self.ccxt_client.place_market_order(
                    self.broker.id, trade.symbol, trade.side, float(trade.quantity)
                )
            else:
                order_result = await self.ccxt_client.place_limit_order(
                    self.broker.id, trade.symbol, trade.side, 
                    float(trade.quantity), float(trade.price)
                )
            
            ccxt_time = time.time() - ccxt_start
            logger.info(f"📡 CCXT response reçue en {ccxt_time:.2f}s: {order_result}")
            
            # Mettre à jour le Trade avec le résultat
            trade.status = 'filled'
            trade.exchange_order_id = order_result.get('id')
            trade.filled_quantity = order_result.get('filled', trade.quantity)
            trade.filled_price = order_result.get('price', trade.price)
            trade.fees = order_result.get('fee', {}).get('cost', 0)
            trade.executed_at = datetime.now()
            
            await sync_to_async(trade.save)()
            
            # Log succès avec timing total
            total_time = time.time() - start_time
            logger.info(f"✅ Trade {trade.id} exécuté avec succès - Order ID: {trade.exchange_order_id} (Total: {total_time:.2f}s)")
            
            return trade
            
        except Exception as e:
            # Log erreur et mise à jour du trade
            error_msg = str(e)
            logger.error(f"❌ Erreur trade {trade.id}: {error_msg}")
            
            trade.status = 'failed'
            trade.error_message = error_msg
            await sync_to_async(trade.save)()
            
            raise
    
    async def _execute_trade_order(self, trade):
        """Exécute l'ordre CCXT pour un Trade existant et met à jour le statut"""
        from datetime import datetime
        import time
        
        start_time = time.time()
        logger.info(f"🔥 _execute_trade_order START: Trade {trade.id}")
        
        try:
            # Envoyer l'ordre via CCXTClient
            ccxt_start = time.time()
            if trade.order_type == 'market':
                logger.info(f"🔥 Exécution ordre marché: {trade.side} {trade.quantity} {trade.symbol}")
                order_result = await self.ccxt_client.place_market_order(
                    self.broker.id, trade.symbol, trade.side, float(trade.quantity)
                )
            else:
                logger.info(f"🔥 Exécution ordre limite: {trade.side} {trade.quantity} {trade.symbol} @ {trade.price}")
                order_result = await self.ccxt_client.place_limit_order(
                    self.broker.id, trade.symbol, trade.side, 
                    float(trade.quantity), float(trade.price)
                )
            
            ccxt_time = time.time() - ccxt_start
            logger.info(f"📡 CCXT response reçue en {ccxt_time:.2f}s: {order_result}")
            
            # Mettre à jour le Trade avec le résultat (gestion des None de Bitget)
            trade.status = 'filled'
            trade.exchange_order_id = order_result.get('id') if order_result else None
            
            # Gérer les valeurs None retournées par Bitget
            if order_result:
                trade.filled_quantity = order_result.get('filled') or trade.quantity
                trade.filled_price = order_result.get('price') or trade.price
                fee_info = order_result.get('fee')
                if fee_info and isinstance(fee_info, dict):
                    trade.fees = fee_info.get('cost', 0)
                else:
                    trade.fees = 0
            else:
                trade.filled_quantity = trade.quantity
                trade.filled_price = trade.price
                trade.fees = 0
                
            trade.executed_at = datetime.now()
            trade.save()
            
            # Log succès avec timing total
            total_time = time.time() - start_time
            logger.info(f"✅ Trade {trade.id} exécuté avec succès - Order ID: {trade.exchange_order_id} (Total: {total_time:.2f}s)")
            
            return order_result
            
        except Exception as e:
            # Log erreur et mise à jour du trade
            error_msg = str(e)
            logger.error(f"❌ Erreur trade {trade.id}: {error_msg}")
            
            trade.status = 'failed'
            trade.error_message = error_msg
            trade.save()
            
            raise
    
    async def calculate_trade_value(self, symbol, quantity=None, total_value=None, price=None):
        """Calcule quantité ↔ valeur USD selon le prix donné ou actuel"""
        from decimal import Decimal, ROUND_HALF_UP
        from datetime import datetime
        
        try:
            # Utiliser le prix fourni ou récupérer le prix actuel
            if price is not None:
                # Prix fourni (pour ordres limites)
                used_price = float(price)
                timestamp = int(datetime.now().timestamp() * 1000)  # Timestamp actuel
                logger.info(f"💰 Prix limite {symbol}: {used_price}")
            else:
                # Récupérer le prix actuel du marché
                ticker = await self.ccxt_client.get_ticker(self.broker.id, symbol)
                
                # Vérifier si le prix est disponible
                if ticker['last'] is None:
                    raise ValueError(f"Prix non disponible pour {symbol}")
                
                used_price = float(ticker['last'])
                timestamp = ticker.get('timestamp')  # Timestamp Unix en millisecondes
                
                # Si pas de timestamp CCXT, générer timestamp actuel
                if timestamp is None:
                    from datetime import datetime
                    timestamp = int(datetime.now().timestamp() * 1000)  # Unix milliseconds
                
                logger.info(f"💰 Prix marché {symbol}: {used_price} à {timestamp}")
            
            if quantity is not None:
                # Calcul valeur depuis quantité
                quantity = Decimal(str(quantity))
                used_price_decimal = Decimal(str(used_price))
                total_value_calculated = quantity * used_price_decimal
                
                return {
                    'symbol': symbol,
                    'quantity': float(quantity),
                    'current_price': used_price,
                    'total_value': float(total_value_calculated.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                    'timestamp': timestamp
                }
                
            elif total_value is not None:
                # Calcul quantité depuis valeur
                total_value_decimal = Decimal(str(total_value))
                used_price_decimal = Decimal(str(used_price))
                quantity_calculated = total_value_decimal / used_price_decimal
                
                return {
                    'symbol': symbol,
                    'quantity': float(quantity_calculated.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)),
                    'current_price': used_price,
                    'total_value': float(total_value),
                    'timestamp': timestamp
                }
            else:
                # Juste le prix utilisé
                return {
                    'symbol': symbol,
                    'current_price': used_price,
                    'timestamp': timestamp
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur calcul trade {symbol}: {e}")
            raise
    
    async def get_open_orders(self, symbol=None, limit=100):
        """Récupère les ordres ouverts via CCXTClient"""
        try:
            open_orders = await self.ccxt_client.fetch_open_orders(
                broker_id=self.broker.id,
                symbol=symbol,
                limit=limit
            )
            
            logger.info(f"📋 Récupérés {len(open_orders)} ordres ouverts pour {self.broker.name}")
            return open_orders
        except Exception as e:
            logger.error(f"❌ Erreur récupération ordres ouverts: {e}")
            raise
    
    async def get_closed_orders(self, symbol=None, since=None, limit=100):
        """Récupère les ordres fermés/exécutés via CCXTClient"""
        try:
            # Convertir since en timestamp si c'est une chaîne
            if since and isinstance(since, str):
                try:
                    since = int(since)
                except ValueError:
                    logger.warning(f"Paramètre 'since' invalide: {since}, ignoré")
                    since = None
            
            closed_orders = await self.ccxt_client.fetch_closed_orders(
                broker_id=self.broker.id,
                symbol=symbol,
                since=since,
                limit=limit
            )
            
            logger.info(f"📋 Récupérés {len(closed_orders)} ordres fermés pour {self.broker.name}")
            return closed_orders
        except Exception as e:
            logger.error(f"❌ Erreur récupération ordres fermés: {e}")
            raise
    
    async def cancel_order(self, order_id, symbol=None):
        """Annule un ordre ouvert via CCXTClient"""
        try:
            result = await self.ccxt_client.cancel_order(
                broker_id=self.broker.id,
                order_id=order_id,
                symbol=symbol
            )
            
            logger.info(f"❌ Ordre {order_id} annulé avec succès sur {self.broker.name}")
            return result
        except Exception as e:
            logger.error(f"❌ Erreur annulation ordre {order_id}: {e}")
            raise
    
    async def edit_order(self, order_id, symbol, order_type='limit', side=None, amount=None, price=None):
        """Modifie un ordre ouvert via CCXTClient"""
        try:
            result = await self.ccxt_client.edit_order(
                broker_id=self.broker.id,
                order_id=order_id,
                symbol=symbol,
                order_type=order_type,
                side=side,
                amount=amount,
                price=price
            )
            
            logger.info(f"✏️ Ordre {order_id} modifié avec succès sur {self.broker.name}")
            return result
        except Exception as e:
            logger.error(f"❌ Erreur modification ordre {order_id}: {e}")
            raise