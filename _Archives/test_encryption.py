#!/usr/bin/env python3
"""
Script de test pour valider le chiffrement des API keys
"""
import os
import sys
import django

# Configuration Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristobot.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.brokers.models import Broker

User = get_user_model()

def test_broker_encryption():
    """Test du chiffrement/déchiffrement des clés API des brokers"""
    print("Test du chiffrement des clés API - Brokers")
    
    # Récupérer l'utilisateur dev
    try:
        user = User.objects.get(username='dev')
    except User.DoesNotExist:
        print("ERREUR: Utilisateur 'dev' non trouvé")
        return False
    
    # Créer un broker avec des clés de test
    test_api_key = "test_api_key_12345"
    test_api_secret = "test_api_secret_67890"
    test_api_password = "test_passphrase"
    
    broker = Broker(
        user=user,
        exchange='binance',
        name='Test Encryption',
        api_key=test_api_key,
        api_secret=test_api_secret,
        api_password=test_api_password,
        is_testnet=True
    )
    
    # Sauvegarder (déclenche le chiffrement)
    broker.save()
    print(f"Broker créé avec ID: {broker.id}")
    
    # Recharger depuis la DB
    broker_from_db = Broker.objects.get(id=broker.id)
    
    # Vérifier que les clés sont chiffrées en DB
    print(f"Clé API en DB (chiffrée): {broker_from_db.api_key[:20]}...")
    print(f"Secret API en DB (chiffrée): {broker_from_db.api_secret[:20]}...")
    
    # Les clés en DB doivent commencer par 'gAAAA' (signature Fernet)
    if not broker_from_db.api_key.startswith('gAAAA'):
        print("ERREUR: La clé API n'est pas chiffrée !")
        return False
    
    if not broker_from_db.api_secret.startswith('gAAAA'):
        print("ERREUR: Le secret API n'est pas chiffré !")
        return False
    
    # Tester le déchiffrement
    decrypted_key = broker_from_db.decrypt_field(broker_from_db.api_key)
    decrypted_secret = broker_from_db.decrypt_field(broker_from_db.api_secret)
    decrypted_password = broker_from_db.decrypt_field(broker_from_db.api_password)
    
    print(f"Clé API déchiffrée: {decrypted_key}")
    print(f"Secret API déchiffré: {decrypted_secret}")
    print(f"Passphrase déchiffrée: {decrypted_password}")
    
    # Vérifier que le déchiffrement fonctionne
    if decrypted_key != test_api_key:
        print(f"ERREUR: Déchiffrement clé API échoué. Attendu: {test_api_key}, Reçu: {decrypted_key}")
        return False
    
    if decrypted_secret != test_api_secret:
        print(f"ERREUR: Déchiffrement secret API échoué. Attendu: {test_api_secret}, Reçu: {decrypted_secret}")
        return False
    
    if decrypted_password != test_api_password:
        print(f"ERREUR: Déchiffrement passphrase échoué. Attendu: {test_api_password}, Reçu: {decrypted_password}")
        return False
    
    print("OK Chiffrement/déchiffrement Broker fonctionnel")
    
    # Nettoyer
    broker.delete()
    print("Broker de test supprimé")
    
    return True

def test_user_encryption():
    """Test du chiffrement des API keys utilisateur (IA)"""
    print("\nTest du chiffrement des clés API - Utilisateur")
    
    # Récupérer l'utilisateur dev
    try:
        user = User.objects.get(username='dev')
    except User.DoesNotExist:
        print("ERREUR: Utilisateur 'dev' non trouvé")
        return False
    
    # Sauvegarder une clé API non chiffrée
    test_ai_key = "sk-or-test-12345-abcdef"
    user.ai_api_key = test_ai_key
    user.save()
    
    # Recharger depuis la DB
    user.refresh_from_db()
    
    # Vérifier que la clé est chiffrée en DB
    print(f"Clé IA en DB (chiffrée): {user.ai_api_key[:20]}...")
    
    if not user.ai_api_key.startswith('gAAAA'):
        print("ERREUR: La clé IA n'est pas chiffrée !")
        return False
    
    # Tester le déchiffrement
    decrypted_ai_key = user.decrypt_api_key()
    print(f"Clé IA déchiffrée: {decrypted_ai_key}")
    
    if decrypted_ai_key != test_ai_key:
        print(f"ERREUR: Déchiffrement clé IA échoué. Attendu: {test_ai_key}, Reçu: {decrypted_ai_key}")
        return False
    
    print("OK Chiffrement/déchiffrement Utilisateur fonctionnel")
    
    # Réinitialiser
    user.ai_api_key = ""
    user.save()
    
    return True

def main():
    print("Tests de chiffrement - Aristobot3")
    print("=" * 50)
    
    # Test chiffrement Broker
    broker_ok = test_broker_encryption()
    
    # Test chiffrement Utilisateur
    user_ok = test_user_encryption()
    
    print("\n" + "=" * 50)
    if broker_ok and user_ok:
        print("OK Tous les tests de chiffrement sont passés !")
        return True
    else:
        print("ERREUR: Certains tests de chiffrement ont échoué")
        if not broker_ok:
            print("- Chiffrement Broker échoué")
        if not user_ok:
            print("- Chiffrement Utilisateur échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)