# -*- coding: utf-8 -*-
"""
ViewSets et APIs pour Trading Manuel - Module 3
"""
import asyncio
import logging
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
            result = asyncio.run(trading_service.get_available_symbols(
                filters, data.get('page', 1), data.get('page_size', 100)
            ))
            
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