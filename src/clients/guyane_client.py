"""Client HTTP (sans navigateur) du RAA de la Guyane.

La page annuelle (…/Recueil-des-actes-administratifs/Annee-YYYY) liste
des cartes « Mois YYYY » menant à des pages de liens a.fr-link--download,
chacun portant le span.fr-link__detail généré par le CMS (source de
vérité pour la date). Aucun navigateur n'est nécessaire.
"""

from src.raa_client import MonthCardsRaaClient


class GuyaneRaaClient(MonthCardsRaaClient):
    """Client HTTP du RAA de la Guyane."""
