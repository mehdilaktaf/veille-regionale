import unittest
from types import SimpleNamespace

from territoire_de_belfort_client import TerritoireDeBelfortRaaClient

DOMAIN = "https://www.territoire-de-belfort.gouv.fr"
P = "/Publications/Le-recueil-des-actes-administratifs"
BASE_URL = DOMAIN + P
ANNUELLE_2026_URL = (
    BASE_URL + "/Le-recueil-des-actes-administratifs-Annee-2026"
)
ANNEE_2022_URL = BASE_URL + "/Annee-2022"

# Page section : liens a.fr-link plain « Année YYYY » (pas de cartes),
# slugs longs (récents) / courts (ancients), + coquille réelle du site :
# « Année 2021 » pointe sur la page Annee-2022.
SECTION_HTML = """
<html><body>
<div class="fr-col-12 fr-col-md-8">
<p><a class="fr-link" href="%s/Le-recueil-des-actes-administratifs-Annee-2026">Année 2026</a></p>
<p><a class="fr-link" href="%s/Le-recueil-des-actes-administratifs-Annee-2025">Année 2025</a></p>
<p><a class="fr-link" href="%s/Annee-2022">Année 2022</a></p>
<p><a class="fr-link" href="%s/Annee-2022">Année 2021</a></p>
<p><a class="fr-link" href="%s/Annee-2010">Année 2010</a></p>
</div>
</body></html>
""" % (P, P, P, P, P)

# Page annuelle : liens directs sans pagination, span CMS 100 %, noms de
# fichier ancrés sur « publié le » (pas « du ») avec double espace réelle.
ANNUAL_2026_HTML = """
<html><body>
<div class="fr-col-12 fr-col-md-8">
<ul>
<li><a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/recueil-90-2026-014- publié le 02-02-2026.pdf">
Télécharger recueil-90-2026-014- publié le 02-02-2026.pdf <span class="fr-link__detail">PDF - 1,20 Mb - 02/02/2026</span></a></li>
<li><a class="fr-link fr-link--download" href="/contenu/telechargement/2/2/file/recueil-90-2026-023- publié le 27-02-2026.pdf">
Télécharger recueil-90-2026-023- publié le 27-02-2026.pdf <span class="fr-link__detail">PDF - 1,10 Mb - 27/02/2026</span></a></li>
<li><a class="fr-link fr-link--download" href="/contenu/telechargement/3/3/file/recueil-90-2026-001- publié le 06-01-2026.pdf">
Télécharger recueil-90-2026-001- publié le 06-01-2026.pdf <span class="fr-link__detail">PDF - 1,78 Mb - 06/01/2026</span></a></li>
</ul>
</div>
</body></html>
"""


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


class TerritoireDeBelfortClientTest(unittest.TestCase):
    def test_find_annual_page(self):
        client = TerritoireDeBelfortRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUELLE_2026_URL)

    def test_find_annual_page_coquille_2021(self):
        # Coquille réelle du site : « Année 2021 » pointe sur la page
        # Annee-2022 — le client suit le lien tel quel.
        client = TerritoireDeBelfortRaaClient(BASE_URL, "2021")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNEE_2022_URL)

    def test_find_annual_page_absente(self):
        client = TerritoireDeBelfortRaaClient(BASE_URL, "2013")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertIsNone(client.find_annual_page())

    def test_documents_for_month(self):
        client = TerritoireDeBelfortRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUAL_2026_HTML})
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            [
                "recueil-90-2026-014- publié le 02-02-2026.pdf",
                "recueil-90-2026-023- publié le 27-02-2026.pdf",
            ],
        )

    def test_mois_vide(self):
        client = TerritoireDeBelfortRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUAL_2026_HTML})
        self.assertEqual(client.documents_for_month("06"), [])


if __name__ == "__main__":
    unittest.main()
