import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from src.raa_client import (
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    find_annual_href,
    parse_day_month,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class CharenteMaritimeRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Charente-Maritime.
    Structure : Page section -> Page annuelle paginée (offset).
    Pattern Hauts-de-Seine.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        # On tente d'abord l'URL directe fournie pour 2026
        if self.year == 2026:
            return "https://www.charente-maritime.gouv.fr/Publications/RAA-Recueil-des-Actes-Administratifs/Annee-2026"
        
        try:
            soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
            href = find_annual_href(soup, f"RAA {self.year}")
            if href is None:
                href = find_annual_href(soup, f"Année {self.year}")
            if href is None:
                return None
            return urljoin(self.base_url, href)
        except Exception as e:
            logger.warning("Erreur lors de la recherche de la page annuelle : %s", e)
            return None

    def _get_pagination_info(self, soup):
        """Extrait le nombre total de pages et le pattern d'URL de la pagination."""
        total_pages = 1
        page_pattern = None
        
        pagination_links = soup.select("ul.fr-pagination__list li a")
        for link in pagination_links:
            text = link.get_text(strip=True)
            href = link.get("href")
            if not href:
                continue
            if text.isdigit():
                total_pages = max(total_pages, int(text))
                import re
                matches = list(re.finditer(r'\d+', href))
                if matches:
                    last_match = matches[-1]
                    start, end = last_match.span()
                    page_pattern = href[:start] + '{}' + href[end:]
                    
        return total_pages, page_pattern

    def _get_page_url(self, page_num, pattern, docs_per_page=10):
        """Construit l'URL pour une page spécifique en calculant l'offset."""
        if pattern is None:
            return None
        offset = (page_num - 1) * docs_per_page
        return urljoin(self.annual_page_url, pattern.format(offset))

    def list_documents(self, month):
        """Retourne les documents du mois cible en utilisant une recherche optimisée (sauts)."""
        month_int = int(month) if isinstance(month, str) else month
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(f"Page annuelle {self.year} introuvable sur {self.base_url}")
        
        soup_first = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        total_pages, page_pattern = self._get_pagination_info(soup_first)
        
        def extract_docs(soup, url):
            docs = []
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                if not href or not href.lower().endswith(".pdf"):
                    continue
                title = link.get("title") or ""
                if "format pdf" not in title.lower():
                    continue
                name = unquote(href.split("/")[-1])
                docs.append((urljoin(self.base_url, href), name, parse_day_month(title), relaxed_day_month(link.get_text(strip=True))))
            return docs

        first_page_docs = extract_docs(soup_first, self.annual_page_url)
        
        if page_pattern is None:
            documents = []
            url = self.annual_page_url
            while url is not None:
                soup = BeautifulSoup(self._get(url).text, "html.parser")
                page_docs = extract_docs(soup, url)
                documents.extend(page_docs)
                if page_docs and page_docs[-1][2] and page_docs[-1][2][1] < month_int:
                    break
                url = None 
            return dedupe_documents(documents)

        target_page = None
        low, high = 1, total_pages
        while low <= high:
            mid = (low + high) // 2
            url_mid = self._get_page_url(mid, page_pattern)
            soup_mid = BeautifulSoup(self._get(url_mid).text, "html.parser")
            docs_mid = extract_docs(soup_mid, url_mid)
            
            if not docs_mid:
                low = mid + 1
                continue
                
            first_valid = next((d[2] for d in docs_mid if d[2]), None)
            last_valid = next((d[2] for d in reversed(docs_mid) if d[2]), None)
            
            if any(d[2] and d[2][1] == month_int for d in docs_mid):
                target_page = mid
                break
            if last_valid and last_valid[1] > month_int:
                low = mid + 1
            elif first_valid and first_valid[1] < month_int:
                high = mid - 1
            else:
                low = mid + 1
        
        if target_page is None:
            low, high = 1, total_pages
            while low <= high:
                mid = (low + high) // 2
                url_mid = self._get_page_url(mid, page_pattern)
                soup_mid = BeautifulSoup(self._get(url_mid).text, "html.parser")
                docs_mid = extract_docs(soup_mid, url_mid)
                if any(d[2] and d[2][1] == month_int for d in docs_mid):
                    target_page = mid
                    break
                first_valid = next((d[2] for d in docs_mid if d[2]), None)
                if first_valid and first_valid[1] < month_int:
                    high = mid - 1
                else:
                    low = mid + 1
                    
        if target_page is None:
            return dedupe_documents(first_page_docs)

        final_docs = []
        p = target_page
        while p >= 1:
            url_p = self._get_page_url(p, page_pattern)
            soup_p = BeautifulSoup(self._get(url_p).text, "html.parser")
            docs_p = extract_docs(soup_p, url_p)
            if not docs_p or not any(d[2] and d[2][1] == month_int for d in docs_p):
                break
            final_docs.extend(docs_p)
            p -= 1
            
        p = target_page + 1
        while p <= total_pages:
            url_p = self._get_page_url(p, page_pattern)
            soup_p = BeautifulSoup(self._get(url_p).text, "html.parser")
            docs_p = extract_docs(soup_p, url_p)
            if not docs_p or not any(d[2] and d[2][1] == month_int for d in docs_p):
                break
            final_docs.extend(docs_p)
            p += 1
            
        return dedupe_documents(final_docs)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        return select_month_documents(self.list_documents(month), month, secondary_source="texte du lien")
