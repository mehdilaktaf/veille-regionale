"""Client HTTP (sans navigateur) du RAA de la Marne.

Deux flows (selon l'année) :

Années 2025-2026 (flow menu, pattern Vendée) : la page annuelle
(…/RAA-Annee-YYYY) porte **un select par mois** (le select du premier
mois est placé en tête de page, à double tiret
« Liste-des-RAA--liste-docs », les autres à tiret simple
« Liste-des-RAA-liste-docs ») — il n'y a pas de select global, la liste
de l'année est l'union des options de tous les selects. Le POST d'une
option vers la même page, avec le champ mensuel (nom du dernier select),
génère le lien de téléchargement (a.fr-link--download +
span.fr-link__detail CMS, source de vérité). Le mois de chaque option est
codé dans la valeur (« Media/Files/Prefecture/RAA/2026/Fevrier/... ») et
confirmé par le libellé (« RAA n°51-2026-040 du 27 février 2026 ») ; le
nom de fichier généré (« recueil-51-2026-040-... ») ne porte aucune date.

Années 2013-2024 (flow pages documents) : la page section porte la carte
« 2024 » directement et, pour 2013-2023, des cartes de groupes
(« Années 2021 à 2023 ») menant aux cartes « RAA Année YYYY » (coquille
réelle : « RAA  Année 2022 » à double espace). La page annuelle est un
tableau de liens vers des pages documents (« Recueil n°2-1 du 1er
février 2024 ») ; chaque page document porte 1 lien a.fr-link--download
+ span CMS (source de vérité) ; le libellé sert de pré-filtre et de
contrôle (un doc « du 31 janvier » publié le 03/02 peut être manqué —
documenté au catalogue).
"""

import logging
import re
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
from unidecode import unidecode

