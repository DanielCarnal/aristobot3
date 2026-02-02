#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURATION BROKER TESTNET POUR TESTS MODULE 4

Configure un broker avec des API keys testnet pour tests sans risque
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.brokers.models import Broker
from apps.accounts.models import User

def configure_testnet_broker():
    """
    Configure ou crée un broker testnet pour tests
    """
    print("\n" + "="*70)
    print("CONFIGURATION BROKER TESTNET - MODULE 4")
    print("="*70 + "\n")

    print("🎯 Objectif : Créer/configurer un broker testnet pour tests sécurisés\n")

    # 1. Sélectionner user
    print("[1] Sélection utilisateur\n")
    users = User.objects.all()

    for u in users:
        print(f"  {u.id}. {u.username}")

    user_choice = input(f"\nUtilisateur (ID) [1 = dev]: ")
    user_id = int(user_choice) if user_choice else 1

    try:
        user = User.objects.get(id=user_id)
        print(f"  ✅ User sélectionné : {user.username}\n")
    except User.DoesNotExist:
        print(f"  ❌ User {user_id} introuvable\n")
        return

    # 2. Chercher broker testnet existant
    print("[2] Recherche broker testnet existant\n")

    testnet_broker = Broker.objects.filter(
        user=user,
        is_testnet=True,
        is_active=True
    ).first()

    if testnet_broker:
        print(f"  ✅ Broker testnet trouvé :")
        print(f"     ID: {testnet_broker.id}")
        print(f"     Nom: {testnet_broker.name}")
        print(f"     Exchange: {testnet_broker.exchange}")

        response = input(f"\n  Utiliser ce broker ? (oui/non): ")

        if response.lower() == 'oui':
            broker = testnet_broker
        else:
            print("\n  Création d'un nouveau broker testnet...\n")
            broker = None
    else:
        print("  ℹ️  Aucun broker testnet trouvé\n")
        broker = None

    # 3. Créer nouveau broker si nécessaire
    if not broker:
        print("[3] Création nouveau broker testnet\n")

        print("  Exchanges disponibles avec testnet :")
        print("    1. bitget (recommandé)")
        print("    2. binance")

        exchange_choice = input("\n  Exchange (1-2) [1 = bitget]: ")
        exchange_map = {'1': 'bitget', '2': 'binance', '': 'bitget'}
        exchange = exchange_map.get(exchange_choice, 'bitget')

        name = input(f"  Nom du broker [Testnet-{exchange}]: ")
        if not name:
            name = f"Testnet-{exchange}"

        print(f"\n  ⚠️  IMPORTANT : Utiliser des API keys TESTNET !")
        print(f"     Bitget testnet : https://testnet.bitget.com")
        print(f"     Binance testnet : https://testnet.binance.vision")
        print()

        api_key = input(f"  API Key (testnet): ")
        api_secret = input(f"  API Secret (testnet): ")

        if not api_key or not api_secret:
            print(f"\n  ❌ API keys requises\n")
            return

        # Créer broker
        broker = Broker.objects.create(
            user=user,
            exchange=exchange,
            name=name,
            api_key=api_key,  # Sera chiffré automatiquement
            api_secret=api_secret,  # Sera chiffré automatiquement
            is_testnet=True,
            is_active=True,
            type_de_trading='Webhooks'
        )

        print(f"\n  ✅ Broker testnet créé :")
        print(f"     ID: {broker.id}")
        print(f"     Nom: {broker.name}")

    # 4. Configurer pour webhooks
    print(f"\n[4] Configuration pour webhooks\n")

    broker.type_de_trading = 'Webhooks'
    broker.is_active = True
    broker.save()

    print(f"  ✅ Configuration appliquée :")
    print(f"     type_de_trading: Webhooks")
    print(f"     is_testnet: True")
    print(f"     is_active: True")

    # 5. Résumé final
    print("\n" + "="*70)
    print("CONFIGURATION TERMINÉE")
    print("="*70 + "\n")

    print(f"📊 Informations pour webhooks :\n")
    print(f"  UserID: {broker.user.id}")
    print(f"  UserExchangeID: {broker.id}")
    print(f"  Exchange: {broker.exchange}")
    print(f"  Testnet: {broker.is_testnet}")

    print(f"\n🚀 Prochaines étapes :\n")
    print(f"  1. Démarrer Terminal 5 : python manage.py run_native_exchange_service")
    print(f"  2. Démarrer Terminal 6 : python manage.py run_webhook_receiver")
    print(f"  3. Démarrer Terminal 3 SANS --test : python manage.py run_trading_engine")
    print(f"  4. Lancer tests : python test_webhook_limit_orders.py")

    print(f"\n💰 Fonds testnet :")
    print(f"  Bitget : Déposer sur https://testnet.bitget.com")
    print(f"  Binance : Déposer sur https://testnet.binance.vision")

    print()

def reset_testnet_broker():
    """Remet le broker testnet en mode OFF"""
    testnet_brokers = Broker.objects.filter(is_testnet=True, type_de_trading='Webhooks')

    if not testnet_brokers.exists():
        print("\n✅ Aucun broker testnet configuré pour webhooks\n")
        return

    for broker in testnet_brokers:
        broker.type_de_trading = 'OFF'
        broker.save()
        print(f"✅ Broker {broker.name} remis en mode OFF")

    print()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_testnet_broker()
    else:
        configure_testnet_broker()
