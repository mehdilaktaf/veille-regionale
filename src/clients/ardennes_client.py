"""Client HTTP (sans navigateur) du RAA de l'Ardennes.

Deux niveaux :
- la page section (…/Recueil-des-actes-administratifs) porte la carte de
  l'année en cours (« Les actes administratifs de l'année 2026 ») et, pour
  les années antérieures, une carte « années antérieures » menant à une
  page de cartes « Les actes administratifs de l'année YYYY » (2025 → 2017,
  puis une carte commune « des années 2015 & 2016 ») ;
- la page annuelle liste directement les liens a.fr-link--download
  (≈ 288/an, sans pagination), chacun portant le span.fr-link__detail
  généré par le CMS (source de vérité). Le nom de fichier
  (« RAA 8-2026-144 du 31 aout 2026.pdf », le 8 = mois) sert de contrôle.

Limite connue : la page commune 2015 & 2016 mélange les deux années — le
filtrage par mois ne distingue pas l'année (documenté au catalogue).
"""

from src.raa_client import AnnualPageRaaClient


class ArdennesRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA de l'Ardennes."""

    def __init__(self, base_url, year, timeout=60):
        needles = [f"l'année {year}"]
        if year in ("2015", "2016"):
            needles.append("années 2015 & 2016")
        super().__init__(
            base_url, needles, timeout, archives_needle="années antérieures"
        )
