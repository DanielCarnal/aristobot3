# -*- coding: utf-8 -*-
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from loguru import logger as loguru_logger
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Position, HeartbeatStatus, CandleHeartbeat
from .serializers import PositionSerializer, CandleHeartbeatSerializer, HeartbeatStatusSerializer

User = get_user_model()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

class PositionViewSet(viewsets.ModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Position.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HeartbeatViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour les donnees Heartbeat et historique des signaux"""
    permission_classes = []  # Pas d'auth pour consulter les données publiques Heartbeat
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Retourne le statut actuel du Heartbeat"""
        try:
            heartbeat_status = HeartbeatStatus.objects.get(id=1)
            serializer = HeartbeatStatusSerializer(heartbeat_status)
            return Response(serializer.data)
        except HeartbeatStatus.DoesNotExist:
            return Response({
                'error': 'Heartbeat non configure'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def signals(self, request):
        """Retourne l'historique des signaux avec pagination et filtres"""
        queryset = CandleHeartbeat.objects.all()
        
        # Filtres
        signal_type = request.query_params.get('signal_type')
        symbol = request.query_params.get('symbol', 'BTCUSDT')
        hours_back = request.query_params.get('hours_back', 24)
        
        # Filtrage par timeframe
        if signal_type:
            queryset = queryset.filter(signal_type=signal_type)
        
        # Filtrage par symbole
        queryset = queryset.filter(symbol=symbol)
        
        # Filtrage temporel (dernieres X heures)
        try:
            hours_back = int(hours_back)
            time_threshold = timezone.now() - timedelta(hours=hours_back)
            queryset = queryset.filter(dhm_candle__gte=time_threshold)
        except ValueError:
            pass
        
        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = CandleHeartbeatSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = CandleHeartbeatSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Retourne les 60 derniers signaux pour l'interface"""
        limit = int(request.query_params.get('limit', 60))
        
        queryset = CandleHeartbeat.objects.select_related('heartbeat_status').order_by('-dhm_reception')[:limit]
        serializer = CandleHeartbeatSerializer(queryset, many=True)
        
        return Response({
            'signals': serializer.data,
            'count': queryset.count(),
            'timestamp': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['get'])
    def timeframes(self, request):
        """Retourne les signaux groupes par timeframe"""
        from django.db.models import Count
        
        hours_back = int(request.query_params.get('hours_back', 1))
        time_threshold = timezone.now() - timedelta(hours=hours_back)
        
        # Compter les signaux par timeframe
        timeframes = CandleHeartbeat.objects.filter(
            dhm_candle__gte=time_threshold
        ).values('signal_type').annotate(
            count=Count('id')
        ).order_by('signal_type')
        
        # Recuperer le dernier signal de chaque timeframe
        latest_signals = {}
        for tf in ['1m', '3m', '5m', '15m', '1h', '4h']:
            try:
                latest = CandleHeartbeat.objects.filter(
                    signal_type=tf,
                    dhm_candle__gte=time_threshold
                ).first()
                if latest:
                    latest_signals[tf] = CandleHeartbeatSerializer(latest).data
            except:
                pass
        
        return Response({
            'timeframe_counts': list(timeframes),
            'latest_signals': latest_signals,
            'period_hours': hours_back
        })


# Vue publique pour les données historiques (sans auth)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

@method_decorator(csrf_exempt, name='dispatch')
class HeartbeatHistoryView(View):
    """API publique pour charger l'historique Heartbeat"""
    
    def get(self, request):
        signal_type = request.GET.get('signal_type')
        limit = int(request.GET.get('limit', 60))
        
        queryset = CandleHeartbeat.objects.all()
        
        if signal_type:
            queryset = queryset.filter(signal_type=signal_type)
            
        # Prendre les derniers signaux
        signals = queryset.order_by('-dhm_reception')[:limit]
        
        data = []
        for signal in signals:
            data.append({
                'id': signal.id,
                'dhm_candle': signal.dhm_candle.isoformat() if signal.dhm_candle else None,
                'signal_type': signal.signal_type,
                'symbol': signal.symbol,
                'close_price': float(signal.close_price),
                'timestamp': signal.dhm_reception.isoformat()
            })
        
        return JsonResponse({
            'results': data,
            'count': len(data)
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def frontend_log_view(request):
    """
    Endpoint async pour recevoir les logs du frontend Vue.js.
    Ecrit dans le fichier de log terminal1 via Loguru.
    """
    data = request.data

    level = data.get('level', 'info').lower()
    message = data.get('message', '')
    component = data.get('component', 'unknown')
    timestamp = data.get('timestamp', '')
    log_data = data.get('data', {})

    # Filtrer les niveaux valides
    valid_levels = {'debug', 'info', 'warning', 'warn', 'error'}
    if level not in valid_levels:
        level = 'info'
    # Normaliser 'warn' vers 'warning' pour loguru
    if level == 'warn':
        level = 'warning'

    bound = loguru_logger.bind(
        terminal_name="terminal1_frontend",
        component=component,
        frontend_timestamp=timestamp,
        **{k: str(v) for k, v in log_data.items()} if log_data else {}
    )
    getattr(bound, level)(message)

    return Response({'status': 'ok'}, status=200)