"""Client HTTP (sans navigateur) du RAA de la Saône-et-Loire.

Trois niveaux :
- la page section (…/Recueil-des-actes-administratifs) porte des liens
  « RAA année YYYY » ;
- la page annuelle (…/RAA-annee-YYYY) liste les documents, paginés par 10 ;
- la page d'un document porte 1 lien a.fr-link--download avec le
  span.fr-link__detail généré par le CMS (source de vérité).
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from src.raa_client import (
    DOWNLOAD_LINK_SELECTOR,
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    link_day_month,
    month_of_text,
    parse_day_month,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class SaoneEtLoireRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Saône-et-Loire."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        # Recherche flexible : on cherche un lien contenant "RAA" et l'année
        for a in soup.select("a"):
            text = a.get_text(strip=True).lower()
            if "raa" in text and str(self.year) in text:
                return urljoin(self.base_url, a["href"])
        return None

    def list_documents(self, month):
        """Retourne les RAA dont la carte porte le mois et l'année cibles
        (toutes les pages de pagination) : (url_page_doc, nom, None, None).
        """
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
            
            for h2 in soup.select("h2.fr-card__title"):
                link = h2.find("a")
                if not link or not link.get("href"):
                    continue
                
                text = link.get_text(" ", strip=True)
                
                # Extraction permissive de la date dans le voisinage du h2
                cms_date = None
                # On cherche dans tout le texte du parent pour trouver "Publié le"
                parent_text = h2.parent.get_text(" ", strip=True)
                if "Publié le" in parent_text:
                    from src.raa_client import parse_day_month
                    # On extrait la partie après "Publié le"
                    date_part = parent_text.split("Publié le")[-1].strip()
                    cms_date = parse_day_month(date_part)
                
                doc_page_url = urljoin(self.base_url, link["href"])
                documents.append(
                    (
                        doc_page_url,
                        text,
                        cms_date,
                        parse_day_month(text) or relaxed_day_month(text),
                    )
                )
            
            if url is not None:
                url = None
                for pagination_link in soup.select("ul.fr-pagination__list li a"):
                    if pagination_link.get_text(strip=True) == "Suivant" and pagination_link.get("href"):
                        url = urljoin(self.base_url, pagination_link["href"])
                        break
                    
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des RAA du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).
        """
        return select_month_documents(
            self.list_documents(month), month, secondary_source="carte"
        )

    def download(self, url, dest_path, retries=4, backoff=10):
        """Surcharge de download : si l'URL est une page document, on extrait le PDF."""
        if self._is_complete_pdf(dest_path):
            logger.info("Déjà téléchargé (reprise) : %s", dest_path)
            return

        if not url.lower().endswith(".pdf") and "/contenu/telechargement/" not in url:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            download_link = soup.select_one(DOWNLOAD_LINK_SELECTOR)
            if not download_link or not download_link.get("href"):
                # Repli sur le sélecteur générique si le sélecteur CMS échoue
                download_link = soup.select_one("a[href$='.pdf']")
                if not download_link or not download_link.get("href"):
                    raise RaaError(f"Lien PDF introuvable sur la page : {url}")
            url = urljoin(self.base_url, download_link["href"])

        super().download(url, dest_path, retries, backoff)
