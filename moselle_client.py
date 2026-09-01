"""Client HTTP (sans navigateur) du RAA de la Moselle.

LA MOSELLE PUBLIE SES RAA SUR UN SITE LEGACY (mc.moselle.gouv.fr),
pas sur la plateforme CMS des préfectures :
- recherche par date de publication : POST du formulaire
  « search_recueil » (raa.html?adminedit=1?tab=1&do=exec_search_rec)
  avec bornes 01/MM/AAAA - 31/MM/AAAA, type_acte=0 (normal + spécial) ;
- résultats dans un tableau table.table_list (Type | Référence
  « Numéro 195 » | Date de publication | lien de téléchargement
  docfile_md5id), paginé (« page=N » via le lien « > », critères
  conservés en session) ;
- la date de publication du tableau fait foi (recherche déjà bornée
  au mois cible) ; le nom de fichier est dérivé de la référence, du
  type (« Spécial » / « Normal ») et de la date.

La page www.moselle.gouv.fr/.../Recueil-des-Actes-Administratifs ne
porte qu'une vue partielle (RAA-2024) : le site legacy couvre toutes
les années et fait foi.
"""

import calendar
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from raa_client import (
    RaaHttpClient,
    dedupe_documents,
    parse_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

MC_BASE = "https://mc.moselle.gouv.fr/"
MAX_PAGES = 50


class MoselleRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Moselle (site legacy mc.moselle.gouv.fr)."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    @staticmethod
    def _next_page_url(html):
        """Retourne l'URL absolue de la page suivante (ou None)."""
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a"):
            href = a.get("href") or ""
            if (
                a.get_text(strip=True) == ">"
                and "exec_search_rec" in href
                and "page=" in href
            ):
                return urljoin(MC_BASE, href)
        return None

    def _result_pages(self, month):
        """Retourne le HTML de chaque page de résultats de la recherche
        du mois (POST initial puis GET de pagination)."""
        last_day = calendar.monthrange(int(self.year), int(month))[1]
        payload = {
            "mot_cle": "",
            "date_pub_op": "entre",
            "date_pub": f"01/{month}/{self.year}",
            "date_pub_end": f"{last_day:02d}/{month}/{self.year}",
            "type_acte": "0",
        }
        # La page d'accueil du site legacy établit la session.
        self._get(MC_BASE + "raa.html")
        response = self._post(
            MC_BASE + "raa.html?adminedit=1?tab=1&do=exec_search_rec",
            data=payload,
        )
        pages = []
        html = response.text
        next_url = self._next_page_url(html)
        seen = set()
        while html is not None:
            pages.append(html)
            if next_url is None or next_url in seen or len(pages) >= MAX_PAGES:
                break
            seen.add(next_url)
            html = self._get(next_url).text
            next_url = self._next_page_url(html)
        return pages

    def list_documents(self, month):
        """Retourne les recueils du mois : (url, nom, jour_mois, None).

        jour_mois est la « Date de publication » du tableau (source de
        vérité) ; nom est dérivé de la référence (« Numéro 195 »), du
        type et de la date.
        """
        documents = []
        for html in self._result_pages(month):
            soup = BeautifulSoup(html, "html.parser")
            table = soup.select_one("table.table_list")
            if table is None:
                continue
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue
                link = cells[-1].find("a", href=True)
                if link is None:
                    continue
                ref = cells[1].get_text(" ", strip=True)
                date_text = cells[2].get_text(strip=True)
                day_month = parse_day_month(date_text)
                num_match = re.search(r"numéro\s+(\d+)", ref, re.IGNORECASE)
                if day_month is None or num_match is None:
                    # lignes de pagination / lignes parasites du tableau
                    continue
                doc_type = cells[0].get_text(strip=True) or "Normal"
                num = int(num_match.group(1))
                date_safe = date_text.replace("/", "-")
                name = f"RAA n°{num} du {date_safe} ({doc_type}).pdf"
                documents.append(
                    (urljoin(MC_BASE, link["href"]), name, day_month, None)
                )
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des recueils du mois, en ordre
        chronologique croissant : (url_absolue, nom_de_fichier)."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="référence"
        )
