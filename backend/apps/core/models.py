# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings

class HeartbeatStatus(models.Model):
    """Etat du service Heartbeat (table systeme)"""
    is_connected = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    symbols_monitored = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'heartbeat_status'
        verbose_name = 'Etat du Heartbeat'
        verbose_name_plural = 'Etats du Heartbeat'
    
    def __str__(self):
        status = "Connecte" if self.is_connected else "Deconnecte"
        return f"Heartbeat: {status}"


class Position(models.Model):
    """Position ouverte pour un utilisateur"""
    STATUS_CHOICES = [
        ('open', 'Ouverte'),
        ('closing', 'En cours de fermeture'),
        ('closed', 'Fermee'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='positions'
    )
    broker = models.ForeignKey(
        'brokers.Broker',
        on_delete=models.CASCADE
    )
    # TODO: Module 5 - Ajouter la reference a Strategy
    # strategy = models.ForeignKey(
    #     'strategies.Strategy',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )
    
    symbol = models.CharField(max_length=50)
    side = models.CharField(
        max_length=10,
        choices=[('buy', 'Achat'), ('sell', 'Vente')]
    )
    
    # Quantites et prix
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    
    # Stop Loss et Take Profit
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    
    # P&L
    unrealized_pnl = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'positions'
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['broker', 'symbol']),
        ]
    
    def calculate_pnl(self, current_price=None):
        """Calcule le P&L non realise"""
        if current_price:
            self.current_price = current_price
        
        if self.current_price and self.entry_price:
            if self.side == 'buy':
                self.unrealized_pnl = (self.current_price - self.entry_price) * self.quantity
            else:  # sell/short
                self.unrealized_pnl = (self.entry_price - self.current_price) * self.quantity
        
        return self.unrealized_pnl
    
    def __str__(self):
        return f"{self.symbol} {self.side} x{self.quantity} @ {self.entry_price}"