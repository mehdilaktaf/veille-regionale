import unittest
from types import SimpleNamespace

from bas_rhin_client import BasRhinRaaClient

DOMAIN = "https://www.bas-rhin.gouv.fr"
P = (
    "/Publications/Publications-officielles/"
    "RAA-Recueils-des-actes-administratifs"
)
BASE_URL = DOMAIN + P
ANNUELLE_2026_URL = BASE_URL + "/RAA-ANNEE-2026"
ANNUELLE_2017_URL = BASE_URL + "/RAA-ANNEE-2017"

# Page section : cartes « RAA ANNEE YYYY » (majuscules sans accent),
# + une carte non-RAA pour vérifier l'absence de faux match.
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="%s/RAA-ANNEE-2026">RAA ANNEE 2026</a></h2>
<h2 class="fr-card__title"><a href="%s/RAA-ANNEE-2025">RAA ANNEE 2025</a></h2>
<h2 class="fr-card__title"><a href="%s/RAA-ANNEE-2017">RAA ANNEE 2017</a></h2>
<h2 class="fr-card__title"><a href="%s/../Arretes-prefectoraux">Arrêtés préfectoraux 2026</a></h2>
</body></html>
""" % (P, P, P, P)

# Page annuelle 2026 : un select PAR MOIS, tous nommés « Liste-liste-docs ».
VAL_J01 = "Media/Files/22.-RAA/2026/Janvier/RAA-N-4-du-30-janvier-2026"
VAL_F01 = "Media/Files/22.-RAA/2026/Fevrier/RAA-N-special-du-02-fevrier-2026"
VAL_F02 = "Media/Files/22.-RAA/2026/Fevrier/RAA-N-08-du-27-fevrier-2026"
VAL_X = "Media/Files/22.-RAA/2026/Recueil-hors-serie"  # sans dossier mois

ANNUELLE_2026_HTML = """
<html><body>
<p>■ JANVIER 2026</p>
<form method="post">
<select name="Liste-liste-docs">
<option selected disabled hidden value="">Liste</option>
<option value=%s title="RAA N°4 du 30 janvier 2026">RAA N°4 du 30 janvier 2026</option>
</select>
</form>
<p>■ FÉVRIER 2026</p>
<form method="post">
<select name="Liste-liste-docs">
<option selected disabled hidden value="">Liste</option>
<option value=%s title="RAA N° spécial du 02 février 2026">RAA N° spécial du 02 février 2026</option>
<option value=%s title="RAA N° 08 du 27 février 2026">RAA N° 08 du 27 février 2026</option>
<option value=%s>Recueil hors série 2026</option>
</select>
</form>
</body></html>
""" % (VAL_J01, VAL_F01, VAL_F02, VAL_X)

# Réponses POST (panneau de téléchargement) par value.
POST_RESPONSES = {
    VAL_F01: """
<html><body><div class="liste_deroulante">
<a href="/Media/Files/22.-RAA/2026/Fevrier/RAA-N-special-02-02-2026.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,60 Mb - 02/02/2026</span></a>
</div></body></html>
""",
    VAL_F02: """
<html><body><div class="liste_deroulante">
<a href="/Media/Files/22.-RAA/2026/Fevrier/RAA-N-08-27-02-2026.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 1,20 Mb - 27/02/2026</span></a>
</div></body></html>
""",
    # Option sans mois détectable : le CMS dit mars → exclue de février.
    VAL_X: """
<html><body><div class="liste_deroulante">
<a href="/Media/Files/22.-RAA/2026/Recueil-hors-serie.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,40 Mb - 04/03/2026</span></a>
</div></body></html>
""",
}


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


def fake_post():
    posted = []

    def _post(url, data=None, retries=4, backoff=10):
        posted.append(data)
        value = list(data.values())[0]
        return SimpleNamespace(text=POST_RESPONSES[value])

    return _post, posted


class BasRhinClientTest(unittest.TestCase):
    def test_find_annual_page_majuscules(self):
        # Cartes « RAA ANNEE YYYY » sans accent : la comparaison
        # insensible à la casse doit matcher « RAA année 2026 ».
        client = BasRhinRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUELLE_2026_URL)

    def test_find_annual_page_annee_ancienne(self):
        client = BasRhinRaaClient(BASE_URL, "2017")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUELLE_2017_URL)

    def test_menu_documents_for_month_union_selects(self):
        client = BasRhinRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUELLE_2026_HTML})
        client._post, posted = fake_post()
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            [
                "RAA-N-special-02-02-2026.pdf",
                "RAA-N-08-27-02-2026.pdf",
            ],
        )
        # POSTs : 2 candidats février + l'option sans mois (balayeur) ;
        # pas janvier.
        self.assertEqual(len(posted), 3)
        for data in posted:
            self.assertIn("Liste-liste-docs", data)

    def test_menu_option_cms_autre_mois_exclue(self):
        # L'option sans mois détectable a un mois CMS de mars → exclue.
        client = BasRhinRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUELLE_2026_HTML})
        client._post, _ = fake_post()
        result = client.documents_for_month("02")
        self.assertEqual(len(result), 2)

    def test_mois_vide(self):
        client = BasRhinRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUELLE_2026_HTML})
        client._post, posted = fake_post()
        result = client.documents_for_month("06")
        self.assertEqual(result, [])
        # Seule l'option sans mois détectable est vérifiée au POST.
        self.assertEqual(len(posted), 1)


if __name__ == "__main__":
    unittest.main()
