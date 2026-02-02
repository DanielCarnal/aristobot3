# -*- coding: utf-8 -*-
"""
TERMINAL 7 - ORDER MONITOR SERVICE

🎯 OBJECTIF: Service de surveillance des ordres executes et calcul P&L automatique
Detecte les ordres nouvellement executes et calcule automatiquement les gains/pertes

📋 ARCHITECTURE:
- Django Management Command avec timing interne 10s
- Utilise Terminal 5 (NativeExchangeManager) pour recuperer les ordres
- Calcul P&L en 3 phases: Price Averaging → FIFO → User Choice
- Notifications temps reel via Django Channels

🚀 DEMARRAGE:
  python manage.py run_order_monitor

🔧 FONCTIONNALITES:
- Detection automatique ordres executes (scan toutes les 10s)
- Calcul P&L Price Averaging et FIFO
- Surveillance multi-exchange (Bitget, Binance, etc.)
- Notifications WebSocket pour frontend
- Monitoring et statistiques detaillees

Compatible avec Terminal 5 architecture existante.
"""

import asyncio
import signal
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict

from loguru import logger

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

# Aristobot imports
from apps.brokers.models import Broker
from apps.trading_manual.models import Trade
from apps.webhooks.models import WebhookState
from apps.core.services.native_exchange_manager import get_native_exchange_manager
from apps.core.services.exchange_client import ExchangeClient
from apps.core.services.loguru_config import setup_loguru

User = get_user_model()


