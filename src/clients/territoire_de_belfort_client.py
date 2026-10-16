"""Client HTTP (sans navigateur) du RAA du Territoire de Belfort.

Deux niveaux :
- la page section (…/Publications/
  Le-recueil-des-actes-administratifs) ne porte ni cartes ni select :
  des liens a.fr-link plain « Année YYYY » (2026 → 2015 + 2010 ;
  2011-2014 absents ; coquille réelle du site : le lien « Année 2021 »
  pointe sur la page Annee-2022). Les slugs récents sont longs
  (…/Le-recueil-des-actes-administratifs-Annee-2026), les anciens
  courts (…/Annee-2022) ;
- la page annuelle liste directement les liens a.fr-link--download
  sans pagination, span.fr-link__detail CMS 100 % (source de vérité),
  même pattern que le Maine-et-Loire. Les noms de fichier
  (« recueil-90-2026-014- publié le 02-02-2026.pdf ») sont ancrés sur
  « publié le » (pas « du ») : `du_day_month` échoue, le repli
  `relaxed_day_month` de la base suffit (le CMS fait foi).
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.raa_client import AnnualPageRaaClient


class TerritoireDeBelfortRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA du Territoire de Belfort."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, f"Année {year}", timeout)
        self.year = int(year)

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None).

        Navigation par les liens a.fr-link « Année YYYY » (pas de cartes
        h2.fr-card__title) : match exact sur le texte du lien.
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        for link in soup.select("a.fr-link"):
            if (
                link.get("href")
                and link.get_text(strip=True) == f"Année {self.year}"
            ):
                return urljoin(self.base_url, link["href"])
        return None