from raa_client import (
    DOWNLOAD_LINK_SELECTOR,
    MONTHS_FR,
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    du_day_month,
    find_annual_href,
    link_day_month,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

# Cartes de groupes : « Années 2021 à 2023 ».
_YEAR_RANGE = re.compile(r"(\d{4})\s*(?:à|-)\s*(\d{4})")


class MarneRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Marne."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = int(year)
        self.annual_page_url = None

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        href = find_annual_href(soup, f"RAA Année {self.year}")
        if href is None:
            # Carte à texte exact (ex. « 2024 ») : pas de match partiel,
            # « Années 2013 à 2016 » contenant « 2016 ».
            for h2 in soup.select("h2.fr-card__title"):
                link = h2.find("a")
                if (
                    link
                    and link.get("href")
                    and link.get_text(strip=True) == str(self.year)
                ):
                    href = link["href"]
                    break
        if href is not None:
            return urljoin(self.base_url, href)
        # Sinon : la carte de groupe dont la plage couvre l'année.
        for h2 in soup.select("h2.fr-card__title"):
            link = h2.find("a")
            if not link or not link.get("href"):
                continue
            match = _YEAR_RANGE.search(link.get_text(" ", strip=True))
            if not match:
                continue
            if int(match.group(1)) <= self.year <= int(match.group(2)):
                group_url = urljoin(self.base_url, link["href"])
                group_soup = BeautifulSoup(self._get(group_url).text, "html.parser")
                group_href = find_annual_href(group_soup, f"RAA Année {self.year}")
                if group_href is not None:
                    return urljoin(group_url, group_href)
        return None

    # ------------------------------------------------------------------
    # Flow menu (années récentes)
    # ------------------------------------------------------------------

    @staticmethod
    def _menu_options(soup):
        """Options de TOUS les selects de la page (un par mois, dont le
        premier placé en tête de page), dédoublonnées par value :
        (value, label, mois hint)."""
        documents = {}
        for select in soup.select("select"):
            for option in select.find_all("option"):
                value = (option.get("value") or "").strip()
                if not value or value in documents:
                    continue
                label = option.get("title") or option.get_text(strip=True)
                documents[value] = (value, label, _option_month(value, label))
        return list(documents.values())

    def _post_download_url(self, field, value):
        """POST l'option vers la page annuelle ; retourne
        (url_pdf, jour_mois_cms)."""
        response = self._post(self.annual_page_url, data={field: value})
        soup = BeautifulSoup(response.text, "html.parser")
        link = soup.select_one("div.liste_deroulante a.fr-link--download")
        if link is None:
            link = soup.select_one("a.fr-link--download")
        if link is None or not link.get("href"):
            raise RaaError(f"Lien de téléchargement introuvable pour {value}")
        return urljoin(self.base_url, link["href"]), link_day_month(link)

    def _menu_documents_for_month(self, soup, month):
        """Flow menu : pré-filtre sur les options, POST des candidats,
        mois CMS faisant foi."""
        selects = soup.select("select[name]")
        if not selects:
            raise RaaError(f"Select introuvable sur {self.annual_page_url}")
        # Champ du POST : le dernier select (les selects mensuels, à
        # tiret simple « Liste-des-RAA-liste-docs », suivent le select du
        # premier mois à double tiret — c'est ce nom qui est validé).
        field = selects[-1].get("name")
        options = self._menu_options(soup)
        candidates = [(v, l) for v, l, m in options if m == month]
        sweep = [(v, l) for v, l, m in options if m is None]
        for _, label in sweep:
            logger.info("Option sans mois détectable, vérification : %s", label)
        documents = []
        for value, label in candidates + sweep:
            url, day_month = self._post_download_url(field, value)
            name = unquote(url.split("/")[-1])
            documents.append((url, name, day_month, du_day_month(label)))
        return select_month_documents(
            documents, month, secondary_source="libellé du menu"
        )

    # ------------------------------------------------------------------
    # Flow pages documents (années anciennes)
    # ------------------------------------------------------------------

    def _table_documents_for_month(self, soup, month):
        """Flow tableau : pré-filtre sur le libellé des liens, GET des
        pages documents, mois CMS faisant foi."""
        candidates = []
        for link in soup.select("a[href]"):
            href = link.get("href") or ""
            if href.endswith(".pdf") or "telechargement" in href:
                continue
            label = link.get_text(" ", strip=True)
            # Date ancrée sur « du » : un parsing libre lirait le numéro
            # (« Recueil n°2-1 » → 02/01).
            day_month = du_day_month(label)
            if day_month is None:
                continue
            candidates.append((href, label, day_month))
        documents = []
        for href, label, day_month in candidates:
            if f"{day_month[1]:02d}" != month:
                continue  # pré-filtre (le CMS fera foi ensuite)
            page = BeautifulSoup(
                self._get(urljoin(self.base_url, href)).text, "html.parser"
            )
            for download in page.select(DOWNLOAD_LINK_SELECTOR):
                url = download.get("href")
                if not url:
                    continue
                name = unquote(url.split("/")[-1])
                documents.append(
                    (
                        urljoin(self.base_url, url),
                        name,
                        link_day_month(download),
                        day_month,
                    )
                )
        return select_month_documents(
            dedupe_documents(documents), month, secondary_source="libellé"
        )

    # ------------------------------------------------------------------

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier)."""
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle {self.year} introuvable sur {self.base_url}"
                )
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        if soup.select_one("select"):
            return self._menu_documents_for_month(soup, month)
        return self._table_documents_for_month(soup, month)


def _option_month(value, label):
    """Mois (« MM ») d'une option du menu : d'abord le dossier mensuel de
    la valeur (« .../2026/Fevrier/... »), puis la date du libellé. None si
    aucune."""
    for part in value.split("/"):
        part = unidecode(part).strip().lower()
        if part in MONTHS_FR:
            return MONTHS_FR[part]
    day_month = du_day_month(label)
    if day_month is not None:
        return f"{day_month[1]:02d}"
    return None
