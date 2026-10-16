from src.raa_client import RaaHttpClient, select_month_documents, dedupe_documents, link_day_month, relaxed_day_month, find_annual_href
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

class OiseRaaClient(RaaHttpClient):
    """Client pour le RAA de l'Oise.
    Structure : section -> page annuelle paginée -> PDF directs.
    """
    def __init__(self, base_url, timeout=60):
        super().__init__(base_url, timeout)
        self.card_needle = "RAA"
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        # Recherche robuste : tout lien contenant "RAA" et une année (4 chiffres)
        for link in soup.select("a"):
            text = link.get_text(strip=True)
            if "RAA" in text and any(char.isdigit() for char in text):
                return urljoin(self.base_url, link["href"])
        
        # Repli sur la méthode standard
        href = find_annual_href(soup, self.card_needle)
        if href:
            return urljoin(self.base_url, href)
        return None

    def _next_page_url(self, soup):
        """Trouve l'URL de la page suivante dans la pagination."""
        for link in soup.select("ul.fr-pagination__list li a"):
            if "Suivant" in link.get_text(strip=True) and link.get("href"):
                return urljoin(self.base_url, link["href"])
        return None

    def list_documents(self):
        """Retourne les documents de l'année en parcourant la pagination :
        (url, nom, jour_mois_cms, jour_mois_nom).
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise Exception(f"Page annuelle introuvable sur {self.base_url}")
        
        url = self.annual_page_url
        documents = []
        
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            
            for link in soup.select("a.fr-link--download"):
                href = link.get("href")
                if not href:
                    continue
                name = unquote(href.split("/")[-1])
                documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        link_day_month(link),
                        du_day_month(name) or relaxed_day_month(name),
                    )
                )
            url = self._next_page_url(soup)
            
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant.
        Optimisation : s'arrête dès que les documents dépassent le mois cible.
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise Exception(f"Page annuelle introuvable sur {self.base_url}")
        
        url = self.annual_page_url
        all_month_docs = []
        
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            page_docs = []
            
            for link in soup.select("a.fr-link--download"):
                href = link.get("href")
                if not href or not href.endswith(".pdf"):
                    continue
                name = unquote(href.split("/")[-1])
                cms_dm = link_day_month(link)
                sec_dm = du_day_month(name) or relaxed_day_month(name)
                
                # Déterminer le mois faisant foi
                effective_month = None
                if cms_dm:
                    effective_month = f"{cms_dm[1]:02d}"
                elif sec_dm:
                    effective_month = f"{sec_dm[1]:02d}"
                
                if effective_month == month:
                    page_docs.append((urljoin(self.base_url, href), name, cms_dm, sec_dm))
                elif effective_month and effective_month > month:
                    # On a dépassé le mois cible (ordre croissant)
                    url = None
                    break
            
            all_month_docs.extend(page_docs)
            if url is not None:
                url = self._next_page_url(soup)
        
        return select_month_documents(dedupe_documents(all_month_docs), month)
