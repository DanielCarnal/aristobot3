#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST PRODUCTION - 5$ MAXIMUM

Test pragmatique avec argent réel, risque minimal :
- Montant total : 5 USDT maximum
- Ordres limites à 50%/200% (garantis non-fill)
- Vérification et suppression immédiate

PREREQUIS :
- Balance minimum 5 USDT sur broker
- Terminal 6, 3, 5 démarrés
- Broker configuré pour webhooks
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

def get_current_price(symbol="BTCUSDT"):
    """Récupère prix actuel Binance API publique"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return float(response.json()['price'])
    except:
        pass
    return None

def main():
    print(f"""
{C.BLUE}╔═══════════════════════════════════════════════════════════════╗
║          TEST PRODUCTION - 5$ MAXIMUM                         ║
╚═══════════════════════════════════════════════════════════════╝{C.RESET}

{C.CYAN}Stratégie :{C.RESET}
  • Montant total : 5 USDT maximum
  • 2 ordres de 2.50 USDT chacun (50% de 5$)
  • BUY Limit @ 50% prix actuel (jamais fill)
  • SELL Limit @ 200% prix actuel (jamais fill)

{C.GREEN}Sécurité :{C.RESET}
  • Risque financier : ~0$ (ordres garantis non-fill)
  • Suppression manuelle après vérification
  • Test complet flux bout-en-bout

{C.YELLOW}⚠️  IMPORTANT :{C.RESET}
  • Terminal 3 doit être lancé SANS --test
  • Vérifie que tu as au moins 5 USDT de balance
  • Prêt à supprimer ordres rapidement sur l'exchange
