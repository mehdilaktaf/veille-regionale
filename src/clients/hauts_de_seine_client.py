"""Client HTTP (sans navigateur) du RAA des Hauts-de-Seine.

Structure :
- page section (Publications/Annonces-avis/Le-Recueil-des-actes-administratifs)
  portant des liens vers les pages annuelles (RAA-YYYY).
- page annuelle listant les documents paginés par 10.
- chaque document est un lien direct vers le PDF avec la date dans l'attribut `title`
  (pattern Aube/Loire-Atlantique).
"""

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


class HautsDeSeineRaaClient(RaaHttpClient):
    """Client HTTP du RAA des Hauts-de-Seine."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        # Le lien est du type "RAA 2026"
        href = find_annual_href(soup, f"RAA {self.year}")
        if href is None:
            return None
        return urljoin(self.base_url, href)

    def _next_page_url(self, soup):
        """Recherche le lien 'Suivant' dans la pagination."""
        for link in soup.select("ul.fr-pagination__list li a"):
            if link.get_text(strip=True) == "Suivant" and link.get("href"):
                return urljoin(self.annual_page_url, link["href"])
        return None

    def list_documents(self, month):
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
            # Les liens sont dans des h2 ou simplement des a avec un title CMS
            for link in soup.find_all("a", href=True):
                # On filtre sur les liens qui pointent vers un PDF et ont un titre formaté CMS
                href = link.get("href")
                if not href or not href.lower().endswith(".pdf"):
                    continue
                
                title = link.get("title") or ""
                # Le titre CMS contient "format pdf - X Mb - JJ/MM/YYYY"
                if "format pdf" not in title.lower():
                    continue
                
                name = unquote(href.split("/")[-1])
                documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        parse_day_month(title),
                        relaxed_day_month(link.get_text(strip=True)),
                    )
                )
            url = self._next_page_url(soup)
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="texte du lien"
        )
