import unittest
from types import SimpleNamespace

from mayotte_client import MayotteRaaClient

BASE_URL = "https://www.mayotte.gouv.fr/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-2026"

ANNUAL_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-2026/MAI-2026">MAI 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-2026/AOUT-2026">AOUT 2026</a></h2>
</body></html>
"""

# Page de mois paginée : 2 cartes documents + « Suivant »
MONTH_PAGE1_HTML = """
<html><body>
<h2 class="fr-card__title"><a class="fr-card__link" href="/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-2026/AOUT-2026/n-160-du-05-aout-2026">n°160 du 05 août 2026</a></h2>
<h2 class="fr-card__title"><a class="fr-card__link" href="/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-2026/AOUT-2026/n-161-du-06-aout-2026">n°161 du 06 août 2026</a></h2>
<ul class="fr-pagination__list">
<li><a href="/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-2026/AOUT-2026/(offset)/10">Suivant</a></li>
</ul>
</body></html>
"""

MONTH_PAGE2_HTML = """
<html><body>
<h2 class="fr-card__title"><a class="fr-card__link" href="/Publications/Recueil-des-actes-administratifs-R.A.A/RAA-2026/AOUT-2026/n-162-du-28-aout-2026">n°162 du 28 août 2026</a></h2>
</body></html>
"""

DOC_HTML_TEMPLATE = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/9/9/file/{name}">
<span class="fr-link__detail">{span}</span>Télécharger</a>
</body></html>
"""


def doc_html(name, span):
    return DOC_HTML_TEMPLATE.format(name=name, span=span)


class MayotteClientTest(unittest.TestCase):
    def setUp(self):
        self.client = MayotteRaaClient(BASE_URL)
        self.pages = {
            BASE_URL: ANNUAL_HTML,
            BASE_URL + "/MAI-2026": "<html><body></body></html>",
            BASE_URL + "/AOUT-2026": MONTH_PAGE1_HTML,
            BASE_URL + "/AOUT-2026/(offset)/10": MONTH_PAGE2_HTML,
            BASE_URL + "/AOUT-2026/n-160-du-05-aout-2026": doc_html(
                "recueil-r06-2026-160.pdf", "PDF - 1,0 Mb - 05/08/2026"
            ),
            BASE_URL + "/AOUT-2026/n-161-du-06-aout-2026": doc_html(
                "recueil-r06-2026-161-special.pdf", "PDF - 1,0 Mb - 06/08/2026"
            ),
            BASE_URL + "/AOUT-2026/n-162-du-28-aout-2026": doc_html(
                "recueil-r06-2026-162.pdf", "PDF - 1,0 Mb - 28/08/2026"
            ),
        }
        self.client._get = lambda url: SimpleNamespace(text=self.pages[url])

    def test_trois_niveaux_et_pagination(self):
        documents = self.client.list_documents("08")
        self.assertEqual(
            sorted(name for _, name, _, _ in documents),
            [
                "recueil-r06-2026-160.pdf",
                "recueil-r06-2026-161-special.pdf",
                "recueil-r06-2026-162.pdf",
            ],
        )

    def test_documents_for_month(self):
        result = self.client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            [
                "recueil-r06-2026-160.pdf",
                "recueil-r06-2026-161-special.pdf",
                "recueil-r06-2026-162.pdf",
            ],
        )
        self.assertTrue(result[0][0].endswith("/file/recueil-r06-2026-160.pdf"))

    def test_autre_mois(self):
        self.assertEqual(self.client.documents_for_month("05"), [])


if __name__ == "__main__":
    unittest.main()
