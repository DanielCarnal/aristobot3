# -*- coding: utf-8 -*-
"""
Vérifier les brokers de l'utilisateur dev
"""

import os
import django

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

from django.contrib.auth import get_user_model
from apps.brokers.models import Broker, ExchangeSymbol

User = get_user_model()

def check_dev_user_brokers():
    """Vérifie les brokers de l'utilisateur dev"""
    print("=== BROKERS UTILISATEUR DEV ===")
    
    try:
        dev_user = User.objects.get(username='dev')
        print(f"[USER] dev trouvé (ID: {dev_user.id})")
    except User.DoesNotExist:
        print("[ERROR] Utilisateur 'dev' non trouvé")
        return
    
    # Lister tous les brokers de dev
    brokers = Broker.objects.filter(user=dev_user).order_by('id')
    print(f"\n[BROKERS] {len(brokers)} brokers pour l'utilisateur dev:")
    
    for broker in brokers:
        print(f"  ID {broker.id}: {broker.name} ({broker.exchange}) - Active: {broker.is_active} - Default: {broker.is_default}")
        
        # Vérifier les symboles pour ce broker
        symbols_count = ExchangeSymbol.objects.filter(
            exchange__iexact=broker.exchange, 
            active=True,
            quote__iexact='USDT'
        ).count()
        print(f"          → {symbols_count} symboles USDT disponibles en DB")
    
    print(f"\n[FOCUS] Frontend utilise broker ID 13:")
    try:
        broker_13 = Broker.objects.get(id=13, user=dev_user)
        print(f"  Broker 13: {broker_13.name} ({broker_13.exchange}) - Active: {broker_13.is_active}")
        
        # Tester les symboles pour broker 13
        symbols_13 = ExchangeSymbol.objects.filter(
            exchange__iexact=broker_13.exchange,
            active=True,
            quote__iexact='USDT'  
        ).count()
        print(f"  Symboles USDT pour {broker_13.exchange}: {symbols_13}")
        
    except Broker.DoesNotExist:
        print("  [ERROR] Broker ID 13 non trouvé pour l'utilisateur dev")

if __name__ == '__main__':
    check_dev_user_brokers()