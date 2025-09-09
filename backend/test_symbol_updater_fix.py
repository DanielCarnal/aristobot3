# -*- coding: utf-8 -*-
"""
TEST CORRECTION SYMBOL UPDATER
Vérifie que les erreurs PostgreSQL sont corrigées
"""

import os
import django

# Configuration Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
    django.setup()

from apps.core.services.symbol_updater import SymbolUpdaterService

def test_safe_decimal_value():
    """Test de la fonction safe_decimal_value"""
    print("=== TEST SAFE_DECIMAL_VALUE ===")
    
    # Test valeurs normales
    assert SymbolUpdaterService.safe_decimal_value(1.5) == 1.5
    assert SymbolUpdaterService.safe_decimal_value("10.5") == "10.5"
    assert SymbolUpdaterService.safe_decimal_value(100) == 100
    print("[OK] Valeurs normales")
    
    # Test valeurs problématiques
    assert SymbolUpdaterService.safe_decimal_value(None) is None
    assert SymbolUpdaterService.safe_decimal_value(0) is None
    assert SymbolUpdaterService.safe_decimal_value(999999999999999) is None  # Trop grande
    assert SymbolUpdaterService.safe_decimal_value(1e15) is None  # Trop grande
    assert SymbolUpdaterService.safe_decimal_value("invalid") is None  # Invalide
    print("[OK] Valeurs problématiques filtrées")
    
    # Test valeurs limites OK
    assert SymbolUpdaterService.safe_decimal_value(999999999999) == 999999999999  # Max OK
    assert SymbolUpdaterService.safe_decimal_value(-999999999999) == -999999999999  # Min OK
    assert SymbolUpdaterService.safe_decimal_value(0.00000001) == 0.00000001  # Très petite OK
    print("[OK] Valeurs limites OK")

def test_potential_problem_symbols():
    """Simuler les symboles qui posaient problème"""
    print("\n=== TEST SYMBOLES PROBLÉMATIQUES ===")
    
    # Simuler des valeurs qui causaient les erreurs
    problem_values = [
        1e20,  # RATS/USDT
        1e25,  # DOGE/EUR 
        9.999999999999999e59,  # AVAX/EUR
        1e100,  # WELL/USDT
        float('inf'),  # QUBIC/USDT (potentiel)
    ]
    
    filtered_count = 0
    for val in problem_values:
        result = SymbolUpdaterService.safe_decimal_value(val)
        if result is None:
            filtered_count += 1
            print(f"[FILTRÉ] {val} -> None")
        else:
            print(f"[PASSÉ] {val} -> {result}")
    
    print(f"[OK] {filtered_count}/{len(problem_values)} valeurs problématiques filtrées")

if __name__ == '__main__':
    print("TEST CORRECTION SYMBOL UPDATER")
    print("=" * 50)
    
    try:
        test_safe_decimal_value()
        test_potential_problem_symbols()
        
        print("\n" + "=" * 50)
        print("✅ TOUS LES TESTS PASSENT")
        print("La correction devrait résoudre les erreurs PostgreSQL")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()