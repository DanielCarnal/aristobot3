# PLAN D'IMPLÉMENTATION ARISTOBOT3

## 📊 ÉTAT ACTUEL DU PROJET

### ✅ Ce qui existe et fonctionne
- **Structure des dossiers** : Complète (10 apps Django créées)
- **Configuration Django** : Base configurée avec channels
- **Service Heartbeat** : WebSocket Binance basique fonctionnel
- **Frontend Vue Router** : Configuré avec 8 vues (placeholders)
- **Design System** : Tokens et couleurs définis

### ❌ Ce qui est VIDE ou NON FONCTIONNEL
- **Tous les models.py** : Vides (aucun modèle défini)
- **Toutes les APIs** : Vides (aucun endpoint)
- **Base de données** : Aucune migration créée
- **Authentification** : Non configurée
- **Trading Engine** : Squelette uniquement
- **Frontend** : Vues placeholders uniquement

## 🎯 DÉCISIONS TECHNIQUES VALIDÉES

### Base de données
- **PostgreSQL uniquement** (pas de MongoDB)
- **Multi-tenant strict** : Filtrage par `user_id` obligatoire
- **Decimal Python** pour tous les montants/prix
- **UTC en DB**, affichage selon préférence utilisateur

### Architecture
- **CCXT** pour multi-exchange (version gratuite, REST API)
- **Singleton pattern** pour instances CCXT (une par exchange/user)
- **asyncio** pour parallélisme (pas de Celery)
- **Django Channels** pour WebSocket
- **Heartbeat** : WebSocket natif Binance (indépendant de CCXT)

### Développement
- **Mode DEBUG** : `DEBUG_ARISTOBOT=True` -> Autorise user "dev" sans login
- **Mode TESTNET** : Global avec status bar inversée
- **Historique complet** : Toutes les tentatives de trades
- **Chiffrement** : Django SECRET_KEY pour API keys

### Frontend
- **Vue 3 Composition API** uniquement
- **Pinia** pour l'état global
- **LocalStorage** pour préférences UI
- **Dark mode** obligatoire avec couleurs néon

---

## 📦 MODULE 1 : USER ACCOUNT & BROKERS

### Objectifs
1. Créer le système d'authentification multi-tenant
2. Gérer les brokers (exchanges) avec CCXT
3. Implémenter le mode DEBUG avec user "dev"
4. Créer la table partagée des symboles
5. Frontend de gestion des comptes et brokers

### ÉTAPE 1.1 : Modèles de base

#### Fichier : `backend/apps/core/models.py`
```python
from django.db import models
from django.conf import settings

class HeartbeatStatus(models.Model):
    """État du service Heartbeat (table système)"""
    is_connected = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    symbols_monitored = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'heartbeat_status'
        verbose_name = 'État du Heartbeat'
        verbose_name_plural = 'États du Heartbeat'
    
    def __str__(self):
        status = "Connecté" if self.is_connected else "Déconnecté"
        return f"Heartbeat: {status}"


class Position(models.Model):
    """Position ouverte pour un utilisateur"""
    STATUS_CHOICES = [
        ('open', 'Ouverte'),
        ('closing', 'En cours de fermeture'),
        ('closed', 'Fermée'),
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
    # TODO: Module 5 - Ajouter la référence à Strategy
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
    
    # Quantités et prix
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
        """Calcule le P&L non réalisé"""
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
```

#### Fichier : `backend/apps/accounts/models.py`
```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings
import base64

class User(AbstractUser):
    """Utilisateur étendu pour Aristobot3"""
    default_broker = models.ForeignKey(
        'brokers.Broker', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='default_for_users'
    )
    
    # Configuration IA
    ai_provider = models.CharField(
        max_length=20,
        choices=[
            ('openrouter', 'OpenRouter'),
            ('ollama', 'Ollama'),
            ('none', 'Aucun')
        ],
        default='none'
    )
    ai_enabled = models.BooleanField(default=False)
    ai_api_key = models.TextField(blank=True, null=True)  # Sera chiffré
    ai_endpoint_url = models.URLField(
        default='http://localhost:11434',
        blank=True
    )
    
    # Préférences d'affichage
    theme = models.CharField(
        max_length=10,
        choices=[
            ('dark', 'Sombre'),
            ('light', 'Clair'),
        ],
        default='dark'
    )
    display_timezone = models.CharField(
        max_length=50,
        choices=[
            ('UTC', 'UTC'),
            ('local', 'Fuseau horaire local'),
        ],
        default='local'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Chiffrer l'API key avant sauvegarde
        if self.ai_api_key and not self.ai_api_key.startswith('gAAAA'):
            self.ai_api_key = self.encrypt_api_key(self.ai_api_key)
        super().save(*args, **kwargs)
    
    def encrypt_api_key(self, raw_key):
        """Chiffre une clé API"""
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.encrypt(raw_key.encode()).decode()
    
    def decrypt_api_key(self):
        """Déchiffre la clé API"""
        if not self.ai_api_key or not self.ai_api_key.startswith('gAAAA'):
            return self.ai_api_key
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.decrypt(self.ai_api_key.encode()).decode()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
```

