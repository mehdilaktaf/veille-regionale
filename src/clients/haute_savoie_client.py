import logging
from urllib.parse import unquote, urljoin
from bs4 import BeautifulSoup

from src.raa_client import (
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    find_annual_href,
    parse_day_month,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

class HauteSavoieRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Haute-Savoie.
    
    Navigation : page section -> page annuelle (paginée) -> liens directs PDF.
    La date fait foi sur l'attribut `title` du lien CMS
    (« format pdf - 0,11 Mb - 09/09/2026 »).
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        href = find_annual_href(soup, str(self.year))
        if href is None:
            return None
        return urljoin(self.base_url, href)

    def _next_page_url(self, soup):
        for link in soup.select("ul.fr-pagination__list li a"):
            if link.get_text(strip=True) == "Suivant" and link.get("href"):
                return urljoin(self.annual_page_url, link["href"])
        return None

    def list_documents(self):
        """Retourne les documents de l'année (toutes les pages) :
        (url, nom, jour_mois_cms, jour_mois_texte).
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle {self.year} introuvable sur {self.base_url}"
                )
        documents = []
        url = self.annual_page_url
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            for link in soup.select("a[href$='.pdf']"):
                href = link.get("href")
                if not href:
                    continue
                name = unquote(href.split("/")[-1])
                documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        parse_day_month(link.get("title") or ""),
                        relaxed_day_month(link.get_text(strip=True)),
                    )
                )
            url = self._next_page_url(soup)
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).
        """
        return select_month_documents(
            self.list_documents(), month, secondary_source="texte du lien"
        )
