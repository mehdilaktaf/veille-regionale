import unittest
from types import SimpleNamespace
from loire_client import LoireRaaClient

BASE_URL = "https://www.loire.gouv.fr/Publications/Publications-legales/Recueil-des-Actes-Administratifs"

SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Publications-legales/Recueil-des-Actes-Administratifs/2026-numeros-speciaux">2026 numéros spéciaux</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Publications-legales/Recueil-des-Actes-Administratifs/2026-numeros-mensuels">2026 numéros mensuels</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Publications-legales/Recueil-des-Actes-Administratifs/2025-numeros-speciaux">2025 numéros spéciaux</a></h2>
</body></html>
"""

ANNUAL_HTML = """
<html><body>
<a href="/contenu/telechargement/1/1/file/raa_42-2026-001.pdf">Télécharger raa_42-2026-001 PDF - 1,0 Mb - 05/01/2026</a>
<a href="/contenu/telechargement/1/2/file/raa_42-2026-002.pdf">Télécharger raa_42-2026-002 PDF - 1,1 Mb - 15/01/2026</a>
<a href="/contenu/telechargement/1/3/file/raa_42-2026-003.pdf">Télécharger raa_42-2026-003 PDF - 1,2 Mb - 05/02/2026</a>
<a href="/contenu/telechargement/1/4/file/non-raa.pdf">Document quelconque sans date</a>
</body></html>
"""

def fake_get(pages):
    def _get(url):
        # Handle relative URLs by simplifying the check
        for page_url, html in pages.items():
            if url == page_url or url.endswith(page_url):
                return SimpleNamespace(text=html)
        raise Exception(f"URL not found: {url}")
    return _get

class LoireClientTest(unittest.TestCase):
    def setUp(self):
        self.client = LoireRaaClient(BASE_URL, "2026")
        self.pages = {
            BASE_URL: SECTION_HTML,
            BASE_URL + "/2026-numeros-speciaux": ANNUAL_HTML,
            BASE_URL + "/2026-numeros-mensuels": ANNUAL_HTML,
        }
        self.client._get = fake_get(self.pages)

    def test_find_annual_page(self):
        # Should find "2026 numéros spéciaux" first
        self.assertEqual(
            self.client.find_annual_page(), 
            BASE_URL + "/2026-numeros-speciaux"
        )

    def test_documents_for_month_janvier(self):
        result = self.client.documents_for_month("01")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], "raa_42-2026-001.pdf")
        self.assertEqual(result[1][1], "raa_42-2026-002.pdf")

    def test_documents_for_month_fevrier(self):
        result = self.client.documents_for_month("02")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "raa_42-2026-003.pdf")

    def test_document_sans_date_exclu(self):
        # The document "non-raa.pdf" has no date in text, should be excluded by select_month_documents
        # based on the logic in raa_client.py
        for month in ["01", "02", "03"]:
            result = self.client.documents_for_month(month)
            names = [name for _, name in result]
            self.assertNotIn("non-raa.pdf", names)

if __name__ == "__main__":
    unittest.main()
