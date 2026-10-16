"""Client HTTP du RAA du Loiret.
Le site utilise une page annuelle de cartes « Mois YYYY ». Pour les années
anciennes, il faut d'abord passer par une page d'année.
"""

from src.raa_client import MonthCardsRaaClient, urljoin
from bs4 import BeautifulSoup


class LoiretRaaClient(MonthCardsRaaClient):
    def __init__(self, base_url, year, timeout=60):
        self.year = str(year)
        self.root_url = base_url
        super().__init__(base_url, timeout)

    def _get_annual_page_for_year(self):
        """Retourne l'URL de la page contenant les cartes mois pour l'année."""
        soup = BeautifulSoup(self._get(self.root_url).text, "html.parser")
        for h2 in soup.select("h2.fr-card__title"):
            link = h2.find("a")
            if link and link.get("href"):
                if link.get_text(strip=True) == self.year:
                    return urljoin(self.root_url, link["href"])
        return self.root_url

    def list_documents(self):
        self.base_url = self._get_annual_page_for_year()
        return super().list_documents()

    def documents_for_month(self, month):
        self.base_url = self._get_annual_page_for_year()
        return super().documents_for_month(month)
