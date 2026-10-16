import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import RaaHttpClient, RaaError, parse_day_month, select_month_documents, dedupe_documents, relaxed_day_month

logger = logging.getLogger(__name__)

class YvelinesRaaClient(RaaHttpClient):
    """Client HTTP pour le RAA des Yvelines.
    Structure : Page annuelle -> Pages mensuelles -> Liens PDF directs.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        # L'URL de base passée est la page section, on construit l'URL annuelle.
        self.annual_url = urljoin(base_url, f"/Publications/Recueil-des-actes-administratifs/{year}")

    def _get_month_url(self, month_code):
        """Construit l'URL du mois (ex: 08 -> AOUT)."""
        # On utilise un mapping simple car les slugs sont en majuscules.
        month_slugs = {
            "01": "JANVIER", "02": "FEVRIER", "03": "MARS", "04": "AVRIL",
            "05": "MAI", "06": "JUIN", "07": "JUILLET", "08": "AOUT",
            "09": "SEPTEMBRE", "10": "OCTOBRE", "11": "NOVEMBRE", "12": "DECEMBRE",
        }
        slug = month_slugs.get(month_code)
        if not slug:
            return None
        return f"{self.annual_url}/{slug}"

    def _collect_from_month_page(self, month_url):
        """Extrait les documents d'une page mensuelle."""
        soup = BeautifulSoup(self._get(month_url).text, "html.parser")
        documents = []
        # Les liens sont des <a> contenant "Télécharger RAA" et pointant vers un .pdf
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".pdf" not in href.lower() or "Télécharger RAA" not in link.get_text():
                continue
            
            name = unquote(href.split("/")[-1])
            text = link.get_text(strip=True)
            
            # La date est dans le texte : "PDF - 4,63 Mb - 03/08/2026"
            # On utilise parse_day_month sur le texte complet.
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
        """Retourne tous les documents de l'année."""
        soup = BeautifulSoup(self._get(self.annual_url).text, "html.parser")
        # On cherche tous les liens vers les mois
        month_links = [
            link["href"] for link in soup.find_all("a", href=True)
            if "/Recueil-des-actes-administratifs/" in link["href"] 
            and link["href"].split("/")[-1].upper() in {
                "JANVIER", "FEVRIER", "MARS", "AVRIL", "MAI", "JUIN", 
                "JUILLET", "AOUT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DECEMBRE"
            }
        ]
        
        all_docs = []
        for href in month_links:
            url = urljoin(self.annual_url, href)
            all_docs.extend(self._collect_from_month_page(url))
            
        return dedupe_documents(all_docs)

    def documents_for_month(self, month):
        """Retourne les documents pour un mois spécifique."""
        month_url = self._get_month_url(month)
        if not month_url:
            return []
            
        docs = self._collect_from_month_page(month_url)
        return select_month_documents(docs, month, secondary_source="texte du lien")
