import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
from src.raa_client import (
    DOWNLOAD_LINK_SELECTOR,
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

class MorbihanRaaClient(RaaHttpClient):
    """Client HTTP du RAA du Morbihan.
    
    Navigation : page root -> POST « Années-liste-docs » -> page annuelle paginée.
    Date : extraite du nom de fichier (source unique).
    """

    def __init__(self, base_url, year=None, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def list_documents(self):
        """Retourne les documents de l'année : (url, nom, date_cms, date_nom)."""
        if not self.year:
            raise RaaError("L'année est requise pour le client Morbihan")

        payload = {"Années-liste-docs": f"RAA/Annee-{self.year}"}
        url = self.base_url
        documents = []

        while url:
            # On utilise _post pour la première page, et _get pour la pagination (si les hrefs sont directs)
            # Mais ici les hrefs de pagination commencent par /RAA/Annee...
            # On vérifie si on doit POST ou GET.
            if url == self.base_url:
                response = self._post(url, data=payload)
            else:
                response = self._get(url)
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for link in soup.select("a[href$='.pdf'], a.fr-link--download"):
                href = link.get("href")
                if not href:
                    continue
                name = unquote(href.split("/")[-1])
                # Pas de span CMS sur ce site, on utilise le nom de fichier
                documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        None,
                        relaxed_day_month(name),
                    )
                )

            # Pagination
            next_link = None
            for a in soup.select("ul.fr-pagination__list li a"):
                if a.get_text(strip=True) == "Suivant" and a.get("href"):
                    next_link = urljoin(self.base_url, a["href"])
                    break
            url = next_link

        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        return select_month_documents(self.list_documents(), month, secondary_source="nom de fichier")
