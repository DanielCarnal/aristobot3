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


class TradingNotificationsConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les notifications de trading manuel
    Gère les notifications d'exécution d'ordres en temps réel
    """
    
    async def connect(self):
        """Connexion WebSocket pour les notifications de trading"""
        try:
            # Vérifier l'authentification
            user = self.scope["user"]
            if user.is_anonymous:
                logger.warning("❌ Connexion WS trading notifications refusée - utilisateur non authentifié")
                await self.close()
                return
            
            self.user = user
            
            # Groupe unique par utilisateur pour les notifications
            self.user_group_name = f"trading_notifications_{user.id}"
            
            # Rejoindre le groupe de l'utilisateur
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            # Accepter la connexion
            await self.accept()
            
            logger.info(f"✅ WebSocket trading notifications connecté pour user {user.id} - groupe: {self.user_group_name}")
            print(f"🔔 NOTIFICATIONS WebSocket connecté pour user {user.id} - groupe: {self.user_group_name}")
            
            # Envoyer message de confirmation de connexion
            await self.send(text_data=json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'WebSocket notifications connecté',
                'timestamp': self._get_timestamp()
            }))
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion WebSocket trading notifications: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket"""
        try:
            if hasattr(self, 'user_group_name'):
                await self.channel_layer.group_discard(
                    self.user_group_name,
                    self.channel_name
                )
                logger.info(f"🔌 WebSocket trading notifications déconnecté - groupe: {self.user_group_name}")
        except Exception as e:
            logger.error(f"❌ Erreur déconnexion WebSocket trading notifications: {e}")
    
    async def receive(self, text_data):
        """Réception de messages du client (optionnel pour ce consumer)"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Répondre au ping pour maintenir la connexion
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self._get_timestamp()
                }))
            else:
                logger.info(f"📨 Message reçu trading notifications: {data}")
                
        except json.JSONDecodeError:
            logger.error("❌ Format JSON invalide dans message WebSocket trading notifications")
        except Exception as e:
            logger.error(f"❌ Erreur traitement message WebSocket trading notifications: {e}")
    
    # === Handlers pour les différents types de notifications ===
    
    async def trade_execution_success(self, event):
        """Notification de succès d'exécution d'ordre"""
        await self.send(text_data=json.dumps({
            'type': 'trade_execution_success',
            'trade_id': event['trade_id'],
            'message': event['message'],
            'trade_data': event['trade_data'],
            'timestamp': event.get('timestamp', self._get_timestamp())
        }))
        
        logger.info(f"✅ Notification succès envoyée - Trade {event['trade_id']}")
    
    async def trade_execution_error(self, event):
        """Notification d'erreur d'exécution d'ordre"""
        logger.info(f"🔥 DEBUG CONSUMER - trade_execution_error method called")
        logger.info(f"🔄 CONSUMER reçoit notification erreur - Trade {event.get('trade_id', 'N/A')}: {event['message']}")
        print(f"🔔 CONSUMER ERROR - Trade {event.get('trade_id', 'N/A')}: {event['message']}")
        
        await self.send(text_data=json.dumps({
            'type': 'trade_execution_error',
            'trade_id': event.get('trade_id'),
            'message': event['message'],
            'error_details': event.get('error_details'),
            'timestamp': event.get('timestamp', self._get_timestamp())
        }))
        
        logger.info(f"✅ Notification erreur envoyée au client - Trade {event.get('trade_id', 'N/A')}")
        print(f"✅ CONSUMER - Message envoyé au client pour Trade {event.get('trade_id', 'N/A')}")
    
    async def order_status_update(self, event):
        """Notification de mise à jour de statut d'ordre"""
        await self.send(text_data=json.dumps({
            'type': 'order_status_update',
            'order_id': event['order_id'],
            'status': event['status'],
            'message': event['message'],
            'timestamp': event.get('timestamp', self._get_timestamp())
        }))
        
        logger.info(f"🔄 Notification statut ordre envoyée - Order {event['order_id']}: {event['status']}")
    
    async def general_notification(self, event):
        """Notification générale (info, warning, etc.)"""
        await self.send(text_data=json.dumps({
            'type': 'general_notification',
            'level': event.get('level', 'info'),  # info, warning, error, success
            'message': event['message'],
            'details': event.get('details'),
            'timestamp': event.get('timestamp', self._get_timestamp())
        }))
        
        logger.info(f"📢 Notification générale envoyée: {event['message']}")
    
    def _get_timestamp(self):
        """Retourne un timestamp Unix en millisecondes"""
        from datetime import datetime
        return int(datetime.now().timestamp() * 1000)