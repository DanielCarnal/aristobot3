# -*- coding: utf-8 -*-
"""
Fallback Redis pour compatibilité avec versions anciennes
"""
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class RedisFallback:
    """Client Redis avec fallback sync→async"""
    
    def __init__(self, host='localhost', port=6379, decode_responses=True):
        import redis
        self.redis_sync = redis.Redis(host=host, port=port, decode_responses=decode_responses)
        
    async def ping(self):
        """Test connexion async"""
        return await asyncio.to_thread(self.redis_sync.ping)
    
    async def rpush(self, key, value):
        """Push async dans une liste"""
        return await asyncio.to_thread(self.redis_sync.rpush, key, value)
    
    async def blpop(self, keys, timeout=1):
        """Pop bloquant async"""
        result = await asyncio.to_thread(self.redis_sync.blpop, keys, timeout)
        return result
    
    async def get(self, key):
        """Get async"""
        return await asyncio.to_thread(self.redis_sync.get, key)
    
    async def setex(self, key, time, value):
        """Set avec expiration async"""
        return await asyncio.to_thread(self.redis_sync.setex, key, time, value)
    
    async def delete(self, key):
        """Delete async"""
        return await asyncio.to_thread(self.redis_sync.delete, key)
    
    async def llen(self, key):
        """Length liste async"""
        return await asyncio.to_thread(self.redis_sync.llen, key)
    
    async def close(self):
        """Fermer connexion"""
        await asyncio.to_thread(self.redis_sync.close)

async def get_redis_client():
    """Factory pour client Redis avec fallback"""
    try:
        # Essayer redis.asyncio d'abord
        import redis.asyncio as redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await client.ping()
        logger.info("✅ Utilisation redis.asyncio")
        return client
    except ImportError:
        logger.info("📦 redis.asyncio non disponible, utilisation fallback")
        return RedisFallback()
    except Exception as e:
        logger.warning(f"⚠️ Erreur redis.asyncio: {e}, utilisation fallback")
        return RedisFallback()