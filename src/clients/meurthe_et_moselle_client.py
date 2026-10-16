"""Client HTTP (sans navigateur) du RAA de la Meurthe-et-Moselle.

Deux niveaux :
- la page section (…/Recueils-des-actes-administratifs) porte des cartes
  « Recueils des actes administratifs année YYYY » (2026 → 2017, pas de
  carte archives visible) ;
- la page annuelle porte un select « Liste-liste-docs » (1 option par
  document, « Numéro N du D mois YYYY », placeholder « Liste ») : le POST
  d'une option vers la même page génère le lien de téléchargement
  (a.fr-link--download + span.fr-link__detail CMS, source de vérité),
  pattern Vendée. Le mois du libellé (ancré « du ») pré-filtre avant le
  POST ; les options sans date détectable sont vérifiées au POST
  (« balayeur »).
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from src.raa_client import (
    RaaError,
    RaaHttpClient,
    du_day_month,
    find_annual_href,
    link_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

SELECT_NAME = "Liste-liste-docs"


class MeurtheEtMoselleRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Meurthe-et-Moselle."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = int(year)
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        href = find_annual_href(soup, f"année {self.year}")
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

        Le mois du libellé du menu (ancré « du ») sélectionne les
        candidats ; le mois faisant foi est celui du panneau de
        téléchargement (CMS). Les options sans date sont aussi vérifiées
        (« balayeur »).
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle {self.year} introuvable sur {self.base_url}"
                )
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        select = soup.select_one(f"select[name='{SELECT_NAME}']")
        if select is None:
            raise RaaError(
                f"Select « {SELECT_NAME} » introuvable sur {self.annual_page_url}"
            )
        documents = []
        for option in select.find_all("option"):
            value = (option.get("value") or "").strip()
            if not value:
                continue
            label = option.get("title") or option.get_text(strip=True)
            day_month = du_day_month(label)
            hint = f"{day_month[1]:02d}" if day_month is not None else None
            if hint is None:
                logger.info("Option sans mois détectable, vérification : %s", label)
            elif hint != month:
                continue
            url, cms_day_month = self._post_download_url(value)
            name = unquote(url.split("/")[-1])
            documents.append((url, name, cms_day_month, day_month))
        return select_month_documents(
            documents, month, secondary_source="libellé du menu"
        )
