import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import RaaHttpClient, RaaError, parse_day_month, select_month_documents, dedupe_documents, relaxed_day_month

logger = logging.getLogger(__name__)

class GirondeRaaClient(RaaHttpClient):
    """Client HTTP pour le RAA de la Gironde.
    Structure : Page section -> Pages annuelles -> Pages mensuelles -> Liens PDF.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def _find_annual_url(self):
        """Trouve l'URL de la page annuelle pour l'année ciblée."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        for link in soup.find_all("a", href=True):
            if f"l'année {self.year}" in link.get_text() or f"l'annee {self.year}" in link.get_text().lower():
                return urljoin(self.base_url, link["href"])
        raise RaaError(f"Page annuelle introuvable pour l'année {self.year} sur {self.base_url}")

    def _find_month_url(self, annual_url, month_code):
        """Trouve l'URL de la page mensuelle."""
        month_names = {
            "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
            "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Août",
            "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre",
        }
        name = month_names.get(month_code)
        if not name:
            return None
            
        soup = BeautifulSoup(self._get(annual_url).text, "html.parser")
        for link in soup.find_all("a", href=True):
            if name in link.get_text():
                return urljoin(annual_url, link["href"])
        return None

    def _collect_from_month_page(self, month_url):
        """Extrait les documents d'une page mensuelle, gérant la pagination."""
        documents = []
        current_url = month_url
        
        while current_url:
            soup = BeautifulSoup(self._get(current_url).text, "html.parser")
            
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if ".pdf" not in href.lower():
                    continue
                
                name = unquote(href.split("/")[-1])
                # Date dans le title ou le texte
                text = link.get("title") or link.get_text(strip=True)
                cms_day_month = parse_day_month(text)
                
                documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        cms_day_month,
                        relaxed_day_month(name),
                    )
                )
            
            # Pagination : chercher le lien "Suivant"
            next_link = None
            for link in soup.find_all("a", href=True):
                if "Suivant" in link.get_text():
                    next_link = urljoin(current_url, link["href"])
                    break
            current_url = next_link
            
        return documents

    def list_documents(self):
        """Retourne tous les documents de l'année."""
        annual_url = self._find_annual_url()
        soup = BeautifulSoup(self._get(annual_url).text, "html.parser")
        
        month_links = [
            link["href"] for link in soup.find_all("a", href=True)
            if any(m in link.get_text() for m in [
                "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
            ])
        ]
        
        all_docs = []
        for href in month_links:
            url = urljoin(annual_url, href)
            all_docs.extend(self._collect_from_month_page(url))
            
        return dedupe_documents(all_docs)

    def documents_for_month(self, month):
        """Retourne les documents pour un mois spécifique."""
        annual_url = self._find_annual_url()
        month_url = self._find_month_url(annual_url, month)
        if not month_url:
            return []
            
        docs = self._collect_from_month_page(month_url)
        return select_month_documents(docs, month, secondary_source="texte du lien")
