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
        
        # Créer un lock si nécessaire pour éviter les créations multiples
        if key not in cls._locks:
            cls._locks[key] = asyncio.Lock()
        
        async with cls._locks[key]:
            if key not in cls._instances:
                try:
                    # Récupérer la classe d'exchange
                    exchange_class = getattr(ccxt, broker.exchange)
                    
                    # Configuration de base
                    config = {
                        'apiKey': broker.decrypt_field(broker.api_key),
                        'secret': broker.decrypt_field(broker.api_secret),
                        'enableRateLimit': True,
                        'rateLimit': 2000,
                        'options': {
                            'defaultType': 'spot',
                        }
                    }
                    
                    # Ajouter le mot de passe si nécessaire (OKX, KuCoin, etc.)
                    if broker.api_password:
                        config['password'] = broker.decrypt_field(broker.api_password)
                    
                    # Mode testnet si activé
                    if broker.is_testnet:
                        config['options']['sandboxMode'] = True
                    
                    # Gestion des sous-comptes
                    if broker.subaccount_name:
                        if broker.exchange == 'binance':
                            config['options']['defaultSubAccount'] = broker.subaccount_name
                        elif broker.exchange == 'okx':
                            config['headers'] = {'x-simulated-trading': '1'} if broker.is_testnet else {}
                    
                    # Créer l'instance
                    exchange = exchange_class(config)
                    
                    # Activer le mode sandbox si nécessaire
                    if broker.is_testnet and hasattr(exchange, 'set_sandbox_mode'):
                        exchange.set_sandbox_mode(True)
                    
                    # Charger les marchés (une seule fois)
                    await exchange.load_markets()
                    
                    cls._instances[key] = exchange
                    logger.info(f"✅ CCXT centralisé: Instance créée pour {broker.name}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur création instance CCXT pour {broker.name}: {e}")
                    raise
            
        return cls._instances[key]
    
    @classmethod
    async def close_exchange(cls, broker):
        """
        Ferme proprement une instance CCXT.
        
        Args:
            broker: Instance du modèle Broker
        """
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
        
        from django.db import models
        from asgiref.sync import sync_to_async
        
        # Utiliser sync_to_async pour convertir la requête Django
        active_brokers = await sync_to_async(list)(
            Broker.objects.filter(is_active=True).select_related('user')
        )
        
        import os
        import sys
        import time
        import random
        import io
        import logging
        
        print(f"\n🔄 CCXT centralisé: Préchargement de {len(active_brokers)} brokers...")
        
        if len(active_brokers) == 0:
            print("   (Aucun broker actif configuré)")
        else:
            # Clear screen et afficher header
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"🔄 CCXT centralisé: Préchargement de {len(active_brokers)} brokers...")
            print(f"   {'Exchange':<15} {'Broker':<20} {'Status':<10} {'Stream Sample':<20} {'Time':<8}")
            print(f"   {'-'*15} {'-'*20} {'-'*10} {'-'*20} {'-'*8}")
        
        # Traiter les brokers un par un avec affichage
        success_count = 0
        error_count = 0
        last_clear = time.time()
        
        # Buffer pour capturer les logs CCXT
        class StreamCapture:
            def __init__(self):
                self.chars = []
                self.last_sample = ""
            
            def capture_from_string(self, text):
                # Extraire les caractères intéressants du texte
                interesting_chars = [c for c in text if c.isalnum() or c in '/:.-_']
                self.chars.extend(interesting_chars[-50:])  # Garder les 50 derniers
                
            def get_random_sample(self):
                if len(self.chars) >= 20:
                    sample = ''.join(random.sample(self.chars, min(20, len(self.chars))))
                    return sample[:20]
                elif len(self.chars) > 0:
                    # Compléter avec des caractères existants
                    sample = ''.join(self.chars)
                    while len(sample) < 20 and self.chars:
                        sample += random.choice(self.chars)
                    return sample[:20]
                return "waiting for data..."
        
        for i, broker in enumerate(active_brokers):
            # Clear screen toutes les 5 secondes
            if time.time() - last_clear > 5:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"🔄 CCXT centralisé: Préchargement de {len(active_brokers)} brokers...")
                print(f"   {'Exchange':<15} {'Broker':<20} {'Status':<10} {'Stream Sample':<20} {'Time':<8}")
                print(f"   {'-'*15} {'-'*20} {'-'*10} {'-'*20} {'-'*8}")
                # Réafficher les brokers déjà traités
                for j in range(i):
                    prev_broker = active_brokers[j]
                    status = "✅ OK" if j < success_count else "❌ ERR" 
                    elapsed = f"{3+(j*2)}s"  # Temps estimé
                    print(f"   {prev_broker.exchange:<15} {prev_broker.name:<20} {status:<10} {'completed':<20} {elapsed:<8}")
                last_clear = time.time()
            
            try:
                stream_capture = StreamCapture()
                start_time = time.time()
                
                # Initialiser l'affichage
                print(f"   {broker.exchange:<15} {broker.name:<20} {'Loading':<10} {'starting...':<20} {'0s':<8}", end="", flush=True)
                
                # Simuler la capture du stream pendant le chargement
                async def update_display():
                    while True:
                        elapsed = int(time.time() - start_time)
                        # Simuler des caractères du stream basés sur l'exchange et les opérations
                        fake_stream_data = f"loading {broker.exchange} markets {broker.name} symbols API fetch"
                        stream_capture.capture_from_string(fake_stream_data)
                        sample = stream_capture.get_random_sample()
                        print(f"\r   {broker.exchange:<15} {broker.name:<20} {'Loading':<10} {sample:<20} {elapsed}s", end="", flush=True)
                        await asyncio.sleep(1)
                
                # Lancer l'affichage en parallèle du vrai chargement
                display_task = asyncio.create_task(update_display())
                
                try:
                    # Vrai chargement CCXT
                    await cls.get_exchange(broker)
                    display_task.cancel()
                    
                    elapsed = int(time.time() - start_time)
                    print(f"\r   {broker.exchange:<15} {broker.name:<20} {'✅ OK':<10} {'completed':<20} {elapsed}s")
                    success_count += 1
                except Exception as load_error:
                    display_task.cancel()
                    elapsed = int(time.time() - start_time)
                    raise load_error
                    
            except Exception as e:
                elapsed = int(time.time() - start_time) if 'start_time' in locals() else 0
                print(f"\r   {broker.exchange:<15} {broker.name:<20} {'❌ ERREUR':<10} {'failed':<20} {elapsed}s")
                logger.error(f"❌ Erreur préchargement {broker.name}: {e}")
                error_count += 1
        
        print(f"\n✅ CCXT centralisé: Préchargement terminé - {success_count} succès, {error_count} erreurs")
        
        return success_count, error_count