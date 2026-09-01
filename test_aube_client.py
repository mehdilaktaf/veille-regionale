import unittest
from types import SimpleNamespace

from aube_client import AubeRaaClient

BASE_URL = (
    "https://www.aube.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA2"
)
ANNUAL_URL = BASE_URL + "/RAA-2026"
PAGE2_URL = ANNUAL_URL + "/(offset)/10"

# Page section : cartes années.
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA2/RAA-2025">RAA 2025</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA2/RAA-2026">RAA 2026</a></h2>
</body></html>
"""

# Page 1 : 2 cartes août (dont 1 sans attribut title) + 1 septembre + « Suivant »
PAGE1_HTML = """
<html><body>
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
 href="/contenu/telechargement/1/1/file/RAA n°203 du 24 août 2026.pdf"
 title="format pdf - 1,20 Mb - 24/08/2026">RAA n°203 du 24 août 2026</a></h2>
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
 href="/contenu/telechargement/2/2/file/RAA n°202 du 20 août 2026.pdf">RAA n°202 du 20 août 2026</a></h2>
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
 href="/contenu/telechargement/3/3/file/RAA n°204 du 02 septembre 2026.pdf"
 title="format pdf - 0,90 Mb - 02/09/2026">RAA n°204 du 02 septembre 2026</a></h2>
<ul class="fr-pagination__list">
<li><a>Précédent</a></li>
<li><a href="%s">Suivant</a></li>
</ul>
</body></html>
""" % PAGE2_URL

# Page 2 : 1 carte août, sans « Suivant ».
PAGE2_HTML = """
<html><body>
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
 href="/contenu/telechargement/4/4/file/RAA nominatif n°208 du 31 août 2026.pdf"
 title="format pdf - 2,57 Mb - 31/08/2026">RAA nominatif n°208 du 31 août 2026</a></h2>
<ul class="fr-pagination__list">
<li><a href="%s">Précédent</a></li>
<li><a>Suivant</a></li>
</ul>
</body></html>
""" % ANNUAL_URL


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


def pages_2026():
    return {
        BASE_URL: SECTION_HTML,
        ANNUAL_URL: PAGE1_HTML,
        PAGE2_URL: PAGE2_HTML,
    }


class AubeClientTest(unittest.TestCase):
    def setUp(self):
        self.client = AubeRaaClient(BASE_URL, "2026")
        self.client._get = fake_get(pages_2026())

    def test_find_annual_page(self):
        self.assertEqual(self.client.find_annual_page(), ANNUAL_URL)

    def test_list_documents_traverse_pagination(self):
        documents = self.client.list_documents("08")
        self.assertEqual(len(documents), 4)

    def test_date_from_title_attribute(self):
        documents = {
            name: cms for _, name, cms, _ in self.client.list_documents("08")
        }
        self.assertEqual(
            documents["RAA n°203 du 24 août 2026.pdf"], (24, 8)
        )

    def test_date_fallback_texte(self):
        documents = {
            name: text_dm for _, name, _, text_dm in self.client.list_documents("08")
        }
        self.assertEqual(documents["RAA n°202 du 20 août 2026.pdf"], (20, 8))

    def test_documents_for_month_aout(self):
        result = self.client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            [
                "RAA n°202 du 20 août 2026.pdf",
                "RAA n°203 du 24 août 2026.pdf",
                "RAA nominatif n°208 du 31 août 2026.pdf",
            ],
        )

    def test_mois_vide(self):
        self.assertEqual(self.client.documents_for_month("01"), [])


if __name__ == "__main__":
    unittest.main()
