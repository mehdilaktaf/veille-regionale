import unittest
from types import SimpleNamespace

from eure_client import EureRaaClient

BASE_URL = "https://www.eure.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA"

# Page section : cartes « RAA YYYY » + cartes documents parasites
# (non confondues avec l'aiguille « RAA 2026 »).
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/RAA-2026">RAA 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/RAA-2025">RAA 2025</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/Recueil-special-n-27-2026-217-du-10-juillet-2026">Recueil spécial n°27-2026-217 du 10 juillet 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/Recueil-special-n-27-2026-009-du-07-janvier-20262">Recueil spécial n° 27-2026-009 du 07 janvier 2026</a></h2>
</body></html>
"""

# Page annuelle paginée : mois ancré « du » dans le titre ; typos réels du
# site (« oaût », « febvrier ») → mois non détectable.
ANNUAL_PAGE_1_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/RAA-2026/Recueil-special-N-27-2026-040-du-27-fevrier-2026">Recueil spécial N°27-2026-040 du 27 février 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/RAA-2026/Recueil-special-N-27-2026-039-du-14-oaut-2026">Recueil spécial N°27-2026-039 du 14 oaût 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/RAA-2026/Recueil-N-27-2026-037-du-31-janvier-2026">Recueil N°27-2026-037 du 31 janvier 2026</a></h2>
<ul class="fr-pagination__list"><li><a href="/Publications/Recueil-des-actes-administratifs-RAA/RAA-2026/(offset)/10">Suivant</a></li></ul>
</body></html>
"""

ANNUAL_PAGE_2_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/RAA-2026/Recueil-special-N-27-2026-038-du-20-fevrier-2026">Recueil spécial N°27-2026-038 du 20 février 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-actes-administratifs-RAA/RAA-2026/Recueil-special-N-27-2026-041-du-28-febvrier-2026">Recueil spécial N°27-2026-041 du 28 febvrier 2026</a></h2>
</body></html>
"""


def doc_html(filename, cms_date):
    return (
        "<html><body>"
        f'<a class="fr-link fr-link--download" '
        f'href="/contenu/telechargement/1/1/file/{filename}">'
        f"Télécharger {filename} "
        f'<span class="fr-link__detail">PDF - 7,71 Mb - {cms_date}</span>'
        "</a></body></html>"
    )


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


def pages_2026():
    return {
        BASE_URL: SECTION_HTML,
        BASE_URL + "/RAA-2026": ANNUAL_PAGE_1_HTML,
        BASE_URL + "/RAA-2026/(offset)/10": ANNUAL_PAGE_2_HTML,
        # Carte « oaût » (typo) : visitée au balayeur, CMS = août → exclue.
        BASE_URL + "/RAA-2026/Recueil-special-N-27-2026-039-du-14-oaut-2026": doc_html(
            "Recueil spécial N°27-2026-039 du 14 oaût 2026.pdf", "14/08/2026"
        ),
        # Carte « febvrier » (typo) : visitée au balayeur, CMS = février →
        # conservée (le pré-filtre seul l'aurait perdue).
        BASE_URL + "/RAA-2026/Recueil-special-N-27-2026-041-du-28-febvrier-2026": doc_html(
            "Recueil spécial N°27-2026-041 du 28 febvrier 2026.pdf", "28/02/2026"
        ),
        BASE_URL + "/RAA-2026/Recueil-special-N-27-2026-038-du-20-fevrier-2026": doc_html(
            "Recueil spécial N°27-2026-038 du 20 février 2026.pdf", "20/02/2026"
        ),
        BASE_URL + "/RAA-2026/Recueil-special-N-27-2026-040-du-27-fevrier-2026": doc_html(
            "Recueil spécial N°27-2026-040 du 27 février 2026.pdf", "27/02/2026"
        ),
    }


class EureClientTest(unittest.TestCase):
    def setUp(self):
        self.client = EureRaaClient(BASE_URL, "2026")
        self.client._get = fake_get(pages_2026())

    def test_find_annual_page(self):
        self.assertEqual(
            self.client.find_annual_page(), BASE_URL + "/RAA-2026"
        )

    def test_find_annual_page_ignore_cartes_parasites(self):
        # Les cartes « Recueil spécial ... 2026 » de la section ne doivent
        # pas masquer la carte d'année.
        client = EureRaaClient(BASE_URL, "2026")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(client.find_annual_page(), BASE_URL + "/RAA-2026")

    def test_card_month(self):
        self.assertEqual(
            self.client._card_month("Recueil spécial N°27-2026-040 du 27 février 2026"),
            "02",
        )
        self.assertIsNone(
            self.client._card_month("Recueil spécial N°27-2026-039 du 14 oaût 2026")
        )
        self.assertIsNone(self.client._card_month("Sommaire RAA"))

    def test_documents_for_month_fevrier(self):
        # Les 3 docs de février, dont celui à la carte typo « febvrier »
        # (récupéré au balayeur, CMS faisant foi) ; ordre chronologique.
        result = self.client.documents_for_month("02")
        self.assertEqual(
            [name for _, name in result],
            [
                "Recueil spécial N°27-2026-038 du 20 février 2026.pdf",
                "Recueil spécial N°27-2026-040 du 27 février 2026.pdf",
                "Recueil spécial N°27-2026-041 du 28 febvrier 2026.pdf",
            ],
        )

    def test_carte_typo_cms_aout_exclue_de_fevrier(self):
        result = self.client.documents_for_month("02")
        names = [name for _, name in result]
        self.assertFalse(any("039" in name for name in names))

    def test_balaie_toutes_les_pages(self):
        documents = self.client.list_documents("02")
        # 3 cartes visitées (27/02, 20/02 + 2 cartes typo) → 4 docs.
        self.assertEqual(len(documents), 4)

    def test_documents_for_month_vide(self):
        self.assertEqual(self.client.documents_for_month("05"), [])


if __name__ == "__main__":
    unittest.main()
