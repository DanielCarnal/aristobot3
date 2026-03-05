# MODULE2 - Refactorisation CCXT vers Service Centralisé (Microservice)

## ATTENTION CLAUDE CODE

**⚠️ RAPPEL CRITIQUE :**
1. **LIS OBLIGATOIREMENT** le fichier `.claude-instructions` à la racine du projet
2. **C'EST L'UTILISATEUR** qui démarre les serveurs et services, **PAS TOI**
3. **NE DÉMARRE AUCUN TERMINAL** ni serveur automatiquement
4. **RESPECTE** strictement l'encodage UTF-8 (première ligne `# -*- coding: utf-8 -*-`)

---

## CONTEXTE & OBJECTIF

### Problème Architectural Identifié
L'actuel `CCXTManager` fonctionne comme singleton **par processus**, mais Aristobot3 utilise **4 processus séparés** :
- Terminal 1 : Serveur Web (Daphne)
- Terminal 2 : Service Heartbeat
- Terminal 3 : Trading Engine  
- Terminal 4 : Frontend (Vite)

**Conséquence** : Chaque processus créé ses **propres instances CCXT**, multipliant les connexions et risquant de **dépasser les rate limits** des exchanges.

### État Actuel de l'Utilisation CCXT
**Modules DÉJÀ implémentés :**
- ✅ `apps/brokers/` (User Account) : Utilise CCXT direct pour tests de connexion → **AUCUN CHANGEMENT REQUIS**
- ✅ Listing des exchanges et validation des credentials → **GARDER EN L'ÉTAT**

**Modules À DÉVELOPPER :**
- ❌ `apps/trading_manual/` : Vide → **UTILISER CCXTClient dès le début**
- ❌ `apps/trading_engine/` : Squelette → **UTILISER CCXTClient dès le début**

### Solution : Service CCXT Centralisé via Redis

**Objectif** : Transformer le `CCXTManager` en **service centralisé** qui :
1. Fonctionne comme processus indépendant (Terminal 5)
2. Maintient les connexions CCXT uniques par `(user_id, broker_id)`
3. Communique avec les autres services via **Redis** (pub/sub)
4. Respecte parfaitement les rate limits CCXT

---

## ARCHITECTURE CIBLE