#### Fichier : `backend/apps/brokers/models.py`
```python
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import ccxt

class Broker(models.Model):
    """Broker (Exchange) configuré par utilisateur"""
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
        help_text="Nom personnalisé (ex: Binance Principal)"
    )
    description = models.TextField(blank=True)
    
    api_key = models.TextField()  # Chiffré
    api_secret = models.TextField()  # Chiffré
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
        # Chiffrer les clés API
        if self.api_key and not self.api_key.startswith('gAAAA'):
            self.api_key = self.encrypt_field(self.api_key)
        if self.api_secret and not self.api_secret.startswith('gAAAA'):
            self.api_secret = self.encrypt_field(self.api_secret)
        if self.api_password and not self.api_password.startswith('gAAAA'):
            self.api_password = self.encrypt_field(self.api_password)
        
        # S'assurer qu'il n'y a qu'un seul broker par défaut par user
        if self.is_default:
            Broker.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def encrypt_field(self, raw_value):
        """Chiffre un champ"""
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.encrypt(raw_value.encode()).decode()
    
    def decrypt_field(self, encrypted_value):
        """Déchiffre un champ"""
        if not encrypted_value or not encrypted_value.startswith('gAAAA'):
            return encrypted_value
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.decrypt(encrypted_value.encode()).decode()
    
    def get_ccxt_client(self):
        """Retourne une instance CCXT configurée pour ce broker"""
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
            # Configuration spécifique pour les sous-comptes selon l'exchange
            if self.exchange == 'binance':
                config['options']['defaultSubAccount'] = self.subaccount_name
            elif self.exchange == 'okx':
                config['headers'] = {'x-simulated-trading': '1'} if self.is_testnet else {}
                
        client = exchange_class(config)
        
        # Activer le mode sandbox si nécessaire
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
    """Symboles disponibles par exchange (table partagée)"""
    exchange = models.CharField(
        max_length=50,
        db_index=True
    )
    symbol = models.CharField(
        max_length=50,
        help_text="Symbol unifié CCXT (ex: BTC/USDT)"
    )
    base = models.CharField(max_length=20)
    quote = models.CharField(max_length=20)
    
    # Informations du marché
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
    
    # Précision
    amount_precision = models.IntegerField(null=True)
    price_precision = models.IntegerField(null=True)
    
    # Métadonnées
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
```

### ÉTAPE 1.2 : Migrations et configuration Django

#### Fichier : `backend/aristobot/settings.py` (modifications)
```python
# Ajouter après les imports existants
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuration DEBUG
DEBUG = os.getenv('DEBUG_ARISTOBOT', 'False') == 'True'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Ajouter dans INSTALLED_APPS
INSTALLED_APPS = [
    # ... apps Django par défaut ...
    'rest_framework',
    'corsheaders',
    'channels',
    # Nos apps
    'apps.accounts',
    'apps.brokers',
    'apps.core',
    # ... autres apps ...
]

# Configuration DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vue dev server
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# Configuration spécifique au mode DEBUG
if DEBUG:
    # Auto-login pour user "dev"
    AUTHENTICATION_BACKENDS = [
        'apps.accounts.backends.DevModeBackend',  # Notre backend custom
        'django.contrib.auth.backends.ModelBackend',  # Backend normal
    ]
```

#### Fichier : `backend/apps/accounts/backends.py`
```python
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class DevModeBackend(BaseBackend):
    """
    Backend d'authentification pour le mode développement.
    Connecte automatiquement l'utilisateur 'dev' si DEBUG_ARISTOBOT=True
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if settings.DEBUG and not username:
            # En mode DEBUG, retourner automatiquement l'user dev
            try:
                return User.objects.get(username='dev')
            except User.DoesNotExist:
                return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

### ÉTAPE 1.3 : Services Core (CCXT Singleton et mise à jour des symboles)

#### Fichier : `backend/apps/core/services/__init__.py`
```python
from .ccxt_service import ccxt_service
from .symbol_updater import SymbolUpdaterService

__all__ = ['ccxt_service', 'SymbolUpdaterService']
```

#### Fichier : `backend/apps/core/services/ccxt_service.py`
```python
import ccxt
from typing import Dict, Any
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class CCXTService:
    """
    Service singleton pour gérer les instances CCXT.
    Une seule instance par exchange/user pour éviter les rate limits.
    """
    _instance = None
    _exchanges: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_exchange(self, broker):
        """
        Retourne une instance CCXT pour un broker donné.
        Utilise le cache pour réutiliser les instances.
        """
        cache_key = f"ccxt_{broker.user_id}_{broker.exchange}_{broker.id}"
        
        if cache_key not in self._exchanges:
            try:
                self._exchanges[cache_key] = broker.get_ccxt_client()
                logger.info(f"Nouvelle instance CCXT créée pour {cache_key}")
            except Exception as e:
                logger.error(f"Erreur création instance CCXT pour {cache_key}: {e}")
                raise
        
        return self._exchanges[cache_key]
    
    def clear_exchange(self, broker):
        """Supprime une instance du cache"""
        cache_key = f"ccxt_{broker.user_id}_{broker.exchange}_{broker.id}"
        if cache_key in self._exchanges:
            del self._exchanges[cache_key]
            logger.info(f"Instance CCXT supprimée pour {cache_key}")
    
    def clear_all(self):
        """Vide tout le cache"""
        self._exchanges.clear()
        logger.info("Toutes les instances CCXT ont été supprimées")

# Instance globale
ccxt_service = CCXTService()
```

#### Fichier : `backend/apps/core/services/symbol_updater.py`
```python
import asyncio
import ccxt.async_support as ccxt_async
from typing import Dict, List
from django.db import transaction
from django.utils import timezone
from apps.brokers.models import ExchangeSymbol
import logging

logger = logging.getLogger(__name__)

