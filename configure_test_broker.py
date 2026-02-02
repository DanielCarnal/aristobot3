#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURATION BROKER POUR TESTS MODULE 4

Configure temporairement un broker pour tests webhooks
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.brokers.models import Broker

def configure_test_broker():
    """Configure broker ID 13 (Bitget dev) pour tests"""

    print("\n" + "="*60)
    print("CONFIGURATION BROKER POUR TESTS MODULE 4")
    print("="*60 + "\n")

    try:
        # Utiliser broker ID 13 (Bitget - user dev)
        broker = Broker.objects.get(id=13)

        print(f"Broker sélectionné :")
        print(f"  ID: {broker.id}")
        print(f"  Nom: {broker.name}")
        print(f"  Exchange: {broker.exchange}")
        print(f"  User: {broker.user.username}")
        print(f"\nConfiguration AVANT :")
        print(f"  type_de_trading: {broker.type_de_trading}")
        print(f"  is_testnet: {broker.is_testnet}")
        print(f"  is_active: {broker.is_active}")

        # Configuration pour tests
        broker.type_de_trading = 'Webhooks'
        broker.is_active = True
        broker.save()

        print(f"\nConfiguration APRÈS :")
        print(f"  type_de_trading: {broker.type_de_trading} ← ACTIVÉ")
        print(f"  is_testnet: {broker.is_testnet}")
        print(f"  is_active: {broker.is_active}")

        print(f"\n✅ Broker configuré pour tests webhooks")
        print(f"\n⚠️  IMPORTANT :")
        print(f"   - Lance Terminal 3 avec --test pour éviter ordres réels")
        print(f"   - Commande : python manage.py run_trading_engine --test")
        print(f"\n📊 User à utiliser dans webhooks :")
        print(f"   - UserID: {broker.user.id}")
        print(f"   - UserExchangeID: {broker.id}")

    except Broker.DoesNotExist:
        print("❌ Broker ID 13 introuvable")
        print("\nBrokers disponibles :")
        for b in Broker.objects.all():
            print(f"  ID {b.id}: {b.name} ({b.exchange}) - User: {b.user.username}")

def reset_broker():
    """Remet le broker en mode OFF après tests"""

    try:
        broker = Broker.objects.get(id=13)
        broker.type_de_trading = 'OFF'
        broker.save()

        print("\n✅ Broker remis en mode OFF (sécurisé)")

    except Broker.DoesNotExist:
        print("❌ Broker ID 13 introuvable")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_broker()
    else:
        configure_test_broker()
        print("\n💡 Pour remettre en mode OFF après tests :")
        print("   python configure_test_broker.py reset\n")
