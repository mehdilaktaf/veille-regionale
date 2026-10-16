import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from src.raa_client import (
    DOWNLOAD_LINK_SELECTOR,
    RaaHttpClient,
    dedupe_documents,
    link_day_month,
    relaxed_day_month,
)

logger = logging.getLogger(__name__)

class SeineMaritimeRaaClient(RaaHttpClient):
    """
    Client for Seine-Maritime RAA.
    Structure: Annual Page -> Monthly Page -> PDF.
    Dates are in the link text.
    """

    def _collect(self, soup, documents):
        """Extracts PDF links from a page (usually a document page)."""
        for link in soup.select(DOWNLOAD_LINK_SELECTOR):
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

    def list_documents(self):
        """
        Returns documents for the year: (url, name, jour_mois_cms, jour_mois_secondaire).
        The annual page lists links to monthly pages, which list links to document pages.
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        
        # Monthly links are within h2 tags on the annual page.
        month_hrefs = []
        for h2 in soup.find_all("h2"):
            link = h2.find("a")
            if link and link.get("href"):
                if "RAA-" in link["href"]:
                    month_hrefs.append(link["href"])
        
        documents = []
        if not month_hrefs:
            self._collect(soup, documents)
            return dedupe_documents(documents)
            
        for href in month_hrefs:
            month_url = urljoin(self.base_url, href)
            month_soup = BeautifulSoup(self._get(month_url).text, "html.parser")
            
            # Find links to document pages on the monthly page.
            # Document links typically don't end in .pdf and are not navigation.
            for link in month_soup.select("a[href]"):
                href_doc = link.get("href")
                if not href_doc or href_doc.endswith(".pdf") or "http" in href_doc and "gouv.fr" not in href_doc:
                    continue
                
                # We visit the document page and collect the PDF.
                doc_url = urljoin(month_url, href_doc)
                doc_soup = BeautifulSoup(self._get(doc_url).text, "html.parser")
                self._collect(doc_soup, documents)
                
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """
        Returns PDF links for the given month in chronological order.
        """
        from src.raa_client import select_month_documents
        return select_month_documents(
            self.list_documents(), month, secondary_source="texte du lien"
        )
