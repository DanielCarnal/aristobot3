# -*- coding: utf-8 -*-
"""
WebSocket Consumer pour Trading Manuel
Gère les connexions et tracking des symboles actifs
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.brokers.models import Broker

logger = logging.getLogger(__name__)

# Stockage des symboles actifs par utilisateur
active_symbols = {}  # {user_id: {'broker_id': X, 'symbol': 'BTC/USDT', 'channel_name': 'xxx'}}

class TradingManualConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour Trading Manuel"""
    
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
            
        # S'abonner directement au heartbeat pour recevoir les signaux
        await self.channel_layer.group_add("heartbeat", self.channel_name)
        await self.accept()
        
        logger.info(f"🔌 Trading Manual WebSocket connecté: {self.user.username}")

    async def disconnect(self, close_code):
        # Nettoyer le symbole actif de cet utilisateur
        if self.user.id in active_symbols:
            del active_symbols[self.user.id]
            logger.info(f"🔌 Trading Manual WebSocket déconnecté: {self.user.username}")
        
        await self.channel_layer.group_discard("heartbeat", self.channel_name)

    async def receive(self, text_data):
        """Reçoit les messages du frontend"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'track_symbol':
                # Frontend indique quel symbole il affiche
                broker_id = data.get('broker_id')
                symbol = data.get('symbol')
                
                if broker_id and symbol:
                    # Vérifier que le broker appartient à l'user
                    if await self.verify_broker_ownership(broker_id):
                        active_symbols[self.user.id] = {
                            'broker_id': broker_id,
                            'symbol': symbol,
                            'channel_name': self.channel_name
                        }
                        logger.info(f"📊 Tracking symbole {symbol} (broker {broker_id}) pour {self.user.username}")
                        
                        # Confirmer au frontend
                        await self.send(text_data=json.dumps({
                            'type': 'tracking_confirmed',
                            'broker_id': broker_id,
                            'symbol': symbol
                        }))
            
            elif action == 'stop_tracking':
                # Frontend arrête le tracking
                if self.user.id in active_symbols:
                    del active_symbols[self.user.id]
                    logger.info(f"🔌 Arrêt tracking pour {self.user.username}")
                    
        except json.JSONDecodeError:
            logger.error(f"❌ Message JSON invalide de {self.user.username}")
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")

    async def heartbeat_message(self, event):
        """Reçoit les signaux heartbeat et met à jour le prix du symbole actif"""
        try:
            # Vérifier si cet utilisateur a un symbole actif
            if self.user.id not in active_symbols:
                return
            
            user_data = active_symbols[self.user.id]
            broker_id = user_data['broker_id']
            symbol = user_data['symbol']
            
            # Récupérer le nouveau prix via CCXT
            from apps.core.services.ccxt_client import CCXTClient
            ccxt_client = CCXTClient()
            
            ticker = await ccxt_client.get_ticker(broker_id, symbol)
            
            if ticker and ticker['last'] is not None:
                current_price = float(ticker['last'])
                timestamp = ticker.get('timestamp')
                
                # Envoyer la mise à jour au frontend
                await self.send(text_data=json.dumps({
                    'type': 'price_update',
                    'symbol': symbol,
                    'broker_id': broker_id,
                    'current_price': current_price,
                    'timestamp': timestamp
                }))
                
                logger.info(f"💰 Prix heartbeat mis à jour: {symbol} = {current_price} pour {self.user.username}")
            else:
                logger.warning(f"⚠️  Prix heartbeat non disponible pour {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour prix heartbeat: {e}")

    @database_sync_to_async
    def verify_broker_ownership(self, broker_id):
        """Vérifie que le broker appartient à l'utilisateur"""
        return Broker.objects.filter(id=broker_id, user=self.user).exists()


def get_active_symbols():
    """Retourne les symboles actuellement trackés"""
    return active_symbols.copy()


class OpenOrdersConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour les ordres ouverts en temps réel"""
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Extraire broker_id des paramètres de query
        query_params = self.scope.get('query_string', b'').decode()
        self.broker_id = None
        
        if 'broker_id=' in query_params:
            try:
                self.broker_id = int(query_params.split('broker_id=')[1].split('&')[0])
            except (ValueError, IndexError):
                await self.close()
                return
        
        if not self.broker_id:
            await self.close()
            return
        
        # Vérifier que l'utilisateur possède ce broker
        try:
            self.broker = await database_sync_to_async(Broker.objects.get)(
                id=self.broker_id, user=self.user
            )
        except Broker.DoesNotExist:
            await self.close()
            return
        
        # Nom du groupe pour ce broker
        self.group_name = f"open_orders_{self.broker_id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer les ordres ouverts initiaux
        await self.send_open_orders()
        
        logger.info(f"🔌 WebSocket ordres ouverts connecté: broker {self.broker_id} pour {self.user.username}")
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        
        logger.info(f"🔌 WebSocket ordres ouverts déconnecté: broker {getattr(self, 'broker_id', 'unknown')} pour {getattr(self.user, 'username', 'unknown')}")
    
    async def receive(self, text_data):
        """Traite les messages reçus du client"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'refresh':
                await self.send_open_orders()
            elif action == 'cancel_order':
                await self.handle_cancel_order(data)
            elif action == 'edit_order':
                await self.handle_edit_order(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Action inconnue: {action}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))
        except Exception as e:
            logger.error(f"❌ Erreur WebSocket ordres ouverts: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def send_open_orders(self):
        """Récupère et envoie les ordres ouverts"""
        try:
            from .services.trading_service import TradingService
            trading_service = TradingService(self.user, self.broker)
            open_orders = await trading_service.get_open_orders()
            
            await self.send(text_data=json.dumps({
                'type': 'open_orders',
                'orders': open_orders,
                'timestamp': int(__import__('time').time() * 1000)
            }))
        except Exception as e:
            logger.error(f"❌ Erreur récupération ordres ouverts WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erreur récupération ordres: {str(e)}'
            }))
    
    async def handle_cancel_order(self, data):
        """Annule un ordre via WebSocket"""
        try:
            order_id = data.get('order_id')
            symbol = data.get('symbol')
            
            if not order_id:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'order_id requis'
                }))
                return
            
            from .services.trading_service import TradingService
            trading_service = TradingService(self.user, self.broker)
            result = await trading_service.cancel_order(order_id, symbol)
            
            await self.send(text_data=json.dumps({
                'type': 'order_cancelled',
                'order_id': order_id,
                'result': result
            }))
            
            # Rafraîchir la liste des ordres
            await self.send_open_orders()
            
            # Notifier les autres clients du même groupe
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'order_cancelled_broadcast',
                    'order_id': order_id,
                    'user_id': self.user.id
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur annulation ordre WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erreur annulation ordre: {str(e)}'
            }))
    
    async def handle_edit_order(self, data):
        """Modifie un ordre via WebSocket"""
        try:
            order_id = data.get('order_id')
            symbol = data.get('symbol')
            
            if not all([order_id, symbol]):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'order_id et symbol requis'
                }))
                return
            
            from .services.trading_service import TradingService
            trading_service = TradingService(self.user, self.broker)
            result = await trading_service.edit_order(
                order_id=order_id,
                symbol=symbol,
                order_type=data.get('order_type', 'limit'),
                side=data.get('side'),
                amount=data.get('amount'),
                price=data.get('price')
            )
            
            await self.send(text_data=json.dumps({
                'type': 'order_edited',
                'order_id': order_id,
                'result': result
            }))
            
            # Rafraîchir la liste des ordres
            await self.send_open_orders()
            
            # Notifier les autres clients du même groupe
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'order_edited_broadcast',
                    'order_id': order_id,
                    'user_id': self.user.id
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur modification ordre WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erreur modification ordre: {str(e)}'
            }))
    
    # Handlers pour les messages de groupe
    async def order_cancelled_broadcast(self, event):
        """Diffuse l'annulation d'ordre aux autres clients"""
        if event['user_id'] != self.user.id:  # Ne pas renvoyer à l'expéditeur
            await self.send(text_data=json.dumps({
                'type': 'order_cancelled_notification',
                'order_id': event['order_id']
            }))
            # Rafraîchir les ordres pour tous
            await self.send_open_orders()
    
    async def order_edited_broadcast(self, event):
        """Diffuse la modification d'ordre aux autres clients"""
        if event['user_id'] != self.user.id:  # Ne pas renvoyer à l'expéditeur
            await self.send(text_data=json.dumps({
                'type': 'order_edited_notification',
                'order_id': event['order_id']
            }))
            # Rafraîchir les ordres pour tous
            await self.send_open_orders()