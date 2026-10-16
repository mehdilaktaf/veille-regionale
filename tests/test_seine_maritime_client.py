import unittest
from types import SimpleNamespace

from seine_maritime_client import SeineMaritimeRaaClient

BASE_URL = "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026"

# Page annuelle : liens vers les mois dans des h2
ANNUAL_HTML = """
<html><body>
<h2><a href="/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Janvier-2026">RAA Janvier 2026</a></h2>
<h2><a href="/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Fevrier-2026">RAA Février 2026</a></h2>
<h2><a href="/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Mars-2026">RAA Mars 2026</a></h2>
<h2><a href="/Other/Page">Not a RAA link</a></h2>
</body></html>
"""

# Page mensuelle : liens vers les pages documents
MONTHLY_HTML_FEV = """
<html><body>
<a href="/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Fevrier-2026/doc-77">Recueil spécial n°77</a>
<a href="/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Fevrier-2026/doc-75">Recueil normal n°75</a>
<a href="/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Fevrier-2026/doc-68">Recueil spécial n°68</a>
</body></html>
"""

MONTHLY_HTML_JAN = """
<html><body>
<a href="/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Janvier-2026/doc-10">Recueil n°10</a>
</body></html>
"""

# Pages documents : liens vers les PDF
DOC_HTML_77 = """
<html><body>
<a class="fr-link--download" href="/contenu/telechargement/1/1/file/recueil-76-2026-077.pdf">
    Télécharger <span class="fr-link__detail">PDF - 0,14 Mb - 27/02/2026</span>
</a>
</body></html>
"""
DOC_HTML_75 = """
<html><body>
<a class="fr-link--download" href="/contenu/telechargement/1/2/file/recueil-76-2026-075.pdf">
    Télécharger <span class="fr-link__detail">PDF - 16,74 Mb - 27/02/2026</span>
</a>
</body></html>
"""
DOC_HTML_68 = """
<html><body>
<a class="fr-link--download" href="/contenu/telechargement/1/3/file/recueil-76-2026-068.pdf">
    Télécharger <span class="fr-link__detail">PDF - 0,32 Mb - 25/02/2026</span>
</a>
</body></html>
"""
DOC_HTML_10 = """
<html><body>
<a class="fr-link--download" href="/contenu/telechargement/1/4/file/recueil-76-2026-010.pdf">
    Télécharger <span class="fr-link__detail">PDF - 1,00 Mb - 15/01/2026</span>
</a>
</body></html>
"""

def fake_get(pages):
    def _get(url):
        if url in pages:
            return SimpleNamespace(text=pages[url])
        raise Exception(f"URL not found: {url}")
    return _get

def fake_get(pages):
    def _get(url):
        if url in pages:
            return SimpleNamespace(text=pages[url])
        raise Exception(f"URL not found: {url}")
    return _get

def pages_2026():
    return {
        BASE_URL: ANNUAL_HTML,
        "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Janvier-2026": MONTHLY_HTML_JAN,
        "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Janvier-2026/doc-10": DOC_HTML_10,
        "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Fevrier-2026": MONTHLY_HTML_FEV,
        "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Fevrier-2026/doc-77": DOC_HTML_77,
        "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Fevrier-2026/doc-75": DOC_HTML_75,
        "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Fevrier-2026/doc-68": DOC_HTML_68,
        "https://www.seine-maritime.gouv.fr/Publications/Recueils-des-actes-administratifs-RAA/RAA-departemental-2026/RAA-Mars-2026": "<html><body>No PDFs here</body></html>",
    }

class SeineMaritimeClientTest(unittest.TestCase):
    def setUp(self):
        self.client = SeineMaritimeRaaClient(BASE_URL)
        self.client._get = fake_get(pages_2026())

    def test_list_documents(self):
        docs = self.client.list_documents()
        # 1 from Jan, 3 from Feb, 0 from Mars = 4
        self.assertEqual(len(docs), 4)
        
        # Verify names are correctly extracted
        names = [name for _, name, _, _ in docs]
        self.assertIn("recueil-76-2026-010.pdf", names)
        self.assertIn("recueil-76-2026-077.pdf", names)

    def test_documents_for_month_fevrier(self):
        result = self.client.documents_for_month("02")
        # Should have 3 documents from February, sorted chronologically (day first)
        # 25/02, then 27/02 (068), then 27/02 (075), then 27/02 (077)
        # Sorting by (day, name)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][1], "recueil-76-2026-068.pdf") # 25/02
        # The other two are 27/02, so they are sorted by name
        self.assertEqual(result[1][1], "recueil-76-2026-075.pdf")
        self.assertEqual(result[2][1], "recueil-76-2026-077.pdf")

    def test_documents_for_month_janvier(self):
        result = self.client.documents_for_month("01")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "recueil-76-2026-010.pdf")

    def test_documents_for_month_vide(self):
        # April should be empty as it's not in our fake pages (actually Mars is there but empty)
        self.assertEqual(self.client.documents_for_month("04"), [])
        self.assertEqual(self.client.documents_for_month("03"), [])

if __name__ == "__main__":
    unittest.main()
