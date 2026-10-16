import unittest
from types import SimpleNamespace

from marne_client import MarneRaaClient

DOMAIN = "https://www.marne.gouv.fr"
P = (
    "/Publications/Publications-administratives-et-legales/"
    "RAA-Recueils-des-actes-administratifs/"
    "RAA-Recueils-des-actes-administratifs-de-la-prefecture-de-la-Marne"
)
BASE_URL = DOMAIN + P
MENU_2026_URL = BASE_URL + "/RAA-Annee-2026"
TABLE_2024_URL = BASE_URL + "/2024"
GROUP_URL = BASE_URL + "/Annees-2021-a-2023"
GROUP_2013_URL = BASE_URL + "/Annees-2013-a-2016"

# Page section : cartes années (directes, exactes, groupes).
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="%s/RAA-Annee-2026">RAA Année 2026</a></h2>
<h2 class="fr-card__title"><a href="%s/RAA-Annee-2025">RAA Année 2025</a></h2>
<h2 class="fr-card__title"><a href="%s/2024">2024</a></h2>
<h2 class="fr-card__title"><a href="%s/Annees-2021-a-2023">Années 2021 à 2023</a></h2>
<h2 class="fr-card__title"><a href="%s/Annees-2013-a-2016">Années 2013 à 2016</a></h2>
</body></html>
""" % (P, P, P, P, P)

# Page de groupe : coquille réelle « RAA  Année 2022 » (double espace).
GROUP_2021_2023_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="%s/Annees-2021-a-2023/RAA-Annee-2021">RAA Année 2021</a></h2>
<h2 class="fr-card__title"><a href="%s/Annees-2021-a-2023/RAA-Annee-2022">RAA  Année 2022</a></h2>
<h2 class="fr-card__title"><a href="%s/Annees-2021-a-2023/RAA-Annee-2023">RAA Année 2023</a></h2>
</body></html>
""" % (P, P, P)

GROUP_2013_2016_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="%s/Annees-2013-a-2016/RAA-Annee-2016">RAA Année 2016</a></h2>
</body></html>
""" % (P,)

# Page annuelle 2026 (flow menu) : un select PAR MOIS — le select du
# premier mois est en tête de page (double tiret), les autres à tiret
# simple. Pas de select global : la liste de l'année = union des options.
VAL_001 = "Media/Files/Prefecture/RAA/2026/Janvier/RAA-N-51-2026-001-du-5-janvier-2026"
VAL_020 = "Media/Files/Prefecture/RAA/2026/Fevrier/RAA-N-51-2026-020-du-03-fevrier-2026"
VAL_040 = "Media/Files/Prefecture/RAA/2026/Fevrier/RAA-n-51-2026-040-du-27-fevrier-2026"
VAL_041 = "Media/Files/Prefecture/RAA/2026/RAA-n-51-2026-041"  # sans mois

MENU_2026_HTML = """
<html><body>
<select id="Liste-des-RAA--liste-docs" name="Liste-des-RAA--liste-docs">
<option selected disabled hidden value="">Liste des RAA</option>
<option value=%s title="RAA N°51-2026-001 du 5 janvier 2026">RAA N°51-2026-001 du 5 janvier 2026</option>
</select>
<p>■ <b>JANVIER 2026</b></p>
<p>■ <b>FÉVRIER 2026</b></p>
<form method="post">
<select id="Liste-des-RAA-liste-docs" name="Liste-des-RAA-liste-docs">
<option selected disabled hidden value="">Liste des RAA</option>
<option value=%s title="RAA N°51-2026-020 du 3 février 2026">RAA N°51-2026-020 du 3 février 2026</option>
<option value=%s title="RAA n°51-2026-040 du 27 février 2026">RAA n°51-2026-040 du 27 février 2026</option>
<option value=%s title="RAA n°51-2026-041">RAA n°51-2026-041</option>
</select>
</form>
</body></html>
""" % (VAL_001, VAL_020, VAL_040, VAL_041)

# Réponses POST (panneau de téléchargement) par value.
POST_RESPONSES = {
    VAL_020: """
<html><body><div class="liste_deroulante">
<a href="/contenu/telechargement/1/1/file/recueil-51-2026-020-recueil-des-actes-administratifs.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,80 Mb - 03/02/2026</span></a>
</div></body></html>
""",
    VAL_040: """
<html><body><div class="liste_deroulante">
<a href="/contenu/telechargement/2/2/file/recueil-51-2026-040-recueil-des-actes-administratifs.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,81 Mb - 27/02/2026</span></a>
</div></body></html>
""",
    # Option sans date au menu : le CMS dit mars → exclue de février.
    VAL_041: """
