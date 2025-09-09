# -*- coding: utf-8 -*-
"""
Vérification simple des symboles en base
"""

import os
import django

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

from apps.brokers.models import ExchangeSymbol

def check_symbols_simple():
    """Vérification simple des symboles"""
    print("=== VÉRIFICATION SIMPLE SYMBOLES ===")
    
    # Vérifier Bitget spécifiquement
    bitget_total = ExchangeSymbol.objects.filter(exchange__iexact='bitget').count()
    bitget_active = ExchangeSymbol.objects.filter(exchange__iexact='bitget', active=True).count()
    bitget_usdt = ExchangeSymbol.objects.filter(
        exchange__iexact='bitget',
        active=True,
        quote__iexact='USDT'
    ).count()
    
    print(f"BITGET:")
    print(f"  Total: {bitget_total}")
    print(f"  Actifs: {bitget_active}")
    print(f"  USDT actifs: {bitget_usdt}")
    
    if bitget_usdt > 0:
        # Échantillon USDT
        usdt_examples = ExchangeSymbol.objects.filter(
            exchange__iexact='bitget',
            active=True,
            quote__iexact='USDT'
        ).values_list('symbol', flat=True)[:10]
        print(f"  Exemples USDT: {list(usdt_examples)}")
    
    # Compter tous les exchanges
    all_exchanges = ExchangeSymbol.objects.values('exchange').distinct()
    print(f"\nTous les exchanges: {[ex['exchange'] for ex in all_exchanges]}")

if __name__ == '__main__':
    check_symbols_simple()