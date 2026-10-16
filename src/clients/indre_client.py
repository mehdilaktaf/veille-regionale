"""Client HTTP pour le RAA de l'Indre."""

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

class IndreRaaClient(AnnualPageRaaClient):
    """
    Client pour le RAA de l'Indre.
    Structure : Page section -> Page annuelle -> Pages mensuelles -> PDF.
    """

    def __init__(self, base_url, timeout=60):
        # La page section contient des cartes "2026", "2025", etc.
        super().__init__(base_url, card_needle="2026", timeout=timeout)

    def list_documents(self):
        """
        Collecte tous les documents de l'année en traversant les pages de mois
        et en gérant la pagination.
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(f"Page annuelle introuvable sur {self.base_url}")

        logger.warning("INDRE: Visite de la page annuelle : %s", self.annual_page_url)
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        
        month_links = []
        months_keywords = ["janvier", "fevrier", "mars", "avril", "mai", "juin", 
                           "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
        
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            href = link["href"].lower()
            if any(m in text or m in href for m in months_keywords):
                if "/202" in href and any(m in text for m in months_keywords):
                    full_url = urljoin(self.base_url, link["href"])
                    logger.warning("INDRE: Lien de mois détecté : %s (texte: %s)", full_url, text)
                    month_links.append(full_url)

        month_links = list(set(month_links))
        logger.warning("INDRE: Nombre total de liens de mois trouvés : %d", len(month_links))

        if not month_links:
            logger.warning("INDRE: Aucun lien de mois trouvé, recherche directe sur la page annuelle.")
            return self._collect_from_soup(soup)

        all_documents = []
        for month_url in month_links:
            try:
                current_url = month_url
                while current_url:
                    logger.warning("INDRE: Visite de la page mois : %s", current_url)
                    month_soup = BeautifulSoup(self._get(current_url).text, "html.parser")
                    docs = self._collect_from_soup(month_soup)
                    logger.warning("INDRE: Documents trouvés sur cette page : %d", len(docs))
                    all_documents.extend(docs)
                    
                    next_link = month_soup.find("a", string=lambda s: s and "Suivant" in s)
                    current_url = urljoin(self.base_url, next_link["href"]) if (next_link and next_link.has_attr("href")) else None
            except RaaError as e:
                logger.warning("INDRE: Erreur lors de la visite de la page mois %s : %s", month_url, e)

        return dedupe_documents(all_documents)

    def _collect_from_soup(self, soup, target_month=None):
        """Collecte les documents PDF depuis un soup donné."""
        documents = []
        # Sélecteur large : tous les liens dont l'href finit par .pdf
        links = soup.find_all("a", href=True)
        pdf_links = [l for l in links if l["href"].lower().endswith(".pdf")]
        
        logger.warning("INDRE: Nombre de liens PDF détectés : %d / %d liens totaux", len(pdf_links), len(links))
        
        for link in pdf_links:
            href = link["href"]
            name = unquote_plus(href.split("/")[-1])
            
            # Date CMS : span.fr-link__detail ou attribut title
            cms_date = link_day_month(link)
            if cms_date is None:
                title = link.get("title")
                if title:
                    from src.raa_client import parse_day_month
                    cms_date = parse_day_month(title)
            
            # Date secondaire : texte du lien (source de vérité pour l'Indre)
            secondary_date = relaxed_day_month(link.get_text(strip=True))
            
            # On force le mois de la page si on est en mode optimisé et que le CMS dérive
            if target_month:
                cms_date = (None, int(target_month))
            elif cms_date is None and secondary_date is None:
                # Fallback classique
                pass
            
            logger.warning("INDRE: Doc: %s | CMS: %s | Sec: %s", name, cms_date, secondary_date)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_date,
                    secondary_date,
                )
            )
        return documents

    def documents_for_month(self, month):
        """
        Optimisation : ne visite que la page du mois cible et gère la pagination.
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(f"Page annuelle introuvable sur {self.base_url}")

        logger.warning("INDRE: Recherche du mois %s sur la page annuelle %s", month, self.annual_page_url)
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
                logger.warning("INDRE: Page mensuelle trouvée : %s", month_url)
                break
        
        if not month_url:
            logger.warning("INDRE: Aucune page trouvée pour le mois %s.", month)
            return []

        try:
            all_docs = []
            current_url = month_url
            while current_url:
                logger.warning("INDRE: Visite de la page mois (optimisée) : %s", current_url)
                month_soup = BeautifulSoup(self._get(current_url).text, "html.parser")
                docs = self._collect_from_soup(month_soup, target_month=month)
                logger.warning("INDRE: Documents trouvés sur cette page : %d", len(docs))
                all_docs.extend(docs)
                
                next_link = month_soup.find("a", string=lambda s: s and "Suivant" in s)
                current_url = urljoin(self.base_url, next_link["href"]) if (next_link and next_link.has_attr("href")) else None
                
            return select_month_documents(all_docs, month, secondary_source="texte du lien")
        except RaaError as e:
            logger.error("INDRE: Erreur lors de la récupération du mois %s : %s", month, e)
            return []
