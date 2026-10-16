"""Client HTTP (sans navigateur) du RAA du Jura.

Structure :
- la page section (…/Recueil-des-Actes-Administratifs) porte des liens
  « Année YYYY » ;
- la page annuelle (…/Annee-YYYY) liste directement les liens PDF,
  paginés par 10 ; la date est dans l'attribut `title` du lien.
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from src.raa_client import (
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    find_annual_href,
    month_of_text,
    parse_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class JuraRaaClient(RaaHttpClient):
    """Client HTTP du RAA du Jura."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        href = find_annual_href(soup, f"Année {self.year}")
        if href is None:
            return None
        return urljoin(self.base_url, href)

    def list_documents(self, month):
        """Retourne les RAA du mois cible (toutes les pages de pagination) :
        (url, nom, jour_mois_cms, None).
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle {self.year} introuvable sur {self.base_url}"
                )
        
        documents = []
        url = self.annual_page_url
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            
            # On cherche les liens PDF directs
            # Ils sont dans des h2 ou simplement des liens a avec un title
            for a in soup.select("a[href$='.pdf']"):
                href = a.get("href")
                if not href:
                    continue
                
                text = a.get_text(" ", strip=True)
                title = a.get("title", "")
                
                # On utilise parse_month pour supporter les dates numériques (ex: 21-09-2026)
                from src.raa_client import parse_month
                m_text = parse_month(text)
                m_title = parse_month(title)
                
                if m_text != month and m_title != month:
                    continue
                
                # Pour le Jura, on utilise l'attribut title pour la date CMS
                # (similaire à l'Aube)
                from src.raa_client import link_day_month
                
                # On simule un objet ayant un span.fr-link__detail pour réutiliser link_day_month
                # ou on extrait manuellement du title.
                # Le pattern est "format pdf - X Mb - DD/MM/YYYY"
                cms_date = None
                if title:
                    # On crée un faux élément pour link_day_month ou on parse
                    # Ici on utilise parse_day_month directement
                    from src.raa_client import parse_day_month
                    cms_date = parse_day_month(title)

                documents.append(
                    (
                        urljoin(self.base_url, href),
                        unquote(href.split("/")[-1]),
                        cms_date,
                        None,
                    )
                )

            # Pagination : on s'arrête si on a dépassé le mois cible
            # (La liste est décroissante)
            # Pour simplifier, on suit le "Suivant"
            url = None
            for link in soup.select("ul.fr-pagination__list li a"):
                if link.get_text(strip=True) == "Suivant" and link.get("href"):
                    url = urljoin(self.annual_page_url, link["href"])
                    break
        
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des RAA du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).
        """
        return select_month_documents(
            self.list_documents(month), month, secondary_source="carte"
        )
