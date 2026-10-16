import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
from src.raa_client import (
    DOWNLOAD_LINK_SELECTOR,
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    link_day_month,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

class CotesDArmorRaaClient(RaaHttpClient):
    """Client HTTP du RAA des Côtes-d'Armor.
    
    Structure : page root -> liens vers pages mensuelles -> liens PDF.
    Date : span.fr-link__detail CMS fait foi.
    """

    def __init__(self, base_url, year=None, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def _get_month_url(self, month_name):
        """Construit l'URL du mois (ex: SEPTEMBRE-2026)."""
        # On suppose que month_name est en majuscule sans accent, ex: 'SEPTEMBRE'
        return urljoin(self.base_url, f"/index.php/Publications/Recueil-des-actes-administratifs/{month_name.upper()}-{self.year}")

    def list_documents(self):
        """Sert de base pour documents_for_month. Ici on ne liste pas toute l'année
        car on préfère cibler le mois via documents_for_month."""
        raise NotImplementedError("Utilisez documents_for_month")

    def documents_for_month(self, month_code):
        """Retourne les liens des PDF du mois.
        
        month_code : '09' pour septembre.
        """
        from src.raa_client import MONTH_NAMES_FR
        month_name = MONTH_NAMES_FR.get(month_code)
        if not month_name:
            raise RaaError(f"Code mois inconnu : {month_code}")
        
        # Normalisation simple du nom du mois pour l'URL (ex: février -> FEVRIER)
        month_url_part = month_name.upper().replace("É", "E")
        url = urljoin(self.base_url, f"/index.php/Publications/Recueil-des-actes-administratifs/{month_url_part}-{self.year}")
        
        documents = []
        while url:
            response = self._get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            for link in soup.select("a[href$='.pdf'], a.fr-link--download"):
                href = link.get("href")
                if not href:
                    continue
                name = unquote(href.split("/")[-1])
                
                cms_date = link_day_month(link)
                second_date = relaxed_day_month(name)
                
                # Si aucune date n'est détectable, on utilise le mois de la page (source unique)
                if cms_date is None and second_date is None:
                    cms_date = (None, int(month_code))
                
                documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        cms_date,
                        second_date,
                    )
                )

            # Pagination
            next_link = None
            for a in soup.select("ul.fr-pagination__list li a"):
                if a.get_text(strip=True) == "Suivant" and a.get("href"):
                    next_link = urljoin(self.base_url, a["href"])
                    break
            url = next_link

        return select_month_documents(dedupe_documents(documents), month_code)
