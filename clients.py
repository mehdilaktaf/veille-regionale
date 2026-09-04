"""Mapping département -> client HTTP, partagé entre app.py (GUI) et
run.py (CLI).

Source de vérité unique pour l'URL de base et la classe de client de chaque
département, afin que la GUI et le CLI ne divergent pas.
"""

from aisne_client import AisneRaaClient
from ardennes_client import ArdennesRaaClient
from aube_client import AubeRaaClient
from marne_client import MarneRaaClient
from haute_marne_client import HauteMarneRaaClient
from meurthe_et_moselle_client import MeurtheEtMoselleRaaClient
from meuse_client import MeuseRaaClient
from bas_rhin_client import BasRhinRaaClient
from haut_rhin_client import HautRhinRaaClient
from territoire_de_belfort_client import TerritoireDeBelfortRaaClient
from calvados_client import CalvadosRaaClient
from eure_client import EureRaaClient
from manche_client import MancheRaaClient
from orne_client import OrneRaaClient
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
    "Marne": "https://www.marne.gouv.fr/Publications/Publications-administratives-et-legales/RAA-Recueils-des-actes-administratifs/RAA-Recueils-des-actes-administratifs-de-la-prefecture-de-la-Marne",
    "Haute-Marne": "https://www.haute-marne.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA",
    "Meurthe-et-Moselle": "https://www.meurthe-et-moselle.gouv.fr/Publications/Recueils-des-actes-administratifs",
    "Meuse": "https://www.meuse.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA",
    "Bas-Rhin": "https://www.bas-rhin.gouv.fr/Publications/Publications-officielles/RAA-Recueils-des-actes-administratifs",
    "Haut-Rhin": "https://www.haut-rhin.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Territoire de Belfort": "https://www.territoire-de-belfort.gouv.fr/Publications/Le-recueil-des-actes-administratifs",
    "Calvados": "https://www.calvados.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-departemental",
    "Eure": "https://www.eure.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA",
    "Manche": "https://www.manche.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Orne": "https://www.orne.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA",
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
    if department == "Marne":
        return MarneRaaClient(url, year)
    if department == "Haute-Marne":
        return HauteMarneRaaClient(url, year)
    if department == "Meurthe-et-Moselle":
        return MeurtheEtMoselleRaaClient(url, year)
    if department == "Meuse":
        return MeuseRaaClient(url, year)
    if department == "Bas-Rhin":
        return BasRhinRaaClient(url, year)
    if department == "Haut-Rhin":
        return HautRhinRaaClient(url, year)
    if department == "Territoire de Belfort":
        return TerritoireDeBelfortRaaClient(url, year)
    if department == "Calvados":
        return CalvadosRaaClient(url, year)
    if department == "Eure":
        return EureRaaClient(url, year)
    if department == "Manche":
        return MancheRaaClient(url, year)
    if department == "Orne":
        return OrneRaaClient(url, year)
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
