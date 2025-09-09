# -*- coding: utf-8 -*-
"""
Service principal pour le trading manuel
"""
import logging
from datetime import datetime
from django.utils import timezone
from asgiref.sync import sync_to_async
from apps.core.services.exchange_client import ExchangeClient as CCXTClient

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
    
    def get_available_symbols(self, filters=None, page=1, page_size=100):
        """Récupère les symboles disponibles depuis la base de données PostgreSQL - VERSION SYNCHRONE"""
        from apps.brokers.models import ExchangeSymbol
        from django.db.models import Q
        
        # SOLUTION: Méthode synchrone classique, plus de sync_to_async !
        # Construire la requête avec filtrage
        queryset = ExchangeSymbol.objects.filter(
            exchange__iexact=self.broker.exchange,
            active=True,
            type='spot'  # On ne récupère que les marchés spot pour le trading manuel
        )
        
        # Filtrage par quote assets
        if filters and not filters.get('all', False):
            quote_filters = Q()
            if filters.get('usdt', False):
                quote_filters |= Q(quote__iexact='USDT')
            if filters.get('usdc', False):
                quote_filters |= Q(quote__iexact='USDC')
            
            if quote_filters:
                queryset = queryset.filter(quote_filters)
        
        # Filtrage par recherche
        if filters and filters.get('search'):
            search_term = filters['search'].lower()
            queryset = queryset.filter(
                Q(symbol__icontains=search_term) | 
                Q(base__icontains=search_term) |
                Q(quote__icontains=search_term)
            )
        
        # Exécuter la requête et retourner la liste (synchrone = rapide!)
        symbols = list(queryset.values_list('symbol', flat=True).order_by('symbol'))
        
        # Virtual scroll - pas de vraie pagination, on retourne tout
        total = len(symbols)
        
        return {
            'symbols': symbols,
            'total': total,
            'page': 1,
            'has_next': False
        }
        
    
    async def validate_trade(self, symbol, side, quantity, order_type, price=None, 
                            stop_loss_price=None, take_profit_price=None, trigger_price=None):
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
        
        # Validation par type d'ordre
        if order_type == 'limit':
            if price is None:
                errors.append("Le prix est requis pour un ordre limite")
            else:
                price_float = float(price) if price is not None else 0
                if price_float <= 0:
                    errors.append(f"Le prix doit être positif pour un ordre limite (reçu: {price_float})")
        
        elif order_type == 'stop_loss':
            if stop_loss_price is None:
                errors.append("Le prix stop loss est requis")
            else:
                sl_price_float = float(stop_loss_price)
                if sl_price_float <= 0:
                    errors.append("Le prix stop loss doit être positif")
        
        elif order_type == 'take_profit':
            if take_profit_price is None:
                errors.append("Le prix take profit est requis")
            else:
                tp_price_float = float(take_profit_price)
                if tp_price_float <= 0:
                    errors.append("Le prix take profit doit être positif")
        
        elif order_type == 'sl_tp_combo':
            if stop_loss_price is None:
                errors.append("Le prix stop loss est requis pour le combo SL+TP")
            if take_profit_price is None:
                errors.append("Le prix take profit est requis pour le combo SL+TP")
            
            if stop_loss_price and take_profit_price:
                sl_float = float(stop_loss_price)
                tp_float = float(take_profit_price)
                if sl_float <= 0 or tp_float <= 0:
                    errors.append("Les prix SL et TP doivent être positifs")
        
        elif order_type == 'stop_limit':
            if price is None:
                errors.append("Le prix limite est requis pour un stop limit")
            if trigger_price is None:
                errors.append("Le prix de déclenchement est requis pour un stop limit")
            
            if price and trigger_price:
                price_float = float(price)
                trigger_float = float(trigger_price)
                if price_float <= 0 or trigger_float <= 0:
                    errors.append("Le prix et le trigger doivent être positifs")
        
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
            # Nouveaux champs pour ordres avances
            stop_loss_price=trade_data.get('stop_loss_price'),
            take_profit_price=trade_data.get('take_profit_price'),
            trigger_price=trade_data.get('trigger_price'),
            status='pending'
        )
        db_create_time = time.time() - db_start
        logger.info(f"✅ Trade créé en DB: ID {trade.id} ({db_create_time:.2f}s)")
        
        try:
            # Log début d'exécution
            db_time = time.time() - start_time
            logger.info(f"🔄 Exécution trade {trade.id}: {trade.side} {trade.quantity} {trade.symbol} (DB: {db_time:.2f}s)")
            
            # NOUVELLE ARCHITECTURE - Méthode unifiée CCXTClient.place_order()
            ccxt_start = time.time()
            
            # Préparer les paramètres selon le type d'ordre
            order_params = {
                'broker_id': self.broker.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'amount': float(trade.quantity),
                'order_type': trade.order_type,
                'price': float(trade.price) if trade.price else None
            }
            
            # Ajouter paramètres avancés selon le type
            if trade.order_type == 'stop_loss' and trade.stop_loss_price:
                order_params['stop_loss_price'] = float(trade.stop_loss_price)
            elif trade.order_type == 'take_profit' and trade.take_profit_price:
                order_params['take_profit_price'] = float(trade.take_profit_price)
            elif trade.order_type == 'sl_tp_combo':
                if trade.stop_loss_price:
                    order_params['stop_loss_price'] = float(trade.stop_loss_price)
                if trade.take_profit_price:
                    order_params['take_profit_price'] = float(trade.take_profit_price)
            elif trade.order_type == 'stop_limit' and trade.trigger_price:
                order_params['trigger_price'] = float(trade.trigger_price)
            
            # APPEL UNIFIÉ via place_order()
            logger.info(f"🎯 TradingService: Appel CCXTClient.place_order avec: {order_params}")
            order_result = await self.ccxt_client.place_order(**order_params)
            
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
            
            # Utiliser database_sync_to_async pour éviter les deadlocks
            from django.db import transaction
            from channels.db import database_sync_to_async
            
            logger.info(f"🔄 Sauvegarde Trade {trade.id} en failed...")
            
            @database_sync_to_async
            def save_failed_trade_sync():
                logger.info(f"🔄 Début save_failed_trade_sync pour Trade {trade.id}")
                try:
                    with transaction.atomic():
                        # Récupérer l'objet depuis la DB pour éviter les conflits
                        from apps.trading_manual.models import Trade
                        logger.info(f"🔄 Récupération Trade {trade.id} depuis DB...")
                        fresh_trade = Trade.objects.get(id=trade.id)
                        logger.info(f"🔄 Trade {trade.id} récupéré, status actuel: {fresh_trade.status}")
                        
                        # Mettre à jour avec les nouvelles valeurs
                        fresh_trade.status = trade.status
                        fresh_trade.error_message = trade.error_message
                        logger.info(f"🔄 Sauvegarde Trade {trade.id} avec status: {fresh_trade.status}")
                        
                        fresh_trade.save()
                        logger.info(f"🔄 Trade {trade.id} sauvegardé avec succès")
                        return fresh_trade.id
                except Exception as e:
                    logger.error(f"❌ Erreur dans save_failed_trade_sync: {e}")
                    raise
            
            try:
                saved_id = await save_failed_trade_sync()
                logger.info(f"✅ Trade {saved_id} marqué failed avec succès")
            except Exception as save_error:
                logger.error(f"❌ Erreur sauvegarde failed Trade {trade.id}: {save_error}")
            
            raise
    
    async def _execute_trade_order(self, trade):
        """Exécute l'ordre CCXT pour un Trade existant et met à jour le statut"""
        from datetime import datetime
        import time
        
        start_time = time.time()
        logger.info(f"🔥 _execute_trade_order START: Trade {trade.id}")
        
        try:
            # Envoyer l'ordre via CCXTClient selon le type
            ccxt_start = time.time()
            if trade.order_type == 'market':
                logger.info(f"🔥 Exécution ordre marché: {trade.side} {trade.quantity} {trade.symbol}")
                
                # Pour Bitget market buy, utiliser la valeur totale USD au lieu de la quantité
                if self.broker.exchange.lower() == 'bitget' and trade.side == 'buy' and trade.total_value:
                    logger.info(f"🔥 Bitget market buy: utilisation total_value=${trade.total_value} au lieu de quantity={trade.quantity}")
                    order_result = await self.ccxt_client.place_market_order(
                        self.broker.id, trade.symbol, trade.side, float(trade.total_value)
                    )
                else:
                    order_result = await self.ccxt_client.place_market_order(
                        self.broker.id, trade.symbol, trade.side, float(trade.quantity)
                    )
            elif trade.order_type == 'limit':
                logger.info(f"🔥 Exécution ordre limite: {trade.side} {trade.quantity} {trade.symbol} @ {trade.price}")
                order_result = await self.ccxt_client.place_limit_order(
                    self.broker.id, trade.symbol, trade.side, 
                    float(trade.quantity), float(trade.price)
                )
            else:
                # NOUVELLE ARCHITECTURE UNIFIÉE - Tous ordres avancés via place_order()
                order_params = {
                    'broker_id': self.broker.id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'amount': float(trade.quantity),
                    'order_type': trade.order_type,
                    'price': float(trade.price) if trade.price else None
                }
                
                # Ajouter paramètres avancés selon le type
                if trade.order_type == 'stop_loss' and trade.stop_loss_price:
                    logger.info(f"🔥 Exécution ordre Stop Loss: {trade.side} {trade.quantity} {trade.symbol} @ SL:{trade.stop_loss_price}")
                    order_params['stop_loss_price'] = float(trade.stop_loss_price)
                elif trade.order_type == 'take_profit' and trade.take_profit_price:
                    logger.info(f"🔥 Exécution ordre Take Profit: {trade.side} {trade.quantity} {trade.symbol} @ TP:{trade.take_profit_price}")
                    order_params['take_profit_price'] = float(trade.take_profit_price)
                elif trade.order_type == 'sl_tp_combo':
                    logger.info(f"🔥 Exécution ordre SL+TP Combo: {trade.side} {trade.quantity} {trade.symbol} SL:{trade.stop_loss_price} TP:{trade.take_profit_price}")
                    if trade.stop_loss_price:
                        order_params['stop_loss_price'] = float(trade.stop_loss_price)
                    if trade.take_profit_price:
                        order_params['take_profit_price'] = float(trade.take_profit_price)
                elif trade.order_type == 'stop_limit' and trade.trigger_price:
                    logger.info(f"🔥 Exécution ordre Stop Limit: {trade.side} {trade.quantity} {trade.symbol} @ {trade.price} trigger:{trade.trigger_price}")
                    order_params['trigger_price'] = float(trade.trigger_price)
                
                # APPEL UNIFIÉ via place_order()
                logger.info(f"🎯 _execute_trade_order: Appel CCXTClient.place_order avec: {order_params}")
                order_result = await self.ccxt_client.place_order(**order_params)
            
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
                
            trade.executed_at = timezone.now()
            
            # Utiliser database_sync_to_async pour éviter les deadlocks
            from django.db import transaction
            from channels.db import database_sync_to_async
            
            logger.info(f"🔄 Tentative sauvegarde Trade {trade.id}...")
            
            @database_sync_to_async
            def save_trade_sync():
                with transaction.atomic():
                    # Récupérer l'objet depuis la DB pour éviter les conflits
                    from apps.trading_manual.models import Trade
                    fresh_trade = Trade.objects.get(id=trade.id)
                    
                    # Mettre à jour avec les nouvelles valeurs
                    fresh_trade.status = trade.status
                    fresh_trade.exchange_order_id = trade.exchange_order_id
                    fresh_trade.filled_quantity = trade.filled_quantity
                    fresh_trade.filled_price = trade.filled_price
                    fresh_trade.fees = trade.fees
                    fresh_trade.executed_at = trade.executed_at
                    
                    fresh_trade.save()
                    return fresh_trade.id
            
            # Envoyer notification de succès AVANT sauvegarde pour éviter les blocages
            total_time = time.time() - start_time
            logger.info(f"🔄 PRIORITÉ - Envoi notification succès AVANT sauvegarde pour Trade {trade.id}")
            try:
                await self._send_success_notification(trade, total_time)
                logger.info(f"✅ PRIORITÉ - Notification succès envoyée AVANT sauvegarde pour Trade {trade.id}")
            except Exception as notif_error:
                logger.error(f"❌ PRIORITÉ - Erreur notification succès avant sauvegarde: {notif_error}")
            
            try:
                saved_id = await save_trade_sync()
                logger.info(f"✅ Trade {saved_id} sauvegardé avec succès")
                
                # Log succès avec timing total
                logger.info(f"✅ Trade {trade.id} exécuté avec succès - Order ID: {trade.exchange_order_id} (Total: {total_time:.2f}s)")
                
            except Exception as save_error:
                logger.error(f"❌ Erreur sauvegarde Trade {trade.id}: {save_error}")
                raise save_error
            
            return order_result
            
        except Exception as e:
            # Log erreur et mise à jour du trade
            error_msg = str(e)
            logger.error(f"❌ Erreur trade {trade.id}: {error_msg}")
            logger.info(f"🔥 DEBUG - Exception capturée dans _execute_trade_order pour Trade {trade.id}")
            
            trade.status = 'failed'
            trade.error_message = error_msg
            
            # NOUVEAU: Envoyer la notification AVANT de sauvegarder en DB pour éviter les blocages
            logger.info(f"🔄 PRIORITÉ - Envoi notification erreur AVANT sauvegarde pour Trade {trade.id}")
            try:
                await self._send_error_notification(trade, error_msg)
                logger.info(f"✅ PRIORITÉ - Notification erreur envoyée AVANT sauvegarde pour Trade {trade.id}")
            except Exception as notif_error:
                logger.error(f"❌ PRIORITÉ - Erreur notification avant sauvegarde: {notif_error}")
            
            # Utiliser database_sync_to_async pour éviter les deadlocks
            from django.db import transaction
            from channels.db import database_sync_to_async
            
            logger.info(f"🔄 Sauvegarde Trade {trade.id} en failed...")
            
            @database_sync_to_async
            def save_failed_trade_sync():
                logger.info(f"🔄 Début save_failed_trade_sync pour Trade {trade.id}")
                try:
                    with transaction.atomic():
                        # Récupérer l'objet depuis la DB pour éviter les conflits
                        from apps.trading_manual.models import Trade
                        logger.info(f"🔄 Récupération Trade {trade.id} depuis DB...")
                        fresh_trade = Trade.objects.get(id=trade.id)
                        logger.info(f"🔄 Trade {trade.id} récupéré, status actuel: {fresh_trade.status}")
                        
                        # Mettre à jour avec les nouvelles valeurs
                        fresh_trade.status = trade.status
                        fresh_trade.error_message = trade.error_message
                        logger.info(f"🔄 Sauvegarde Trade {trade.id} avec status: {fresh_trade.status}")
                        
                        fresh_trade.save()
                        logger.info(f"🔄 Trade {trade.id} sauvegardé avec succès")
                        return fresh_trade.id
                except Exception as e:
                    logger.error(f"❌ Erreur dans save_failed_trade_sync: {e}")
                    raise
            
            try:
                saved_id = await save_failed_trade_sync()
                logger.info(f"✅ Trade {saved_id} marqué failed avec succès")
                
            except Exception as save_error:
                logger.error(f"❌ Erreur sauvegarde failed Trade {trade.id}: {save_error}")
                # Note: La notification a déjà été envoyée avant, donc pas besoin de la renvoyer ici
            
            raise
    
    async def _send_success_notification(self, trade, execution_time):
        """Envoie une notification de succès d'exécution via WebSocket"""
        from channels.layers import get_channel_layer
        from datetime import datetime
        
        try:
            channel_layer = get_channel_layer()
            user_group_name = f"trading_notifications_{self.user.id}"
            
            logger.info(f"🔄 TRADING_SERVICE - Envoi notification succès à {user_group_name} pour Trade {trade.id}")
            
            # Construire le message de succès
            message = f"✅ Ordre exécuté avec succès ! {trade.side.upper()} {trade.filled_quantity or trade.quantity} {trade.symbol}"
            if trade.exchange_order_id:
                message += f" - ID: {trade.exchange_order_id}"
            
            # Données détaillées du trade
            trade_data = {
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'order_type': trade.order_type,
                'quantity': float(trade.quantity),
                'filled_quantity': float(trade.filled_quantity or trade.quantity),
                'price': float(trade.price) if trade.price else None,
                'filled_price': float(trade.filled_price) if trade.filled_price else None,
                'total_value': float(trade.total_value) if trade.total_value else None,
                'fees': float(trade.fees) if trade.fees else 0,
                'status': trade.status,
                'exchange_order_id': trade.exchange_order_id,
                'execution_time': round(execution_time, 2),
                'executed_at': trade.executed_at.isoformat() if trade.executed_at else None
            }
            
            await channel_layer.group_send(
                user_group_name,
                {
                    'type': 'trade_execution_success',
                    'trade_id': trade.id,
                    'message': message,
                    'trade_data': trade_data,
                    'timestamp': int(datetime.now().timestamp() * 1000)
                }
            )
            
            logger.info(f"✅ TRADING_SERVICE - Notification succès envoyée à {user_group_name} pour Trade {trade.id}")
            
        except Exception as e:
            logger.error(f"❌ TRADING_SERVICE - Erreur envoi notification succès: {e}")
            import traceback
            logger.error(f"📄 Traceback: {traceback.format_exc()}")
    
    async def _send_error_notification(self, trade, error_msg):
        """Envoie une notification d'erreur d'exécution via WebSocket"""
        from channels.layers import get_channel_layer
        from datetime import datetime
        
        logger.info(f"🔥 DEBUG _send_error_notification CALLED - Trade {trade.id}, user {self.user.id}")
        
        try:
            channel_layer = get_channel_layer()
            user_group_name = f"trading_notifications_{self.user.id}"
            
            logger.info(f"🔄 TRADING_SERVICE - Envoi notification erreur à {user_group_name} pour Trade {trade.id}")
            
            # Construire le message d'erreur
            message = f"❌ Erreur lors de l'exécution de l'ordre ! {trade.side.upper()} {trade.quantity} {trade.symbol} - {error_msg}"
            
            logger.info(f"🔥 DEBUG - Avant channel_layer.group_send pour {user_group_name}")
            
            await channel_layer.group_send(
                user_group_name,
                {
                    'type': 'trade_execution_error',
                    'trade_id': trade.id,
                    'message': message,
                    'error_details': error_msg,
                    'timestamp': int(datetime.now().timestamp() * 1000)
                }
            )
            
            logger.info(f"🔥 DEBUG - Après channel_layer.group_send pour {user_group_name}")
            logger.info(f"✅ TRADING_SERVICE - Notification erreur envoyée à {user_group_name} pour Trade {trade.id}")
            
        except Exception as e:
            logger.error(f"❌ TRADING_SERVICE - Erreur envoi notification erreur: {e}")
            import traceback
            logger.error(f"📄 Traceback: {traceback.format_exc()}")
    
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
    
    async def get_portfolio_prices(self, portfolio_assets):
        """
        Convertit les assets du portfolio en prix USDT via fetchTickers
        portfolio_assets = ['BTC', 'ETH', 'USDT'] → prix pour chaque asset
        """
        logger.info(f"🔄 get_portfolio_prices appelé pour assets: {portfolio_assets}")
        
        if not portfolio_assets:
            return {}
        
        # Filtrer les stablecoins qui n'ont pas besoin de prix
        tradable_assets = [asset for asset in portfolio_assets 
                          if asset not in ['USDT', 'USDC', 'USD']]
        
        # Convertir en paires USDT pour fetchTickers
        symbols = [f"{asset}/USDT" for asset in tradable_assets]
        
        prices = {}
        
        if symbols:
            try:
                # Récupérer tous les prix via fetchTickers en une requête
                tickers = await self.ccxt_client.get_tickers(self.broker.id, symbols)
                
                # Transformer pour le frontend: BTC/USDT → BTC
                for symbol, ticker in tickers.items():
                    asset = symbol.split('/')[0]  # BTC/USDT → BTC
                    if ticker and ticker.get('last'):
                        prices[asset] = float(ticker['last'])
                        logger.info(f"💰 Prix {asset}: ${prices[asset]}")
                    else:
                        logger.warning(f"⚠️ Pas de prix pour {asset}")
                        
            except Exception as e:
                logger.error(f"❌ Erreur récupération prix portfolio: {e}")
                raise
        
        # Ajouter les stablecoins avec prix fixe $1
        for asset in portfolio_assets:
            if asset in ['USDT', 'USDC', 'USD']:
                prices[asset] = 1.0
                
        logger.info(f"✅ Prix portfolio récupérés: {prices}")
        return prices