# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Strategy


class StrategySerializer(serializers.ModelSerializer):
    """Serializer CRUD pour les strategies utilisateur."""

    class Meta:
        model = Strategy
        fields = ['id', 'name', 'description', 'code', 'timeframe', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class StrategyValidationSerializer(serializers.Serializer):
    """Serializer pour la validation syntaxique du code d'une strategie."""
    code = serializers.CharField()
