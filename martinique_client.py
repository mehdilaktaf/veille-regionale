"""Client HTTP (sans navigateur) du RAA de la Martinique.

La page publications porte une carte « RAA YYYY » (années récentes) ;
les années antérieures sont sous la carte « Archives » (cartes
« RAAP YYYY » ou « R.A.A.P YYYY »). La page annuelle n liste pas les
liens directement : elle porte des sous-cartes (RAA + éditions
spéciales), chacune menant à une page de liens a.fr-link--download,
chacun portant le span.fr-link__detail généré par le CMS (source de
vérité pour la date).
"""

from bs4 import BeautifulSoup

from raa_client import (
    AnnualPageRaaClient,
    RaaError,
    dedupe_documents,
    du_day_month,
    find_annual_href,
    link_day_month,
)
from urllib.parse import unquote, urljoin


class MartiniqueRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA de la Martinique."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, f"RAA {year}", timeout)
        self.year = year

    def _needles(self):
        return (f"RAA {self.year}", f"RAAP {self.year}", f"R.A.A.P {self.year}")

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None).

        Cherche d'abord sur la page publications, puis sous la carte
        « Archives » (années antérieures).
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        for needle in self._needles():
            href = find_annual_href(soup, needle)
            if href is not None:
                return urljoin(self.base_url, href)
        href = find_annual_href(soup, "Archives")
        if href is not None:
            archives_soup = BeautifulSoup(
                self._get(urljoin(self.base_url, href)).text, "html.parser"
            )
            for needle in self._needles():
                href = find_annual_href(archives_soup, needle)
                if href is not None:
                    return urljoin(self.base_url, href)
        return None

    def list_documents(self):
        """Retourne les documents de l'année : (url, nom, jour_mois_cms,
        jour_mois_secondaire), collectés sur toutes les sous-pages de la
        page annuelle et dédoublonnés par nom de fichier."""
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle {self.year} introuvable sur {self.base_url}"
                )
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        sub_hrefs = [
            link["href"]
            for h2 in soup.select("h2.fr-card__title")
            for link in [h2.find("a")]
            if link is not None and link.get("href")
        ]
        if not sub_hrefs:
            sub_hrefs = [self.annual_page_url]
        documents = []
        for href in sub_hrefs:
            sub_soup = BeautifulSoup(
                self._get(urljoin(self.base_url, href)).text, "html.parser"
            )
            for link in sub_soup.select("a.fr-link.fr-link--download"):
                link_href = link.get("href")
                if not link_href:
                    continue
                documents.append(
                    (
                        urljoin(self.base_url, link_href),
                        unquote(link_href.split("/")[-1]),
                        link_day_month(link),
                        du_day_month(link.get_text(strip=True)),
                    )
                )
        return dedupe_documents(documents)
