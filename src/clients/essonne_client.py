"""Client HTTP (sans navigateur) du RAA de l'Essonne.

La page annuelle (/Publications/Recueils-des-actes-administratifs-RAA/YYYY)
liste les mois sous forme de liens dans des h2. Chaque page de mois liste
les documents (liens directs vers PDF). La date fait foi sur l'attribut
title du lien (« PDF - 0,10 Mb - 02/01/2026 »).
"""

from urllib.parse import urljoin
from bs4 import BeautifulSoup

from src.raa_client import (
    MonthCardsRaaClient,
    parse_day_month,
    relaxed_day_month,
    month_of_text,
)


class EssonneRaaClient(MonthCardsRaaClient):
    """Client HTTP du RAA de l'Essonne.

    base_url : l'URL de la rubrique RAA
    (« .../Publications/Recueils-des-actes-administratifs-RAA »).
    """

    def _collect(self, soup, documents):
        # Les liens PDF de l'Essonne n'ont pas de classe CMS spécifique,
        # on cible les ancres dont l'href se termine par .pdf.
        for link in soup.select("a[href$='.pdf']"):
            href = link.get("href")
            if not href:
                continue
            name = href.split("/")[-1]
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    parse_day_month(link.get("title") or ""),
                    relaxed_day_month(link.get_text(strip=True)),
                )
            )

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        month_hrefs = [
            link["href"]
            for h2 in soup.select("h2")
            for link in [h2.find("a")]
            if link is not None and link.get("href") and month_of_text(link.get_text()) == month
        ]
        
        if not month_hrefs:
            documents = []
            self._collect(soup, documents)
            from src.raa_client import select_month_documents
            return select_month_documents(documents, month, secondary_source="texte du lien")

        all_docs = []
        for href in month_hrefs:
            url = urljoin(self.base_url, href)
            while url is not None:
                page_soup = BeautifulSoup(self._get(url).text, "html.parser")
                self._collect(page_soup, all_docs)
                url = self._next_page_url(page_soup)
        
        from src.raa_client import dedupe_documents, select_month_documents
        return select_month_documents(dedupe_documents(all_docs), month, secondary_source="texte du lien")

    def list_documents(self):
        """Retourne tous les documents de l'année."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        month_hrefs = [
            link["href"]
            for h2 in soup.select("h2")
            for link in [h2.find("a")]
            if link is not None and link.get("href")
        ]
        documents = []
        if not month_hrefs:
            self._collect(soup, documents)
            return documents
        for href in month_hrefs:
            url = urljoin(self.base_url, href)
            while url is not None:
                page_soup = BeautifulSoup(self._get(url).text, "html.parser")
                self._collect(page_soup, documents)
                url = self._next_page_url(page_soup)
        
        from src.raa_client import dedupe_documents
        return dedupe_documents(documents)
