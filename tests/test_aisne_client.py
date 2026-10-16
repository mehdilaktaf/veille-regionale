import unittest
from types import SimpleNamespace

from aisne_client import AisneRaaClient

BASE_URL = (
    "https://www.aisne.gouv.fr/Publications/Recueil-des-Actes-Administratifs"
)

# Page section : cartes années (2012 en minuscule — coquille réelle du site)
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/RAA-Annee-2026">RAA Année 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/RAA-Annee-2025">RAA Année 2025</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/RAA-annee-2012">RAA année 2012</a></h2>
</body></html>
"""

# Page annuelle paginée : mois codé dans le nom de carte, carte « Sommaire »
# parasite.
ANNUAL_PAGE_1_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/RAA-Annee-2026/Sommaire-RAA">Sommaire RAA</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/RAA-Annee-2026/RAA_Janvier_02-2026-001">RAA_Janvier_02-2026-001</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/RAA-Annee-2026/RAA_Aout_02-2026-120">RAA_Aout_02-2026-120</a></h2>
<ul class="fr-pagination__list"><li><a href="/Publications/Recueil-des-Actes-Administratifs/RAA-Annee-2026/p2">Suivant</a></li></ul>
</body></html>
"""

ANNUAL_PAGE_2_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/RAA-Annee-2026/RAA_Aout_02-2026-121">RAA_Aout_02-2026-121</a></h2>
</body></html>
"""


def card_html(filename, cms_date):
    return (
        "<html><body>"
        f'<a class="fr-link fr-link--download" '
        f'href="/contenu/telechargement/1/1/file/{filename}">'
        f"Télécharger {filename} "
        f'<span class="fr-link__detail">PDF - 3,63 Mb - {cms_date}</span>'
        "</a></body></html>"
    )


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


def pages_2026():
    return {
        BASE_URL: SECTION_HTML,
        BASE_URL + "/RAA-Annee-2026": ANNUAL_PAGE_1_HTML,
        BASE_URL + "/RAA-Annee-2026/p2": ANNUAL_PAGE_2_HTML,
        BASE_URL + "/RAA-Annee-2026/RAA_Aout_02-2026-120": card_html(
            "recueil-02-2026-120-recueil-des-actes-administratifs.pdf", "15/08/2026"
        ),
        BASE_URL + "/RAA-Annee-2026/RAA_Aout_02-2026-121": card_html(
            "recueil-02-2026-121-recueil-des-actes-administratifs.pdf", "28/08/2026"
        ),
    }


class AisneClientTest(unittest.TestCase):
    def setUp(self):
        self.client = AisneRaaClient(BASE_URL, "2026")
        self.client._get = fake_get(pages_2026())

    def test_find_annual_page(self):
        self.assertEqual(
            self.client.find_annual_page(), BASE_URL + "/RAA-Annee-2026"
        )

    def test_find_annual_page_minuscule(self):
        client = AisneRaaClient(BASE_URL, "2012")
        client._get = fake_get({BASE_URL: SECTION_HTML})
        self.assertEqual(
            client.find_annual_page(), BASE_URL + "/RAA-annee-2012"
        )

    def test_documents_for_month_aout(self):
        result = self.client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            [
                "recueil-02-2026-120-recueil-des-actes-administratifs.pdf",
                "recueil-02-2026-121-recueil-des-actes-administratifs.pdf",
            ],
        )

    def test_mois_sans_carte_exclu(self):
        # Février : aucune carte « Fevrier » → aucune page document visitée.
        self.assertEqual(self.client.documents_for_month("02"), [])

    def test_balaie_toutes_les_pages(self):
        documents = self.client.list_documents("08")
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0][2], (15, 8))


if __name__ == "__main__":
    unittest.main()
