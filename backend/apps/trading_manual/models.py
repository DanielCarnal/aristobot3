# -*- coding: utf-8 -*-
"""
Modeles Trading Manuel - Module 3
"""
from django.db import models
from django.conf import settings
from decimal import Decimal


class Trade(models.Model):
    """
    Modele Trade pour enregistrer tous les trades manuels
    Multi-tenant strict avec isolation par user
    """
    
    TRADE_TYPES = [
        ('manual', 'Trading Manuel'),
        ('webhook', 'Webhook TradingView'),
        ('strategy', 'Strategie Automatique'),
        ('backtest', 'Backtest'),
    ]
    
    SIDE_CHOICES = [
        ('buy', 'Achat'),
        ('sell', 'Vente'),
    ]
    
    ORDER_TYPES = [
        ('market', 'Marche'),
        ('limit', 'Limite'),
        ('stop_loss', 'Stop Loss'),
        ('take_profit', 'Take Profit'),
        ('sl_tp_combo', 'Stop Loss + Take Profit'),
        ('stop_limit', 'Stop Limite'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('filled', 'Execute'),
        ('cancelled', 'Annule'),
        ('failed', 'Echec'),
    ]
    
    # Identification
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    broker = models.ForeignKey('brokers.Broker', on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=20, choices=TRADE_TYPES, default='manual')
    
    # Details de l'ordre
    symbol = models.CharField(max_length=20)  # Ex: "BTC/USDT"
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    order_type = models.CharField(max_length=15, choices=ORDER_TYPES)
    
    # Quantites et prix
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    total_value = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Prix pour ordres avances (SL/TP)
    stop_loss_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    trigger_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  # Pour stop orders
    
    # Resultats
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    filled_quantity = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    filled_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    fees = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Identifiants exchange
    exchange_order_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadonnees
    error_message = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'broker', 'symbol']),
            models.Index(fields=['user', 'trade_type', 'status']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"{self.side.upper()} {self.quantity} {self.symbol} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Validation avant sauvegarde"""
        # Calculer total_value si pas fourni
        if not self.total_value and self.quantity and self.price:
            self.total_value = self.quantity * self.price
            
        super().save(*args, **kwargs)
    
    @property
    def profit_loss(self):
        """Calcule le P&L si le trade est execute"""
        if self.status == 'filled' and self.filled_price and self.filled_quantity:
            if self.side == 'buy':
                # Pour un achat, on calcule vs prix de vente futur (pas implemente ici)
                return None
            else:
                # Pour une vente, on calcule vs prix d'achat (necessite logique plus complexe)
                return None
        return None
    
    @property
    def display_fees(self):
        """Affichage formate des frais"""
        if self.fees:
            return f"{self.fees:.8f}"
        return "0.00000000"