"""Client HTTP (sans navigateur) du RAA de la Loire-Atlantique.

La page mensuelle (/{année}/<mois>/) liste les documents sous forme de
cartes (a.fr-card__link.menu-item-link), paginées par 10 (URL de
pagination « (offset)/10 »). La date fait foi sur l'attribut title de la
carte, généré par le CMS (« format pdf - 10,24 Mb - 28/08/2026 ») ; le
texte de la carte (« RAA n°214 du 28 août 2026 ») sert de contrôle.
Aucun navigateur n'est nécessaire.
"""

from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
from unidecode import unidecode

from src.raa_client import (
    MONTH_NAMES_FR,
    RaaHttpClient,
    parse_day_month,
    relaxed_day_month,
    select_month_documents,
)


class LoireAtlantiqueRaaClient(RaaHttpClient):
    """Client HTTP du RAA de la Loire-Atlantique.

    base_url : l'URL de l'année avec slash final
    (« .../Recueil-des-actes-administratifs-RAA-en-Loire-Atlantique/2026/ ») ;
    le client y adosse le slug du mois (« Aout/ »).
    """

    def __init__(self, base_url, timeout=60):
        super().__init__(base_url, timeout)

    def _next_page_url(self, soup):
        for link in soup.select("ul.fr-pagination__list li a"):
            if link.get_text(strip=True) == "Suivant" and link.get("href"):
                return urljoin(self.base_url, link["href"])
        return None

    def list_documents(self, month):
        """Retourne les documents du mois (toutes pages de pagination) :
        (url, nom, jour_mois_cms, jour_mois_texte).
        """
        url = self.base_url + unidecode(MONTH_NAMES_FR[month]) + "/"
        documents = []
        while url is not None:
            soup = BeautifulSoup(self._get(url).text, "html.parser")
            for link in soup.select("a.fr-card__link.menu-item-link"):
                href = link.get("href")
                if not href:
                    continue
                name = unquote(href.split("/")[-1])
                documents.append(
                    (
                        urljoin(self.base_url, href),
                        name,
                        parse_day_month(link.get("title") or ""),
                        relaxed_day_month(link.get_text(strip=True)),
                    )
                )
            url = self._next_page_url(soup)
        return documents

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).
        """
        return select_month_documents(
            self.list_documents(month), month, secondary_source="texte de la carte"
        )
