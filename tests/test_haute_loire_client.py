import unittest
from types import SimpleNamespace
from haute_loire_client import HauteLoireRaaClient

BASE_URL = "https://www.haute-loire.gouv.fr/Publications/Recueils-des-actes-administratifs"

SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs/Recueil-des-actes-administratifs-2026">Recueil des actes administratifs 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs/Recueil-des-actes-administratifs-2025">Recueil des actes administratifs 2025</a></h2>
</body></html>
"""

ANNUAL_HTML = """
<html><body>
<a href="/contenu/telechargement/1/1/file/recueil-43-2026-001.pdf">Télécharger recueil-43-2026-001 PDF - 0,11 Mb - 05/01/2026</a>
<a href="/contenu/telechargement/1/2/file/recueil-43-2026-002.pdf">Télécharger recueil-43-2026-002 PDF - 0,11 Mb - 15/01/2026</a>
<a href="/contenu/telechargement/1/3/file/recueil-43-2026-003.pdf">Télécharger recueil-43-2026-003 PDF - 0,10 Mb - 05/02/2026</a>
<a href="/contenu/telechargement/1/4/file/non-raa.pdf">Document quelconque sans date</a>
</body></html>
"""

def fake_get(pages):
    def _get(url):
        for page_url, html in pages.items():
            if url == page_url or url.endswith(page_url):
                return SimpleNamespace(text=html)
        raise Exception(f"URL not found: {url}")
    return _get

class HauteLoireClientTest(unittest.TestCase):
    def setUp(self):
        self.client = HauteLoireRaaClient(BASE_URL, "2026")
        self.pages = {
            BASE_URL: SECTION_HTML,
            BASE_URL + "/Recueil-des-actes-administratifs-2026": ANNUAL_HTML,
        }
        self.client._get = fake_get(self.pages)

    def test_find_annual_page(self):
        self.assertEqual(
            self.client.find_annual_page(), 
            BASE_URL + "/Recueil-des-actes-administratifs-2026"
        )

    def test_documents_for_month_janvier(self):
        result = self.client.documents_for_month("01")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], "recueil-43-2026-001.pdf")
        self.assertEqual(result[1][1], "recueil-43-2026-002.pdf")

    def test_documents_for_month_fevrier(self):
        result = self.client.documents_for_month("02")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "recueil-43-2026-003.pdf")

if __name__ == "__main__":
    unittest.main()