class Command(BaseCommand):
    help = 'Terminal 7 - Service de surveillance des ordres et calcul P&L automatique'
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.shutdown_requested = False
        
        # Gestionnaire Terminal 5 (Exchange Gateway)
        self.exchange_manager = None
        
        # Etats de surveillance par broker
        self.broker_states: Dict[int, Dict] = {}
        
        # Statistiques de monitoring
        self.stats = {
            'start_time': None,
            'cycles_completed': 0,
            'brokers_scanned': 0,
            'orders_processed': 0,
            'new_executions_found': 0,
            'pnl_calculations': 0,
            'errors': 0,
            'last_execution_time': None,
            'total_pnl_calculated': 0.0
        }
        
        # Configuration
        self.scan_interval = 10  # 10 secondes entre chaque cycle
        self.broker_delay = 1    # 1 seconde entre chaque broker
        self.history_limit = 50  # Nombre d'ordres history a recuperer
    
    def add_arguments(self, parser):
        """Arguments de ligne de commande"""
        parser.add_argument(
            '--scan-interval',
            type=int,
            default=10,
            help='Intervalle de scan en secondes (defaut: 10)'
        )
        parser.add_argument(
            '--broker-delay',
            type=int,
            default=1,
            help='Delai entre brokers en secondes (defaut: 1)'
        )
        parser.add_argument(
            '--history-limit',
            type=int,
            default=50,
            help='Nombre d\'ordres history a recuperer (defaut: 50)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mode verbeux avec logs detailles'
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Mode test: scan une seule fois puis arret'
        )
    
    def handle(self, *args, **options):
        """Point d'entree principal - Pattern identique Terminal 5"""
        setup_loguru("terminal7")

        # Configuration depuis arguments
        self.scan_interval = options['scan_interval']
        self.broker_delay = options['broker_delay'] 
        self.history_limit = options['history_limit']
        
        # Affichage banniere
        self._print_banner()
        
        # Verifications prealables
        if not self._check_prerequisites():
            self.stdout.write(
                self.style.ERROR("[ERR] Prerequis non satisfaits - Arret du service")
            )
            return
        
        # Configuration gestionnaire de signaux pour arret propre
        self._setup_signal_handlers()
        
        # Demarrage du service
        try:
            if options['test_mode']:
                asyncio.run(self._run_test_mode())
            else:
                asyncio.run(self._run_service())
        except KeyboardInterrupt:
            pass  # Gere par signal handler
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[ERR] Erreur critique: {e}")
            )
            import traceback
            traceback.print_exc()
            return
        
        self.stdout.write(
            self.style.SUCCESS("[OK] Terminal 7 - Order Monitor arrete proprement")
        )
    
    def _print_banner(self):
        """Affichage banniere de demarrage"""
        banner = f"""
+==============================================================+
|                    ARISTOBOT3 TERMINAL 7                    |
|                   Order Monitor Service                     |
+==============================================================+
|  [>] Detection automatique ordres executes                  |
|  [*] Calcul P&L: Price Averaging + FIFO                     |
|  [+] Multi-exchange via Terminal 5                          |
|  [#] Timing: {self.scan_interval}s scan, {self.broker_delay}s entre brokers                    |
+==============================================================+
"""
        self.stdout.write(self.style.SUCCESS(banner))
    
    def _check_prerequisites(self) -> bool:
        """Verification des prerequis"""
        self.stdout.write("[CHECK] Verification des prerequis...")
        
        checks = []
        
        # Verification Terminal 5 (NativeExchangeManager)
        try:
            manager = get_native_exchange_manager()
            if manager:
                checks.append(("[OK] Terminal 5", "NativeExchangeManager disponible"))
            else:
                checks.append(("[ERR] Terminal 5", "NativeExchangeManager indisponible"))
                return False
        except Exception as e:
            checks.append(("[ERR] Terminal 5", f"Erreur: {e}"))
            return False
        
        # Verification base de donnees
        try:
            broker_count = Broker.objects.filter(is_active=True).count()
            checks.append(("[OK] Database", f"{broker_count} brokers actifs trouves"))
            
            if broker_count == 0:
                checks.append(("[WARN] Brokers", "Aucun broker actif - service fonctionnera a vide"))
        except Exception as e:
            checks.append(("[ERR] Database", f"Erreur: {e}"))
            return False
        
        # Verification Django Channels
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                checks.append(("[OK] Channels", "Django Channels disponible"))
            else:
                checks.append(("[WARN] Channels", "Django Channels indisponible - pas de notifications"))
        except Exception as e:
            checks.append(("[WARN] Channels", f"Erreur: {e}"))
        
        # Affichage resultats
        for check_name, check_result in checks:
            self.stdout.write(f"  {check_name}: {check_result}")
        
        # Succes si pas d'erreur critique
        has_errors = any("[ERR]" in check[0] for check in checks)
        if not has_errors:
            self.stdout.write(self.style.SUCCESS("[OK] Tous les prerequis sont satisfaits"))
        
        return not has_errors
    
    def _setup_signal_handlers(self):
        """Configuration des gestionnaires de signaux pour arret propre"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.stdout.write(
                self.style.WARNING(f"\n[STOP] Signal {signal_name} recu - Arret en cours...")
            )
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Terminaison systeme
        
        if hasattr(signal, 'SIGHUP'):  # Unix seulement
            signal.signal(signal.SIGHUP, signal_handler)
    
    async def _run_service(self):
        """Service principal avec timing interne de 10s - CŒUR DE TERMINAL 7"""
        
        # Initialisation
        await self._initialize_service()
        
        logger.info(f"Terminal 7 demarre avec succes - {len(self.broker_states)} brokers surveilles toutes les {self.scan_interval}s")
        self.stdout.write("[TIP] Appuyez sur Ctrl+C pour arreter proprement")
        
        # BOUCLE PRINCIPALE - TIMING INTERNE (comme Terminal 5)
        cycle_count = 0
        while self.running and not self.shutdown_requested:
            cycle_count += 1
            cycle_start_time = time.time()
            
            try:
                # SCAN DE TOUS LES BROKERS SEQUENTIELLEMENT
                await self._scan_all_brokers(cycle_count)

                # NOUVEAU: POSITION GUARDIAN - Validation SL/TP coherence
                await self._validate_webhook_positions(cycle_count)

                # Mise a jour des statistiques
                cycle_time = time.time() - cycle_start_time
                self.stats['cycles_completed'] = cycle_count
                self.stats['last_execution_time'] = cycle_time
                
                # Affichage periodique des statistiques (toutes les 6 cycles = 1 minute)
                if cycle_count % 6 == 0:
                    self._display_service_stats()
                
                # TIMING INTERNE: Attendre 10 secondes avant le prochain cycle
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Erreur cycle {cycle_count}: {e}")
                
                # Continuer malgre l'erreur apres une pause
                await asyncio.sleep(self.scan_interval)
        
        # Arret propre
        await self._shutdown_service()
    
    async def _run_test_mode(self):
        """Mode test: scan une seule fois puis arret"""
        self.stdout.write(self.style.WARNING("[TEST] Mode test active - un seul cycle puis arret"))
        
        await self._initialize_service()
        await self._scan_all_brokers(1)
        
        self.stdout.write(self.style.SUCCESS("[TEST] Cycle de test termine"))
    
    async def _initialize_service(self):
        """Initialisation du service"""
        logger.info("Initialisation Terminal 7")

        # Demarrage du service
        self.running = True
        self.stats['start_time'] = datetime.utcnow()

        # Recuperation de l'Exchange Manager (Terminal 5)
        try:
            self.exchange_manager = get_native_exchange_manager()
            if not self.exchange_manager:
                raise Exception("NativeExchangeManager indisponible")

            logger.info("Connexion Terminal 5 etablie")
        except Exception as e:
            logger.error(f"Erreur connexion Terminal 5: {e}")
            raise

        # Chargement des brokers actifs
        await self._load_active_brokers()

        logger.info(f"Service initialise - {len(self.broker_states)} brokers surveilles")
    
    async def _load_active_brokers(self):
        """Charge la liste des brokers actifs a surveiller"""
        try:
            logger.info("Chargement des brokers actifs")
            
            # Recuperation de tous les brokers actifs
            brokers = await sync_to_async(list)(
                Broker.objects.filter(is_active=True).select_related('user')
            )
            
            loaded_count = 0
            for broker in brokers:
                try:
                    # Recuperation capital initial (sera ajoute au model Broker plus tard)
                    initial_capital = getattr(broker, 'initial_capital', 1000.0)
                    
                    # Etat initial de surveillance pour ce broker
                    self.broker_states[broker.id] = {
                        'id': broker.id,
                        'name': broker.name,
                        'exchange': broker.exchange,
                        'user_id': broker.user_id,
                        'user_name': broker.user.username,
                        
                        # Surveillance
                        'last_check': int((time.time() - 86400) * 1000),  # 24h en arriere
                        'known_orders': set(),  # OrderIDs deja traites
                        
                        # P&L et statistiques
                        'initial_capital': initial_capital,
                        'current_balance': None,
                        'total_pnl': 0.0,
                        'total_fees': 0.0,
                        'trade_count': 0,
                        
                        # Monitoring
                        'last_successful_scan': None,
                        'consecutive_errors': 0,
                        'total_scan_time': 0.0,
                        'avg_scan_time': 0.0,
                        
                        # Status
                        'status': 'active',
                        'last_error': None
                    }
                    
                    loaded_count += 1
                    logger.bind(broker_id=broker.id, exchange=broker.exchange).info(
                        f"Broker charge: {broker.name} - User: {broker.user.username}"
                    )

                except Exception as e:
                    logger.warning(f"Erreur chargement broker {broker.id}: {e}")

            logger.info(f"{loaded_count}/{len(brokers)} brokers charges avec succes")
            
        except Exception as e:
            logger.error(f"Erreur chargement brokers: {e}")
            raise
    
    async def _scan_all_brokers(self, cycle_count: int):
        """Scanne tous les brokers sequentiellement"""
        if not self.broker_states:
            return
        
        logger.bind(cycle=cycle_count).info(f"Cycle {cycle_count} debut - {len(self.broker_states)} brokers")
        cycle_new_executions = 0
        cycle_errors = 0
        
        for broker_id in list(self.broker_states.keys()):
            broker_state = self.broker_states[broker_id]
            
            try:
                scan_start = time.time()
                
                # SCAN DU BROKER
                new_executions = await self._scan_broker_orders(broker_id)
                cycle_new_executions += new_executions
                
                # Mise a jour timing
                scan_time = time.time() - scan_start
                broker_state['total_scan_time'] += scan_time
                broker_state['avg_scan_time'] = broker_state['total_scan_time'] / self.stats['cycles_completed'] if self.stats['cycles_completed'] > 0 else scan_time
                broker_state['last_successful_scan'] = time.time()
                broker_state['consecutive_errors'] = 0
                
                # Log si nouvelles executions
                if new_executions > 0:
                    logger.bind(broker_id=broker_id).info(
                        f"Nouveaux ordres traites: {broker_state['name']} - {new_executions}"
                    )
                
                # DELAI ENTRE BROKERS (rate limiting)
                if broker_id != list(self.broker_states.keys())[-1]:  # Pas de delai apres le dernier
                    await asyncio.sleep(self.broker_delay)
                
            except Exception as e:
                cycle_errors += 1
                broker_state['consecutive_errors'] += 1
                broker_state['last_error'] = str(e)
                broker_state['status'] = 'error' if broker_state['consecutive_errors'] >= 3 else 'active'
                
                logger.bind(broker_id=broker_id).error(f"Erreur scan broker {broker_state['name']}: {e}")
        
        # Mise a jour statistiques globales
        self.stats['brokers_scanned'] += len(self.broker_states)
        self.stats['new_executions_found'] += cycle_new_executions
        self.stats['errors'] += cycle_errors
        
        # Resume du cycle
        if cycle_new_executions > 0 or cycle_errors > 0:
            logger.bind(cycle=cycle_count).info(
                f"Cycle {cycle_count} termine: {cycle_new_executions} executions, {cycle_errors} erreurs"
            )
    
    async def _scan_broker_orders(self, broker_id: int) -> int:
        """
        Scanne les ordres d'un broker specifique
        Retourne le nombre de nouvelles executions detectees
        """
        broker_state = self.broker_states[broker_id]
        
        try:
            # 1. RECUPERATION DES ORDRES HISTORY RECENTS via Terminal 5
            history_orders = await self._get_broker_history_orders(broker_id)
            
            # 2. DETECTION DES NOUVEAUX ORDRES EXECUTES
            new_executed_orders = await self._detect_new_executions(broker_id, history_orders)
            
            # 3. TRAITEMENT DE CHAQUE NOUVEL ORDRE EXECUTE
            for order in new_executed_orders:
                try:
                    await self._process_executed_order(broker_id, order)
                    self.stats['orders_processed'] += 1
                    broker_state['trade_count'] += 1
                except Exception as e:
                    logger.error(f"Erreur traitement ordre {order.get('id', 'unknown')}: {e}")
            
            # 4. MISE A JOUR TIMESTAMP ET STATISTIQUES
            broker_state['last_check'] = int(time.time() * 1000)
            
            return len(new_executed_orders)
            
        except Exception as e:
            logger.error(f"Erreur scan broker {broker_id}: {e}")
            raise

    async def _validate_webhook_positions(self, cycle_count: int):
        """
        POSITION GUARDIAN - Validation coherence SL/TP pour positions webhooks

        Verifie toutes les positions WebhookState (status='open') et s'assure qu'elles
        ont bien leurs ordres SL/TP actifs. Si manquant, les recree automatiquement
        depuis les valeurs stockees dans position.current_sl/tp.

        Cette fonction repare automatiquement les echecs de Terminal 3 dans max 10s.
        """
        try:
            logger.bind(cycle=cycle_count, component="position_guardian").debug(
                "Position Guardian: debut validation"
            )

            # 1. CHARGER TOUTES LES POSITIONS OUVERTES
            open_positions = await sync_to_async(list)(
                WebhookState.objects.filter(status='open').select_related('broker', 'user')
            )

            if not open_positions:
                logger.bind(component="position_guardian").debug(
                    "Aucune position webhook ouverte"
                )
                return

            logger.bind(component="position_guardian").info(
                f"Position Guardian: {len(open_positions)} positions a valider"
            )

            repairs_made = 0

            # 2. VALIDER CHAQUE POSITION
            for position in open_positions:
                try:
                    # 3. VERIFIER SL ACTIF EN DB
                    sl_exists = await sync_to_async(
                        Trade.objects.filter(
                            user=position.user,
                            broker=position.broker,
                            symbol=position.symbol,
                            type='stop_loss',
                            status='open'
                        ).exists
                    )()

                    # 4. VERIFIER TP ACTIF EN DB
                    tp_exists = await sync_to_async(
                        Trade.objects.filter(
                            user=position.user,
                            broker=position.broker,
                            symbol=position.symbol,
                            type='take_profit',
                            status='open'
                        ).exists
                    )()

                    # 5. REPARER SL SI MANQUANT
                    if not sl_exists and position.current_sl:
                        logger.bind(
                            component="position_guardian",
                            position_id=position.id,
                            symbol=position.symbol,
                        ).warning(
                            "SL manquant - reparation en cours",
                            current_sl=float(position.current_sl),
                        )

                        try:
                            # Calcul side: LONG → SL sell, SHORT → SL buy
                            sl_side = 'sell' if position.side == 'buy' else 'buy'

                            # Creation SL via ExchangeClient (Terminal 5)
                            exchange_client = ExchangeClient(user_id=position.user.id)
                            sl_result = await exchange_client.place_order(
                                broker_id=position.broker.id,
                                symbol=position.symbol,
                                side=sl_side,
                                amount=float(position.quantity),
                                order_type='stop_loss',
                                stop_price=float(position.current_sl),
                            )

                            # Mise a jour position
                            def update_sl():
                                position.sl_order_id = sl_result.get('id', '')
                                position.save()

                            await sync_to_async(update_sl)()

                            logger.bind(
                                component="position_guardian",
                                position_id=position.id,
                                symbol=position.symbol,
                            ).info(
                                "SL repare avec succes",
                                sl_order_id=position.sl_order_id,
                            )

                            repairs_made += 1

                        except Exception as e:
                            logger.bind(
                                component="position_guardian",
                                position_id=position.id,
                            ).error(
                                "Echec reparation SL",
                                error=str(e),
                            )

                    # 6. REPARER TP SI MANQUANT
                    if not tp_exists and position.current_tp:
                        logger.bind(
                            component="position_guardian",
                            position_id=position.id,
                            symbol=position.symbol,
                        ).warning(
                            "TP manquant - reparation en cours",
                            current_tp=float(position.current_tp),
                        )

                        try:
                            # Calcul side: LONG → TP sell, SHORT → TP buy
                            tp_side = 'sell' if position.side == 'buy' else 'buy'

                            # Creation TP via ExchangeClient (Terminal 5)
                            exchange_client = ExchangeClient(user_id=position.user.id)
                            tp_result = await exchange_client.place_order(
                                broker_id=position.broker.id,
                                symbol=position.symbol,
                                side=tp_side,
                                amount=float(position.quantity),
                                order_type='take_profit',
                                price=float(position.current_tp),
                            )

                            # Mise a jour position
                            def update_tp():
                                position.tp_order_id = tp_result.get('id', '')
                                position.save()

                            await sync_to_async(update_tp)()

                            logger.bind(
                                component="position_guardian",
                                position_id=position.id,
                                symbol=position.symbol,
                            ).info(
                                "TP repare avec succes",
                                tp_order_id=position.tp_order_id,
                            )

                            repairs_made += 1

                        except Exception as e:
                            logger.bind(
                                component="position_guardian",
                                position_id=position.id,
                            ).error(
                                "Echec reparation TP",
                                error=str(e),
                            )

                except Exception as e:
                    logger.bind(
                        component="position_guardian",
                        position_id=position.id,
                    ).error(
                        "Erreur validation position",
                        error=str(e),
                    )

            # 7. LOG FINAL
            if repairs_made > 0:
                logger.bind(component="position_guardian").info(
                    f"Position Guardian: {repairs_made} ordres repares"
                )
            else:
                logger.bind(component="position_guardian").debug(
                    "Position Guardian: aucune reparation necessaire"
                )

        except Exception as e:
            logger.bind(component="position_guardian").error(
                "Erreur globale Position Guardian",
                error=str(e),
            )

    async def _shutdown_service(self):
        """Arret propre du service"""
        logger.info("Arret propre Terminal 7")

        self.running = False

        # Affichage statistiques finales
        self._display_final_stats()

        logger.info("Terminal 7 arrete proprement")
    
    def _display_service_stats(self):
        """Affiche les statistiques du service Terminal 7"""
        if not self.stats['start_time']:
            return
        
        uptime = datetime.utcnow() - self.stats['start_time']
        uptime_str = self._format_duration(uptime.total_seconds())
        
        active_brokers = sum(1 for s in self.broker_states.values() 
                           if s['status'] == 'active')
        total_brokers = len(self.broker_states)
        total_pnl = sum(s['total_pnl'] for s in self.broker_states.values())
        
        stats_display = f"""
