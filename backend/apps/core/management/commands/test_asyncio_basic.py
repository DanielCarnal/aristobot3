# -*- coding: utf-8 -*-
"""
TEST ASYNCIO DE BASE - Diagnostic du problème fondamental
"""

import asyncio
import signal
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Test asyncio de base'
    
    def __init__(self):
        super().__init__()
        self.shutdown_requested = False
    
    def handle(self, *args, **options):
        """Test asyncio minimal"""
        
        print("=" * 50)
        print("TEST ASYNCIO DE BASE")
        print("=" * 50)
        
        print("[1] Test sans signal handler...")
        try:
            asyncio.run(self._test_without_signals())
            print("[1] SUCCES: Test sans signal OK")
        except Exception as e:
            print(f"[1] ECHEC: {e}")
        
        print("\n[2] Test avec signal handler...")
        try:
            # Signal handler
            def signal_handler(signum, frame):
                print(f"[SIGNAL] Signal {signum} recu")
                self.shutdown_requested = True
            
            signal.signal(signal.SIGINT, signal_handler)
            
            asyncio.run(self._test_with_signals())
            print("[2] SUCCES: Test avec signal OK")
        except Exception as e:
            print(f"[2] ECHEC: {e}")
        
        print("\n[3] Test event loop policy...")
        try:
            # Test policy Windows
            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                print("[POLICY] WindowsProactorEventLoopPolicy detectee")
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                print("[POLICY] Policy mise en place")
            
            asyncio.run(self._test_policy())
            print("[3] SUCCES: Test policy OK")
        except Exception as e:
            print(f"[3] ECHEC: {e}")
        
        print("\n[CONCLUSION] Tests termines")
    
    async def _test_without_signals(self):
        """Test boucle async simple"""
        print("[ASYNC1] Entree boucle sans signals")
        
        for i in range(5):
            print(f"[ASYNC1] Iteration {i+1}/5")
            await asyncio.sleep(0.5)
        
        print("[ASYNC1] Sortie boucle sans signals")
    
    async def _test_with_signals(self):
        """Test avec signal handler"""
        print("[ASYNC2] Entree boucle avec signals")
        
        for i in range(5):
            if self.shutdown_requested:
                print("[ASYNC2] Arret demande par signal")
                break
            
            print(f"[ASYNC2] Iteration {i+1}/5")
            await asyncio.sleep(0.5)
        
        print("[ASYNC2] Sortie boucle avec signals")
    
    async def _test_policy(self):
        """Test avec policy Windows"""
        print("[ASYNC3] Entree boucle avec policy")
        
        # Test création tâche
        async def sub_task():
            print("[TASK] Sous-tache demarre")
            await asyncio.sleep(1)
            print("[TASK] Sous-tache termine")
        
        task = asyncio.create_task(sub_task())
        
        for i in range(3):
            print(f"[ASYNC3] Iteration {i+1}/3")
            await asyncio.sleep(0.5)
        
        await task
        print("[ASYNC3] Sortie boucle avec policy")