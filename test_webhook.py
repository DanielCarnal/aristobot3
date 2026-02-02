#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE TEST - TERMINAL 6 WEBHOOK RECEIVER

Simule des webhooks TradingView pour tester Terminal 6
"""
import requests
import json
import time
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:8888/webhook"
WEBHOOK_TOKEN = "aristobot_webhook_secret_dev_2026"

# Couleurs pour affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def send_webhook(payload, description=""):
    """Envoie un webhook et affiche le resultat"""
    print(f"\n{Colors.BLUE}[TEST]{Colors.RESET} {description}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")

    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Token': WEBHOOK_TOKEN
    }

    try:
        start = time.time()
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            print(f"  {Colors.GREEN}✅ SUCCESS{Colors.RESET} ({response.status_code}) - {elapsed:.0f}ms")
            print(f"  Response: {response.json()}")
        else:
            print(f"  {Colors.RED}❌ ERROR{Colors.RESET} ({response.status_code})")
            print(f"  Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"  {Colors.RED}❌ CONNECTION ERROR{Colors.RESET}")
        print(f"  Terminal 6 n'est pas demarre ou port 8888 inaccessible")
    except Exception as e:
        print(f"  {Colors.RED}❌ EXCEPTION{Colors.RESET}: {e}")

def test_health():
    """Test endpoint /health"""
    print(f"\n{Colors.BLUE}[TEST]{Colors.RESET} Health Check")
    try:
        response = requests.get("http://localhost:8888/health")
        if response.status_code == 200:
            print(f"  {Colors.GREEN}✅ Terminal 6 is running{Colors.RESET}")
            print(f"  Stats: {response.json()}")
        else:
            print(f"  {Colors.RED}❌ Unexpected status: {response.status_code}{Colors.RESET}")
    except:
        print(f"  {Colors.RED}❌ Terminal 6 not running{Colors.RESET}")

def main():
    """Tests complets"""
    print(f"""
{Colors.YELLOW}╔════════════════════════════════════════════════╗
║        TEST TERMINAL 6 - WEBHOOK RECEIVER      ║
╚════════════════════════════════════════════════╝{Colors.RESET}
""")

    # Test 1: Health check
    test_health()

    # Test 2: PING (ne fait rien)
    send_webhook(
        {
            "Symbol": "BTCUSDT",
            "Exchange": "BINANCE",
            "Interval": "5m",
            "Action": "PING",
            "Prix": 43000.0,
            "UserID": 1,
            "UserExchangeID": 13
        },
        "Test 1: PING (heartbeat)"
    )

    time.sleep(0.5)

    # Test 3: BuyMarket
    send_webhook(
        {
            "Symbol": "BTCUSDT",
            "Exchange": "BINANCE",
            "Interval": "15m",
            "Action": "BuyMarket",
            "Prix": 43500.0,
            "PourCent": 50,
            "UserID": 1,
            "UserExchangeID": 13
        },
        "Test 2: BuyMarket 50%"
    )

    time.sleep(0.5)

    # Test 4: MAJ (mise a jour SL/TP)
    send_webhook(
        {
            "Symbol": "BTCUSDT",
            "Exchange": "BINANCE",
            "Interval": "15m",
            "Action": "MAJ",
            "Prix": 44000.0,
            "PrixSL": 42000.0,
            "PrixTP": 46000.0,
            "PourCent": 100,
            "UserID": 1,
            "UserExchangeID": 13
        },
        "Test 3: MAJ (update SL/TP)"
    )

    time.sleep(0.5)

    # Test 5: SellMarket
    send_webhook(
        {
            "Symbol": "BTCUSDT",
            "Exchange": "BINANCE",
            "Interval": "15m",
            "Action": "SellMarket",
            "Prix": 44200.0,
            "PourCent": 100,
            "UserID": 1,
            "UserExchangeID": 13
        },
        "Test 4: SellMarket 100%"
    )

    time.sleep(0.5)

    # Test 6: Token invalide (doit echouer)
    print(f"\n{Colors.BLUE}[TEST]{Colors.RESET} Test 5: Token invalide (doit echouer)")
    headers_invalid = {
        'Content-Type': 'application/json',
        'X-Webhook-Token': 'INVALID_TOKEN'
    }
    try:
        response = requests.post(
            WEBHOOK_URL,
            json={"Symbol": "BTCUSDT", "Action": "PING"},
            headers=headers_invalid
        )
        if response.status_code == 401:
            print(f"  {Colors.GREEN}✅ Token invalide correctement rejete{Colors.RESET}")
        else:
            print(f"  {Colors.RED}❌ Attendu 401, recu {response.status_code}{Colors.RESET}")
    except Exception as e:
        print(f"  {Colors.RED}❌ EXCEPTION{Colors.RESET}: {e}")

    # Test final: Health check
    test_health()

    print(f"\n{Colors.GREEN}╔════════════════════════════════════════════════╗")
    print(f"║              TESTS TERMINES                    ║")
    print(f"╚════════════════════════════════════════════════╝{Colors.RESET}\n")
    print(f"Prochaines etapes:")
    print(f"  1. Verifier logs Terminal 6 pour voir les webhooks recus")
    print(f"  2. Verifier Redis avec: redis-cli SUBSCRIBE webhook_raw")
    print(f"  3. Une fois Terminal 3 pret, les webhooks seront traites\n")

if __name__ == '__main__':
    main()
