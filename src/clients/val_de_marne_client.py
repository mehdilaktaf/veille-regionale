import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import (
    RaaHttpClient,
    dedupe_documents,
    select_month_documents,
    relaxed_day_month,
    link_day_month,
    DOWNLOAD_LINK_SELECTOR,
)

logger = logging.getLogger(__name__)

class ValDeMarneRaaClient(RaaHttpClient):
    """Client pour le RAA du Val-de-Marne.
    
    Structure :
    - Page racine : /Publications/Publications-legales/RAA-Recueil-des-actes-administratifs
    - Page annuelle : /Publications/Publications-legales/RAA-Recueil-des-actes-administratifs/Les-recueils-des-actes-administratifs-annee-YYYY
    - Liste directe des PDF sur la page annuelle (pas de pages mensuelles séparées).
    - Date dans le texte du lien ("du 6 octobre 2026") et dans le titre ("... - 07/10/2026").
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        # base_url is https://www.val-de-marne.gouv.fr/Publications/Publications-legales/RAA-Recueil-des-actes-administratifs
        self.annual_url = urljoin(base_url + "/", f"Les-recueils-des-actes-administratifs-annee-{year}")

    def _collect(self, soup, documents):
        # Recherche de tous les liens se terminant par .pdf
        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href")
            if not href or not href.lower().endswith(".pdf"):
                continue
            name = unquote(href.split("/")[-1])
            
            # Source 1 : span CMS (si présent)
            cms_dm = link_day_month(link)
            
            # Source 2 : title ou texte du lien
            title = link.get("title", "")
            text = link.get_text(strip=True)
            second_dm = relaxed_day_month(title) or relaxed_day_month(text)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_dm,
                    second_dm,
                )
            )

    def list_documents(self):
        """Liste tous les documents de la page annuelle."""
        soup = BeautifulSoup(self._get(self.annual_url).text, "html.parser")
        documents = []
        self._collect(soup, documents)
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Filtre les documents de la page annuelle pour le mois cible."""
        return select_month_documents(self.list_documents(), month, secondary_source="title/texte")