```ascii
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Terminal 1    │    │   Terminal 2    │    │   Terminal 3    │    │   Terminal 4    │    │   Terminal 5    │
│  Serveur Web    │    │   Heartbeat     │    │ Trading Engine  │    │   Frontend      │    │  CCXT Service   │
│    (Daphne)     │    │                 │    │                 │    │   (Vue.js)      │    │ **NOUVEAU**     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │                       │
         │                       │                       │                       │                       │
         └───────────────────────┼───────────────────────┼───────────────────────┼───────────────────────┤
                                 │                       │                       │                       │
                          ┌─────────────────────────────────────────────────────────────────────────────────┐
                          │                            REDIS PUB/SUB                                        │
                          │  • Channel: ccxt_requests   (Trading Engine → CCXT Service)                    │
                          │  • Channel: ccxt_responses  (CCXT Service → Trading Engine)                    │
                          │  • Channel: heartbeat       (Heartbeat → Trading Engine) [existant]           │
                          │  • Channel: websockets      (Tous → Frontend) [existant]                      │
                          └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## IMPLÉMENTATION DÉTAILLÉE

### ⚠️ IMPORTANT : Modules SANS Modification

**User Account (`apps/brokers`) - AUCUN CHANGEMENT**
- `apps/brokers/models.py` → **GARDER** `get_ccxt_client()` en CCXT direct
- `apps/brokers/views.py` → **GARDER** `test_connection()` en CCXT direct
- **Raison** : Tests ponctuels, pas de problème de rate limits

**Nouveaux Modules - UTILISER CCXTClient**
- `apps/trading_manual/` → **CCXTClient** (à développer)
- `apps/trading_engine/` → **CCXTClient** (à compléter)

### 1. Nouveau Service : CCXT Centralisé

**Fichier** : `backend/apps/core/management/commands/run_ccxt_service.py`

```python
# -*- coding: utf-8 -*-
"""
Service centralisé CCXT - Processus indépendant (Terminal 5)
Gère toutes les connexions CCXT et répond aux requêtes via Redis
"""
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from apps.core.services.ccxt_manager import CCXTManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Service centralisé CCXT - Gère toutes les connexions exchanges'
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.channel_layer = get_channel_layer()
        self.request_handlers = {
            'get_balance': self._handle_get_balance,
            'get_candles': self._handle_get_candles,
            'place_order': self._handle_place_order,
            'preload_brokers': self._handle_preload_brokers,
        }
    
    def handle(self, *args, **options):
        # Gestion arrêt propre
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        self.stdout.write(
            self.style.SUCCESS("✅ CCXT Service centralisé démarré\n")
        )
        
        asyncio.run(self.run_service())
    
    async def run_service(self):
        """Boucle principale du service CCXT"""
        
        # Précharger tous les brokers actifs
        await CCXTManager.preload_all_brokers()
        
        # Écouter les requêtes Redis
        while self.running:
            try:
                # Recevoir requête depuis le channel ccxt_requests
                message = await self.channel_layer.receive('ccxt_requests')
                await self._process_request(message)
                
            except Exception as e:
                logger.error(f"❌ Erreur CCXT Service: {e}")
                await asyncio.sleep(1)
    
    async def _process_request(self, message):
        """Traite une requête CCXT et envoie la réponse"""
        try:
            request_id = message.get('request_id')
            action = message.get('action')
            params = message.get('params', {})
            
            # Exécuter l'action
            if action in self.request_handlers:
                result = await self.request_handlers[action](params)
                response = {
                    'request_id': request_id,
                    'success': True,
                    'data': result
                }
            else:
                response = {
                    'request_id': request_id,
                    'success': False,
                    'error': f'Action inconnue: {action}'
                }
            
            # Envoyer la réponse
            await self.channel_layer.send('ccxt_responses', response)
            
        except Exception as e:
            response = {
                'request_id': message.get('request_id'),
                'success': False,
                'error': str(e)
            }
            await self.channel_layer.send('ccxt_responses', response)
    
    async def _handle_get_balance(self, params):
        """Récupère le solde d'un broker"""
        from apps.brokers.models import Broker
        
        broker_id = params['broker_id']
        broker = await Broker.objects.aget(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        balance = await exchange.fetch_balance()
        return balance
    
    async def _handle_get_candles(self, params):
        """Récupère des bougies OHLCV"""
        from apps.brokers.models import Broker
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        timeframe = params['timeframe']
        limit = params.get('limit', 100)
        
        broker = await Broker.objects.aget(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    
    async def _handle_place_order(self, params):
        """Passe un ordre de trading"""
        from apps.brokers.models import Broker
        
        broker_id = params['broker_id']
        symbol = params['symbol']
        side = params['side']  # 'buy' or 'sell'
        amount = params['amount']
        order_type = params.get('type', 'market')
        price = params.get('price')
        
        broker = await Broker.objects.aget(id=broker_id)
        exchange = await CCXTManager.get_exchange(broker)
        
        if order_type == 'market':
            order = await exchange.create_market_order(symbol, side, amount)
        else:
            order = await exchange.create_limit_order(symbol, side, amount, price)
        
        return order
    
    async def _handle_preload_brokers(self, params):
        """Précharge tous les brokers"""
        return await CCXTManager.preload_all_brokers()
    
    def shutdown(self, signum, frame):
        """Arrêt propre du service"""
        self.stdout.write(
            self.style.WARNING("⚠️ Arrêt CCXT Service...")
        )
        self.running = False
        
        # Fermer toutes les connexions CCXT
        asyncio.create_task(CCXTManager.close_all())
        
        sys.exit(0)
```

### 2. Client CCXT : Interface pour les autres services

**Fichier** : `backend/apps/core/services/ccxt_client.py`

```python
# -*- coding: utf-8 -*-
"""
Client CCXT - Interface pour communiquer avec le service centralisé CCXT
Utilisé par Trading Engine, Trading Manuel, Backtest, etc.
"""
import asyncio
import uuid
import json
import logging
from channels.layers import get_channel_layer
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class CCXTClient:
    """
    Client pour communiquer avec le service CCXT centralisé via Redis
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.pending_requests: Dict[str, asyncio.Future] = {}
    
    async def _send_request(self, action: str, params: Dict) -> Any:
        """Envoie une requête au service CCXT et attend la réponse"""
        request_id = str(uuid.uuid4())
        
        # Créer une Future pour attendre la réponse
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[request_id] = future
        
        # Envoyer la requête
        request = {
            'request_id': request_id,
            'action': action,
            'params': params,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await self.channel_layer.send('ccxt_requests', request)
        
        try:
            # Attendre la réponse (timeout 30s)
            response = await asyncio.wait_for(future, timeout=30.0)
            
            if response['success']:
                return response['data']
            else:
                raise Exception(response['error'])
                
        except asyncio.TimeoutError:
            raise Exception(f"Timeout CCXT request {action}")
        finally:
            # Nettoyer
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
    
    async def handle_response(self, response: Dict):
        """Traite une réponse reçue du service CCXT"""
        request_id = response.get('request_id')
        if request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                future.set_result(response)
    
    async def get_balance(self, broker_id: int) -> Dict:
        """Récupère le solde d'un broker"""
        return await self._send_request('get_balance', {'broker_id': broker_id})
    
    async def get_candles(self, broker_id: int, symbol: str, 
                         timeframe: str, limit: int = 100) -> list:
        """Récupère des bougies OHLCV"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'limit': limit
        }
        return await self._send_request('get_candles', params)
    
    async def place_market_order(self, broker_id: int, symbol: str, 
                                side: str, amount: float) -> Dict:
        """Passe un ordre au marché"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'type': 'market'
        }
        return await self._send_request('place_order', params)
    
    async def place_limit_order(self, broker_id: int, symbol: str, 
                               side: str, amount: float, price: float) -> Dict:
        """Passe un ordre limite"""
        params = {
            'broker_id': broker_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'type': 'limit'
        }
        return await self._send_request('place_order', params)
    
    async def preload_all_brokers(self) -> tuple:
        """Demande le préchargement de tous les brokers"""
        return await self._send_request('preload_brokers', {})
```

### 3. Modification du Trading Engine

**Fichier** : `backend/apps/core/management/commands/run_trading_engine.py`

```python
# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings
from channels.layers import get_channel_layer
import asyncio
import logging
import signal
import sys
from datetime import datetime
from apps.core.services.ccxt_client import CCXTClient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Lance le moteur de trading qui ecoute les signaux du Heartbeat'
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.channel_layer = get_channel_layer()
        self.ccxt_client = CCXTClient()
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Mode test sans execution reelle des trades',
        )
    
    def handle(self, *args, **options):
        self.test_mode = options.get('test', False)
        
        # Gerer l'arret propre
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Trading Engine demarre {'(MODE TEST)' if self.test_mode else ''}\n"
            )
        )
        
        # Lancer la boucle async
        asyncio.run(self.run_engine())
    
    async def run_engine(self):
        """Boucle principale du Trading Engine"""
        
        self.stdout.write(
            self.style.SUCCESS("✅ Connexion au service CCXT centralisé...")
        )
        
        # Écouter les réponses CCXT
        asyncio.create_task(self.listen_ccxt_responses())
        
        # Demander le préchargement des brokers
        try:
            success_count, error_count = await self.ccxt_client.preload_all_brokers()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Brokers préchargés: {success_count} succès, {error_count} erreurs")
            )
        except Exception as e:
            logger.error(f"❌ Erreur préchargement brokers: {e}")
        
        # Boucle principale
        while self.running:
            try:
                # Attendre un signal du Heartbeat
                # TODO: Implémenter l'écoute des signaux Heartbeat
                await asyncio.sleep(1)
                
                # Traiter les signaux (sera implémenté dans Module 7)
                if False:  # Placeholder
                    await self.process_signal({})
                    
            except Exception as e:
                logger.error(f"❌ Erreur Trading Engine: {e}")
                await asyncio.sleep(5)
    
    async def listen_ccxt_responses(self):
        """Écoute les réponses du service CCXT"""
        while self.running:
            try:
                response = await self.channel_layer.receive('ccxt_responses')
                await self.ccxt_client.handle_response(response)
            except Exception as e:
                logger.error(f"❌ Erreur réception réponse CCXT: {e}")
                await asyncio.sleep(1)
    
    async def process_signal(self, signal_data):
        """
        Traite un signal reçu du Heartbeat.
        Utilise maintenant le CCXTClient au lieu du CCXTManager direct.
        """
        timeframe = signal_data.get('timeframe')
        timestamp = signal_data.get('timestamp')
        
        self.stdout.write(f"📊 Signal reçu: {timeframe} à {timestamp}")
        
        # TODO: Module 7 - Utiliser self.ccxt_client au lieu de CCXTManager
        # Exemple:
        # balance = await self.ccxt_client.get_balance(broker_id)
        # candles = await self.ccxt_client.get_candles(broker_id, symbol, timeframe)
        pass
    
    def shutdown(self, signum, frame):
        """Arret propre du service"""
        self.stdout.write(
            self.style.WARNING("\n⚠️ Arrêt du Trading Engine...")
        )
        self.running = False
        sys.exit(0)
