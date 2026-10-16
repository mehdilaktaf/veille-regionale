"""Client HTTP pour le RAA de l'Indre-et-Loire."""

import logging
from urllib.parse import urljoin, unquote_plus
from bs4 import BeautifulSoup

from src.raa_client import (
    AnnualPageRaaClient,
    RaaError,
    link_day_month,
    relaxed_day_month,
    dedupe_documents,
    select_month_documents,
)

logger = logging.getLogger(__name__)

class IndreEtLoireRaaClient(AnnualPageRaaClient):
    """
    Client pour le RAA de l'Indre-et-Loire.
    Structure : Page section -> Page annuelle listant tous les PDF de l'année.
    """

    def __init__(self, base_url, timeout=60):
        # La page section contient des liens "Année : 2026", etc.
        super().__init__(base_url, card_needle="Année : 2026", timeout=timeout)

    def list_documents(self):
        """
        Collecte tous les documents de la page annuelle.
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(f"Page annuelle introuvable sur {self.base_url}")

        logger.warning("IDL: Visite de la page annuelle : %s", self.annual_page_url)
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        docs = self._collect_from_soup(soup)
        logger.warning("IDL: Nombre total de documents collectés : %d", len(docs))
        return docs

    def _collect_from_soup(self, soup):
        """Collecte les documents PDF depuis un soup donné."""
        documents = []
        links = soup.find_all("a", href=True)
        pdf_links = [l for l in links if l["href"].lower().endswith(".pdf")]
        
        logger.warning("IDL: Nombre de liens PDF détectés : %d / %d liens totaux", len(pdf_links), len(links))
        
        for link in pdf_links:
            href = link["href"]
            name = unquote_plus(href.split("/")[-1])
            
            cms_date = link_day_month(link)
            if cms_date is None:
                title = link.get("title")
                if title:
                    from src.raa_client import parse_day_month
                    cms_date = parse_day_month(title)
            
            secondary_date = relaxed_day_month(link.get_text(strip=True))
            
            logger.warning("IDL: Doc: %s | CMS: %s | Sec: %s", name, cms_date, secondary_date)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_date,
                    secondary_date,
                )
            )
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """
        Filtre les documents de la page annuelle pour le mois cible.
        """
        logger.warning("IDL: Recherche du mois %s", month)
        docs = self.list_documents()
        results = select_month_documents(docs, month, secondary_source="texte du lien")
        logger.warning("IDL: Documents filtrés pour le mois %s : %d", month, len(results))
        return results
