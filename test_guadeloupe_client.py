import unittest
from types import SimpleNamespace

from guadeloupe_client import GuadeloupeRaaClient

BASE_URL = (
    "https://www.guadeloupe.gouv.fr/Publications/"
    "Le-Recueil-des-actes-administratifs/2026"
)

ANNUAL_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Le-Recueil-des-actes-administratifs/2026/Janvier-2026">Janvier 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Le-Recueil-des-actes-administratifs/2026/Fevrier-2026">Février 2026</a></h2>
</body></html>
"""

# Le mois CMS (span) fait foi : un doc daté du 02/02 est posté sur la
# page de janvier.
MONTH_JANVIER_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/RAA N° 971-2026-005 publié le 31 janvier 2026.pdf">
<span class="fr-link__detail">PDF - 3,45 Mb - 31/01/2026</span>Télécharger</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/2/2/file/RAA N° 971-2026-006 publié le 02 février 2026.pdf">
<span class="fr-link__detail">PDF - 2,83 Mb - 02/02/2026</span>Télécharger</a>
</body></html>
"""

MONTH_FEVRIER_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/3/3/file/RAA N° 971-2026-007 publié le 03 février 2026.pdf">
<span class="fr-link__detail">PDF - 1,20 Mb - 03/02/2026</span>Télécharger</a>
</body></html>
"""


class GuadeloupeClientTest(unittest.TestCase):
    def setUp(self):
        self.client = GuadeloupeRaaClient(BASE_URL)
        pages = {
            BASE_URL: ANNUAL_HTML,
            BASE_URL + "/Janvier-2026": MONTH_JANVIER_HTML,
            BASE_URL + "/Fevrier-2026": MONTH_FEVRIER_HTML,
        }
        self.client._get = lambda url: SimpleNamespace(text=pages[url])

    def test_list_documents_balaie_tout(self):
        self.assertEqual(len(self.client.list_documents()), 3)

    def test_mois_cms_fait_foi(self):
        janvier = self.client.documents_for_month("01")
        self.assertEqual(
            [name for _, name in janvier],
            ["RAA N° 971-2026-005 publié le 31 janvier 2026.pdf"],
        )
        fevrier = self.client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in fevrier],
            [
                "RAA N° 971-2026-006 publié le 02 février 2026.pdf",
                "RAA N° 971-2026-007 publié le 03 février 2026.pdf",
            ],
        )


if __name__ == "__main__":
    unittest.main()