""")

    # Vérification broker
    broker = Broker.objects.filter(
        type_de_trading='Webhooks',
        is_active=True
    ).first()

    if not broker:
        print(f"{C.RED}❌ Aucun broker configuré pour webhooks{C.RESET}")
        print(f"Lance: python configure_test_broker.py\n")
        return

    print(f"{C.GREEN}✅ Broker configuré:{C.RESET} {broker.name} ({broker.exchange})")
    print(f"   User: {broker.user.username}")
    print(f"   Production: {not broker.is_testnet}")

    # Récupération prix
    symbol = "BTCUSDT"
    current_price = get_current_price(symbol)

    if not current_price:
        print(f"\n{C.RED}❌ Impossible de récupérer le prix BTC{C.RESET}\n")
        return

    buy_price = round(current_price * 0.5, 2)
    sell_price = round(current_price * 2.0, 2)

    print(f"\n{C.CYAN}Prix calculés :{C.RESET}")
    print(f"   Prix actuel BTC: ${current_price:,.2f}")
    print(f"   BUY Limit:  ${buy_price:,.2f}  (50% du prix)")
    print(f"   SELL Limit: ${sell_price:,.2f}  (200% du prix)")

    # Confirmation
    print(f"\n{C.YELLOW}═══════════════════════════════════════════════════════════════")
    print(f"CONFIRMATION REQUISE")
    print(f"═══════════════════════════════════════════════════════════════{C.RESET}")
    print(f"\nTu vas passer 2 ordres RÉELS (mais garantis non-fill) :")
    print(f"  1. BUY {symbol} @ ${buy_price:,.2f} pour ~2.50 USDT")
    print(f"  2. SELL {symbol} @ ${sell_price:,.2f} pour ~2.50 USDT")
    print(f"\nRisque financier : ~0$ (prix garantis non-fill)")
    print(f"Coût maximum théorique : 5 USDT\n")

    response = input(f"{C.CYAN}Continuer ? (tape 'OUI' en majuscules): {C.RESET}")

    if response != 'OUI':
        print(f"\n{C.YELLOW}Test annulé{C.RESET}\n")
        return

    # Envoi webhooks
    print(f"\n{C.GREEN}╔═══════════════════════════════════════════════════════════════╗")
    print(f"║                    ENVOI WEBHOOKS                             ║")
    print(f"╚═══════════════════════════════════════════════════════════════╝{C.RESET}\n")

    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Token': WEBHOOK_TOKEN
    }

    # BUY Limit
    payload_buy = {
        "Symbol": symbol,
        "Exchange": broker.exchange.upper(),
        "Interval": "15m",
        "Action": "BuyLimit",
        "Prix": buy_price,
        "PourCent": 50,  # 50% de 5$ = 2.50$
        "UserID": broker.user.id,
        "UserExchangeID": broker.id
    }

    print(f"{C.CYAN}[1/2]{C.RESET} Envoi BUY Limit @ ${buy_price:,.2f}...")
    try:
        r = requests.post(WEBHOOK_URL, json=payload_buy, headers=headers, timeout=5)
        if r.status_code == 200:
            print(f"      {C.GREEN}✅ Webhook envoyé{C.RESET}")
        else:
            print(f"      {C.RED}❌ Erreur {r.status_code}{C.RESET}")
    except Exception as e:
        print(f"      {C.RED}❌ Erreur: {e}{C.RESET}")

    time.sleep(2)

    # SELL Limit
    payload_sell = {
        "Symbol": symbol,
        "Exchange": broker.exchange.upper(),
        "Interval": "15m",
        "Action": "SellLimit",
        "Prix": sell_price,
        "PourCent": 50,  # 50% de 5$ = 2.50$
        "UserID": broker.user.id,
        "UserExchangeID": broker.id
    }

    print(f"{C.CYAN}[2/2]{C.RESET} Envoi SELL Limit @ ${sell_price:,.2f}...")
    try:
        r = requests.post(WEBHOOK_URL, json=payload_sell, headers=headers, timeout=5)
        if r.status_code == 200:
            print(f"      {C.GREEN}✅ Webhook envoyé{C.RESET}")
        else:
            print(f"      {C.RED}❌ Erreur {r.status_code}{C.RESET}")
    except Exception as e:
        print(f"      {C.RED}❌ Erreur: {e}{C.RESET}")

    # Attente traitement
    print(f"\n{C.YELLOW}[WAIT]{C.RESET} Attente traitement Terminal 3 (10s)...")
    time.sleep(10)

    # Vérification DB
    recent_webhooks = Webhook.objects.filter(
        action__in=['BuyLimit', 'SellLimit']
    ).order_by('-id')[:2]

    print(f"\n{C.GREEN}╔═══════════════════════════════════════════════════════════════╗")
    print(f"║                  RÉSULTATS EN BASE DE DONNÉES                 ║")
    print(f"╚═══════════════════════════════════════════════════════════════╝{C.RESET}\n")

    for wh in recent_webhooks:
        status_color = C.GREEN if wh.status == 'processed' else C.RED
        status_icon = "✅" if wh.status == 'processed' else "❌"

        print(f"{status_color}{status_icon} {wh.action}{C.RESET}")
        print(f"   Prix: ${wh.prix}")
        print(f"   Order ID: {C.GREEN}{wh.order_id or 'N/A'}{C.RESET}")
        print(f"   Status: {wh.status}")
        if wh.error_message:
            print(f"   Erreur: {wh.error_message}")
        print()

    # Instructions finales
    print(f"{C.MAGENTA}╔═══════════════════════════════════════════════════════════════╗")
    print(f"║                  PROCHAINES ACTIONS                           ║")
    print(f"╚═══════════════════════════════════════════════════════════════╝{C.RESET}\n")

    print(f"{C.CYAN}1. VÉRIFIER SUR L'EXCHANGE :{C.RESET}")
    print(f"   • Connecte-toi sur {broker.exchange}")
    print(f"   • Va dans 'Ordres' → 'Ordres ouverts'")
    print(f"   • Cherche les 2 ordres (BUY {buy_price}, SELL {sell_price})")
    print(f"   • Vérifie qu'ils sont en status 'Open' (PAS exécutés)")

    print(f"\n{C.CYAN}2. SUPPRIMER LES ORDRES :{C.RESET}")
    print(f"   • Sélectionne chaque ordre")
    print(f"   • Clique 'Annuler' ou 'Cancel'")
    print(f"   • Confirme la suppression")

    print(f"\n{C.CYAN}3. NETTOYAGE :{C.RESET}")
    print(f"   • Lance: python configure_test_broker.py reset")

    print(f"\n{C.GREEN}🎉 TEST TERMINÉ !{C.RESET}")
    print(f"\nSi les ordres sont visibles sur l'exchange :")
    print(f"  → {C.GREEN}✅ MODULE 4 FONCTIONNE PARFAITEMENT !{C.RESET}\n")

if __name__ == '__main__':
    main()
