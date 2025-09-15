# -*- coding: utf-8 -*-
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Broker, ExchangeSymbol
from .serializers import BrokerSerializer, ExchangeSymbolSerializer, TestConnectionSerializer
import ccxt
import asyncio
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class BrokerViewSet(viewsets.ModelViewSet):
    """ViewSet pour gerer les brokers"""
    serializer_class = BrokerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement les brokers de l'utilisateur connecte"""
        logger.info(f"BrokerViewSet - User: {self.request.user}, Authenticated: {self.request.user.is_authenticated}")
        return Broker.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def exchanges(self, request):
        """Retourne la liste des exchanges disponibles avec leurs infos"""
        exchanges = []
        
        for exchange_id, exchange_name in Broker.EXCHANGE_CHOICES:
            try:
                # Creer une instance temporaire pour analyser les exigences
                exchange_class = getattr(ccxt, exchange_id)
                temp_instance = exchange_class()
                
                # Analyser les credentials requis
                required_credentials = []
                if temp_instance.requiredCredentials.get('apiKey', False):
                    required_credentials.append('api_key')
                if temp_instance.requiredCredentials.get('secret', False):
                    required_credentials.append('api_secret')
                if temp_instance.requiredCredentials.get('password', False):
                    required_credentials.append('api_password')
                
                exchanges.append({
                    'id': exchange_id,
                    'name': exchange_name,
                    'required_credentials': required_credentials,
                    'has_testnet': hasattr(temp_instance, 'set_sandbox_mode') or 'sandbox' in temp_instance.urls,
                    'countries': getattr(temp_instance, 'countries', []),
                    'has_future': temp_instance.has.get('future', False),
                    'has_option': temp_instance.has.get('option', False),
                })
                
            except Exception as e:
                logger.warning(f"Impossible de charger l'exchange {exchange_id}: {e}")
                # Fallback avec infos minimales
                exchanges.append({
                    'id': exchange_id,
                    'name': exchange_name,
                    'required_credentials': ['api_key', 'api_secret'],
                    'has_testnet': True,
                    'countries': [],
                    'has_future': False,
                    'has_option': False,
                })
        
        return Response({
            'exchanges': exchanges,
            'count': len(exchanges)
        })
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Teste la connexion a un broker et recupere le solde"""
        broker = self.get_object()
        success, result = broker.test_connection()
        
        if success:
            # Formater les informations de solde
            total_balance = result.get('total', {})
            free_balance = result.get('free', {})
            used_balance = result.get('used', {})
            
            # Calculer la valeur totale en USDT si possible
            total_value_usd = 0
            for symbol, amount in total_balance.items():
                if symbol == 'USDT' or symbol == 'USD' or symbol == 'USDC':
                    total_value_usd += float(amount) if amount else 0
            
            return Response({
                'success': True,
                'message': 'Connexion reussie',
                'balance': {
                    'total': total_balance,
                    'free': free_balance,
                    'used': used_balance,
                    'total_usd_equivalent': round(total_value_usd, 2)
                },
                'connection_info': {
                    'exchange': broker.exchange,
                    'testnet': broker.is_testnet,
                    'timestamp': timezone.now().isoformat()
                }
            })
        else:
            return Response({
                'success': False,
                'message': f'Erreur de connexion : {result}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_symbols(self, request, pk=None):
        """Met a jour les symboles disponibles pour un exchange"""
        broker = self.get_object()
        
        # Lancer la mise a jour en arriere-plan
        from apps.core.services.symbol_updater import SymbolUpdaterService
        from threading import Thread
        
        def update_in_background():
            try:
                stats = SymbolUpdaterService.update_symbols_sync(broker.exchange)
                
                logger.info(
                f"Mise a jour des symboles pour {broker.exchange}: "
                f"{stats.get('added', 0)} ajoutes, "
                f"{stats.get('updated', 0)} mis a jour"
                )
                    
            except Exception as e:
                logger.error(f"Erreur mise a jour symboles: {e}")
        
        thread = Thread(target=update_in_background)
        thread.daemon = True
        thread.start()
        
        return Response({
            'message': f'Mise a jour des paires de trading pour {broker.exchange} lancee en arriere-plan'
        })
    
    @action(detail=True, methods=['get'])
    def capabilities(self, request, pk=None):
        """Récupère les capacités CCXT natives d'un broker"""
        broker = self.get_object()
        show_all = request.query_params.get('all', 'false').lower() == 'true'
        
        try:
            # Utiliser CCXT déjà importé
            exchange_class = getattr(ccxt, broker.exchange)
            instance = exchange_class()
            
            if show_all:
                # Retourner TOUTES les capacités avec catégorisation
                all_capabilities = dict(instance.has)
                
                # Catégoriser les capacités
                categories = {
                    'trading': {
                        'name': 'Trading',
                        'capabilities': {}
                    },
                    'orders': {
                        'name': 'Gestion ordres', 
                        'capabilities': {}
                    },
                    'market_data': {
                        'name': 'Données marché',
                        'capabilities': {}
                    },
                    'account': {
                        'name': 'Compte',
                        'capabilities': {}
                    },
                    'websocket': {
                        'name': 'WebSocket',
                        'capabilities': {}
                    },
                    'advanced': {
                        'name': 'Avancé',
                        'capabilities': {}
                    },
                    'other': {
                        'name': 'Autres',
                        'capabilities': {}
                    }
                }
                
                # Classification automatique
                for key, value in all_capabilities.items():
                    if key in ['spot', 'future', 'margin', 'option', 'swap']:
                        categories['trading']['capabilities'][key] = value
                    elif key.startswith('create') or key.startswith('cancel') or key.startswith('edit') or 'Order' in key:
                        categories['orders']['capabilities'][key] = value
                    elif key.startswith('fetch') and not key.startswith('fetchBalance'):
                        categories['market_data']['capabilities'][key] = value
                    elif key in ['fetchBalance', 'fetchMyTrades', 'fetchTradingFee', 'fetchTradingFees']:
                        categories['account']['capabilities'][key] = value
                    elif key.startswith('ws') or 'websocket' in key.lower():
                        categories['websocket']['capabilities'][key] = value
                    elif key in ['sandbox', 'CORS', 'publicAPI', 'privateAPI']:
                        categories['advanced']['capabilities'][key] = value
                    else:
                        categories['other']['capabilities'][key] = value
                
                # Supprimer les catégories vides
                categories = {k: v for k, v in categories.items() if v['capabilities']}
                
                response_data = {
                    'exchange': broker.exchange,
                    'name': broker.name,
                    'broker_name': broker.name,
                    'show_all': True,
                    'total_capabilities': len(all_capabilities),
                    'categories': categories
                }
            else:
                # Mode normal - capacités essentielles seulement
                capabilities = {
                    'exchange': broker.exchange,
                    'name': broker.name,
                    'broker_name': broker.name,
                    'show_all': False,
                    
                    # Types de Trading
                    'spot_trading': instance.has.get('spot', True),
                    'futures_trading': instance.has.get('future', False),
                    'margin_trading': instance.has.get('margin', False),
                    
                    # Types d'ordres
                    'market_orders': instance.has.get('createMarketOrder', False),
                    'limit_orders': instance.has.get('createLimitOrder', False),
                    'stop_orders': instance.has.get('createStopOrder', False),
                    'stop_limit_orders': instance.has.get('createStopLimitOrder', False),
                    
                    # Données de marché
                    'fetch_balance': instance.has.get('fetchBalance', False),
                    'fetch_ticker': instance.has.get('fetchTicker', False),
                    'fetch_order_book': instance.has.get('fetchOrderBook', False),
                    'fetch_ohlcv': instance.has.get('fetchOHLCV', False),
                    
                    # Gestion ordres
                    'fetch_orders': instance.has.get('fetchOrders', False),
                    'fetch_open_orders': instance.has.get('fetchOpenOrders', False),
                    'cancel_order': instance.has.get('cancelOrder', False),
                    
                    # Fonctionnalités avancées
                    'websocket': instance.has.get('ws', False),
                    'sandbox': instance.has.get('sandbox', False),
                }
                response_data = capabilities
            
            logger.info(f"Capacités récupérées pour {broker.exchange}: {len(response_data)} propriétés (show_all={show_all})")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Erreur récupération capacités {broker.exchange}: {e}")
            return Response({
                'error': f'Erreur récupération capacités: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Definit un broker comme broker par defaut"""
        broker = self.get_object()
        broker.is_default = True
        broker.save()
        return Response({'message': f'{broker.name} est maintenant le broker par defaut'})


class ExchangeSymbolViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour consulter les symboles disponibles"""
    serializer_class = ExchangeSymbolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les symboles par exchange si demande"""
        queryset = ExchangeSymbol.objects.filter(active=True)
        exchange = self.request.query_params.get('exchange', None)
        if exchange:
            queryset = queryset.filter(exchange=exchange)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(symbol__icontains=search)
        return queryset