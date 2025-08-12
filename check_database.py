#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier la sauvegarde des données Heartbeat en base
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
sys.path.append('backend')
django.setup()

from apps.core.models import CandleHeartbeat, HeartbeatStatus

def check_database():
    print("=== VERIFICATION BASE DE DONNEES HEARTBEAT ===\n")
    
    # Vérifier le status
    try:
        status = HeartbeatStatus.objects.first()
        if status:
            print(f"Status Heartbeat:")
            print(f"  - ID: {status.id}")
            print(f"  - Connecté: {status.is_connected}")
            print(f"  - Dernière connexion: {status.last_application_start}")
            print(f"  - Dernière erreur: {status.last_error}")
        else:
            print("ATTENTION: Aucun status Heartbeat trouvé")
    except Exception as e:
        print(f"ERREUR status: {e}")
    
    print()
    
    # Vérifier les signaux
    try:
        total_signals = CandleHeartbeat.objects.count()
        print(f"Nombre total de signaux CandleHeartbeat: {total_signals}")
        
        if total_signals > 0:
            print("\nDerniers 10 signaux:")
            signals = CandleHeartbeat.objects.order_by('-dhm_reception')[:10]
            
            for i, signal in enumerate(signals, 1):
                print(f"  {i:2d}. {signal.dhm_reception.strftime('%d.%m.%y %H:%M:%S')} | "
                      f"{signal.signal_type:>3s} | {signal.symbol:>8s} | "
                      f"Prix: {signal.close_price:>10.2f}")
            
            # Statistiques par timeframe
            print("\nRépartition par timeframe:")
            timeframes = ['1m', '3m', '5m', '15m', '1h', '4h']
            for tf in timeframes:
                count = CandleHeartbeat.objects.filter(signal_type=tf).count()
                print(f"  {tf:>3s}: {count:>5d} signaux")
                
            # Dernière activité par timeframe
            print("\nDernière activité par timeframe:")
            for tf in timeframes:
                latest = CandleHeartbeat.objects.filter(signal_type=tf).order_by('-dhm_reception').first()
                if latest:
                    print(f"  {tf:>3s}: {latest.dhm_reception.strftime('%d.%m.%y %H:%M:%S')}")
                else:
                    print(f"  {tf:>3s}: Aucun signal")
        else:
            print("ATTENTION: Aucun signal trouvé en base")
            print("Le service run_heartbeat fonctionne-t-il ?")
            
    except Exception as e:
        print(f"ERREUR signaux: {e}")

if __name__ == '__main__':
    check_database()