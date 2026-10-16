"""Client HTTP pour le RAA d'Eure-et-Loir."""

import logging
from urllib.parse import urljoin, unquote_plus
from bs4 import BeautifulSoup

from src.raa_client import (
    AnnualPageRaaClient,
    RaaError,
    DOWNLOAD_LINK_SELECTOR,
    link_day_month,
    relaxed_day_month,
    dedupe_documents,
    select_month_documents,
)

logger = logging.getLogger(__name__)

class EureEtLoirRaaClient(AnnualPageRaaClient):
    """
    Client pour le RAA d'Eure-et-Loir.
    Structure : Page section -> Page annuelle -> Pages mensuelles -> PDF.
    """

    def __init__(self, base_url, timeout=60):
        # La page section contient des cartes "2026", "2025", etc.
        super().__init__(base_url, card_needle="2026", timeout=timeout)

    def list_documents(self):
        """
        Collecte tous les documents de l'année en traversant les pages de mois.
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(f"Page annuelle introuvable sur {self.base_url}")

        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        
        # On cherche les liens vers les mois (Janvier, Février...)
        month_links = []
        months_keywords = ["janvier", "fevrier", "mars", "avril", "mai", "juin", 
                           "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
        
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            href = link["href"].lower()
            if any(m in text or m in href for m in months_keywords):
                if "/202" in href and any(m in text for m in months_keywords):
                    month_links.append(urljoin(self.base_url, link["href"]))

        month_links = list(set(month_links))

        if not month_links:
            logger.info("Aucun lien de mois trouvé, recherche directe sur la page annuelle.")
            return self._collect_from_soup(soup)

        all_documents = []
        for month_url in month_links:
            try:
                month_soup = BeautifulSoup(self._get(month_url).text, "html.parser")
                all_documents.extend(self._collect_from_soup(month_soup))
            except RaaError as e:
                logger.warning("Erreur lors de la visite de la page mois %s : %s", month_url, e)

        return dedupe_documents(all_documents)

    def _collect_from_soup(self, soup):
        """Collecte les documents PDF depuis un soup donné."""
        documents = []
        for link in soup.select(DOWNLOAD_LINK_SELECTOR):
            href = link.get("href")
            if not href:
                continue
            
            name = unquote_plus(href.split("/")[-1])
            
            # Extraction de la date CMS : on regarde d'abord le span, puis l'attribut title
            cms_date = link_day_month(link)
            if cms_date is None:
                title = link.get("title")
                if title:
                    from src.raa_client import parse_day_month
                    cms_date = parse_day_month(title)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_date,
                    relaxed_day_month(name),
                )
            )
        return documents

    def documents_for_month(self, month):
        """
        Optimisation : ne visite que la page du mois cible.
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(f"Page annuelle introuvable sur {self.base_url}")

        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        
        target_month_name = {
            "01": "janvier", "02": "fevrier", "03": "mars", "04": "avril",
            "05": "mai", "06": "juin", "07": "juillet", "08": "aout",
            "09": "septembre", "10": "octobre", "11": "novembre", "12": "decembre"
        }.get(month, "").lower()

        month_url = None
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            href = link["href"].lower()
            if target_month_name in text or target_month_name in href:
                month_url = urljoin(self.base_url, link["href"])
                break
        
        if not month_url:
            logger.info("Aucune page trouvée pour le mois %s.", month)
            return []

        try:
            month_soup = BeautifulSoup(self._get(month_url).text, "html.parser")
            docs = self._collect_from_soup(month_soup)
            return select_month_documents(docs, month, secondary_source="texte du lien")
        except RaaError as e:
            logger.error("Erreur lors de la récupération du mois %s : %s", month, e)
            return []
