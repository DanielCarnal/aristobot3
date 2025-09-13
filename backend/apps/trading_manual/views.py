# -*- coding: utf-8 -*-
"""
ViewSets et APIs pour Trading Manuel - Module 3
"""
import asyncio
import logging
import time
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from asgiref.sync import sync_to_async
from apps.brokers.models import Broker
from .models import Trade
from .serializers import (
    TradeSerializer, TradeExecutionSerializer, SymbolFilterSerializer,
    CalculateTradeSerializer, ValidationTradeSerializer
)
from .services.trading_service import TradingService
from .services.portfolio_service import PortfolioService

logger = logging.getLogger(__name__)


class TradeViewSet(ModelViewSet):
    """ViewSet pour la gestion des trades"""
    
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrage multi-tenant strict"""
        return Trade.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Associer l'user et le broker lors de la creation"""
        serializer.save(user=self.request.user)


class PortfolioView(APIView):
    """Vue pour recuperer le resume du portfolio"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        broker_id = request.GET.get('broker_id')
        if not broker_id:
            return Response({'error': 'broker_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            portfolio_service = PortfolioService(request.user, broker)
            result = asyncio.run(portfolio_service.get_portfolio_summary())
            return Response(result)
        except Exception as e:
            logger.error(f"Erreur recuperation portfolio: {e}")
            return Response(
                {'error': f'Erreur recuperation portfolio: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BalanceView(APIView):
    """Vue pour recuperer uniquement la balance"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        broker_id = request.GET.get('broker_id')
        if not broker_id:
            return Response({'error': 'broker_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            balance = asyncio.run(trading_service.get_balance())
            return Response({'balance': balance})
        except Exception as e:
            logger.error(f"Erreur recuperation balance: {e}")
            return Response(
                {'error': f'Erreur recuperation balance: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SymbolFilteredView(APIView):
    """Liste des symboles avec filtrage avance"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = SymbolFilterSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            broker = Broker.objects.get(id=data['broker_id'], user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            filters = {
                'usdt': data.get('usdt', True),
                'usdc': data.get('usdc', False), 
                'all': data.get('all', False),
                'search': data.get('search', '')
            }
            
            trading_service = TradingService(request.user, broker)
            # PLUS BESOIN de asyncio.run() car get_available_symbols() est maintenant synchrone !
            result = trading_service.get_available_symbols(
                filters, data.get('page', 1), data.get('page_size', 100)
            )
            
            return Response(result)
        except Exception as e:
            logger.error(f"Erreur recuperation symboles: {e}")
            return Response(
                {'error': f'Erreur recuperation symboles: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExchangeInfoView(APIView):
    """Informations sur les capacites d'un exchange via exchange.has"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, broker_id):
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Recuperer les capacites CCXT completes via exchange.has
            import ccxt
            exchange_class = getattr(ccxt, broker.exchange)
            exchange_instance = exchange_class()
            
            # Attribut exchange.has complet
            exchange_has = exchange_instance.has
            
            # Formatage pour l'affichage frontend
            capabilities = {
                'exchange': broker.exchange,
                'name': broker.name,
                'rate_limit': exchange_instance.rateLimit,
                
                # Capacites principales
                'spot_trading': exchange_has.get('spot', True),
                'futures_trading': exchange_has.get('future', False),
                'margin_trading': exchange_has.get('margin', False),
                'options_trading': exchange_has.get('option', False),
                
                # Types d'ordres
                'market_orders': exchange_has.get('createMarketOrder', False),
                'limit_orders': exchange_has.get('createLimitOrder', False),
                'stop_orders': exchange_has.get('createStopOrder', False),
                'stop_limit_orders': exchange_has.get('createStopLimitOrder', False),
                
                # Fonctionnalites avancees
                'websocket': exchange_has.get('ws', False),
                'sandbox': exchange_has.get('sandbox', False),
                'cors': exchange_has.get('CORS', False),
                
                # Donnees de marche
                'fetch_balance': exchange_has.get('fetchBalance', False),
                'fetch_ticker': exchange_has.get('fetchTicker', False),
                'fetch_order_book': exchange_has.get('fetchOrderBook', False),
                'fetch_ohlcv': exchange_has.get('fetchOHLCV', False),
                'fetch_trades': exchange_has.get('fetchTrades', False),
                
                # Gestion des ordres
                'fetch_orders': exchange_has.get('fetchOrders', False),
                'fetch_open_orders': exchange_has.get('fetchOpenOrders', False),
                'cancel_order': exchange_has.get('cancelOrder', False),
                'cancel_all_orders': exchange_has.get('cancelAllOrders', False),
                
                # Capacites brutes pour debug (optionnel)
                'raw_has': exchange_has
            }
            
            return Response(capabilities)
        except Exception as e:
            logger.error(f"Erreur recuperation capacites exchange: {e}")
            return Response(
                {'error': f'Erreur recuperation capacites: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CalculateTradeView(APIView):
    """Calcul automatique quantite <-> valeur USD"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CalculateTradeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            broker = Broker.objects.get(id=data['broker_id'], user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            result = asyncio.run(trading_service.calculate_trade_value(
                data['symbol'],
                data.get('quantity'),
                data.get('total_value'),
                data.get('price')  # Passer le prix limite si fourni
            ))
            
            return Response(result)
        except Exception as e:
            logger.error(f"Erreur calcul trade: {e}")
            return Response(
                {'error': f'Erreur calcul trade: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ValidateTradeView(APIView):
    """Validation d'un trade avant execution"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logger.info(f"🔍 ValidateTradeView: Data reçue: {request.data}")
        
        serializer = ValidationTradeSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"❌ Validation serializer échouée: {serializer.errors}")
            logger.error(f"📊 Data envoyée: {request.data}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            broker = Broker.objects.get(id=data['broker_id'], user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            validation = asyncio.run(trading_service.validate_trade(
                data['symbol'],
                data['side'],
                data['quantity'],
                data['order_type'],
                data.get('price'),
                data.get('stop_loss_price'),
                data.get('take_profit_price'),
                data.get('trigger_price')
            ))
            
            return Response(validation)
        except Exception as e:
            logger.error(f"Erreur validation trade: {e}")
            return Response(
                {'error': f'Erreur validation trade: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExecuteTradeView(APIView):
    """Execute un trade manuel"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        import time
        request_start = time.time()
        logger.info(f"🚀 ExecuteTradeView: Début requête trade")
        logger.info(f"📊 Data reçue: {request.data}")
        
        serializer = TradeExecutionSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"❌ Validation serializer échouée: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        logger.info(f"✅ Serializer validé en {time.time() - request_start:.2f}s")
        
        try:
            broker = Broker.objects.get(id=data['broker_id'], user=request.user)
            logger.info(f"✅ Broker trouvé: {broker.name} (ID: {broker.id})")
        except Broker.DoesNotExist:
            logger.error(f"❌ Broker non trouvé: {data['broker_id']}")
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            logger.info(f"✅ TradingService créé en {time.time() - request_start:.2f}s")
            
            # Validation prealable
            validation_start = time.time()
            logger.info(f"🔍 Début validation trade...")
            validation = asyncio.run(trading_service.validate_trade(
                data['symbol'],
                data['side'],
                data['quantity'],
                data['order_type'],
                data.get('price'),
                data.get('stop_loss_price'),
                data.get('take_profit_price'),
                data.get('trigger_price')
            ))
            logger.info(f"✅ Validation terminée en {time.time() - validation_start:.2f}s: {validation['valid']}")
            
            if not validation['valid']:
                logger.error(f"❌ Validation échouée: {validation['errors']}")
                return Response({
                    'error': 'Validation echouee',
                    'details': validation['errors']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Execution - Revenir à l'ancienne méthode qui fonctionnait
            execution_start = time.time()
            logger.info(f"🚀 Début exécution trade...")
            
            # Créer Trade DIRECTEMENT en DB (pas async - évite deadlock)
            try:
                from apps.trading_manual.models import Trade
                
                logger.info(f"💾 Création Trade directe en DB...")
                trade = Trade.objects.create(
                    user=request.user,
                    broker=broker,
                    trade_type='manual',
                    symbol=data['symbol'],
                    side=data['side'],
                    order_type=data['order_type'],
                    quantity=data['quantity'],
                    price=data.get('price'),
                    total_value=data['total_value'],
                    # Nouveaux champs pour ordres avancés
                    stop_loss_price=data.get('stop_loss_price'),
                    take_profit_price=data.get('take_profit_price'),
                    trigger_price=data.get('trigger_price'),
                    status='pending'
                )
                logger.info(f"✅ Trade {trade.id} créé en DB")
                
                # Puis exécuter via _execute_trade_order (ancienne méthode)
                trading_service = TradingService(request.user, broker)
                order_result = asyncio.run(trading_service._execute_trade_order(trade))
                
                # Récupérer le trade mis à jour depuis la DB
                trade.refresh_from_db()
                
                # Sérialiser le trade retourné
                trade_serializer = TradeSerializer(trade)
                total_time = time.time() - request_start
                logger.info(f"✅ ExecuteTradeView: Succès en {total_time:.2f}s")
                
                return Response(trade_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"❌ Erreur exécution trade: {e}")
                
                # Envoyer notification d'erreur
                try:
                    if 'trade' in locals():
                        asyncio.run(self._send_error_notification(
                            request.user, trade.id,
                            f'Erreur lors de l\'execution: {str(e)}', str(e)
                        ))
                except:
                    pass
                
                return Response({
                    'error': f'Erreur execution trade: {str(e)}',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            total_time = time.time() - request_start
            logger.error(f"❌ Erreur execution trade après {total_time:.2f}s: {e}")
            import traceback
            logger.error(f"📄 Traceback: {traceback.format_exc()}")
            
            # Envoyer notification d'erreur générale via WebSocket
            asyncio.run(self._send_error_notification(
                request.user, None,
                f'Erreur fatale lors de l\'exécution: {str(e)}', str(e)
            ))
            
            return Response(
                {'error': f'Erreur execution trade: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def _send_success_notification(self, user, trade, execution_time):
        """Envoie une notification de succès d'exécution via WebSocket"""
        from channels.layers import get_channel_layer
        from datetime import datetime
        
        try:
            channel_layer = get_channel_layer()
            user_group_name = f"trading_notifications_{user.id}"
            
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
            
            logger.info(f"✅ Notification succès envoyée à {user_group_name} pour Trade {trade.id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi notification succès: {e}")
    
    async def _send_error_notification(self, user, trade_id, message, error_details):
        """Envoie une notification d'erreur d'exécution via WebSocket"""
        from channels.layers import get_channel_layer
        from datetime import datetime
        
        try:
            channel_layer = get_channel_layer()
            user_group_name = f"trading_notifications_{user.id}"
            
            logger.info(f"🔄 TENTATIVE envoi notification erreur à {user_group_name} pour Trade {trade_id or 'N/A'}")
            
            await channel_layer.group_send(
                user_group_name,
                {
                    'type': 'trade_execution_error',
                    'trade_id': trade_id,
                    'message': message,
                    'error_details': error_details,
                    'timestamp': int(datetime.now().timestamp() * 1000)
                }
            )
            
            logger.info(f"✅ Notification erreur envoyée à {user_group_name} pour Trade {trade_id or 'N/A'}")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi notification erreur: {e}")
            import traceback
            logger.error(f"📄 Traceback: {traceback.format_exc()}")


class CurrentPriceView(APIView):
    """Recupere le prix actuel d'un symbole"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, symbol):
        broker_id = request.GET.get('broker_id')
        if not broker_id:
            return Response({'error': 'broker_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            result = asyncio.run(trading_service.calculate_trade_value(symbol))
            
            return Response({
                'symbol': symbol,
                'current_price': result['current_price'],
                'timestamp': result.get('timestamp')
            })
        except Exception as e:
            logger.error(f"Erreur recuperation prix {symbol}: {e}")
            return Response(
                {'error': f'Erreur recuperation prix: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OpenOrdersView(APIView):
    """Gestion des ordres ouverts"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère les ordres ouverts"""
        broker_id = request.GET.get('broker_id')
        if not broker_id:
            return Response({'error': 'broker_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            open_orders = asyncio.run(trading_service.get_open_orders(
                symbol=request.GET.get('symbol'),
                limit=request.GET.get('limit', 100)
            ))
            
            return Response({'orders': open_orders})
        except Exception as e:
            logger.error(f"Erreur récupération ordres ouverts: {e}")
            return Response(
                {'error': f'Erreur récupération ordres: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClosedOrdersView(APIView):
    """Gestion des ordres fermés/exécutés"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère les ordres fermés"""
        broker_id = request.GET.get('broker_id')
        if not broker_id:
            return Response({'error': 'broker_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            closed_orders = asyncio.run(trading_service.get_closed_orders(
                symbol=request.GET.get('symbol'),
                since=request.GET.get('since'),
                limit=request.GET.get('limit', 100)
            ))
            
            return Response({'orders': closed_orders})
        except Exception as e:
            logger.error(f"Erreur récupération ordres fermés: {e}")
            return Response(
                {'error': f'Erreur récupération ordres fermés: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CancelOrderView(APIView):
    """Annule un ordre ouvert"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        broker_id = request.data.get('broker_id')
        order_id = request.data.get('order_id')
        symbol = request.data.get('symbol')
        
        if not all([broker_id, order_id]):
            return Response({'error': 'broker_id et order_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            result = asyncio.run(trading_service.cancel_order(order_id, symbol))
            
            return Response({
                'success': True,
                'message': 'Ordre annulé avec succès',
                'result': result
            })
        except Exception as e:
            logger.error(f"Erreur annulation ordre {order_id}: {e}")
            return Response(
                {'error': f'Erreur annulation ordre: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EditOrderView(APIView):
    """Modifie un ordre ouvert"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        broker_id = request.data.get('broker_id')
        order_id = request.data.get('order_id')
        symbol = request.data.get('symbol')
        
        if not all([broker_id, order_id, symbol]):
            return Response({'error': 'broker_id, order_id et symbol requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            result = asyncio.run(trading_service.edit_order(
                order_id=order_id,
                symbol=symbol,
                order_type=request.data.get('order_type', 'limit'),
                side=request.data.get('side'),
                amount=request.data.get('amount'),
                price=request.data.get('price')
            ))
            
            return Response({
                'success': True,
                'message': 'Ordre modifié avec succès',
                'result': result
            })
        except Exception as e:
            logger.error(f"Erreur modification ordre {order_id}: {e}")
            return Response(
                {'error': f'Erreur modification ordre: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PortfolioPricesView(APIView):
    """Récupère les prix des assets du portfolio via fetchTickers"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        broker_id = request.data.get('broker_id')
        assets = request.data.get('assets', [])
        
        if not broker_id:
            return Response({'error': 'broker_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not assets:
            return Response({'prices': {}})
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trading_service = TradingService(request.user, broker)
            prices = asyncio.run(trading_service.get_portfolio_prices(assets))
            
            logger.info(f"✅ Prix portfolio envoyés: {len(prices)} assets")
            return Response({'prices': prices})
        except Exception as e:
            logger.error(f"Erreur récupération prix portfolio: {e}")
            return Response(
                {'error': f'Erreur récupération prix: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PositionsView(APIView):
    """
    🎯 API POSITIONS P&L - Données Terminal 7
    
    Sert les positions calculées automatiquement par Terminal 7 avec P&L en temps réel.
    Source: Trades avec source='order_monitor' enrichis par Terminal 7.
    
    📊 FONCTIONNALITÉS:
    - Positions actives avec P&L calculé
    - Historique des positions fermées
    - Calculs automatiques price averaging → FIFO
    - Intégration WebSocket temps réel
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/trading-manual/positions/?broker_id=X&status=active|closed|all
        
        Récupère les positions P&L calculées par Terminal 7
        """
        broker_id = request.GET.get('broker_id')
        position_status = request.GET.get('status', 'active')  # active, closed, all
        limit = int(request.GET.get('limit', 50))
        
        if not broker_id:
            return Response({'error': 'broker_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            broker = Broker.objects.get(id=broker_id, user=request.user)
        except Broker.DoesNotExist:
            return Response({'error': 'Broker introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Récupérer les positions calculées par Terminal 7
            positions_data = self._get_terminal7_positions(
                request.user, broker, position_status, limit
            )
            
            logger.info(f"📊 Positions Terminal 7 pour {request.user.username}: "
                       f"{positions_data['count']} positions ({position_status})")
            
            return Response(positions_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération positions P&L: {e}")
            return Response(
                {'error': f'Erreur récupération positions: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_terminal7_positions(self, user, broker, position_status, limit):
        """
        🧮 POSITIONS P&L TERMINAL 7
        
        Récupère et calcule les positions basées sur les trades Terminal 7.
        Logique: 1 position = ensemble de trades order_monitor pour un symbole.
        """
        from django.db.models import Q, Sum, Avg, Max, Min, Count
        from collections import defaultdict
        from decimal import Decimal
        
        # Base queryset: trades Terminal 7 uniquement
        base_queryset = Trade.objects.filter(
            user=user,
            broker=broker,
            source='order_monitor'  # Trades détectés par Terminal 7
        ).select_related('broker')
        
        # Grouper par symbole pour calculer les positions
        symbols = base_queryset.values_list('symbol', flat=True).distinct()
        
        positions = []
        for symbol in symbols:
            # Trades pour ce symbole
            symbol_trades = base_queryset.filter(symbol=symbol).order_by('executed_at')
            
            if not symbol_trades.exists():
                continue
                
            # Calculer la position nette
            position_data = self._calculate_symbol_position(symbol_trades, symbol)
            
            # Filtrer selon le status demandé
            if position_status == 'active' and position_data['net_quantity'] == 0:
                continue
            elif position_status == 'closed' and position_data['net_quantity'] != 0:
                continue
            
            positions.append(position_data)
        
        # Trier par P&L ou date
        positions.sort(key=lambda x: x['last_trade_date'], reverse=True)
        
        # Appliquer limite
        positions = positions[:limit]
        
        # Statistiques globales
        total_realized_pnl = sum(pos['realized_pnl'] for pos in positions)
        active_positions = len([p for p in positions if p['net_quantity'] != 0])
        
        return {
            'success': True,
            'positions': positions,
            'count': len(positions),
            'statistics': {
                'total_realized_pnl': float(total_realized_pnl),
                'active_positions': active_positions,
                'closed_positions': len(positions) - active_positions,
                'broker_name': broker.name,
                'broker_exchange': broker.exchange
            },
            'metadata': {
                'status_filter': position_status,
                'limit_applied': limit,
                'calculation_method': 'terminal7_price_averaging',
                'timestamp': int(time.time() * 1000)
            }
        }
    
    def _calculate_symbol_position(self, symbol_trades, symbol):
        """
        🧮 CALCUL POSITION INDIVIDUELLE
        
        Calcule les métriques P&L pour un symbole basé sur les trades Terminal 7.
        Utilise la logique price averaging → FIFO intégrée dans Terminal 7.
        """
        from decimal import Decimal
        import time
        
        # Métriques de base
        trades_list = list(symbol_trades)
        total_trades = len(trades_list)
        
        if not trades_list:
            return self._empty_position(symbol)
        
        # Calculs agrégés via Terminal 7
        net_quantity = Decimal('0')
        total_buy_quantity = Decimal('0')
        total_sell_quantity = Decimal('0')
        total_buy_value = Decimal('0')
        total_sell_value = Decimal('0')
        total_fees = Decimal('0')
        
        # P&L basé sur Terminal 7
        realized_pnl = Decimal('0')
        first_trade_date = None
        last_trade_date = None
        
        for trade in trades_list:
            quantity = trade.filled_quantity or trade.quantity
            price = trade.filled_price or trade.price or Decimal('0')
            fees = trade.fees or Decimal('0')
            
            # Dates
            trade_date = trade.executed_at or trade.created_at
            if not first_trade_date or trade_date < first_trade_date:
                first_trade_date = trade_date
            if not last_trade_date or trade_date > last_trade_date:
                last_trade_date = trade_date
            
            # Accumulations
            total_fees += fees
            
            if trade.side == 'buy':
                net_quantity += quantity
                total_buy_quantity += quantity
                total_buy_value += quantity * price
            else:  # sell
                net_quantity -= quantity
                total_sell_quantity += quantity
                total_sell_value += quantity * price
            
            # P&L calculé par Terminal 7 (si disponible)
            if trade.realized_pnl is not None:
                realized_pnl += trade.realized_pnl
        
        # Prix moyens
        avg_buy_price = total_buy_value / total_buy_quantity if total_buy_quantity > 0 else Decimal('0')
        avg_sell_price = total_sell_value / total_sell_quantity if total_sell_quantity > 0 else Decimal('0')
        
        # Si Terminal 7 n'a pas calculé le P&L, fallback manuel
        if realized_pnl == 0 and total_sell_quantity > 0:
            # Simple: (prix vente moyen - prix achat moyen) * quantité vendue
            realized_pnl = (avg_sell_price - avg_buy_price) * total_sell_quantity - total_fees
        
        # P&L calculation method (Terminal 7 intelligent)
        pnl_method = 'terminal7_automatic'
        latest_trade = max(trades_list, key=lambda t: t.executed_at or t.created_at)
        if latest_trade.pnl_calculation_method != 'none':
            pnl_method = latest_trade.pnl_calculation_method
        
        # Statut position
        position_status = 'active' if abs(net_quantity) > Decimal('0.00000001') else 'closed'
        
        return {
            'symbol': symbol,
            'net_quantity': float(net_quantity),
            'position_status': position_status,
            
            # Métriques de trading
            'total_trades': total_trades,
            'total_buy_quantity': float(total_buy_quantity),
            'total_sell_quantity': float(total_sell_quantity),
            'avg_buy_price': float(avg_buy_price),
            'avg_sell_price': float(avg_sell_price),
            
            # P&L Terminal 7
            'realized_pnl': float(realized_pnl),
            'total_fees': float(total_fees),
            'pnl_calculation_method': pnl_method,
            
            # Dates
            'first_trade_date': first_trade_date.isoformat() if first_trade_date else None,
            'last_trade_date': last_trade_date.isoformat() if last_trade_date else None,
            
            # Métadonnées
            'net_profit_percentage': float((realized_pnl / total_buy_value) * 100) if total_buy_value > 0 else 0.0,
            'is_profitable': realized_pnl > 0,
            'source': 'terminal7_order_monitor'
        }
    
    def _empty_position(self, symbol):
        """Position vide pour consistance API"""
        return {
            'symbol': symbol,
            'net_quantity': 0.0,
            'position_status': 'closed',
            'total_trades': 0,
            'total_buy_quantity': 0.0,
            'total_sell_quantity': 0.0,
            'avg_buy_price': 0.0,
            'avg_sell_price': 0.0,
            'realized_pnl': 0.0,
            'total_fees': 0.0,
            'pnl_calculation_method': 'none',
            'first_trade_date': None,
            'last_trade_date': None,
            'net_profit_percentage': 0.0,
            'is_profitable': False,
            'source': 'terminal7_order_monitor'
        }