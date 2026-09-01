"""Client HTTP (sans navigateur) du RAA de la Sarthe.

Même structure que le Maine-et-Loire : la page publications liste des
cartes « ... RAA - Sarthe - YYYY » menant à la page annuelle des liens
a.fr-link--download, chacun portant le span.fr-link__detail généré par
le CMS (source de vérité pour la date). Aucun navigateur nécessaire.
"""

from raa_client import AnnualPageRaaClient


class SartheRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA de la Sarthe."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, f"Sarthe - {year}", timeout)
