import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import RaaHttpClient, RaaError, parse_day_month, select_month_documents, dedupe_documents, relaxed_day_month

logger = logging.getLogger(__name__)

class HauteVienneRaaClient(RaaHttpClient):
    """Client HTTP pour le RAA de la Haute-Vienne.
    Structure : Page section -> Pages semestrielles -> Liens PDF directs.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def _get_semestrial_urls(self):
        """Trouve les URLs des deux semestres pour l'année ciblée."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        urls = []
        # Patterns : "JANVIER - JUIN 2026" et "JUILLET - DÉCEMBRE 2026"
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).upper()
            if str(self.year) in text and ("JANVIER" in text or "JUILLET" in text):
                urls.append(urljoin(self.base_url, link["href"]))
        return urls

    def list_documents(self):
        """Retourne tous les documents de l'année en parcourant les deux semestres."""
        semestrial_urls = self._get_semestrial_urls()
        if not semestrial_urls:
            raise RaaError(f"Aucun semestre trouvé pour l'année {self.year} sur {self.base_url}")
            
        all_docs = []
        for url in semestrial_urls:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if ".pdf" not in href.lower():
                    continue
                
                name = unquote(href.split("/")[-1])
                text = link.get_text(strip=True)
                cms_day_month = parse_day_month(text)
                
                all_docs.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        cms_day_month,
                        relaxed_day_month(name),
                    )
                )
                
        return dedupe_documents(all_docs)

    def documents_for_month(self, month):
        """Retourne les documents pour un mois spécifique."""
        docs = self.list_documents()
        return select_month_documents(docs, month, secondary_source="texte du lien")