┌─ TERMINAL 7 - ORDER MONITOR SERVICE ─────────────────────┐
│ Uptime: {uptime_str:>8s}        │  Brokers: {active_brokers:2d}/{total_brokers:2d} actifs      │
│ Cycles: {self.stats['cycles_completed']:6d}        │  P&L Total: ${total_pnl:+8.2f}     │
│ Executions: {self.stats['new_executions_found']:4d}    │  Ordres: {self.stats['orders_processed']:6d}         │
│ Erreurs: {self.stats['errors']:7d}        │  Derniere: {self._format_last_exec():8s}      │
└──────────────────────────────────────────────────────────┘"""
        
        self.stdout.write(stats_display)
        
        # Detail brokers en erreur
        error_brokers = [s for s in self.broker_states.values() if s['status'] == 'error']
        for broker in error_brokers:
            self.stdout.write(
                f"⚠️  {broker['name']}: {broker['consecutive_errors']} erreurs consecutives"
            )
    
    def _display_final_stats(self):
        """Affiche les statistiques finales du service"""
        if not self.stats['start_time']:
            return
        
        uptime = datetime.utcnow() - self.stats['start_time']
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("STATISTIQUES FINALES TERMINAL 7")
        self.stdout.write("="*60)
        self.stdout.write(f"Duree fonctionnement: {self._format_duration(uptime.total_seconds())}")
        self.stdout.write(f"Cycles completes: {self.stats['cycles_completed']}")
        self.stdout.write(f"Brokers scannes: {self.stats['brokers_scanned']}")
        self.stdout.write(f"Nouvelles executions: {self.stats['new_executions_found']}")
        self.stdout.write(f"Ordres traites: {self.stats['orders_processed']}")
        self.stdout.write(f"Calculs P&L: {self.stats['pnl_calculations']}")
        self.stdout.write(f"Erreurs totales: {self.stats['errors']}")
        
        # P&L par broker
        if self.broker_states:
            self.stdout.write("\nP&L PAR BROKER:")
            for broker_state in self.broker_states.values():
                if broker_state['trade_count'] > 0:
                    self.stdout.write(
                        f"  {broker_state['name']}: ${broker_state['total_pnl']:+8.2f} "
                        f"({broker_state['trade_count']} trades)"
                    )
        
        self.stdout.write("="*60)
    
    def _format_duration(self, seconds: float) -> str:
        """Formatage duree en format lisible"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m{seconds%60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h{minutes:.0f}m"
    
    def _format_last_exec(self) -> str:
        """Formate le temps de la derniere execution"""
        if self.stats['last_execution_time']:
            return f"{self.stats['last_execution_time']*1000:.0f}ms"
        return "N/A"


