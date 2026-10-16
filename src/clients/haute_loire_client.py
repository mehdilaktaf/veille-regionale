import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from src.raa_client import AnnualPageRaaClient, RaaError, relaxed_day_month

logger = logging.getLogger(__name__)

class HauteLoireRaaClient(AnnualPageRaaClient):
    """Client pour le RAA de la Haute-Loire.
    
    Structure :
    - Page section : liens h2 vers les pages annuelles (« Recueil des actes administratifs YYYY »).
    - Page annuelle : liens directs vers PDF. La date est dans le texte du lien.
    """

    def __init__(self, base_url, year, timeout=60):
        # On cherche la carte correspondant à l'année
        card_needle = f"Recueil des actes administratifs {year}"
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
            # La date est dans le texte du lien : « Télécharger recueil-43... PDF - 0,11 Mb - 16/09/2026 »
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
