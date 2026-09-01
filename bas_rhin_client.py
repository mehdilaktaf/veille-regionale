"""Client HTTP (sans navigateur) du RAA du Bas-Rhin.

Deux niveaux :
- la page section (…/Publications-officielles/
  RAA-Recueils-des-actes-administratifs) porte des cartes « RAA ANNEE
  YYYY » (majuscules sans accent, 2026 → 2017) ;
- la page annuelle porte **un select par mois**, tous nommés
  « Liste-liste-docs » (1 option par document, libellés « RAA N° X du
  D mois YYYY ») : le POST d'une option vers la même page génère le lien
  de téléchargement (a.fr-link--download + span.fr-link__detail CMS,
  source de vérité), pattern Vendée/Marne. La liste de l'année est l'union
  des options de tous les selects ; le mois fait d'abord foi sur le
  dossier mensuel de la valeur (« Media/Files/22.-RAA/2026/Fevrier/... »),
  le libellé (ancré « du ») en contrôle ; les options sans mois détectable
  sont vérifiées au POST (« balayeur »).
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
from unidecode import unidecode

from raa_client import (
    MONTHS_FR,
    RaaError,
    RaaHttpClient,
    du_day_month,
    find_annual_href,
    link_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

SELECT_NAME = "Liste-liste-docs"


class BasRhinRaaClient(RaaHttpClient):
    """Client HTTP du RAA du Bas-Rhin."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = int(year)
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        href = find_annual_href(soup, f"RAA année {self.year}")
        if href is None:
            return None
        return urljoin(self.base_url, href)

    def _post_download_url(self, value):
        """POST l'option vers la page annuelle ; retourne
        (url_pdf, jour_mois_cms)."""
        response = self._post(
            self.annual_page_url, data={SELECT_NAME: value}
        )
        soup = BeautifulSoup(response.text, "html.parser")
        link = soup.select_one("div.liste_deroulante a.fr-link--download")
        if link is None:
            link = soup.select_one("a.fr-link--download")
        if link is None or not link.get("href"):
            raise RaaError(f"Lien de téléchargement introuvable pour {value}")
        return urljoin(self.annual_page_url, link["href"]), link_day_month(link)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).

        Union des options de tous les selects mensuels ; le mois de la
        valeur (dossier mensuel) pré-filtre, le mois faisant foi est celui
        du panneau de téléchargement (CMS). Les options sans mois
        détectable sont aussi vérifiées (« balayeur »).
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle {self.year} introuvable sur {self.base_url}"
                )
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        selects = soup.select(f"select[name='{SELECT_NAME}']")
        if not selects:
            raise RaaError(
                f"Select « {SELECT_NAME} » introuvable sur {self.annual_page_url}"
            )
        documents = []
        seen = set()
        for select in selects:
            for option in select.find_all("option"):
                value = (option.get("value") or "").strip()
                if not value or value in seen:
                    continue
                seen.add(value)
                label = option.get("title") or option.get_text(strip=True)
                hint = _option_month(value, label)
                if hint is None:
                    logger.info("Option sans mois détectable, vérification : %s", label)
                elif hint != month:
                    continue
                url, cms_day_month = self._post_download_url(value)
                name = unquote(url.split("/")[-1])
                documents.append(
                    (url, name, cms_day_month, du_day_month(label))
                )
        return select_month_documents(
            documents, month, secondary_source="libellé du menu"
        )


def _option_month(value, label):
    """Mois (« MM ») d'une option : d'abord le dossier mensuel de la valeur
    (« .../2026/Fevrier/... »), puis la date du libellé. None si aucune."""
    for part in value.split("/"):
        part = unidecode(part).strip().lower()
        if part in MONTHS_FR:
            return MONTHS_FR[part]
    day_month = du_day_month(label)
    if day_month is not None:
        return f"{day_month[1]:02d}"
    return None
