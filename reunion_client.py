"""Client HTTP (sans navigateur) du RAA de La Réunion.

LA REUNION NE PUBLIE PAS DE RECUEIL COMPOSÉ : la page annuelle
(…/Recueil-des-actes-administratifs-YYYY), paginée par 10, liste des
séparateurs de mois (cartes « AOUT » sans date — absents pour le mois
le plus récent) et des cartes RAA (« Spécial n° 169 du 27 août 2026 »),
chacune menant à une page portant les actes individuels du recueil
(a.fr-link--download avec span.fr-link__detail CMS, source de vérité).
Le « fusionné » de La Réunion est donc la fusion des actes du mois.
Le texte de la carte sert de pré-filtre (mois) et de contrôle.
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from raa_client import (
    RaaHttpClient,
    dedupe_documents,
    du_day_month,
    link_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class ReunionRaaClient(RaaHttpClient):
    """Client HTTP du RAA de La Réunion (actes individuels)."""

    def list_documents(self, month):
        """Retourne les actes des RAA dont le mois de carte correspond :
        (url, nom, jour_mois_cms, jour_mois_carte)."""
        documents = []
        url = self.base_url
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            for h2 in soup.select("h2.fr-card__title"):
                link = h2.find("a")
                if not link or not link.get("href"):
                    continue
                card_day_month = du_day_month(link.get_text(strip=True))
                if card_day_month is None:
                    continue  # séparateur de mois
                if f"{card_day_month[1]:02d}" != month:
                    continue
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
        """Retourne les liens des actes du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier)."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="texte de la carte"
        )
