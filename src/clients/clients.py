"""Mapping département -> client HTTP, partagé entre app.py (GUI) et
run.py (CLI).

Source de vérité unique pour l'URL de base et la classe de client de chaque
département, afin que la GUI et le CLI ne divergent pas.
"""

from .ariege_client import AriegeRaaClient
from .aveyron_client import AveyronRaaClient
from .lozere_client import LozereRaaClient
from .gard_client import GardRaaClient
from .herault_client import HeraultRaaClient
from .haute_garonne_client import HauteGaronneRaaClient
from .lot_client import LotRaaClient
from .aude_client import AudeRaaClient
from .essonne_client import EssonneRaaClient
from .haute_corse_client import HauteCorseRaaClient
from .corse_du_sud_client import CorseDuSudRaaClient
from .nord_client import NordRaaClient
from .paris_client import ParisRaaClient
from .pas_de_calais_client import PasDeCalaisRaaClient
from .seine_saint_denis_client import SeineSaintDenisRaaClient
from .val_de_marne_client import ValDeMarneRaaClient
from .vald_oise_client import ValdOiseRaaClient
from .yvelines_client import YvelinesRaaClient
from .gironde_client import GirondeRaaClient
from .pyrenees_atlantiques_client import PyreneesAtlantiquesRaaClient
from .landes_client import LandesRaaClient
from .dordogne_client import DordogneRaaClient
from .lotetgaronne_client import LotEtGaronneRaaClient
from .creuse_client import CreuseRaaClient
from .haute_vienne_client import HauteVienneRaaClient
from .correze_client import CorrezeRaaClient
from .charente_maritime_client import CharenteMaritimeRaaClient
from .deux_sevres_client import DeuxSevresRaaClient
from .somme_client import SommeRaaClient
from .oise_client import OiseRaaClient
from .seine_et_marne_client import SeineEtMarneRaaClient
from .ain_client import AinRaaClient
from .allier_client import AllierRaaClient
from .aisne_client import AisneRaaClient
from .isere_client import IsereRaaClient
from .loire_client import LoireRaaClient
from .haute_loire_client import HauteLoireRaaClient
from .rhone_client import RhoneRaaClient
from .ardeche_client import ArdecheRaaClient
from .savoie_client import SavoieRaaClient
from .puy_de_dome_client import PuyDeDomeRaaClient
from .ardennes_client import ArdennesRaaClient
from .cantal_client import CantalRaaClient
from .drome_client import DromeRaaClient
from .haute_savoie_client import HauteSavoieRaaClient
from .aube_client import AubeRaaClient
from .marne_client import MarneRaaClient
from .haute_marne_client import HauteMarneRaaClient
from .meurthe_et_moselle_client import MeurtheEtMoselleRaaClient
from .meuse_client import MeuseRaaClient
from .bas_rhin_client import BasRhinRaaClient
from .haut_rhin_client import HautRhinRaaClient
from .hauts_de_seine_client import HautsDeSeineRaaClient
from .territoire_de_belfort_client import TerritoireDeBelfortRaaClient
from .jura_client import JuraRaaClient
from .nievre_client import NievreRaaClient
from .saone_et_loire_client import SaoneEtLoireRaaClient
from .yonne_client import YonneRaaClient
from .doubs_client import DoubsRaaClient
from .calvados_client import CalvadosRaaClient
from .eure_client import EureRaaClient
from .manche_client import MancheRaaClient
from .orne_client import OrneRaaClient
from .seine_maritime_client import SeineMaritimeRaaClient
from .vendee_client import VendeeRaaClient
from .maine_et_loire_client import MaineEtLoireRaaClient
from .sarthe_client import SartheRaaClient
from .mayenne_client import MayenneRaaClient
from .loire_atlantique_client import LoireAtlantiqueRaaClient
from .guadeloupe_client import GuadeloupeRaaClient
from .guyane_client import GuyaneRaaClient
from .martinique_client import MartiniqueRaaClient
from .reunion_client import ReunionRaaClient
from .mayotte_client import MayotteRaaClient
from .moselle_client import MoselleRaaClient
from .cote_dor_client import CoteDorRaaClient
from .haute_saone_client import HauteSaoneRaaClient
from .finistere_client import FinistereRaaClient
from .morbihan_client import MorbihanRaaClient
from .cotes_d_armor_client import CotesDArmorRaaClient
from .ille_et_vilaine_client import IlleEtVilaineRaaClient
from .cher_client import CherRaaClient
from .eure_et_loir_client import EureEtLoirRaaClient
from .indre_client import IndreRaaClient
from .indre_et_loire_client import IndreEtLoireRaaClient
from .loiret_client import LoiretRaaClient

