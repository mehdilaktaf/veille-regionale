import unittest
from types import SimpleNamespace

from allier_client import AllierRaaClient

BASE_URL = "https://www.allier.gouv.fr/Publications/Recueil-des-actes-administratifs-arretes"
ANNUAL_URL_2026 = f"{BASE_URL}/Recueil-des-actes-administratifs-de-l-annee-2026"

# Page annuelle : liens directs avec span detail
ANNUAL_PAGE_HTML = """
<html><body class="fr-container">
    <div class="fr-col-12 fr-col-md-8">
        <a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/doc1.pdf" target="_blank">
            Télécharger recueil édité le 05 janvier 2026
            <span class="fr-link__detail">PDF - 0,52 Mb - 05/01/2026</span>
        </a>
        <a class="fr-link fr-link--download" href="/contenu/telechargement/1/2/file/doc2.pdf" target="_blank">
            Télécharger recueil spécial édité le 06 janvier 2026
            <span class="fr-link__detail">PDF - 0,20 Mb - 06/01/2026</span>
        </a>
        <a class="fr-link fr-link--download" href="/contenu/telechargement/1/3/file/doc3.pdf" target="_blank">
            Télécharger recueil édité le 05 février 2026
            <span class="fr-link__detail">PDF - 12,70 Mb - 05/02/2026</span>
        </a>
    </div>
</body></html>
"""

def fake_get(pages):
    def _get(url):
        if url in pages:
            return SimpleNamespace(text=pages[url])
        raise Exception(f"URL not found in fake_get: {url}")
    return _get

class AllierClientTest(unittest.TestCase):
    def setUp(self):
        self.client = AllierRaaClient("2026")
        # On injecte la page annuelle directement
        self.client._get = fake_get({ANNUAL_URL_2026: ANNUAL_PAGE_HTML})

    def test_list_documents(self):
        docs = self.client.list_documents()
        self.assertEqual(len(docs), 3)
        self.assertEqual(docs[0][1], "doc1.pdf")
        self.assertEqual(docs[0][2], (5, 1)) # CMS date

    def test_documents_for_month_janvier(self):
        result = self.client.documents_for_month("01")
        self.assertEqual(len(result), 2)
        self.assertEqual([name for _, name in result], ["doc1.pdf", "doc2.pdf"])

    def test_documents_for_month_fevrier(self):
        result = self.client.documents_for_month("02")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "doc3.pdf")

if __name__ == "__main__":
    unittest.main()
