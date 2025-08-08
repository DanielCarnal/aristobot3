#!/usr/bin/env python
"""
Test spécifique PostgreSQL avec gestion d'encodage
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger l'environnement
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / '.env')

print("=== TEST POSTGRESQL AVANCÉ ===")

try:
    import psycopg2
    from psycopg2 import sql
    
    # Paramètres de connexion
    params = {
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
    }
    
    print(f"Test 1: Connexion à la base postgres par défaut...")
    
    # Test 1: Connexion à la base postgres (par défaut)
    try:
        conn = psycopg2.connect(dbname='postgres', **params)
        conn.set_client_encoding('UTF8')
        print("✅ Connexion à postgres: OK")
        
        # Lister les bases de données
        cursor = conn.cursor()
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        print(f"Bases existantes: {[db[0] for db in databases]}")
        
        # Vérifier si Aristobot3 existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", ('Aristobot3',))
        exists = cursor.fetchone()
        
        if not exists:
            print("❌ Base de données 'Aristobot3' n'existe pas")
            print("Création de la base de données...")
            
            # Créer la base de données
            conn.autocommit = True
            cursor.execute(sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'").format(
                sql.Identifier('Aristobot3')
            ))
            print("✅ Base de données 'Aristobot3' créée")
        else:
            print("✅ Base de données 'Aristobot3' existe déjà")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur connexion postgres: {e}")
        print(f"Type: {type(e)}")
        return
    
    # Test 2: Connexion à Aristobot3
    print("\nTest 2: Connexion à Aristobot3...")
    try:
        db_params = dict(params)
        db_params['dbname'] = 'Aristobot3'
        
        conn = psycopg2.connect(**db_params)
        conn.set_client_encoding('UTF8')
        print("✅ Connexion à Aristobot3: OK")
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL version: {version}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur connexion Aristobot3: {e}")
        
except ImportError:
    print("❌ psycopg2 non installé")
    print("Installez avec: pip install psycopg2")

print("\n=== RECOMMANDATIONS ===")
print("1. Vérifiez que PostgreSQL est installé et démarré")
print("2. La base 'Aristobot3' sera créée automatiquement si elle n'existe pas")
print("3. Si l'erreur persiste, PostgreSQL pourrait ne pas être installé")
