# -*- coding: utf-8 -*-
"""
POSITION NOTIFICATIONS UTILS - Integration Terminal 7

🎯 OBJECTIF: Notifications WebSocket temps réel pour positions P&L
Intégration avec Terminal7MonitoringConsumer pour Solution 2

📋 FONCTIONNALITÉS:
- Notifications position updates via WebSocket
- Intégration avec Terminal 7 P&L calculations
- Synchronisation Frontend positions tab temps réel
- Utilise architecture existante Terminal7MonitoringConsumer
"""

import logging
import time
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)
User = get_user_model()


async def notify_position_update(user_id: int, broker_id: int, position_data: dict):
    """
    🔔 NOTIFICATION POSITION UPDATE
    
    Envoie une notification WebSocket temps réel d'une mise à jour de position
    calculée par Terminal 7. Intégration avec Terminal7MonitoringConsumer.
    
    Args:
        user_id: ID utilisateur
        broker_id: ID broker concerné  
        position_data: Données position calculées par Terminal 7
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("⚠️ Channel layer indisponible pour notification position")
            return
        
        # Groupe WebSocket utilisateur pour Trading Manual
        user_group_name = f"trading_manual_{user_id}"
        
        # Message standardisé position update
        message_data = {
            'type': 'position_pnl_update',
            'source': 'terminal7_order_monitor',
            'broker_id': broker_id,
            'position_data': position_data,
            'timestamp': int(time.time() * 1000)
        }
        
        # Envoyer via Terminal7MonitoringConsumer
        await channel_layer.group_send(
            user_group_name,
            message_data
        )
        
        logger.info(f"🔔 Position update notification envoyée - User {user_id}, "
                   f"Symbol: {position_data.get('symbol')}, "
                   f"P&L: {position_data.get('realized_pnl')}")
        
    except Exception as e:
        logger.error(f"❌ Erreur notification position update: {e}")


async def notify_positions_batch_update(user_id: int, broker_id: int, 
                                      positions_list: list, statistics: dict):
    """
    📊 NOTIFICATION POSITIONS BATCH
    
    Envoie une notification de mise à jour batch de toutes les positions
    pour un broker. Utilisé lors de recalculs Terminal 7 globaux.
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("⚠️ Channel layer indisponible pour batch notification")
            return
        
        user_group_name = f"trading_manual_{user_id}"
        
        message_data = {
            'type': 'positions_batch_update',
            'source': 'terminal7_batch_calculation',
            'broker_id': broker_id,
            'positions_count': len(positions_list),
            'positions': positions_list,
            'statistics': statistics,
            'timestamp': int(time.time() * 1000)
        }
        
        await channel_layer.group_send(
            user_group_name,
            message_data
        )
        
        logger.info(f"📊 Positions batch notification envoyée - User {user_id}, "
                   f"Broker: {broker_id}, Count: {len(positions_list)}")
        
    except Exception as e:
        logger.error(f"❌ Erreur notification positions batch: {e}")


async def notify_new_trade_detected(user_id: int, broker_id: int, trade_data: dict):
    """
    🆕 NOTIFICATION NOUVEAU TRADE DÉTECTÉ
    
    Notification lorsque Terminal 7 détecte un nouvel ordre exécuté.
    Déclenche mise à jour automatique positions P&L frontend.
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Groupes: Trading Manual + général Terminal 7
        user_group_name = f"trading_manual_{user_id}"
        
        # Message pour le frontend Trading Manual
        message_data = {
            'type': 'new_trade_detected',
            'source': 'terminal7_order_monitor', 
            'broker_id': broker_id,
            'trade_data': {
                'id': trade_data.get('id'),
                'symbol': trade_data.get('symbol'),
                'side': trade_data.get('side'),
                'quantity': trade_data.get('quantity'),
                'price': trade_data.get('price'),
                'realized_pnl': trade_data.get('realized_pnl'),
                'pnl_calculation_method': trade_data.get('pnl_calculation_method'),
                'executed_at': trade_data.get('executed_at')
            },
            'action_required': 'refresh_positions',  # Frontend sait qu'il faut rafraîchir
            'timestamp': int(time.time() * 1000)
        }
        
        await channel_layer.group_send(
            user_group_name,
            message_data
        )
        
        logger.info(f"🆕 Nouveau trade notification envoyée - User {user_id}, "
                   f"Trade: {trade_data.get('symbol')} {trade_data.get('side')}")
        
    except Exception as e:
        logger.error(f"❌ Erreur notification nouveau trade: {e}")


async def get_broker_name(broker_id: int) -> str:
    """Helper: récupère le nom du broker"""
    try:
        from apps.brokers.models import Broker
        broker = await sync_to_async(Broker.objects.get)(id=broker_id)
        return broker.name
    except:
        return f"Broker {broker_id}"


# === INTÉGRATION TERMINAL 7 ===

def send_position_notification_sync(user_id: int, broker_id: int, position_data: dict):
    """
    Version synchrone pour utilisation dans Terminal 7 management command
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(notify_position_update(user_id, broker_id, position_data))
    except RuntimeError:
        # Pas de loop, créer une tâche synchrone
        import threading
        def run_async():
            asyncio.run(notify_position_update(user_id, broker_id, position_data))
        
        thread = threading.Thread(target=run_async)
        thread.start()


def send_batch_notification_sync(user_id: int, broker_id: int, 
                                positions_list: list, statistics: dict):
    """
    Version synchrone pour batch updates Terminal 7
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(notify_positions_batch_update(
            user_id, broker_id, positions_list, statistics
        ))
    except RuntimeError:
        import threading
        def run_async():
            asyncio.run(notify_positions_batch_update(
                user_id, broker_id, positions_list, statistics
            ))
        
        thread = threading.Thread(target=run_async)
        thread.start()