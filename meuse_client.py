"""Client HTTP (sans navigateur) du RAA de la Meuse.

Deux niveaux :
- la page section (…/Recueil-des-Actes-Administratifs-RAA) ne porte pas de
  cartes années mais un select « Liste-des-recueils-liste-docs » (1 option
  par année, libellés « RAA année YYYY », 2026 → 2006, coquille de casse
  réelle pour 2020 : « RAA Année 2020 ») ;
- la page annuelle liste directement les liens a.fr-link--download sans
  pagination, span.fr-link__detail CMS 100 % (source de vérité), même
  pattern que le Maine-et-Loire.
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from raa_client import AnnualPageRaaClient

SELECT_NAME = "Liste-des-recueils-liste-docs"


class MeuseRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA de la Meuse."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, f"RAA année {year}", timeout)
        self.year = int(year)

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None).

        Navigation par le select d'années (pas de cartes) : l'option dont
        le libellé est « RAA année YYYY » (comparaison exacte, insensible
        à la casse — 2020 est « RAA Année 2020 ») pointe sur la page
        annuelle via sa value.
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        select = soup.select_one(f"select[name='{SELECT_NAME}']")
        if select is None:
            return None
        for option in select.find_all("option"):
            text = " ".join(option.get_text(strip=True).lower().split())
            if text == f"raa année {self.year}":
                value = (option.get("value") or "").strip()
                if not value:
                    continue
                # Value relative à la racine du site (« Publications/... »),
                # pas à la page section : un urljoin direct dupliquerait le
                # préfixe.
                if not value.startswith(("/", "http")):
                    value = "/" + value
                return urljoin(self.base_url, value)
        return None
