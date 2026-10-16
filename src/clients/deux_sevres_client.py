import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from src.raa_client import MonthCardsRaaClient, RaaError

logger = logging.getLogger(__name__)

class DeuxSevresRaaClient(MonthCardsRaaClient):
    """Client HTTP pour le RAA des Deux-Sèvres.
    
    Structure :
    - Page annuelle : listes de liens vers les mois (h2.fr-card__title).
    - Page mensuelle : liens directs vers les PDF avec date dans le texte du lien.
    """

    def _collect(self, soup, documents):
        # Le site des Deux-Sèvres utilise des liens simples sans span.fr-link__detail
        # Le format est : [Télécharger <nom> PDF - <taille> - <date>](<url>)
        # On utilise relaxed_day_month sur le texte du lien pour extraire la date.
        from src.raa_client import DOWNLOAD_LINK_SELECTOR, relaxed_day_month, unquote, link_day_month
        
        for link in soup.select(DOWNLOAD_LINK_SELECTOR):
            href = link.get("href")
            if not href:
                continue
            name = unquote(href.split("/")[-1])
            
            # On tente d'abord le span CMS (si présent), sinon le texte du lien
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
