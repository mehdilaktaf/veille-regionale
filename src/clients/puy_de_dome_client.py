import logging
from urllib.parse import unquote, urljoin
from bs4 import BeautifulSoup

from src.raa_client import (
    AnnualPageRaaClient,
    RaaError,
)

logger = logging.getLogger(__name__)

class PuyDeDomeRaaClient(AnnualPageRaaClient):
    """Client pour le RAA du Puy-de-Dôme.
    
    Structure simple : page section -> page annuelle -> liens PDF directs.
    La date est présente dans le texte du lien (ex: « ... PDF - 0,13 Mb - 17/09/2026 »).
    """

    def __init__(self, base_url, card_needle="2026", timeout=60):
        # base_url est la page section : .../Recueils-des-actes-administratifs
        # On doit pointer vers la page spécifique du dépt : .../Recueils-des-actes-administratifs-Puy-de-Dome
        # Mais pour rester flexible avec build_client, on gère la redirection ici si besoin.
        super().__init__(base_url, card_needle, timeout)

    def find_annual_page(self):
        """Surcharge pour gérer le lien spécifique vers la page du dépt avant les années."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        
        # Cherche le lien vers la page spécifique du Puy-de-Dôme
        dept_link = soup.find("a", string=lambda t: t and "Recueils des actes administratifs Puy-de-Dôme" in t)
        if dept_link and dept_link.get("href"):
            dept_url = urljoin(self.base_url, dept_link["href"])
            
            # Maintenant on cherche l'année sur cette page
            dept_soup = BeautifulSoup(self._get(dept_url).text, "html.parser")
            for h2 in dept_soup.select("h2"):
                link = h2.find("a")
                if link and link.get("href") and self.card_needle in link.get_text():
                    return urljoin(dept_url, link["href"])
        
        return super().find_annual_page()
