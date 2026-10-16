import unittest
from types import SimpleNamespace

from isere_client import IsereRaaClient

BASE_URL = "https://www.isere.gouv.fr/Publications/RAA-Recueil-des-actes-administratifs/Recueils-des-Actes-Administratifs-de-la-prefecture-de-l-Isere-2026"

# Page annuelle avec select
ANNUAL_PAGE_HTML = """
<html><body class="fr-container">
    <form method="post" name="form">
        <select class="fr-select" id="isere-2026-liste-docs" name="isere-2026-liste-docs">
            <option value="">Sélectez...</option>
            <option value="doc1.pdf" title="Recueil spécial n°1 du 05 janvier 2026">Recueil spécial n°1 du 05 janvier 2026</option>
            <option value="doc2.pdf" title="Recueil spécial n°2 du 06 janvier 2026">Recueil spécial n°2 du 06 janvier 2026</option>
            <option value="doc3.pdf" title="Recueil spécial n°3 du 05 février 2026">Recueil spécial n°3 du 05 février 2026</option>
        </select>
    </form>
</body></html>
"""

# Page de téléchargement (résultat du POST)
PANEL_HTML = """
<html><body class="fr-container">
    <div class="fr-link--download">
        <a class="fr-link fr-link--download" href="/download/doc.pdf">
            Télécharger le document
            <span class="fr-link__detail">PDF - 1 Mb - 05/01/2026</span>
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

def fake_post():
    def _post(payload, max_retries=3):
        # On récupère la valeur sélectionnée pour simuler la date CMS correspondante
        # Le payload est un dictionnaire {select_name: value}
        val = next(iter(payload.values())) if payload else ""
        date_cms = "05/01/2026"
        if "doc3" in val:
            date_cms = "05/02/2026"
        
        return SimpleNamespace(text=f"""
        <html><body class="fr-container">
            <a class="fr-link fr-link--download" href="/download/{val}.pdf">
                Télécharger
                <span class="fr-link__detail">PDF - 1 Mb - {date_cms}</span>
            </a>
        </body></html>
        """)
    return _post

class IsereClientTest(unittest.TestCase):
    def setUp(self):
        self.client = IsereRaaClient(BASE_URL, "2026")
        self.client._get = fake_get({BASE_URL: ANNUAL_PAGE_HTML})
        # On utilise le fake_post dynamique
        self.client._post = fake_post()

    def test_list_documents(self):
        docs = self.client.list_documents()
        self.assertEqual(len(docs), 3)
        self.assertEqual(docs[0][0], "doc1.pdf")
        self.assertEqual(docs[0][2], (5, 1))

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
