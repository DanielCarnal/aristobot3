# -*- coding: utf-8 -*-
"""
Vérification des symboles en base de données
"""

import os
import django

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

from apps.brokers.models import ExchangeSymbol

def check_symbols_in_db():
    """Vérifie la présence des symboles en base"""
    print("=== VÉRIFICATION SYMBOLES EN BASE ===")
    
    # Compter par exchange
    exchanges = ExchangeSymbol.objects.values('exchange').distinct()
    print(f"Exchanges en base: {[ex['exchange'] for ex in exchanges]}")
    
    for exchange in exchanges:
        exchange_name = exchange['exchange']
        
        total_count = ExchangeSymbol.objects.filter(exchange=exchange_name).count()
        active_count = ExchangeSymbol.objects.filter(exchange=exchange_name, active=True).count()
        spot_count = ExchangeSymbol.objects.filter(exchange=exchange_name, active=True, type='spot').count()
        usdt_count = ExchangeSymbol.objects.filter(
            exchange=exchange_name, 
            active=True, 
            type='spot',
            quote__iexact='USDT'
        ).count()
        
        print(f"\n{exchange_name.upper()}:")
        print(f"  Total symboles: {total_count}")
        print(f"  Actifs: {active_count}")
        print(f"  Spot actifs: {spot_count}")
        print(f"  USDT/Spot actifs: {usdt_count}")
        
        # Afficher quelques exemples
        if usdt_count > 0:
            examples = ExchangeSymbol.objects.filter(
                exchange=exchange_name,
                active=True,
                type='spot',
                quote__iexact='USDT'
            ).values_list('symbol', flat=True)[:10]
            print(f"  Exemples USDT: {list(examples)}")

if __name__ == '__main__':
    check_symbols_in_db()