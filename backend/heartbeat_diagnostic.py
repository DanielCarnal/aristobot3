#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnostic Heartbeat MODULE2
Vérifiie l'état du service et donne des instructions
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from apps.core.models import HeartbeatStatus, CandleHeartbeat
from django.utils import timezone
from datetime import timedelta

def main():
    print("=== DIAGNOSTIC HEARTBEAT MODULE 2 ===\n")
    
    try:
        # Vérifier le statut
        status = HeartbeatStatus.objects.get(id=1)
        print(f"[OK] Status trouve (ID: {status.id})")
        print(f"  - Connecté: {'OUI' if status.is_connected else 'NON'}")
        print(f"  - Symboles surveillés: {status.symbols_monitored}")
        print(f"  - Dernier démarrage: {status.last_application_start or 'Jamais'}")
        print(f"  - Dernier arrêt: {status.last_application_stop or 'Jamais'}")
        print(f"  - Dernière erreur: {status.last_error or 'Aucune'}")
        
    except HeartbeatStatus.DoesNotExist:
        print("[WARNING] Aucun status trouve - Le service n'a jamais ete demarre")
        return
    
    # Vérifier les signaux
    total_signals = CandleHeartbeat.objects.count()
    print(f"\n[OK] Signaux en base: {total_signals}")
    
    if total_signals > 0:
        # Dernier signal
        last_signal = CandleHeartbeat.objects.first()
        print(f"  - Dernier signal: {last_signal.symbol} {last_signal.signal_type}")
        print(f"  - Reçu le: {last_signal.dhm_reception}")
        
        # Signaux récents (dernière heure)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_count = CandleHeartbeat.objects.filter(
            dhm_reception__gte=one_hour_ago
        ).count()
        print(f"  - Signaux dernière heure: {recent_count}")
    
    # Instructions
    print(f"\n=== INSTRUCTIONS ===")
    
    if not status.is_connected:
        print("[STOP] SERVICE ARRETE")
        print("\nPour démarrer le Heartbeat:")
        print("  1. Ouvrir un terminal dans backend/")
        print("  2. Exécuter: python manage.py run_heartbeat")
        print("  3. Le service va se connecter à Binance WebSocket")
        print("  4. Vérifier que le frontend affiche 'Connecté'")
        
        print("\nPour tester les APIs:")
        print("  - Status: GET /api/heartbeat/status/")
        print("  - Signaux récents: GET /api/heartbeat/recent/")
        print("  - Par timeframe: GET /api/heartbeat/timeframes/")
    else:
        print("[RUNNING] SERVICE EN COURS")
        print("\nLe service Heartbeat fonctionne correctement!")
        print("Vérifiez l'interface frontend pour voir les signaux.")
    
    print(f"\n=== FICHIERS CLÉS ===")
    print("  - Service: apps/core/management/commands/run_heartbeat.py")
    print("  - APIs: apps/core/views.py (HeartbeatViewSet)")  
    print("  - Frontend: frontend/src/views/HeartbeatView.vue")
    print("  - Modèles: apps/core/models.py (CandleHeartbeat)")

if __name__ == '__main__':
    main()