"""Client HTTP (sans navigateur) du RAA du Haut-Rhin.

Deux niveaux :
- la page section (…/Recueil-des-actes-administratifs) porte des cartes
  d'années à **texte exact « YYYY »** (2026 → 1994, archive très
  profonde ; jamais de préfixe « RAA » — la comparaison doit être exacte,
  jamais partiel). La page section peut porter un lien PDF égaré dans une
  carte (« Reccueil n°77 du 10 juillet 2026 » — coquille du site) : il
  est ignoré car sa carte ne porte pas un texte d'année ;
- la page annuelle liste les cartes documents paginées par 10
  (« (offset)/10 ») : chaque carte est un lien direct vers le PDF
  (a.fr-card__link.menu-item-link), sans page document intermédiaire,
  même pattern que l'Aube / la Loire-Atlantique.

La date fait foi sur l'attribut title de la carte, généré par le CMS
(« format pdf - 1,02 Mb - 31/08/2026 ») ; le texte de la carte
(« Recueil n°100 du 31 août 2026 ») sert de contrôle. Toutes les pages
de l'année sont balayées (les mois sont mêlés sur la même pagination).
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from src.raa_client import (
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    parse_day_month,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class HautRhinRaaClient(RaaHttpClient):
    """Client HTTP du RAA du Haut-Rhin."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = int(year)
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None).

        Les cartes d'années portent un texte exact (« 2026 ») : jamais de
        match partiel (une carte « RAA 2026 » d'un autre dépt ou un texte
        contenant l'année ne doit pas matcher).
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        for h2 in soup.select("h2.fr-card__title"):
            link = h2.find("a")
            if (
                link
                and link.get("href")
                and link.get_text(strip=True) == str(self.year)
            ):
                return urljoin(self.base_url, link["href"])
        return None

    def _next_page_url(self, soup):
        for link in soup.select("ul.fr-pagination__list li a"):
            if link.get_text(strip=True) == "Suivant" and link.get("href"):
                return urljoin(self.annual_page_url, link["href"])
        return None

    def list_documents(self, month):
        """Retourne les documents de l'année (toutes les pages) :
        (url, nom, jour_mois_cms, jour_mois_texte)."""
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
            for link in soup.select("a.fr-card__link.menu-item-link"):
                href = link.get("href")
                if not href or not href.endswith(".pdf"):
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
        croissant : (url_absolue, nom_de_fichier)."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="texte de la carte"
        )
