# -*- coding: utf-8 -*-
"""
NATIVE EXCHANGE MANAGER - Remplace le service CCXT centralisé (Terminal 5)

🎯 OBJECTIF: Service centralisé pour gérer tous les clients exchanges natifs
Remplace Terminal 5 (run_ccxt_service.py) avec une architecture native optimisée

📋 ARCHITECTURE NATIVE:
- NativeExchangeManager: Gestionnaire central des clients exchanges
- Pooling intelligent des connexions par exchange type
- Communication Redis identique (ccxt_requests/ccxt_responses)
- Interface 100% compatible avec CCXTClient existant

🚀 AVANTAGES vs SERVICE CCXT:
- Performance: ~3x plus rapide (clients natifs directs)
- Mémoire: Moins de RAM (pas de CCXT abstraction layer)
- Rate limiting: Gestion native par exchange
- Extensibilité: Support facile nouveaux exchanges

🔧 FONCTIONNEMENT:
1. Écoute Redis ccxt_requests (comme Terminal 5 existant)
2. Route vers le client native approprié (Bitget, Binance, etc.)
3. Retourne résultats via Redis ccxt_responses
4. Compatible avec TradingService, TradingManual, Webhooks existants
"""

import asyncio
import json
import logging
import uuid
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

# Django imports
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

# Aristobot imports  
from apps.brokers.models import Broker
from .redis_fallback import get_redis_client
from .base_exchange_client import BaseExchangeClient, ExchangeClientFactory

# Import des clients natifs pour enregistrement automatique
from .bitget_native_client import BitgetNativeClient
from .binance_native_client import BinanceNativeClient
from .kraken_native_client import KrakenNativeClient

logger = logging.getLogger(__name__)
User = get_user_model()

# 🔍 VERSION DE DEBUG POUR CLAUDE - LOGS GARANTIS AU DÉMARRAGE
TERMINAL5_VERSION = "2.5.3-FIX-REDIS-JSON-SERIALIZATION"
print(f"[STARTUP CLAUDE] ===== TERMINAL 5 VERSION {TERMINAL5_VERSION} =====")
logger.info(f"🔍 TERMINAL 5 CHARGÉ - VERSION: {TERMINAL5_VERSION}")
print(f"[STARTUP CLAUDE] Fichier: {__file__}")
print(f"[STARTUP CLAUDE] Modifications Claude actives: create_and_execute_trade debug logs")


