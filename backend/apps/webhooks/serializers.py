# -*- coding: utf-8 -*-
"""
MODULE 4 - WEBHOOKS SERIALIZERS
Serializers DRF pour les APIs REST webhooks
"""
from rest_framework import serializers
from .models import Webhook, WebhookState


class WebhookSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des webhooks"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    broker_name = serializers.CharField(source='broker.name', read_only=True)
    exchange_name = serializers.CharField(source='broker.exchange', read_only=True)

    class Meta:
        model = Webhook
        fields = [
            'id',
            'user',
            'user_username',
            'broker',
            'broker_name',
            'exchange_name',
            'symbol',
            'interval',
            'action',
            'prix',
            'prix_sl',
            'prix_tp',
            'pour_cent',
            'status',
            'order_id',
            'error_message',
            'raw_payload',
            'received_at',
            'processed_at',
        ]
        read_only_fields = ['id', 'received_at', 'processed_at']


class WebhookStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques webhooks"""
    total_webhooks = serializers.IntegerField()
    received = serializers.IntegerField()
    processing = serializers.IntegerField()
    processed = serializers.IntegerField()
    errors = serializers.IntegerField()
    missed = serializers.IntegerField()

    # Statistiques par action
    actions_breakdown = serializers.DictField()

    # Taux de succes
    success_rate = serializers.FloatField()

    # Derniere activite
    last_webhook_time = serializers.DateTimeField(allow_null=True)

    # Periode
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()


class WebhookStateSerializer(serializers.ModelSerializer):
    """Serializer pour les positions ouvertes via webhooks"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    broker_name = serializers.CharField(source='broker.name', read_only=True)
    exchange_name = serializers.CharField(source='broker.exchange', read_only=True)

    # Calcul P&L non realise
    unrealized_pnl = serializers.SerializerMethodField()

    class Meta:
        model = WebhookState
        fields = [
            'id',
            'user',
            'user_username',
            'broker',
            'broker_name',
            'exchange_name',
            'symbol',
            'side',
            'quantity',
            'entry_price',
            'current_sl',
            'current_tp',
            'sl_order_id',
            'tp_order_id',
            'unrealized_pnl',
            'realized_pnl',
            'status',
            'opened_at',
            'closed_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'opened_at', 'updated_at']

    def get_unrealized_pnl(self, obj):
        """Retourne le P&L non realise stocke"""
        return float(obj.unrealized_pnl) if obj.unrealized_pnl else 0.0
