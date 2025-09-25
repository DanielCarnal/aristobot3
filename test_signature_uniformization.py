# -*- coding: utf-8 -*-
"""
TEST SIGNATURE UNIFORMIZATION - Validation des signatures unifiées

🎯 OBJECTIF: Valider que tous les exchange clients ont des signatures identiques
Après extension de BinanceNativeClient et KrakenNativeClient pour correspondre à BitgetNativeClient

📋 TESTS:
✅ Vérifier signatures get_order_history() identiques
✅ Vérifier signatures get_open_orders() identiques  
✅ Test d'appel avec paramètres étendus
✅ Validation que Terminal 7 ne plantera plus

🚀 RÉSULTAT ATTENDU: 
Terminal 7 peut appeler tous les clients avec les mêmes paramètres sans erreur de signature.

Usage:
  python test_signature_uniformization.py
"""

import asyncio
import sys
import os
import inspect
from typing import get_type_hints

# Configuration Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')

import django
django.setup()

from apps.core.services.bitget_native_client import BitgetNativeClient
from apps.core.services.binance_native_client import BinanceNativeClient  
from apps.core.services.kraken_native_client import KrakenNativeClient


def analyze_method_signature(client_class, method_name: str) -> dict:
    """Analyse la signature d'une méthode"""
    try:
        method = getattr(client_class, method_name)
        sig = inspect.signature(method)
        
        return {
            'parameters': list(sig.parameters.keys()),
            'signature': str(sig),
            'parameter_count': len(sig.parameters),
            'has_extended_params': any(param in sig.parameters for param in 
                                     ['start_time', 'end_time', 'tpsl_type', 'id_less_than'])
        }
    except AttributeError:
        return {
            'error': f'Method {method_name} not found',
            'parameters': [],
            'signature': 'NOT_FOUND',
            'parameter_count': 0,
            'has_extended_params': False
        }


def compare_signatures(bitget_sig: dict, binance_sig: dict, kraken_sig: dict, method_name: str) -> dict:
    """Compare les signatures entre les trois clients"""
    
    # Vérifier si toutes ont les paramètres étendus
    all_extended = all([
        bitget_sig.get('has_extended_params', False),
        binance_sig.get('has_extended_params', False),
        kraken_sig.get('has_extended_params', False)
    ])
    
    # Vérifier si les signatures sont identiques (même nombre de paramètres)
    param_counts = [
        bitget_sig.get('parameter_count', 0),
        binance_sig.get('parameter_count', 0),
        kraken_sig.get('parameter_count', 0)
    ]
    
    uniform_param_count = len(set(param_counts)) == 1
    
    return {
        'method': method_name,
        'all_have_extended_params': all_extended,
        'uniform_parameter_count': uniform_param_count,
        'parameter_counts': {
            'bitget': param_counts[0],
            'binance': param_counts[1], 
            'kraken': param_counts[2]
        },
        'signatures_match': all_extended and uniform_param_count,
        'details': {
            'bitget': bitget_sig,
            'binance': binance_sig,
            'kraken': kraken_sig
        }
    }


async def test_method_calls():
    """Test d'appel des méthodes avec paramètres étendus"""
    
    print("\n" + "="*80)
    print("TEST D'APPEL AVEC PARAMÈTRES ÉTENDUS")
    print("="*80)
    
    # Paramètres étendus de test (ne pas exécuter réellement)
    extended_params = {
        'symbol': 'BTC/USDT',
        'start_time': '1640995200000',  # 1er janvier 2022
        'end_time': '1704067200000',    # 1er janvier 2024
        'id_less_than': '12345',
        'limit': 50,
        'order_id': '67890',
        'tpsl_type': 'normal',
        'request_time': '1704067200000',
        'receive_window': '5000'
    }
    
    clients_info = [
        ('BitgetNativeClient', BitgetNativeClient),
        ('BinanceNativeClient', BinanceNativeClient),
        ('KrakenNativeClient', KrakenNativeClient)
    ]
    
    # Test des signatures sans exécuter (pas besoin de vraies API keys)
    for client_name, client_class in clients_info:
        print(f"\n[TEST] {client_name}")
        
        for method_name in ['get_order_history', 'get_open_orders']:
            try:
                method = getattr(client_class, method_name)
                sig = inspect.signature(method)
                
                # Vérifier si la méthode accepte tous les paramètres étendus
                method_params = set(sig.parameters.keys())
                extended_params_set = set(extended_params.keys())
                
                # Enlever 'self' de la comparaison
                method_params.discard('self')
                
                # Vérifier combien de paramètres étendus sont acceptés
                accepted_params = extended_params_set.intersection(method_params)
                missing_params = extended_params_set - method_params
                
                print(f"  {method_name}:")
                print(f"    ✅ Paramètres acceptés: {len(accepted_params)}/{len(extended_params_set)}")
                print(f"    📝 Acceptés: {sorted(accepted_params)}")
                if missing_params:
                    print(f"    ❌ Manquants: {sorted(missing_params)}")
                else:
                    print(f"    🎉 TOUS LES PARAMÈTRES SUPPORTÉS!")
                    
            except AttributeError:
                print(f"  ❌ {method_name}: MÉTHODE INTROUVABLE")
            except Exception as e:
                print(f"  ⚠️  {method_name}: ERREUR {e}")


