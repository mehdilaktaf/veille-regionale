import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import (
    RaaHttpClient,
    dedupe_documents,
    select_month_documents,
    relaxed_day_month,
    link_day_month,
    DOWNLOAD_LINK_SELECTOR,
    MONTHS_FR,
    MONTH_NAMES_FR,
)

logger = logging.getLogger(__name__)

class SeineSaintDenisRaaClient(RaaHttpClient):
    """Client pour le RAA de la Seine-Saint-Denis.
    
    Structure :
    - Page racine : /Publications/Recueil-des-actes-administratifs
    - Page annuelle : /Publications/Recueil-des-actes-administratifs/Annee-YYYY
    - Pages mensuelles : /Publications/Recueil-des-actes-administratifs/Annee-YYYY/MOIS
    - Documents : liens PDF avec date dans le title.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        # Ensure base_url ends with / to make urljoin work as expected
        base = base_url if base_url.endswith("/") else base_url + "/"
        self.annual_url = urljoin(base, f"Annee-{year}")

    def _collect(self, soup, documents):
        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href")
            if not href or not href.lower().endswith(".pdf"):
                continue
            name = unquote(href.split("/")[-1])
            
            # Source 1 : span CMS
            cms_dm = link_day_month(link)
            
            # Source 2 : title ou texte (format pdf - 1,37 Mb - 02/02/2026)
            title = link.get("title", "")
            text = link.get_text(strip=True)
            second_dm = relaxed_day_month(title) or relaxed_day_month(text)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_dm,
                    second_dm,
                )
            )

    def list_documents(self):
        soup = BeautifulSoup(self._get(self.annual_url).text, "html.parser")
        
        # Trouver les liens vers les mois (ex: [JANVIER](/.../JANVIER))
        month_hrefs = []
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            # On normalise les accents pour matcher MONTHS_FR
            # Le site utilise "JANVIER", "FEVRIER" (sans accent)
            if text in MONTHS_FR:
                month_hrefs.append(link["href"])
        
        documents = []
        for href in month_hrefs:
            url = urljoin(self.annual_url, href)
            while url is not None:
                page_soup = BeautifulSoup(self._get(url).text, "html.parser")
                self._collect(page_soup, documents)
                
                # Pagination "Suivant"
                next_link = page_soup.find("a", string="Suivant")
                url = urljoin(self.annual_url, next_link["href"]) if next_link and next_link.get("href") else None
                
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        # On cible uniquement la page du mois demandé
        soup = BeautifulSoup(self._get(self.annual_url).text, "html.parser")
        
        # On cherche le lien du mois sur la page annuelle
        month_href = None
        import raa_client
        target_month_name = raa_client.MONTH_NAMES_FR.get(month).lower() # "février"
        
        # On trouve la version sans accent pour le mois cible (clé dans MONTHS_FR)
        month_key_no_accent = next((k for k, v in raa_client.MONTHS_FR.items() if v == month), None)
        
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            if text == target_month_name or text == month_key_no_accent:
                month_href = link["href"]
                break
        
        if not month_href:
            # Repli : recherche plus souple
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True).lower()
                if target_month_name in text or (month_key_no_accent and month_key_no_accent in text):
                    month_href = link["href"]
                    break
        
        if not month_href:
            return []
            
        all_docs = []
        url = urljoin(self.annual_url, month_href)
        while url is not None:
            page_soup = BeautifulSoup(self._get(url).text, "html.parser")
            self._collect(page_soup, all_docs)
            next_link = page_soup.find("a", string="Suivant")
            url = urljoin(self.annual_url, next_link["href"]) if next_link and next_link.get("href") else None
            
        return select_month_documents(dedupe_documents(all_docs), month, secondary_source="title/texte")
