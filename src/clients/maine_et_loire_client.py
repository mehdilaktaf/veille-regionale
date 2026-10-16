"""Client HTTP (sans navigateur) du RAA du Maine-et-Loire.

La page publications liste des cartes « Année YYYY » ; la page annuelle
liste directement les liens de téléchargement (a.fr-link--download),
chacun portant le span.fr-link__detail généré par le CMS (source de
vérité pour la date). Le nom de fichier (parfois fautif : « du
23062026 », « du 08 janvier », ordinal « 1er ») sert de contrôle
croisé. La page n'étant pas générée par JavaScript, aucun navigateur
n'est nécessaire et le pop-up de cookies (tarteaucitron) n'a pas
d'impact.
"""

from src.raa_client import AnnualPageRaaClient, du_day_month, du_month

__all__ = [
    "MaineEtLoireRaaClient",
    "filename_day_month",
    "filename_month",
    "find_annual_href",
    "link_day_month",
]


def filename_day_month(name):
    """Extrait (jour, mois) du nom de fichier. None si aucune date fiable."""
    return du_day_month(name)


def filename_month(name):
    """Extrait le mois (« MM ») du nom de fichier. None si aucune date fiable."""
    return du_month(name)


# Re-exportés depuis raa_client pour compatibilité des imports existants
from src.raa_client import find_annual_href, link_day_month  # noqa: E402,F401


class MaineEtLoireRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA du Maine-et-Loire.

    Les années antérieures (2005-2021) sont sous la carte « Archives RAA »
    de la page publications (cartes « Année YYYY ») ; les années 2022+
    sont directement sur la page publications.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, f"Année {year}", timeout,
                         archives_needle="Archives")
