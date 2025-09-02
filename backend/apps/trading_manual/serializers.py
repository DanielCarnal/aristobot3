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
    order_type = serializers.ChoiceField(choices=[
        'market', 'limit', 'stop_loss', 'take_profit', 'sl_tp_combo', 'stop_limit'
    ])
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8)
    price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    total_value = serializers.DecimalField(max_digits=20, decimal_places=8)
    
    # Nouveaux champs pour ordres avances
    stop_loss_price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    take_profit_price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    trigger_price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    
    def validate(self, data):
        """Validation croisee des donnees"""
        order_type = data['order_type']
        
        # Validations par type d'ordre
        if order_type == 'limit' and not data.get('price'):
            raise serializers.ValidationError("Le prix est requis pour un ordre limite")
        
        if order_type == 'stop_loss' and not data.get('stop_loss_price'):
            raise serializers.ValidationError("Le prix stop loss est requis")
        
        if order_type == 'take_profit' and not data.get('take_profit_price'):
            raise serializers.ValidationError("Le prix take profit est requis")
        
        if order_type == 'sl_tp_combo':
            if not data.get('stop_loss_price'):
                raise serializers.ValidationError("Le prix stop loss est requis pour le combo SL+TP")
            if not data.get('take_profit_price'):
                raise serializers.ValidationError("Le prix take profit est requis pour le combo SL+TP")
        
        if order_type == 'stop_limit':
            if not data.get('price'):
                raise serializers.ValidationError("Le prix limite est requis pour un stop limit")
            if not data.get('trigger_price'):
                raise serializers.ValidationError("Le prix de declenchement est requis pour un stop limit")
        
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
    order_type = serializers.ChoiceField(choices=[
        'market', 'limit', 'stop_loss', 'take_profit', 'sl_tp_combo', 'stop_limit'
    ])
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8)
    price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    
    # Nouveaux champs pour ordres avances
    stop_loss_price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    take_profit_price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    trigger_price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    
    def validate(self, data):
        """Validation croisee des donnees pour tous types d'ordres"""
        order_type = data['order_type']
        
        # Validations par type d'ordre
        if order_type == 'limit' and not data.get('price'):
            raise serializers.ValidationError("Le prix est requis pour un ordre limite")
        
        if order_type == 'stop_loss' and not data.get('stop_loss_price'):
            raise serializers.ValidationError("Le prix stop loss est requis")
        
        if order_type == 'take_profit' and not data.get('take_profit_price'):
            raise serializers.ValidationError("Le prix take profit est requis")
        
        if order_type == 'sl_tp_combo':
            if not data.get('stop_loss_price'):
                raise serializers.ValidationError("Le prix stop loss est requis pour le combo SL+TP")
            if not data.get('take_profit_price'):
                raise serializers.ValidationError("Le prix take profit est requis pour le combo SL+TP")
        
        if order_type == 'stop_limit':
            if not data.get('price'):
                raise serializers.ValidationError("Le prix limite est requis pour un stop limit")
            if not data.get('trigger_price'):
                raise serializers.ValidationError("Le prix de declenchement est requis pour un stop limit")
        
        if data['quantity'] <= 0:
            raise serializers.ValidationError("La quantite doit etre positive")
            
        return data