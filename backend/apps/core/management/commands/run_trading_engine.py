# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings
from channels.layers import get_channel_layer
import asyncio
import logging
import signal
import sys
from datetime import datetime
from apps.core.services.exchange_client import ExchangeClient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Lance le moteur de trading qui ecoute les signaux du Heartbeat'
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.channel_layer = get_channel_layer()
        # 🔒 SÉCURITÉ: Trading Engine est multi-user - ExchangeClient créé par stratégie utilisateur
        # self.ccxt_client sera remplacé par des clients spécifiques dans process_signal()
        
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
        
        # TODO MODULE 7: Préchargement brokers sera fait par stratégie utilisateur
        # Le Trading Engine n'a plus de client global - chaque stratégie aura son ExchangeClient
        self.stdout.write(
            self.style.SUCCESS("✅ Trading Engine multi-user prêt (Module 7: stratégies utilisateur)")
        )
        
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
                # TODO MODULE 7: Écoute des signaux Heartbeat et traitement des stratégies
                # Chaque stratégie aura son propre ExchangeClient(user_id=strategy.user_id)
                await asyncio.sleep(0.1)  # Placeholder
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
        """Arrêt propre du service"""
        self.stdout.write(
            self.style.WARNING("\n⚠️ Arrêt du Trading Engine...")
        )
        self.running = False
        sys.exit(0)