# URL de base par département ({year} remplacé par l'année ciblée).
DEPARTMENT_URLS = {
    "Hauts-de-Seine": "https://www.hauts-de-seine.gouv.fr/Publications/Annonces-avis/Le-Recueil-des-actes-administratifs",
    "Ariège": "https://www.ariege.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueils-des-Actes-Administratifs-de-l-Ariege-a-partir-du-28-avril-2015",
    "Aveyron": "https://www.aveyron.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueils-2026",
    "Lozère": "https://www.lozere.gouv.fr/Publications/Recueil-des-Actes-Administratifs-R.A.A",
    "Gard": "https://www.gard.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Hérault": "https://www.herault.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Haute-Garonne": "https://www.haute-garonne.gouv.fr/Publications/Recueil-des-Actes-Administratifs/Recueil-des-Actes-Administratifs-Haute-Garonne",
    "Lot": "https://www.lot.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Aude": "https://www.aude.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA/Annee-{year}",
    "Aisne": "https://www.aisne.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Allier": "https://www.allier.gouv.fr/Publications/Recueil-des-actes-administratifs-arretes",
    "Ain": "https://www.ain.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA/Recueil-des-actes-administratifs-{year}",
    "Isère": "https://www.isere.gouv.fr/Publications/RAA-Recueil-des-actes-administratifs/Recueils-des-Actes-Administratifs-de-la-prefecture-de-l-Isere-{year}",
    "Ardèche": "https://www.ardeche.gouv.fr/Publications/Recueil-des-actes-administratifs/RAA-{year}",
    "Cantal": "https://www.cantal.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Drôme": "https://www.drome.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA/RAA-{year}-consulter-le-recueil-des-services-de-l-Etat-dans-la-Drome",
    "Haute-Savoie": "https://www.haute-savoie.gouv.fr/Publications/Actes-administratifs",
    "Ardennes": "https://www.ardennes.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Aube": "https://www.aube.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA2",
    "Marne": "https://www.marne.gouv.fr/Publications/Publications-administratives-et-legales/RAA-Recueils-des-actes-administratifs/RAA-Recueils-des-actes-administratifs-de-la-prefecture-de-la-Marne",
    "Haute-Marne": "https://www.haute-marne.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA",
    "Meurthe-et-Moselle": "https://www.meurthe-et-moselle.gouv.fr/Publications/Recueils-des-actes-administratifs",
    "Meuse": "https://www.meuse.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA",
    "Bas-Rhin": "https://www.bas-rhin.gouv.fr/Publications/Publications-officielles/RAA-Recueils-des-actes-administratifs",
    "Haut-Rhin": "https://www.haut-rhin.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Territoire de Belfort": "https://www.territoire-de-belfort.gouv.fr/Publications/Le-recueil-des-actes-administratifs",
    "Jura": "https://www.jura.gouv.fr/Publications/Publications-legales/Recueil-des-Actes-Administratifs",
    "Nièvre": "https://www.nievre.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Saône-et-Loire": "https://www.saone-et-loire.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Yonne": "https://www.yonne.gouv.fr/Publications/Publications-legales/Recueil-des-actes-administratifs",
    "Doubs": "https://www.doubs.gouv.fr/Publications/Publications-Legales/Recueil-des-Actes-Administratifs-RAA",
    "Calvados": "https://www.calvados.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-departemental",
    "Eure": "https://www.eure.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA",
    "Manche": "https://www.manche.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Orne": "https://www.orne.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA",
    "Seine-Maritime": "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-{year}",
    "Paris": "https://www.prefectures-regions.gouv.fr/ile-de-france/Documents-publications/Recueil-des-actes-administratifs/Raa-du-departement-de-Paris-{year}",
    "Maine-et-Loire": "https://www.maine-et-loire.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Vendée": "https://www.vendee.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueils-des-Actes-Administratifs-{year}",
    "Loire-Atlantique": "https://www.loire-atlantique.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA-en-Loire-Atlantique/{year}/",
    "Mayenne": "https://www.mayenne.gouv.fr/Publications/Recueil-Actes-Administratifs/Annee-{year}",
    "Sarthe": "https://www.sarthe.gouv.fr/Publications/Recueils-des-actes-administratifs",
    "Loire": "https://www.loire.gouv.fr/Publications/Publications-legales/Recueil-des-Actes-Administratifs",
    "Haute-Loire": "https://www.haute-loire.gouv.fr/Publications/Recueils-des-actes-administratifs",
    "Rhône": "https://www.rhone.gouv.fr/Publications/Recueil-des-actes-administratifs-du-Rhone-RAA",
    "Savoie": "https://www.savoie.gouv.fr/Publications/Recueils-hebdomadaires-et-speciaux-des-actes-administratifs",
    "Puy-de-Dôme": "https://www.puy-de-dome.gouv.fr/Publications/Recueils-des-actes-administratifs",
    "Guadeloupe": "https://www.guadeloupe.gouv.fr/Publications/Le-Recueil-des-actes-administratifs/{year}",
    "Martinique": "https://www.martinique.gouv.fr/Publications/Recueils-des-actes-administratifs-publies",
    "Guyane": "https://www.guyane.gouv.fr/Publications/Recueil-des-actes-administratifs/Annee-{year}",
    "Réunion": "https://www.reunion.gouv.fr/Publications/Publications-administratives-et-legales/Recueil-des-actes-administratifs-RAA/Recueil-des-actes-administratifs-{year}",
    "Mayotte": "https://www.mayotte.gouv.fr/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-{year}",
    "Moselle": "https://www.moselle.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Côte-d'Or": "https://www.cote-dor.gouv.fr/Publications/Recueils-des-Actes-Administratifs/Recueils-des-actes-administratifs-de-l-annee-en-cours",
    "Haute-Saône": "https://www.haute-saone.gouv.fr/Publications/RAA",
    "Finistère": "https://www.finistere.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Morbihan": "https://www.morbihan.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA",
    "Côtes-d'Armor": "https://www.cotes-darmor.gouv.fr/index.php/Publications/Recueil-des-actes-administratifs",
    "Ille-et-Vilaine": "https://www.ille-et-vilaine.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Cher": "https://www.cher.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA-Arretes-et-circulaires/Recueil-des-actes-administratifs",
    "Eure-et-Loir": "https://www.eure-et-loir.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Indre": "https://www.indre.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Indre-et-Loire": "https://www.indre-et-loire.gouv.fr/Publications/Recueil-actes-administratifs",
    "Loiret": "https://www.loiret.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-departementaux",
    "Nord": "https://www.nord.gouv.fr/Publications/Recueils-des-actes-administratifs",
    "Pas-de-Calais": "https://www.pas-de-calais.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Somme": "https://www.somme.gouv.fr/Publications/Recueil-des-actes-administratifs-du-departement-de-la-Somme",
    "Oise": "https://www.oise.gouv.fr/Publications/Publications-legales/Recueils-des-actes-administratifs-RAA",
    "Seine-et-Marne": "https://www.seine-et-marne.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA",
    "Seine-Saint-Denis": "https://www.seine-saint-denis.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Val-de-Marne": "https://www.val-de-marne.gouv.fr/Publications/Publications-legales/RAA-Recueil-des-actes-administratifs",
    "Val-d'Oise": "https://www.val-doise.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Yvelines": "https://www.yvelines.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Gironde": "https://www.gironde.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
    "Pyrénées-Atlantiques": "https://www.pyrenees-atlantiques.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Landes": "https://www.landes.gouv.fr/Publications/Publications-legales/Le-Recueil-des-Actes-Administratifs-RAA",
    "Dordogne": "https://www.dordogne.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Lot-et-Garonne": "https://www.lot-et-garonne.gouv.fr/Publications/Publications-legales/RAA",
    "Creuse": "https://www.creuse.gouv.fr/Publications/Les-Recueils-des-actes-administratifs",
    "Haute-Vienne": "https://www.haute-vienne.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Corrèze": "https://www.correze.gouv.fr/Publications/Recueil-des-actes-administratifs",
    "Charente-Maritime": "https://www.charente-maritime.gouv.fr/Publications/RAA-Recueil-des-Actes-Administratifs",
    "Deux-Sèvres": "https://www.deux-sevres.gouv.fr/Publications/Le-Recueil-des-actes-administratifs/Annee-{year}",
    "Essonne": "https://www.essonne.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/{year}",
    "Haute-Corse": "https://www.haute-corse.gouv.fr/Publications/Publications-administratives-et-legales/Recueils-des-actes-administratifs",
    "Corse-du-Sud": "https://www.corse-du-sud.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-de-la-prefecture-de-la-Corse-du-Sud",
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

    if department == "Ariège":
        return AriegeRaaClient(url)
    if department == "Aveyron":
        return AveyronRaaClient(url)
    if department == "Lozère":
        return LozereRaaClient(url, year)
    if department == "Gard":
        return GardRaaClient(url)
    if department == "Hérault":
        return HeraultRaaClient(url)
    if department == "Haute-Garonne":
        return HauteGaronneRaaClient(url)
    if department == "Lot":
        return LotRaaClient(url, year)
    if department == "Aude":
        return AudeRaaClient(url)
    if department == "Paris":
        return ParisRaaClient(url)
    if department == "Hauts-de-Seine":
        return HautsDeSeineRaaClient(url, year)
    if department == "Ain":
        return AinRaaClient(url)
    if department == "Allier":
        return AllierRaaClient(url, year)
    if department == "Isère":
        return IsereRaaClient(url, year)
    if department == "Ardèche":
        return ArdecheRaaClient(url)
    if department == "Cantal":
        return CantalRaaClient(url, year)
    if department == "Drôme":
        return DromeRaaClient(url)
    if department == "Haute-Savoie":
        return HauteSavoieRaaClient(url, year)
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
    if department == "Jura":
        return JuraRaaClient(url, year)
    if department == "Nièvre":
        return NievreRaaClient(url, year)
    if department == "Saône-et-Loire":
        return SaoneEtLoireRaaClient(url, year)
    if department == "Yonne":
        return YonneRaaClient(url, year)
    if department == "Doubs":
        return DoubsRaaClient(url, year)
    if department == "Calvados":
        return CalvadosRaaClient(url, year)
    if department == "Eure":
        return EureRaaClient(url, year)
    if department == "Manche":
        return MancheRaaClient(url, year)
    if department == "Orne":
        return OrneRaaClient(url, year)
    if department == "Seine-Maritime":
        return SeineMaritimeRaaClient(url)
    if department == "Vendée":
        return VendeeRaaClient(url, year)
    if department == "Maine-et-Loire":
        return MaineEtLoireRaaClient(url, year)
    if department == "Sarthe":
        return SartheRaaClient(url, year)
    if department == "Loire":
        return LoireRaaClient(url, year)
    if department == "Haute-Loire":
        return HauteLoireRaaClient(url, year)
    if department == "Rhône":
        return RhoneRaaClient(url, year)
    if department == "Savoie":
        return SavoieRaaClient(url, year)
    if department == "Puy-de-Dôme":
        return PuyDeDomeRaaClient(url, year)
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
    if department == "Côte-d'Or":
        return CoteDorRaaClient(url, year)
    if department == "Haute-Saône":
        return HauteSaoneRaaClient(url, year)
    if department == "Finistère":
        return FinistereRaaClient(url)
    if department == "Morbihan":
        return MorbihanRaaClient(url, year)
    if department == "Côtes-d'Armor":
        return CotesDArmorRaaClient(url, year)
    if department == "Ille-et-Vilaine":
        return IlleEtVilaineRaaClient(url)
    if department == "Cher":
        return CherRaaClient(url)
    if department == "Eure-et-Loir":
        return EureEtLoirRaaClient(url)
    if department == "Indre":
        return IndreRaaClient(url)
    if department == "Indre-et-Loire":
        return IndreEtLoireRaaClient(url)
    if department == "Loiret":
        return LoiretRaaClient(url, year)
    if department == "Nord":
        return NordRaaClient(url, year)
    if department == "Pas-de-Calais":
        return PasDeCalaisRaaClient(url)
    if department == "Somme":
        return SommeRaaClient(url)
    if department == "Oise":
        return OiseRaaClient(url)
    if department == "Seine-et-Marne":
        return SeineEtMarneRaaClient(url, year)
    if department == "Seine-Saint-Denis":
        return SeineSaintDenisRaaClient(url, year)
    if department == "Val-de-Marne":
        return ValDeMarneRaaClient(url, year)
    if department == "Val-d'Oise":
        return ValdOiseRaaClient(url, year)
    if department == "Yvelines":
        return YvelinesRaaClient(url, year)
    if department == "Gironde":
        return GirondeRaaClient(url, year)
    if department == "Pyrénées-Atlantiques":
        return PyreneesAtlantiquesRaaClient(url, year)
    if department == "Landes":
        return LandesRaaClient(url, year)
    if department == "Dordogne":
        return DordogneRaaClient(url, year)
    if department == "Lot-et-Garonne":
        return LotEtGaronneRaaClient(url, year)
    if department == "Creuse":
        return CreuseRaaClient(url, year)
    if department == "Haute-Vienne":
        return HauteVienneRaaClient(url, year)
    if department == "Corrèze":
        return CorrezeRaaClient(url, year)
    if department == "Charente-Maritime":
        return CharenteMaritimeRaaClient(url, year)
    if department == "Deux-Sèvres":
        return DeuxSevresRaaClient(url)
    if department == "Essonne":
        return EssonneRaaClient(url)
    if department == "Haute-Corse":
        return HauteCorseRaaClient(url, year)
    if department == "Corse-du-Sud":
        return CorseDuSudRaaClient(url, year)
    raise ValueError(f"Département non pris en charge : {department!r}")
