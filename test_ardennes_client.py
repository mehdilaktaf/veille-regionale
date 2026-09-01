import unittest
from types import SimpleNamespace

from ardennes_client import ArdennesRaaClient

DOMAIN = "https://www.ardennes.gouv.fr"
BASE_URL = DOMAIN + "/Publications/Recueil-des-actes-administratifs"
ARCHIVES_URL = (
    BASE_URL + "/Les-actes-administratifs-des-annees-anterieures2"
)

# Page section : carte année en cours + carte « années antérieures ».
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/Les-actes-administratifs-de-l-annee-2026">Les actes administratifs de l'année 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/Les-actes-administratifs-des-annees-anterieures2">Les actes administratifs des années antérieures</a></h2>
</body></html>
"""

# Page d'archives : cartes années + carte commune 2015 & 2016.
ARCHIVES_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/Les-actes-administratifs-des-annees-anterieures2/Les-actes-administratifs-de-l-annee-2025">Les actes administratifs de l'année 2025</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs/Les-actes-administratifs-des-annees-anterieures2/Les-actes-administratifs">Les actes administratifs des années 2015 &amp; 2016</a></h2>
</body></html>
"""

# Page annuelle : liens directs, span CMS 100 %, nom de fichier daté.
ANNUAL_2026_HTML = """
<html><body>
<div class="fr-col-12 fr-col-md-8">
<a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/RAA 8-2026-143 du 28 aout 2026.pdf">
Télécharger RAA 8-2026-143 du 28 aout 2026
<span class="fr-link__detail">PDF - 3,13 Mb - 28/08/2026</span></a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/2/2/file/RAA 8-2026-144 du 31 aout 2026.pdf">
Télécharger RAA 8-2026-144 du 31 aout 2026
<span class="fr-link__detail">PDF - 3,11 Mb - 31/08/2026</span></a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/3/3/file/RAA 9-2026-145 du 2 septembre 2026.pdf">
Télécharger RAA 9-2026-145 du 2 septembre 2026
<span class="fr-link__detail">PDF - 2,00 Mb - 02/09/2026</span></a>
</div>
</body></html>
"""


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


class ArdennesClientTest(unittest.TestCase):
    def setUp(self):
        self.client = ArdennesRaaClient(BASE_URL, "2026")
        pages = {
            BASE_URL: SECTION_HTML,
            BASE_URL + "/Les-actes-administratifs-de-l-annee-2026": ANNUAL_2026_HTML,
        }
        self.client._get = fake_get(pages)

    def test_find_annual_page_annee_courante(self):
        self.assertEqual(
            self.client.find_annual_page(),
            BASE_URL + "/Les-actes-administratifs-de-l-annee-2026",
        )

    def test_find_annual_page_via_archives(self):
        client = ArdennesRaaClient(BASE_URL, "2025")
        client._get = fake_get({BASE_URL: SECTION_HTML, ARCHIVES_URL: ARCHIVES_HTML})
        self.assertEqual(
            client.find_annual_page(),
            ARCHIVES_URL + "/Les-actes-administratifs-de-l-annee-2025",
        )

    def test_find_annual_page_carte_commune_2015_2016(self):
        client = ArdennesRaaClient(BASE_URL, "2016")
        client._get = fake_get({BASE_URL: SECTION_HTML, ARCHIVES_URL: ARCHIVES_HTML})
        self.assertEqual(
            client.find_annual_page(),
            ARCHIVES_URL + "/Les-actes-administratifs",
        )

    def test_list_documents_secondaire_nom_fichier(self):
        documents = self.client.list_documents()
        self.assertEqual(len(documents), 3)
        self.assertEqual(documents[0][2], (28, 8))  # span CMS
        self.assertEqual(documents[0][3], (28, 8))  # nom de fichier

    def test_documents_for_month_aout(self):
        result = self.client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            [
                "RAA 8-2026-143 du 28 aout 2026.pdf",
                "RAA 8-2026-144 du 31 aout 2026.pdf",
            ],
        )

    def test_documents_for_month_vide(self):
        self.assertEqual(self.client.documents_for_month("01"), [])


if __name__ == "__main__":
    unittest.main()
