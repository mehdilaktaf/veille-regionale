"""Client HTTP (sans navigateur) du RAA des Hauts-de-Seine.

Structure :
- page section (Publications/Annonces-avis/Le-Recueil-des-actes-administratifs)
  portant des liens vers les pages annuelles (RAA-YYYY).
- page annuelle listant les documents paginés par 10.
- chaque document est un lien direct vers le PDF avec la date dans l'attribut `title`
  (pattern Aube/Loire-Atlantique).
"""

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


class HautsDeSeineRaaClient(RaaHttpClient):
    """Client HTTP du RAA des Hauts-de-Seine."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        # Le lien est du type "RAA 2026"
        href = find_annual_href(soup, f"RAA {self.year}")
        if href is None:
            return None
        return urljoin(self.base_url, href)

    def _next_page_url(self, soup):
        """Recherche le lien 'Suivant' dans la pagination."""
        for link in soup.select("ul.fr-pagination__list li a"):
            if link.get_text(strip=True) == "Suivant" and link.get("href"):
                return urljoin(self.annual_page_url, link["href"])
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
                # On a trouvé un numéro de page, on peut en déduire le pattern
                total_pages = max(total_pages, int(text))
                # On enregistre le pattern en remplaçant le dernier nombre trouvé par {}
                # car le numéro de page est généralement à la fin de l'URL (ex: /RAA-2026?page=2)
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
        # On s'assure que month est un entier pour les comparaisons
        month_int = int(month) if isinstance(month, str) else month
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(f"Page annuelle {self.year} introuvable sur {self.base_url}")
        
        # 1. Analyse de la première page
        soup_first = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        total_pages, page_pattern = self._get_pagination_info(soup_first)
        logger.info("Pagination : %d pages trouvées. Pattern : %s", total_pages, page_pattern)
        
        # Collecte des docs de la page 1
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
        logger.info("Page 1 : %d docs trouvés", len(first_page_docs))
        if first_page_docs:
            # Trouver la première date valide pour le log
            valid_first = next((d[2] for d in first_page_docs if d[2]), None)
            valid_last = next((d[2] for d in reversed(first_page_docs) if d[2]), None)
            logger.info("Page 1 : premier doc valide mois %s, dernier doc valide mois %s", 
                       valid_first[1] if valid_first else "N/A",
                       valid_last[1] if valid_last else "N/A")
        
        # Si on ne peut pas sauter, on repasse en mode séquentiel (fallback)
        if page_pattern is None:
            logger.info("Pas de pattern de pagination trouvé, fallback en mode séquentiel.")
            documents = []
            url = self.annual_page_url
            while url is not None:
                soup = BeautifulSoup(self._get(url).text, "html.parser")
                page_docs = extract_docs(soup, url)
                documents.extend(page_docs)
                # Arrêt précoce : on cherche le dernier doc valide de la page
                valid_last = next((d[2] for d in reversed(page_docs) if d[2]), None)
                if valid_last and valid_last[1] < month_int:
                    break
                url = self._next_page_url(soup)
            return dedupe_documents(documents)

        # 2. Recherche binaire pour trouver une page contenant le mois cible
        target_page = None
        low, high = 1, total_pages
        while low <= high:
            mid = (low + high) // 2
            url_mid = self._get_page_url(mid, page_pattern)
            logger.info("Binary search : test page %d (%s)", mid, url_mid)
            soup_mid = BeautifulSoup(self._get(url_mid).text, "html.parser")
            docs_mid = extract_docs(soup_mid, url_mid)
            
            if not docs_mid:
                logger.info("Page %d vide", mid)
                low = mid + 1
                continue
            
            # On ne base la décision que sur les documents ayant une date valide
            valid_docs = [d for d in docs_mid if d[2] is not None]
                
            if not valid_docs:
                logger.info("Page %d ne contient aucune date valide, on avance par défaut", mid)
                low = mid + 1
                continue

            first_valid = valid_docs[0][2]
            last_valid = valid_docs[-1][2]
            
            logger.info("Page %d : premier doc valide mois %s, dernier doc valide mois %s", 
                       mid, first_valid[1], last_valid[1])
            
            # Si le mois est présent sur cette page (même partiellement)
            if any(d[2] and d[2][1] == month_int for d in docs_mid):
                logger.info("Mois cible trouvé sur page %d", mid)
                target_page = mid
                break
            
            # Si tout sur la page est strictement > month, on va plus loin
            if last_valid[1] > month_int:
                logger.info("Page %d trop récente (min: %d), on avance", mid, last_valid[1])
                low = mid + 1
            # Si tout sur la page est strictement < month, on revient en arrière
            elif first_valid[1] < month_int:
                logger.info("Page %d trop ancienne (max: %d), on recule", mid, first_valid[1])
                high = mid - 1
            else:
                # Cas ambigu (ex: page contient des dates mais aucune n'est = month, 
                # et first < month < last... impossible si trié, mais par sécurité)
                logger.info("Page %d ambiguë, on avance", mid)
                low = mid + 1
        
        # Si on n'a pas trouvé de page contenant le mois, on tente une dernière passe de chevauchement
        if target_page is None:
            logger.info("Aucune page identifiée pour le mois %d, recherche finale...", month_int)
            low, high = 1, total_pages
            while low <= high:
                mid = (low + high) // 2
                url_mid = self._get_page_url(mid, page_pattern)
                soup_mid = BeautifulSoup(self._get(url_mid).text, "html.parser")
                docs_mid = extract_docs(soup_mid, url_mid)
                if any(d[2] and d[2][1] == month_int for d in docs_mid):
                    logger.info("Chevauchement trouvé sur page %d", mid)
                    target_page = mid
                    break
                valid_docs = [d for d in docs_mid if d[2] is not None]
                if valid_docs and valid_docs[0][2][1] < month_int:
                    high = mid - 1
                else:
                    low = mid + 1
                    
        if target_page is None:
            logger.info("Mois %d introuvable après recherche binaire", month_int)
            return dedupe_documents(first_page_docs)

        # 3. Extension : on récupère toutes les pages qui contiennent le mois cible
        logger.info("Extension autour de la page %d...", target_page)
        final_docs = []
        
        # Vers l'arrière
        p = target_page
        while p >= 1:
            url_p = self._get_page_url(p, page_pattern)
            soup_p = BeautifulSoup(self._get(url_p).text, "html.parser")
            docs_p = extract_docs(soup_p, url_p)
            if not docs_p or not any(d[2] and d[2][1] == month_int for d in docs_p):
                logger.info("Arrêt extension arrière à la page %d", p)
                break
            logger.info("Extension arrière : page %d OK", p)
            final_docs.extend(docs_p)
            p -= 1
            
        # Vers l'avant
        p = target_page + 1
        while p <= total_pages:
            url_p = self._get_page_url(p, page_pattern)
            soup_p = BeautifulSoup(self._get(url_p).text, "html.parser")
            docs_p = extract_docs(soup_p, url_p)
            if not docs_p or not any(d[2] and d[2][1] == month_int for d in docs_p):
                logger.info("Arrêt extension avant à la page %d", p)
                break
            logger.info("Extension avant : page %d OK", p)
            final_docs.extend(docs_p)
            p += 1
            
        return dedupe_documents(final_docs)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="texte du lien"
        )
