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

class ParisRaaClient(RaaHttpClient):
    """Client pour le RAA de Paris.
    
    Structure :
    - Page annuelle avec sommaire des mois (liens simples) et quelques documents.
    - Pages mensuelles avec listes de PDF.
    """

    def _collect(self, soup, documents):
        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href")
            if not href or not href.lower().endswith(".pdf"):
                continue
            name = unquote(href.split("/")[-1])
            # Date source 1 : span CMS
            cms_dm = link_day_month(link)
            # Date source 2 : texte du lien ou titre
            text = link.get_text(strip=True)
            title = link.get("title", "")
            second_dm = relaxed_day_month(text) or relaxed_day_month(title)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_dm,
                    second_dm,
                )
            )

    def list_documents(self):
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        
        # 1. Collect from root page
        documents = []
        self._collect(soup, documents)
        
        # 2. Find month links in summary
        month_hrefs = []
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            if text in MONTHS_FR:
                month_hrefs.append(link["href"])
        
        # 3. Visit month pages
        for href in month_hrefs:
            url = urljoin(self.base_url, href).split("#")[0]
            while url is not None:
                page_soup = BeautifulSoup(self._get(url).text, "html.parser")
                self._collect(page_soup, documents)
                
                # Pagination "Suivant"
                next_link = page_soup.find("a", string="Suivant")
                url = urljoin(self.base_url, next_link["href"]) if next_link else None
        
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        # Root page docs
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        root_docs = []
        self._collect(soup, root_docs)
        
        # Target month page docs
        month_name = MONTH_NAMES_FR.get(month)
        if not month_name:
            return select_month_documents(dedupe_documents(root_docs), month)
            
        month_hrefs = []
        for link in soup.find_all("a", href=True):
            if link.get_text(strip=True).lower() == month_name.lower():
                month_hrefs.append(link["href"])
        
        all_docs = root_docs
        for href in month_hrefs:
            url = urljoin(self.base_url, href).split("#")[0]
            while url is not None:
                page_soup = BeautifulSoup(self._get(url).text, "html.parser")
                self._collect(page_soup, all_docs)
                next_link = page_soup.find("a", string="Suivant")
                url = urljoin(self.base_url, next_link["href"]) if next_link else None
                
        return select_month_documents(dedupe_documents(all_docs), month, secondary_source="texte du lien")