# ===============================================================
# FONCTIONS CORE - INTEGRATION TERMINAL 5 & DETECTION
# ===============================================================

    async def _get_broker_history_orders(self, broker_id: int, limit: int = None) -> List[Dict]:
        """
        Recupere les ordres history via Terminal 5 (NativeExchangeManager)
        Compatible avec l'architecture existante + SÉCURITÉ MULTI-TENANT
        """
        if limit is None:
            limit = self.history_limit
        
        try:
            # 🔒 SÉCURITÉ: Récupérer user_id du broker avant création ExchangeClient
            user_id = await self._get_broker_user_id(broker_id)
            
            # CORRECTION: Utiliser ExchangeClient avec user_id pour sécurité Terminal 5
            from apps.core.services.exchange_client import ExchangeClient
            client = ExchangeClient(user_id=user_id)
            return await client.fetch_closed_orders(broker_id, limit=limit)
                
        except Exception as e:
            logger.error(f"Erreur recuperation history orders broker {broker_id}: {e}")
            raise
    
    async def _detect_new_executions(self, broker_id: int, history_orders: List[Dict]) -> List[Dict]:
        """
        Detecte les ordres nouvellement executes depuis la derniere verification
        """
        broker_state = self.broker_states[broker_id]
        last_check_time = broker_state['last_check']
        known_orders = broker_state['known_orders']
        
        new_executions = []
        
        for order in history_orders:
            # Extraction des identifiants (format variable selon exchange)
            order_id = order.get('id') or order.get('orderId') or order.get('order_id')
            if not order_id:
                continue
                
            # Extraction du timestamp de mise a jour
            update_time = order.get('updated') or order.get('uTime') or order.get('updateTime')
            if update_time:
                # Conversion en millisecondes si necessaire
                if isinstance(update_time, str) and update_time.isdigit():
                    update_time = int(update_time)
                elif isinstance(update_time, (int, float)):
                    # Si le timestamp semble etre en secondes, convertir en ms
                    if update_time < 1e12:  # Timestamp en secondes
                        update_time = int(update_time * 1000)
                    else:  # Deja en millisecondes
                        update_time = int(update_time)
                else:
                    # Fallback: utiliser timestamp actuel
                    update_time = int(time.time() * 1000)
            else:
                update_time = int(time.time() * 1000)
            
            # Extraction du status
            status = order.get('status', '').lower()
            
            # CONDITIONS pour "nouvel ordre execute"
            is_new = order_id not in known_orders
            is_recent = update_time > last_check_time  
            is_filled = status in ['filled', 'closed', 'full_fill', 'completely_filled']
            
            # Debug pour le premier cycle
            if self.stats['cycles_completed'] <= 1:
                logger.debug(
                    f"Order {order_id}: new={is_new}, recent={is_recent}, filled={is_filled}, "
                    f"status={status}, update_time={update_time}, last_check={last_check_time}"
                )
            
            if is_new and is_recent and is_filled:
                new_executions.append(order)
                known_orders.add(order_id)
                
                logger.info(f"Nouvelle execution detectee: {order_id} ({status})")
        
        return new_executions
    
    async def _process_executed_order(self, broker_id: int, order: Dict):
        """
        Traite un ordre execute: calcule P&L et sauvegarde en DB
        """
        try:
            # EXTRACTION DES DONNEES DE L'ORDRE
            order_data = self._extract_order_data(order)
            
            if not order_data['symbol'] or not order_data['side']:
                logger.warning(f"Ordre incomplet ignore: {order_data}")
                return
            
            # CALCUL P&L avec Price Averaging (Phase 1)
            pnl_data = await self._calculate_pnl_price_averaging(broker_id, order_data)
            
            # SAUVEGARDE/MISE A JOUR EN BASE DE DONNEES
            trade = await self._save_or_update_trade(broker_id, order_data, pnl_data, order)
            
            # MISE A JOUR DES STATISTIQUES BROKER
            await self._update_broker_stats(broker_id, pnl_data)
            
            # NOTIFICATIONS WEBSOCKET
            await self._send_notifications(broker_id, trade, pnl_data)
            
            # LOG DU RESULTAT
            logger.bind(symbol=order_data['symbol'], side=order_data['side']).info(
                f"P&L calcule: {order_data['symbol']} {order_data['side']} "
                f"${pnl_data['realized_pnl']:+.2f} (fees: ${pnl_data['total_fees']:.2f})"
            )
            
            # Compteur statistiques
            self.stats['pnl_calculations'] += 1
            
        except Exception as e:
            logger.error(f"Erreur traitement ordre: {e}", exc_info=True)
    
    def _extract_order_data(self, order: Dict) -> Dict:
        """
        Extrait et normalise les donnees d'un ordre exchange
        Compatible avec les formats Bitget, Binance, etc.
        """
        # IDs
        order_id = order.get('id') or order.get('orderId') or order.get('order_id')
        client_order_id = order.get('clientOrderId') or order.get('clientOid') or order.get('client_order_id')
        
        # Donnees de base
        symbol = order.get('symbol', '')
        side = order.get('side', '')
        order_type = order.get('type') or order.get('orderType', 'market')
        
        # Quantites et prix - Gestion des formats variables
        filled_quantity = 0.0
        avg_price = 0.0
        
        # Quantite executee
        for field in ['filled', 'fillSize', 'baseVolume', 'executedQty', 'cumExecQty']:
            if field in order and order[field]:
                try:
                    filled_quantity = float(order[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        # Prix moyen d'execution
        for field in ['average', 'priceAvg', 'avgPrice', 'avgExecPrice']:
            if field in order and order[field]:
                try:
                    avg_price = float(order[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        # Si pas de prix moyen, utiliser le prix limite
        if avg_price == 0.0:
            for field in ['price', 'limitPrice']:
                if field in order and order[field]:
                    try:
                        avg_price = float(order[field])
                        break
                    except (ValueError, TypeError):
                        continue
        
        # Frais
        total_fees = self._extract_total_fees(order)
        
        # Timestamp execution
        executed_at = self._parse_timestamp(
            order.get('updated') or order.get('uTime') or order.get('updateTime')
        )
        
        return {
            'order_id': order_id,
            'client_order_id': client_order_id,
            'symbol': symbol,
            'side': side.lower() if side else '',
            'type': order_type.lower() if order_type else 'market',
            'quantity': filled_quantity,
            'avg_price': avg_price,
            'total_fees': total_fees,
            'executed_at': executed_at,
            'raw_order': order  # Garder l'ordre brut pour debug
        }
    
    def _extract_total_fees(self, order: Dict) -> float:
        """
        Extrait le montant total des frais selon le format exchange
        Compatible Bitget feeDetail, Binance, etc.
        """
        total_fees = 0.0
        
        # Format Bitget - feeDetail complexe
        if 'feeDetail' in order:
            fee_detail = order['feeDetail']
            
            # Nouveau format avec newFees
            if isinstance(fee_detail, dict) and 'newFees' in fee_detail:
                new_fees = fee_detail['newFees']
                if isinstance(new_fees, dict):
                    # Total fee amount
                    total_fees = float(new_fees.get('t', 0))
            
            # Ancien format avec clé dynamique (ex: BGB)
            elif isinstance(fee_detail, dict):
                for key, value in fee_detail.items():
                    if isinstance(value, dict) and 'totalFee' in value:
                        total_fees += float(value['totalFee'])
        
        # Format standard simple
        elif 'fee' in order:
            fee_data = order['fee']
            if isinstance(fee_data, dict):
                total_fees = float(fee_data.get('cost', 0))
            elif isinstance(fee_data, (int, float, str)):
                total_fees = float(fee_data)
        
        # Format Binance
        elif 'commission' in order:
            total_fees = float(order['commission'])
        
        # Champs alternatifs
        for field in ['fees', 'totalFee', 'feeAmount']:
            if field in order and order[field]:
                try:
                    total_fees = float(order[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        return abs(total_fees)  # Toujours positif
    
    def _parse_timestamp(self, timestamp) -> Optional[datetime]:
        """Parse un timestamp en datetime"""
        if not timestamp:
            return datetime.utcnow()
        
        try:
            # Si c'est deja un datetime
            if isinstance(timestamp, datetime):
                return timestamp
            
            # Si c'est un string numeric
            if isinstance(timestamp, str) and timestamp.isdigit():
                timestamp = int(timestamp)
            
            # Si c'est un nombre
            if isinstance(timestamp, (int, float)):
                # Detecter si c'est en secondes ou millisecondes
                if timestamp > 1e12:  # Millisecondes
                    timestamp = timestamp / 1000
                
                return datetime.utcfromtimestamp(timestamp)
            
            # Sinon, timestamp actuel
            return datetime.utcnow()
            
        except Exception:
            return datetime.utcnow()


# ===============================================================
# CALCUL P&L - PHASE 1: PRICE AVERAGING
# ===============================================================

    async def _calculate_pnl_price_averaging(self, broker_id: int, order_data: Dict) -> Dict:
        """
        PHASE 1: Calcul P&L avec methode Price Averaging
        
        Simple mais efficace pour commencer.
        Sera remplace par FIFO en Phase 2.
        """
        symbol = order_data['symbol']
        side = order_data['side']
        quantity = order_data['quantity']
        avg_price = order_data['avg_price']
        total_fees = order_data['total_fees']
        
        # Recuperation des trades precedents pour ce symbole
        previous_trades = await sync_to_async(list)(
            Trade.objects.filter(
                broker_id=broker_id,
                symbol=symbol,
                exchange_order_status='filled'
            ).order_by('executed_at')
        )
        
        if side == 'buy':
            # Achat : pas de P&L realise, juste mise a jour position
            realized_pnl = 0.0
            avg_buy_price = avg_price  # Prix d'achat pour ce trade
            
        else:  # sell
            # Vente : calcul P&L base sur prix moyen d'achat
            total_buy_quantity = 0.0
            total_buy_value = 0.0
            
            for trade in previous_trades:
                if trade.side == 'buy' and trade.exchange_order_status == 'filled':
                    trade_quantity = float(trade.filled_quantity or trade.quantity)
                    trade_price = float(trade.filled_price or trade.price)
                    
                    total_buy_quantity += trade_quantity
                    total_buy_value += (trade_quantity * trade_price)
            
            if total_buy_quantity > 0:
                avg_buy_price = total_buy_value / total_buy_quantity
                realized_pnl = (avg_price - avg_buy_price) * quantity
            else:
                # Vente sans achat prealable (short ou erreur)
                avg_buy_price = 0.0
                realized_pnl = 0.0
                self.stdout.write(f"[WARN] Vente sans achat prealable: {symbol}")
        
        # Calcul position restante approximatif
        position_quantity = self._calculate_current_position(previous_trades, order_data)
        
        return {
            'realized_pnl': realized_pnl,
            'total_fees': total_fees,
            'calculation_method': 'price_averaging',
            'avg_buy_price': avg_buy_price,
            'position_quantity': position_quantity,
            'details': {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'avg_price': avg_price
            }
        }
    
    def _calculate_current_position(self, previous_trades: List, current_order: Dict) -> float:
        """
        Calcule la position actuelle approximative
        (Simplifie pour Phase 1, sera ameliore en Phase 2 FIFO)
        """
        total_buys = 0.0
        total_sells = 0.0
        
        # Compter tous les trades precedents
        for trade in previous_trades:
            quantity = float(trade.filled_quantity or trade.quantity)
            if trade.side == 'buy':
                total_buys += quantity
            elif trade.side == 'sell':
                total_sells += quantity
        
        # Ajouter le trade actuel
        current_quantity = current_order['quantity']
        if current_order['side'] == 'buy':
            total_buys += current_quantity
        elif current_order['side'] == 'sell':
            total_sells += current_quantity
        
        return total_buys - total_sells
    
    def _parse_timestamp(self, timestamp_value):
        """
        Parse un timestamp exchange en datetime UTC timezone-aware
        Compatible avec formats milliseconds, seconds, string ISO
        """
        from django.utils import timezone
        
        if not timestamp_value:
            return timezone.now()
        
        try:
            # Si c'est une string, parser comme ISO
            if isinstance(timestamp_value, str):
                if timestamp_value.isdigit():
                    # String de chiffres = timestamp
                    timestamp_value = int(timestamp_value)
                else:
                    # ISO format, parser directement
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                    return dt.replace(tzinfo=timezone.utc)
            
            # Si c'est un entier/float
            if isinstance(timestamp_value, (int, float)):
                # Déterminer si c'est en millisecondes ou secondes
                if timestamp_value > 1e12:  # Plus grand que 1e12 = millisecondes
                    timestamp_seconds = timestamp_value / 1000
                else:  # Secondes
                    timestamp_seconds = timestamp_value
                
                # Créer datetime UTC timezone-aware
                from datetime import datetime
                dt = datetime.utcfromtimestamp(timestamp_seconds)
                return dt.replace(tzinfo=timezone.utc)
            
        except Exception as e:
            logger.warning(f"Erreur parsing timestamp {timestamp_value}: {e}")
        
        # Fallback: timestamp actuel UTC
        return timezone.now()

# ===============================================================
# SAUVEGARDE BASE DE DONNEES
# ===============================================================

    async def _save_or_update_trade(self, broker_id: int, order_data: Dict, pnl_data: Dict, raw_order: Dict) -> Trade:
        """
        Met a jour un trade existant OU cree un nouveau trade pour ordres detectes
        LOGIQUE CORRIGEE: UPDATE au lieu de CREATE systematique
        """
        try:
            # Recuperation de l'utilisateur du broker
            user_id = await self._get_broker_user_id(broker_id)
            
            # 1. RECHERCHER TRADE EXISTANT par exchange_order_id
            try:
                trade = await sync_to_async(Trade.objects.get)(
                    exchange_order_id=order_data['order_id']
                )
                
                logger.info(f"✅ Trade existant trouve: {trade.id} - Mise a jour P&L")
                
                # MISE A JOUR avec donnees Terminal 7
                trade.realized_pnl = pnl_data['realized_pnl']
                trade.fees = pnl_data['total_fees']
                trade.filled_quantity = order_data['quantity']
                trade.filled_price = order_data['avg_price']
                trade.status = 'completed'
                trade.exchange_order_status = 'filled'
                trade.executed_at = order_data['executed_at']
                
                # Enrichir avec TOUTES les donnees Exchange (NOUVEAU)
                trade.exchange_user_id = raw_order.get('userId')
                trade.enter_point_source = raw_order.get('enterPointSource')
                trade.order_source = raw_order.get('orderSource')
                trade.quote_volume = raw_order.get('quoteVolume')
                trade.amount = raw_order.get('amount')
                trade.trade_id = raw_order.get('tradeId')
                trade.trade_scope = raw_order.get('tradeScope')
                trade.tpsl_type = raw_order.get('tpslType')
                trade.cancel_reason = raw_order.get('cancelReason')
                
                # JSON complets (DEBUG + FRAIS)
                trade.fee_detail = raw_order.get('feeDetail')
                trade.exchange_raw_data = raw_order
                
                # Metadonnees mise a jour
                current_notes = trade.notes or ""
                trade.notes = f"{current_notes}\nP&L enrichi par Terminal 7 ({pnl_data['calculation_method']})"
                
                await sync_to_async(trade.save)()
                logger.info(f"✅ Trade {trade.id} mis a jour avec P&L: {trade.realized_pnl}")
                return trade
                
            except Trade.DoesNotExist:
                # 2. CREER NOUVEAU TRADE pour ordre "orphelin" detecte
                logger.warning(f"⚠️ Ordre orphelin detecte: {order_data['order_id']} - Creation nouveau Trade")
                
                trade = await sync_to_async(Trade.objects.create)(
                    # Relations
                    user_id=user_id,
                    broker_id=broker_id,
                    source='terminal7',
                    
                    # TRAÇABILITÉ ORDRE DETECTE
                    ordre_existant="By Terminal7 detection",
                    
                    # Donnees de l'ordre
                    symbol=order_data['symbol'],
                    side=order_data['side'],
                    order_type=order_data['type'],
                    quantity=order_data['quantity'],
                    filled_quantity=order_data['quantity'],
                    price=order_data['avg_price'],
                    filled_price=order_data['avg_price'],
                    
                    # Valeurs calculees
                    total_value=order_data['quantity'] * order_data['avg_price'],
                    fees=pnl_data['total_fees'],
                    realized_pnl=pnl_data['realized_pnl'],
                    
                    # Status et timing
                    status='completed',
                    exchange_order_status='filled',
                    exchange_order_id=order_data['order_id'],
                    exchange_client_order_id=order_data.get('client_order_id'),
                    executed_at=order_data['executed_at'],
                    
                    # TOUS les champs Exchange (MAPPING COMPLET)
                    exchange_user_id=raw_order.get('userId'),
                    enter_point_source=raw_order.get('enterPointSource'),
                    order_source=raw_order.get('orderSource'),
                    quote_volume=raw_order.get('quoteVolume'),
                    amount=raw_order.get('amount'),
                    trade_id=raw_order.get('tradeId'),
                    trade_scope=raw_order.get('tradeScope'),
                    tpsl_type=raw_order.get('tpslType'),
                    cancel_reason=raw_order.get('cancelReason'),
                    
                    # JSON complets
                    fee_detail=raw_order.get('feeDetail'),
                    exchange_raw_data=raw_order,
                    
                    # Metadata
                    notes=f"Ordre detecte par Terminal 7 ({pnl_data['calculation_method']})",
                    pnl_calculation_method=pnl_data['calculation_method'],
                    avg_buy_price=pnl_data.get('avg_buy_price', 0.0),
                    position_quantity_after=pnl_data.get('position_quantity', 0.0)
                )
                
                logger.info(f"✅ Nouveau Trade orphelin cree: {trade.id} - {order_data['symbol']}")
                return trade
            
            logger.info(f"Trade sauvegarde: ID {trade.id}, {order_data['symbol']} {order_data['side']}")
            return trade
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde trade: {e}")
            raise
    
    async def _get_broker_user_id(self, broker_id: int) -> int:
        """Recupere l'user_id d'un broker"""
        broker_state = self.broker_states.get(broker_id)
        if broker_state:
            return broker_state['user_id']
        
        # Fallback: requete DB
        broker = await sync_to_async(Broker.objects.select_related('user').get)(id=broker_id)
        return broker.user_id
    
    async def _update_broker_stats(self, broker_id: int, pnl_data: Dict):
        """Met a jour les statistiques du broker"""
        broker_state = self.broker_states[broker_id]
        
        # Mise a jour P&L total
        broker_state['total_pnl'] += pnl_data['realized_pnl']
        broker_state['total_fees'] += pnl_data['total_fees']
        
        # Mise a jour compteurs
        broker_state['trade_count'] += 1
        
        # Mise a jour P&L global
        self.stats['total_pnl_calculated'] += pnl_data['realized_pnl']

# ===============================================================
# NOTIFICATIONS WEBSOCKET
# ===============================================================

    async def _send_notifications(self, broker_id: int, trade: Trade, pnl_data: Dict):
        """
        Envoie des notifications temps reel via Django Channels
        Compatible avec le frontend Trading Manual
        """
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
            
            user_id = await self._get_broker_user_id(broker_id)
            broker_state = self.broker_states[broker_id]
            
            # NOTIFICATION 1: Trading Manual (pour l'utilisateur specifique)
            await channel_layer.group_send(
                f"trading_manual_{user_id}",
                {
                    'type': 'order_executed_notification',
                    'source': 'terminal7',
                    'trade_id': trade.id,
                    'broker_id': broker_id,
                    'broker_name': broker_state['name'],
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': float(trade.quantity),
                    'price': float(trade.price),
                    'realized_pnl': float(pnl_data['realized_pnl']),
                    'total_fees': float(pnl_data['total_fees']),
                    'calculation_method': pnl_data['calculation_method'],
                    'timestamp': int(time.time() * 1000)
                }
            )
            
            # NOTIFICATION 2: Dashboard Terminal 7 (monitoring global)
            await channel_layer.group_send(
                "terminal7_monitoring",
                {
                    'type': 'pnl_update',
                    'broker_id': broker_id,
                    'broker_name': broker_state['name'],
                    'trade_count': broker_state['trade_count'],
                    'broker_total_pnl': broker_state['total_pnl'],
                    'last_trade': {
                        'symbol': trade.symbol,
                        'side': trade.side,
                        'pnl': float(pnl_data['realized_pnl'])
                    },
                    'global_stats': {
                        'total_executions': self.stats['new_executions_found'],
                        'total_pnl': self.stats['total_pnl_calculated'],
                        'active_brokers': len([s for s in self.broker_states.values() if s['status'] == 'active'])
                    },
                    'timestamp': int(time.time() * 1000)
                }
            )
            
            logger.info(f"Notifications envoyees pour trade {trade.id}")
            
        except Exception as e:
            logger.error(f"Erreur envoi notifications: {e}")

# ===============================================================
# EXTENSIONS FUTURES - FIFO (PHASE 2)
# ===============================================================

    async def _calculate_pnl_fifo(self, broker_id: int, order_data: Dict) -> Dict:
        """
        PHASE 2: Calcul P&L avec methode FIFO (First In, First Out)
        
        Plus precis que price averaging, respecte l'ordre chronologique.
        A implementer en Phase 2.
        """
        # TODO: Implementation FIFO pour Phase 2
        # Pour l'instant, fallback sur price averaging
        return await self._calculate_pnl_price_averaging(broker_id, order_data)
    
    async def _get_fifo_buy_queue(self, broker_id: int, symbol: str) -> List[Dict]:
        """
        Recupere la queue FIFO des achats non encore vendus
        Ordre chronologique : premier achete = premier vendu
        
        A implementer en Phase 2 avec nouveau champ remaining_quantity.
        """
        # TODO: Implementation FIFO queue pour Phase 2
        pass
    
    async def _update_fifo_queue(self, broker_id: int, symbol: str, consumed_trades: List[Dict]):
        """
        Met a jour la queue FIFO apres une vente
        
        A implementer en Phase 2.
        """
        # TODO: Implementation FIFO update pour Phase 2
        pass

# ===============================================================
# FONCTIONS UTILITAIRES
# ===============================================================

    def _validate_order_data(self, order_data: Dict) -> bool:
        """Valide que les donnees de l'ordre sont coherentes"""
        required_fields = ['symbol', 'side', 'quantity', 'avg_price']
        
        for field in required_fields:
            if not order_data.get(field):
                return False
        
        # Validations supplementaires
        if order_data['quantity'] <= 0:
            return False
        
        if order_data['avg_price'] <= 0:
            return False
        
        if order_data['side'] not in ['buy', 'sell']:
            return False
        
        return True
    
    def _should_skip_broker(self, broker_id: int) -> bool:
        """Determine si un broker doit etre ignore temporairement"""
        broker_state = self.broker_states.get(broker_id)
        if not broker_state:
            return True
        
        # Skip si trop d'erreurs consecutives
        if broker_state['consecutive_errors'] >= 5:
            return True
        
        # Skip si derniere erreur trop recente (< 1 minute)
        if (broker_state['last_error'] and 
            broker_state['last_successful_scan'] and
            time.time() - broker_state['last_successful_scan'] < 60):
            return True
        
        return False
    
    def _format_broker_status(self, broker_state: Dict) -> str:
        """Formate le statut d'un broker pour affichage"""
        status = broker_state['status']
        
        if status == 'active':
            return "🟢 ACTIF"
        elif status == 'error':
            return f"🔴 ERREUR ({broker_state['consecutive_errors']})"
        else:
            return f"🟡 {status.upper()}"
    
    async def _cleanup_old_known_orders(self):
        """
        Nettoie les anciens order IDs pour eviter une croissance infinie de la memoire
        Garde seulement les ordres des 7 derniers jours
        """
        cutoff_time = time.time() - (7 * 24 * 3600)  # 7 jours
        
        for broker_state in self.broker_states.values():
            # Simple: vider la set si elle devient trop grande
            if len(broker_state['known_orders']) > 1000:
                broker_state['known_orders'].clear()
                broker_state['last_check'] = int((time.time() - 86400) * 1000)  # Reset a 24h
                logger.info(f"Reset known_orders pour broker {broker_state['name']}")


# ===============================================================
# POINT D'ENTREE POUR TESTS INDEPENDANTS
# ===============================================================

async def test_terminal7_standalone():
    """
    Fonction de test independante pour valider Terminal 7
    Peut etre appelee depuis les scripts de test
    """
    command = Command()
    command.scan_interval = 5  # Test plus rapide
    command.history_limit = 10
    
    try:
        await command._initialize_service()
        await command._scan_all_brokers(1)
        
        print("✅ Test Terminal 7 reussi")
        return True
        
    except Exception as e:
        print(f"❌ Test Terminal 7 echoue: {e}")
        return False
    finally:
        await command._shutdown_service()


if __name__ == "__main__":
    # Permet d'executer Terminal 7 directement pour les tests
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()
    
    # Test standalone
    asyncio.run(test_terminal7_standalone())