import unittest
from types import SimpleNamespace

from haut_rhin_client import HautRhinRaaClient

DOMAIN = "https://www.haut-rhin.gouv.fr"
P = "/Publications/Recueil-des-actes-administratifs"
BASE_URL = DOMAIN + P
ANNUELLE_2026_URL = BASE_URL + "/2026"
PAGE2_URL = BASE_URL + "/2026/(offset)/10"

# Page section : cartes d'années à TEXTE EXACT (« 2026 »), archive
# profonde, + un lien PDF égaré dans une carte (coquille réelle du site :
# « Reccueil n°77 ») qui ne doit pas matcher.
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="%s/2026">2026</a></h2>
<h2 class="fr-card__title"><a href="%s/2025">2025</a></h2>
<h2 class="fr-card__title"><a href="%s/1994">1994</a></h2>
<h2 class="fr-card__title"><a href="/contenu/telechargement/53112/376427/file/RAA n° 77 du 10 juillet 2026.pdf">Reccueil n°77 du 10 juillet 2026</a></h2>
</body></html>
""" % (P, P, P)

# Page annuelle : cartes = liens PDF directs, title CMS faisant foi,
# pagination « Suivant ». Page 1 : août (les plus récents d'abord).
PAGE1_HTML = """
<html><body>
<div class="fr-col-12 fr-col-md-8">
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
href="/contenu/telechargement/1/1/file/RAA n°100 du 31 août 2026.pdf"
title="format pdf - 1,02 Mb - 31/08/2026">Recueil n°100 du 31 août 2026</a></h2>
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
href="/contenu/telechargement/2/2/file/RAA n°60 du 27 février 2026.pdf"
title="format pdf - 0,90 Mb - 27/02/2026">Recueil n°60 du 27 février 2026</a></h2>
</div>
<ul class="fr-pagination__list">
<li><a href="%s/2026/(offset)/10">Suivant</a></li>
</ul>
</body></html>
""" % P

# Page 2 : février (mois mêlés sur la pagination).
PAGE2_HTML = """
<html><body>
<div class="fr-col-12 fr-col-md-8">
<h2 class="fr-card__title"><a class="fr-card__link menu-item-link"
href="/contenu/telechargement/3/3/file/RAA n°55 du 2 février 2026.pdf"
title="format pdf - 0,85 Mb - 02/02/2026">Recueil n°55 du 2 février 2026</a></h2>
</div>
</body></html>
"""


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


class HautRhinClientTest(unittest.TestCase):
    def test_find_annual_page_texte_exact(self):
        client = HautRhinRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUELLE_2026_URL)

    def test_find_annual_page_lien_pdf_egare_ignoré(self):
        # Sans carte « 2026 », la carte « Reccueil n°77 du 10 juillet
        # 2026 » (lien PDF égaré) ne porte pas un texte d'année → aucun
        # faux match.
        sans_2026 = SECTION_HTML.replace(
            '<h2 class="fr-card__title"><a href="%s/2026">2026</a></h2>' % P, ""
        )
        client = HautRhinRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: sans_2026})
        self.assertIsNone(client.find_annual_page())

    def test_documents_for_month_pagination(self):
        client = HautRhinRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get(
            {ANNUELLE_2026_URL: PAGE1_HTML, PAGE2_URL: PAGE2_HTML}
        )
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            [
                "RAA n°55 du 2 février 2026.pdf",
                "RAA n°60 du 27 février 2026.pdf",
            ],
        )

    def test_mois_vide(self):
        client = HautRhinRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get(
            {ANNUELLE_2026_URL: PAGE1_HTML, PAGE2_URL: PAGE2_HTML}
        )
        self.assertEqual(client.documents_for_month("06"), [])


if __name__ == "__main__":
    unittest.main()
