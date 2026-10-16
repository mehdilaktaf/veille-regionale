"""Client HTTP (sans navigateur) du RAA de l'Aisne.

Trois niveaux :
- la page section (…/Recueil-des-Actes-Administratifs) porte des cartes
  « RAA Année YYYY » (2026 → 2010 ; « RAA année 2012 » en minuscule) ;
- la page annuelle (…/RAA-Annee-YYYY) liste les cartes RAA
  (« RAA_Janvier_02-2026-001 »), paginées (≈ 17 pages) ; le mois est
  codé dans le nom de la carte (le 02 est le numéro de département) ;
- la page d'une carte porte 1 lien a.fr-link--download avec le
  span.fr-link__detail généré par le CMS (source de vérité : le nom de
  fichier « recueil-02-2026-NNN-... » ne porte aucune date).

La carte « Sommaire RAA » n'est pas un document.
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from src.raa_client import (
    DOWNLOAD_LINK_SELECTOR,
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    find_annual_href,
    link_day_month,
    month_of_text,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class AisneRaaClient(RaaHttpClient):
    """Client HTTP du RAA de l'Aisne."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        href = find_annual_href(soup, f"RAA Année {self.year}")
        if href is None:
            return None
        return urljoin(self.base_url, href)

    def list_documents(self, month):
        """Retourne les RAA dont la carte porte le mois cible (toutes les
        pages de pagination) : (url, nom, jour_mois_cms, None)."""
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
            for h2 in soup.select("h2.fr-card__title"):
                link = h2.find("a")
                if not link or not link.get("href"):
                    continue
                if month_of_text(link.get_text(" ", strip=True)) != month:
                    continue  # « Sommaire RAA » et autres mois
                page = BeautifulSoup(
                    self._get(urljoin(self.base_url, link["href"])).text,
                    "html.parser",
                )
                for download in page.select(DOWNLOAD_LINK_SELECTOR):
                    href = download.get("href")
                    if not href:
                        continue
                    documents.append(
                        (
                            urljoin(self.base_url, href),
                            unquote(href.split("/")[-1]),
                            link_day_month(download),
                            None,
                        )
                    )
            url = None
            for link in soup.select("ul.fr-pagination__list li a"):
                if link.get_text(strip=True) == "Suivant" and link.get("href"):
                    url = urljoin(self.annual_page_url, link["href"])
                    break
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des RAA du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier)."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="carte"
        )
