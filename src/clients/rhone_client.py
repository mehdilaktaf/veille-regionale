import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from src.raa_client import MonthCardsRaaClient, RaaError, relaxed_day_month, find_annual_href

logger = logging.getLogger(__name__)

class RhoneRaaClient(MonthCardsRaaClient):
    """Client pour le RAA du Rhône.
    
    Structure :
    - Page section : liens h2 vers les pages annuelles (« Recueils de YYYY »).
    - Page annuelle : cartes mois (« Recueils de <Mois> »).
    - Page mensuelle : liens directs vers PDF. La date est dans le texte du lien.
    """

    def __init__(self, base_url, year, timeout=60):
        # On doit trouver l'URL de la page annuelle à partir de la page section
        # On utilise une session temporaire pour cette découverte
        from src.raa_client import RaaHttpClient
        temp_client = RaaHttpClient(base_url, timeout=timeout)
        soup = BeautifulSoup(temp_client._get(base_url).text, "html.parser")
        
        needle = f"Recueils de {year}"
        annual_href = find_annual_href(soup, needle)
        if not annual_href:
            raise RaaError(f"Page annuelle pour {year} introuvable sur {base_url}")
        
        annual_url = urljoin(base_url, annual_href)
        # On initialise la classe parente avec l'URL de la page annuelle comme base_url
        super().__init__(annual_url, timeout=timeout)

    def _collect(self, soup, documents):
        """Surcharge de _collect pour extraire la date du texte du lien."""
        for link in soup.select("a[href$='.pdf']"):
            href = link.get("href")
            if not href:
                continue
            name = unquote(href.split("/")[-1])
            text = link.get_text(strip=True)
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    None, # Pas de span CMS
                    relaxed_day_month(text),
                )
            )
