import unittest
from types import SimpleNamespace

from reunion_client import ReunionRaaClient

DOMAIN = "https://www.reunion.gouv.fr"
BASE_URL = (
    DOMAIN + "/Publications/"
    "Publications-administratives-et-legales/"
    "Recueil-des-actes-administratifs-RAA/Recueil-des-actes-administratifs-2026"
)
ANNUAL_SLUG = "/Publications/Publications-administratives-et-legales/Recueil-des-actes-administratifs-RAA/Recueil-des-actes-administratifs-2026"

# Page 1 : séparateur de mois (sans date) + cartes RAA d'août et de juillet
PAGE1_HTML = f"""
<html><body>
<h2 class="fr-card__title"><a href="{ANNUAL_SLUG}/AOUT">AOUT</a></h2>
<h2 class="fr-card__title"><a href="{ANNUAL_SLUG}/Special-n-169-du-27-aout-2026">Spécial n° 169 du 27 août 2026</a></h2>
<h2 class="fr-card__title"><a href="{ANNUAL_SLUG}/RAA-n-100-du-05-juillet-2026">RAA n° 100 du 05 juillet 2026</a></h2>
<ul class="fr-pagination__list">
<li><a href="{ANNUAL_SLUG}/(offset)/10">Suivant</a></li>
</ul>
</body></html>
"""

PAGE2_HTML = f"""
<html><body>
<h2 class="fr-card__title"><a href="{ANNUAL_SLUG}/Special-n-170-du-28-aout-2026">Spécial n° 170 du 28 août 2026</a></h2>
</body></html>
"""

# La carte de juillet n'est PAS suivie (pré-filtre sur le mois de carte) :
# sa page n'est pas dans le dictionnaire → KeyError si on la demande.
DOC_169_HTML = f"""
<html><body>
<a class="fr-link fr-link--download" href="{ANNUAL_SLUG}/file/arrete-1415-sentiers.pdf">
<span class="fr-link__detail">PDF - 0,65 Mb - 27/08/2026</span>Télécharger</a>
<a class="fr-link fr-link--download" href="{ANNUAL_SLUG}/file/arrete-1416-coderst.pdf">
<span class="fr-link__detail">PDF - 0,94 Mb - 27/08/2026</span>Télécharger</a>
</body></html>
"""

DOC_170_HTML = f"""
<html><body>
<a class="fr-link fr-link--download" href="{ANNUAL_SLUG}/file/arrete-1500.pdf">
<span class="fr-link__detail">PDF - 0,5 Mb - 28/08/2026</span>Télécharger</a>
</body></html>
"""


class ReunionClientTest(unittest.TestCase):
    def setUp(self):
        self.client = ReunionRaaClient(BASE_URL)
        self.pages = {
            BASE_URL: PAGE1_HTML,
            BASE_URL + "/(offset)/10": PAGE2_HTML,
            DOMAIN + ANNUAL_SLUG + "/Special-n-169-du-27-aout-2026": DOC_169_HTML,
            DOMAIN + ANNUAL_SLUG + "/Special-n-170-du-28-aout-2026": DOC_170_HTML,
        }
        self.client._get = lambda url: SimpleNamespace(text=self.pages[url])

    def test_prefiltre_par_mois_de_carte(self):
        documents = self.client.list_documents("08")
        self.assertEqual(
            sorted(name for _, name, _, _ in documents),
            ["arrete-1415-sentiers.pdf", "arrete-1416-coderst.pdf", "arrete-1500.pdf"],
        )

    def test_documents_for_month(self):
        result = self.client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            [
                "arrete-1415-sentiers.pdf",
                "arrete-1416-coderst.pdf",
                "arrete-1500.pdf",
            ],
        )

    def test_mois_vide(self):
        self.assertEqual(self.client.documents_for_month("06"), [])


if __name__ == "__main__":
    unittest.main()
