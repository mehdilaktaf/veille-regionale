import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import RaaHttpClient, RaaError, parse_day_month, select_month_documents, dedupe_documents, relaxed_day_month

logger = logging.getLogger(__name__)

class CorrezeRaaClient(RaaHttpClient):
    """Client HTTP pour le RAA de la Corrèze.
    Structure : Page section -> Page annuelle -> Liens PDF directs.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def _find_annual_url(self):
        """Trouve l'URL de la page annuelle pour l'année ciblée."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            if f"année {self.year}" in text.lower() or f"Année {self.year}" in text:
                return urljoin(self.base_url, link["href"])
        raise RaaError(f"Page annuelle introuvable pour l'année {self.year} sur {self.base_url}")

    def list_documents(self):
        """Retourne tous les documents de l'année."""
        annual_url = self._find_annual_url()
        soup = BeautifulSoup(self._get(annual_url).text, "html.parser")
        
        documents = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".pdf" not in href.lower():
                continue
            
            name = unquote(href.split("/")[-1])
            # La date est dans le title ou le texte du lien
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
            
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les documents pour un mois spécifique."""
        docs = self.list_documents()
        return select_month_documents(docs, month, secondary_source="texte du lien")
