import unittest
from types import SimpleNamespace

from meuse_client import MeuseRaaClient

DOMAIN = "https://www.meuse.gouv.fr"
P = "/Publications/Recueil-des-Actes-Administratifs-RAA"
BASE_URL = DOMAIN + P
ANNUELLE_2026_URL = BASE_URL + "/RAA-annee-2026"
ANNUELLE_2020_URL = BASE_URL + "/RAA-Annee-2020"

# Page section : select d'années (pas de cartes), coquille de casse réelle
# pour 2020 (« RAA Année 2020 »), placeholder « Liste des recueils ».
# Les values sont relatives à la racine du site (pas de barre initiale) —
# c'est le format réel, qui piège un urljoin naïf (préfixe dupliqué, 404).
SECTION_HTML = """
<html><body>
<form method="post">
<select id="Liste-des-recueils-liste-docs" name="Liste-des-recueils-liste-docs">
<option selected disabled hidden value="">Liste des recueils</option>
<option value="Publications/Recueil-des-Actes-Administratifs-RAA/RAA-annee-2026" title="RAA année 2026">RAA année 2026</option>
<option value="Publications/Recueil-des-Actes-Administratifs-RAA/RAA-annee-2025" title="RAA année 2025">RAA année 2025</option>
<option value="Publications/Recueil-des-Actes-Administratifs-RAA/RAA-Annee-2020" title="RAA Année 2020">RAA Année 2020</option>
<option value="Publications/Recueil-des-Actes-Administratifs-RAA/RAA-annee-2006" title="RAA année 2006">RAA année 2006</option>
</select>
</form>
</body></html>
"""

# Page annuelle : liens directs dans le conteneur, span CMS 100 %.
ANNUAL_2026_HTML = """
<html><body>
<div class="fr-col-12 fr-col-md-8">
<ul>
<li><a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/RAA n°16 du 2 février 2026.pdf">
Télécharger RAA n°16 du 2 février 2026 <span class="fr-link__detail">PDF - 1,10 Mb - 02/02/2026</span></a></li>
<li><a class="fr-link fr-link--download" href="/contenu/telechargement/2/2/file/RAA n°26 du 27 février 2026.pdf">
Télécharger RAA n°26 du 27 février 2026 <span class="fr-link__detail">PDF - 0,90 Mb - 27/02/2026</span></a></li>
<li><a class="fr-link fr-link--download" href="/contenu/telechargement/3/3/file/RAA n°2 du 6 janvier 2026.pdf">
Télécharger RAA n°2 du 6 janvier 2026 <span class="fr-link__detail">PDF - 0,80 Mb - 06/01/2026</span></a></li>
</ul>
</div>
</body></html>
"""


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


class MeuseClientTest(unittest.TestCase):
    def test_find_annual_page(self):
        client = MeuseRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUELLE_2026_URL)

    def test_find_annual_page_casse_2020(self):
        # Coquille de casse réelle : « RAA Année 2020 » (A majuscule).
        client = MeuseRaaClient(BASE_URL, "2020")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUELLE_2020_URL)

    def test_find_annual_page_absente(self):
        client = MeuseRaaClient(BASE_URL, "1999")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertIsNone(client.find_annual_page())

    def test_documents_for_month(self):
        client = MeuseRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUAL_2026_HTML})
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            [
                "RAA n°16 du 2 février 2026.pdf",
                "RAA n°26 du 27 février 2026.pdf",
            ],
        )

    def test_mois_vide(self):
        client = MeuseRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUAL_2026_HTML})
        self.assertEqual(client.documents_for_month("06"), [])


if __name__ == "__main__":
    unittest.main()
