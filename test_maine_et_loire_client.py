import unittest
from types import SimpleNamespace

from bs4 import BeautifulSoup

from maine_et_loire_client import (
    MaineEtLoireRaaClient,
    find_annual_href,
    filename_month,
    link_day_month,
)
from raa_client import parse_month

PAGES_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/Annee-2026">Année 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/Annee-2025">Année 2025</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/Archives-RAA">Archives RAA</a></h2>
</body></html>
"""


class FilenameMonthTest(unittest.TestCase):
    def test_date_francaise_accents(self):
        self.assertEqual(filename_month("168-RAA du 28 août 2026.pdf"), "08")

    def test_jour_un_chiffre(self):
        self.assertEqual(filename_month("158-RAA spécial du 6 août 2026.pdf"), "08")

    def test_date_compacte(self):
        # faute réelle : date sans séparateurs
        self.assertEqual(filename_month("114 - RAA  spécial du 23062026.pdf"), "06")

    def test_date_sans_annee(self):
        # faute réelle : année absente
        self.assertEqual(filename_month("006-RRA special du 08 janvier_tempete.pdf"), "01")

    def test_mai(self):
        self.assertEqual(filename_month("093-RAA du 29 mai 2026.pdf"), "05")

    def test_fevrier(self):
        self.assertEqual(filename_month("042-RAA spécial du 27 février 2026.pdf"), "02")

    def test_rediffusion(self):
        self.assertEqual(
            filename_month("031-RAA du 11 février 2026 (re-diffusion).pdf"), "02"
        )

    def test_non_raa_sans_date(self):
        # un arrêté sans date ne doit pas être daté
        name = ("Arrêté N SIDPC-2026-069 portant mesures temporaires de "
                "prévention et de protection des forêts contre les incendies "
                "dans le cadre du niveau de risque incendie élevé (orange).pdf")
        self.assertIsNone(filename_month(name))

    def test_numero_pas_daté(self):
        # « 2026-069 » seul ne doit pas être lu comme une date du 26/06
        self.assertIsNone(filename_month("RAA-2026-069.pdf"))


class ParseMonthTest(unittest.TestCase):
    def test_compact_invalide(self):
        # 8 chiffres mais mois invalide
        self.assertIsNone(parse_month("ref 13132026 doc"))

    def test_compact_valide(self):
        self.assertEqual(parse_month("ref 13062026 doc"), "06")

    def test_date_francaise_sans_annee(self):
        self.assertEqual(parse_month("publié le 4 mars"), "03")

    def test_ordinal(self):
        # faute réelle : « 1er » avec ordinal
        self.assertEqual(filename_month("120 - RAA du 1er juillet 2026.pdf"), "07")


LINKS_HTML = """
<div class="fr-col-12 fr-col-md-8">
<a class="fr-link fr-link--download" href="/contenu/telechargement/32647/209063/file/168-RAA du 28 août 2026.pdf">
    Télécharger 168-RAA du 28 août 2026
    <span class="fr-link__detail">PDF - 10,51 Mb - 28/08/2026</span>
</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/1/2/file/recueil-49-2026-162-recueil-des-actes-administratifs-special.pdf">
    Télécharger recueil-49-2026-162
    <span class="fr-link__detail">PDF - 1,2 Mb - 31/07/2026</span>
</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/3/4/file/sans-span.pdf">Télécharger</a>
</div>
"""


class LinkDayMonthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.links = BeautifulSoup(LINKS_HTML, "html.parser").select(
            "a.fr-link--download"
        )

    def test_span_cms(self):
        self.assertEqual(link_day_month(self.links[0]), (28, 8))

    def test_span_cms_mais_nom_sans_date(self):
        self.assertEqual(link_day_month(self.links[1]), (31, 7))

    def test_sans_span(self):
        self.assertIsNone(link_day_month(self.links[2]))


class FindAnnualHrefTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.soup = BeautifulSoup(PAGES_HTML, "html.parser")

    def test_année_trouvée(self):
        self.assertEqual(
            find_annual_href(self.soup, "2026"),
            "/Publications/Recueil-des-Actes-Administratifs/Annee-2026",
        )

    def test_année_inconnue(self):
        self.assertIsNone(find_annual_href(self.soup, "2021"))

    def test_archives_ne_sont_pas_confondues(self):
        self.assertEqual(
            find_annual_href(self.soup, "2025"),
            "/Publications/Recueil-des-Actes-Administratifs/Annee-2025",
        )


BASE_M49 = (
    "https://www.maine-et-loire.gouv.fr/Publications/"
    "Recueil-des-Actes-Administratifs"
)

# Page publications : années récentes + carte « Archives RAA »
# (les années 2005-2021 y sont sous forme de cartes « Année YYYY »).
PUBLICATIONS_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/Annee-2026">Année 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/Archives-RAA">Archives RAA</a></h2>
</body></html>
"""

ARCHIVES_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/Archives-RAA/Annee-2017">Année 2017</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-des-Actes-Administratifs/Archives-RAA/Annee-2016">Année 2016</a></h2>
</body></html>
"""


class MaineEtLoireArchivesTest(unittest.TestCase):
    def setUp(self):
        self.client = MaineEtLoireRaaClient(BASE_M49, "2017")
        pages = {BASE_M49: PUBLICATIONS_HTML, BASE_M49 + "/Archives-RAA": ARCHIVES_HTML}
        self.client._get = lambda url: SimpleNamespace(text=pages[url])

    def test_annual_page_via_archives(self):
        self.assertEqual(
            self.client.find_annual_page(),
            BASE_M49 + "/Archives-RAA/Annee-2017",
        )

    def test_annual_page_recente_sur_publications(self):
        client = MaineEtLoireRaaClient(BASE_M49, "2026")
        pages = {BASE_M49: PUBLICATIONS_HTML}
        client._get = lambda url: SimpleNamespace(text=pages[url])
        self.assertEqual(
            client.find_annual_page(), BASE_M49 + "/Annee-2026"
        )


if __name__ == "__main__":
    unittest.main()
