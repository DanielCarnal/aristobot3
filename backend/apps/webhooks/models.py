# -*- coding: utf-8 -*-
"""
MODELS WEBHOOKS - Module 4

Stockage des webhooks TradingView et gestion des positions
"""
from django.db import models
from django.conf import settings
from decimal import Decimal


class Webhook(models.Model):
    """
    Historique complet des webhooks recus de TradingView
    Stockage dual : colonnes + raw_payload JSONB
    """
    STATUS_CHOICES = [
        ('received', 'Recu'),
        ('processing', 'En traitement'),
        ('processed', 'Traite'),
        ('error', 'Erreur'),
        ('miss', 'Manquant'),  # Detecte par coherence check
    ]

    ACTION_CHOICES = [
        ('PING', 'Ping (heartbeat)'),
        ('BuyMarket', 'Achat marche'),
        ('SellMarket', 'Vente marche'),
        ('BuyLimit', 'Achat limite'),
        ('SellLimit', 'Vente limite'),
        ('MAJ', 'Mise a jour SL/TP'),
        ('MISS', 'Signal manquant'),
    ]

    # === Multi-tenant ===
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    broker = models.ForeignKey(
        'brokers.Broker',
        on_delete=models.CASCADE,
        related_name='webhooks'
    )

    # === Donnees webhook ===
    symbol = models.CharField(max_length=50)
    exchange_name = models.CharField(max_length=50, blank=True)  # Binance, Bitget...
    interval = models.CharField(max_length=10)  # 1m, 5m, 15m...

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    # Prix
    prix = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    prix_sl = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    prix_tp = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    pour_cent = models.DecimalField(max_digits=5, decimal_places=2, default=100)  # % quantite

    # === Metadonnees ===
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    error_message = models.TextField(blank=True)

    # Timestamps
    bar_time = models.DateTimeField(null=True, blank=True)  # Timestamp bougie TradingView
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # === Stockage raw (JSONB) ===
    raw_payload = models.JSONField(default=dict)

    # === Resultats execution ===
    order_id = models.CharField(max_length=128, blank=True)  # ID ordre cree
    execution_result = models.JSONField(null=True, blank=True)  # Reponse Exchange

    class Meta:
        db_table = 'webhooks'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['broker', 'symbol']),
            models.Index(fields=['action', 'received_at']),
            models.Index(fields=['-received_at']),
        ]
        verbose_name = 'Webhook'
        verbose_name_plural = 'Webhooks'

    def __str__(self):
        return f"{self.symbol} {self.action} @ {self.received_at}"

    def is_actionable(self) -> bool:
        """Determine si le webhook necessite une action trading"""
        return self.action not in ['PING', 'MISS']

    def calculate_quantity(self, balance: Decimal) -> Decimal:
        """
        Calcule la quantite a executer selon PourCent et balance

        Args:
            balance: Balance disponible en USDT

        Returns:
            Quantite a executer
        """
        if not balance or balance <= 0:
            return Decimal('0')

        percentage = self.pour_cent / Decimal('100')
        amount = balance * percentage

        return amount


class WebhookState(models.Model):
    """
    Etat actuel des positions ouvertes via webhooks
    Une seule position active par (user, broker, symbol)
    """
    POSITION_CHOICES = [
        ('open', 'Ouverte'),
        ('closed', 'Fermee'),
    ]

    # === Multi-tenant ===
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhook_states'
    )
    broker = models.ForeignKey(
        'brokers.Broker',
        on_delete=models.CASCADE,
        related_name='webhook_states'
    )
    symbol = models.CharField(max_length=50)

    # === Position ===
    status = models.CharField(max_length=20, choices=POSITION_CHOICES, default='open')

    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    side = models.CharField(max_length=10)  # buy/sell

    # Stop Loss / Take Profit actuels
    current_sl = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    current_tp = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # IDs ordres SL/TP
    sl_order_id = models.CharField(max_length=128, blank=True)
    tp_order_id = models.CharField(max_length=128, blank=True)

    # === P&L ===
    unrealized_pnl = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    # === Timestamps ===
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # === Webhooks associes ===
    opening_webhook = models.ForeignKey(
        Webhook,
        on_delete=models.SET_NULL,
        null=True,
        related_name='opened_positions'
    )

    class Meta:
        db_table = 'webhook_states'
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['user', 'broker', 'symbol', 'status']),
            models.Index(fields=['status', '-opened_at']),
        ]
        unique_together = [['user', 'broker', 'symbol', 'status']]  # 1 position open max
        verbose_name = 'Etat Position Webhook'
        verbose_name_plural = 'Etats Positions Webhooks'

    def __str__(self):
        return f"{self.symbol} {self.side} x{self.quantity} ({self.status})"

    def calculate_pnl(self, current_price: Decimal) -> Decimal:
        """
        Calcule le P&L non realise

        Args:
            current_price: Prix actuel du marche

        Returns:
            P&L non realise
        """
        if self.side == 'buy':
            pnl = (current_price - self.entry_price) * self.quantity
        else:  # sell/short
            pnl = (self.entry_price - current_price) * self.quantity

        self.unrealized_pnl = pnl
        return pnl
