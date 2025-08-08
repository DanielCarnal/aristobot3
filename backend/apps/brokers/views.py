from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Broker, ExchangeSymbol
from .serializers import BrokerSerializer, ExchangeSymbolSerializer, TestConnectionSerializer
from apps.core.services.ccxt_service import ccxt_service
import ccxt
import asyncio
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class BrokerViewSet(viewsets.ModelViewSet):
    """ViewSet pour gerer les brokers"""
    serializer_class = BrokerSerializer
    
    def get_queryset(self):
        """Retourne uniquement les brokers de l'utilisateur connecte"""
        return Broker.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Teste la connexion a un broker"""
        broker = self.get_object()
        success, result = broker.test_connection()
        
        if success:
            return Response({
                'success': True,
                'message': 'Connexion reussie',
                'balance': result.get('total', {})
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
        from apps.core.services import SymbolUpdaterService
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