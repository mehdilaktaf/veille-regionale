"""Client HTTP (sans navigateur) du RAA de l'Yonne.

Deux niveaux :
- la page section (…/Recueil-des-actes-administratifs) porte des liens
  « RAA année YYYY » ou « Année YYYY » ;
- la page annuelle (…/RAA-annee-YYYY) liste les documents avec liens directs
  vers le PDF et le span.fr-link__detail généré par le CMS (source de vérité).
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


class YonneRaaClient(RaaHttpClient):
    """Client HTTP du RAA de l'Yonne."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        # Recherche flexible : on cherche un lien contenant "RAA" ou "Année" et l'année
        for a in soup.select("a"):
            text = a.get_text(strip=True).lower()
            if ("raa" in text or "année" in text) and str(self.year) in text:
                url = urljoin(self.base_url, a["href"])
                logger.info("Page annuelle trouvée : %s", url)
                return url
        return None

    def list_documents(self, month):
        """Retourne les RAA du mois cible (toutes les pages de pagination) :
        (url_pdf, nom, None, date).
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
            
            for a in soup.select("a.fr-link--download"):
                detail = a.select_one("span.fr-link__detail")
                detail_text = detail.get_text(strip=True) if detail else ""
                
                # On récupère le texte brut du lien pour le nom
                full_text = a.get_text(" ", strip=True)
                # On tente de nettoyer le nom en retirant le détail du PDF
                text = full_text.replace(detail_text, "").strip()
                if not text:
                    text = "Document RAA"
                
                # Extraction de la date CMS : on nettoie le texte pour faciliter le regex
                # (ex: "PDF - 1,2 Mb - 18/09/2026" -> "18/09/2026")
                date_cms = None
                if detail_text:
                    # On ne garde que la partie après le dernier tiret si présent
                    parts = detail_text.split(" - ")
                    clean_date_text = parts[-1].strip() if len(parts) > 1 else detail_text
                    date_cms = parse_day_month(clean_date_text) or relaxed_day_month(clean_date_text)
                
                # Détection du mois pour l'arrêt précoce
                card_month = month_of_text(text) or (date_cms[0] if date_cms else None)
                
                if card_month and str(self.year) in text:
                    if int(card_month) < int(month):
                        url = None
                        break
                
                pdf_url = urljoin(self.base_url, a["href"])
                documents.append(
                    (
                        pdf_url,
                        text,
                        date_cms,
                        None,
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
            self.list_documents(month), month, secondary_source="cms"
        )

    def download(self, url, dest_path, retries=4, backoff=10):
        """Téléchargement direct du PDF."""
        super().download(url, dest_path, retries, backoff)

