# -*- coding: utf-8 -*-
"""
SERVICE NATIVE EXCHANGE - REMPLACE TERMINAL 5

🎯 OBJECTIF: Service centralisé native remplaçant run_ccxt_service.py
Utilise l'architecture native (BitgetNativeClient + NativeExchangeManager)

📋 MIGRATION TERMINAL 5:
- Interface identique: écoute ccxt_requests → répond ccxt_responses
- Performance: ~3x plus rapide que CCXT
- Extensibilité: Support facile nouveaux exchanges natifs
- Monitoring: Statistiques avancées temps réel

🚀 DÉMARRAGE:
  python manage.py run_native_exchange_service

🔧 FONCTIONNALITÉS:
- Gestion pool clients natifs par exchange type
- Hot-reload credentials sans redémarrage
- Rate limiting optimisé par exchange
- Monitoring et logs détaillés
- Graceful shutdown avec CTRL+C

Compatible 100% avec:
- TradingService (apps/trading_manual)
- Trading Engine (apps/trading_engine) 
- Backtest (apps/backtest)
- Webhooks (apps/webhooks)
"""

import asyncio
import signal
import sys
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.core.services.native_exchange_manager import get_native_exchange_manager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Démarre le service Native Exchange centralisé (remplace Terminal 5 CCXT)'
    
    def __init__(self):
        super().__init__()
        self.manager = None
        self.shutdown_requested = False
    
    def add_arguments(self, parser):
        """Arguments de ligne de commande"""
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mode verbeux avec logs détaillés'
        )
        parser.add_argument(
            '--stats-interval',
            type=int,
            default=60,
            help='Intervalle affichage statistiques (secondes, 0=désactiver)'
        )
        parser.add_argument(
            '--redis-timeout',
            type=int,
            default=120,
            help='Timeout Redis en secondes'
        )
    
    def handle(self, *args, **options):
        """Point d'entrée principal"""
        
        # Configuration logging
        if options['verbose']:
            logging.getLogger('apps.core.services').setLevel(logging.DEBUG)
        
        # Affichage bannière
        self._print_banner()
        
        # Vérifications préalables
        if not self._check_prerequisites():
            self.stdout.write(
                self.style.ERROR("[ERR] Prerequis non satisfaits - Arret du service")
            )
            return
        
        # Configuration gestionnaire de signaux pour arrêt propre
        self._setup_signal_handlers()
        
        # Démarrage du service
        try:
            asyncio.run(self._run_service(options))
        except KeyboardInterrupt:
            pass  # Géré par signal handler
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[ERR] Erreur critique: {e}")
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS("[OK] Service Native Exchange arrete proprement")
        )
    
    def _print_banner(self):
        """Affichage bannière de démarrage"""
        banner = """
+==============================================================+
|                    ARISTOBOT3 NATIVE EXCHANGE                |
|                     Service Centralise v2.0                 |
+==============================================================+
|  [>] Remplace Terminal 5 CCXT avec clients natifs           |
|  [*] Performance: ~3x plus rapide                           |
|  [+] Exchanges: Bitget native (+ extensible)                |
|  [#] Monitoring: Statistiques temps reel                    |
+==============================================================+
"""
        self.stdout.write(self.style.SUCCESS(banner))
    
    def _check_prerequisites(self) -> bool:
        """Vérification des prérequis"""
        self.stdout.write("[CHECK] Verification des prerequis...")
        
        checks = []
        
        # Vérification Redis
        try:
            import redis
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            
            r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            r.ping()
            checks.append(("[OK] Redis", f"Connexion OK ({redis_host}:{redis_port})"))
        except Exception as e:
            checks.append(("[ERR] Redis", f"Connexion echouee: {e}"))
            # Afficher les résultats avant de retourner False
            for check_name, check_result in checks:
                self.stdout.write(f"  {check_name}: {check_result}")
            return False
        
        # Vérification base de données
        try:
            from apps.brokers.models import Broker
            broker_count = Broker.objects.filter(is_active=True).count()
            checks.append(("[OK] Database", f"{broker_count} brokers actifs trouves"))
        except Exception as e:
            checks.append(("[ERR] Database", f"Erreur: {e}"))
            # Afficher les résultats avant de retourner False
            for check_name, check_result in checks:
                self.stdout.write(f"  {check_name}: {check_result}")
            return False
        
        # Vérification clients natifs
        try:
            from apps.core.services.base_exchange_client import ExchangeClientFactory
            exchanges = ExchangeClientFactory.list_supported_exchanges()
            checks.append(("[OK] Exchanges natifs", f"Supportes: {', '.join(exchanges)}"))
        except Exception as e:
            checks.append(("[ERR] Exchanges natifs", f"Erreur: {e}"))
            # Afficher les résultats avant de retourner False
            for check_name, check_result in checks:
                self.stdout.write(f"  {check_name}: {check_result}")
            return False
        
        # Affichage résultats
        for check_name, check_result in checks:
            self.stdout.write(f"  {check_name}: {check_result}")
        
        self.stdout.write(self.style.SUCCESS("[OK] Tous les prerequis sont satisfaits"))
        return True
    
    def _setup_signal_handlers(self):
        """Configuration des gestionnaires de signaux pour arrêt propre"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.stdout.write(
                self.style.WARNING(f"\n[STOP] Signal {signal_name} recu - Arret en cours...")
            )
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Terminaison système
        
        if hasattr(signal, 'SIGHUP'):  # Unix seulement
            signal.signal(signal.SIGHUP, signal_handler)
    
    async def _run_service(self, options):
        """Boucle principale du service"""
        
        # Initialisation du gestionnaire
        self.manager = get_native_exchange_manager()
        
        # Configuration
        if options['redis_timeout']:
            self.manager.redis_timeout = options['redis_timeout']
        
        # Démarrage avec gestion d'erreurs
        try:
            self.stdout.write("[START] Demarrage du service...")
            self.stdout.write("[DEBUG] Creation de la tache manager...")
            
            # Lancement du gestionnaire en arrière-plan
            manager_task = asyncio.create_task(self.manager.start())
            self.stdout.write("[DEBUG] Tache manager creee, attente...")
            
            # Tâche d'affichage des statistiques
            stats_task = None
            if options['stats_interval'] > 0:
                stats_task = asyncio.create_task(
                    self._stats_display_loop(options['stats_interval'])
                )
            
            self.stdout.write(
                self.style.SUCCESS("[OK] Service Native Exchange demarre avec succes")
            )
            self.stdout.write("[INFO] Ecoute des requetes exchange_requests...")
            self.stdout.write("[TIP] Appuyez sur Ctrl+C pour arreter proprement")
            self.stdout.write(f"[DEBUG] Entree boucle: shutdown={self.shutdown_requested}, running={self.manager.running}")
            
            # CORRECTION : Attendre que le manager démarre (comme run_working_native_service)
            self.stdout.write("[DEBUG] Attente demarrage manager...")
            for i in range(20):  # Attendre max 10 secondes
                await asyncio.sleep(0.5)
                self.stdout.write(f"[DEBUG] Attente {i+1}/20: running={self.manager.running}")
                
                if self.manager.running:
                    self.stdout.write("[DEBUG] Manager demarre avec succes!")
                    break
                    
                # Vérifier si la tâche a planté
                if manager_task.done():
                    self.stdout.write("[DEBUG] ERREUR: Tache manager terminee prematurment!")
                    try:
                        await manager_task  # Récupérer l'exception
                    except Exception as e:
                        self.stdout.write(f"[ERROR] Exception tache manager: {e}")
                        import traceback
                        traceback.print_exc()
                    return
            
            if not self.manager.running:
                self.stdout.write("[ERROR] Manager n'a pas demarre apres 10s")
                return
            
            # Attendre l'arrêt demandé
            while not self.shutdown_requested and self.manager.running:
                await asyncio.sleep(0.5)
                
                # Vérifier si la tâche a planté
                if manager_task.done():
                    self.stdout.write("[DEBUG] ERREUR: Tache manager s'est arretee!")
                    try:
                        await manager_task  # Récupérer l'exception
                    except Exception as e:
                        self.stdout.write(f"[ERROR] Exception tache manager: {e}")
                        import traceback
                        traceback.print_exc()
                    break
            
            self.stdout.write(f"[DEBUG] Sortie boucle: shutdown={self.shutdown_requested}, running={self.manager.running}")
            
            # Arrêt des tâches
            self.stdout.write("[STOP] Arret des services en cours...")
            
            if stats_task and not stats_task.done():
                stats_task.cancel()
                try:
                    await stats_task
                except asyncio.CancelledError:
                    pass
            
            # Arrêt du gestionnaire
            await self.manager.stop()
            
            if not manager_task.done():
                manager_task.cancel()
                try:
                    await manager_task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur service: {e}")
            )
            
            # Tentative d'arrêt propre même en cas d'erreur
            if self.manager:
                try:
                    await self.manager.stop()
                except:
                    pass
            
            raise
    
    async def _stats_display_loop(self, interval: int):
        """
        📊 AFFICHAGE PÉRIODIQUE DES STATISTIQUES
        
        Affiche les statistiques de performance du service à intervalle régulier.
        """
        try:
            while not self.shutdown_requested:
                await asyncio.sleep(interval)
                
                if self.manager and self.manager.running:
                    stats = self.manager.get_stats()
                    
                    # Formatage des statistiques
                    uptime_min = int(stats['uptime_seconds'] // 60)
                    uptime_sec = int(stats['uptime_seconds'] % 60)
                    
                    stats_display = f"""
