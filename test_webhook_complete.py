#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST COMPLET MODULE 4 - FLUX BOUT-EN-BOUT

Teste le flux complet :
TradingView → Terminal 6 → Redis → Terminal 3 → (Terminal 5) → DB

PREREQUIS :
1. Terminal 6 demarre (python manage.py run_webhook_receiver)
2. Terminal 3 demarre (python manage.py run_trading_engine --test)
3. Redis actif
4. PostgreSQL actif
"""
import requests
import json
import time
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.webhooks.models import Webhook
from apps.brokers.models import Broker

# Configuration
WEBHOOK_URL = "http://localhost:8888/webhook"
WEBHOOK_TOKEN = "aristobot_webhook_secret_dev_2026"

# Couleurs
class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{C.BLUE}╔{'═' * 60}╗")
    print(f"║ {text:^58} ║")
    print(f"╚{'═' * 60}╝{C.RESET}\n")

def check_broker_config():
    """Verifie qu'un broker est configure pour webhooks"""
    print(f"{C.YELLOW}[CHECK]{C.RESET} Verification configuration broker...")

    try:
        webhook_broker = Broker.objects.filter(
            type_de_trading='Webhooks',
            is_active=True
        ).first()

        if webhook_broker:
            print(f"  {C.GREEN}✅ Broker webhook trouve: {webhook_broker.name}{C.RESET}")
            print(f"     ID: {webhook_broker.id}")
            print(f"     Exchange: {webhook_broker.exchange}")
            print(f"     User: {webhook_broker.user.username}")
            return webhook_broker
        else:
            print(f"  {C.RED}❌ Aucun broker configure pour webhooks{C.RESET}")
            print(f"\n  {C.YELLOW}ACTION REQUISE:{C.RESET}")
            print(f"  Lance d'abord :")
            print(f"  {C.CYAN}python configure_test_broker.py{C.RESET}")
            print(f"\n  Cela configurera automatiquement le broker ID 13 (Bitget dev)")
            print(f"  pour les tests webhooks.\n")
            return None

    except Exception as e:
        print(f"  {C.RED}❌ Erreur: {e}{C.RESET}")
        return None

def send_webhook(payload, description):
    """Envoie un webhook"""
    print(f"\n{C.CYAN}[WEBHOOK]{C.RESET} {description}")

    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Token': WEBHOOK_TOKEN
    }

    try:
        start = time.time()
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            print(f"  {C.GREEN}✅ Webhook envoye{C.RESET} ({elapsed:.0f}ms)")
            return True
        else:
            print(f"  {C.RED}❌ Erreur {response.status_code}{C.RESET}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  {C.RED}❌ Terminal 6 non accessible{C.RESET}")
        print(f"     Lance: python manage.py run_webhook_receiver")
        return False
    except Exception as e:
        print(f"  {C.RED}❌ Exception: {e}{C.RESET}")
        return False

def check_webhook_in_db(expected_action, max_wait=5):
    """Verifie que le webhook est dans la DB"""
    print(f"  {C.YELLOW}[DB]{C.RESET} Attente traitement Terminal 3...")

    for i in range(max_wait):
        time.sleep(1)
        webhook = Webhook.objects.filter(action=expected_action).order_by('-id').first()

        if webhook:
            status_color = C.GREEN if webhook.status == 'processed' else C.RED
            print(f"  {status_color}✅ Webhook trouve en DB{C.RESET}")
            print(f"     Status: {webhook.status}")
            print(f"     Action: {webhook.action}")
            if webhook.order_id:
                print(f"     Order ID: {webhook.order_id}")
            if webhook.error_message:
                print(f"     Erreur: {webhook.error_message}")
            return webhook

    print(f"  {C.RED}❌ Webhook non trouve en DB apres {max_wait}s{C.RESET}")
    print(f"     Terminal 3 demarre ?")
    return None

def main():
    print_header("TEST COMPLET MODULE 4 - WEBHOOKS")

    # 1. Verification broker
    print_header("ETAPE 1 : VERIFICATION CONFIGURATION")
    broker = check_broker_config()

    if not broker:
        print(f"\n{C.RED}[STOP] Test arrete - Configuration incomplete{C.RESET}\n")
        return

    user_id = broker.user.id
    broker_id = broker.id

    # 2. Test PING (ne fait rien)
    print_header("ETAPE 2 : TEST PING")
    payload_ping = {
        "Symbol": "BTCUSDT",
        "Exchange": "BINANCE",
        "Interval": "5m",
        "Action": "PING",
        "Prix": 43000.0,
        "UserID": user_id,
        "UserExchangeID": broker_id
    }

    if send_webhook(payload_ping, "PING (heartbeat)"):
        check_webhook_in_db('PING')

    time.sleep(2)

    # 3. Test BuyMarket MODE TEST
    print_header("ETAPE 3 : TEST BUY MARKET (MODE TEST)")
    payload_buy = {
        "Symbol": "BTCUSDT",
        "Exchange": broker.exchange.upper(),
        "Interval": "15m",
        "Action": "BuyMarket",
        "Prix": 43500.0,
        "PourCent": 10,  # 10% de la balance
        "UserID": user_id,
        "UserExchangeID": broker_id
    }

    if send_webhook(payload_buy, "BuyMarket 10%"):
        webhook = check_webhook_in_db('BuyMarket')
        if webhook and webhook.status == 'processed':
            print(f"\n  {C.GREEN}✅ TEST BUY REUSSI{C.RESET}")
        elif webhook and webhook.status == 'error':
            print(f"\n  {C.YELLOW}⚠️ Webhook traite avec erreur (normal si balance = 0){C.RESET}")

    time.sleep(2)

    # 4. Test MAJ SL/TP
    print_header("ETAPE 4 : TEST MAJ SL/TP")
    payload_maj = {
        "Symbol": "BTCUSDT",
        "Exchange": broker.exchange.upper(),
        "Interval": "15m",
        "Action": "MAJ",
        "Prix": 44000.0,
        "PrixSL": 42000.0,
        "PrixTP": 46000.0,
        "PourCent": 100,
        "UserID": user_id,
        "UserExchangeID": broker_id
    }

    if send_webhook(payload_maj, "MAJ SL/TP"):
        check_webhook_in_db('MAJ')

    # 5. Statistiques finales
    print_header("STATISTIQUES FINALES")

    total_webhooks = Webhook.objects.count()
    processed = Webhook.objects.filter(status='processed').count()
    errors = Webhook.objects.filter(status='error').count()

    print(f"  Total webhooks: {total_webhooks}")
    print(f"  Processed: {C.GREEN}{processed}{C.RESET}")
    print(f"  Errors: {C.RED}{errors}{C.RESET}")

    # 6. Conclusion
    print_header("CONCLUSION")

    if processed > 0:
        print(f"{C.GREEN}✅ MODULE 4 FONCTIONNE !{C.RESET}\n")
        print("Flux valide :")
        print("  TradingView → Terminal 6 → Redis → Terminal 3 → DB\n")
        print("Prochaines etapes :")
        print("  - Tache #4 : APIs REST pour frontend")
        print("  - Tache #5 : Interface Vue.js WebhooksView")
    else:
        print(f"{C.RED}❌ PROBLEMES DETECTES{C.RESET}\n")
        print("Verifie :")
        print("  - Terminal 6 demarre ?")
        print("  - Terminal 3 demarre ?")
        print("  - Redis accessible ?")
        print("  - Logs Terminal 3 pour erreurs")

    print()

if __name__ == '__main__':
    main()
