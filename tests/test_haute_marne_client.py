import unittest
from types import SimpleNamespace

from haute_marne_client import HauteMarneRaaClient

DOMAIN = "https://www.haute-marne.gouv.fr"
BASE_URL = DOMAIN + "/Publications/Recueil-des-actes-administratifs-RAA"
ANNUAL_2026_URL = BASE_URL + "/Annee-2026"
ANNUAL_2017_URL = BASE_URL + "/Annee-2017"

# Page section : cartes « Année YYYY » (+ une carte non-RAA pour vérifier
# l'absence de faux match sur le seul « 2026 »).
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/Annee-2026">Année 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/Annee-2017">Année 2017</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Communiques-de-presse/2026">Communiqués de presse 2026</a></h2>
</body></html>
"""

# Page annuelle récente (2026) : liens a.fr-link plain, URL absolue,
# sans span CMS — date dans le nom seulement (coquilles incluses).
ANNUAL_2026_HTML = """
<html><body>
<p>Recueil des actes administratifs de l'année 2026 :</p>
<ul>
<li><a href="%s/contenu/telechargement/1/1/file/RAA n° 20 du 27-02-2026.pdf" class="fr-link">Télécharger RAA n° 20 du 27-02-2026</a></li>
<li><a href="%s/contenu/telechargement/2/2/file/RAA n° 19 du 05-02-26.pdf" class="fr-link">Télécharger RAA n° 19 du 05-02-26</a></li>
<li><a href="%s/contenu/telechargement/3/3/file/RAA n° 21 du 02-03-2026-.pdf" class="fr-link">Télécharger RAA n° 21 du 02-03-2026-</a></li>
</ul>
</body></html>
""" % (DOMAIN, DOMAIN, DOMAIN)

# Page annuelle ancienne (2017) : liens fr-link--download + span CMS.
ANNUAL_2017_HTML = """
<html><body>
<div class="fr-downloads-group fr-downloads-group--bordered">
<h2 class="fr-downloads-group__title">Documents listés dans l’article</h2>
<ul>
<li><a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/RAA N°1-17 du 16-01-17.pdf">
Télécharger RAA N°1-17 du 16-01-17 <span class="fr-link__detail">PDF - 18,40 Mb - 16/01/2017</span></a></li>
<li><a class="fr-link fr-link--download" href="/contenu/telechargement/2/2/file/RAA du 29-12-17.pdf">
Télécharger RAA du 29-12-17 <span class="fr-link__detail">PDF - 12,10 Mb - 29/12/2017</span></a></li>
</ul>
</div>
</body></html>
"""


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


class HauteMarneClientTest(unittest.TestCase):
    def test_find_annual_page(self):
        client = HauteMarneRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUAL_2026_URL)

    def test_find_annual_page_annee_ancienne(self):
        client = HauteMarneRaaClient(BASE_URL, "2017")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUAL_2017_URL)

    def test_documents_for_month_sans_span(self):
        # 2026 : pas de span CMS, la date vient du nom de fichier.
        client = HauteMarneRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML, ANNUAL_2026_URL: ANNUAL_2026_HTML})
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            [
                "RAA n° 19 du 05-02-26.pdf",
                "RAA n° 20 du 27-02-2026.pdf",
            ],
        )

    def test_documents_for_month_avec_span(self):
        # 2017 : le span CMS fait foi.
        client = HauteMarneRaaClient(BASE_URL, "2017")
        client._get = fake_get({BASE_URL: SECTION_HTML, ANNUAL_2017_URL: ANNUAL_2017_HTML})
        result = client.documents_for_month("01")
        self.assertEqual(
            [name for _, name in result], ["RAA N°1-17 du 16-01-17.pdf"]
        )

    def test_mois_vide(self):
        client = HauteMarneRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML, ANNUAL_2026_URL: ANNUAL_2026_HTML})
        self.assertEqual(client.documents_for_month("06"), [])


if __name__ == "__main__":
    unittest.main()
