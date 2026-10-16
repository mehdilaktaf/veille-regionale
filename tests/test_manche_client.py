import unittest
from types import SimpleNamespace

from manche_client import MancheRaaClient

BASE_URL = "https://www.manche.gouv.fr/Publications/Recueil-des-actes-administratifs"

# Page section : cartes années à texte exact « YYYY » (coquilles de slug
# 2021 → /20212, 2020 → /20202 : la navigation est par le texte).
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/2026">2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/20212">2021</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/20202">2020</a></h2>
</body></html>
"""

# Page annuelle paginée : préfixes numériques non fiables (« 10. »
# manquant, « 11. Septembre »), carte non-mois « Délégations ».
ANNUAL_PAGE_1_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/2026/1.-Janvier">1. Janvier</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/2026/2.-Delegations-de-signatures-du-Prefet-de-la-Manche">2. Délégations de signatures du Préfet de la Manche</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/2026/3.-Fevrier">3. Février</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/2026/4.-Mars">4. Mars</a></h2>
<ul class="fr-pagination__list"><li><a href="/Publications/Recueil-des-actes-administratifs/2026/(offset)/10">Suivant</a></li></ul>
</body></html>
"""

ANNUAL_PAGE_2_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/2026/11.-Septembre">11. Septembre</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/2026/12.-Octobre">12. Octobre</a></h2>
</body></html>
"""

# Page de carte mois : liens a.fr-link plain (sans span fr-link__detail
# en 2026), date de publication dans le texte du lien. Le « RAA mensuel »
# de février est publié le 05/03 (M+1).
FEBRIER_HTML = """
<html><body>
<a class="fr-link" href="/contenu/telechargement/1/2/file/RAA spécial 50-2026-038.pdf">Télécharger RAA spécial 50-2026-038.pdf PDF - 0,42 Mb - 20/02/2026</a>
<a class="fr-link" href="/contenu/telechargement/1/2/file/RAA mensuel Février 2026 50-2026-047.pdf">Télécharger RAA mensuel Février 2026 50-2026-047.pdf PDF - 24,44 Mb - 05/03/2026</a>
</body></html>
"""

# Page Janvier : lien au nom de fichier en slug (sans date), texte du lien
# avec « publié le » (sans espace avant l'année, coquille du CMS).
JANVIER_HTML = """
<html><body>
<a class="fr-link" href="/contenu/telechargement/1/2/file/recueil-50-2026-002-recueil-des-actes-administratifs.pdf">Télécharger RAA n°50-2026-002 publié le 2 janvier2026 PDF - 0,25 Mb - 02/01/2026</a>
</body></html>
"""

MARS_HTML = """
<html><body>
<a class="fr-link" href="/contenu/telechargement/1/2/file/RAA spécial 50-2026-050.pdf">Télécharger RAA spécial 50-2026-050.pdf PDF - 0,30 Mb - 05/03/2026</a>
</body></html>
"""

# Carte non-mois : porte des RAA absents des cartes mois (n°013 n'est que
# là, pas sur la page Janvier).
DELEGATIONS_HTML = """
<html><body>
<a class="fr-link" href="/contenu/telechargement/1/2/file/RAA Spécial délégation de signature 50-2026-042.pdf">Télécharger RAA Spécial délégation de signature 50-2026-042.pdf PDF - 0,15 Mb - 18/02/2026</a>
<a class="fr-link" href="/contenu/telechargement/1/2/file/RAA Spécial délégation de signature 50-2026-013.pdf">Télécharger RAA Spécial délégation de signature 50-2026-013.pdf PDF - 0,15 Mb - 12/01/2026</a>
</body></html>
"""

# Année ancienne éventuelle : liens directs sur la page annuelle (span CMS).
ANNUAL_DIRECT_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/1/2/file/recueil-50-2020-010.pdf">Télécharger recueil-50-2020-010.pdf <span class="fr-link__detail">PDF - 1,02 Mb - 10/02/2020</span></a>
</body></html>
"""

