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
        ('terminal7', 'Terminal 7 (Auto-detection)'),
    ]
    
    SOURCE_CHOICES = [
        ('manual', 'Saisie Manuelle'),
        ('trading_manual', 'Trading Manuel'),
        ('webhook', 'Webhook'),
        ('strategy', 'Strategie'),
        ('terminal7', 'Terminal 7'),
        ('backtest', 'Backtest'),
    ]
    
    PNL_CALCULATION_METHODS = [
        ('none', 'Aucun'),
        ('manual', 'Manuel'),
        ('price_averaging', 'Prix Moyen'),
        ('fifo', 'FIFO'),
        ('user_choice', 'Choix Utilisateur'),
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
        ('completed', 'Termine'),  # Terminal 7
    ]
    
    # Identification
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    broker = models.ForeignKey('brokers.Broker', on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=20, choices=TRADE_TYPES, default='manual')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    
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
    
    # === CHAMPS TERMINAL 7 ===
    # Statut ordre sur l'exchange
    exchange_order_status = models.CharField(max_length=50, null=True, blank=True)
    
    # ID client ordre pour tracking
    exchange_client_order_id = models.CharField(max_length=100, null=True, blank=True)
    
    # P&L calcule par Terminal 7
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    pnl_calculation_method = models.CharField(
        max_length=20, 
        choices=PNL_CALCULATION_METHODS, 
        default='none'
    )
    
    # Prix moyen d'achat pour calcul P&L
    avg_buy_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # === CHAMPS EXCHANGE COMPLETS (TERMINAL 5 UNIFIED) ===
    
    # 1. Traçabilite source ordre
    ordre_existant = models.CharField(max_length=100, null=True, blank=True)
    # "By Trading Manuel", "By strategie {nom}", "By Webhook", "By Terminal7 detection"
    
    # 2. Métadonnées client/source 
    ENTER_POINT_CHOICES = [
        ('WEB', 'Web Client'),
        ('APP', 'App Client'), 
        ('API', 'API Client'),
        ('SYS', 'System Client'),
        ('ANDROID', 'Android Client'),
        ('IOS', 'iOS Client'),
    ]
    enter_point_source = models.CharField(max_length=20, choices=ENTER_POINT_CHOICES, null=True, blank=True)
    
    ORDER_SOURCE_CHOICES = [
        ('normal', 'Normal Order'),
        ('market', 'Market Order'),
        ('spot_trader_buy', 'Elite Spot Trade Buy'),
        ('spot_follower_buy', 'Copy Trade Buy'),
        ('spot_trader_sell', 'Elite Spot Trade Sell'),
        ('spot_follower_sell', 'Copy Trade Sell'),
        ('strategy_oco_limit', 'OCO Orders'),
    ]
    order_source = models.CharField(max_length=50, choices=ORDER_SOURCE_CHOICES, null=True, blank=True)
    
    # 3. Volumes detailles  
    quote_volume = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  # Volume quote coin
    amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  # Montant total trading
    
    # 4. Timestamps Exchange
    update_time = models.DateTimeField(null=True, blank=True)  # uTime Exchange
    
    # 5. Gestion annulation
    CANCEL_REASON_CHOICES = [
        ('normal_cancel', 'Normal Cancel'),
        ('stp_cancel', 'Cancelled by STP'),
    ]
    cancel_reason = models.CharField(max_length=50, choices=CANCEL_REASON_CHOICES, null=True, blank=True)
    
    # 6. TP/SL avances Bitget
    preset_take_profit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    execute_take_profit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  
    preset_stop_loss_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    execute_stop_loss_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    TPSL_TYPE_CHOICES = [
        ('normal', 'Spot Order'),
        ('tpsl', 'Spot TPSL Order'),
    ]
    tpsl_type = models.CharField(max_length=20, choices=TPSL_TYPE_CHOICES, null=True, blank=True)
    
    # 7. Execution details (Fills API)
    trade_id = models.CharField(max_length=100, null=True, blank=True)  # tradeId unique
    
    TRADE_SCOPE_CHOICES = [
        ('taker', 'Taker'),
        ('maker', 'Maker'),
    ]
    trade_scope = models.CharField(max_length=10, choices=TRADE_SCOPE_CHOICES, null=True, blank=True)
    
    # 8. Options trading avancees
    STP_MODE_CHOICES = [
        ('none', 'No STP'),
        ('cancel_taker', 'Cancel Taker'),
        ('cancel_maker', 'Cancel Maker'), 
        ('cancel_both', 'Cancel Both'),
    ]
    stp_mode = models.CharField(max_length=20, choices=STP_MODE_CHOICES, null=True, blank=True)
    
    FORCE_CHOICES = [
        ('GTC', 'Good Till Cancel'),
        ('FOK', 'Fill or Kill'),
        ('IOC', 'Immediate or Cancel'),
        ('post_only', 'Post Only'),
    ]
    force = models.CharField(max_length=10, choices=FORCE_CHOICES, null=True, blank=True)
    
    # 9. User ID Exchange pour validation
    exchange_user_id = models.CharField(max_length=50, null=True, blank=True)
    
    # 10. Donnees JSON completes
    fee_detail = models.JSONField(null=True, blank=True)  # Frais detailles Exchange
    exchange_raw_data = models.JSONField(null=True, blank=True)  # Donnees brutes DEBUG
    
    # Quantite de position apres ce trade
    position_quantity_after = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Donnees brutes de l'exchange pour audit
    raw_order_data = models.JSONField(null=True, blank=True)
    
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
            # Index Terminal 7
            models.Index(fields=['source']),
            # Index optimisé pour TradeViewSet filtrage broker
            models.Index(fields=['user', 'broker', '-created_at']),
            models.Index(fields=['exchange_order_id']),
            models.Index(fields=['executed_at']),
            models.Index(fields=['user', 'broker', 'symbol', 'side']),  # Pour position tracking
            # Index nouveaux champs
            models.Index(fields=['ordre_existant']),
            models.Index(fields=['enter_point_source']),
            models.Index(fields=['trade_id']),  # Fills API
            models.Index(fields=['exchange_user_id']),
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