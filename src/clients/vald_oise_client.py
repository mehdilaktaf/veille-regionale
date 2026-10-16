import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import (
    RaaHttpClient,
    dedupe_documents,
    select_month_documents,
    relaxed_day_month,
    link_day_month,
    DOWNLOAD_LINK_SELECTOR,
)

logger = logging.getLogger(__name__)

class ValdOiseRaaClient(RaaHttpClient):
    """Client pour le RAA du Val-d'Oise.
    
    Structure :
    - Page racine : /Publications/Recueil-des-Actes-Administratifs
    - Page annuelle : /Publications/Recueil-des-Actes-Administratifs/RAA-de-YYYY
    - Page document : /Media/Files/RAAE-n-XXX...
    - PDF : lien sur la page document.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_url = urljoin(base_url + "/", f"RAA-de-{year}")

    def _collect_from_doc_page(self, doc_url):
        """Visite la page du document pour extraire le lien PDF et sa date."""
        try:
            soup = BeautifulSoup(self._get(doc_url).text, "html.parser")
            # On cherche le lien PDF
            pdf_link = None
            for link in soup.find_all("a", href=True):
                if link["href"].lower().endswith(".pdf"):
                    pdf_link = link
                    break
            
            if not pdf_link:
                return None

            href = pdf_link["href"]
            name = unquote(href.split("/")[-1])
            
            # Date source 1 : span CMS
            cms_dm = link_day_month(pdf_link)
            # Date source 2 : texte du lien ou titre
            title = pdf_link.get("title", "")
            text = pdf_link.get_text(strip=True)
            second_dm = relaxed_day_month(title) or relaxed_day_month(text)
            
            return (urljoin(self.base_url, href), name, cms_dm, second_dm)
        except Exception as e:
            logger.warning("Erreur lors de la collecte sur %s : %s", doc_url, e)
            return None

    def list_documents(self):
        soup = BeautifulSoup(self._get(self.annual_url).text, "html.parser")
        
        # Trouver les liens vers les pages de documents (ex: /Media/Files/RAAE-n-...)
        doc_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/Media/Files/" in href:
                doc_links.append((urljoin(self.base_url, href), link.get_text(strip=True)))
        
        documents = []
        for doc_url, text in doc_links:
            res = self._collect_from_doc_page(doc_url)
            if res:
                url, name, cms_dm, second_dm = res
                # On peut enrichir second_dm avec le texte de la page annuelle si besoin
                if second_dm is None:
                    second_dm = relaxed_day_month(text)
                documents.append((url, name, cms_dm, second_dm))
                
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Filtre les documents de la page annuelle pour le mois cible avant de visiter les pages documents."""
        soup = BeautifulSoup(self._get(self.annual_url).text, "html.parser")
        
        from src.raa_client import month_of_text
        doc_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/Media/Files/" in href:
                text = link.get_text(strip=True)
                # Optimisation : on ne visite que les pages du mois demandé
                if month_of_text(text) == month:
                    doc_links.append((urljoin(self.base_url, href), text))
        
        documents = []
        for doc_url, text in doc_links:
            res = self._collect_from_doc_page(doc_url)
            if res:
                url, name, cms_dm, second_dm = res
                if second_dm is None:
                    second_dm = relaxed_day_month(text)
                documents.append((url, name, cms_dm, second_dm))
                
        return select_month_documents(dedupe_documents(documents), month, secondary_source="texte du lien")
