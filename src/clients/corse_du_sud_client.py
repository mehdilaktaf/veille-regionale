from src.raa_client import AnnualPageRaaClient, dedupe_documents, link_day_month, relaxed_day_month
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

class CorseDuSudRaaClient(AnnualPageRaaClient):
    """Client pour le RAA de la Corse-du-Sud.
    
    Structure : Page section -> cartes années -> page annuelle -> liens directs PDF.
    """
    def __init__(self, url, annee):
        super().__init__(
            base_url="https://www.corse-du-sud.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-de-la-prefecture-de-la-Corse-du-Sud",
            card_needle="Recueils des actes administratifs de l'année",
        )
        self.annee = annee
        self.annual_page_url = f"https://www.corse-du-sud.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-de-la-prefecture-de-la-Corse-du-Sud/Recueils-des-actes-administratifs-de-l-annee-{annee}"

    def list_documents(self):
        """Surcharge pour utiliser un sélecteur de liens plus permissif (sans classe fr-link)."""
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise Exception(f"Page annuelle introuvable sur {self.base_url}")
        
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        documents = []
        # On cherche tous les liens qui pointent vers un PDF
        for link in soup.select("a[href$='.pdf']"):
            href = link.get("href")
            if not href:
                continue
            name = unquote(href.split("/")[-1])
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    link_day_month(link),
                    relaxed_day_month(link.get_text(strip=True)),
                )
            )
        return dedupe_documents(documents)
