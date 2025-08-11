# -*- coding: utf-8 -*-
"""
Gestionnaire singleton pour les instances CCXT asynchrones.
Une instance par (user_id, broker_id) pour respecter les rate limits.
"""
import ccxt.async_support as ccxt
import asyncio
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class CCXTManager:
    """
    Service singleton pour gérer les instances CCXT asynchrones.
    Une seule instance par broker/user pour éviter les rate limits.
    """
    _instances: Dict[Tuple[int, int], Any] = {}
    _locks: Dict[Tuple[int, int], asyncio.Lock] = {}
    
    @classmethod
    async def get_exchange(cls, broker):
        """
        Retourne une instance CCXT asynchrone pour un broker donné.
        Charge automatiquement les marchés à la première utilisation.
        
        Args:
            broker: Instance du modèle Broker
            
        Returns:
            Instance CCXT configurée et prête
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
                    logger.info(f"✅ Instance CCXT créée et marchés chargés pour {broker.name} (user: {broker.user.username})")
                    
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
                logger.info(f"Instance CCXT fermée pour {broker.name}")
            except Exception as e:
                logger.error(f"Erreur fermeture instance CCXT: {e}")
    
    @classmethod
    async def close_all(cls):
        """Ferme toutes les instances CCXT proprement."""
        for key, exchange in list(cls._instances.items()):
            try:
                await exchange.close()
                logger.info(f"Instance fermée pour key {key}")
            except Exception as e:
                logger.error(f"Erreur fermeture instance {key}: {e}")
        
        cls._instances.clear()
        cls._locks.clear()
        logger.info("Toutes les instances CCXT ont été fermées")
    
    @classmethod
    async def preload_all_brokers(cls):
        """
        Précharge tous les brokers actifs au démarrage du Trading Engine.
        Utile pour minimiser la latence lors des signaux.
        """
        from apps.brokers.models import Broker
        
        active_brokers = Broker.objects.filter(is_active=True).select_related('user')
        
        logger.info(f"Préchargement de {active_brokers.count()} brokers...")
        
        tasks = []
        for broker in active_brokers:
            tasks.append(cls.get_exchange(broker))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = sum(1 for r in results if isinstance(r, Exception))
        
        logger.info(f"Préchargement terminé: {success_count} succès, {error_count} erreurs")
        
        # Log les erreurs
        for broker, result in zip(active_brokers, results):
            if isinstance(result, Exception):
                logger.error(f"Erreur préchargement {broker.name}: {result}")
        
        return success_count, error_count
