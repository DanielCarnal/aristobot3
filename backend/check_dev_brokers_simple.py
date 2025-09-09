# -*- coding: utf-8 -*-
"""
Verification simple des brokers utilisateur dev (sans Unicode)
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

def check_dev_brokers_simple():
    """Verifie les brokers de l'utilisateur dev - Version ASCII"""
    print("=== DIAGNOSTIC BROKERS DEV ===")
    
    try:
        dev_user = User.objects.get(username='dev')
        print(f"[USER] dev trouve (ID: {dev_user.id})")
    except User.DoesNotExist:
        print("[ERROR] Utilisateur 'dev' non trouve")
        return
    
    # Lister tous les brokers de dev
    brokers = Broker.objects.filter(user=dev_user).order_by('id')
    print(f"\n[BROKERS] {len(brokers)} brokers pour dev:")
    
    for broker in brokers:
        print(f"  ID {broker.id}: {broker.name} ({broker.exchange})")
        print(f"    Active: {broker.is_active} | Default: {broker.is_default}")
        
        # Compter les symboles pour ce broker
        symbols_usdt = ExchangeSymbol.objects.filter(
            exchange__iexact=broker.exchange, 
            active=True,
            quote__iexact='USDT'
        ).count()
        
        symbols_total = ExchangeSymbol.objects.filter(
            exchange__iexact=broker.exchange,
            active=True  
        ).count()
        
        print(f"    Symboles USDT: {symbols_usdt}")
        print(f"    Symboles total: {symbols_total}")
        print()
    
    # Focus sur broker ID 13 que le frontend utilise
    print("[FOCUS] Frontend utilise broker ID 13:")
    try:
        broker_13 = Broker.objects.get(id=13, user=dev_user)
        print(f"  Broker 13 trouve: {broker_13.name} ({broker_13.exchange})")
        print(f"  Active: {broker_13.is_active}")
        
        # Verifier les symboles pour ce broker specifique
        symbols_13_usdt = ExchangeSymbol.objects.filter(
            exchange__iexact=broker_13.exchange,
            active=True,
            quote__iexact='USDT'
        ).count()
        
        symbols_13_total = ExchangeSymbol.objects.filter(
            exchange__iexact=broker_13.exchange,
            active=True
        ).count()
        
        print(f"  Symboles USDT disponibles: {symbols_13_usdt}")
        print(f"  Symboles total disponibles: {symbols_13_total}")
        
        if symbols_13_usdt == 0:
            print("  [PROBLEME] Aucun symbole USDT trouve pour ce broker!")
        else:
            print("  [OK] Symboles USDT disponibles")
            
    except Broker.DoesNotExist:
        print("  [ERROR] Broker ID 13 non trouve pour dev")

if __name__ == '__main__':
    check_dev_brokers_simple()