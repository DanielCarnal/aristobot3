# -*- coding: utf-8 -*-
"""
Serializers pour Trading Manuel - Module 3
"""
from rest_framework import serializers
from .models import Trade


class TradeSerializer(serializers.ModelSerializer):
    """Serializer pour le modele Trade"""
    
    # Champs calcules en lecture seule
    display_fees = serializers.ReadOnlyField()
    profit_loss = serializers.ReadOnlyField()
    
    class Meta:
        model = Trade
        fields = [
            'id', 'user', 'broker', 'trade_type', 'symbol', 'side', 'order_type',
            'quantity', 'price', 'total_value', 'status', 'filled_quantity',
            'filled_price', 'fees', 'display_fees', 'exchange_order_id',
            'created_at', 'executed_at', 'error_message', 'notes', 'profit_loss'
        ]
        read_only_fields = [
            'id', 'user', 'broker', 'status', 'filled_quantity', 'filled_price',
            'fees', 'exchange_order_id', 'created_at', 'executed_at', 'error_message'
        ]


class TradeExecutionSerializer(serializers.Serializer):
    """Serializer pour l'execution d'un trade"""
    
    broker_id = serializers.IntegerField()
    symbol = serializers.CharField(max_length=20)
    side = serializers.ChoiceField(choices=['buy', 'sell'])
    order_type = serializers.ChoiceField(choices=['market', 'limit'])
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8)
    price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    total_value = serializers.DecimalField(max_digits=20, decimal_places=8)
    
    def validate(self, data):
        """Validation croisee des donnees"""
        if data['order_type'] == 'limit' and not data.get('price'):
            raise serializers.ValidationError("Le prix est requis pour un ordre limite")
        
        if data['quantity'] <= 0:
            raise serializers.ValidationError("La quantite doit etre positive")
            
        return data


class SymbolFilterSerializer(serializers.Serializer):
    """Serializer pour le filtrage des symboles"""
    
    broker_id = serializers.IntegerField()
    usdt = serializers.BooleanField(default=True)
    usdc = serializers.BooleanField(default=False)
    all = serializers.BooleanField(default=False)
    search = serializers.CharField(max_length=50, required=False, allow_blank=True)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=100, min_value=10, max_value=500)


class CalculateTradeSerializer(serializers.Serializer):
    """Serializer pour le calcul quantite <-> valeur"""
    
    broker_id = serializers.IntegerField()
    symbol = serializers.CharField(max_length=20)
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    total_value = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    
    def validate(self, data):
        """Validation: un seul des deux champs doit etre fourni"""
        quantity = data.get('quantity')
        total_value = data.get('total_value')
        
        if quantity and total_value:
            raise serializers.ValidationError("Fournir soit quantity soit total_value, pas les deux")
        
        if not quantity and not total_value:
            # Aucun des deux -> juste recuperer le prix
            pass
            
        return data


class ValidationTradeSerializer(serializers.Serializer):
    """Serializer pour la validation d'un trade avant execution"""
    
    broker_id = serializers.IntegerField()
    symbol = serializers.CharField(max_length=20)
    side = serializers.ChoiceField(choices=['buy', 'sell'])
    order_type = serializers.ChoiceField(choices=['market', 'limit'])
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8)
    price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)