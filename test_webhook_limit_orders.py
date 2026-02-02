#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST WEBHOOKS - ORDRES LIMITE SÉCURISÉS

Stratégie de test intelligente :
- BUY Limit à 50% du prix actuel (jamais exécuté)
- SELL Limit à 200% du prix actuel (jamais exécuté)
- Ordres visibles sur exchange pour vérification
- Suppression manuelle après contrôle

PREREQUIS :
- Terminal 6 démarré
- Terminal 3 démarré SANS --test (pour ordres réels)
- Terminal 5 démarré
- Broker configuré : python configure_test_broker.py
- TESTNET recommandé (is_testnet=True) OU petits montants
"""
import requests
import json
import time
import sys
import os
import django
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.brokers.models import Broker
from apps.webhooks.models import Webhook

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
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{C.BLUE}╔{'═' * 70}╗")
    print(f"║ {text:^68} ║")
    print(f"╚{'═' * 70}╝{C.RESET}\n")

def print_warning(text):
    print(f"{C.YELLOW}⚠️  {text}{C.RESET}")

def get_current_price(symbol="BTCUSDT"):
    """
    Récupère le prix actuel depuis Binance API publique
    (pas besoin d'authentification)
    """
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = float(data['price'])
            return price
        else:
            return None
    except Exception as e:
        print(f"  {C.RED}❌ Erreur récupération prix: {e}{C.RESET}")
        return None

def calculate_safe_prices(current_price):
    """
    Calcule les prix sécurisés pour ordres limite

    BUY: 50% du prix actuel (trop bas, jamais exécuté)
    SELL: 200% du prix actuel (trop haut, jamais exécuté)
    """
    buy_price = current_price * 0.5   # 50% du prix
    sell_price = current_price * 2.0  # 200% du prix

    return {
        'current': current_price,
        'buy_limit': round(buy_price, 2),
        'sell_limit': round(sell_price, 2)
    }

def check_broker_config():
    """Vérifie configuration broker"""
    print(f"{C.CYAN}[CONFIG]{C.RESET} Vérification broker...")

    try:
        broker = Broker.objects.filter(
            type_de_trading='Webhooks',
            is_active=True
        ).first()

        if not broker:
            print(f"  {C.RED}❌ Aucun broker configuré pour webhooks{C.RESET}")
            print(f"\n  Lance d'abord: python configure_test_broker.py\n")
            return None

        print(f"  {C.GREEN}✅ Broker trouvé: {broker.name}{C.RESET}")
        print(f"     ID: {broker.id}")
        print(f"     Exchange: {broker.exchange}")
        print(f"     User: {broker.user.username}")
        print(f"     Testnet: {broker.is_testnet}")

        # Avertissement si pas en testnet
        if not broker.is_testnet:
            print(f"\n  {C.YELLOW}⚠️  ATTENTION: Broker en mode PRODUCTION{C.RESET}")
            print(f"     Les ordres seront passés avec de l'argent RÉEL")
            print(f"     Recommandation: Utilise un broker en testnet")

            response = input(f"\n  Continuer quand même ? (oui/non): ")
            if response.lower() != 'oui':
                print(f"\n  {C.YELLOW}Test annulé{C.RESET}\n")
                return None

        return broker

    except Exception as e:
        print(f"  {C.RED}❌ Erreur: {e}{C.RESET}")
        return None

def send_webhook(payload, description):
    """Envoie un webhook"""
    print(f"\n{C.CYAN}[WEBHOOK]{C.RESET} {description}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")

    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Token': WEBHOOK_TOKEN
    }

    try:
        start = time.time()
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            print(f"  {C.GREEN}✅ Webhook envoyé{C.RESET} ({elapsed:.0f}ms)")
            return True
        else:
            print(f"  {C.RED}❌ Erreur {response.status_code}{C.RESET}")
            return False

    except Exception as e:
        print(f"  {C.RED}❌ Erreur: {e}{C.RESET}")
        return False

def wait_for_webhook_processing(action, max_wait=10):
    """Attend que le webhook soit traité"""
    print(f"  {C.YELLOW}[WAIT]{C.RESET} Attente traitement Terminal 3...")

    for i in range(max_wait):
        time.sleep(1)
        webhook = Webhook.objects.filter(action=action).order_by('-id').first()

        if webhook and webhook.status in ['processed', 'error']:
            status_color = C.GREEN if webhook.status == 'processed' else C.RED
            status_icon = "✅" if webhook.status == 'processed' else "❌"

            print(f"  {status_color}{status_icon} Webhook traité{C.RESET}")
            print(f"     Status: {webhook.status}")

            if webhook.order_id:
                print(f"     {C.GREEN}Order ID: {webhook.order_id}{C.RESET}")

            if webhook.error_message:
                print(f"     Erreur: {webhook.error_message}")

            return webhook

    print(f"  {C.YELLOW}⏰ Timeout après {max_wait}s{C.RESET}")
    return None

def main():
    print_header("TEST WEBHOOKS - ORDRES LIMITE SÉCURISÉS")

    # 1. Vérification broker
    print_header("ÉTAPE 1 : VÉRIFICATION CONFIGURATION")
    broker = check_broker_config()

    if not broker:
        return

    user_id = broker.user.id
    broker_id = broker.id

    # 2. Récupération prix actuel
    print_header("ÉTAPE 2 : RÉCUPÉRATION PRIX ACTUEL")

    symbol = "BTCUSDT"
    print(f"  Symbol: {symbol}")
    print(f"  Source: Binance API publique")

    current_price = get_current_price(symbol)

    if not current_price:
        print(f"\n  {C.RED}❌ Impossible de récupérer le prix actuel{C.RESET}")
        return

    # 3. Calcul prix sécurisés
    prices = calculate_safe_prices(current_price)

    print(f"\n  {C.GREEN}✅ Prix récupéré: ${prices['current']:,.2f}{C.RESET}")
    print(f"\n  {C.CYAN}Prix calculés pour ordres limite :{C.RESET}")
    print(f"     BUY Limit:  ${prices['buy_limit']:,.2f}  (50% du prix actuel)")
    print(f"     SELL Limit: ${prices['sell_limit']:,.2f}  (200% du prix actuel)")

    print(f"\n  {C.MAGENTA}💡 Stratégie:{C.RESET}")
    print(f"     - Ces ordres ne seront JAMAIS exécutés")
    print(f"     - Ils apparaîtront sur l'exchange")
    print(f"     - Tu pourras les voir et les supprimer manuellement")

    # 4. Confirmation utilisateur
    print_header("ÉTAPE 3 : CONFIRMATION")

    print_warning("IMPORTANT: Terminal 3 doit être lancé SANS --test")
    print_warning("Commande: python manage.py run_trading_engine")
    print()

    response = input(f"  {C.CYAN}Lancer les tests ? (oui/non): {C.RESET}")

    if response.lower() != 'oui':
        print(f"\n  {C.YELLOW}Test annulé{C.RESET}\n")
        return

    # 5. Test BUY Limit
    print_header("ÉTAPE 4 : TEST BUY LIMIT (50% du prix)")

    payload_buy = {
        "Symbol": symbol,
        "Exchange": broker.exchange.upper(),
        "Interval": "15m",
        "Action": "BuyLimit",
        "Prix": prices['buy_limit'],
        "PourCent": 5,  # 5% de la balance seulement
        "UserID": user_id,
        "UserExchangeID": broker_id
    }

    if send_webhook(payload_buy, f"BuyLimit @ ${prices['buy_limit']:,.2f}"):
        webhook = wait_for_webhook_processing('BuyLimit')

        if webhook and webhook.status == 'processed' and webhook.order_id:
            print(f"\n  {C.GREEN}🎉 ORDRE BUY PASSÉ SUR L'EXCHANGE !{C.RESET}")
            print(f"\n  {C.CYAN}Prochaines actions :{C.RESET}")
            print(f"     1. Connecte-toi à {broker.exchange}")
            print(f"     2. Va dans 'Ordres ouverts'")
            print(f"     3. Cherche l'ordre ID: {webhook.order_id}")
            print(f"     4. Vérifie qu'il est bien à ${prices['buy_limit']:,.2f}")
            print(f"     5. Supprime-le manuellement")

    time.sleep(3)

    # 6. Test SELL Limit
    print_header("ÉTAPE 5 : TEST SELL LIMIT (200% du prix)")

    payload_sell = {
        "Symbol": symbol,
        "Exchange": broker.exchange.upper(),
        "Interval": "15m",
        "Action": "SellLimit",
        "Prix": prices['sell_limit'],
        "PourCent": 5,  # 5% de la balance seulement
        "UserID": user_id,
        "UserExchangeID": broker_id
    }

    if send_webhook(payload_sell, f"SellLimit @ ${prices['sell_limit']:,.2f}"):
        webhook = wait_for_webhook_processing('SellLimit')

        if webhook and webhook.status == 'processed' and webhook.order_id:
            print(f"\n  {C.GREEN}🎉 ORDRE SELL PASSÉ SUR L'EXCHANGE !{C.RESET}")
            print(f"\n  {C.CYAN}Prochaines actions :{C.RESET}")
            print(f"     1. Connecte-toi à {broker.exchange}")
            print(f"     2. Va dans 'Ordres ouverts'")
            print(f"     3. Cherche l'ordre ID: {webhook.order_id}")
            print(f"     4. Vérifie qu'il est bien à ${prices['sell_limit']:,.2f}")
            print(f"     5. Supprime-le manuellement")

    # 7. Résumé final
    print_header("RÉSUMÉ DES ORDRES PASSÉS")

    recent_webhooks = Webhook.objects.filter(
        action__in=['BuyLimit', 'SellLimit']
    ).order_by('-id')[:2]

    print(f"  {C.CYAN}Ordres créés :{C.RESET}\n")

    for wh in recent_webhooks:
        status_color = C.GREEN if wh.status == 'processed' else C.RED
        print(f"  {status_color}• {wh.action}{C.RESET}")
        print(f"    Prix: ${wh.prix}")
        print(f"    Order ID: {wh.order_id or 'N/A'}")
        print(f"    Status: {wh.status}")
        print()

    print(f"  {C.MAGENTA}📋 Checklist finale :{C.RESET}")
    print(f"     □ Vérifier ordres sur {broker.exchange}")
    print(f"     □ Confirmer qu'ils ne sont PAS exécutés")
    print(f"     □ Les supprimer manuellement")
    print(f"     □ Lancer: python configure_test_broker.py reset")
    print()

if __name__ == '__main__':
    main()
