# -*- coding: utf-8 -*-
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