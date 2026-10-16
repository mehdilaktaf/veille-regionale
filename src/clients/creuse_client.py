import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import RaaHttpClient, RaaError, parse_day_month, select_month_documents, dedupe_documents, relaxed_day_month

logger = logging.getLogger(__name__)

class CreuseRaaClient(RaaHttpClient):
    """Client HTTP pour le RAA de la Creuse.
    Structure : Page section -> Page annuelle -> Pages de type (Réguliers/Spéciaux/Nominatifs) -> Liens PDF.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def _find_annual_url(self):
        """Trouve l'URL de la page annuelle pour l'année ciblée."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            if f"Année {self.year}" in text or f"Annee {self.year}" in text.lower():
                return urljoin(self.base_url, link["href"])
        raise RaaError(f"Page annuelle introuvable pour l'année {self.year} sur {self.base_url}")

    def _collect_from_type_page(self, type_url):
        """Extrait les documents d'une page de type (ex: Réguliers)."""
        documents = []
        soup = BeautifulSoup(self._get(type_url).text, "html.parser")
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".pdf" not in href.lower():
                continue
            
            name = unquote(href.split("/")[-1])
            # La date est dans le texte du lien : "Télécharger ... PDF - 13,34 Mb - 16/01/2026"
            text = link.get_text(strip=True)
            cms_day_month = parse_day_month(text)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_day_month,
                    relaxed_day_month(name),
                )
            )
            
        return documents

    def list_documents(self):
        """Retourne tous les documents de l'année en visitant Réguliers, Spéciaux et Nominatifs."""
        annual_url = self._find_annual_url()
        soup = BeautifulSoup(self._get(annual_url).text, "html.parser")
        
        type_links = []
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            if text in ["Réguliers", "Spéciaux", "Nominatifs"]:
                type_links.append(urljoin(annual_url, link["href"]))
        
        all_docs = []
        for url in type_links:
            all_docs.extend(self._collect_from_type_page(url))
            
        return dedupe_documents(all_docs)

    def documents_for_month(self, month):
        """Retourne les documents pour un mois spécifique."""
        docs = self.list_documents()
        return select_month_documents(docs, month, secondary_source="texte du lien")
