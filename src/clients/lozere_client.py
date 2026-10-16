import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from src.raa_client import RaaHttpClient, RaaError, link_day_month, relaxed_day_month, dedupe_documents, select_month_documents

logger = logging.getLogger(__name__)

class LozereRaaClient(RaaHttpClient):
    """Client HTTP pour le RAA de la Lozère.
    
    Structure à 4 niveaux :
    Section -> Page Annuelle (2026) -> Page Trimestre (3ème trimestre) -> Page Mois (Août) -> PDF.
    """

    MONTH_TO_QUARTER = {
        "01": "1er-trimestre", "02": "1er-trimestre", "03": "1er-trimestre",
        "04": "2eme-trimestre", "05": "2eme-trimestre", "06": "2eme-trimestre",
        "07": "3eme-trimestre", "08": "3eme-trimestre", "09": "3eme-trimestre",
        "10": "4eme-trimestre", "11": "4eme-trimestre", "12": "4eme-trimestre",
    }

    MONTH_SLUGS = {
        "01": "Janvier", "02": "Fevrier", "03": "Mars", "04": "Avril",
        "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Aout",
        "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Decembre",
    }

    def list_documents(self, year):
        """Retourne les documents de l'année : (url, nom, jour_mois_cms, jour_mois_secondaire)."""
        # On s'assure que la base_url se termine par un slash pour urljoin
        base = self.base_url if self.base_url.endswith("/") else self.base_url + "/"
        annual_url = urljoin(base, str(year))
        documents = []
        
        for month, quarter in self.MONTH_TO_QUARTER.items():
            quarter_url = urljoin(annual_url + "/", quarter)
            month_slug = self.MONTH_SLUGS[month]
            month_url = urljoin(quarter_url + "/", month_slug)
            
            try:
                soup = BeautifulSoup(self._get(month_url).text, "html.parser")
                for link in soup.select("a[href$='.pdf']"):
                    href = link.get("href")
                    if not href:
                        continue
                    name = unquote(href.split("/")[-1])
                    documents.append(
                        (
                            urljoin(self.base_url, href),
                            name,
                            link_day_month(link),
                            relaxed_day_month(link.get_text(strip=True)),
                        )
                    )
            except RaaError as e:
                logger.warning("Impossible de récupérer le mois %s pour %s : %s", month, year, e)
        
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        # Note: year is usually handled by the factory, but here we need it.
        # In the current architecture, we can't easily get 'year' from the instance 
        # unless we store it. Let's assume we store it in __init__.
        year = getattr(self, "year", "2026")
        docs = self.list_documents(year)
        return select_month_documents(docs, month)

    def __init__(self, base_url, year=None, **kwargs):
        super().__init__(base_url, **kwargs)
        self.year = year if year else "2026"
