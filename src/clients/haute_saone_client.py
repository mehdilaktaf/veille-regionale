"""Client HTTP (sans navigateur) du RAA de la Haute-Saône.

Trois niveaux :
- la page section (…/Publications/RAA) liste les documents
  (« RAA 70-2026-172 publié le 18 septembre 2026 »), paginées ;
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


class HauteSaoneRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Haute-Saône."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def list_documents(self, month):
        """Retourne les RAA dont la carte porte le mois et l'année cibles
        (toutes les pages de pagination) : (url_page_doc, nom, None, None).
        """
        documents = []
        url = self.base_url
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            
            for h2 in soup.select("h2.fr-card__title"):
                link = h2.find("a")
                if not link or not link.get("href"):
                    continue
                
                text = link.get_text(" ", strip=True)
                card_month = month_of_text(text)
                
                # Arrêt précoce : si on dépasse le mois cible (liste décroissante)
                if card_month and str(self.year) in text:
                    if int(card_month) < int(month):
                        url = None
                        break
                
                if card_month != month or str(self.year) not in text:
                    continue
                
                # On ne visite plus la page document ici pour éviter le WAF.
                # On renvoie l'URL de la page document ; download() s'occupera de l'extraction.
                doc_page_url = urljoin(self.base_url, link["href"])
                documents.append(
                    (
                        doc_page_url,
                        text, # Nom provisoire utilisé pour le cache/reprise
                        None,
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
        # On utilise select_month_documents, mais comme on renvoie (url_page, text, None, None),
        # la date CMS est absente. select_month_documents utilisera donc la source secondaire (la carte).
        return select_month_documents(
            self.list_documents(month), month, secondary_source="carte"
        )

    def download(self, url, dest_path, retries=4, backoff=10):
        """Surcharge de download : si l'URL est une page document, on extrait le PDF."""
        if self._is_complete_pdf(dest_path):
            logger.info("Déjà téléchargé (reprise) : %s", dest_path)
            return

        # Si l'URL ne pointe pas vers un PDF, on cherche le lien PDF sur la page
        if not url.lower().endswith(".pdf") and "/contenu/telechargement/" not in url:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            download_link = soup.select_one(DOWNLOAD_LINK_SELECTOR)
            if not download_link or not download_link.get("href"):
                raise RaaError(f"Lien PDF introuvable sur la page : {url}")
            url = urljoin(self.base_url, download_link["href"])

        super().download(url, dest_path, retries, backoff)