SECTION_2020_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/20202">2020</a></h2>
</body></html>
"""


def fake_get(pages):
    def _get(url):
        if url not in pages:
            raise AssertionError(f"URL non prévue : {url}")
        return SimpleNamespace(text=pages[url])
    return _get


def pages_2026():
    return {
        BASE_URL: SECTION_HTML,
        BASE_URL + "/2026": ANNUAL_PAGE_1_HTML,
        BASE_URL + "/2026/(offset)/10": ANNUAL_PAGE_2_HTML,
        BASE_URL + "/2026/1.-Janvier": JANVIER_HTML,
        BASE_URL + "/2026/3.-Fevrier": FEBRIER_HTML,
        BASE_URL + "/2026/4.-Mars": MARS_HTML,
        BASE_URL + "/2026/2.-Delegations-de-signatures-du-Prefet-de-la-Manche": DELEGATIONS_HTML,
    }


class MancheClientTest(unittest.TestCase):
    def setUp(self):
        self.client = MancheRaaClient(BASE_URL, "2026")
        self.client._get = fake_get(pages_2026())

    def test_find_annual_page(self):
        self.assertEqual(
            self.client.find_annual_page(), BASE_URL + "/2026"
        )

    def test_card_month(self):
        self.assertEqual(self.client._card_month("3. Février"), "02")
        self.assertIsNone(self.client._card_month("2. Délégations de signatures du Préfet de la Manche"))
        self.assertEqual(self.client._card_month("11. Septembre"), "09")
        self.assertEqual(self.client._card_month("14. Décembre"), "12")

    def test_documents_for_month_fevrier(self):
        # 038 (20/02) + mensuel (publié 05/03 → début de mois) + n°042 de
        # la carte « Délégations » (18/02, balayeur) ; le n°013 (12/01)
        # est exclu. Ordre (jour, nom) : mensuel, 042, 038.
        result = self.client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            [
                "RAA mensuel Février 2026 50-2026-047.pdf",
                "RAA Spécial délégation de signature 50-2026-042.pdf",
                "RAA spécial 50-2026-038.pdf",
            ],
        )

    def test_mensuel_publie_m_plus_1_conserve(self):
        # Le mensuel de février (publié le 05/03) ne doit pas passer en
        # mars : le mois de la carte fait foi.
        fevrier = [name for _, name in self.client.documents_for_month("02")]
        self.assertIn("RAA mensuel Février 2026 50-2026-047.pdf", fevrier)
        mars = [name for _, name in self.client.documents_for_month("03")]
        self.assertNotIn("RAA mensuel Février 2026 50-2026-047.pdf", mars)

    def test_balayeur_carte_sans_mois(self):
        # Le n°013 (12/01, absent de la page Janvier) est trouvé au
        # balayeur de la carte « Délégations » pour le mois 01.
        self.assertEqual(
            [name for _, name in self.client.documents_for_month("01")],
            [
                "recueil-50-2026-002-recueil-des-actes-administratifs.pdf",
                "RAA Spécial délégation de signature 50-2026-013.pdf",
            ],
        )

    def test_autres_mois_non_visites(self):
        # Seul le mois cible + les cartes sans mois sont visitées : les
        # pages Janvier/Mars/Septembre/Octobre ne sont pas dans la map de
        # fake_get → AssertionError si visitées.
        self.client.documents_for_month("02")

    def test_mois_vide(self):
        self.assertEqual(self.client.documents_for_month("05"), [])

    def test_annee_ancienne_liens_directs(self):
        # Page annuelle sans carte : liens directs collectés, span CMS
        # faisant foi.
        client = MancheRaaClient(BASE_URL, "2020")
        client._get = fake_get(
            {
                BASE_URL: SECTION_2020_HTML,
                BASE_URL + "/20202": ANNUAL_DIRECT_HTML,
            }
        )
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result], ["recueil-50-2020-010.pdf"]
        )


if __name__ == "__main__":
    unittest.main()