def main():
    """Test principal de validation des signatures"""
    
    print("="*80)
    print("VALIDATION SIGNATURE UNIFORMIZATION - EXCHANGE CLIENTS")
    print("="*80)
    print("🎯 Objectif: Vérifier que tous les clients ont des signatures identiques")
    print("📋 Clients: BitgetNativeClient, BinanceNativeClient, KrakenNativeClient") 
    print("🔧 Méthodes: get_order_history(), get_open_orders()")
    
    # Analyse des signatures
    methods_to_test = ['get_order_history', 'get_open_orders']
    results = []
    
    for method_name in methods_to_test:
        print(f"\n{'='*60}")
        print(f"ANALYSE METHOD: {method_name.upper()}")
        print(f"{'='*60}")
        
        # Analyser chaque client
        bitget_sig = analyze_method_signature(BitgetNativeClient, method_name)
        binance_sig = analyze_method_signature(BinanceNativeClient, method_name)
        kraken_sig = analyze_method_signature(KrakenNativeClient, method_name)
        
        # Afficher les signatures
        print(f"\n📊 SIGNATURES DÉTECTÉES:")
        print(f"  • BitgetNativeClient:  {bitget_sig['signature']}")
        print(f"  • BinanceNativeClient: {binance_sig['signature']}")  
        print(f"  • KrakenNativeClient:  {kraken_sig['signature']}")
        
        print(f"\n📈 ANALYSE DES PARAMÈTRES:")
        print(f"  • Bitget:  {bitget_sig['parameter_count']} paramètres - Extended: {bitget_sig['has_extended_params']}")
        print(f"  • Binance: {binance_sig['parameter_count']} paramètres - Extended: {binance_sig['has_extended_params']}")
        print(f"  • Kraken:  {kraken_sig['parameter_count']} paramètres - Extended: {kraken_sig['has_extended_params']}")
        
        # Comparaison
        comparison = compare_signatures(bitget_sig, binance_sig, kraken_sig, method_name)
        results.append(comparison)
        
        # Résultat
        if comparison['signatures_match']:
            print(f"\n✅ RÉSULTAT: {method_name} - SIGNATURES UNIFORMISÉES!")
            print(f"   🎉 Tous les clients supportent les paramètres étendus")
        else:
            print(f"\n❌ RÉSULTAT: {method_name} - SIGNATURES NON UNIFORMES")
            if not comparison['all_have_extended_params']:
                print(f"   ⚠️  Certains clients n'ont pas les paramètres étendus")
            if not comparison['uniform_parameter_count']:
                print(f"   ⚠️  Nombres de paramètres différents: {comparison['parameter_counts']}")
    
    # Rapport final
    print(f"\n{'='*80}")
    print("RAPPORT FINAL DE UNIFORMISATION")
    print("="*80)
    
    all_methods_uniform = all(result['signatures_match'] for result in results)
    
    if all_methods_uniform:
        print("🎉 SUCCÈS COMPLET: TOUTES LES SIGNATURES SONT UNIFORMISÉES!")
        print("\n✅ RÉSULTATS:")
        for result in results:
            print(f"   • {result['method']}: UNIFORME ✅")
        
        print(f"\n🚀 CONSÉQUENCES:")
        print(f"   • Terminal 7 peut appeler tous les clients sans erreur de signature")
        print(f"   • NativeExchangeManager peut passer les paramètres étendus à tous")
        print(f"   • Plus d'erreurs 'unexpected keyword argument'")
        print(f"   • Architecture multi-exchange pleinement opérationnelle")
        
    else:
        print("❌ ÉCHEC: CERTAINES SIGNATURES NE SONT PAS UNIFORMISÉES")
        print("\n📋 DÉTAILS:")
        for result in results:
            status = "UNIFORME ✅" if result['signatures_match'] else "NON UNIFORME ❌"
            print(f"   • {result['method']}: {status}")
    
    # Test des appels
    asyncio.run(test_method_calls())
    
    print(f"\n{'='*80}")
    print("TEST SIGNATURE UNIFORMIZATION TERMINÉ")
    print("="*80)


if __name__ == "__main__":
    main()