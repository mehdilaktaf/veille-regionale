import unittest
from types import SimpleNamespace

from moselle_client import MoselleRaaClient

BASE_URL = "https://www.moselle.gouv.fr/Publications/Recueil-des-Actes-Administratifs"
MC_BASE = "https://mc.moselle.gouv.fr/"

RAA_HTML = "<html><body>raa</body></html>"

# Page de résultats 1 : 3 recueils + lien « > » vers la page 2
RESULT_PAGE1_HTML = """
<html><body>
<table class="table_list">
<tr><td>Type</td><td>Référence</td><td>Date de publication</td><td>Actions</td></tr>
<tr><td>Spécial</td><td>Numéro 195</td><td>28/08/2026</td>
<td><a href="index.php?dims_op=doc_file_download&docfile_md5id=aaa">PDF</a></td></tr>
<tr><td>Spécial</td><td>Numéro 194</td><td>28/08/2026</td>
<td><a href="index.php?dims_op=doc_file_download&docfile_md5id=bbb">PDF</a></td></tr>
<tr><td>Normal</td><td>Numéro 89</td><td>05/08/2026</td>
<td><a href="index.php?dims_op=doc_file_download&docfile_md5id=ccc">PDF</a></td></tr>
</table>
<a href="index.php?tab=1&do=exec_search_rec&page=1">&gt;</a>
</body></html>
"""

# Page de résultats 2 : 1 recueil, plus de lien « > »
RESULT_PAGE2_HTML = """
<html><body>
<table class="table_list">
<tr><td>Type</td><td>Référence</td><td>Date de publication</td><td>Actions</td></tr>
<tr><td>Normal</td><td>Numéro 90</td><td>06/08/2026</td>
<td><a href="index.php?dims_op=doc_file_download&docfile_md5id=ddd">PDF</a></td></tr>
</table>
</body></html>
"""

EMPTY_RESULT_HTML = """
<html><body>
<table class="table_list">
<tr><td>Type</td><td>Référence</td><td>Date de publication</td><td>Actions</td></tr>
</table>
</body></html>
"""


def make_client(result_pages):
    client = MoselleRaaClient(BASE_URL, "2026")
    client._get = lambda url: SimpleNamespace(text=RAA_HTML if url.endswith("raa.html") else result_pages.pop(0))
    client._post = lambda url, data=None: SimpleNamespace(text=result_pages.pop(0))
    return client


class MoselleClientTest(unittest.TestCase):
    def test_list_documents_pagination(self):
        client = make_client([RESULT_PAGE1_HTML, RESULT_PAGE2_HTML])
        documents = client.list_documents("08")
        self.assertEqual(
            [name for _, name, _, _ in documents],
            [
                "RAA n°195 du 28-08-2026 (Spécial).pdf",
                "RAA n°194 du 28-08-2026 (Spécial).pdf",
                "RAA n°89 du 05-08-2026 (Normal).pdf",
                "RAA n°90 du 06-08-2026 (Normal).pdf",
            ],
        )
        self.assertEqual(documents[0][0], MC_BASE + "index.php?dims_op=doc_file_download&docfile_md5id=aaa")

    def test_documents_for_month_ordre_chronologique(self):
        client = make_client([RESULT_PAGE1_HTML, RESULT_PAGE2_HTML])
        result = client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            [
                "RAA n°89 du 05-08-2026 (Normal).pdf",
                "RAA n°90 du 06-08-2026 (Normal).pdf",
                "RAA n°194 du 28-08-2026 (Spécial).pdf",
                "RAA n°195 du 28-08-2026 (Spécial).pdf",
            ],
        )

    def test_mois_vide(self):
        client = make_client([EMPTY_RESULT_HTML])
        self.assertEqual(client.documents_for_month("08"), [])


if __name__ == "__main__":
    unittest.main()
