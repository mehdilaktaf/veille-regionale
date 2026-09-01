"""Client HTTP (sans navigateur) du RAA de Mayotte.

Trois niveaux :
- la page annuelle (…/RAA-YYYY) porte des cartes « MOIS YYYY »
  (h2.fr-card__title, majuscules, année parfois absente : « FÉVRIER »,
  accents variables) ;
- la page de mois liste des cartes documents (« n°001 du 05 janvier
  2026 »), paginées par 10 (« (offset)/10 ») ;
- la page d'un document porte le lien a.fr-link--download, avec le
  span.fr-link__detail généré par le CMS (source de vérité pour la
  date). Le texte de la carte sert de contrôle croisé.
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from raa_client import (
    MONTH_NAMES_FR,
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    du_day_month,
    link_day_month,
    select_month_documents,
)
from unidecode import unidecode

logger = logging.getLogger(__name__)


class MayotteRaaClient(RaaHttpClient):
    """Client HTTP du RAA de Mayotte."""

    def _month_page_url(self, month):
        """Retourne l'URL absolue de la page du mois (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        wanted = unidecode(MONTH_NAMES_FR[month]).lower()
        for h2 in soup.select("h2.fr-card__title"):
            link = h2.find("a")
            if (
                link
                and link.get("href")
                and wanted in unidecode(link.get_text(strip=True)).lower()
            ):
                return urljoin(self.base_url, link["href"])
        return None

    def list_documents(self, month):
        """Retourne les documents de la page du mois : (url, nom,
        jour_mois_cms, jour_mois_carte)."""
        url = self._month_page_url(month)
        if url is None:
            raise RaaError(
                f"Carte du mois introuvable sur {self.base_url}"
            )
        documents = []
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            for h2 in soup.select("h2.fr-card__title"):
                link = h2.find("a")
                if not link or not link.get("href"):
                    continue
                card_day_month = du_day_month(link.get_text(strip=True))
                page = BeautifulSoup(
                    self._get(urljoin(self.base_url, link["href"])).text,
                    "html.parser",
                )
                for download in page.select("a.fr-link.fr-link--download"):
                    href = download.get("href")
                    if not href:
                        continue
                    documents.append(
                        (
                            urljoin(self.base_url, href),
                            unquote(href.split("/")[-1]),
                            link_day_month(download),
                            card_day_month,
                        )
                    )
            next_url = None
            for link in soup.select("ul.fr-pagination__list li a"):
                if link.get_text(strip=True) == "Suivant" and link.get("href"):
                    next_url = urljoin(self.base_url, link["href"])
            url = next_url
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier)."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="texte de la carte"
        )
