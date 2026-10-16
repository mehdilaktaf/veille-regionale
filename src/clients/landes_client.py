import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import RaaHttpClient, RaaError, parse_day_month, select_month_documents, dedupe_documents, relaxed_day_month

logger = logging.getLogger(__name__)

class LandesRaaClient(RaaHttpClient):
    """Client HTTP pour le RAA des Landes.
    Structure : Page section -> Page RAA -> Pages annuelles (paginées) -> Pages documents -> Liens PDF.
    
    Optimisation WAF : list_documents ne visite pas les pages de documents.
    L'URL du PDF est résolue au moment du téléchargement.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def _find_annual_url(self):
        """Trouve l'URL de la page annuelle pour l'année ciblée."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        for link in soup.find_all("a", href=True):
            if link.get_text(strip=True) == str(self.year):
                return urljoin(self.base_url, link["href"])
        raise RaaError(f"Page annuelle introuvable pour l'année {self.year} sur {self.base_url}")

    def list_documents(self):
        """Retourne les documents de l'année sans visiter les pages individuelles.
        L'URL retournée est celle de la page du document.
        """
        annual_url = self._find_annual_url()
        documents = []
        current_url = annual_url
        
        while current_url:
            soup = BeautifulSoup(self._get(current_url).text, "html.parser")
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                if "RAA" in text.upper() and "du" in text.lower():
                    name = text # On utilise le texte comme nom provisoire
                    doc_url = urljoin(annual_url, link["href"])
                    
                    # Date extraite du texte du lien
                    cms_day_month = parse_day_month(text)
                    
                    documents.append(
                        (
                            doc_url,
                            name,
                            cms_day_month,
                            relaxed_day_month(text),
                        )
                    )
            
            next_link = None
            for link in soup.find_all("a", href=True):
                if "Suivant" in link.get_text():
                    next_link = urljoin(current_url, link["href"])
                    break
            current_url = next_link
            
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Filtre les documents pour le mois donné."""
        return select_month_documents(self.list_documents(), month, secondary_source="texte du lien")

    def download(self, url, dest_path, retries=4, backoff=10):
        """Résout l'URL du PDF si nécessaire avant de télécharger."""
        if url.endswith(".pdf"):
            return super().download(url, dest_path, retries, backoff)
            
        # On est sur une page de document, on cherche le lien PDF
        soup = BeautifulSoup(self._get(url).text, "html.parser")
        pdf_link = None
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".pdf" in href.lower() and "Télécharger" in link.get_text():
                pdf_link = urljoin(url, href)
                break
        
        if not pdf_link:
            raise RaaError(f"Lien PDF introuvable sur la page {url}")
            
        return super().download(pdf_link, dest_path, retries, backoff)

def month_of_text_simple(text):
    """Version simplifiée de month_of_text pour les Landes."""
    from src.raa_client import MONTHS_FR
    text = text.lower()
    for m_name, m_code in MONTHS_FR.items():
        if m_name in text:
            return m_code
    return None
