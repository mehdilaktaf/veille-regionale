import unittest
from types import SimpleNamespace

from calvados_client import CalvadosRaaClient

DEPTAL_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-departemental/2026">2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-departemental/2025">2025</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-departemental/Archives">Archives</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/Recueil-des-actes-administratifs-departemental/2018">2018</a></h2>
</body></html>
"""

ANNUAL_2026_HTML = """
<html><body>
<div class="fr-col-12 fr-col-md-8">
<a class="fr-link fr-link--download" href="/contenu/telechargement/32317/232916/file/recueil-14-2026-369-recueil-des-actes-administratifs.pdf">
<span class="fr-link__detail">PDF - 0,21 Mb - 01/09/2026</span></a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/31000/230000/file/recueil-14-2026-042-recueil-des-actes-administratifs.pdf">
<span class="fr-link__detail">PDF - 1,10 Mb - 27/02/2026</span></a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/30000/220000/file/202602_AP_delegation_signature.pdf">
<span class="fr-link__detail">PDF - 0,08 Mb - 03/02/2026</span></a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/29000/210000/file/recueil-14-2026-041-recueil-des-actes-administratifs.pdf">
<span class="fr-link__detail">PDF - 0,95 Mb - 20/02/2026</span></a>
</div>
</body></html>
"""

DOMAIN = "https://www.calvados.gouv.fr"
BASE_URL = (
    DOMAIN + "/Publications/Recueil-des-actes-administratifs"
    "/Recueil-des-actes-administratifs-departemental"
)


class CalvadosClientTest(unittest.TestCase):
    def setUp(self):
        self.client = CalvadosRaaClient(BASE_URL, "2026")
        pages = {
            BASE_URL: DEPTAL_HTML,
            BASE_URL + "/2026": ANNUAL_2026_HTML,
        }
        self.client._get = lambda url: SimpleNamespace(text=pages[url])

    def test_card_needle(self):
        self.assertEqual(self.client.card_needle, "2026")
        self.assertEqual(self.client.archives_needle, "Archives")

    def test_find_annual_page(self):
        self.assertEqual(
            self.client.find_annual_page(), BASE_URL + "/2026"
        )

    def test_list_documents(self):
        documents = self.client.list_documents()
        self.assertEqual(len(documents), 4)
        self.assertEqual(
            documents[0][1],
            "recueil-14-2026-369-recueil-des-actes-administratifs.pdf",
        )
        self.assertEqual(documents[0][2], (1, 9))

    def test_documents_for_month_fevrier(self):
        # L'AP non-RAA datée CMS du 03/02 est incluse (règle M49) ;
        # ordre chronologique (jour, nom).
        self.assertEqual(
            self.client.documents_for_month("02"),
            [
                (DOMAIN + "/contenu/telechargement/30000/220000/file/202602_AP_delegation_signature.pdf",
                 "202602_AP_delegation_signature.pdf"),
                (DOMAIN + "/contenu/telechargement/29000/210000/file/recueil-14-2026-041-recueil-des-actes-administratifs.pdf",
                 "recueil-14-2026-041-recueil-des-actes-administratifs.pdf"),
                (DOMAIN + "/contenu/telechargement/31000/230000/file/recueil-14-2026-042-recueil-des-actes-administratifs.pdf",
                 "recueil-14-2026-042-recueil-des-actes-administratifs.pdf"),
            ],
        )

    def test_documents_for_month_vide(self):
        self.assertEqual(self.client.documents_for_month("12"), [])


if __name__ == "__main__":
    unittest.main()
