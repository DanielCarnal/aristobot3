#!/usr/bin/env python3
"""
Bitget API Documentation Scraper
Convertit la documentation API Bitget en fichiers Markdown locaux
"""

import requests
import os
import re
import time
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
import markdownify
from pathlib import Path

class BitgetDocScraper:
    def __init__(self, output_dir="bitget_docs"):
        self.base_url = "https://www.bitget.com"
        self.doc_base = "https://www.bitget.com/api-doc/"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.visited_urls = set()
        self.failed_urls = set()
        
        # Headers exactement comme ton navigateur + améliorations
        self.headers = {
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
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Ajoute des adapters pour retry automatique
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def clean_filename(self, url):
        """Convertit une URL en nom de fichier valide"""
        # Supprime le domaine et les paramètres
        path = urlparse(url).path
        if path.endswith('/'):
            path += 'index'
        
        # Remplace les caractères invalides
        filename = re.sub(r'[<>:"/\\|?*]', '_', path)
        filename = filename.replace('/api-doc/', '').replace('/', '_')
        
        if not filename:
            filename = "index"
            
        return filename + ".md"

    def get_page_content(self, url):
        """Récupère le contenu d'une page avec plusieurs stratégies"""
        try:
            print(f"Récupération: {url}")
            
            # Stratégie 1: Visite d'abord la page d'accueil pour établir une session
            if not hasattr(self, '_session_established'):
                print("Établissement de la session...")
                home_response = self.session.get('https://www.bitget.com/', timeout=10)
                if home_response.status_code == 200:
                    print("Session établie avec succès")
                    self._session_established = True
                    
                    # Récupère les cookies de la page d'accueil
                    for cookie in home_response.cookies:
                        self.session.cookies.set(cookie.name, cookie.value)
                else:
                    print(f"Problème avec la page d'accueil: {home_response.status_code}")
            
            # Petite pause pour éviter de surcharger le serveur
            time.sleep(1)
            
            # Stratégie 2: Ajoute un referer dynamique
            headers = self.headers.copy()
            headers['Referer'] = 'https://www.bitget.com/api-doc/'
            
            response = self.session.get(url, timeout=15, headers=headers)
            
            # Stratégie 3: Si 403, essaie avec différents referers
            if response.status_code == 403:
                print("Erreur 403, tentative avec referer différent...")
                headers['Referer'] = 'https://www.bitget.com/'
                response = self.session.get(url, timeout=15, headers=headers)
                
            if response.status_code == 403:
                print("Erreur 403, tentative sans referer...")
                headers.pop('Referer', None)
                response = self.session.get(url, timeout=15, headers=headers)
            
            response.raise_for_status()
            print(f"✅ Succès: {response.status_code}")
            return response.text
            
        except requests.RequestException as e:
            print(f"❌ Erreur lors de la récupération de {url}: {e}")
            
            # Stratégie 4: Essaie avec une pause plus longue
            if "403" in str(e):
                print("Tentative avec pause longue...")
                time.sleep(5)
                try:
                    # Headers minimalistes
                    minimal_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    }
                    response = self.session.get(url, timeout=15, headers=minimal_headers)
                    response.raise_for_status()
                    print(f"✅ Succès avec headers minimalistes: {response.status_code}")
                    return response.text
                except:
                    pass
            
            self.failed_urls.add(url)
            return None

    def extract_content_and_links(self, html, current_url):
        """Extrait le contenu principal et trouve les liens de documentation"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Trouve le contenu principal (ajuste selon la structure du site)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        
        if not main_content:
            # Fallback: prendre tout le body moins la navigation
            main_content = soup.find('body')
            # Supprime les éléments de navigation/footer
            for elem in main_content.find_all(['nav', 'header', 'footer']):
                elem.decompose()
        
        # Trouve les liens vers d'autres pages de documentation
        doc_links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            
            # Ne garde que les liens vers la documentation API
            if '/api-doc/' in full_url and full_url.startswith(self.base_url):
                # Supprime les ancres
                full_url = full_url.split('#')[0]
                doc_links.add(full_url)
        
        return main_content, doc_links

    def html_to_markdown(self, html_content, url):
        """Convertit le HTML en Markdown"""
        if not html_content:
            return "# Erreur\n\nImpossible de récupérer le contenu de cette page."
        
        # Configuration pour markdownify
        md = markdownify.markdownify(
            str(html_content),
            heading_style="ATX",  # Utilise # ## ### au lieu de === ---
            bullets="-",  # Utilise - pour les listes
            strip=['script', 'style'],  # Supprime JS et CSS
            convert=['a', 'b', 'strong', 'i', 'em', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'td', 'th']
        )
        
        # Ajoute un header avec l'URL source
        header = f"# Documentation API Bitget\n\n**Source:** {url}\n\n---\n\n"
        
        return header + md

    def save_page(self, url, content):
        """Sauvegarde une page en Markdown"""
        filename = self.clean_filename(url)
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Sauvegardé: {filename}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de {filename}: {e}")

    def crawl_documentation(self, start_url=None, max_pages=100):
        """Lance le crawling de la documentation"""
        if start_url is None:
            start_url = "https://www.bitget.com/api-doc/spot/intro"
        
        urls_to_visit = [start_url]
        pages_processed = 0
        
        print(f"Début du crawling depuis: {start_url}")
        print(f"Dossier de sortie: {self.output_dir}")
        print("=" * 50)
        
        while urls_to_visit and pages_processed < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            
            # Récupère le contenu
            html = self.get_page_content(current_url)
            if html is None:
                continue
            
            # Extrait le contenu et les liens
            main_content, new_links = self.extract_content_and_links(html, current_url)
            
            # Convertit en Markdown
            markdown_content = self.html_to_markdown(main_content, current_url)
            
            # Sauvegarde
            self.save_page(current_url, markdown_content)
            
            # Ajoute les nouveaux liens à visiter
            for link in new_links:
                if link not in self.visited_urls:
                    urls_to_visit.append(link)
            
            pages_processed += 1
            print(f"Progression: {pages_processed}/{max_pages} pages")
        
        print("=" * 50)
        print(f"Crawling terminé!")
        print(f"Pages récupérées: {pages_processed}")
        print(f"Pages en erreur: {len(self.failed_urls)}")
        print(f"Fichiers sauvegardés dans: {self.output_dir}")
        
        if self.failed_urls:
            print("\nPages en erreur:")
            for url in self.failed_urls:
                print(f"  - {url}")

    def create_index(self):
        """Crée un fichier index avec tous les liens"""
        index_content = "# Index - Documentation API Bitget\n\n"
        
        markdown_files = list(self.output_dir.glob("*.md"))
        markdown_files.sort()
        
        for md_file in markdown_files:
            if md_file.name != "index.md":
                # Lit la première ligne pour obtenir le titre
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        title = md_file.stem.replace('_', ' ').title()
                        for line in lines:
                            if line.startswith('# ') and 'Documentation API Bitget' not in line:
                                title = line.strip('# \n')
                                break
                    
                    index_content += f"- [{title}]({md_file.name})\n"
                except:
                    index_content += f"- [{md_file.stem}]({md_file.name})\n"
        
        with open(self.output_dir / "index.md", 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"Index créé: {self.output_dir / 'index.md'}")


def main():
    """Fonction principale"""
    print("Bitget API Documentation Scraper")
    print("=" * 40)
    
    # Demande les paramètres à l'utilisateur
    output_dir = input("Dossier de sortie (défaut: bitget_docs): ").strip()
    if not output_dir:
        output_dir = "bitget_docs"
    
    max_pages = input("Nombre max de pages (défaut: 100): ").strip()
    if not max_pages:
        max_pages = 100
    else:
        max_pages = int(max_pages)
    
    # Lance le scraper
    scraper = BitgetDocScraper(output_dir)
    scraper.crawl_documentation(max_pages=max_pages)
    scraper.create_index()
    
    print(f"\nTerminé! Ouvre le fichier '{output_dir}/index.md' pour commencer.")


if __name__ == "__main__":
    # Vérification des dépendances
    try:
        import requests
        import markdownify
        from bs4 import BeautifulSoup
    except ImportError as e:
        print("Dépendances manquantes. Installe-les avec:")
        print("pip install requests beautifulsoup4 markdownify")
        print(f"Erreur: {e}")
        exit(1)
    
    main()