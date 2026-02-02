# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Broker, ExchangeSymbol
import ccxt

class BrokerSerializer(serializers.ModelSerializer):
    """Serializer pour les brokers"""
    last_balance = serializers.SerializerMethodField()
    available_symbols_count = serializers.SerializerMethodField()
    has_api_key = serializers.SerializerMethodField()
    has_api_secret = serializers.SerializerMethodField()
    has_api_password = serializers.SerializerMethodField()

    class Meta:
        model = Broker
        fields = [
            'id', 'exchange', 'name', 'description',
            'api_key', 'api_secret', 'api_password',
            'subaccount_name', 'is_default', 'is_testnet', 'is_active',
            'type_de_trading',
            'last_connection_test', 'last_connection_success',
            'last_balance_update', 'last_balance',
            'available_symbols_count',
            'has_api_key', 'has_api_secret', 'has_api_password',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True, 'required': False},
            'api_secret': {'write_only': True, 'required': False},
            'api_password': {'write_only': True, 'required': False},
        }
    
    def get_has_api_key(self, obj):
        return bool(obj.api_key)

    def get_has_api_secret(self, obj):
        return bool(obj.api_secret)

    def get_has_api_password(self, obj):
        return bool(obj.api_password)

    def get_last_balance(self, obj):
        """Retourne le dernier balance connu (sera implemente plus tard)"""
        return None
    
    def get_available_symbols_count(self, obj):
        """Compte les symboles disponibles pour cet exchange"""
        return ExchangeSymbol.objects.filter(
            exchange=obj.exchange,
            active=True
        ).count()
    
    def validate_exchange(self, value):
        """Verifie que l'exchange est supporte par CCXT"""
        if value not in ccxt.exchanges:
            raise serializers.ValidationError(
                f"L'exchange '{value}' n'est pas supporte"
            )
        return value
    
    def create(self, validated_data):
        if not validated_data.get('api_key'):
            raise serializers.ValidationError({'api_key': 'La cle API est requise lors de la creation.'})
        if not validated_data.get('api_secret'):
            raise serializers.ValidationError({'api_secret': 'Le secret API est requis lors de la creation.'})
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ExchangeSymbolSerializer(serializers.ModelSerializer):
    """Serializer pour les symboles d'exchange"""
    class Meta:
        model = ExchangeSymbol
        fields = '__all__'


class TestConnectionSerializer(serializers.Serializer):
    """Serializer pour tester une connexion"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    balance = serializers.DictField(required=False)