class SymbolUpdaterService:
    """
    Service pour mettre à jour les symboles disponibles sur les exchanges.
    Utilise ccxt en mode async pour des performances optimales.
    """
    
    @staticmethod
    async def update_exchange_symbols(exchange_name: str) -> Dict:
        """
        Met à jour les symboles pour un exchange donné.
        Retourne un dictionnaire avec les statistiques de mise à jour.
        """
        stats = {
            'exchange': exchange_name,
            'added': 0,
            'updated': 0,
            'deactivated': 0,
            'errors': []
        }
        
        try:
            # Créer une instance CCXT async pour l'exchange
            exchange_class = getattr(ccxt_async, exchange_name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'rateLimit': 2000
            })
            
            try:
                # Charger les marchés
                markets = await exchange.load_markets()
                
                # Transaction pour la mise à jour atomique
                with transaction.atomic():
                    # Marquer tous les symboles existants comme inactifs
                    ExchangeSymbol.objects.filter(
                        exchange=exchange_name
                    ).update(active=False)
                    stats['deactivated'] = ExchangeSymbol.objects.filter(
                        exchange=exchange_name,
                        active=False
                    ).count()
                    
                    # Traiter chaque marché
                    for symbol, market in markets.items():
                        # On ne traite que les marchés spot actifs
                        if not market.get('active', False):
                            continue
                        
                        if market.get('type') not in ['spot', None]:
                            continue
                        
                        try:
                            # Extraire les informations
                            limits = market.get('limits', {})
                            precision = market.get('precision', {})
                            
                            # Créer ou mettre à jour le symbole
                            obj, created = ExchangeSymbol.objects.update_or_create(
                                exchange=exchange_name,
                                symbol=symbol,
                                type=market.get('type', 'spot'),
                                defaults={
                                    'base': market.get('base', ''),
                                    'quote': market.get('quote', ''),
                                    'active': True,
                                    'min_amount': limits.get('amount', {}).get('min'),
                                    'max_amount': limits.get('amount', {}).get('max'),
                                    'min_price': limits.get('price', {}).get('min'),
                                    'max_price': limits.get('price', {}).get('max'),
                                    'min_cost': limits.get('cost', {}).get('min'),
                                    'amount_precision': precision.get('amount'),
                                    'price_precision': precision.get('price'),
                                    'raw_info': market,
                                    'last_updated': timezone.now(),
                                }
                            )
                            
                            if created:
                                stats['added'] += 1
                            else:
                                stats['updated'] += 1
                                
                        except Exception as e:
                            logger.error(f"Erreur traitement symbole {symbol}: {e}")
                            stats['errors'].append(f"{symbol}: {str(e)}")
                    
                    # Supprimer les symboles qui ne sont plus actifs
                    deleted_count = ExchangeSymbol.objects.filter(
                        exchange=exchange_name,
                        active=False
                    ).delete()[0]
                    
                    logger.info(
                        f"Mise à jour {exchange_name}: "
                        f"{stats['added']} ajoutés, {stats['updated']} mis à jour, "
                        f"{deleted_count} supprimés"
                    )
                    
            finally:
                # Toujours fermer l'exchange
                await exchange.close()
                
        except Exception as e:
            logger.error(f"Erreur mise à jour exchange {exchange_name}: {e}")
            stats['errors'].append(str(e))
        
        return stats
    
    @staticmethod
    def update_symbols_sync(exchange_name: str) -> Dict:
        """
        Version synchrone pour appel depuis Django.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                SymbolUpdaterService.update_exchange_symbols(exchange_name)
            )
        finally:
            loop.close()
```

### ÉTAPE 1.4 : Scripts de gestion (initialisation et Trading Engine)

#### Fichier : `backend/apps/core/management/commands/run_trading_engine.py`
```python
from django.core.management.base import BaseCommand
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import asyncio
import logging
import signal
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Lance le moteur de trading qui écoute les signaux du Heartbeat'
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.channel_layer = get_channel_layer()
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Mode test sans exécution réelle des trades',
        )
    
    def handle(self, *args, **options):
        self.test_mode = options.get('test', False)
        
        # Gérer l'arrêt propre
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🚀 Trading Engine démarré {'(MODE TEST)' if self.test_mode else ''}\n"
            )
        )
        
        # Lancer la boucle async
        asyncio.run(self.run_engine())
    
    async def run_engine(self):
        """Boucle principale du Trading Engine"""
        
        # Se connecter au channel Redis pour écouter les signaux
        channel_name = 'trading_engine'
        
        self.stdout.write(
            self.style.SUCCESS(f"✓ Connexion au channel 'heartbeat'...")
        )
        
        while self.running:
            try:
                # Attendre un signal du Heartbeat (implémentation simplifiée)
                # Cette partie sera complétée dans le Module 7
                await asyncio.sleep(1)
                
                # Vérifier s'il y a des signaux à traiter
                # Pour l'instant, juste un placeholder
                if False:  # Sera remplacé par la vraie logique
                    await self.process_signal({})
                    
            except Exception as e:
                logger.error(f"Erreur dans le Trading Engine: {e}")
                await asyncio.sleep(5)  # Attendre avant de réessayer
    
    async def process_signal(self, signal_data):
        """
        Traite un signal reçu du Heartbeat.
        Cette méthode sera complétée dans le Module 7.
        """
        timeframe = signal_data.get('timeframe')
        timestamp = signal_data.get('timestamp')
        
        self.stdout.write(
            f"Signal reçu: {timeframe} à {timestamp}"
        )
        
        # TODO: Module 7
        # 1. Récupérer les stratégies actives pour ce timeframe
        # 2. Pour chaque stratégie:
        #    a. Récupérer les bougies nécessaires
        #    b. Exécuter la logique de la stratégie
        #    c. Passer les ordres si nécessaire
        pass
    
    def shutdown(self, signum, frame):
        """Arrêt propre du service"""
        self.stdout.write(
            self.style.WARNING("\n⚠️  Arrêt du Trading Engine...")
        )
        self.running = False
        sys.exit(0)
```

#### Fichier : `backend/apps/accounts/management/commands/init_aristobot.py`
```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialise Aristobot3 avec les utilisateurs de base'
    
    def handle(self, *args, **options):
        with transaction.atomic():
            # Créer l'utilisateur dev
            if not User.objects.filter(username='dev').exists():
                User.objects.create_user(
                    username='dev',
                    email='dev@aristobot.local',
                    password=None,  # Pas de mot de passe en mode dev
                    first_name='Mode',
                    last_name='Développement',
                )
                self.stdout.write(
                    self.style.SUCCESS('✓ Utilisateur "dev" créé')
                )
            else:
                self.stdout.write('Utilisateur "dev" existe déjà')
            
            # Créer l'utilisateur dac
            if not User.objects.filter(username='dac').exists():
                User.objects.create_user(
                    username='dac',
                    email='daniel.carnal@gmail.com',
                    password='aristobot',
                    first_name='Daniel',
                    last_name='Carnal',
                    is_staff=True,
                    is_superuser=True,
                )
                self.stdout.write(
                    self.style.SUCCESS('✓ Utilisateur "dac" créé (superuser)')
                )
            else:
                self.stdout.write('Utilisateur "dac" existe déjà')
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ Initialisation terminée!')
            )
            
            # Initialiser la table HeartbeatStatus
            from apps.core.models import HeartbeatStatus
            if not HeartbeatStatus.objects.exists():
                HeartbeatStatus.objects.create(
                    is_connected=False,
                    symbols_monitored=['BTC/USDT']  # Symbole par défaut
                )
                self.stdout.write(
                    self.style.SUCCESS('✓ Table HeartbeatStatus initialisée')
                )
```

### ÉTAPE 1.5 : APIs REST

#### Fichier : `backend/apps/brokers/serializers.py`
```python
from rest_framework import serializers
from .models import Broker, ExchangeSymbol
import ccxt

class BrokerSerializer(serializers.ModelSerializer):
    """Serializer pour les brokers"""
    last_balance = serializers.SerializerMethodField()
    available_symbols_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Broker
        fields = [
            'id', 'exchange', 'name', 'description',
            'api_key', 'api_secret', 'api_password',
            'subaccount_name', 'is_default', 'is_testnet', 'is_active',
            'last_connection_test', 'last_connection_success',
            'last_balance_update', 'last_balance',
            'available_symbols_count', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True, 'required': True},
            'api_secret': {'write_only': True, 'required': True},
            'api_password': {'write_only': True, 'required': False},
        }
    
    def get_last_balance(self, obj):
        """Retourne le dernier balance connu (sera implémenté plus tard)"""
        return None
    
    def get_available_symbols_count(self, obj):
        """Compte les symboles disponibles pour cet exchange"""
        return ExchangeSymbol.objects.filter(
            exchange=obj.exchange,
            active=True
        ).count()
    
    def validate_exchange(self, value):
        """Vérifie que l'exchange est supporté par CCXT"""
        if value not in ccxt.exchanges:
            raise serializers.ValidationError(
                f"L'exchange '{value}' n'est pas supporté"
            )
        return value
    
    def create(self, validated_data):
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
```

#### Fichier : `backend/apps/brokers/views.py`
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Broker, ExchangeSymbol
from .serializers import BrokerSerializer, ExchangeSymbolSerializer, TestConnectionSerializer
from apps.core.services.ccxt_service import ccxt_service
import ccxt
import asyncio
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class BrokerViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les brokers"""
    serializer_class = BrokerSerializer
    
    def get_queryset(self):
        """Retourne uniquement les brokers de l'utilisateur connecté"""
        return Broker.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Teste la connexion à un broker"""
        broker = self.get_object()
        success, result = broker.test_connection()
        
        if success:
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'balance': result.get('total', {})
            })
        else:
            return Response({
                'success': False,
                'message': f'Erreur de connexion : {result}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_symbols(self, request, pk=None):
        """Met à jour les symboles disponibles pour un exchange"""
        broker = self.get_object()
        
        # Lancer la mise à jour en arrière-plan
        from apps.core.services import SymbolUpdaterService
        from threading import Thread
        
        def update_in_background():
            try:
                stats = SymbolUpdaterService.update_symbols_sync(broker.exchange)
                
                logger.info(
                f"Mise à jour des symboles pour {broker.exchange}: "
                f"{stats.get('added', 0)} ajoutés, "
                f"{stats.get('updated', 0)} mis à jour"
                )
                    
            except Exception as e:
                logger.error(f"Erreur mise à jour symboles: {e}")
        
        thread = Thread(target=update_in_background)
        thread.daemon = True
        thread.start()
        
        return Response({
            'message': f'Mise à jour des paires de trading pour {broker.exchange} lancée en arrière-plan'
        })
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Définit un broker comme broker par défaut"""
        broker = self.get_object()
        broker.is_default = True
        broker.save()
        return Response({'message': f'{broker.name} est maintenant le broker par défaut'})


class ExchangeSymbolViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour consulter les symboles disponibles"""
    serializer_class = ExchangeSymbolSerializer
    
    def get_queryset(self):
        """Filtre les symboles par exchange si demandé"""
        queryset = ExchangeSymbol.objects.filter(active=True)
        exchange = self.request.query_params.get('exchange', None)
        if exchange:
            queryset = queryset.filter(exchange=exchange)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(symbol__icontains=search)
        return queryset
```

