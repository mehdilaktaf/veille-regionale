from src.raa_client import RaaHttpClient, select_month_documents, dedupe_documents, link_day_month, relaxed_day_month
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

class NordRaaClient(RaaHttpClient):
    """Client pour le RAA du Nord.
    
    Structure : Page section -> page annuelle -> pages mensuelles -> liens directs PDF.
    """
    def __init__(self, url, annee):
        super().__init__(base_url="https://www.nord.gouv.fr/Publications/Recueils-des-actes-administratifs")
        self.annee = annee
        self.annual_page_url = f"https://www.nord.gouv.fr/Publications/Recueils-des-actes-administratifs/RAA-du-departement-du-Nord/{annee}"

    def list_documents(self):
        """Retourne les documents de l'année : (url, nom, jour_mois_cms, jour_mois_secondaire)."""
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        
        # On cherche les liens vers les mois. Ils sont dans des h2 ou listes.
        # Sur le site du Nord, ils sont dans des h2.
        month_links = []
        for h2 in soup.find_all("h2"):
            link = h2.find("a")
            if link and link.get("href"):
                month_links.append(link["href"])
        
        # Si on n'a rien trouvé dans h2, on cherche dans les liens de la rubrique
        if not month_links:
            for link in soup.select("ul li a"):
                href = link.get("href")
                if href and any(m in href for m in ["Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin", "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"]):
                    month_links.append(href)

        documents = []
        for href in month_links:
            url = urljoin(self.annual_page_url, href)
            try:
                month_soup = BeautifulSoup(self._get(url).text, "html.parser")
                
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
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Erreur lors de la visite du mois %s : %s", href, e)

        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        return select_month_documents(self.list_documents(), month, secondary_source="texte du lien")
