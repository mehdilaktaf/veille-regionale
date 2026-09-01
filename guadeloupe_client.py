"""Client HTTP (sans navigateur) du RAA de la Guadeloupe.

La page annuelle (…/Le-Recueil-des-actes-administratifs/YYYY) liste des
cartes « Mois YYYY » menant à des pages de liens a.fr-link--download,
chacun portant le span.fr-link__detail généré par le CMS (source de
vérité pour la date). Aucun navigateur n'est nécessaire.
"""

from raa_client import MonthCardsRaaClient


class GuadeloupeRaaClient(MonthCardsRaaClient):
    """Client HTTP du RAA de la Guadeloupe."""
