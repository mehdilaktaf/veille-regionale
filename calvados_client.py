"""Client HTTP (sans navigateur) du RAA du Calvados.

La page publications liste la carte « Recueil des actes administratifs
départemental » (et « régional ») ; la page départementale porte des
cartes d'années à texte exact « YYYY » (2026→2018) et une carte
« Archives ». La page annuelle liste directement les liens
a.fr-link--download (≈ 350/an, sans pagination), chacun portant le
span.fr-link__detail généré par le CMS (source de vérité pour la date) :
les noms de fichier (« recueil-14-2026-369-... ») ne portent aucune date.
Aucun navigateur nécessaire.
"""

from raa_client import AnnualPageRaaClient


class CalvadosRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA du Calvados."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, year, timeout, archives_needle="Archives")