class NativeExchangeManager:
    """
    🏛️ GESTIONNAIRE CENTRAL EXCHANGES NATIFS
    
    Remplace le service CCXT centralisé avec une architecture native optimisée.
    
    🎯 FONCTIONNALITÉS:
    - Gestion pool de clients natifs par exchange type
    - Communication Redis compatible Terminal 5
    - Rate limiting intelligent par exchange
    - Hot-reload des credentials sans redémarrage
    - Monitoring et statistiques avancées
    
    🔧 PATTERN DE POOLING:
    - Un client par type d'exchange (bitget, binance, etc.)
    - Injection dynamique des credentials par requête
    - Réutilisation optimale des connexions HTTP
    - Cache intelligent des contraintes de marché
    
    📊 ENDPOINTS SUPPORTÉS (compatible CCXTClient):
    - get_balance, get_markets, get_ticker, get_tickers
    - place_order, cancel_order, edit_order  
    - fetch_open_orders, fetch_closed_orders
    - preload_brokers (optimisé natif)
    """
    
    def __init__(self):
        self.running = False
        self.redis_client = None
        
        # Pool de clients natives par exchange
        self._exchange_pools: Dict[str, BaseExchangeClient] = {}
        
        # Cache des brokers actifs
        self._brokers_cache: Dict[int, Dict] = {}
        self._brokers_cache_ttl = 300  # 5 minutes
        self._brokers_cache_timestamp = 0
        
        # Statistiques de monitoring
        self.stats = {
            'requests_processed': 0,
            'requests_failed': 0,
            'requests_by_action': defaultdict(int),
            'avg_response_time': 0,
            'start_time': datetime.utcnow()
        }
        
        # Configuration
        self.redis_timeout = 120  # 2 minutes timeout
        self.max_concurrent_requests = 50
    
    async def start(self):
        """
        🚀 DÉMARRAGE DU SERVICE
        
        Initialise Redis, précharge les brokers actifs, démarre la boucle d'écoute.
        """
        if self.running:
            return
        
        logger.info("[START] Demarrage NativeExchangeManager...")
        
        try:
            # Connexion Redis
            print("[MANAGER DEBUG] Connexion Redis...")
            self.redis_client = await get_redis_client()
            await self.redis_client.ping()
            print("[MANAGER DEBUG] Redis OK")
            logger.info("[OK] Connexion Redis etablie")
            
            # Préchargement des brokers actifs
            print("[MANAGER DEBUG] Preload brokers...")
            await self._preload_active_brokers()
            print("[MANAGER DEBUG] Preload OK")
            
            # Démarrage de la boucle d'écoute
            print("[MANAGER DEBUG] Set running=True...")
            self.running = True
            self.stats['start_time'] = datetime.utcnow()
            print(f"[MANAGER DEBUG] Running={self.running}")
            
            logger.info("[OK] NativeExchangeManager demarre avec succes")
            print("[MANAGER DEBUG] Lancement _main_loop()...")
            
            # Lancement de la boucle principale
            logger.info("[DEBUG] Lancement _main_loop()...")
            await self._main_loop()
            print("[MANAGER DEBUG] _main_loop() terminee")
            logger.info("[DEBUG] _main_loop() terminee normalement")
            
        except Exception as e:
            logger.error(f"[ERR] Erreur demarrage NativeExchangeManager: {e}")
            logger.error(f"[ERR] Type exception: {type(e)}")
            import traceback
            logger.error(f"[ERR] Traceback complet: {traceback.format_exc()}")
            await self.stop()
            raise
    
    async def stop(self):
        """
        🛑 ARRÊT PROPRE DU SERVICE
        """
        if not self.running:
            return
        
        logger.info("[STOP] Arret NativeExchangeManager...")
        self.running = False
        
        # Fermeture des clients exchanges
        for exchange_name, client in self._exchange_pools.items():
            try:
                await client._close_session()
                logger.info(f"[OK] Client {exchange_name} ferme")
            except Exception as e:
                logger.warning(f"[WARN] Erreur fermeture client {exchange_name}: {e}")
        
        # Fermeture Redis
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("[OK] Connexion Redis fermee")
            except Exception as e:
                logger.warning(f"[WARN] Erreur fermeture Redis: {e}")
        
        logger.info("[OK] NativeExchangeManager arrete")
    
    async def _main_loop(self):
        """
        🔄 BOUCLE PRINCIPALE D'ÉCOUTE REDIS - CORRIGÉE SELON RUN_WORKING_NATIVE_SERVICE
        
        Écoute les requêtes ccxt_requests et traite en parallèle.
        Compatible 100% avec le format Terminal 5 existant.
        """
        print("[MANAGER] Ecoute des requetes ccxt_requests...")
        logger.info("[INFO] Ecoute des requetes ccxt_requests...")
        
        iteration = 0
        while self.running:
            iteration += 1
            try:
                # CORRECTION : Utiliser blpop comme Terminal 5 et run_working_native_service
                result = await self.redis_client.blpop('ccxt_requests', timeout=1)
                
                if result:
                    # CORRECTION : Décomposer le tuple comme Terminal 5
                    _, message_json = result
                    print(f"[MANAGER] Requete recue: {message_json}")
                    
                    # Traitement async avec gestion d'erreur améliorée
                    task = asyncio.create_task(self._process_request(message_json))
                    self.stats['requests_processed'] += 1
                    
                    # Vérifier si la tâche a planté (debug)
                    await asyncio.sleep(0.1)  # Laisser temps à la tâche
                    if task.done():
                        try:
                            await task
                            print(f"[MANAGER] Traitement OK (iteration {iteration})")
                        except Exception as e:
                            print(f"[MANAGER ERROR] Exception traitement: {e}")
                            import traceback
                            traceback.print_exc()
                else:
                    # Timeout normal avec blpop
                    if iteration % 50 == 0:  # Log toutes les 50 itérations (50s)
                        print(f"[MANAGER] Iteration {iteration}: en attente de requetes...")
                    
            except asyncio.TimeoutError:
                # Timeout normal pour blpop
                continue
            except Exception as e:
                print(f"[MANAGER ERROR] Erreur boucle principale: {e}")
                logger.error(f"[ERR] Erreur boucle principale: {e}")
                import traceback
                print(f"[MANAGER ERROR] Traceback: {traceback.format_exc()}")
                logger.error(f"[ERR] Traceback: {traceback.format_exc()}")
                await asyncio.sleep(1)  # Pause avant retry
        
        print(f"[MANAGER] Sortie de _main_loop() après {iteration} iterations")
        logger.info("[INFO] Sortie de _main_loop(), service arrete")
    
    async def _process_request(self, raw_request):
        """
        ⚙️ TRAITEMENT D'UNE REQUÊTE - CORRIGÉ SELON RUN_WORKING_NATIVE_SERVICE
        
        Parse la requête, route vers le bon client, retourne la réponse via Redis.
        """
        request_start_time = time.time()
        
        try:
            # Parse JSON CORRIGÉ
            if isinstance(raw_request, bytes):
                request_str = raw_request.decode()
            else:
                request_str = str(raw_request)
            
            request_data = json.loads(request_str)
            request_id = request_data.get('request_id')
            action = request_data.get('action')
            params = request_data.get('params', {})
            user_id = request_data.get('user_id')  # 🔒 NOUVEAU: Extraction user_id sécurité
            
            print(f"[MANAGER] Traitement: {action} - {request_id[:8]}... - User: {user_id}")
            
            # Mise à jour des statistiques
            self.stats['requests_by_action'][action] += 1
            
            # Traitement de l'action avec vérification sécurité
            result = await self._handle_action(action, params, user_id)
            
            # Calcul du temps de réponse
            response_time = (time.time() - request_start_time) * 1000
            self._update_avg_response_time(response_time)
            
            # CORRECTION : Structure de réponse simplifiée selon Terminal 5
            if isinstance(result, dict) and 'success' in result:
                # Déjà formaté par _handle_action
                response = {
                    'request_id': request_id,
                    'success': result['success'],
                    'data': result.get('data'),
                    'error': result.get('error'),
                    'processing_time_ms': response_time
                }
            else:
                # Format simple pour compatibilité
                response = {
                    'request_id': request_id,
                    'success': True,
                    'data': result,
                    'error': None,
                    'processing_time_ms': response_time
                }
            
            # CORRECTION : Envoi via Redis avec setex comme Terminal 5
            response_key = f"ccxt_response_{request_id}"
            await self.redis_client.setex(response_key, 30, json.dumps(response))
            
            print(f"[MANAGER] Reponse envoyee: {action} - {request_id[:8]}... ({response_time:.0f}ms)")
            
        except Exception as e:
            print(f"[MANAGER ERROR] Erreur traitement: {e}")
            logger.error(f"[ERR] Erreur traitement requête: {e}")
            self.stats['requests_failed'] += 1
            
            # Réponse d'erreur
            if 'request_data' in locals() and request_data and request_data.get('request_id'):
                error_response = {
                    'request_id': request_data['request_id'],
                    'success': False,
                    'data': None,
                    'error': str(e)
                }
                
                try:
                    response_key = f"ccxt_response_{request_data['request_id']}"
                    await self.redis_client.setex(response_key, 30, json.dumps(error_response))
                except:
                    pass  # Échec silencieux si Redis indisponible
            
            import traceback
            print(f"[MANAGER ERROR] Traceback: {traceback.format_exc()}")
            traceback.print_exc()
    
    async def _handle_action(self, action: str, params: Dict, user_id: int = None) -> Dict:
        """
        🎯 ROUTAGE DES ACTIONS VERS LES CLIENTS NATIFS + SÉCURITÉ MULTI-TENANT
        
        Route chaque action vers la méthode appropriée du client exchange.
        NOUVEAU: Vérifie que le broker appartient à l'utilisateur demandeur.
        """
        print(f"[DEBUG CLAUDE] _handle_action ENTRY: action={action}")
        try:
            logger.info(f"🔧 _handle_action: START action={action}, user_id={user_id}")
        except Exception as e:
            print(f"[DEBUG CLAUDE] LOGGER EXCEPTION: {e}")
        print(f"[DEBUG CLAUDE] After logger.info, getting broker_id...")
        broker_id = params.get('broker_id')
        print(f"[DEBUG CLAUDE] Extracted broker_id: {broker_id}")
        
        if not broker_id:
            print(f"[DEBUG CLAUDE] ERREUR: broker_id manquant")
            return {
                'success': False,
                'error': 'broker_id requis'
            }
        
        print(f"[DEBUG CLAUDE] broker_id OK, checking security...")
        
        # 🔒 SÉCURITÉ: Vérifier ownership du broker AVANT de récupérer le client
        if user_id:
            print(f"[DEBUG CLAUDE] Security check: user_id={user_id}, getting broker_info...")
            broker_info = await self._get_broker_info(broker_id)
            print(f"[DEBUG CLAUDE] broker_info retrieved: {broker_info}")
            if not broker_info:
                print(f"[DEBUG CLAUDE] ERREUR: broker_info non trouvé")
                return {
                    'success': False,
                    'error': f'Broker {broker_id} non trouvé'
                }
            
            # CRITIQUE: Vérifier que le broker appartient à cet utilisateur
            if broker_info.get('user_id') != user_id:
                print(f"[DEBUG CLAUDE] ERREUR: Accès non autorisé user_id mismatch")
                logger.warning(f"🚨 TENTATIVE ACCÈS NON AUTORISÉ: User {user_id} vers Broker {broker_id} (propriétaire: {broker_info.get('user_id')})")
                return {
                    'success': False,
                    'error': f'Accès refusé: broker {broker_id} n\'appartient pas à l\'utilisateur'
                }
            print(f"[DEBUG CLAUDE] Security check OK: broker belongs to user")
        else:
            # AVERTISSEMENT: Requête sans user_id (rétrocompatibilité temporaire)
            print(f"[DEBUG CLAUDE] WARNING: No user_id provided, using retrocompatibility")
            logger.warning(f"⚠️ SÉCURITÉ: Requête {action} sans user_id pour broker {broker_id} - Rétrocompatibilité temporaire")
        
        # Récupération du client exchange pour ce broker (après vérification sécurité)
        print(f"[DEBUG CLAUDE] Getting exchange client for broker {broker_id}...")
        client = await self._get_exchange_client(broker_id)
        print(f"[DEBUG CLAUDE] Client retrieved: {client}")
        if not client:
            print(f"[DEBUG CLAUDE] ERREUR: Client exchange indisponible")
            return {
                'success': False,
                'error': f'Client exchange indisponible pour broker {broker_id}'
            }
        
        print(f"[DEBUG CLAUDE] Client OK, starting action routing for: {action}")
        try:
            # Routage vers les méthodes natives
            if action == 'get_balance':
                result = await client.get_balance()
                return {'success': result['success'], 'data': result.get('balances'), 'error': result.get('error')}
            
            elif action == 'get_markets':
                result = await client.get_markets()
                return {'success': result['success'], 'data': result.get('markets'), 'error': result.get('error')}
            
            elif action == 'get_ticker':
                symbol = params.get('symbol')
                if not symbol:
                    return {'success': False, 'error': 'symbol requis'}
                result = await client.get_ticker(symbol)
                return {'success': result['success'], 'data': result, 'error': result.get('error')}
            
            elif action == 'fetch_tickers':
                # Support batch tickers pour Bitget
                symbols = params.get('symbols', [])
                if hasattr(client, 'get_tickers_batch'):
                    result = await client.get_tickers_batch(symbols)
                    return {'success': result['success'], 'data': result.get('tickers'), 'error': result.get('error')}
                else:
                    # Fallback: récupération individuelle
                    tickers = {}
                    for symbol in symbols:
                        ticker_result = await client.get_ticker(symbol)
                        if ticker_result['success']:
                            tickers[client.normalize_symbol(symbol)] = ticker_result
                    return {'success': True, 'data': tickers}
            
            elif action == 'place_order':
                symbol = params.get('symbol')
                side = params.get('side')
                amount = params.get('amount')
                order_type = params.get('type', 'market')
                price = params.get('price')
                
                if not all([symbol, side, amount]):
                    return {'success': False, 'error': 'symbol, side, amount requis'}
                
                # Extraction des paramètres avancés
                kwargs = {}
                for key in ['stop_loss_price', 'take_profit_price', 'force', 'client_order_id']:
                    if key in params:
                        kwargs[key] = params[key]
                
                # 🔥 PASSAGE D'ORDRE avec INTERFACE UNIFIÉE
                result = await client.place_order(symbol, side, amount, order_type, price, **kwargs)
                
                # 🎯 ENRICHISSEMENT RÉPONSE avec INTERFACE UNIFIÉE (sans créer Trade - fait par TradingService)
                if result['success'] and result.get('data'):
                    try:
                        # Enrichir les données avec l'interface unifiée COMPLÈTE
                        standardized_order = client._standardize_complete_order_response(result['data'])
                        
                        # Ajouter TOUS les champs de l'interface unifiée à la réponse
                        result['data'].update(standardized_order)
                        
                        logger.info(f"✅ Réponse enrichie avec {len(standardized_order)} champs interface unifiée")
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur enrichissement interface unifiée: {e}")
                        # Ne pas faire échouer l'ordre si l'enrichissement échoue
                        result['enrichment_error'] = str(e)
                
                return {'success': result['success'], 'data': result, 'error': result.get('error')}
            
            elif action == 'cancel_order':
                symbol = params.get('symbol')
                order_id = params.get('order_id')
                
                if not all([symbol, order_id]):
                    return {'success': False, 'error': 'symbol, order_id requis'}
                
                result = await client.cancel_order(symbol, order_id)
                return {'success': result['success'], 'data': result, 'error': result.get('error')}
            
            elif action == 'edit_order':
                symbol = params.get('symbol')
                order_id = params.get('order_id')
                
                if not all([symbol, order_id]):
                    return {'success': False, 'error': 'symbol, order_id requis'}
                
                # Vérifier si le client supporte la modification native
                if hasattr(client, 'modify_order'):
                    new_price = params.get('price')
                    new_amount = params.get('amount')
                    result = await client.modify_order(symbol, order_id, new_price, new_amount)
                    return {'success': result['success'], 'data': result, 'error': result.get('error')}
                else:
                    return {'success': False, 'error': 'Modification d\'ordre non supportée par cet exchange'}
            
            elif action == 'fetch_open_orders':
                # 🆕 SUPPORT COMPLET PARAMÈTRES BITGET OPEN ORDERS
                symbol = params.get('symbol')
                
                # 📋 NOUVEAUX PARAMÈTRES ÉTENDUS BITGET
                start_time = params.get('start_time') or params.get('startTime')
                end_time = params.get('end_time') or params.get('endTime') 
                id_less_than = params.get('id_less_than') or params.get('idLessThan')
                limit = params.get('limit', 100)
                order_id = params.get('order_id') or params.get('orderId')
                tpsl_type = params.get('tpsl_type') or params.get('tpslType')
                request_time = params.get('request_time') or params.get('requestTime')
                receive_window = params.get('receive_window') or params.get('receiveWindow')
                
                # Sécuriser conversion limit
                try:
                    limit = int(limit)
                except (ValueError, TypeError):
                    limit = 100
                
                # Appel avec TOUS les paramètres (compatibilité BitgetNativeClient étendu)
                result = await client.get_open_orders(
                    symbol=symbol,
                    start_time=start_time,
                    end_time=end_time,
                    id_less_than=id_less_than,
                    limit=limit,
                    order_id=order_id,
                    tpsl_type=tpsl_type,
                    request_time=request_time,
                    receive_window=receive_window
                )
                return {'success': result['success'], 'data': result.get('orders'), 'error': result.get('error')}
            
            elif action == 'fetch_closed_orders':
                # 🆕 SUPPORT COMPLET PARAMÈTRES BITGET HISTORY ORDERS
                symbol = params.get('symbol')
                
                # 📋 NOUVEAUX PARAMÈTRES ÉTENDUS BITGET
                start_time = params.get('start_time') or params.get('startTime')
                end_time = params.get('end_time') or params.get('endTime')
                id_less_than = params.get('id_less_than') or params.get('idLessThan')
                limit = params.get('limit', 100)
                order_id = params.get('order_id') or params.get('orderId')
                tpsl_type = params.get('tpsl_type') or params.get('tpslType')
                request_time = params.get('request_time') or params.get('requestTime')
                receive_window = params.get('receive_window') or params.get('receiveWindow')
                
                # Sécuriser conversion limit
                try:
                    limit = int(limit)
                except (ValueError, TypeError):
                    limit = 100
                
                # Appel avec TOUS les paramètres (compatibilité BitgetNativeClient étendu)
                result = await client.get_order_history(
                    symbol=symbol,
                    start_time=start_time,
                    end_time=end_time,
                    id_less_than=id_less_than,
                    limit=limit,
                    order_id=order_id,
                    tpsl_type=tpsl_type,
                    request_time=request_time,
                    receive_window=receive_window
                )
                return {'success': result['success'], 'data': result.get('orders'), 'error': result.get('error')}
            
            elif action == 'get_order_info':
                # 🆕 NOUVEAU ENDPOINT ORDRE SPÉCIFIQUE
                order_id = params.get('order_id') or params.get('orderId')
                client_oid = params.get('client_oid') or params.get('clientOid')
                request_time = params.get('request_time') or params.get('requestTime')
                receive_window = params.get('receive_window') or params.get('receiveWindow')
                
                # Validation: soit order_id soit client_oid requis
                if not order_id and not client_oid:
                    return {'success': False, 'error': 'order_id ou client_oid requis'}
                
                # Appel du client natif avec support get_order_info
                if hasattr(client, 'get_order_info'):
                    result = await client.get_order_info(
                        order_id=order_id,
                        client_oid=client_oid,
                        request_time=request_time,
                        receive_window=receive_window
                    )
                    return {'success': result['success'], 'data': result.get('order'), 'error': result.get('error')}
                else:
                    return {'success': False, 'error': 'get_order_info non supporté par cet exchange'}
            
            elif action == 'preload_brokers':
                # Rechargement des brokers actifs
                await self._preload_active_brokers()
                broker_count = len(self._brokers_cache)
                return {'success': True, 'data': {'loaded_brokers': broker_count}}
            
            elif action == 'test_connection':
                # Test connexion API keys pour User Account
                result = await self._handle_test_connection(params)
                return result
            
            elif action == 'load_markets':
                # Chargement marchés en arrière-plan pour User Account
                result = await self._handle_load_markets(params)
                return result
            
            elif action == 'create_and_execute_trade':
                # 🔥 NOUVELLE ACTION: Création ET exécution Trade par Terminal 5
                print(f"[DEBUG CLAUDE] ROUTING: Found create_and_execute_trade action!")
                logger.info(f"🔥 _handle_action: Routage vers _handle_create_and_execute_trade - user_id={user_id}")
                print(f"[DEBUG CLAUDE] About to call _handle_create_and_execute_trade...")
                result = await self._handle_create_and_execute_trade(params, user_id)
                print(f"[DEBUG CLAUDE] _handle_create_and_execute_trade returned: {result}")
                logger.info(f"🔥 _handle_action: Retour de _handle_create_and_execute_trade - success={result.get('success')}")
                return result
            
            else:
                return {'success': False, 'error': f'Action inconnue: {action}'}
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement action {action}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_exchange_client(self, broker_id: int) -> Optional[BaseExchangeClient]:
        """
        🔌 RÉCUPÉRATION CLIENT EXCHANGE POUR UN BROKER
        
        Récupère ou crée le client exchange approprié avec injection des credentials.
        """
        try:
            # Récupération des infos broker depuis cache ou DB
            broker_info = await self._get_broker_info(broker_id)
            if not broker_info:
                logger.error(f"❌ Broker {broker_id} non trouvé")
                return None
            
            exchange_name = broker_info['exchange'].lower()
            
            # Récupération ou création du client depuis le pool
            if exchange_name not in self._exchange_pools:
                # Création du client pour ce type d'exchange
                try:
                    client = ExchangeClientFactory.create_client(
                        exchange_name=exchange_name,
                        api_key=broker_info['api_key'],
                        api_secret=broker_info['api_secret'],
                        api_passphrase=broker_info.get('api_password'),  # Optionnel
                        is_testnet=broker_info.get('is_testnet', False)
                    )
                    
                    # Ajout au pool
                    self._exchange_pools[exchange_name] = client
                    logger.info(f"🆕 Client {exchange_name} créé et ajouté au pool")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur création client {exchange_name}: {e}")
                    return None
            
            # Récupération du client depuis le pool
            client = self._exchange_pools[exchange_name]
            
            # Injection des credentials pour ce broker spécifique
            # (Pattern optimisé: un client par exchange type, credentials injectés à la demande)
            client.api_key = broker_info['api_key']
            client.api_secret = broker_info['api_secret']
            if broker_info.get('api_password'):
                client.api_passphrase = broker_info['api_password']
            client.is_testnet = broker_info.get('is_testnet', False)
            
            return client
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération client pour broker {broker_id}: {e}")
            return None
    
    async def _get_broker_info(self, broker_id: int) -> Optional[Dict]:
        """
        📋 RÉCUPÉRATION INFOS BROKER AVEC CACHE
        
        Récupère les informations du broker depuis le cache ou la DB.
        """
        # Vérifier le cache TTL
        if (time.time() - self._brokers_cache_timestamp > self._brokers_cache_ttl or
            broker_id not in self._brokers_cache):
            
            # Rechargement depuis DB
            await self._refresh_broker_cache(broker_id)
        
        return self._brokers_cache.get(broker_id)
    
    async def _refresh_broker_cache(self, broker_id: int):
        """
        🔄 RAFRAÎCHISSEMENT CACHE BROKER
        """
        try:
            broker = await sync_to_async(Broker.objects.select_related('user').get)(id=broker_id)
            
            self._brokers_cache[broker_id] = {
                'id': broker.id,
                'name': broker.name,
                'exchange': broker.exchange,
                'api_key': broker.decrypt_field(broker.api_key),
                'api_secret': broker.decrypt_field(broker.api_secret),
                'api_password': broker.decrypt_field(broker.api_password) if broker.api_password else None,
                'is_testnet': broker.is_testnet,
                'user_id': broker.user_id
            }
            
            logger.debug(f"🔄 Cache broker {broker_id} rafraîchi")
            
        except Exception as e:
            logger.error(f"❌ Erreur rafraîchissement cache broker {broker_id}: {e}")
    
    async def _preload_active_brokers(self):
        """
        ⚡ PRÉCHARGEMENT DES BROKERS ACTIFS
        
        Charge tous les brokers actifs en cache au démarrage.
        """
        try:
            logger.info("⚡ Préchargement des brokers actifs...")
            
            # Récupération de tous les brokers actifs
            brokers = await sync_to_async(list)(
                Broker.objects.select_related('user').filter(is_active=True)
            )
            
            loaded_count = 0
            for broker in brokers:
                try:
                    self._brokers_cache[broker.id] = {
                        'id': broker.id,
                        'name': broker.name,
                        'exchange': broker.exchange,
                        'api_key': broker.decrypt_field(broker.api_key),
                        'api_secret': broker.decrypt_field(broker.api_secret),
                        'api_password': broker.decrypt_field(broker.api_password) if broker.api_password else None,
                        'is_testnet': broker.is_testnet,
                        'user_id': broker.user_id
                    }
                    loaded_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur chargement broker {broker.id}: {e}")
            
            self._brokers_cache_timestamp = time.time()
            logger.info(f"✅ Préchargement terminé: {loaded_count} brokers chargés")
            
        except Exception as e:
            logger.error(f"❌ Erreur préchargement brokers: {e}")
    
    async def _handle_test_connection(self, params: Dict) -> Dict:
        """
        🔌 HANDLER TEST CONNEXION - POUR USER ACCOUNT
        
        Teste la connexion API keys d'un broker via client natif.
        Utilisé par User Account pour valider les credentials.
        """
        broker_id = params.get('broker_id')
        if not broker_id:
            return {'success': False, 'error': 'broker_id requis'}
        
        logger.info(f"🔌 Test connexion broker {broker_id}")
        
        try:
            # Récupération du client exchange (création temporaire si nécessaire)
            client = await self._get_exchange_client(broker_id)
            if not client:
                return {
                    'success': False, 
                    'error': f'Impossible de créer client pour broker {broker_id}'
                }
            
            # Test connexion via balance (minimal)
            balance_result = await client.get_balance()
            
            if balance_result['success']:
                # Extraction d'un échantillon de balances pour confirmation
                balances = balance_result.get('balances', {})
                sample_balances = {}
                
                # Prendre les 3 premières balances non nulles
                count = 0
                for asset, balance_info in balances.items():
                    if count >= 3:
                        break
                    if balance_info.get('total', 0) > 0:
                        sample_balances[asset] = {
                            'free': balance_info.get('free', 0),
                            'total': balance_info.get('total', 0)
                        }
                        count += 1
                
                # Déclencher chargement marchés en arrière-plan si connexion OK
                asyncio.create_task(self._load_markets_for_broker(broker_id))
                
                logger.info(f"✅ Test connexion réussi pour broker {broker_id}")
                return {
                    'success': True,
                    'connected': True,
                    'balance_sample': sample_balances,
                    'markets_loading': True
                }
            else:
                logger.warning(f"❌ Test connexion échoué pour broker {broker_id}: {balance_result.get('error')}")
                return {
                    'success': True,  # Pas d'erreur système
                    'connected': False,
                    'error': balance_result.get('error', 'Connexion échouée')
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur test connexion broker {broker_id}: {e}")
            return {
                'success': True,  # Pas d'erreur système Redis
                'connected': False,
                'error': str(e)
            }
    
    async def _handle_load_markets(self, params: Dict) -> Dict:
        """
        📊 HANDLER CHARGEMENT MARCHÉS - POUR USER ACCOUNT
        
        Lance le chargement des marchés en arrière-plan pour un broker.
        Utilisé par User Account bouton "[MAJ Paires]".
        """
        broker_id = params.get('broker_id')
        if not broker_id:
            return {'success': False, 'error': 'broker_id requis'}
        
        logger.info(f"🔄 Chargement manuel marchés broker {broker_id}")
        
        try:
            # Lancer chargement en arrière-plan
            asyncio.create_task(self._load_markets_for_broker(broker_id))
            
            return {
                'success': True,
                'message': 'Chargement des marchés démarré en arrière-plan',
                'loading': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage chargement marchés broker {broker_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _load_markets_for_broker(self, broker_id: int):
        """
        📊 CHARGEMENT MARCHÉS EN ARRIÈRE-PLAN
        
        Charge les marchés pour un broker spécifique avec notifications WebSocket.
        Appelé par test_connection (auto) et load_markets (manuel).
        """
        logger.info(f"📊 Début chargement marchés broker {broker_id}")
        
        try:
            # Récupération du client exchange
            client = await self._get_exchange_client(broker_id)
            if not client:
                await self._notify_markets_error(broker_id, "Client exchange indisponible")
                return
            
            # Récupération info broker pour notifications
            broker_info = await self._get_broker_info(broker_id)
            if not broker_info:
                await self._notify_markets_error(broker_id, "Informations broker non trouvées")
                return
            
            # Récupération des marchés via client natif
            logger.info(f"📊 Récupération marchés {broker_info['exchange']}...")
            markets_result = await client.get_markets()
            
            if not markets_result['success']:
                await self._notify_markets_error(broker_id, markets_result.get('error', 'Erreur récupération marchés'))
                return
            
            markets = markets_result.get('markets', {})
            logger.info(f"📊 {len(markets)} marchés récupérés pour {broker_info['exchange']}")
            
            # Sauvegarde en DB
            await self._save_markets_to_db(broker_info['exchange'], markets)
            
            # Notification succès
            await self._notify_markets_loaded(broker_id, len(markets), broker_info['exchange'])
            
            logger.info(f"✅ Chargement marchés terminé pour broker {broker_id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement marchés broker {broker_id}: {e}")
            await self._notify_markets_error(broker_id, str(e))
    
    async def _save_markets_to_db(self, exchange_name: str, markets: Dict):
        """
        💾 SAUVEGARDE MARCHÉS EN BASE DE DONNÉES
        
        Sauvegarde les marchés dans la table ExchangeSymbol partagée.
        """
        try:
            from apps.brokers.models import ExchangeSymbol
            
            @sync_to_async
            def save_markets_sync():
                # Supprimer anciens marchés pour cet exchange
                deleted_count = ExchangeSymbol.objects.filter(exchange=exchange_name).delete()[0]
                logger.info(f"💾 {deleted_count} anciens marchés supprimés pour {exchange_name}")
                
                # Créer nouveaux marchés
                symbols_to_create = []
                for symbol, market_info in markets.items():
                    symbols_to_create.append(ExchangeSymbol(
                        exchange=exchange_name,
                        symbol=symbol,
                        base_asset=market_info.get('base', ''),
                        quote_asset=market_info.get('quote', ''),
                        is_active=market_info.get('active', True),
                        market_type=market_info.get('type', 'spot'),
                        price_precision=market_info.get('precision', {}).get('price', 8),
                        amount_precision=market_info.get('precision', {}).get('amount', 8),
                        min_amount=market_info.get('limits', {}).get('amount', {}).get('min', 0),
                        max_amount=market_info.get('limits', {}).get('amount', {}).get('max')
                    ))
                
                # Bulk create par batches de 500
                created_count = 0
                for i in range(0, len(symbols_to_create), 500):
                    batch = symbols_to_create[i:i+500]
                    ExchangeSymbol.objects.bulk_create(batch)
                    created_count += len(batch)
                
                return created_count
            
            count = await save_markets_sync()
            logger.info(f"💾 {count} marchés sauvegardés en DB pour {exchange_name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde marchés {exchange_name}: {e}")
            raise
    
    async def _notify_markets_loaded(self, broker_id: int, market_count: int, exchange_name: str):
        """
        📢 NOTIFICATION MARCHÉS CHARGÉS VIA WEBSOCKET
        
        Notifie User Account que les marchés sont chargés avec succès.
        """
        try:
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if channel_layer:
                await channel_layer.group_send(
                    "user_account_updates",
                    {
                        'type': 'markets_loaded',
                        'broker_id': broker_id,
                        'exchange_name': exchange_name,
                        'market_count': market_count,
                        'status': 'success',
                        'timestamp': int(time.time() * 1000)
                    }
                )
                
                logger.info(f"📢 Notification envoyée: {market_count} marchés chargés pour {exchange_name} (broker {broker_id})")
            
        except Exception as e:
            logger.error(f"❌ Erreur notification marchés chargés: {e}")
    
    async def _notify_markets_error(self, broker_id: int, error_message: str):
        """
        📢 NOTIFICATION ERREUR CHARGEMENT MARCHÉS
        
        Notifie User Account d'une erreur de chargement des marchés.
        """
        try:
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if channel_layer:
                await channel_layer.group_send(
                    "user_account_updates",
                    {
                        'type': 'markets_error',
                        'broker_id': broker_id,
                        'error': error_message,
                        'status': 'error',
                        'timestamp': int(time.time() * 1000)
                    }
                )
                
                logger.warning(f"📢 Notification erreur envoyée pour broker {broker_id}: {error_message}")
            
        except Exception as e:
            logger.error(f"❌ Erreur notification erreur marchés: {e}")
    
    def _update_avg_response_time(self, response_time: float):
        """
        📊 MISE À JOUR TEMPS DE RÉPONSE MOYEN
        """
        current_avg = self.stats['avg_response_time']
        total_requests = self.stats['requests_processed']
        
        if total_requests == 1:
            self.stats['avg_response_time'] = response_time
        else:
            # Moyenne mobile pondérée
            self.stats['avg_response_time'] = (current_avg * 0.9) + (response_time * 0.1)
    
    async def _create_complete_trade_record(
        self, 
        broker_data: Dict, 
        user_id: int, 
        exchange_response: Dict,
        original_params: Dict,
        client: BaseExchangeClient
    ) -> Optional['Trade']:
        """
        🏛️ CRÉATION TRADE RECORD COMPLET - INTERFACE UNIFIÉE
        
        Utilise l'interface unifiée pour créer un Trade record avec TOUS les champs
        disponibles depuis l'exchange native (Bitget, Binance, Kraken).
        
        Args:
            broker_data: Données du broker depuis cache
            user_id: ID utilisateur pour multi-tenant
            exchange_response: Réponse complète de l'exchange
            original_params: Paramètres originaux de la requête
            client: Client exchange natif (avec interface unifiée)
            
        Returns:
            Trade: Record créé ou None si erreur
        """
        try:
            # Import dynamique pour éviter circular imports
            from apps.trading_manual.models import Trade
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # Récupération async des objets Django
            user = await sync_to_async(User.objects.get)(id=user_id)
            broker = await sync_to_async(Broker.objects.get)(id=broker_data['id'])
            
            # 🎯 STANDARDISATION COMPLÈTE VIA INTERFACE UNIFIÉE
            # Utiliser la méthode standardisée qui appelle toutes les méthodes abstraites
            standardized_order = client._standardize_complete_order_response(exchange_response)
            
            # 🏗️ CONSTRUCTION TRADE RECORD COMPLET
            trade_data = {
                # === CHAMPS CORE ARISTOBOT ===
                'user': user,
                'broker': broker,
                'trade_type': 'manual',  # Terminal 5 gère principalement trading manuel
                'source': 'trading_manual',
                
                # === DÉTAILS ORDRE STANDARDISÉS ===
                'symbol': standardized_order.get('symbol'),
                'side': standardized_order.get('side'),
                'order_type': standardized_order.get('type'),
                'quantity': standardized_order.get('amount', 0),
                'price': standardized_order.get('price'),
                'total_value': standardized_order.get('quote_volume', 0),
                
                # === RÉSULTATS EXÉCUTION ===
                'status': self._map_order_status_to_trade(standardized_order.get('status')),
                'filled_quantity': standardized_order.get('filled', 0),
                'filled_price': standardized_order.get('price_avg') or standardized_order.get('price'),
                
                # === IDENTIFIANTS EXCHANGE ===
                'exchange_order_id': standardized_order.get('order_id'),
                'exchange_client_order_id': standardized_order.get('client_order_id'),
                'exchange_order_status': standardized_order.get('status'),
                'exchange_user_id': standardized_order.get('user_id'),
                
                # === CHAMPS SPÉCIALISÉS INTERFACE UNIFIÉE ===
                'quote_volume': standardized_order.get('quote_volume'),
                'amount': standardized_order.get('base_volume'),
                'enter_point_source': standardized_order.get('enter_point_source', 'API'),
                'order_source': standardized_order.get('order_source', 'normal'),
                'cancel_reason': standardized_order.get('cancel_reason'),
                
                # === TP/SL AVANCÉS ===
                'preset_take_profit_price': standardized_order.get('preset_take_profit_price'),
                'preset_stop_loss_price': standardized_order.get('preset_stop_loss_price'),
                'trigger_price': standardized_order.get('trigger_price'),
                'tpsl_type': standardized_order.get('tpsl_type', 'normal'),
                
                # === FRAIS ET TIMING ===
                'fee_detail': standardized_order.get('fee_detail'),
                'update_time': self._parse_timestamp(standardized_order.get('updated_at')),
                
                # === PARAMÈTRES ORIGINAUX ===
                'stop_loss_price': original_params.get('stop_loss_price'),
                'take_profit_price': original_params.get('take_profit_price'),
                'force': original_params.get('force'),
                
                # === MÉTADONNÉES COMPLÈTES ===
                'ordre_existant': f"By Terminal 5 ({client.exchange_name})",
                'exchange_raw_data': {
                    'original_exchange_response': exchange_response,
                    'standardized_response': standardized_order,
                    'specialized_fields': standardized_order.get('specialized_fields', {}),
                    'terminal5_metadata': {
                        'exchange_type': client.exchange_name,
                        'interface_version': 'unified_v1',
                        'creation_timestamp': datetime.utcnow().isoformat(),
                        'original_params': original_params
                    }
                }
            }
            
            # Calculer les frais depuis fee_detail si disponible
            if standardized_order.get('fee_detail') and isinstance(standardized_order['fee_detail'], dict):
                trade_data['fees'] = standardized_order['fee_detail'].get('total_fee', 0)
            
            # 💾 CRÉATION ASYNC DU TRADE
            trade = await sync_to_async(Trade.objects.create)(**trade_data)
            
            logger.info(
                f"✅ Trade record complet créé: ID={trade.id}, "
                f"exchange={client.exchange_name}, "
                f"ordre_id={standardized_order.get('order_id')}, "
                f"champs_captures={len([k for k, v in trade_data.items() if v is not None])}"
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"❌ Erreur _create_complete_trade_record: {e}")
            return None
    
    def _map_order_status_to_trade(self, order_status: str) -> str:
        """
        🔄 MAPPING STATUT ORDRE VERS STATUT TRADE
        """
        status_mapping = {
            'open': 'pending',
            'partial': 'pending', 
            'closed': 'filled',
            'filled': 'filled',
            'canceled': 'cancelled',
            'cancelled': 'cancelled',
            'rejected': 'failed',
            'expired': 'failed'
        }
        return status_mapping.get(order_status, 'pending')
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        🕒 PARSING TIMESTAMP VERS DATETIME
        """
        if not timestamp_str:
            return None
        try:
            # Support format ISO
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    async def _handle_create_and_execute_trade(self, params: Dict, user_id: int) -> Dict:
        """
        🔥 NOUVELLE MÉTHODE: Terminal 5 devient MAÎTRE D'ŒUVRE des Trades
        
        Crée ET exécute un Trade complet avec TOUTES les données d'exchange.
        Remplace la logique de Trading Manuel pour une gestion centralisée.
        
        Architecture: Trading Manuel → Terminal 5 → DB (source de vérité unique)
        """
        logger.info(f"🔥 Terminal 5: Création et exécution Trade pour user {user_id} - VERSION 2.1 (Fix Thread Safety)")
        logger.info(f"🔍 DEBUG Terminal 5: _handle_create_and_execute_trade START - params keys: {list(params.keys())}")
        
        try:
            # Validation des paramètres obligatoires
            required_fields = ['broker_id', 'symbol', 'side', 'order_type', 'quantity']
            missing_fields = [field for field in required_fields if not params.get(field)]
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Champs obligatoires manquants: {", ".join(missing_fields)}'
                }
            
            broker_id = params['broker_id']
            
            # 🔒 SÉCURITÉ: Vérifier que le broker appartient à l'utilisateur
            broker_info = await self._get_broker_info(broker_id)
            if not broker_info or broker_info.get('user_id') != user_id:
                logger.warning(f"🚨 Accès refusé: User {user_id} vers Broker {broker_id}")
                return {
                    'success': False,
                    'error': f'Accès refusé: broker {broker_id} n\'appartient pas à l\'utilisateur'
                }
            
            # 📊 ÉTAPE 1: Créer le Trade en DB avec status 'pending'
            logger.info(f"📊 Terminal 5: Création Trade en DB...")
            
            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=user_id)
            broker = await sync_to_async(Broker.objects.get)(id=broker_id)
            
            from apps.trading_manual.models import Trade
            
            # Création Trade avec TOUS les champs disponibles dans le modèle
            trade_data = {
                'user': user,
                'broker': broker,
                'trade_type': params.get('trade_type', 'manual'),
                'source': params.get('source', 'trading_manual'),
                'symbol': params['symbol'],
                'side': params['side'],
                'order_type': params['order_type'],
                'quantity': params['quantity'],
                'price': params.get('price'),
                'total_value': params.get('total_value'),
                # Ordres avancés
                'stop_loss_price': params.get('stop_loss_price'),
                'take_profit_price': params.get('take_profit_price'),
                'trigger_price': params.get('trigger_price'),
                # Traçabilité (utiliser ordre_existant, pas demandeur qui n'existe pas)
                'ordre_existant': params.get('ordre_existant', f"By Terminal 5 - {params.get('demandeur', 'Unknown')}"),
                'status': 'pending'
            }
            
            trade = await sync_to_async(Trade.objects.create)(**trade_data)
            logger.info(f"✅ Terminal 5: Trade {trade.id} créé en DB")
            
            # 🚀 ÉTAPE 2: Exécuter l'ordre via client exchange natif
            logger.info(f"🚀 Terminal 5: Exécution ordre via client natif...")
            
            client = await self._get_exchange_client(broker_id)
            if not client:
                # Mettre à jour le Trade avec l'erreur
                trade.status = 'error'
                trade.error_message = f'Client exchange indisponible pour broker {broker_id}'
                await sync_to_async(trade.save)()
                
                return {
                    'success': False,
                    'error': f'Client exchange indisponible pour broker {broker_id}',
                    'trade_id': trade.id
                }
            
            # Paramètres pour l'ordre avec mapping Bitget correct
            order_params = {
                'symbol': params['symbol'],
                'side': params['side'],
                'type': params['order_type'],
                'price': params.get('price')
            }
            
            # 🔧 CORRECTION BITGET: Market Buy utilise total_value (USDT), pas quantity (base)
            if params['order_type'] == 'market' and params['side'] == 'buy':
                # Market Buy: amount = montant en USDT (quote currency)
                order_params['amount'] = params['total_value']
                logger.info(f"🔧 Market Buy LINK: amount={params['total_value']} USDT")
            else:
                # Market Sell, Limit: amount = quantité en LINK (base currency)  
                order_params['amount'] = params['quantity']
                logger.info(f"🔧 {params['order_type']} {params['side']}: amount={params['quantity']} LINK")
            
            # Ajouter paramètres avancés
            for key in ['stop_loss_price', 'take_profit_price', 'client_order_id']:
                if params.get(key):
                    order_params[key] = params[key]
            
            # Exécution de l'ordre
            order_result = await client.place_order(**order_params)
            
            # 🔍 DEBUG: Examiner la structure complète de order_result
            logger.info(f"🔍 DEBUG order_result complet: success={order_result.get('success')}, keys={list(order_result.keys())}")
            
            # 📝 ÉTAPE 3: Enrichir le Trade avec les données d'exchange
            if order_result['success']:
                logger.info(f"📝 Terminal 5: Enrichissement Trade avec données exchange...")
                
                # 🔧 CORRECTION: order_result est déjà standardisé par place_order()
                # Ne pas re-standardiser, utiliser directement les données disponibles
                try:
                    # Pour un ordre market: status="pending" -> ordre placé mais peut être immédiatement exécuté
                    trade_status = 'executed' if order_result.get('status') in ['filled', 'executed'] else 'pending'
                    
                    update_fields = {
                        'status': trade_status,
                        'exchange_order_id': order_result.get('order_id'),
                        'exchange_client_order_id': order_result.get('client_order_id'),
                        'exchange_order_status': order_result.get('status'),  # Statut brut exchange
                        'filled_quantity': order_result.get('filled_amount', 0),
                        # Calculer quantity totale si remaining_amount disponible
                        'quantity': order_result.get('remaining_amount') + order_result.get('filled_amount', 0) if order_result.get('remaining_amount') else trade.quantity,
                    }
                    
                    # Appliquer les mises à jour
                    for field, value in update_fields.items():
                        if hasattr(trade, field) and value is not None:
                            setattr(trade, field, value)
                    
                    await sync_to_async(trade.save)()
                    
                    logger.info(f"✅ Terminal 5: Trade {trade.id} enrichi avec {len(update_fields)} champs (success=True)")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur enrichissement Trade: {e}")
                    import traceback
                    traceback.print_exc()
                    # Trade exécuté mais enrichissement partiellement échoué
                    trade.status = 'executed'
                    trade.error_message = f'Ordre exécuté, enrichissement partiel: {str(e)}'
                    await sync_to_async(trade.save)()
                
                # 🔧 FIX THREAD SAFETY: Supprimer gestion manuelle connexion DB 
                # Django gère automatiquement les connexions et transactions async
                # La gestion manuelle entre threads cause des erreurs DatabaseWrapper
                logger.info(f"💾 Terminal 5: Trade {trade.id} sauvé - Django gère auto les connexions async")
                
                # Retourner le Trade créé et exécuté
                logger.info(f"🎯 Terminal 5: SUCCESS create_and_execute_trade - Trade {trade.id} - Retour success=True")
                return {
                    'success': True,
                    'data': {
                        'trade_id': trade.id,
                        'status': trade.status,
                        'exchange_order_id': trade.exchange_order_id,
                        'message': 'Trade créé et exécuté avec succès par Terminal 5'
                    },
                    'trade_id': trade.id  # 🔧 FIX: Retourner trade_id au lieu de l'objet Trade (Redis JSON incompatible)
                }
            
            else:
                # Ordre échoué - mettre à jour le Trade avec erreur détaillée
                # 🔍 DEBUG: Examiner la structure complète de order_result
                logger.error(f"🔍 DEBUG order_result complet: {order_result}")
                
                # Récupération intelligente de l'erreur
                error_msg = None
                if 'error' in order_result and order_result['error']:
                    error_msg = order_result['error']
                elif 'message' in order_result:
                    error_msg = order_result['message']
                elif 'msg' in order_result:
                    error_msg = order_result['msg']
                else:
                    # Fallback avec détails de debugging
                    error_msg = f"Ordre échoué - Debug: success={order_result.get('success')}, keys={list(order_result.keys())}"
                
                trade.status = 'error'
                trade.error_message = error_msg
                await sync_to_async(trade.save)()
                
                logger.error(f"❌ Terminal 5: Ordre échoué pour Trade {trade.id}: {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'trade_id': trade.id  # 🔧 FIX: Trade ID seulement, pas l'objet Trade
                }
                
        except Exception as e:
            logger.error(f"❌ Terminal 5: Erreur critique create_and_execute_trade: {e}")
            import traceback
            traceback.print_exc()
            
            # 🔍 DEBUG: Log exception détaillée
            logger.error(f"🔍 DEBUG Exception create_and_execute_trade: type={type(e).__name__}, message={str(e)}")
            
            return {
                'success': False,
                'error': f'Erreur inconnue Terminal 5'  # Message standardisé pour debugging
            }

    def get_stats(self) -> Dict:
        """
        📈 RÉCUPÉRATION STATISTIQUES DE MONITORING
        """
        uptime = datetime.utcnow() - self.stats['start_time']
        
        return {
            'running': self.running,
            'uptime_seconds': uptime.total_seconds(),
            'requests_processed': self.stats['requests_processed'],
            'requests_failed': self.stats['requests_failed'],
            'success_rate': (
                (self.stats['requests_processed'] - self.stats['requests_failed']) / 
                max(self.stats['requests_processed'], 1) * 100
            ),
            'avg_response_time_ms': round(self.stats['avg_response_time'], 2),
            'requests_by_action': dict(self.stats['requests_by_action']),
            'active_exchanges': list(self._exchange_pools.keys()),
            'cached_brokers': len(self._brokers_cache)
        }


# Instance globale pour le service
_native_exchange_manager_instance = None


def get_native_exchange_manager() -> NativeExchangeManager:
    """
    Récupère l'instance globale du NativeExchangeManager
    """
    global _native_exchange_manager_instance
    if _native_exchange_manager_instance is None:
        _native_exchange_manager_instance = NativeExchangeManager()
    return _native_exchange_manager_instance