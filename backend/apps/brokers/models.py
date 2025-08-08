# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import ccxt

class Broker(models.Model):
    """Broker (Exchange) configure par utilisateur"""
    EXCHANGE_CHOICES = [
        ('binance', 'Binance'),
        ('binanceus', 'Binance US'),
        ('kraken', 'Kraken'),
        ('coinbase', 'Coinbase'),
        ('kucoin', 'KuCoin'),
        ('bitget', 'Bitget'),
        ('okx', 'OKX'),
        ('bybit', 'Bybit'),
        ('gateio', 'Gate.io'),
        ('mexc', 'MEXC'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='brokers'
    )
    exchange = models.CharField(
        max_length=50,
        choices=EXCHANGE_CHOICES
    )
    name = models.CharField(
        max_length=100,
        help_text="Nom personnalise (ex: Binance Principal)"
    )
    description = models.TextField(blank=True)
    
    api_key = models.TextField()  # Chiffre
    api_secret = models.TextField()  # Chiffre
    api_password = models.TextField(blank=True, null=True)  # Pour certains exchanges
    
    subaccount_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nom du sous-compte si applicable"
    )
    
    is_default = models.BooleanField(default=False)
    is_testnet = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Statistiques
    last_connection_test = models.DateTimeField(null=True, blank=True)
    last_connection_success = models.BooleanField(default=False)
    last_balance_update = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'brokers'
        unique_together = ['user', 'name']
        ordering = ['-is_default', 'name']
        verbose_name = 'Broker'
        verbose_name_plural = 'Brokers'
    
    def save(self, *args, **kwargs):
        # Chiffrer les cles API
        if self.api_key and not self.api_key.startswith('gAAAA'):
            self.api_key = self.encrypt_field(self.api_key)
        if self.api_secret and not self.api_secret.startswith('gAAAA'):
            self.api_secret = self.encrypt_field(self.api_secret)
        if self.api_password and not self.api_password.startswith('gAAAA'):
            self.api_password = self.encrypt_field(self.api_password)
        
        # S'assurer qu'il n'y a qu'un seul broker par defaut par user
        if self.is_default:
            Broker.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def encrypt_field(self, raw_value):
        """Chiffre un champ"""
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.encrypt(raw_value.encode()).decode()
    
    def decrypt_field(self, encrypted_value):
        """Dechiffre un champ"""
        if not encrypted_value or not encrypted_value.startswith('gAAAA'):
            return encrypted_value
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.decrypt(encrypted_value.encode()).decode()
    
    def get_ccxt_client(self):
        """Retourne une instance CCXT configuree pour ce broker"""
        exchange_class = getattr(ccxt, self.exchange)
        config = {
            'apiKey': self.decrypt_field(self.api_key),
            'secret': self.decrypt_field(self.api_secret),
            'enableRateLimit': True,
            'rateLimit': 2000,
            'options': {
                'defaultType': 'spot',  # spot, future, swap, option
            }
        }
        
        if self.api_password:
            config['password'] = self.decrypt_field(self.api_password)
        
        if self.is_testnet:
            config['options']['sandboxMode'] = True
            
        if self.subaccount_name:
            # Configuration specifique pour les sous-comptes selon l'exchange
            if self.exchange == 'binance':
                config['options']['defaultSubAccount'] = self.subaccount_name
            elif self.exchange == 'okx':
                config['headers'] = {'x-simulated-trading': '1'} if self.is_testnet else {}
                
        client = exchange_class(config)
        
        # Activer le mode sandbox si necessaire
        if self.is_testnet and hasattr(client, 'set_sandbox_mode'):
            client.set_sandbox_mode(True)
            
        return client
    
    def test_connection(self):
        """Teste la connexion au broker"""
        from django.utils import timezone
        try:
            client = self.get_ccxt_client()
            balance = client.fetch_balance()
            self.last_connection_test = timezone.now()
            self.last_connection_success = True
            self.last_balance_update = timezone.now()
            self.save()
            return True, balance
        except Exception as e:
            self.last_connection_test = timezone.now()
            self.last_connection_success = False
            self.save()
            return False, str(e)
    
    def __str__(self):
        return f"{self.name} ({self.exchange}) - {self.user.username}"


class ExchangeSymbol(models.Model):
    """Symboles disponibles par exchange (table partagee)"""
    exchange = models.CharField(
        max_length=50,
        db_index=True
    )
    symbol = models.CharField(
        max_length=50,
        help_text="Symbol unifie CCXT (ex: BTC/USDT)"
    )
    base = models.CharField(max_length=20)
    quote = models.CharField(max_length=20)
    
    # Informations du marche
    active = models.BooleanField(default=True)
    type = models.CharField(
        max_length=20,
        choices=[
            ('spot', 'Spot'),
            ('future', 'Future'),
            ('swap', 'Swap'),
            ('option', 'Option'),
        ],
        default='spot'
    )
    
    # Limites
    min_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    max_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    min_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    max_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    min_cost = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    
    # Precision
    amount_precision = models.IntegerField(null=True)
    price_precision = models.IntegerField(null=True)
    
    # Metadonnees
    raw_info = models.JSONField(default=dict, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exchange_symbols'
        unique_together = ['exchange', 'symbol', 'type']
        ordering = ['exchange', 'symbol']
        indexes = [
            models.Index(fields=['exchange', 'active']),
            models.Index(fields=['symbol']),
        ]
    
    def __str__(self):
        return f"{self.exchange}:{self.symbol}"