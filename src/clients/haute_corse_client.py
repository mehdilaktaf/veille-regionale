from src.raa_client import RaaHttpClient, select_month_documents, dedupe_documents, link_day_month, relaxed_day_month, find_annual_href
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

class HauteCorseRaaClient(RaaHttpClient):
    """Client pour le RAA de la Haute-Corse.
    
    Structure : Page section -> cartes années -> page annuelle -> pages mensuelles -> liens directs PDF.
    """
    def __init__(self, url, annee):
        super().__init__(base_url="https://www.haute-corse.gouv.fr/Publications/Publications-administratives-et-legales/Recueils-des-actes-administratifs")
        self.annee = annee
        self.annual_page_url = f"https://www.haute-corse.gouv.fr/Publications/Publications-administratives-et-legales/Recueils-des-actes-administratifs/Recueil-des-actes-administratifs-{annee}"

    def list_documents(self):
        """Retourne les documents de l'année : (url, nom, jour_mois_cms, jour_mois_secondaire)."""
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        
        # On cherche les liens vers les mois. Ils sont dans des h2.
        month_links = []
        for h2 in soup.find_all("h2"):
            link = h2.find("a")
            if link and link.get("href"):
                month_links.append(link["href"])
        
        documents = []
        for href in month_links:
            url = urljoin(self.annual_page_url, href)
            month_soup = BeautifulSoup(self._get(url).text, "html.parser")
            
            # Sur la page du mois, on cherche les liens de téléchargement
            # On utilise le sélecteur générique du projet
            from src.raa_client import DOWNLOAD_LINK_SELECTOR
            for link in month_soup.select(DOWNLOAD_LINK_SELECTOR):
                pdf_href = link.get("href")
                if not pdf_href:
                    continue
                name = unquote(pdf_href.split("/")[-1])
                documents.append(
                    (
                        urljoin(self.base_url, pdf_href),
                        name,
                        link_day_month(link),
                        relaxed_day_month(link.get_text(strip=True)),
                    )
                )
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        return select_month_documents(self.list_documents(), month, secondary_source="texte du lien")
