import logging
from urllib.parse import unquote, urljoin
from bs4 import BeautifulSoup

from src.raa_client import (
    RaaHttpClient,
    RaaError,
    parse_day_month,
    du_day_month,
    relaxed_day_month,
    select_month_documents,
    find_annual_href,
    dedupe_documents,
)

logger = logging.getLogger(__name__)

class SavoieRaaClient(RaaHttpClient):
    """Client pour le RAA de la Savoie.
    
    Particularité : une année peut être divisée en plusieurs pages 
    (ex: « 2026 - 1 », « 2026 - 2 »). On collecte les documents de toutes 
    les pages annuelles correspondant à l'année.
    La date est présente dans le texte du lien (ex: « ... PDF - 0,44 Mb - 31/07/2026 »).
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = str(year)

    def list_documents(self):
        """Retourne les documents de toutes les pages annuelles de l'année :
        (url, nom, jour_mois_cms, jour_mois_nom).
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        
        # On cherche toutes les cartes h2 dont le texte contient l'année
        annual_hrefs = []
        for h2 in soup.select("h2.fr-card__title"):
            link = h2.find("a")
            if link and link.get("href") and self.year in link.get_text():
                annual_hrefs.append(urljoin(self.base_url, link["href"]))
        
        if not annual_hrefs:
            raise RaaError(f"Aucune page annuelle trouvée pour l'année {self.year} sur {self.base_url}")

        all_documents = []
        for annual_url in annual_hrefs:
            logger.info("Collecte sur la page annuelle : %s", annual_url)
            annual_soup = BeautifulSoup(self._get(annual_url).text, "html.parser")
            
            # On cherche tous les liens vers des PDF
            for link in annual_soup.select("a[href$='.pdf']"):
                href = link.get("href")
                if not href:
                    continue
                
                name = unquote(href.split("/")[-1])
                link_text = link.get_text(strip=True)
                
                # La date est dans le texte du lien : « ... PDF - 0,44 Mb - 31/07/2026 »
                # On utilise parse_day_month sur le texte complet du lien.
                cms_day_month = parse_day_month(link_text)
                
                all_documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        cms_day_month,
                        du_day_month(name) or relaxed_day_month(name),
                    )
                )
        
        return dedupe_documents(all_documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, triés chronologiquement."""
        return select_month_documents(self.list_documents(), month, secondary_source="texte du lien")
