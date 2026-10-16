import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from src.raa_client import AnnualPageRaaClient, RaaError, relaxed_day_month, select_month_documents

logger = logging.getLogger(__name__)

class LoireRaaClient(AnnualPageRaaClient):
    """Client pour le RAA de la Loire.
    
    Structure :
    - Page section : liens h2 vers les pages annuelles (« 2026 numéros spéciaux », etc.).
    - Page annuelle : liens directs vers PDF. La date est dans le texte du lien.
    """

    def __init__(self, base_url, year, timeout=60):
        # On cherche les pages "numéros spéciaux" ou "numéros mensuels" pour l'année donnée
        card_needle = (f"{year} numéros spéciaux", f"{year} numéros mensuels")
        super().__init__(base_url, card_needle, timeout=timeout)

    def list_documents(self):
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle introuvable ({self.card_needle!r}) "
                    f"sur {self.base_url}"
                )
        
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        # Les documents sont des liens se terminant par .pdf
        documents = []
        for link in soup.select("a[href$='.pdf']"):
            href = link.get("href")
            if not href:
                continue
            name = unquote(href.split("/")[-1])
            # La date est dans le texte du lien : « Télécharger ... PDF - 0,16 Mb - 24/12/2025 »
            text = link.get_text(strip=True)
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    None, # Pas de span CMS
                    relaxed_day_month(text),
                )
            )
        return documents