<html><body><div class="liste_deroulante">
<a href="/contenu/telechargement/3/3/file/recueil-51-2026-041-recueil-des-actes-administratifs.pdf" class="fr-link fr-link--download">
Télécharger <span class="fr-link__detail">PDF - 0,70 Mb - 04/03/2026</span></a>
</div></body></html>
""",
}

# Page annuelle 2024 (flow tableau) : liens vers pages documents.
TABLE_2024_HTML = """
<html><body>
<table>
<tr><td><div><a href="%s/2024/RAA-Annee-2024/Recueil-1-20-du-31-janvier-2024">Recueil n°1-20 du 31 janvier 2024</a></div></td></tr>
<tr><td><div><a href="%s/2024/RAA-Annee-2024/Recueil-n-2-1-du-1er-fevrier-2024">Recueil n°2-1 du 1er février 2024</a></div></td></tr>
<tr><td><div><a href="%s/2024/RAA-Annee-2024/Recueil-n-2-9-du-12-fevrier-2024">Recueil n°2-9 du 12 février 2024</a></div></td></tr>
</table>
</body></html>
""" % (P, P, P)


def doc_page_html(filename, cms_date):
    return (
        "<html><body>"
        f'<a class="fr-link fr-link--download" '
        f'href="/contenu/telechargement/9/9/file/{filename}">'
        f"Télécharger {filename} "
        f'<span class="fr-link__detail">PDF - 0,52 Mb - {cms_date}</span>'
        "</a></body></html>"
    )


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


class MarneClientTest(unittest.TestCase):
    def test_find_annual_page_annee_courante(self):
        client = MarneRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), MENU_2026_URL)

    def test_find_annual_page_carte_exacte(self):
        client = MarneRaaClient(BASE_URL, "2024")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), TABLE_2024_URL)

    def test_find_annual_page_groupe_double_espace(self):
        client = MarneRaaClient(BASE_URL, "2022")
        client._get = fake_get({BASE_URL: SECTION_HTML, GROUP_URL: GROUP_2021_2023_HTML})
        self.assertEqual(
            client.find_annual_page(), GROUP_URL + "/RAA-Annee-2022"
        )

    def test_find_annual_page_groupe_2013_2016(self):
        # 2016 : pas de carte exacte « 2016 » sur la section (le match
        # partiel sur « Années 2013 à 2016 » est interdit) → passage par
        # la carte de groupe.
        client = MarneRaaClient(BASE_URL, "2016")
        client._get = fake_get(
            {BASE_URL: SECTION_HTML, GROUP_2013_URL: GROUP_2013_2016_HTML}
        )
        self.assertEqual(
            client.find_annual_page(), GROUP_2013_URL + "/RAA-Annee-2016"
        )

    def test_menu_documents_for_month(self):
        client = MarneRaaClient(BASE_URL, "2026")
        client.annual_page_url = MENU_2026_URL
        client._get = fake_get({MENU_2026_URL: MENU_2026_HTML})
        client._post, posted = fake_post()
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            [
                "recueil-51-2026-020-recueil-des-actes-administratifs.pdf",
                "recueil-51-2026-040-recueil-des-actes-administratifs.pdf",
            ],
        )
        # POSTs avec le champ mensuel : 2 candidats février + l'option
        # sans date (balayeur) ; pas janvier.
        self.assertEqual(len(posted), 3)
        for data in posted:
            self.assertIn("Liste-des-RAA-liste-docs", data)

    def test_menu_option_cms_autre_mois_exclue(self):
        # L'option sans date (041) a un mois CMS de mars → exclue de
        # février.
        client = MarneRaaClient(BASE_URL, "2026")
        client.annual_page_url = MENU_2026_URL
        client._get = fake_get({MENU_2026_URL: MENU_2026_HTML})
        client._post, _ = fake_post()
        result = client.documents_for_month("02")
        self.assertEqual(len(result), 2)

    def test_table_documents_for_month(self):
        client = MarneRaaClient(BASE_URL, "2024")
        client.annual_page_url = TABLE_2024_URL
        pages = {
            TABLE_2024_URL: TABLE_2024_HTML,
            TABLE_2024_URL + "/RAA-Annee-2024/Recueil-n-2-1-du-1er-fevrier-2024":
                doc_page_html("recueil-51-2024-2-1.pdf", "08/02/2024"),
            TABLE_2024_URL + "/RAA-Annee-2024/Recueil-n-2-9-du-12-fevrier-2024":
                doc_page_html("recueil-51-2024-2-9.pdf", "12/02/2024"),
        }
        client._get = fake_get(pages)
        result = client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            ["recueil-51-2024-2-1.pdf", "recueil-51-2024-2-9.pdf"],
        )

    def test_table_mois_janvier(self):
        client = MarneRaaClient(BASE_URL, "2024")
        client.annual_page_url = TABLE_2024_URL
        pages = {
            TABLE_2024_URL: TABLE_2024_HTML,
            TABLE_2024_URL + "/RAA-Annee-2024/Recueil-1-20-du-31-janvier-2024":
                doc_page_html("recueil-51-2024-1-20.pdf", "31/01/2024"),
        }
        client._get = fake_get(pages)
        result = client.documents_for_month("01")
        self.assertEqual(
            [name for _, name in result], ["recueil-51-2024-1-20.pdf"]
        )


if __name__ == "__main__":
    unittest.main()
