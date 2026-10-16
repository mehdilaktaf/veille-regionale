"""Client HTTP (sans navigateur) du RAA du Lot.

Trois niveaux :
- la page section (…/Recueil-des-Actes-Administratifs) porte des cartes
  « RAA YYYY » ;
- la page annuelle (…/RAA-YYYY) liste les documents, paginés (offset/10) ;
  le mois est extrait du texte « Publié le DD/MM/YYYY » suivant le lien ;
- la page d'un document porte le lien a.fr-link--download avec le
  span.fr-link__detail CMS (source de vérité).
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
    parse_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class LotRaaClient(RaaHttpClient):
    """Client HTTP du RAA du Lot."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        href = find_annual_href(soup, f"RAA {self.year}")
        if href is None:
            return None
        return urljoin(self.base_url, href)

    def list_documents(self, month):
        """Retourne les RAA dont la date de publication correspond au mois cible
        (toutes les pages de pagination) : (url, nom, jour_mois_cms, None).
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
            
            # Les liens vers les documents sont dans des h2 (ou similaires) 
            # suivis du texte "Publié le..."
            for link in soup.select("h2 a"):
                href = link.get("href")
                if not href:
                    continue
                
                # On cherche la date dans le texte qui suit le lien
                # Le lien est dans un h2, la date est souvent dans le parent ou le suivant
                text_context = link.find_parent().get_text(" ", strip=True)
                if parse_month(text_context) != month:
                    continue
                
                try:
                    page = BeautifulSoup(
                        self._get(urljoin(self.base_url, href)).text,
                        "html.parser",
                    )
                    for download in page.select(DOWNLOAD_LINK_SELECTOR):
                        d_href = download.get("href")
                        if not d_href:
                            continue
                        documents.append(
                            (
                                urljoin(self.base_url, d_href),
                                unquote(d_href.split("/")[-1]),
                                 link_day_month(download),
                                 None,
                             )
                        )
                except RaaError as e:
                    logger.warning("Erreur lors de la visite du document %s : %s", href, e)

            url = None
            for p_link in soup.select("ul.fr-pagination__list li a"):
                if p_link.get_text(strip=True) == "Suivant" and p_link.get("href"):
                    url = urljoin(self.annual_page_url, p_link["href"])
                    break
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des RAA du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier)."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="date publication"
        )
