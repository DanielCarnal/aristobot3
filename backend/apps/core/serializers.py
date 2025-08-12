# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Position, HeartbeatStatus, CandleHeartbeat


class PositionSerializer(serializers.ModelSerializer):
    """Serializer pour les positions de trading"""
    
    class Meta:
        model = Position
        fields = [
            'id', 'symbol', 'side', 'quantity', 'entry_price', 
            'current_price', 'stop_loss', 'take_profit', 
            'unrealized_pnl', 'realized_pnl', 'status',
            'opened_at', 'closed_at', 'updated_at'
        ]
        read_only_fields = ['id', 'unrealized_pnl', 'realized_pnl', 
                           'opened_at', 'closed_at', 'updated_at']


class HeartbeatStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut du service Heartbeat"""
    
    class Meta:
        model = HeartbeatStatus
        fields = [
            'id', 'is_connected', 'last_heartbeat', 'last_error',
            'symbols_monitored', 'last_application_start', 
            'last_application_stop', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_connected', 'last_heartbeat', 'last_error',
            'symbols_monitored', 'last_application_start', 
            'last_application_stop', 'created_at', 'updated_at'
        ]


class CandleHeartbeatSerializer(serializers.ModelSerializer):
    """Serializer pour les signaux Heartbeat individuels"""
    
    # Champs calculés
    is_recent = serializers.SerializerMethodField()
    price_change = serializers.SerializerMethodField()
    
    class Meta:
        model = CandleHeartbeat
        fields = [
            'id', 'dhm_reception', 'dhm_candle', 'signal_type',
            'symbol', 'open_price', 'high_price', 'low_price', 
            'close_price', 'volume', 'created_at',
            'is_recent', 'price_change'
        ]
        read_only_fields = [
            'id', 'dhm_reception', 'dhm_candle', 'signal_type',
            'symbol', 'open_price', 'high_price', 'low_price', 
            'close_price', 'volume', 'created_at'
        ]
    
    def get_is_recent(self, obj):
        """Détermine si le signal est récent (moins de 5 minutes)"""
        from django.utils import timezone
        from datetime import timedelta
        
        threshold = timezone.now() - timedelta(minutes=5)
        return obj.dhm_reception >= threshold
    
    def get_price_change(self, obj):
        """Calcule la variation de prix (close - open)"""
        try:
            return float(obj.close_price - obj.open_price)
        except:
            return 0.0


class CandleHeartbeatMinimalSerializer(serializers.ModelSerializer):
    """Version minimale pour l'interface en temps réel"""
    
    class Meta:
        model = CandleHeartbeat
        fields = [
            'id', 'dhm_candle', 'signal_type', 'symbol', 
            'close_price', 'volume'
        ]