#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic specifique pour le probleme de login DEBUG_ARISTOBOT
"""

import os
import sys
import django
import requests

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
sys.path.append('backend')
django.setup()

from django.conf import settings
from apps.auth_custom.models import DebugMode

def test_debug_backend():
    print("=== TEST CONFIGURATION BACKEND ===")
    
    # Variable d'environnement
    debug_aristobot = getattr(settings, 'DEBUG_ARISTOBOT', None)
    print(f"DEBUG_ARISTOBOT dans settings: {debug_aristobot}")
    
    # État en base
    debug_state = DebugMode.get_state()
    print(f"DebugMode.get_state(): {debug_state}")
    
    # Objet en base
    try:
        debug_obj = DebugMode.objects.get(id=1)
        print(f"DebugMode object: {debug_obj}")
        print(f"  - is_active: {debug_obj.is_active}")
        print(f"  - updated_at: {debug_obj.updated_at}")
    except DebugMode.DoesNotExist:
        print("ERREUR: Pas d'objet DebugMode en base")
        DebugMode.objects.create(id=1, is_active=True)
        print("CORRECTION: Objet DebugMode cree")

def test_debug_apis():
    print("\n=== TEST APIS DEBUG ===")
    
    base_url = "http://localhost:8000"
    
    # Test debug-config
    try:
        response = requests.get(f"{base_url}/api/auth/debug-config/", timeout=5)
        print(f"GET /api/auth/debug-config/ -> {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
        else:
            print(f"  Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"ERREUR /api/auth/debug-config/: {e}")
    
    # Test status
    try:
        response = requests.get(f"{base_url}/api/auth/status/", timeout=5)
        print(f"GET /api/auth/status/ -> {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Debug config: {data.get('debug', 'Non trouve')}")
    except requests.exceptions.RequestException as e:
        print(f"ERREUR /api/auth/status/: {e}")
    
    # Test toggle debug
    try:
        response = requests.post(f"{base_url}/api/auth/toggle-debug/", timeout=5)
        print(f"POST /api/auth/toggle-debug/ -> {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
    except requests.exceptions.RequestException as e:
        print(f"ERREUR /api/auth/toggle-debug/: {e}")

def test_frontend_api_call():
    print("\n=== SIMULATION APPEL FRONTEND ===")
    
    # Simulation de l'appel exact que fait le frontend
    try:
        session = requests.Session()
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        response = session.get(
            "http://localhost:8000/api/auth/debug-config/",
            headers=headers,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code == 200:
            print(f"Response Data: {response.json()}")
        else:
            print(f"Error Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"ERREUR simulation frontend: {e}")

def suggest_fixes():
    print("\n=== SUGGESTIONS DE CORRECTION ===")
    
    debug_enabled = getattr(settings, 'DEBUG_ARISTOBOT', False)
    debug_active = DebugMode.get_state()
    
    if not debug_enabled:
        print("1. Verifier que DEBUG_ARISTOBOT=True dans le .env")
        print("2. Redemarrer le serveur Django")
    
    if not debug_active:
        print("3. Activer le mode debug en base:")
        print("   python manage.py shell -c \"from apps.auth_custom.models import DebugMode; DebugMode.set_state(True)\"")
    
    print("4. Verifier que le serveur Django fonctionne:")
    print("   curl http://localhost:8000/api/auth/debug-config/")
    
    print("5. Vider le cache browser et recharger la page de login")
    
    print("6. Verifier les logs du serveur Django pour des erreurs")

def main():
    print("=== DIAGNOSTIC DEBUG LOGIN MODULE ===")
    
    test_debug_backend()
    test_debug_apis()
    test_frontend_api_call()
    suggest_fixes()
    
    print("\n=== FIN DIAGNOSTIC ===")

if __name__ == '__main__':
    main()