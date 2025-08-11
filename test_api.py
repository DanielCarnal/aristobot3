#!/usr/bin/env python3
"""
Script de test pour valider l'API Aristobot3 Module 1
"""
import requests
import json
import sys

BASE_URL = 'http://127.0.0.1:8000'
session = requests.Session()

def test_login():
    """Test du login automatique en mode DEBUG"""
    print("Test de connexion automatique (mode DEBUG)")
    response = session.post(f'{BASE_URL}/api/auth/login/', json={})
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK Connexion réussie: {data['user']['username']} (is_dev: {data['user']['is_dev']})")
        return True
    else:
        print(f"ERREUR Échec de la connexion: {response.status_code} - {response.text}")
        return False

def test_current_user():
    """Test de récupération de l'utilisateur courant"""
    print("\nTest utilisateur courant")
    response = session.get(f'{BASE_URL}/api/auth/current/')
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK Utilisateur: {data['username']} (ID: {data['id']})")
        return data
    else:
        print(f"ERREUR Échec: {response.status_code} - {response.text}")
        return None

def test_brokers_crud():
    """Test du CRUD des brokers"""
    print("\nTest CRUD Brokers")
    
    # 1. Liste des brokers (doit être vide initialement)
    response = session.get(f'{BASE_URL}/api/brokers/')
    if response.status_code == 200:
        brokers = response.json()
        count = len(brokers.get('results', brokers))
        print(f"OK Liste brokers: {count} broker(s)")
    else:
        print(f"ERREUR Échec liste brokers: {response.status_code}")
        return False
    
    # 2. Créer un broker de test (sans vraies clés API)
    test_broker = {
        "exchange": "binance",
        "name": "Test Binance",
        "description": "Broker de test",
        "api_key": "test_key_123",
        "api_secret": "test_secret_456",
        "is_testnet": True
    }
    
    response = session.post(f'{BASE_URL}/api/brokers/', json=test_broker)
    if response.status_code == 201:
        broker_data = response.json()
        broker_id = broker_data['id']
        print(f"OK Broker créé: ID {broker_id}")
        
        # 3. Récupérer le broker créé
        response = session.get(f'{BASE_URL}/api/brokers/{broker_id}/')
        if response.status_code == 200:
            broker = response.json()
            print(f"OK Broker récupéré: {broker['name']}")
            
            # 4. Modifier le broker
            update_data = {"description": "Description mise à jour"}
            response = session.patch(f'{BASE_URL}/api/brokers/{broker_id}/', json=update_data)
            if response.status_code == 200:
                print("OK Broker mis à jour")
            else:
                print(f"ERREUR Échec mise à jour: {response.status_code}")
            
            # 5. Supprimer le broker
            response = session.delete(f'{BASE_URL}/api/brokers/{broker_id}/')
            if response.status_code == 204:
                print("OK Broker supprimé")
                return True
            else:
                print(f"ERREUR Échec suppression: {response.status_code}")
                return False
        else:
            print(f"ERREUR Échec récupération broker: {response.status_code}")
            return False
    else:
        print(f"ERREUR Échec création broker: {response.status_code} - {response.text}")
        return False

def test_symbols():
    """Test de l'API des symboles"""
    print("\nTest API Symboles")
    response = session.get(f'{BASE_URL}/api/symbols/')
    
    if response.status_code == 200:
        symbols = response.json()
        count = len(symbols.get('results', symbols))
        print(f"OK Symboles disponibles: {count}")
        return True
    else:
        print(f"ERREUR Échec récupération symboles: {response.status_code}")
        return False

def main():
    print("Tests de validation Module 1 - Aristobot3")
    print("=" * 50)
    
    # Test de connexion
    if not test_login():
        sys.exit(1)
    
    # Test utilisateur courant
    user = test_current_user()
    if not user:
        sys.exit(1)
    
    # Test CRUD Brokers
    if not test_brokers_crud():
        sys.exit(1)
    
    # Test symboles
    test_symbols()
    
    print("\n" + "=" * 50)
    print("OK Tous les tests API sont passés !")

if __name__ == "__main__":
    main()