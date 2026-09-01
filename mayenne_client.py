"""Client HTTP (sans navigateur) du RAA de la Mayenne.

La page annuelle (/Annee-YYYY) présente deux layouts :
- années récentes : des cartes « Mois YYYY » (h2.fr-card__title) menant
  à une page par mois ;
- années plus anciennes : les liens de téléchargement directement sur la
  page annuelle.

Sources de date par lien, par ordre de préférence :
1. le span.fr-link__detail généré par le CMS (présent sur une partie
   des liens) ;
2. le texte du lien, ancré sur « du » (« RAA spécial du 28 août 2026 »).
Les fichiers sans date (recueil-53-2026-XXX-...) ne peuvent être classés
ni vérifiés : ils sont exclus avec un warning.
Un même fichier peut être posté deux fois (ré-upload) : en cas de
doublon de nom, l'entrée datée par le CMS est conservée.
"""

from raa_client import MonthCardsRaaClient


class MayenneRaaClient(MonthCardsRaaClient):
    """Client HTTP du RAA de la Mayenne."""
