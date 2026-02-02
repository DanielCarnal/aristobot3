# -*- coding: utf-8 -*-
"""
TERMINAL 3 - TRADING ENGINE

Moteur de trading qui ecoute :
1. Signaux Heartbeat (Module 7 - strategies Python)
2. Webhooks TradingView (Module 4 - en cours)

Responsabilites :
- Traiter webhooks avec logique metier
- Valider exchange actif (TypeDeTrading='Webhooks')
- Calculer quantites selon PourCent
- Executer ordres via Terminal 5 (ExchangeClient)
- Sauvegarder resultats en DB
"""
import asyncio
import json
import signal
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async
import redis.asyncio as redis
from loguru import logger
from apps.core.services.loguru_config import setup_loguru

from apps.core.services.exchange_client import ExchangeClient
from apps.brokers.models import Broker
from apps.webhooks.models import Webhook, WebhookState
from apps.trading_manual.models import Trade


class Command(BaseCommand):
    help = 'Lance le moteur de trading (Heartbeat + Webhooks)'

    def __init__(self):
        super().__init__()
        self.running = True
        self.redis_client = None

        # Statistiques
        self.webhooks_processed = 0
        self.webhooks_errors = 0
        self.orders_executed = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Mode test sans execution reelle des trades',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mode verbeux avec logs detailles',
        )

    def handle(self, *args, **options):
        setup_loguru("terminal3")

        self.test_mode = options.get('test', False)
        self.verbose = options.get('verbose', False)

        if self.verbose:
            import os
            os.environ["ARISTOBOT_LOG_LEVEL"] = "DEBUG"
            setup_loguru("terminal3")

        # Gerer l'arret propre
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n"
                f"╔════════════════════════════════════════════════╗\n"
                f"║       TERMINAL 3 - TRADING ENGINE v2.0        ║\n"
                f"╚════════════════════════════════════════════════╝\n"
                f"  Mode: {'TEST' if self.test_mode else 'PRODUCTION'}\n"
                f"  Ecoute: heartbeat + webhook_raw\n"
                f"\n"
            )
        )

        logger.info(
            "Trading Engine demarre",
            mode="TEST" if self.test_mode else "PRODUCTION",
            verbose=self.verbose
        )

        # Lancer la boucle async
        asyncio.run(self.run_engine())

    async def run_engine(self):
        """Boucle principale du Trading Engine"""
        try:
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)

            self.redis_client = await redis.from_url(
                f'redis://{redis_host}:{redis_port}',
                encoding='utf-8',
                decode_responses=True
            )

            await self.redis_client.ping()
            logger.info("Connexion Redis OK", host=redis_host, port=redis_port)

            # Lancer les taches d'ecoute en parallele
            tasks = [
                asyncio.create_task(self.listen_heartbeat()),
                asyncio.create_task(self.listen_webhooks()),
                asyncio.create_task(self.stats_display_loop()),
            ]

            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Trading Engine pret\n"
                    "   [1] Ecoute heartbeat (strategies - Module 7)\n"
                    "   [2] Ecoute webhook_raw (TradingView - Module 4)\n"
                )
            )

            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error("Erreur critique Trading Engine", error=str(e))
            raise
        finally:
            await self.cleanup()

    async def listen_heartbeat(self):
        """
        MODULE 7 (FUTUR): Ecoute signaux Heartbeat pour strategies Python
        Pour le moment, juste un placeholder
        """
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe('heartbeat')

        logger.info("Ecoute canal heartbeat active (strategies - Module 7)")

        async for message in pubsub.listen():
            if not self.running:
                break

            if message['type'] == 'message':
                # TODO MODULE 7: Traiter signaux strategies
                if self.verbose:
                    logger.debug("Signal heartbeat recu", data=message['data'][:100])

    async def listen_webhooks(self):
        """
        MODULE 4: Ecoute webhooks TradingView depuis Redis
        """
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe('webhook_raw')

        logger.info("Ecoute canal webhook_raw active (TradingView - Module 4)")

        async for message in pubsub.listen():
            if not self.running:
                break

            if message['type'] == 'message':
                try:
                    webhook_data = json.loads(message['data'])
                    await self.process_webhook(webhook_data)
                except Exception as e:
                    logger.error("Erreur traitement webhook", error=str(e))
                    self.webhooks_errors += 1

    async def process_webhook(self, webhook_data):
        """
        Traite un webhook TradingView avec logique metier complete

        Etapes :
        1. Sauvegarder webhook en DB
        2. Valider exchange actif
        3. Calculer quantite selon PourCent
        4. Executer action (BuyMarket, SellMarket, MAJ, PING)
        5. Mettre a jour etat position
        """
        # Extraire trace_id propagé depuis Terminal 6
        trace_id = webhook_data.get('trace_id', str(uuid.uuid4()))

        payload = webhook_data.get('payload', {})
        received_at = webhook_data.get('received_at')

        # Extraire donnees webhook
        symbol = payload.get('Symbol')
        action = payload.get('Action')
        prix = payload.get('Prix')
        prix_sl = payload.get('PrixSL')
        prix_tp = payload.get('PrixTP')
        pour_cent = Decimal(str(payload.get('PourCent', 100)))
        user_id = payload.get('UserID')
        broker_id = payload.get('UserExchangeID')
        interval = payload.get('Interval', 'N/A')

        logger.bind(trace_id=trace_id).info(
            f"Webhook recu: {symbol} {action} @ {prix} ({pour_cent}%)",
            symbol=symbol,
            action=action,
            prix=prix,
            pour_cent=str(pour_cent),
            user_id=user_id,
            broker_id=broker_id,
            interval=interval,
        )

        webhook = None
        try:
            # 1. SAUVEGARDER WEBHOOK EN DB
            webhook = await sync_to_async(Webhook.objects.create)(
                user_id=user_id,
                broker_id=broker_id,
                symbol=symbol,
                interval=interval,
                action=action,
                prix=Decimal(str(prix)) if prix else None,
                prix_sl=Decimal(str(prix_sl)) if prix_sl else None,
                prix_tp=Decimal(str(prix_tp)) if prix_tp else None,
                pour_cent=pour_cent,
                raw_payload=payload,
                status='processing',
                received_at=datetime.fromisoformat(received_at) if received_at else timezone.now()
            )

            logger.bind(trace_id=trace_id).info(
                "Webhook sauvegarde en DB",
                webhook_id=webhook.id,
            )

            # 2. ACTION PING - Ne rien faire
            if action == 'PING':
                await sync_to_async(self._update_webhook_status)(
                    webhook, 'processed', None
                )
                logger.bind(trace_id=trace_id).info("PING recu - Aucune action")
                self.webhooks_processed += 1
                return

            # 3. VALIDER EXCHANGE ACTIF
            broker = await sync_to_async(Broker.objects.get)(id=broker_id)

            if broker.type_de_trading != 'Webhooks':
                error_msg = (
                    f"Exchange {broker.name} pas configure pour webhooks "
                    f"(type_de_trading={broker.type_de_trading})"
                )
                logger.bind(trace_id=trace_id).warning(
                    "Exchange non active pour webhooks",
                    broker_name=broker.name,
                    type_de_trading=broker.type_de_trading,
                )
                await sync_to_async(self._update_webhook_status)(
                    webhook, 'error', error_msg
                )
                self.webhooks_errors += 1
                return

            # 4. EXECUTER ACTION
            if action in ['BuyMarket', 'SellMarket', 'BuyLimit', 'SellLimit']:
                await self.execute_order(webhook, broker, payload, trace_id)
            elif action == 'MAJ':
                await self.update_sl_tp(webhook, broker, payload, trace_id)
            else:
                error_msg = f"Action inconnue: {action}"
                logger.bind(trace_id=trace_id).error(
                    "Action webhook inconnue", action=action
                )
                await sync_to_async(self._update_webhook_status)(
                    webhook, 'error', error_msg
                )
                self.webhooks_errors += 1
                return

            self.webhooks_processed += 1

        except Broker.DoesNotExist:
            logger.bind(trace_id=trace_id).error(
                "Broker introuvable", broker_id=broker_id
            )
            if webhook:
                await sync_to_async(self._update_webhook_status)(
                    webhook, 'error', f"Broker {broker_id} introuvable"
                )
            self.webhooks_errors += 1
        except Exception as e:
            logger.bind(trace_id=trace_id).error(
                "Erreur process_webhook", error=str(e)
            )
            if webhook:
                await sync_to_async(self._update_webhook_status)(
                    webhook, 'error', str(e)
                )
            self.webhooks_errors += 1

    async def execute_order(self, webhook, broker, payload, trace_id):
        """
        Execute un ordre BuyMarket, SellMarket, BuyLimit, SellLimit
        """
        symbol = payload['Symbol']
        action = payload['Action']
        prix = payload.get('Prix')
        pour_cent = Decimal(str(payload.get('PourCent', 100)))

        side = 'buy' if 'Buy' in action else 'sell'
        order_type = 'market' if 'Market' in action else 'limit'

        logger.bind(trace_id=trace_id).info(
            f"Execution ordre: {side} {order_type} {symbol}",
            side=side,
            order_type=order_type,
            symbol=symbol,
            prix=prix,
            pour_cent=str(pour_cent),
        )

        if self.test_mode:
            logger.bind(trace_id=trace_id).info("MODE TEST - Ordre non execute")
            await sync_to_async(self._update_webhook_status)(
                webhook, 'processed', None, order_id='TEST_ORDER_123'
            )
            return

        try:
            exchange_client = ExchangeClient(user_id=webhook.user_id)
            exchange_client.trace_id = trace_id  # Propagation trace causale vers T5

            # Obtenir balance pour calculer quantite
            logger.bind(trace_id=trace_id).info(
                "Recuperation balance", broker_id=broker.id
            )
            balance_data = await exchange_client.get_balance(broker.id)

            # Balance USDT disponible
            # Format natif T5: {symbol: {available, frozen, total}}
            usdt_balance = Decimal('0')
            if 'USDT' in balance_data and isinstance(balance_data['USDT'], dict):
                usdt_balance = Decimal(str(balance_data['USDT'].get('available', 0)))
            elif 'free' in balance_data and 'USDT' in balance_data['free']:
                usdt_balance = Decimal(str(balance_data['free']['USDT']))

            logger.bind(trace_id=trace_id).info(
                f"Balance USDT: {usdt_balance}",
                usdt_balance=str(usdt_balance),
            )

            # Calculer quantite selon PourCent
            amount_usdt = usdt_balance * (pour_cent / Decimal('100'))

            if amount_usdt <= 0:
                logger.bind(trace_id=trace_id).error(
                    "Balance insuffisante",
                    usdt_balance=str(usdt_balance),
                    amount_usdt=str(amount_usdt),
                )
                await sync_to_async(self._update_webhook_status)(
                    webhook, 'error', f"Balance insuffisante: {usdt_balance} USDT"
                )
                return

            # Convertir symbol BTCUSDT -> BTC/USDT si necessaire
            if '/' not in symbol:
                symbol_unified = f"{symbol[:-4]}/{symbol[-4:]}"
            else:
                symbol_unified = symbol

            logger.bind(trace_id=trace_id).info(
                f"Ordre calcule: {amount_usdt} USDT @ {symbol_unified}",
                amount_usdt=str(amount_usdt),
                symbol_unified=symbol_unified,
            )

            # Executer via ExchangeClient (Terminal 5)
            order_params = {
                'broker_id': broker.id,
                'symbol': symbol_unified,
                'side': side,
                'amount': float(amount_usdt),
                'type': order_type,
            }

            if order_type == 'limit' and prix:
                order_params['price'] = float(prix)

            result = await exchange_client.place_order(**order_params)

            logger.bind(trace_id=trace_id).info(
                f"Ordre execute avec succes",
                order_id=result.get('id', 'N/A'),
                result=result,
            )

            # Sauvegarder resultat
            await sync_to_async(self._update_webhook_status)(
                webhook,
                'processed',
                None,
                order_id=result.get('id'),
                execution_result=result
            )

            self.orders_executed += 1

        except Exception as e:
            logger.bind(trace_id=trace_id).error(
                "Erreur execution ordre", error=str(e)
            )
            await sync_to_async(self._update_webhook_status)(
                webhook, 'error', f"Erreur execution ordre: {e}"
            )

    async def update_sl_tp(self, webhook, broker, payload, trace_id):
        """
        Mise a jour Stop Loss / Take Profit (action MAJ)
        """
        symbol = payload['Symbol']
        prix_sl = payload.get('PrixSL')
        prix_tp = payload.get('PrixTP')

        logger.bind(trace_id=trace_id).info(
            f"MAJ SL/TP: {symbol}",
            symbol=symbol,
            prix_sl=prix_sl,
            prix_tp=prix_tp,
        )

        if self.test_mode:
            logger.bind(trace_id=trace_id).info("MODE TEST - MAJ non executee")
            await sync_to_async(self._update_webhook_status)(
                webhook, 'processed', None
            )
            return

        # === IMPLEMENTATION COMPLETE MAJ SL/TP ===

        try:
            # 1. VERIFIER POSITION EXISTE (WebhookState status='open')
            logger.bind(trace_id=trace_id).info(
                "Recherche position active",
                symbol=symbol,
                broker_id=broker.id,
                user_id=webhook.user_id,
            )

            position = await sync_to_async(
                lambda: WebhookState.objects.filter(
                    user_id=webhook.user_id,
                    broker_id=broker.id,
                    symbol=symbol,
                    status='open'
                ).first()
            )()

            if not position:
                logger.bind(trace_id=trace_id).warning(
                    "Position absente - MAJ SL/TP impossible",
                    symbol=symbol,
                )
                await sync_to_async(self._update_webhook_status)(
                    webhook,
                    'processed',
                    f"Position {symbol} absente - MAJ SL/TP ignore"
                )
                return

            logger.bind(trace_id=trace_id).info(
                "Position trouvee",
                position_id=position.id,
                side=position.side,
                quantity=float(position.quantity),
            )

            # 2. ANNULER ANCIENS SL/TP (si existent)
            exchange_client = ExchangeClient(user_id=webhook.user_id)
            exchange_client.trace_id = trace_id

            # Annuler ancien SL si existe
            if position.sl_order_id:
                try:
                    logger.bind(trace_id=trace_id).info(
                        "Annulation ancien SL",
                        sl_order_id=position.sl_order_id,
                    )
                    await exchange_client.cancel_order(
                        broker_id=broker.id,
                        order_id=position.sl_order_id,
                        symbol=symbol
                    )
                    logger.bind(trace_id=trace_id).info("Ancien SL annule")
                except Exception as e:
                    logger.bind(trace_id=trace_id).warning(
                        "Echec annulation ancien SL (peut etre deja execute)",
                        error=str(e)
                    )
                    # CONTINUER quand meme

            # Annuler ancien TP si existe
            if position.tp_order_id:
                try:
                    logger.bind(trace_id=trace_id).info(
                        "Annulation ancien TP",
                        tp_order_id=position.tp_order_id,
                    )
                    await exchange_client.cancel_order(
                        broker_id=broker.id,
                        order_id=position.tp_order_id,
                        symbol=symbol
                    )
                    logger.bind(trace_id=trace_id).info("Ancien TP annule")
                except Exception as e:
                    logger.bind(trace_id=trace_id).warning(
                        "Echec annulation ancien TP (peut etre deja execute)",
                        error=str(e)
                    )
                    # CONTINUER quand meme

            # 3. CALCULER SIDE POUR SL/TP
            # LONG (position buy) → SL/TP = sell
            # SHORT (position sell) → SL/TP = buy
            sl_tp_side = 'sell' if position.side == 'buy' else 'buy'

            logger.bind(trace_id=trace_id).info(
                "Side calcule pour SL/TP",
                position_side=position.side,
                sl_tp_side=sl_tp_side,
            )

            # 4. CREER NOUVEAU SL (si prix fourni)
            new_sl_order_id = None
            if prix_sl:
                try:
                    prix_sl_decimal = Decimal(str(prix_sl))
                    logger.bind(trace_id=trace_id).info(
                        "Creation nouveau SL",
                        prix_sl=float(prix_sl_decimal),
                        quantity=float(position.quantity),
                        side=sl_tp_side,
                    )

                    sl_result = await exchange_client.place_order(
                        broker_id=broker.id,
                        symbol=symbol,
                        side=sl_tp_side,
                        amount=float(position.quantity),  # Toujours 100% position
                        order_type='stop_loss',
                        stop_price=float(prix_sl_decimal),
                    )

                    new_sl_order_id = sl_result.get('id')
                    logger.bind(trace_id=trace_id).info(
                        "Nouveau SL cree",
                        sl_order_id=new_sl_order_id,
                    )

                except Exception as e:
                    logger.bind(trace_id=trace_id).error(
                        "ECHEC creation SL - Terminal 7 reparera",
                        error=str(e),
                    )
                    # NE PAS STOPPER - laisser Terminal 7 reparer

            # 5. CREER NOUVEAU TP (si prix fourni)
            new_tp_order_id = None
            if prix_tp:
                try:
                    prix_tp_decimal = Decimal(str(prix_tp))
                    logger.bind(trace_id=trace_id).info(
                        "Creation nouveau TP",
                        prix_tp=float(prix_tp_decimal),
                        quantity=float(position.quantity),
                        side=sl_tp_side,
                    )

                    tp_result = await exchange_client.place_order(
                        broker_id=broker.id,
                        symbol=symbol,
                        side=sl_tp_side,
                        amount=float(position.quantity),  # Toujours 100% position
                        order_type='take_profit',
                        price=float(prix_tp_decimal),
                    )

                    new_tp_order_id = tp_result.get('id')
                    logger.bind(trace_id=trace_id).info(
                        "Nouveau TP cree",
                        tp_order_id=new_tp_order_id,
                    )

                except Exception as e:
                    logger.bind(trace_id=trace_id).error(
                        "ECHEC creation TP - Terminal 7 reparera",
                        error=str(e),
                    )
                    # NE PAS STOPPER - laisser Terminal 7 reparer

            # 6. METTRE A JOUR WebhookState
            def update_position():
                position.current_sl = Decimal(str(prix_sl)) if prix_sl else position.current_sl
                position.current_tp = Decimal(str(prix_tp)) if prix_tp else position.current_tp
                position.sl_order_id = new_sl_order_id or ''
                position.tp_order_id = new_tp_order_id or ''
                position.save()

            await sync_to_async(update_position)()

            logger.bind(trace_id=trace_id).info(
                "Position mise a jour",
                position_id=position.id,
                current_sl=float(position.current_sl) if position.current_sl else None,
                current_tp=float(position.current_tp) if position.current_tp else None,
                sl_order_id=position.sl_order_id,
                tp_order_id=position.tp_order_id,
            )

            # 7. MARQUER WEBHOOK PROCESSED
            await sync_to_async(self._update_webhook_status)(
                webhook,
                'processed',
                None,
                execution_result={
                    'sl_order_id': new_sl_order_id,
                    'tp_order_id': new_tp_order_id,
                    'position_id': position.id,
                }
            )

        except Exception as e:
            logger.bind(trace_id=trace_id).error(
                "Erreur MAJ SL/TP",
                error=str(e),
            )
            await sync_to_async(self._update_webhook_status)(
                webhook,
                'error',
                f"Erreur MAJ SL/TP: {e}"
            )

    def _update_webhook_status(self, webhook, status, error_msg=None, order_id=None, execution_result=None):
        """Helper sync pour mettre a jour webhook"""
        webhook.status = status
        if error_msg:
            webhook.error_message = error_msg
        if order_id:
            webhook.order_id = order_id
        if execution_result:
            webhook.execution_result = execution_result
        webhook.processed_at = timezone.now()
        webhook.save()

    async def stats_display_loop(self):
        """Affiche statistiques toutes les 60s"""
        while self.running:
            await asyncio.sleep(60)

            logger.info(
                "Statistiques periodiques",
                webhooks_processed=self.webhooks_processed,
                webhooks_errors=self.webhooks_errors,
                orders_executed=self.orders_executed,
            )

    async def cleanup(self):
        """Nettoyage ressources"""
        logger.info("Arret Trading Engine en cours")

        if self.redis_client:
            await self.redis_client.close()

        self.stdout.write(
            self.style.SUCCESS("✅ Trading Engine arrete proprement\n")
        )

    def shutdown(self, signum, frame):
        """Arret propre du service"""
        logger.info("Signal d'arret recu", signal=signum)
        self.running = False
        sys.exit(0)
