from src.raa_client import AnnualPageRaaClient

class SommeRaaClient(AnnualPageRaaClient):
    """Client pour le RAA de la Somme.
    Structure : section -> page annuelle -> PDF directs.
    Pas de span CMS, la date est dans le texte du lien.
    """
    def __init__(self, base_url, timeout=60):
        super().__init__(
            base_url=base_url,
            card_needle="Année",
            timeout=timeout
        )

    def list_documents(self):
        """Surcharge pour utiliser un sélecteur de liens plus large (a.fr-link)."""
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise Exception(f"Page annuelle introuvable sur {self.base_url}")
        
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, unquote
        from src.raa_client import link_day_month, du_day_month, relaxed_day_month

        response = self._get(self.annual_page_url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Les liens sont dans des <p> à l'intérieur de div.fr-text--lead
        container = soup.select_one("div.fr-text--lead") or soup
        documents = []
        
        for link in container.select("a.fr-link"):
            href = link.get("href")
            if not href or not href.endswith(".pdf"):
                continue
            
            name = unquote(href.split("/")[-1])
            text = link.get_text(strip=True)
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    link_day_month(link), # Sera None car pas de span.fr-link__detail
                    du_day_month(text) or relaxed_day_month(text),
                )
            )
        return documents
