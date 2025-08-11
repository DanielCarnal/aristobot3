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