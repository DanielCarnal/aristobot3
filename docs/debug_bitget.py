#!/usr/bin/env python3
"""
Script de diagnostic pour comprendre la structure HTML de Bitget
"""

import requests
import time
from bs4 import BeautifulSoup
from pathlib import Path

def debug_bitget_page():
    """Analyse une page Bitget pour comprendre sa structure"""
    
    # Headers identiques au scraper principal
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'www.bitget.com',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Brave";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # Établit la session
    print("Établissement de la session...")
    home_response = session.get('https://www.bitget.com/', timeout=10)
    print(f"Page d'accueil: {home_response.status_code}")
    
    # Test de la page de documentation
    url = "https://www.bitget.com/api-doc/spot/intro"
    print(f"\nTest de: {url}")
    
    # SI ça ne marche pas, on essaie sans Accept-Encoding pour éviter la compression
    headers_no_compression = headers.copy()
    headers_no_compression.pop('Accept-Encoding', None)
    headers_no_compression['Referer'] = 'https://www.bitget.com/api-doc/'
    
    try:
        response = session.get(url, timeout=15, headers=headers_no_compression)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Encoding: {response.headers.get('content-encoding', 'N/A')}")
        print(f"Taille du contenu: {len(response.content)} bytes")
        print(f"Taille du texte: {len(response.text)} caractères")
        
        # Vérifie si on a un contenu valide
        if response.status_code != 200:
            print(f"[ERROR] HTTP: {response.status_code}")
            print(f"Headers de reponse: {dict(response.headers)}")
        
        # Sauvegarde le HTML brut pour inspection
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        # Sauvegarde le contenu brut ET le texte décodé
        with open(debug_dir / "raw_content.bin", 'wb') as f:
            f.write(response.content)
        
        try:
            with open(debug_dir / "raw_html.html", 'w', encoding='utf-8', errors='ignore') as f:
                f.write(response.text)
            print(f"HTML brut sauvegarde dans: {debug_dir / 'raw_html.html'}")
        except Exception as e:
            print(f"[ERROR] Erreur sauvegarde HTML: {e}")
        
        # Vérifie si c'est du HTML valide
        if '<html' in response.text[:1000].lower():
            print("[OK] Contenu HTML detecte")
            soup = BeautifulSoup(response.text, 'html.parser')
        else:
            print("[ERROR] Pas de HTML valide detecte dans les 1000 premiers caracteres")
            print(f"Debut du contenu: {response.text[:200]}")
            return
            
    except Exception as e:
        print(f"[ERROR] Erreur de requete: {e}")
        return
    
    print("\n" + "="*50)
    print("ANALYSE DE LA STRUCTURE HTML")
    print("="*50)
    
    # Cherche différents sélecteurs possibles
    selectors_to_try = [
        ('title', 'title'),
        ('main', 'main'),
        ('article', 'article'),
        ('.content', 'div.content'),
        ('.main-content', 'div.main-content'),
        ('.doc-content', 'div.doc-content'),
        ('.documentation', 'div.documentation'),
        ('.api-doc', 'div.api-doc'),
        ('.markdown-body', 'div.markdown-body'),
        ('.container', 'div.container'),
        ('#content', '#content'),
        ('#main', '#main'),
    ]
    
    for name, selector in selectors_to_try:
        try:
            elements = soup.select(selector)
            print(f"\n{name} ({selector}):")
            if elements:
                print(f"  Trouvé {len(elements)} élément(s)")
                first_elem = elements[0]
                text_preview = first_elem.get_text().strip()[:200]
                print(f"  Aperçu du texte: {text_preview}...")
                
                # Sauvegarde du contenu de cet élément
                with open(debug_dir / f"content_{name.replace('.', '_').replace('#', '_')}.html", 'w', encoding='utf-8') as f:
                    f.write(str(first_elem))
            else:
                print(f"  Aucun élément trouvé")
        except Exception as e:
            print(f"  Erreur: {e}")
    
    # Affiche les classes CSS disponibles
    print(f"\n" + "="*50)
    print("CLASSES CSS DISPONIBLES (première 20)")
    print("="*50)
    
    all_classes = set()
    for elem in soup.find_all(True):
        if elem.get('class'):
            all_classes.update(elem.get('class'))
    
    sorted_classes = sorted(list(all_classes))[:20]
    for cls in sorted_classes:
        print(f"  .{cls}")
    
    # Affiche les IDs disponibles
    print(f"\n" + "="*30)
    print("IDS DISPONIBLES")
    print("="*30)
    
    all_ids = set()
    for elem in soup.find_all(True):
        if elem.get('id'):
            all_ids.add(elem.get('id'))
    
    for elem_id in sorted(list(all_ids)):
        print(f"  #{elem_id}")
    
    # Cherche du contenu qui ressemble à de la documentation
    print(f"\n" + "="*50)
    print("RECHERCHE DE CONTENU DOCUMENTATION")
    print("="*50)
    
    # Cherche des mots-clés typiques de documentation API
    keywords = ['api', 'endpoint', 'request', 'response', 'parameter', 'authentication']
    
    for keyword in keywords:
        elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())
        if elements:
            print(f"\nMot-clé '{keyword}' trouvé {len(elements)} fois")
            # Affiche le contexte du premier
            if elements:
                parent = elements[0].parent
                if parent:
                    print(f"  Contexte: {parent.name} avec classes {parent.get('class', [])}")

if __name__ == "__main__":
    debug_bitget_page()
    print(f"\nTerminé! Vérifie le dossier 'debug_output' pour les fichiers HTML.")
    print("Utilise ces informations pour améliorer le scraper principal.")