#### Fichier : `backend/apps/brokers/urls.py`
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BrokerViewSet, ExchangeSymbolViewSet

router = DefaultRouter()
router.register(r'brokers', BrokerViewSet, basename='broker')
router.register(r'symbols', ExchangeSymbolViewSet, basename='symbol')

urlpatterns = [
    path('', include(router.urls)),
]
```

#### Fichier : `backend/apps/accounts/views.py`
```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Endpoint de connexion"""
    # En mode DEBUG (`DEBUG_ARISTOBOT=True`), connexion automatique avec user dev
    if settings.DEBUG and not request.data.get('username'):
        try:
            user = User.objects.get(username='dev')
            login(request, user)
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_dev': True
                }
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur dev non trouvé. Lancez "python manage.py init_aristobot"'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Connexion normale
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Nom d\'utilisateur et mot de passe requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_dev': False
            }
        })
    
    return Response(
        {'error': 'Identifiants invalides'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Endpoint de déconnexion"""
    logout(request)
    # En mode DEBUG (`DEBUG_ARISTOBOT=True`), reconnecter automatiquement avec dev
    if settings.DEBUG:
        try:
            user = User.objects.get(username='dev')
            login(request, user)
            return Response({'message': 'Déconnecté, reconnecté en tant que dev'})
        except User.DoesNotExist:
            pass
    return Response({'message': 'Déconnecté'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Retourne l'utilisateur actuellement connecté"""
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_dev': user.username == 'dev',
        'ai_provider': user.ai_provider,
        'ai_enabled': user.ai_enabled,
        'theme': user.theme,
        'display_timezone': user.display_timezone,
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """Met à jour les préférences utilisateur"""
    user = request.user
    
    # Gestion des switches IA - activer l'un désactive l'autre
    if 'ai_provider' in request.data:
        provider = request.data['ai_provider']
        if provider != 'none':
            user.ai_provider = provider
            user.ai_enabled = True
        else:
            user.ai_enabled = False
            user.ai_provider = 'none'
    
    if 'ai_enabled' in request.data:
        user.ai_enabled = request.data['ai_enabled']
        if not user.ai_enabled:
            user.ai_provider = 'none'
    
    if 'ai_api_key' in request.data:
        user.ai_api_key = request.data['ai_api_key']
    if 'ai_endpoint_url' in request.data:
        user.ai_endpoint_url = request.data['ai_endpoint_url']
    if 'theme' in request.data:
        user.theme = request.data['theme']
    if 'display_timezone' in request.data:
        user.display_timezone = request.data['display_timezone']
    
    user.save()
    return Response({'message': 'Préférences mises à jour'})
```

#### Fichier : `backend/apps/accounts/urls.py`
```python
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('current/', views.current_user, name='current-user'),
    path('preferences/', views.update_preferences, name='update-preferences'),
]
```

#### Fichier : `backend/aristobot/urls.py` (modifications)
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.brokers.urls')),
    # ... autres URLs ...
]
```

### ÉTAPE 1.6 : Frontend Vue.js

#### Fichier : `frontend/src/stores/auth.js`
```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  
  const isAuthenticated = computed(() => !!user.value)
  const isDev = computed(() => user.value?.is_dev || false)
  
  async function login(username = null, password = null) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.post('/api/auth/login/', {
        username,
        password
      })
      user.value = response.data.user
      return true
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur de connexion'
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  async function logout() {
    try {
      await axios.post('/api/auth/logout/')
      // En mode dev, on sera reconnecté automatiquement
      await checkAuth()
    } catch (err) {
      console.error('Erreur de déconnexion:', err)
    }
  }
  
  async function checkAuth() {
    try {
      const response = await axios.get('/api/auth/current/')
      user.value = response.data
      return true
    } catch (err) {
      // En mode DEBUG (`DEBUG_ARISTOBOT=True`), essayer de se connecter automatiquement
      if (import.meta.env.DEV) {
        return await login()
      }
      user.value = null
      return false
    }
  }
  
  async function updatePreferences(preferences) {
    try {
      await axios.put('/api/auth/preferences/', preferences)
      // Recharger les infos utilisateur
      await checkAuth()
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur de mise à jour'
      throw err
    }
  }
  
  return {
    user,
    isLoading,
    error,
    isAuthenticated,
    isDev,
    login,
    logout,
    checkAuth,
    updatePreferences
  }
})
```

#### Fichier : `frontend/src/views/AccountView.vue`
```vue
<template>
  <div class="account-view">
    <h1>Mon Compte</h1>
    
    <!-- Informations utilisateur -->
    <div class="section">
      <h2>Informations</h2>
      <div class="info-grid">
        <div class="info-item">
          <label>Nom d'utilisateur :</label>
          <span>{{ user?.username }}</span>
          <span v-if="isDev" class="badge dev">MODE DEV</span>
        </div>
        <div class="info-item">
          <label>Email :</label>
          <span>{{ user?.email }}</span>
        </div>
      </div>
    </div>
    
    <!-- Configuration IA -->
    <div class="section">
      <h2>Assistant IA</h2>
      <div class="form-group">
        <label>Fournisseur :</label>
        <div class="switch-group">
          <div class="switch-item">
            <label>OpenRouter</label>
            <label class="switch">
              <input 
                type="checkbox" 
                :checked="preferences.ai_provider === 'openrouter' && preferences.ai_enabled"
                @change="toggleAI('openrouter')"
              >
              <span class="slider"></span>
            </label>
          </div>
          <div class="switch-item">
            <label>Ollama (local)</label>
            <label class="switch">
              <input 
                type="checkbox" 
                :checked="preferences.ai_provider === 'ollama' && preferences.ai_enabled"
                @change="toggleAI('ollama')"
              >
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>
      
      <div v-if="preferences.ai_provider === 'openrouter'" class="form-group">
        <label>Clé API OpenRouter :</label>
        <input 
          type="password" 
          v-model="preferences.ai_api_key"
          placeholder="sk-or-..."
        >
      </div>
      
      <div v-if="preferences.ai_provider === 'ollama'" class="form-group">
        <label>URL Ollama :</label>
        <input 
          type="url" 
          v-model="preferences.ai_endpoint_url"
          placeholder="http://localhost:11434"
        >
      </div>
    </div>
    
    <!-- Préférences d'affichage -->
    <div class="section">
      <h2>Affichage</h2>
      <div class="form-group">
        <label>Thème :</label>
        <select v-model="preferences.theme">
          <option value="dark">Sombre (avec couleurs néon)</option>
          <option value="light">Clair</option>
        </select>
      </div>
      <div class="form-group">
        <label>Fuseau horaire :</label>
        <select v-model="preferences.display_timezone">
          <option value="UTC">UTC</option>
          <option value="local">Fuseau horaire local ({{ localTimezone }})</option>
        </select>
      </div>
    </div>
    
    <!-- Brokers -->
    <div class="section">
      <h2>Exchanges / Brokers</h2>
      <button @click="showAddBroker = true" class="btn btn-primary">
        + Ajouter un Broker
      </button>
      
      <div class="brokers-table">
        <table>
          <thead>
            <tr>
              <th>Exchange</th>
              <th>Description</th>
              <th>Clé API</th>
              <th>Défaut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="broker in brokers" :key="broker.id">
              <td>{{ broker.exchange.toUpperCase() }}</td>
              <td>{{ broker.name }}</td>
              <td>
                <span v-if="broker.last_connection_success" class="status-dot success"></span>
                <span v-else-if="broker.last_connection_test" class="status-dot error"></span>
                <span v-else class="status-dot unknown"></span>
                {{ broker.api_key ? '••••••••••' : 'Non configuré' }}
              </td>
              <td>
                <span v-if="broker.is_default" class="badge success">✓</span>
              </td>
              <td>
                <button @click="editBroker(broker)" class="btn btn-sm">
                  Modifier
                </button>
                <button @click="deleteBroker(broker)" class="btn btn-sm btn-danger">
                  Supprimer
                </button>
                <button @click="updateSymbols(broker)" class="btn btn-sm">
                  MAJ Paires
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- Modal Broker -->
    <div v-if="showBrokerModal" class="modal">
      <div class="modal-content">
        <h3>{{ editingBroker ? 'Modifier' : 'Ajouter' }} un Broker</h3>
        
        <div class="form-group">
          <label>Exchange :</label>
          <select v-model="brokerForm.exchange">
            <option value="binance">Binance</option>
            <option value="kucoin">KuCoin</option>
            <option value="bitget">Bitget</option>
            <option value="okx">OKX</option>
            <option value="bybit">Bybit</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Nom personnalisé :</label>
          <input 
            type="text" 
            v-model="brokerForm.name"
            placeholder="Ex: Binance Principal"
          >
        </div>
        
        <div class="form-group">
          <label>Description :</label>
          <textarea 
            v-model="brokerForm.description"
            placeholder="Notes optionnelles..."
          ></textarea>
        </div>
        
        <div class="form-group">
          <label>Clé API :</label>
          <input 
            type="text" 
            v-model="brokerForm.api_key"
            placeholder="Votre clé API"
          >
        </div>
        
        <div class="form-group">
          <label>Secret API :</label>
          <input 
            type="password" 
            v-model="brokerForm.api_secret"
            placeholder="Votre secret API"
          >
        </div>
        
        <div class="form-group">
          <label>
            <input 
              type="checkbox" 
              v-model="brokerForm.is_testnet"
            >
            Mode Testnet
          </label>
        </div>
        
        <div class="modal-actions">
          <button @click="testConnection" class="btn">
            Tester la connexion
          </button>
          <button @click="saveBroker" class="btn btn-primary">
            Sauvegarder
          </button>
          <button @click="closeBrokerModal" class="btn btn-secondary">
            Annuler
          </button>
        </div>
        
        <div v-if="connectionTest" class="alert" :class="connectionTest.success ? 'success' : 'error'">
          {{ connectionTest.message }}
        </div>
      </div>
    </div>
    
    <!-- Bouton sauvegarder -->
    <div class="actions">
      <button @click="savePreferences" class="btn btn-primary">
        Sauvegarder les préférences
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const isDev = computed(() => authStore.isDev)

const preferences = ref({
  ai_provider: 'none',
  ai_enabled: false,
  ai_api_key: '',
  ai_endpoint_url: 'http://localhost:11434',
  theme: 'dark',
  display_timezone: 'local'
})

// Détecter le fuseau horaire local
const localTimezone = ref(Intl.DateTimeFormat().resolvedOptions().timeZone)

const brokers = ref([])
const showBrokerModal = ref(false)
const showAddBroker = computed({
  get: () => showBrokerModal.value,
  set: (val) => {
    if (val) {
      editingBroker.value = null
      resetBrokerForm()
    }
    showBrokerModal.value = val
  }
})

const editingBroker = ref(null)
const brokerForm = ref({
  exchange: 'binance',
  name: '',
  description: '',
  api_key: '',
  api_secret: '',
  api_password: '',
  subaccount_name: '',
  is_testnet: false
})

const connectionTest = ref(null)

onMounted(async () => {
  // Charger les préférences utilisateur
  if (user.value) {
    preferences.value = {
      ai_provider: user.value.ai_provider || 'none',
      ai_enabled: user.value.ai_enabled || false,
      ai_api_key: '',
      ai_endpoint_url: user.value.ai_endpoint_url || 'http://localhost:11434',
      theme: user.value.theme || 'dark',
      display_timezone: user.value.display_timezone || 'local'
    }
    
    // Appliquer le thème
    document.documentElement.setAttribute('data-theme', preferences.value.theme)
  }
  
  // Charger les brokers
  await loadBrokers()
})

async function loadBrokers() {
  try {
    const response = await axios.get('/api/brokers/')
    brokers.value = response.data.results || response.data
  } catch (error) {
    console.error('Erreur chargement brokers:', error)
  }
}

async function savePreferences() {
  try {
    await authStore.updatePreferences(preferences.value)
    alert('Préférences sauvegardées')
  } catch (error) {
    alert('Erreur lors de la sauvegarde')
  }
}

function editBroker(broker) {
  editingBroker.value = broker
  brokerForm.value = {
    exchange: broker.exchange,
    name: broker.name,
    description: broker.description || '',
    api_key: '',  // Ne pas afficher la clé existante pour sécurité
    api_secret: '',  // Ne pas afficher le secret existant
    api_password: broker.api_password ? '••••••••' : '',
    subaccount_name: broker.subaccount_name || '',
    is_testnet: broker.is_testnet || false
  }
  showBrokerModal.value = true
}

async function deleteBroker(broker) {
  if (confirm(`Supprimer ${broker.name} ?`)) {
    try {
      await axios.delete(`/api/brokers/${broker.id}/`)
      await loadBrokers()
    } catch (error) {
      alert('Erreur lors de la suppression')
    }
  }
}

async function updateSymbols(broker) {
  try {
    const response = await axios.post(`/api/brokers/${broker.id}/update_symbols/`)
    alert(response.data.message)
  } catch (error) {
    alert('Erreur lors de la mise à jour des symboles')
  }
}

async function testConnection() {
  connectionTest.value = null
  
  // Validation temps réel des clés
  if (!brokerForm.value.api_key || !brokerForm.value.api_secret) {
    connectionTest.value = {
      success: false,
      message: 'Veuillez entrer les clés API'
    }
    return
  }
  
  // Sauvegarder d'abord si nouveau broker
  let brokerId = editingBroker.value?.id
  
  if (!brokerId) {
    try {
      const response = await axios.post('/api/brokers/', brokerForm.value)
      brokerId = response.data.id
    } catch (error) {
      connectionTest.value = {
        success: false,
        message: 'Erreur lors de la création du broker'
      }
      return
    }
  }
  
  try {
    const response = await axios.post(`/api/brokers/${brokerId}/test_connection/`)
    connectionTest.value = response.data
  } catch (error) {
    connectionTest.value = {
      success: false,
      message: error.response?.data?.message || 'Erreur de connexion'
    }
  }
}

async function saveBroker() {
  try {
    // Ne pas envoyer les champs vides ou masqués lors de l'édition
    const dataToSend = { ...brokerForm.value }
    if (editingBroker.value) {
      // En mode édition, ne pas envoyer les clés si elles sont masquées
      if (dataToSend.api_key === '') delete dataToSend.api_key
      if (dataToSend.api_secret === '') delete dataToSend.api_secret
      if (dataToSend.api_password === '••••••••') delete dataToSend.api_password
      
      await axios.patch(`/api/brokers/${editingBroker.value.id}/`, dataToSend)
    } else {
      await axios.post('/api/brokers/', dataToSend)
    }
    await loadBrokers()
    closeBrokerModal()
  } catch (error) {
    alert('Erreur lors de la sauvegarde')
  }
}

function toggleAI(provider) {
  if (preferences.value.ai_provider === provider && preferences.value.ai_enabled) {
    // Désactiver
    preferences.value.ai_enabled = false
    preferences.value.ai_provider = 'none'
  } else {
    // Activer ce provider et désactiver l'autre
    preferences.value.ai_enabled = true
    preferences.value.ai_provider = provider
  }
}

function closeBrokerModal() {
  showBrokerModal.value = false
  editingBroker.value = null
  resetBrokerForm()
  connectionTest.value = null
}

function resetBrokerForm() {
  brokerForm.value = {
    exchange: 'binance',
    name: '',
    description: '',
    api_key: '',
    api_secret: '',
    api_password: '',
    subaccount_name: '',
    is_testnet: false
  }
}
</script>

<style scoped>
/* Styles adaptés au thème dark avec couleurs néon */
.account-view {
  padding: 2rem;
}

.section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--color-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1);
}

.switch-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--color-background);
  border-radius: 0.25rem;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-border);
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--color-primary);
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 0.5rem;
}

.status-dot.success {
  background-color: var(--color-success);
}

.status-dot.error {
  background-color: var(--color-danger);
}

.status-dot.unknown {
  background-color: var(--color-border);
}

.brokers-table {
  margin-top: 1rem;
  overflow-x: auto;
}

.brokers-table table {
  width: 100%;
  border-collapse: collapse;
}

.brokers-table th,
.brokers-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.brokers-table th {
  color: var(--color-primary);
  font-weight: 600;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
}

.btn:hover {
  background: var(--color-background);
  border-color: var(--color-primary);
}

.btn-primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-background);
}

.btn-primary:hover {
  background: var(--color-primary-dark);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.btn-danger {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: white;
}

.btn-danger:hover {
  background: var(--color-danger-dark);
  box-shadow: 0 0 10px rgba(255, 0, 85, 0.5);
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge.dev {
  background: var(--color-warning);
  color: var(--color-background);
}

.badge.success {
  color: var(--color-success);
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.alert {
  padding: 1rem;
  border-radius: 0.25rem;
  margin-top: 1rem;
}

.alert.success {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid var(--color-success);
  color: var(--color-success);
}

.alert.error {
  background: rgba(255, 0, 85, 0.1);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 2rem;
}
</style>
```

### ÉTAPE 1.7 : Commandes de validation

```bash
# Créer et appliquer les migrations
cd backend
python manage.py makemigrations accounts brokers core
python manage.py migrate

# Initialiser les utilisateurs
python manage.py init_aristobot

# Lancer le serveur
python manage.py runserver

# Dans un autre terminal, lancer le frontend
cd frontend
npm run dev

# Dans un troisième terminal, tester le Trading Engine
python manage.py run_trading_engine --test

# Tester :
# 1. Accéder à http://localhost:5173
# 2. Vérifier la connexion auto en mode DEBUG
# 3. Créer un broker
# 4. Tester la connexion
# 5. Mettre à jour les symboles
# 6. Vérifier que le Trading Engine démarre sans erreur
```

---

## 📦 MODULE 2 : HEARTBEAT AMÉLIORÉ

### Objectifs
1. Améliorer le service Heartbeat existant
2. Sauvegarder les bougies en PostgreSQL
3. Créer une interface de monitoring temps réel
4. Gérer la cohérence des données

### Structure générale
- Modèle `Candle` pour stocker les bougies
- Service amélioré avec sauvegarde DB
- API REST pour récupérer l'historique
- WebSocket pour le temps réel
- Frontend avec affichage 20 lignes / scroll 60

---

## 📦 MODULE 3 : TRADING MANUEL

### Objectifs
1. Interface de trading manuel complète
2. Passage d'ordres via CCXT
3. Visualisation du portfolio
4. Historique des trades

### Structure générale
- Modèle `Trade` multi-tenant
- API pour passer des ordres (buy/sell, market/limit)
- Service de calcul position/balance
- Frontend avec calculateur quantité/montant
- Sélection des paires depuis `ExchangeSymbol`

---

## 📦 MODULE 4 : WEBHOOKS

### Objectifs
1. Recevoir des signaux TradingView
2. Passer automatiquement les ordres
3. Logger toutes les tentatives

### Structure générale
- Modèle `Webhook` pour l'historique
- Endpoint POST pour réception
- Service de traitement asynchrone
- Frontend de monitoring

---

## 📦 MODULE 5 : STRATÉGIES

### Objectifs
1. Éditeur de stratégies Python
2. Assistant IA pour coder
3. Validation syntaxique
4. Template de base `Strategy`

### Structure générale
- Modèle `Strategy` avec code Python
- Classe de base `apps.strategies.base.Strategy`
- API de validation Python (ast.parse)
- Intégration IA (OpenRouter/Ollama)
- Frontend avec éditeur de code

---

## 📦 MODULE 6 : BACKTEST

### Objectifs
1. Test sur données historiques
2. Progression en temps réel
3. Calcul des métriques
4. Interruption possible

### Structure générale
- Modèle `BacktestResult`
- Service de calcul asynchrone
- WebSocket pour progression
- Frontend avec graphiques

---

## 📦 MODULE 7 : TRADING BOT

### Objectifs
1. Activation des stratégies
2. Écoute du Heartbeat
3. Exécution automatique
4. Monitoring en temps réel

### Structure générale
- Modèle `ActiveStrategy`
- Service Trading Engine amélioré
- Connexion au Heartbeat
- Frontend de contrôle

---

## 📦 MODULE 8 : STATISTIQUES

### Objectifs
1. Calcul des performances
2. Graphiques d'évolution
3. Analyse par stratégie

### Structure générale
- Services de calcul statistique
- API d'agrégation
- Frontend avec charts

---

## 🔧 PROMPTS OPTIMISÉS POUR CLAUDE CODE

### Pour le Module 1 (à copier-coller dans Claude Code)

```
Contexte : Je développe Aristobot3, un bot de trading crypto en Django/Vue.js.

Fichiers de référence :
- ARISTOBOT3.md : Description complète du projet
- IMPLEMENTATION_PLAN.md : Plan détaillé avec TOUT le code du Module 1 (c'est là que tu trouveras le code à copier)

Chemin du projet : C:\Users\dac\Documents\Python\Django\Aristobot3

Objectif : Implémenter EXACTEMENT le Module 1 (User Account & Brokers) en suivant le code fourni dans IMPLEMENTATION_PLAN.md

Actions à réaliser dans l'ordre :
1. Créer les modèles dans :
   - backend/apps/core/models.py (HeartbeatStatus, Position)
   - backend/apps/accounts/models.py (User étendu)
   - backend/apps/brokers/models.py (Broker, ExchangeSymbol)
2. Créer backend/apps/accounts/backends.py (DevModeBackend)
3. Créer les services dans backend/apps/core/services/ :
   - __init__.py
   - ccxt_service.py
   - symbol_updater.py
4. Créer les management commands :
   - backend/apps/accounts/management/commands/init_aristobot.py
   - backend/apps/core/management/commands/run_trading_engine.py
5. Créer les serializers et viewsets :
   - backend/apps/brokers/serializers.py
   - backend/apps/brokers/views.py
6. Créer les views pour accounts :
   - backend/apps/accounts/views.py
7. Configurer les URLs :
   - backend/apps/accounts/urls.py
   - backend/apps/brokers/urls.py
   - Modifier backend/aristobot/urls.py
8. Modifier backend/aristobot/settings.py
9. Créer/modifier le frontend Vue :
   - frontend/src/stores/auth.js
   - frontend/src/views/AccountView.vue

Prérequis à vérifier :
- PostgreSQL est installé et configuré
- Redis est installé et lancé
- Un fichier .env existe avec DEBUG_ARISTOBOT=True
- Le projet Django de base existe déjà
- Le projet Vue.js de base existe avec Pinia installé

Dépendances à installer si besoin :
pip install ccxt cryptography django-cors-headers channels channels-redis djangorestframework python-dotenv

Contraintes importantes :
- PostgreSQL uniquement (pas de MongoDB)
- Multi-tenant strict (toujours filtrer par user_id)
- Chiffrement avec Django SECRET_KEY
- Mode DEBUG = connexion auto avec user "dev"
- CCXT avec enableRateLimit: true

Tests après chaque étape :
1. Vérifier que le serveur démarre : python manage.py runserver
2. Après tous les modèles, faire les migrations :
   python manage.py makemigrations accounts brokers core
   python manage.py migrate
3. Après tout, lancer : python manage.py init_aristobot
4. Tester le Trading Engine : python manage.py run_trading_engine --test

IMPORTANT : Le code détaillé pour chaque fichier est dans IMPLEMENTATION_PLAN.md, section "MODULE 1". 
Utilise CE code exact, ne réinvente pas. Le code commence à "ÉTAPE 1.1" et va jusqu'à "ÉTAPE 1.7".
```

### Pour débugger si nécessaire

```
J'ai une erreur : [coller l'erreur]

Contexte : Module 1 de Aristobot3
Fichier concerné : [nom du fichier]

Aide-moi à corriger sans casser le reste du code.
```

---

## ✅ CHECKLIST DE VALIDATION

### Module 1
- [ ] Migrations créées et appliquées (accounts, brokers, core)
- [ ] Script init_aristobot fonctionne
- [ ] Table HeartbeatStatus initialisée
- [ ] Mode DEBUG : connexion auto avec user "dev"
- [ ] CRUD Brokers fonctionnel
- [ ] Test connexion CCXT réussi
- [ ] Service SymbolUpdater fonctionnel
- [ ] Mise à jour symboles en arrière-plan
- [ ] Trading Engine démarre sans erreur (mode test)
- [ ] Frontend AccountView complet
- [ ] Chiffrement des API keys vérifié
- [ ] Table Position créée pour suivi des trades ouverts

### Points d'attention
- Toujours utiliser `request.user` pour le multi-tenant
- Vérifier les permissions sur chaque endpoint
- Tester en mode DEBUG_ARISTOBOT=True et DEBUG_ARISTOBOT=False
- Valider le chiffrement/déchiffrement des clés

---

## 📝 NOTES IMPORTANTES

1. **CCXT Rate Limiting** : Toujours activer `enableRateLimit: true`
2. **Multi-tenant** : Ne jamais oublier de filtrer par `user_id`
3. **Mode Dev** : L'user "dev" a accès à TOUTES les données
4. **Testnet** : À implémenter progressivement
5. **Symboles** : Table partagée mise à jour en async
6. **Instances CCXT** : Singleton pattern obligatoire

Ce plan est votre guide de référence. Suivez-le étape par étape avec Claude Code.

Bonne implémentation ! 🚀
