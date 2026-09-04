import unittest
from types import SimpleNamespace

from orne_client import OrneRaaClient

BASE_URL = "https://www.orne.gouv.fr/Publications/Recueil-des-Actes-Administratifs-RAA"
RAA_PAGE = BASE_URL + "/Le-Recueil-des-Actes-Administratifs-RAA"
ANNUAL_2026 = RAA_PAGE + "/Le-Recueil-des-Actes-Administratifs-2026"

# Page section : 1 carte « (RAA) », pas de menu latéral d'années.
SECTION_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA">Le Recueil des Actes Administratifs (RAA)</a></h2>
</body></html>
"""

# Page RAA : cartes h2 au MÊME texte qu'années mais href cassé (renvoi
# vers la page elle-même) + menu latéral a.fr-sidemenu__link aux hrefs
# corrects (2026 en majuscules, les autres en minuscules).
RAA_PAGE_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA">Le Recueil des Actes Administratifs 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA">Le Recueil des actes administratifs 2025</a></h2>
<a class="fr-sidemenu__link" href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-2026">Le Recueil des Actes Administratifs 2026</a>
<a class="fr-sidemenu__link" href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-actes-administratifs-2025">Le Recueil des actes administratifs 2025</a>
</body></html>
"""

# Page annuelle 2026 : cartes mois à nom seul + carte thématique à nom de
# mois (« Spéciaux du mois de juillet »).
ANNUAL_2026_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-2026/Janvier">Janvier</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-2026/Fevrier">Février</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-2026/Juillet">Juillet</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-Actes-Administratifs-2026/Speciaux-du-mois-de-juillet">Spéciaux du mois de juillet</a></h2>
</body></html>
"""


def orne_link(filename, pub_date):
    # Anchor réel de l'Orne : classes corrompues par le CMS (« <a
    # fr-link--download="" id='class="fr-link'... ») — le sélecteur
    # a.fr-link--download ne matche pas ; span fr-link__detail intact.
    label = filename.rsplit(".", 1)[0]
    return (
        '<li><a fr-link--download"="" '
        f'href="/contenu/telechargement/1/2/file/{filename}" '
        'id=\'class="fr-link\' target="_blank"> Télécharger '
        f"{label} <span class=\"fr-link__detail\">PDF - 0,43 Mb - {pub_date}</span> </a></li>"
    )


FEVRIER_HTML = (
    "<html><body><ul>"
    + orne_link("Spécial n° 1 du lundi 2 février 2026.pdf", "02/02/2026")
    # Annexe sans date dans le nom (la date vient du seul span CMS).
    + orne_link("Spécial n° 8 - DDT - SHC -Annexe 1 de l'arrêté n° 2330-2025-037.pdf", "11/02/2026")
    + orne_link("Spécial n° 20 du vendredi 27 février 2026.pdf", "27/02/2026")
    # « du <mois> » sans jour dans le nom.
    + orne_link("Spécial n° 21 du février 2026.pdf", "27/02/2026")
    + "</ul></body></html>"
)

JUILLET_HTML = (
    "<html><body><ul>"
    + orne_link("Spécial n° 40 du lundi 6 juillet 2026.pdf", "06/07/2026")
    # Présent aussi sur la carte « Spéciaux du mois de juillet » :
    # dédoublonné par nom.
    + orne_link("Spécial n° 40 du lundi 6 juillet 2026.pdf", "06/07/2026")
    + "</ul></body></html>"
)

SPECIAUX_JUILLET_HTML = (
    "<html><body><ul>"
    + orne_link("Spécial n° 40 du lundi 6 juillet 2026.pdf", "06/07/2026")
    + orne_link("Spécial n° 41 du mardi 7 juillet 2026.pdf", "07/07/2026")
    + "</ul></body></html>"
)

# Année ancienne éventuelle : menu latéral dès la section + liens directs
# sur la page annuelle (sans carte).
SECTION_2020_HTML = """
<html><body>
<a class="fr-sidemenu__link" href="/Publications/Recueil-des-Actes-Administratifs-RAA/Le-Recueil-des-actes-administratifs-2020">Le Recueil des actes administratifs 2020</a>
</body></html>
"""

ANNUAL_2020_HTML = (
    "<html><body><ul>"
    + orne_link("recueil-61-2020-010.pdf", "10/02/2020")
    + "</ul></body></html>"
)


def fake_get(pages):
    def _get(url):
        if url not in pages:
            raise AssertionError(f"URL non prévue : {url}")
        return SimpleNamespace(text=pages[url])
    return _get


def pages_2026():
    return {
        BASE_URL: SECTION_HTML,
        RAA_PAGE: RAA_PAGE_HTML,
        ANNUAL_2026: ANNUAL_2026_HTML,
        ANNUAL_2026 + "/Fevrier": FEVRIER_HTML,
        ANNUAL_2026 + "/Juillet": JUILLET_HTML,
        ANNUAL_2026 + "/Speciaux-du-mois-de-juillet": SPECIAUX_JUILLET_HTML,
    }


class OrneClientTest(unittest.TestCase):
    def setUp(self):
        self.client = OrneRaaClient(BASE_URL, "2026")
        self.client._get = fake_get(pages_2026())

    def test_find_annual_page(self):
        # Menu latéral (hrefs corrects), pas les cartes h2 cassées.
        self.assertEqual(self.client.find_annual_page(), ANNUAL_2026)

    def test_card_month(self):
        self.assertEqual(self.client._card_month("Février"), "02")
        self.assertEqual(self.client._card_month("Spéciaux du mois de juillet"), "07")
        self.assertIsNone(self.client._card_month("Sommaire"))

    def test_documents_for_month_fevrier(self):
        # Ordre (jour, nom) : n°01 (02/02), annexe (11/02, span faisant
        # foi — nom sans date), n°20 puis n°21 (27/02).
        self.assertEqual(
            [name for _, name in self.client.documents_for_month("02")],
            [
                "Spécial n° 1 du lundi 2 février 2026.pdf",
                "Spécial n° 8 - DDT - SHC -Annexe 1 de l'arrêté n° 2330-2025-037.pdf",
                "Spécial n° 20 du vendredi 27 février 2026.pdf",
                "Spécial n° 21 du février 2026.pdf",
            ],
        )

    def test_carte_thematique_meme_mois(self):
        # « Spéciaux du mois de juillet » = carte de juillet : visitée
        # avec « Juillet » pour 07, dédoublonnage par nom.
        self.assertEqual(
            [name for _, name in self.client.documents_for_month("07")],
            [
                "Spécial n° 40 du lundi 6 juillet 2026.pdf",
                "Spécial n° 41 du mardi 7 juillet 2026.pdf",
            ],
        )

    def test_carte_juillet_non_visitee_pour_fevrier(self):
        # Seules les cartes du mois cible + sans mois sont visitées : les
        # pages Juillet / Spéciaux sont retirées de la map → AssertionError
        # si visitées pour le mois 02.
        pages = pages_2026()
        del pages[ANNUAL_2026 + "/Juillet"]
        del pages[ANNUAL_2026 + "/Speciaux-du-mois-de-juillet"]
        client = OrneRaaClient(BASE_URL, "2026")
        client._get = fake_get(pages)
        self.assertEqual(len(client.documents_for_month("02")), 4)

    def test_mois_vide(self):
        self.assertEqual(self.client.documents_for_month("05"), [])

    def test_annee_ancienne_liens_directs(self):
        # Menu latéral dès la section (pas de carte intermédiaire) + page
        # annuelle sans carte : liens directs, span CMS faisant foi.
        client = OrneRaaClient(BASE_URL, "2020")
        client._get = fake_get(
            {
                BASE_URL: SECTION_2020_HTML,
                BASE_URL + "/Le-Recueil-des-actes-administratifs-2020": ANNUAL_2020_HTML,
            }
        )
        self.assertEqual(
            [name for _, name in client.documents_for_month("02")],
            ["recueil-61-2020-010.pdf"],
        )


if __name__ == "__main__":
    unittest.main()
