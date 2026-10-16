import unittest
from types import SimpleNamespace

from sarthe_client import SartheRaaClient

PUBLICATIONS_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs/Recueil-des-actes-administratifs-RAA-Sarthe-2026">Recueil des actes administratifs (RAA) - Sarthe - 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs/Recueil-des-actes-administratifs-RAA-Sarthe-2025">Recueil des actes administratifs (RAA) - Sarthe - 2025</a></h2>
</body></html>
"""

ANNUAL_2026_HTML = """
<html><body>
<div class="fr-col-12 fr-col-md-8">
<a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/RAA n°194 du 26 août 2026.pdf">
<span class="fr-link__detail">PDF - 1,26 Mb - 26/08/2026</span></a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/2/2/file/RAA n°195 du 05 septembre 2026.pdf">
<span class="fr-link__detail">PDF - 1,14 Mb - 05/09/2026</span></a>
</div>
</body></html>
"""

DOMAIN = "https://www.sarthe.gouv.fr"
BASE_URL = DOMAIN + "/Publications/Recueils-des-actes-administratifs"


class SartheClientTest(unittest.TestCase):
    def setUp(self):
        self.client = SartheRaaClient(BASE_URL, "2026")
        pages = {
            BASE_URL: PUBLICATIONS_HTML,
            BASE_URL + "/Recueil-des-actes-administratifs-RAA-Sarthe-2026": ANNUAL_2026_HTML,
        }
        self.client._get = lambda url: SimpleNamespace(text=pages[url])

    def test_card_needle(self):
        self.assertEqual(self.client.card_needle, "Sarthe - 2026")

    def test_find_annual_page(self):
        self.assertEqual(
            self.client.find_annual_page(),
            BASE_URL + "/Recueil-des-actes-administratifs-RAA-Sarthe-2026",
        )

    def test_list_documents(self):
        documents = self.client.list_documents()
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0][1], "RAA n°194 du 26 août 2026.pdf")
        self.assertEqual(documents[0][2], (26, 8))

    def test_documents_for_month_aout(self):
        self.assertEqual(
            self.client.documents_for_month("08"),
            [(DOMAIN + "/contenu/telechargement/1/1/file/RAA n°194 du 26 août 2026.pdf",
              "RAA n°194 du 26 août 2026.pdf")],
        )

    def test_documents_for_month_vide(self):
        self.assertEqual(self.client.documents_for_month("01"), [])


if __name__ == "__main__":
    unittest.main()
