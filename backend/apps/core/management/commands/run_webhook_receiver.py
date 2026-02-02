# -*- coding: utf-8 -*-
"""
TERMINAL 6 - WEBHOOK RECEIVER SERVICE

Service HTTP minimaliste pour reception webhooks TradingView
- Port 8888 (configurable)
- Endpoint POST /webhook
- Validation token X-Webhook-Token
- Generation trace_id UUID pour propagation
- Sauvegarde DB immediate (TOUS les webhooks y compris PING)
- Publication Redis canal 'webhook_raw'
- Reponse rapide < 100ms
- AUCUNE logique metier
"""
import asyncio
import json
import signal
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from aiohttp import web
import redis.asyncio as redis
from django.core.management.base import BaseCommand
from django.conf import settings
from asgiref.sync import sync_to_async
from loguru import logger
from apps.core.services.loguru_config import setup_loguru
from apps.webhooks.models import Webhook


class Command(BaseCommand):
    help = 'Lance le service de reception webhooks TradingView (Terminal 6)'

    def __init__(self):
        super().__init__()
        self.app = None
        self.runner = None
        self.site = None
        self.redis_client = None
        self.running = True

        # Configuration
        self.port = 8888
        self.host = '0.0.0.0'

        self.webhook_token = getattr(settings, 'WEBHOOK_TOKEN', 'CHANGE_ME_IN_PRODUCTION')

        # Statistiques
        self.webhooks_received = 0
        self.webhooks_rejected = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            default=8888,
            help='Port du serveur HTTP (defaut: 8888)',
        )
        parser.add_argument(
            '--host',
            type=str,
            default='0.0.0.0',
            help='Host du serveur HTTP (defaut: 0.0.0.0)',
        )

    def handle(self, *args, **options):
        setup_loguru("terminal6")

        self.port = options['port']
        self.host = options['host']

        # Gerer l'arret propre
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n"
                f"╔════════════════════════════════════════════════╗\n"
                f"║     TERMINAL 6 - WEBHOOK RECEIVER SERVICE     ║\n"
                f"╚════════════════════════════════════════════════╝\n"
                f"  Port: {self.port}\n"
                f"  Host: {self.host}\n"
                f"  Endpoint: POST /webhook\n"
                f"  Token header: X-Webhook-Token\n"
                f"\n"
            )
        )

        logger.info(
            "Service Webhook Receiver demarre",
            host=self.host,
            port=self.port,
        )

        # Lancer le serveur
        asyncio.run(self.run_server())

    async def run_server(self):
        """Demarre le serveur HTTP aiohttp"""
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

            # Configuration aiohttp
            self.app = web.Application()
            self.app.router.add_post('/webhook', self.handle_webhook)
            self.app.router.add_get('/health', self.handle_health)

            # Demarrage serveur
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Terminal 6 demarre sur http://{self.host}:{self.port}\n"
                    f"   En attente de webhooks TradingView...\n"
                )
            )

            # Boucle principale
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error("Erreur demarrage Terminal 6", error=str(e))
            raise
        finally:
            await self.cleanup()

    async def handle_webhook(self, request):
        """
        Endpoint POST /webhook
        Recoit webhooks TradingView, genere trace_id, publie sur Redis
        """
        start_time = asyncio.get_event_loop().time()

        # Generation du trace_id au point d'entree
        trace_id = str(uuid.uuid4())

        try:
            # 1. Validation token
            token = request.headers.get('X-Webhook-Token', '')

            if token != self.webhook_token:
                self.webhooks_rejected += 1
                logger.bind(trace_id=trace_id).warning(
                    "Webhook rejete: token invalide",
                    source_ip=request.remote,
                )
                return web.json_response(
                    {'error': 'Invalid token'},
                    status=401
                )

            # 2. Recuperer payload JSON
            try:
                data = await request.json()
            except Exception as e:
                logger.bind(trace_id=trace_id).error(
                    "Erreur parsing JSON", error=str(e)
                )
                return web.json_response(
                    {'error': 'Invalid JSON'},
                    status=400
                )

            # 3. Construire message avec trace_id pour propagation
            webhook_message = {
                'payload': data,
                'received_at': datetime.utcnow().isoformat(),
                'source_ip': request.remote,
                'trace_id': trace_id,
            }

            # 4. NOUVEAU: Sauvegarder en DB immediatement (y compris PING)
            try:
                # Extraction champs avec gestion valeurs manquantes
                user_id = data.get('UserID')
                broker_id = data.get('UserExchangeID')
                symbol = data.get('Symbol', 'UNKNOWN')
                exchange_name = data.get('Exchange', '')
                interval = data.get('Interval', '')
                action = data.get('Action', 'PING')

                # Prix optionnels
                prix = Decimal(str(data['Prix'])) if data.get('Prix') else None
                prix_sl = Decimal(str(data['PrixSL'])) if data.get('PrixSL') else None
                prix_tp = Decimal(str(data['PrixTP'])) if data.get('PrixTP') else None
                pour_cent = Decimal(str(data.get('PourCent', 100)))

                # Parsing bar_time si present
                bar_time = None
                if data.get('BarTime'):
                    try:
                        bar_time = datetime.fromisoformat(data['BarTime'].replace('Z', '+00:00'))
                    except:
                        pass

                # Sauvegarde DB (sync_to_async)
                webhook = await sync_to_async(Webhook.objects.create)(
                    user_id=user_id,
                    broker_id=broker_id,
                    symbol=symbol,
                    exchange_name=exchange_name,
                    interval=interval,
                    action=action,
                    prix=prix,
                    prix_sl=prix_sl,
                    prix_tp=prix_tp,
                    pour_cent=pour_cent,
                    bar_time=bar_time,
                    status='received',
                    raw_payload=data,
                )

                logger.bind(trace_id=trace_id).info(
                    "Webhook enregistre en DB",
                    webhook_id=webhook.id,
                    symbol=symbol,
                    action=action,
                )

            except Exception as e:
                logger.bind(trace_id=trace_id).error(
                    "Erreur sauvegarde webhook DB",
                    error=str(e),
                    payload=data,
                )
                # CONTINUER meme si DB fail - publier sur Redis quand meme

            # 5. Publier sur Redis (canal webhook_raw)
            await self.redis_client.publish(
                'webhook_raw',
                json.dumps(webhook_message)
            )

            logger.bind(trace_id=trace_id).debug(
                "Webhook publie sur Redis canal webhook_raw"
            )

            # 6. Statistiques et log structure
            self.webhooks_received += 1
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000

            logger.bind(trace_id=trace_id).info(
                f"Webhook complete: {data.get('Symbol', 'N/A')} {data.get('Action', 'N/A')}",
                symbol=data.get('Symbol', 'N/A'),
                action=data.get('Action', 'N/A'),
                elapsed_ms=round(elapsed, 1),
                source_ip=request.remote,
            )

            # 7. Reponse rapide
            return web.json_response(
                {
                    'status': 'received',
                    'timestamp': webhook_message['received_at'],
                    'trace_id': trace_id,
                },
                status=200
            )

        except Exception as e:
            logger.bind(trace_id=trace_id).error(
                "Erreur traitement webhook", error=str(e)
            )
            return web.json_response(
                {'error': 'Internal server error'},
                status=500
            )

    async def handle_health(self, request):
        """Endpoint GET /health pour monitoring"""
        try:
            await self.redis_client.ping()
            redis_status = 'ok'
        except Exception:
            redis_status = 'error'

        return web.json_response({
            'status': 'running',
            'redis': redis_status,
            'webhooks_received': self.webhooks_received,
            'webhooks_rejected': self.webhooks_rejected,
        })

    async def cleanup(self):
        """Nettoyage ressources"""
        logger.info("Arret Terminal 6 en cours")

        if self.site:
            await self.site.stop()

        if self.runner:
            await self.runner.cleanup()

        if self.redis_client:
            await self.redis_client.close()

        self.stdout.write(
            self.style.SUCCESS("✅ Terminal 6 arrete proprement\n")
        )

    def shutdown(self, signum, frame):
        """Arret propre du service"""
        logger.info("Signal d'arret recu", signal=signum)
        self.running = False
        sys.exit(0)
