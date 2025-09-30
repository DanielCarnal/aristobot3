#!/usr/bin/env python
"""
Script de debug pour identifier la source du problème UTF-8
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

print("=== DEBUG ENVIRONNEMENT ===")
print(f"Python version: {sys.version}")
print(f"Python encoding: {sys.getdefaultencoding()}")
print(f"File system encoding: {sys.getfilesystemencoding()}")
print()

# Test du fichier .env
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR.parent / '.env'
print(f"Chemin .env: {env_path}")
print(f"Fichier .env existe: {env_path.exists()}")

# Test de lecture directe du fichier .env
try:
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print("✅ Lecture UTF-8 du .env: OK")
except UnicodeDecodeError as e:
    print(f"❌ Erreur UTF-8 dans .env: {e}")
    # Essai avec Windows-1252
    try:
        with open(env_path, 'r', encoding='windows-1252') as f:
            content = f.read()
        print("⚠️ Le fichier .env est en Windows-1252, pas UTF-8")
    except Exception as e2:
        print(f"❌ Erreur Windows-1252: {e2}")

# Test de load_dotenv
try:
    load_dotenv(env_path)
    print("✅ load_dotenv: OK")
except Exception as e:
    print(f"❌ Erreur load_dotenv: {e}")

# Test des variables d'environnement
print("\n=== VARIABLES D'ENVIRONNEMENT ===")
db_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
for var in db_vars:
    value = os.getenv(var)
    print(f"{var}: {repr(value)}")

# Test de connexion PostgreSQL sans Django
print("\n=== TEST CONNEXION POSTGRESQL ===")
try:
    import psycopg2
    
    # Paramètres de connexion
    params = {
        'dbname': os.getenv('DB_NAME', 'aristobot3'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
    }
    
    print(f"Paramètres de connexion: {params}")
    
    # Test de connexion
    conn = psycopg2.connect(**params)
    print("✅ Connexion PostgreSQL: OK")
    conn.close()
    
except ImportError:
    print("❌ psycopg2 non installé")
except Exception as e:
    print(f"❌ Erreur connexion PostgreSQL: {e}")
    print(f"Type d'erreur: {type(e)}")

print("\n=== VARIABLES SYSTÈME ===")
print(f"USERNAME: {os.getenv('USERNAME')}")
print(f"USERPROFILE: {os.getenv('USERPROFILE')}")
print(f"PATH contient des caractères non-ASCII: {any(ord(c) > 127 for c in os.getenv('PATH', ''))}")
