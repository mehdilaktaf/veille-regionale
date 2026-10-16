"""Client HTTP (sans navigateur) du RAA de la Manche.

Trois niveaux :
- la page section (…/Recueil-des-actes-administratifs) porte des cartes
  années à texte exact « YYYY » (2026→2016, pas de carte « Archives »
  visible ; coquilles de slug : 2021 → /20212, 2020 → /20202 — la
  navigation est par le texte de la carte, jamais par le slug) ;
- la page annuelle (…/2026) liste des cartes mois « N. <Mois> » paginées
  par 10 — le préfixe numérique n'est pas fiable (« 10. » manquant,
  « 11. Septembre »), le mois se repère sur le nom — et des cartes
  non-mois (« 2. Délégations de signatures du Préfet de la Manche ») qui
  portent des RAA aussi absents des cartes mois ;
- la page d'une carte liste des liens a.fr-link plain (2026, sans span
  fr-link__detail) dont le texte porte la date de publication (« PDF -
  0,11 Mb - 05/02/2026 ») ; les noms de fichier ne portent pas de jour
  (« RAA spécial 50-2026-029.pdf », slugs « recueil-50-2026-010-... »),
  sauf le « RAA mensuel <Mois> YYYY 50-YYYY-XXX.pdf » (mois en lettres).

Le mois de la carte mois fait foi : le « RAA mensuel <Mois> » du mois M
est publié le M+1 (le mensuel de février porte 05/03), la date de
publication le classerait le mois suivant. Les cartes non-mois sont
visitées au balayeur : leurs documents sont datés par la date de
publication (le mois faisant foi) et dédoublonnés par nom avec les
cartes mois. Si la page annuelle ne porte aucune carte (années
anciennes éventuelles), les liens y sont collectés directement.
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
    find_annual_href,
    link_day_month,
    month_of_text,
    parse_day_month,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class MancheRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Manche."""

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

    @staticmethod
    def _next_page(soup):
        """Href du lien « Suivant » de la pagination (ou None)."""
        for link in soup.select("ul.fr-pagination__list li a"):
            if link.get_text(strip=True) == "Suivant" and link.get("href"):
                return link["href"]
        return None

    @staticmethod
    def _card_month(text):
        """Mois (« MM ») d'une carte (« 3. Février ») ou None pour une carte
        sans mois (« 2. Délégations de signatures ... »)."""
        return month_of_text(text)

    def _annual_cards(self):
        """(mois_carte, href) des cartes de la page annuelle, toutes pages
        de pagination ; mois_carte = None pour une carte sans mois."""
        cards = []
        url = self.annual_page_url
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            for h2 in soup.select("h2.fr-card__title"):
                link = h2.find("a")
                if link is None or not link.get("href"):
                    continue
                cards.append(
                    (
                        self._card_month(link.get_text(" ", strip=True)),
                        link["href"],
                    )
                )
            next_href = self._next_page(soup)
            url = urljoin(self.annual_page_url, next_href) if next_href else None
        return cards

    def _collect_page(self, url, card_month, documents):
        """Collecte les documents d'une page de carte (et sa pagination) :
        (url, nom, jour_mois_publication, jour_mois_nom, mois_carte)."""
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            for link in soup.select(DOWNLOAD_LINK_SELECTOR):
                href = link.get("href")
                if not href:
                    continue
                name = unquote(href.split("/")[-1])
                # 2026 : pas de span fr-link__detail, la date de publication
                # est dans le texte du lien (« PDF - 0,11 Mb - 05/02/2026 ») ;
                # repli sur le span pour les années à liens --download.
                publication = link_day_month(link) or parse_day_month(
                    link.get_text(" ", strip=True)
                )
                documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        publication,
                        du_day_month(name) or relaxed_day_month(name),
                        card_month,
                    )
                )
            next_href = self._next_page(soup)
            url = urljoin(url, next_href) if next_href else None

    def list_documents(self, month):
        """Retourne les documents du mois (carte du mois + cartes non-mois
        au balayeur), en (url, nom, jour_mois_faisant_foi, jour_mois_nom).

        Le mois de la carte mois fait foi (le « RAA mensuel » du mois M
        est publié le M+1 : publié hors mois → classé en début de mois
        avec warning). Sur une carte non-mois, la date de publication
        fait foi.
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle {self.year} introuvable sur {self.base_url}"
                )
        raw = []
        cards = self._annual_cards()
        month_cards = [href for m, href in cards if m == month]
        other_cards = [href for m, href in cards if m is None]
        if not cards:
            # Années anciennes éventuelles : liens directs sur la page
            # annuelle (sans carte) — la date de publication fait foi.
            self._collect_page(self.annual_page_url, None, raw)
        else:
            for href in month_cards:
                self._collect_page(
                    urljoin(self.annual_page_url, href), month, raw
                )
            for href in other_cards:
                self._collect_page(urljoin(self.annual_page_url, href), None, raw)
        documents = []
        for url, name, publication, name_day_month, card_month in raw:
            if card_month is not None:
                if publication is not None and f"{publication[1]:02d}" != card_month:
                    logger.warning(
                        "Date de publication %02d/%02d hors du mois de la carte "
                        "(%s) : classé en début de mois : %s",
                        publication[0] or 0,
                        publication[1],
                        card_month,
                        name,
                    )
                    day_month = (None, int(card_month))
                elif publication is not None:
                    day_month = publication
                else:
                    if (
                        name_day_month is not None
                        and f"{name_day_month[1]:02d}" == card_month
                    ):
                        day_month = name_day_month
                    else:
                        logger.warning(
                            "Date de publication absente : classé en début de "
                            "mois (mois de la carte) : %s",
                            name,
                        )
                        day_month = (None, int(card_month))
                documents.append((url, name, day_month, name_day_month))
            else:
                if publication is not None:
                    logger.warning(
                        "Document hors carte mois (mois = date de publication, "
                        "non vérifié) : %s",
                        name,
                    )
                documents.append((url, name, publication, name_day_month))
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des RAA du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier)."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="nom de fichier"
        )
