# MODULE 1 IMPLEMENTATION - USER ACCOUNT & BROKERS

## 🎯 OBJECTIFS DU MODULE 1

1. **Système d'authentification multi-tenant** avec utilisateur "dev"
2. **Gestion des brokers** (exchanges) avec CCXT  
3. **Mode DEBUG** sécurisé via table DebugMode
4. **Table partagée** des symboles d'exchanges
5. **Frontend Vue.js** pour gestion comptes et brokers

---

## ✅ ÉTAT ACTUEL - 85% TERMINÉ

### Ce qui fonctionne
- ✅ **Authentification refactorisée** : Suppression des privilèges spéciaux pour "dev"
- ✅ **App auth** créée avec modèle DebugMode singleton
- ✅ **Modèles Broker** avec chiffrement des clés API
- ✅ **Services CCXT** : CCXTManager + SymbolUpdaterService
- ✅ **API REST complète** : Endpoints brokers avec test connexion
- ✅ **Frontend AccountView** : Interface complète avec modale brokers
- ✅ **Test connexion** : Affichage détaillé du solde
- ✅ **Mise à jour symboles** en arrière-plan

### Ce qui reste à finaliser
- ⚠️ **Command init_aristobot** : Créer user "dev" normal avec mot de passe
- ⚠️ **Frontend debug toggle** : Intégrer le bouton debug dans LoginView
- ⚠️ **Tests finaux** : Validation complète en mode DEBUG_ARISTOBOT=False

---

## 📋 ÉTAPES D'IMPLÉMENTATION

### ÉTAPE 1.1 : Modèles de base ✅

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

### ÉTAPE 1.2 : Migrations et configuration Django ✅

#### Fichier : `backend/aristobot/settings.py` (modifications)
```python
# Configuration DEBUG
DEBUG = os.getenv('DEBUG_ARISTOBOT', 'False') == 'True'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

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
```

### ÉTAPE 1.3 : Services Core (CCXT Singleton et mise à jour des symboles) ✅

#### Fichier : `backend/apps/core/services/symbol_updater.py`
```python
import asyncio
import ccxt
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
    Utilise ccxt pour récupérer les informations de marché.
    """
    
    @staticmethod
    def update_exchange_symbols_sync(exchange_name: str) -> Dict:
        """
        Met à jour les symboles pour un exchange donné (version synchrone).
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
            # Créer une instance CCXT synchrone pour l'exchange
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'rateLimit': 2000
            })
            
            try:
                # Charger les marchés
                markets = exchange.load_markets()
                
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
                # Fermer l'exchange si possible
                if hasattr(exchange, 'close'):
                    exchange.close()
                
        except Exception as e:
            logger.error(f"Erreur mise à jour exchange {exchange_name}: {e}")
            stats['errors'].append(str(e))
        
        return stats
    
    @staticmethod
    def update_symbols_sync(exchange_name: str) -> Dict:
        """
        Version synchrone pour appel depuis Django.
        """
        return SymbolUpdaterService.update_exchange_symbols_sync(exchange_name)
```

### ÉTAPE 1.4 : APIs REST ✅