```

### 4. IMPORTANT : Coexistence CCXT Direct + Service Centralisé

**STRATÉGIE :**
- ✅ **User Account (`apps/brokers`)** : **GARDER CCXT DIRECT** pour tests ponctuels
- ✅ **Trading Manuel/Engine** : **UTILISER CCXTClient** pour opérations répétées

**Fichier** : `backend/apps/core/services/ccxt_manager.py` (modifié pour service centralisé)

```python
# -*- coding: utf-8 -*-
"""
Gestionnaire singleton CCXT - VERSION SERVICE CENTRALISÉ
Utilisé UNIQUEMENT par le service CCXT centralisé (Terminal 5)
Les autres services doivent utiliser CCXTClient
"""
import ccxt.async_support as ccxt
import asyncio
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class CCXTManager:
    """
    Service singleton CCXT - RÉSERVÉ AU SERVICE CENTRALISÉ
    Toutes les autres applications doivent utiliser CCXTClient
    """
    _instances: Dict[Tuple[int, int], Any] = {}
    _locks: Dict[Tuple[int, int], asyncio.Lock] = {}
    
    @classmethod
    async def get_exchange(cls, broker):
        """
        ATTENTION: Cette méthode n'est utilisable que dans le service CCXT centralisé
        """
        key = (broker.user_id, broker.id)
        
        # Créer un lock si nécessaire
        if key not in cls._locks:
            cls._locks[key] = asyncio.Lock()
        
        async with cls._locks[key]:
            if key not in cls._instances:
                try:
                    # Récupérer la classe d'exchange
                    exchange_class = getattr(ccxt, broker.exchange)
                    
                    # Configuration CCXT
                    config = {
                        'apiKey': broker.decrypt_field(broker.api_key),
                        'secret': broker.decrypt_field(broker.api_secret),
                        'enableRateLimit': True,
                        'rateLimit': 2000,
                        'options': {'defaultType': 'spot'}
                    }
                    
                    # Mot de passe si nécessaire
                    if broker.api_password:
                        config['password'] = broker.decrypt_field(broker.api_password)
                    
                    # Mode testnet
                    if broker.is_testnet:
                        config['options']['sandboxMode'] = True
                    
                    # Créer l'instance
                    exchange = exchange_class(config)
                    
                    # Mode sandbox
                    if broker.is_testnet and hasattr(exchange, 'set_sandbox_mode'):
                        exchange.set_sandbox_mode(True)
                    
                    # Charger les marchés
                    await exchange.load_markets()
                    
                    cls._instances[key] = exchange
                    logger.info(f"✅ CCXT centralisé: Instance créée pour {broker.name}")
                    
                except Exception as e:
                    logger.error(f"❌ CCXT centralisé: Erreur création {broker.name}: {e}")
                    raise
            
        return cls._instances[key]
    
    @classmethod
    async def close_exchange(cls, broker):
        """Ferme une instance CCXT"""
        key = (broker.user_id, broker.id)
        
        if key in cls._instances:
            try:
                exchange = cls._instances[key]
                await exchange.close()
                del cls._instances[key]
                logger.info(f"✅ CCXT centralisé: Instance fermée pour {broker.name}")
            except Exception as e:
                logger.error(f"❌ Erreur fermeture instance CCXT: {e}")
    
    @classmethod
    async def close_all(cls):
        """Ferme toutes les instances CCXT proprement"""
        logger.info(f"🔄 CCXT centralisé: Fermeture de {len(cls._instances)} instances...")
        
        for key, exchange in list(cls._instances.items()):
            try:
                await exchange.close()
                logger.info(f"✅ Instance fermée pour key {key}")
            except Exception as e:
                logger.error(f"❌ Erreur fermeture instance {key}: {e}")
        
        cls._instances.clear()
        cls._locks.clear()
        logger.info("✅ CCXT centralisé: Toutes les instances fermées")
    
    @classmethod
    async def preload_all_brokers(cls):
        """Précharge tous les brokers actifs"""
        from apps.brokers.models import Broker
        
        active_brokers = await Broker.objects.filter(
            is_active=True
        ).select_related('user').aall()
        
        logger.info(f"🔄 CCXT centralisé: Préchargement de {len(active_brokers)} brokers...")
        
        tasks = [cls.get_exchange(broker) for broker in active_brokers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = sum(1 for r in results if isinstance(r, Exception))
        
        logger.info(f"✅ CCXT centralisé: Préchargement terminé - {success_count} succès, {error_count} erreurs")
        
        # Log des erreurs
        for broker, result in zip(active_brokers, results):
            if isinstance(result, Exception):
                logger.error(f"❌ Erreur préchargement {broker.name}: {result}")
        
        return success_count, error_count
```

---

## CHANNELS REDIS : Configuration

**Fichier** : `backend/aristobot/settings.py` (ajout)

```python
# Configuration Channels Redis - Ajout des nouveaux channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Channels dédiés CCXT
CCXT_CHANNELS = {
    'requests': 'ccxt_requests',
    'responses': 'ccxt_responses',
}
```

---

## TESTS & VALIDATION

### 1. Test du Service CCXT

```bash
# Dans backend/
python manage.py run_ccxt_service
```

**Sortie attendue** :
```
✅ CCXT Service centralisé démarré
🔄 CCXT centralisé: Préchargement de X brokers...
✅ CCXT centralisé: Instance créée pour [broker1]
✅ CCXT centralisé: Instance créée pour [broker2]
✅ CCXT centralisé: Préchargement terminé - X succès, Y erreurs
```

### 2. Test du Trading Engine

```bash
# Dans backend/
python manage.py run_trading_engine
```

**Sortie attendue** :
```
✅ Trading Engine demarre
✅ Connexion au service CCXT centralisé...
✅ Brokers préchargés: X succès, Y erreurs
```

### 3. Test de Communication

Créer un script de test `backend/test_ccxt_communication.py` :

```python
# -*- coding: utf-8 -*-
import asyncio
from apps.core.services.ccxt_client import CCXTClient

async def test_ccxt_communication():
    client = CCXTClient()
    
    # Test préchargement
    result = await client.preload_all_brokers()
    print(f"✅ Préchargement: {result}")
    
    # Test récupération balance (remplacer broker_id)
    # balance = await client.get_balance(1)
    # print(f"✅ Balance: {balance}")

if __name__ == '__main__':
    asyncio.run(test_ccxt_communication())
```

---

## NOUVEAUX TERMINAUX DE DÉMARRAGE

L'application nécessite maintenant **5 terminaux** :

```bash
# Terminal 1: Serveur Web
cd backend && daphne aristobot.asgi:application

# Terminal 2: Service Heartbeat  
cd backend && python manage.py run_heartbeat

# Terminal 3: Trading Engine
cd backend && python manage.py run_trading_engine

# Terminal 4: Frontend
cd frontend && npm run dev

# Terminal 5: Service CCXT (NOUVEAU)
cd backend && python manage.py run_ccxt_service
```

---

## CHECKLIST IMPLÉMENTATION

### Phase 1 : Service CCXT Centralisé
- [ ] Créer `run_ccxt_service.py` avec handlers complets
- [ ] Créer `CCXTClient` avec méthodes async
- [ ] Modifier `CCXTManager` pour service centralisé uniquement
- [ ] Configurer channels Redis (`ccxt_requests`, `ccxt_responses`)

### Phase 2 : Modification Trading Engine
- [ ] Remplacer `CCXTManager` par `CCXTClient` dans Trading Engine
- [ ] Ajouter écoute des réponses CCXT
- [ ] Tester communication bidirectionnelle

### Phase 3 : Tests & Validation
- [ ] Tester démarrage service CCXT seul
- [ ] Tester démarrage Trading Engine avec service CCXT
- [ ] Vérifier préchargement des brokers
- [ ] Tester timeout et gestion d'erreurs

### Phase 4 : Documentation
- [ ] Mettre à jour la documentation de démarrage
- [ ] Ajouter le Terminal 5 dans les instructions
- [ ] Documenter les nouveaux channels Redis

---

## POINTS D'ATTENTION

1. **Rate Limits** : Une seule connexion par (user_id, broker_id) garantie
2. **Timeout** : Requêtes CCXT avec timeout 30s
3. **Gestion d'erreur** : Échecs de connexion gracefully handled
4. **Arrêt propre** : Fermeture de toutes les connexions CCXT
5. **Logging** : Traces détaillées pour debugging
6. **Encodage** : UTF-8 obligatoire première ligne

---

## RÉSULTAT ATTENDU

✅ **Coexistence équilibrée** : CCXT direct (tests) + Service centralisé (trading)  
✅ **Rate limits respectés** : Une instance par broker pour les opérations répétées  
✅ **Communication async** : Via Redis pub/sub  
✅ **Rétrocompatibilité** : User Account inchangé  
✅ **Robustesse** : Gestion d'erreurs et timeouts  

**Architecture finale** : 
- **5 processus** indépendants communiquant via Redis
- **Coexistence** : CCXT direct (ponctuel) + centralisé (répétitif)
- **Impact minimal** : Pas de refactoring, que du nouveau code
