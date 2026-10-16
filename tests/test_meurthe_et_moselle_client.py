import unittest
from types import SimpleNamespace

from meurthe_et_moselle_client import MeurtheEtMoselleRaaClient

DOMAIN = "https://www.meurthe-et-moselle.gouv.fr"
P = "/Publications/Recueils-des-actes-administratifs"
BASE_URL = DOMAIN + P
ANNUELLE_2026_URL = BASE_URL + "/Recueils-des-actes-administratifs-annee-2026"
ANNUELLE_2017_URL = BASE_URL + "/Recueils-des-actes-administratifs-annee-2017"

# Page section : cartes années (+ une carte non-RAA pour vérifier
# l'absence de faux match).
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="%s/Recueils-des-actes-administratifs-annee-2026">Recueils des actes administratifs année 2026</a></h2>
<h2 class="fr-card__title"><a href="%s/Recueils-des-actes-administratifs-annee-2025">Recueils des actes administratifs année 2025</a></h2>
<h2 class="fr-card__title"><a href="%s/Recueils-des-actes-administratifs-annee-2017">Recueils des actes administratifs année 2017</a></h2>
<h2 class="fr-card__title"><a href="%s/../Communiques">Communiqués de presse 2026</a></h2>
</body></html>
""" % (P, P, P, P)

# Page annuelle : 1 select « Liste-liste-docs » (placeholder « Liste »,
# libellés « Numéro N du D mois YYYY »).
VAL_10 = "Numero-10-du-30-janvier-2026"
VAL_11 = "Numero-11-du-2-fevrier-2026"
VAL_12 = "Numero-12-du-4-fevrier-2026"
VAL_17 = "Numero-17-du-27-fevrier-2026"
VAL_X = "Recueil-special-2026"  # option sans date détectable

ANNUELLE_2026_HTML = """
<html><body>
<form method="post">
<select name="Liste-liste-docs">
<option selected disabled hidden value="">Liste</option>
<option value="%s" title="Numéro 10 du 30 janvier 2026">Numéro 10 du 30 janvier 2026</option>
<option value="%s" title="Numéro 11 du 2 février 2026">Numéro 11 du 2 février 2026</option>
<option value="%s" title="Numéro 12 du 4 février 2026">Numéro 12 du 4 février 2026</option>
<option value="%s" title="Numéro 17 du 27 février 2026">Numéro 17 du 27 février 2026</option>
<option value="%s">Recueil spécial 2026</option>
</select>
</form>
</body></html>
""" % (VAL_10, VAL_11, VAL_12, VAL_17, VAL_X)

# Réponses POST (panneau de téléchargement) par value.
POST_RESPONSES = {
    VAL_11: """
<html><body><div class="liste_deroulante">
<a href="/contenu/telechargement/1/1/file/RAA-54-2026-11.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,80 Mb - 02/02/2026</span></a>
</div></body></html>
""",
    VAL_12: """
<html><body><div class="liste_deroulante">
<a href="/contenu/telechargement/2/2/file/RAA-54-2026-12.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,81 Mb - 04/02/2026</span></a>
</div></body></html>
""",
    VAL_17: """
<html><body><div class="liste_deroulante">
<a href="/contenu/telechargement/3/3/file/RAA-54-2026-17.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,82 Mb - 27/02/2026</span></a>
</div></body></html>
""",
    # Option sans date au menu : le CMS dit mars → exclue de février.
    VAL_X: """
<html><body><div class="liste_deroulante">
<a href="/contenu/telechargement/4/4/file/RAA-54-2026-special.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,70 Mb - 04/03/2026</span></a>
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


class MeurtheEtMoselleClientTest(unittest.TestCase):
    def test_find_annual_page(self):
        client = MeurtheEtMoselleRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUELLE_2026_URL)

    def test_find_annual_page_annee_ancienne(self):
        client = MeurtheEtMoselleRaaClient(BASE_URL, "2017")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), ANNUELLE_2017_URL)

    def test_menu_documents_for_month(self):
        client = MeurtheEtMoselleRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUELLE_2026_HTML})
        client._post, posted = fake_post()
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            ["RAA-54-2026-11.pdf", "RAA-54-2026-12.pdf", "RAA-54-2026-17.pdf"],
        )
        # POSTs : 3 candidats février + l'option sans date (balayeur) ;
        # pas janvier.
        self.assertEqual(len(posted), 4)
        for data in posted:
            self.assertIn("Liste-liste-docs", data)

    def test_menu_option_cms_autre_mois_exclue(self):
        # L'option sans date a un mois CMS de mars → exclue de février.
        client = MeurtheEtMoselleRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUELLE_2026_HTML})
        client._post, _ = fake_post()
        result = client.documents_for_month("02")
        self.assertEqual(len(result), 3)

    def test_mois_vide(self):
        client = MeurtheEtMoselleRaaClient(BASE_URL, "2026")
        client.annual_page_url = ANNUELLE_2026_URL
        client._get = fake_get({ANNUELLE_2026_URL: ANNUELLE_2026_HTML})
        client._post, posted = fake_post()
        result = client.documents_for_month("06")
        self.assertEqual(result, [])
        # Seule l'option sans date est vérifiée au POST (balayeur).
        self.assertEqual(len(posted), 1)


if __name__ == "__main__":
    unittest.main()
