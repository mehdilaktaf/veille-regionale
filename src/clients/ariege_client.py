import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from src.raa_client import MonthCardsRaaClient, month_of_text, DOWNLOAD_LINK_SELECTOR, link_day_month, relaxed_day_month, dedupe_documents, select_month_documents

logger = logging.getLogger(__name__)

class AriegeRaaClient(MonthCardsRaaClient):
    """Client HTTP pour le RAA de l'Ariège.
    
    Structure :
    - Page annuelle : cartes « Recueil des actes administratifs du mois ... » (h2.fr-card__title).
    - Page mensuelle : liens directs vers les PDF avec date dans le texte du lien.
    """
    def documents_for_month(self, month):
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        cards = soup.select("h2.fr-card__title")
        
        month_hrefs = []
        for h2 in cards:
            link = h2.find("a")
            if link and link.get("href"):
                text = link.get_text(strip=True)
                if month_of_text(text) == month:
                    month_hrefs.append(link["href"])
        
        if not month_hrefs:
            documents = []
            self._collect(soup, documents)
            return select_month_documents(documents, month, secondary_source="texte du lien")

        all_docs = []
        for href in month_hrefs:
            url = urljoin(self.base_url, href)
            page_soup = BeautifulSoup(self._get(url).text, "html.parser")
            self._collect(page_soup, all_docs)
        
        return select_month_documents(dedupe_documents(all_docs), month, secondary_source="texte du lien")

    def _collect(self, soup, documents):
        # Sur l'Ariège, on utilise un sélecteur plus large car les classes peuvent varier
        for link in soup.select("a[href$='.pdf']"):
            href = link.get("href")
            if not href:
                continue
            import os
            from urllib.parse import unquote
            name = unquote(href.split("/")[-1])
            
            cms_day_month = link_day_month(link)
            text_day_month = relaxed_day_month(link.get_text(strip=True))
            
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    cms_day_month,
                    text_day_month,
                )
            )

