# -*- coding: utf-8 -*-
"""
MODULE 4 - WEBHOOKS VIEWS
APIs REST pour le frontend WebhooksView.vue
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from decimal import Decimal

from .models import Webhook, WebhookState
from .serializers import (
    WebhookSerializer,
    WebhookStatsSerializer,
    WebhookStateSerializer,
)


class WebhookViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour l'historique des webhooks
    Endpoints:
    - GET /api/webhooks/ : Liste des webhooks (filtrable)
    - GET /api/webhooks/{id}/ : Detail d'un webhook
    - GET /api/webhooks/stats/ : Statistiques globales
    """
    serializer_class = WebhookSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['symbol', 'action', 'status', 'broker']
    ordering_fields = ['received_at', 'processed_at']
    ordering = ['-received_at']  # Plus recent en premier

    def get_queryset(self):
        """Filtre multi-tenant par user_id"""
        return Webhook.objects.filter(
            user=self.request.user
        ).select_related('user', 'broker')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        GET /api/webhooks/stats/
        Statistiques globales sur les webhooks

        Query params:
        - period: '24h', '7d', '30d' (default: '24h')
        - broker_id: Filtrer par broker (optionnel)
        """
        # Periode
        period = request.query_params.get('period', '24h')
        if period == '24h':
            period_start = timezone.now() - timedelta(hours=24)
        elif period == '7d':
            period_start = timezone.now() - timedelta(days=7)
        elif period == '30d':
            period_start = timezone.now() - timedelta(days=30)
        else:
            period_start = timezone.now() - timedelta(hours=24)

        period_end = timezone.now()

        # Base queryset
        queryset = Webhook.objects.filter(
            user=request.user,
            received_at__gte=period_start,
            received_at__lte=period_end
        )

        # Filtre par broker si demande
        broker_id = request.query_params.get('broker_id')
        if broker_id:
            queryset = queryset.filter(broker_id=broker_id)

        # Statistiques totales
        total_webhooks = queryset.count()

        # Par status
        status_counts = queryset.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        received = status_dict.get('received', 0)
        processing = status_dict.get('processing', 0)
        processed = status_dict.get('processed', 0)
        errors = status_dict.get('error', 0)
        missed = status_dict.get('miss', 0)

        # Par action
        actions_counts = queryset.values('action').annotate(count=Count('id'))
        actions_breakdown = {item['action']: item['count'] for item in actions_counts}

        # Taux de succes
        if total_webhooks > 0:
            success_rate = (processed / total_webhooks) * 100
        else:
            success_rate = 0.0

        # Dernier webhook
        last_webhook = queryset.order_by('-received_at').first()
        last_webhook_time = last_webhook.received_at if last_webhook else None

        # Serializer
        data = {
            'total_webhooks': total_webhooks,
            'received': received,
            'processing': processing,
            'processed': processed,
            'errors': errors,
            'missed': missed,
            'actions_breakdown': actions_breakdown,
            'success_rate': round(success_rate, 2),
            'last_webhook_time': last_webhook_time,
            'period_start': period_start,
            'period_end': period_end,
        }

        serializer = WebhookStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        GET /api/webhooks/recent/
        20 derniers webhooks (pour affichage temps reel)
        """
        webhooks = self.get_queryset()[:20]
        serializer = self.get_serializer(webhooks, many=True)
        return Response(serializer.data)


class WebhookStateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les positions ouvertes via webhooks
    Endpoints:
    - GET /api/webhook-states/ : Liste des positions ouvertes
    - GET /api/webhook-states/{id}/ : Detail d'une position
    - GET /api/webhook-states/summary/ : Resume des positions
    """
    serializer_class = WebhookStateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['symbol', 'status', 'broker']
    ordering_fields = ['opened_at', 'updated_at']
    ordering = ['-opened_at']

    def get_queryset(self):
        """Filtre multi-tenant par user_id"""
        return WebhookState.objects.filter(
            user=self.request.user
        ).select_related('user', 'broker')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/webhook-states/summary/
        Resume des positions ouvertes

        Retourne:
        - Nombre de positions ouvertes
        - P&L non realise total
        - Liste des symboles actifs
        """
        # Positions ouvertes uniquement
        open_positions = self.get_queryset().filter(status='open')

        # Calcul P&L total depuis le champ maintenu par Terminal 3
        total_pnl = sum(
            (pos.unrealized_pnl or Decimal('0')) for pos in open_positions
        )

        # Symboles actifs
        active_symbols = list(
            open_positions.values_list('symbol', flat=True).distinct()
        )

        data = {
            'open_positions_count': open_positions.count(),
            'total_unrealized_pnl': float(total_pnl),
            'active_symbols': active_symbols,
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def open(self, request):
        """
        GET /api/webhook-states/open/
        Positions ouvertes uniquement
        """
        open_positions = self.get_queryset().filter(status='open')
        serializer = self.get_serializer(open_positions, many=True)
        return Response(serializer.data)
