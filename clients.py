"""Mapping département -> client HTTP, partagé entre app.py (GUI) et
run.py (CLI).

Source de vérité unique pour l'URL de base et la classe de client de chaque
département, afin que la GUI et le CLI ne divergent pas.
"""

from aisne_client import AisneRaaClient
from ardennes_client import ArdennesRaaClient
from aube_client import AubeRaaClient
from vendee_client import VendeeRaaClient
from maine_et_loire_client import MaineEtLoireRaaClient
from sarthe_client import SartheRaaClient
from mayenne_client import MayenneRaaClient
from loire_atlantique_client import LoireAtlantiqueRaaClient
from guadeloupe_client import GuadeloupeRaaClient
from guyane_client import GuyaneRaaClient
from martinique_client import MartiniqueRaaClient
from reunion_client import ReunionRaaClient
from mayotte_client import MayotteRaaClient
from moselle_client import MoselleRaaClient

# URL de base par département ({year} remplacé par l'année ciblée).
DEPARTMENT_URLS = {
    "Aisne": "https://www.aisne.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Ardennes": "https://www.ardennes.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Aube": "https://www.aube.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA2",
    "Maine-et-Loire": "https://www.maine-et-loire.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Vendée": "https://www.vendee.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueils-des-Actes-Administratifs-{year}",
    "Loire-Atlantique": "https://www.loire-atlantique.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA-en-Loire-Atlantique/{year}/",
    "Mayenne": "https://www.mayenne.gouv.fr/Publications/Recueil-Actes-Administratifs/Annee-{year}",
    "Sarthe": "https://www.sarthe.gouv.fr/Publications/Recueils-des-actes-administratifs",
    "Guadeloupe": "https://www.guadeloupe.gouv.fr/Publications/Le-Recueil-des-actes-administratifs/{year}",
    "Martinique": "https://www.martinique.gouv.fr/Publications/Recueils-des-actes-administratifs-publies",
    "Guyane": "https://www.guyane.gouv.fr/Publications/Recueil-des-actes-administratifs/Annee-{year}",
    "Réunion": "https://www.reunion.gouv.fr/Publications/Publications-administratives-et-legales/Recueil-des-actes-administratifs-RAA/Recueil-des-actes-administratifs-{year}",
    "Mayotte": "https://www.mayotte.gouv.fr/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-{year}",
    "Moselle": "https://www.moselle.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
}


def build_client(department, year):
    """Retourne l'instance du client HTTP du département donné.

    Les constructeurs des clients varient (certains prennent l'année,
    d'autres non) ; cette fabrique centralise cette différence.
    """
    try:
        url = DEPARTMENT_URLS[department].format(year=year)
    except KeyError:
        raise ValueError(f"Département non pris en charge : {department!r}") from None

    if department == "Aisne":
        return AisneRaaClient(url, year)
    if department == "Ardennes":
        return ArdennesRaaClient(url, year)
    if department == "Aube":
        return AubeRaaClient(url, year)
    if department == "Vendée":
        return VendeeRaaClient(url, year)
    if department == "Maine-et-Loire":
        return MaineEtLoireRaaClient(url, year)
    if department == "Sarthe":
        return SartheRaaClient(url, year)
    if department == "Mayenne":
        return MayenneRaaClient(url)
    if department == "Loire-Atlantique":
        return LoireAtlantiqueRaaClient(url)
    if department == "Guadeloupe":
        return GuadeloupeRaaClient(url)
    if department == "Guyane":
        return GuyaneRaaClient(url)
    if department == "Martinique":
        return MartiniqueRaaClient(url, year)
    if department == "Réunion":
        return ReunionRaaClient(url)
    if department == "Mayotte":
        return MayotteRaaClient(url)
    if department == "Moselle":
        return MoselleRaaClient(url, year)
    raise ValueError(f"Département non pris en charge : {department!r}")
