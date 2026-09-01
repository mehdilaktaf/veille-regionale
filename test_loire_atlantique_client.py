import unittest
from types import SimpleNamespace

from loire_atlantique_client import LoireAtlantiqueRaaClient

BASE_URL = (
    "https://www.loire-atlantique.gouv.fr/Publications/"
    "Recueil-des-actes-administratifs-RAA-en-Loire-Atlantique/2026/"
)
MONTH_URL = BASE_URL + "aout/"
PAGE2_URL = MONTH_URL + "(offset)/10"

# Page 1 : 2 cards (dont 1 sans attribut title) + pagination vers la page 2
PAGE1_HTML = """
<html><body>
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
 href="/contenu/telechargement/1/1/file/RAA n°214 du 28 août 2026.pdf"
 title="format pdf - 10,24 Mb - 28/08/2026">RAA n°214 du 28 août 2026</a></h2>
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
 href="/contenu/telechargement/2/2/file/RAA n°213 du 25 août 2026.pdf">RAA n°213 du 25 août 2026</a></h2>
<ul class="fr-pagination__list">
<li><a>Précédent</a></li>
<li><a href="%s">Suivant</a></li>
</ul>
</body></html>
""" % PAGE2_URL

# Page 2 : 1 card (hors mois) + pagination sans « Suivant »
PAGE2_HTML = """
<html><body>
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
 href="/contenu/telechargement/3/3/file/RAA n°215 du 05 septembre 2026.pdf"
 title="format pdf - 2,91 Mb - 05/09/2026">RAA n°215 du 05 septembre 2026</a></h2>
<ul class="fr-pagination__list">
<li><a href="%s">Précédent</a></li>
<li><a>Suivant</a></li>
</ul>
</body></html>
""" % MONTH_URL


class LoireAtlantiqueClientTest(unittest.TestCase):
    def setUp(self):
        self.client = LoireAtlantiqueRaaClient(BASE_URL)
        pages = {
            MONTH_URL: PAGE1_HTML,
            PAGE2_URL: PAGE2_HTML,
            BASE_URL + "janvier/": "<html><body></body></html>",
        }
        self.client._get = lambda url: SimpleNamespace(text=pages[url])

    def test_list_documents_traverse_pagination(self):
        documents = self.client.list_documents("08")
        self.assertEqual(len(documents), 3)

    def test_date_from_title_attribute(self):
        documents = {
            name: cms for _, name, cms, _ in self.client.list_documents("08")
        }
        self.assertEqual(
            documents["RAA n°214 du 28 août 2026.pdf"], (28, 8)
        )

    def test_date_fallback_texte(self):
        documents = {name: text_dm for _, name, _, text_dm in self.client.list_documents("08")}
        self.assertEqual(
            documents["RAA n°213 du 25 août 2026.pdf"], (25, 8)
        )

    def test_documents_for_month(self):
        result = self.client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            ["RAA n°213 du 25 août 2026.pdf", "RAA n°214 du 28 août 2026.pdf"],
        )
        self.assertTrue(
            result[0][0].endswith("/file/RAA n°213 du 25 août 2026.pdf")
        )

    def test_mois_vide(self):
        self.assertEqual(self.client.documents_for_month("01"), [])


if __name__ == "__main__":
    unittest.main()