┌─ STATISTIQUES SERVICE NATIVE EXCHANGE ─────────────────┐
│ Uptime: {uptime_min:3d}m {uptime_sec:2d}s  │  Exchanges: {', '.join(stats['active_exchanges']) or 'aucun':15s} │
│ Requêtes: {stats['requests_processed']:6d}  │  Succès: {stats['success_rate']:5.1f}%           │
│ Échecs: {stats['requests_failed']:8d}  │  Temps moy: {stats['avg_response_time_ms']:6.1f}ms      │
│ Brokers: {stats['cached_brokers']:7d}  │                                │
└─────────────────────────────────────────────────────────┘"""
                    
                    self.stdout.write(stats_display)
                    
                    # Détail par action si verbose
                    if stats['requests_by_action']:
                        action_stats = []
                        for action, count in sorted(stats['requests_by_action'].items()):
                            action_stats.append(f"{action}: {count}")
                        
                        if action_stats:
                            self.stdout.write(f"📊 Par action: {' | '.join(action_stats)}")
        
        except asyncio.CancelledError:
            pass  # Arrêt normal
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠️ Erreur affichage statistiques: {e}")
            )
    
    def _format_duration(self, seconds: float) -> str:
        """Formatage durée en format lisible"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"


# Point d'entrée pour tests manuels
if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()
    
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'run_native_exchange_service', '--verbose'])