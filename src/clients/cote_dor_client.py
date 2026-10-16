from src.raa_client import AnnualPageRaaClient, parse_day_month, unquote, urljoin
from bs4 import BeautifulSoup

class CoteDorRaaClient(AnnualPageRaaClient):
    """
    Client HTTP du RAA de la Côte-d'Or.
    Page annuelle avec liens directs, date dans l'attribut title du lien.
    """
    def __init__(self, url, year):
        super().__init__(url, card_needle="2026")

    def find_annual_page(self):
        return self.base_url

    def list_documents(self):
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
        
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        documents = []
        # Les liens sont directs vers les PDF
        for link in soup.select("a[href$='.pdf']"):
            href = link.get("href")
            if not href:
                continue
            name = unquote(href.split("/")[-1])
            
            # La date est dans l'attribut title : "PDF - 1,30 Mb - 18/09/2026"
            title = link.get("title", "")
            cms_day_month = parse_day_month(title)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_day_month,
                    None,
                )
            )
        return documents
