# -*- coding: utf-8 -*-
"""
SERVICE NATIVE SIMPLE - Version minimale qui FONCTIONNE

Test basique pour valider que l'architecture native marche
sans toute la complexité du NativeExchangeManager.
"""

import asyncio
import json
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Service natif minimal pour tests'
    
    def __init__(self):
        super().__init__()
        self.running = False
    
    def handle(self, *args, **options):
        """Point d'entree principal"""
        
        try:
            print("[TEST] Demarrage service minimal...")
            print("[TEST] Test Redis...")
            
            # Test Redis simple
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            print("[TEST] Redis OK")
            
            print("[TEST] Test brokers...")
            from apps.brokers.models import Broker
            broker_count = Broker.objects.filter(is_active=True).count()
            print(f"[TEST] {broker_count} brokers actifs")
            
            print("[TEST] Test client natif...")
            from apps.core.services.bitget_native_client import BitgetNativeClient
            print("[TEST] Import BitgetNativeClient OK")
            
            print("[TEST] Test factory...")
            from apps.core.services.base_exchange_client import ExchangeClientFactory
            exchanges = ExchangeClientFactory.list_supported_exchanges()
            print(f"[TEST] Exchanges supportes: {exchanges}")
            
            print("[TEST] Lancement boucle async...")
            asyncio.run(self._test_async_loop())
            
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
    
    async def _test_async_loop(self):
        """Test boucle async simple"""
        try:
            print("[ASYNC] Entree boucle async")
            
            # Test connexion Redis async
            from apps.core.services.redis_fallback import get_redis_client
            redis_client = await get_redis_client()
            await redis_client.ping()
            print("[ASYNC] Redis async OK")
            
            self.running = True
            print(f"[ASYNC] running = {self.running}")
            
            # Boucle de test simple (10 secondes)
            for i in range(10):
                print(f"[ASYNC] Loop iteration {i+1}/10")
                await asyncio.sleep(1)
                
                if not self.running:
                    print("[ASYNC] Arret demande")
                    break
            
            print("[ASYNC] Fin boucle async")
            await redis_client.close()
            
        except Exception as e:
            print(f"[ASYNC ERROR] Exception: {e}")
            import traceback
            print(f"[ASYNC ERROR] Traceback: {traceback.format_exc()}")