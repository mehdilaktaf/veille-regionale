"""Client HTTP (sans navigateur) du RAA de l'Eure.

Trois niveaux (pattern Aisne) :
- la page section (…/Recueil-des-actes-administratifs-RAA) porte des cartes
  « RAA YYYY » (2026→2015, pas de carte « Archives » visible) ;
- la page annuelle (…/RAA-YYYY) liste les cartes documents
  (« Recueil spécial N°27-2026-261 du 01 septembre 2026 »), paginées par 10
  (≈ 25 pages en 2026) ;
- la page d'une carte porte 1 lien a.fr-link--download avec le
  span.fr-link__detail généré par le CMS (source de vérité) ; le nom de
  fichier porte la date (« du 01 septembre 2026 ») en source secondaire.

Le mois de la carte (date ancrée « du ») sert de pré-filtre avant de
visiter la page document : les cartes à mois non détectable (typos du site
comme « oaût ») sont quand même visitées (« balayeur »), le mois CMS
faisant foi. Si la page annuelle ne porte aucune carte (années anciennes
éventuelles), les liens directs y sont collectés.
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from src.raa_client import (
    DOWNLOAD_LINK_SELECTOR,
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    du_day_month,
    du_month,
    find_annual_href,
    link_day_month,
    month_of_text,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class EureRaaClient(RaaHttpClient):
    """Client HTTP du RAA de l'Eure."""

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

    @staticmethod
    def _card_month(text):
        """Mois (« MM ») de la carte : date ancrée « du » d'abord, puis tout
        mois en lettres. None si non détectable (typos du site, ex.
        « du 14 oaût 2026 »)."""
        return du_month(text) or month_of_text(text)

    def list_documents(self, month):
        """Retourne les RAA dont la carte porte le mois cible — ou dont le
        mois est non détectable (balayeur) — toutes pages de pagination :
        (url, nom, jour_mois_cms, jour_mois_nom)."""
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
            cards = [
                link
                for h2 in soup.select("h2.fr-card__title")
                for link in [h2.find("a")]
                if link is not None and link.get("href")
            ]
            if not cards:
                # Années anciennes éventuelles : liens directs sur la page
                # annuelle (pas de cartes).
                for link in soup.select(DOWNLOAD_LINK_SELECTOR):
                    href = link.get("href")
                    if not href:
                        continue
                    name = unquote(href.split("/")[-1])
                    documents.append(
                        (
                            urljoin(self.base_url, href),
                            name,
                            link_day_month(link),
                            du_day_month(name) or relaxed_day_month(name),
                        )
                    )
            else:
                for link in cards:
                    text = link.get_text(" ", strip=True)
                    card_month = self._card_month(text)
                    if card_month is not None and card_month != month:
                        continue  # autre mois : la page doc n'est pas visitée
                    page = BeautifulSoup(
                        self._get(urljoin(self.base_url, link["href"])).text,
                        "html.parser",
                    )
                    for download in page.select(DOWNLOAD_LINK_SELECTOR):
                        href = download.get("href")
                        if not href:
                            continue
                        name = unquote(href.split("/")[-1])
                        documents.append(
                            (
                                urljoin(self.base_url, href),
                                name,
                                link_day_month(download),
                                du_day_month(name) or relaxed_day_month(name),
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
            self.list_documents(month), month, secondary_source="nom de fichier"
        )
