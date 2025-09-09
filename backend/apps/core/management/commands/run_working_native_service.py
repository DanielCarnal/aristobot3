# -*- coding: utf-8 -*-
"""
SERVICE NATIF QUI FONCTIONNE - Version simplifiée

Basé sur les tests validés du service minimal.
Remplace le NativeExchangeManager complexe par une version qui MARCHE.
"""

import asyncio
import json
import logging
import signal
import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

class WorkingNativeService:
    """Service natif simplifié qui FONCTIONNE"""
    
    def __init__(self):
        self.running = False
        self.redis_client = None
        self.requests_processed = 0
    
    async def start(self):
        """Démarrage du service"""
        print("[SERVICE DEBUG] Entree dans start()...")
        
        try:
            print("[SERVICE DEBUG] Import redis_fallback...")
            from apps.core.services.redis_fallback import get_redis_client
            print("[SERVICE DEBUG] Import OK")
            
            print("[SERVICE DEBUG] Appel get_redis_client()...")
            self.redis_client = await get_redis_client()
            print("[SERVICE DEBUG] Redis client obtenu")
            
            print("[SERVICE DEBUG] Test ping Redis...")
            await self.redis_client.ping()
            print("[SERVICE] Redis connecte")
            
            # Démarrage
            print("[SERVICE DEBUG] Mise à jour running=True...")
            self.running = True
            print(f"[SERVICE] Service demarre, running={self.running}, ecoute ccxt_requests...")
            
            # Boucle principale
            print("[SERVICE DEBUG] Appel _main_loop()...")
            await self._main_loop()
            print("[SERVICE DEBUG] _main_loop() terminee")
            
        except Exception as e:
            print(f"[SERVICE ERROR] Exception dans start(): {e}")
            print(f"[SERVICE ERROR] Type: {type(e)}")
            import traceback
            print(f"[SERVICE ERROR] Traceback complet:")
            traceback.print_exc()
            await self.stop()
    
    async def stop(self):
        """Arrêt du service"""
        print("[SERVICE] Arret en cours...")
        self.running = False
        
        if self.redis_client:
            await self.redis_client.close()
            print("[SERVICE] Redis ferme")
        
        print("[SERVICE] Arrete proprement")
    
    async def _main_loop(self):
        """Boucle principale d'écoute Redis avec logs détaillés"""
        print(f"[LOOP] Entree boucle principale, running={self.running}")
        
        iteration = 0
        while self.running:
            iteration += 1
            print(f"[LOOP] Iteration {iteration}, running={self.running}")
            
            try:
                # CORRECTION: Utiliser blpop comme Terminal 5
                print("[LOOP] Test blpop bloquant (comme Terminal 5)...")
                result = await self.redis_client.blpop('ccxt_requests', timeout=1)
                print(f"[LOOP] blpop resultat: {result}")
                
                if result:
                    # CORRECTION: Décomposer le tuple comme Terminal 5
                    _, message_json = result
                    print(f"[REQUEST] Requete recue: {message_json}")
                    
                    # Traitement async avec gestion d'erreur
                    task = asyncio.create_task(self._process_request(message_json))
                    self.requests_processed += 1
                    print(f"[STATS] Requetes traitees: {self.requests_processed}")
                    
                    # Vérifier si la tâche a planté (debug)
                    await asyncio.sleep(0.1)  # Laisser temps à la tâche
                    if task.done():
                        try:
                            await task
                            print("[TASK] Traitement OK")
                        except Exception as e:
                            print(f"[TASK ERROR] Exception traitement: {e}")
                            import traceback
                            traceback.print_exc()
                else:
                    # Timeout normal avec blpop
                    print("[LOOP] Timeout blpop (normal)")
                    
            except asyncio.TimeoutError:
                # Timeout normal pour blpop
                print("[LOOP] Timeout asyncio (normal)")
                continue
                
            except Exception as e:
                print(f"[LOOP ERROR] Exception: {e}")
                print(f"[LOOP ERROR] Type: {type(e)}")
                import traceback
                print(f"[LOOP ERROR] Traceback: {traceback.format_exc()}")
                await asyncio.sleep(1)
            
            # Log du statut à chaque 10 itérations
            if iteration % 10 == 0:
                print(f"[LOOP STATUS] Iteration {iteration}, running={self.running}, requests={self.requests_processed}")
        
        print(f"[SERVICE] Sortie boucle principale après {iteration} iterations, running={self.running}")
    
    async def _process_request(self, raw_request):
        """Traite une requête reçue - PRODUCTION"""
        try:
            # Parse JSON
            if isinstance(raw_request, bytes):
                request_str = raw_request.decode()
            else:
                request_str = str(raw_request)
            
            request = json.loads(request_str)
            request_id = request.get('request_id')
            action = request.get('action')
            params = request.get('params', {})
            
            print(f"[PROCESS] Action: {action}, ID: {request_id[:8]}...")
            
            # Traitement selon l'action
            if action == 'get_balance':
                result = await self._handle_get_balance(params)
            elif action == 'place_order':
                result = await self._handle_place_order(params)
            elif action == 'get_markets':
                result = await self._handle_get_markets(params)
            elif action == 'get_ticker':
                result = await self._handle_get_ticker(params)
            else:
                result = {'error': f'Action non supportee: {action}'}
            
            # Réponse via Redis
            response = {
                'request_id': request_id,
                'success': 'error' not in result,
                'data': result if 'error' not in result else None,
                'error': result.get('error')
            }
            
            response_key = f"ccxt_response_{request_id}"
            await self.redis_client.setex(response_key, 30, json.dumps(response))
            print(f"[PROCESS] Reponse envoyee: {request_id[:8]}...")
            
        except Exception as e:
            print(f"[PROCESS ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    async def _handle_get_balance(self, params):
        """Traite get_balance"""
        try:
            broker_id = params.get('broker_id')
            print(f"[BALANCE] Broker ID: {broker_id}")
            
            # Récupération du broker
            from apps.brokers.models import Broker
            from asgiref.sync import sync_to_async
            broker = await sync_to_async(Broker.objects.get)(id=broker_id)
            
            # Client natif
            from apps.core.services.bitget_native_client import BitgetNativeClient
            
            async with BitgetNativeClient(
                api_key=broker.decrypt_field(broker.api_key),
                api_secret=broker.decrypt_field(broker.api_secret),
                api_passphrase=broker.decrypt_field(broker.api_password),
                is_testnet=broker.is_testnet
            ) as client:
                result = await client.get_balance()
                print(f"[BALANCE] Succes: {len(result.get('balances', {}))} devises")
                return result
                
        except Exception as e:
            print(f"[BALANCE ERROR] {e}")
            return {'error': str(e)}
    
    async def _handle_get_markets(self, params):
        """Traite get_markets"""
        try:
            broker_id = params.get('broker_id')
            
            from apps.brokers.models import Broker
            from asgiref.sync import sync_to_async
            broker = await sync_to_async(Broker.objects.get)(id=broker_id)
            
            from apps.core.services.bitget_native_client import BitgetNativeClient
            
            async with BitgetNativeClient(
                api_key=broker.decrypt_field(broker.api_key),
                api_secret=broker.decrypt_field(broker.api_secret),
                api_passphrase=broker.decrypt_field(broker.api_password),
                is_testnet=broker.is_testnet
            ) as client:
                result = await client.get_markets()
                print(f"[MARKETS] Succes: {len(result.get('markets', {}))} symboles")
                return result
                
        except Exception as e:
            print(f"[MARKETS ERROR] {e}")
            return {'error': str(e)}
    
    async def _handle_get_ticker(self, params):
        """Traite get_ticker"""
        try:
            broker_id = params.get('broker_id')
            symbol = params.get('symbol')
            
            from apps.brokers.models import Broker
            from asgiref.sync import sync_to_async
            broker = await sync_to_async(Broker.objects.get)(id=broker_id)
            
            from apps.core.services.bitget_native_client import BitgetNativeClient
            
            async with BitgetNativeClient(
                api_key=broker.decrypt_field(broker.api_key),
                api_secret=broker.decrypt_field(broker.api_secret),
                api_passphrase=broker.decrypt_field(broker.api_password),
                is_testnet=broker.is_testnet
            ) as client:
                result = await client.get_ticker(symbol)
                print(f"[TICKER] Succes: {symbol} = {result.get('price')}")
                return result
                
        except Exception as e:
            print(f"[TICKER ERROR] {e}")
            return {'error': str(e)}
    
    async def _handle_place_order(self, params):
        """Traite place_order"""
        try:
            broker_id = params.get('broker_id')
            symbol = params.get('symbol')
            side = params.get('side')
            amount = params.get('amount')
            order_type = params.get('type', 'market')
            
            print(f"[ORDER] {order_type} {side} {amount} {symbol}")
            
            from apps.brokers.models import Broker
            from asgiref.sync import sync_to_async
            broker = await sync_to_async(Broker.objects.get)(id=broker_id)
            
            from apps.core.services.bitget_native_client import BitgetNativeClient
            
            async with BitgetNativeClient(
                api_key=broker.decrypt_field(broker.api_key),
                api_secret=broker.decrypt_field(broker.api_secret),
                api_passphrase=broker.decrypt_field(broker.api_password),
                is_testnet=broker.is_testnet
            ) as client:
                result = await client.place_order(
                    symbol=symbol,
                    side=side,
                    amount=amount,
                    order_type=order_type,
                    price=params.get('price')
                )
                print(f"[ORDER] Succes: Order ID {result.get('order_id')}")
                return result
                
        except Exception as e:
            print(f"[ORDER ERROR] {e}")
            return {'error': str(e)}


class Command(BaseCommand):
    help = 'Service natif qui fonctionne (version simplifiée)'
    
    def __init__(self):
        super().__init__()
        self.service = None
        self.shutdown_requested = False
    
    def handle(self, *args, **options):
        """Point d'entrée principal"""
        
        print("=" * 60)
        print("SERVICE NATIF QUI FONCTIONNE v1.0")
        print("Version simplifiée basée sur tests validés")
        print("=" * 60)
        
        # Signal handler
        def signal_handler(signum, frame):
            print(f"\n[SIGNAL] Signal {signum} recu, arret...")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Vérifications préalables (reprendre du service complexe)
        if not self._check_prerequisites():
            print("[ERROR] Prerequisites non satisfaits")
            return
        
        try:
            asyncio.run(self._run_service())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[ERROR] Erreur critique: {e}")
        
        print("[OK] Service arrete proprement")
    
    def _check_prerequisites(self):
        """Vérifications de base"""
        try:
            # Redis
            import redis
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            print("[OK] Redis: Connexion OK")
            
            # Database
            from apps.brokers.models import Broker
            broker_count = Broker.objects.filter(is_active=True).count()
            print(f"[OK] Database: {broker_count} brokers actifs")
            
            # Exchanges
            from apps.core.services.base_exchange_client import ExchangeClientFactory
            exchanges = ExchangeClientFactory.list_supported_exchanges()
            print(f"[OK] Exchanges: {exchanges}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Prerequis: {e}")
            return False
    
    async def _run_service(self):
        """Lance le service avec logs détaillés"""
        print("[RUN] Creation WorkingNativeService...")
        self.service = WorkingNativeService()
        
        print("[RUN] Lancement tache service en arriere-plan...")
        # Démarrage en arrière-plan
        service_task = asyncio.create_task(self.service.start())
        
        print(f"[RUN] Service cree, shutdown={self.shutdown_requested}, service.running={self.service.running}")
        print("[INFO] Service demarre, Ctrl+C pour arreter")
        
        # NOUVELLE LOGIQUE: Attendre un peu que le service démarre
        print("[RUN] Attente demarrage service...")
        for i in range(10):  # Attendre max 5 secondes
            await asyncio.sleep(0.5)
            print(f"[RUN] Attente {i+1}/10: running={self.service.running}")
            
            if self.service.running:
                print("[RUN] Service demarre avec succes!")
                break
                
            # Vérifier si la tâche a planté
            if service_task.done():
                print("[RUN] ERREUR: Tache service terminee prematurment!")
                try:
                    await service_task  # Récupérer l'exception
                except Exception as e:
                    print(f"[RUN ERROR] Exception tache service: {e}")
                    import traceback
                    traceback.print_exc()
                return
        
        if not self.service.running:
            print("[RUN] ERREUR: Service n'a pas demarre apres 5s")
            return
        
        # Attente arrêt avec logs détaillés
        try:
            wait_iteration = 0
            while not self.shutdown_requested and self.service.running:
                wait_iteration += 1
                print(f"[WAIT] Iteration {wait_iteration}: shutdown={self.shutdown_requested}, running={self.service.running}")
                
                await asyncio.sleep(1)
                
                # Stats simples
                if self.service.requests_processed > 0:
                    print(f"[STATS] Requetes traitees: {self.service.requests_processed}")
                
                # Log détaillé toutes les 5 secondes
                if wait_iteration % 5 == 0:
                    print(f"[STATUS] Service actif depuis {wait_iteration}s, requests={self.service.requests_processed}")
                
                # Vérifier si la tâche a planté
                if service_task.done():
                    print("[WAIT] ERREUR: Tache service s'est arretee!")
                    try:
                        await service_task  # Récupérer l'exception
                    except Exception as e:
                        print(f"[WAIT ERROR] Exception tache service: {e}")
                        import traceback
                        traceback.print_exc()
                    break
            
            print(f"[WAIT] Sortie boucle attente: shutdown={self.shutdown_requested}, running={self.service.running}")
            
        finally:
            print("[RUN] Arret du service...")
            await self.service.stop()
            if not service_task.done():
                print("[RUN] Annulation tache service...")
                service_task.cancel()
                try:
                    await service_task
                except asyncio.CancelledError:
                    print("[RUN] Tache service annulee")