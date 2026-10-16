"""Client HTTP (sans navigateur) du RAA de la Haute-Marne.

Deux niveaux :
- la page section (…/Recueil-des-actes-administratifs-RAA) porte des
  cartes « Année YYYY » (2026 → 2017, pas de carte archives visible) ;
- la page annuelle liste directement les liens de téléchargement, sans
  pagination ni cartes mois. Deux markups selon l'époque :
  - années récentes (2026) : liens a.fr-link plain, URL absolue, **sans
    span CMS** — la date n'est que dans le libellé/nom (« RAA n° 93 du
    28-08-2026.pdf », coquilles tolérées : année sur 2 chiffres « 30-06-26 »,
    tiret final « 31-07-2026-.pdf ») ;
  - années anciennes (2017) : liens a.fr-link--download + span.fr-link__detail
    CMS (source de vérité).
"""

from src.raa_client import AnnualPageRaaClient


class HauteMarneRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA de la Haute-Marne."""

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, f"Année {year}", timeout)