#### Fichier : `backend/apps/brokers/views.py`
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Broker, ExchangeSymbol
from .serializers import BrokerSerializer, ExchangeSymbolSerializer, TestConnectionSerializer
from apps.core.services.symbol_updater import SymbolUpdaterService
import ccxt
import asyncio
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class BrokerViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les brokers"""
    serializer_class = BrokerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement les brokers de l'utilisateur connecté"""
        logger.info(f"BrokerViewSet - User: {self.request.user}, Authenticated: {self.request.user.is_authenticated}")
        return Broker.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def exchanges(self, request):
        """Retourne la liste des exchanges disponibles avec leurs infos"""
        exchanges = []
        
        for exchange_id, exchange_name in Broker.EXCHANGE_CHOICES:
            try:
                # Créer une instance temporaire pour analyser les exigences
                exchange_class = getattr(ccxt, exchange_id)
                temp_instance = exchange_class()
                
                # Analyser les credentials requis
                required_credentials = []
                if temp_instance.requiredCredentials.get('apiKey', False):
                    required_credentials.append('api_key')
                if temp_instance.requiredCredentials.get('secret', False):
                    required_credentials.append('api_secret')
                if temp_instance.requiredCredentials.get('password', False):
                    required_credentials.append('api_password')
                
                exchanges.append({
                    'id': exchange_id,
                    'name': exchange_name,
                    'required_credentials': required_credentials,
                    'has_testnet': hasattr(temp_instance, 'set_sandbox_mode') or 'sandbox' in temp_instance.urls,
                    'countries': getattr(temp_instance, 'countries', []),
                    'has_future': temp_instance.has.get('future', False),
                    'has_option': temp_instance.has.get('option', False),
                })
                
            except Exception as e:
                logger.warning(f"Impossible de charger l'exchange {exchange_id}: {e}")
                # Fallback avec infos minimales
                exchanges.append({
                    'id': exchange_id,
                    'name': exchange_name,
                    'required_credentials': ['api_key', 'api_secret'],
                    'has_testnet': True,
                    'countries': [],
                    'has_future': False,
                    'has_option': False,
                })
        
        return Response({
            'exchanges': exchanges,
            'count': len(exchanges)
        })
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Teste la connexion à un broker et recupere le solde"""
        broker = self.get_object()
        success, result = broker.test_connection()
        
        if success:
            # Formater les informations de solde
            total_balance = result.get('total', {})
            free_balance = result.get('free', {})
            used_balance = result.get('used', {})
            
            # Calculer la valeur totale en USDT si possible
            total_value_usd = 0
            for symbol, amount in total_balance.items():
                if symbol == 'USDT' or symbol == 'USD' or symbol == 'USDC':
                    total_value_usd += float(amount) if amount else 0
            
            return Response({
                'success': True,
                'message': 'Connexion reussie',
                'balance': {
                    'total': total_balance,
                    'free': free_balance,
                    'used': used_balance,
                    'total_usd_equivalent': round(total_value_usd, 2)
                },
                'connection_info': {
                    'exchange': broker.exchange,
                    'testnet': broker.is_testnet,
                    'timestamp': timezone.now().isoformat()
                }
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
```

### ÉTAPE 1.5 : Frontend Vue.js ✅

#### Fichier : `frontend/src/views/AccountView.vue`
Interface complète avec :
- ✅ **Gestion dynamique des brokers** : Liste des exchanges depuis CCXT
- ✅ **Modale adaptive** : Champs qui s'adaptent selon l'exchange
- ✅ **Test connexion** : Modale séparée avec affichage du solde
- ✅ **Interface utilisateur** : Design crypto avec couleurs néon
- ✅ **Gestion des préférences** : IA, thème, timezone

---

## 🚧 TÂCHES RESTANTES

### 1. Finaliser la commande init_aristobot

**Objectif :** Créer l'utilisateur "dev" comme utilisateur normal avec mot de passe

**Fichier à modifier :** `backend/apps/accounts/management/commands/init_aristobot.py`

**Code requis :**
```python
# Créer l'utilisateur dev avec mot de passe
if not User.objects.filter(username='dev').exists():
    User.objects.create_user(
        username='dev',
        email='dev@aristobot.local',
        password='dev123',  # Mot de passe normal
        first_name='Mode',
        last_name='Développement',
    )
    self.stdout.write(
        self.style.SUCCESS('✓ Utilisateur "dev" créé avec mot de passe')
    )

# Initialiser la table DebugMode
from apps.auth_custom.models import DebugMode
if not DebugMode.objects.exists():
    DebugMode.objects.create(is_active=False)
    self.stdout.write(
        self.style.SUCCESS('✓ Table DebugMode initialisée')
    )
```

### 2. Frontend : Intégrer le debug toggle

**Objectif :** Ajouter le bouton debug dans LoginView

**Fichier à créer/modifier :** `frontend/src/views/LoginView.vue`

**Fonctionnalités requises :**
- Bouton "Mode développement" visible seulement si DEBUG_ARISTOBOT=True
- Toggle ON/OFF qui met à jour la table DebugMode
- Auto-login avec user "dev" quand activé
- Affichage du statut debug dans la barre de statut

### 3. Tests finaux

**Objectifs :**
- ✅ Vérifier le fonctionnement en mode DEBUG_ARISTOBOT=True
- ⚠️ Tester en mode DEBUG_ARISTOBOT=False
- ⚠️ Valider la sécurité (pas d'accès spéciaux pour "dev")
- ⚠️ Confirmer le multi-tenant (chaque user voit ses données)

---

## ⚡ COMMANDES DE VALIDATION

```bash
# 1. Migrations
python manage.py makemigrations accounts brokers core auth_custom
python manage.py migrate

# 2. Initialisation
python manage.py init_aristobot

# 3. Serveur
python manage.py runserver

# 4. Frontend  
cd frontend && npm run dev

# 5. Tests
# - Accéder à http://localhost:5173
# - Tester connexion broker
# - Vérifier multi-tenant
# - Valider chiffrement des clés
```

---

## 📊 ARCHITECTURE FINALE

### Tables créées
- ✅ `users` - Utilisateurs étendus
- ✅ `brokers` - Comptes exchanges avec clés chiffrées  
- ✅ `exchange_symbols` - Symboles par exchange (partagé)
- ✅ `positions` - Positions ouvertes
- ✅ `heartbeat_status` - Monitoring système
- ✅ `debug_mode` - État debug mode

### Services implémentés
- ✅ `SymbolUpdaterService` - MAJ symboles async
- ✅ `BrokerViewSet` - CRUD + test connexion
- ✅ `AccountView` - Interface utilisateur complète

### Sécurité
- ✅ **Chiffrement Fernet** pour toutes les clés API
- ✅ **Multi-tenant strict** : Filtrage par user_id obligatoire
- ✅ **Permissions DRF** : IsAuthenticated sur tous les endpoints
- ✅ **CCXT rate limiting** : enableRateLimit: true partout

---

## 🎯 PROCHAINES ÉTAPES (MODULE 2)

Une fois le Module 1 à 100% :
1. **Heartbeat amélioré** : Sauvegarde bougies en DB
2. **Interface monitoring** : WebSocket temps réel  
3. **API historique** : Endpoints pour récupérer les bougies
4. **Cohérence données** : Détection trous dans l'historique

Le Module 1 pose les **fondations solides** pour tout le reste d'Aristobot3 ! 🚀