import unittest
from types import SimpleNamespace

from vendee_client import VendeeRaaClient, label_month, parse_month

BASE_2026 = (
    "https://www.vendee.gouv.fr/Publications/Recueil-des-actes-administratifs/"
    "Recueils-des-Actes-Administratifs-2026"
)

# Page d'archive 2017 : liens directs, libellé « publié le » = vraie date,
# span CMS = date de re-publication (identique pour tous).
_ARCHIVE_ROWS = [
    ("2017-48.pdf", "SPECIAL 2017- 48", "16 août 2017"),
    ("2017-49.pdf", "2017-49", "17 août 2017"),
    ("2017-50.pdf", "2017-50", "18 août 2017"),
    ("2017-70.pdf", "2017-70", "12 octobre 2017"),
    ("2017-71.pdf", "2017-71", "19 octobre 2017"),
    ("2017-72.pdf", "2017-72", "26 octobre 2017"),
]


def _archive_link(i, nom, num, publie):
    return (
        f'<a class="fr-link fr-link--download" '
        f'href="/content/download/{i}/{i}/file/{nom}">\n'
        f"Télécharger {num} publié le {publie} PDF - 5,0 Mb - 05/08/2023</a>\n"
    )


ARCHIVE_2017_HTML = (
    "<html><body>\n"
    + "".join(
        _archive_link(i, nom, num, publie)
        for i, (nom, num, publie) in enumerate(_ARCHIVE_ROWS, start=1)
    )
    + "</body></html>\n"
)


class ParseMonthTest(unittest.TestCase):
    def test_date_complete(self):
        self.assertEqual(parse_month("29/11/2024"), "11")

    def test_annee_trois_chiffres(self):
        self.assertEqual(parse_month("20/08/026"), "08")

    def test_separateurs_doublés(self):
        self.assertEqual(parse_month("19//06/2026"), "06")

    def test_sans_annee(self):
        self.assertEqual(parse_month("17/08"), "08")

    def test_date_francaise(self):
        self.assertEqual(parse_month("4 novembre 2024"), "11")
        self.assertEqual(parse_month("5 janvier 2024"), "01")

    def test_mois_invalide(self):
        self.assertIsNone(parse_month("20/13/2026"))

    def test_jour_invalide(self):
        self.assertIsNone(parse_month("85-2026"))

    def test_detail_cms(self):
        self.assertEqual(parse_month("PDF - 19,38 Mb - 29/11/2024"), "11")

    def test_sans_date(self):
        self.assertIsNone(parse_month("N°85-2026-131"))


class LabelMonthTest(unittest.TestCase):
    def test_annee_trois_chiffres(self):
        # doc 168 (2026), faute réelle du site
        label = "Recueil des actes administratifs nominatif 2026-168 (publié le 20/08/026)."
        value = "Recueil-des-actes-administratifs-nominatif-2026-168-publie-le-20-08-026"
        self.assertEqual(label_month(label, value), "08")

    def test_separateurs_doublés(self):
        # doc 118 (2026), faute réelle du site
        label = "Recueil des actes administratifs 2026-118 (publié le 19//06/2026)."
        value = "Recueil-des-actes-administratifs-2026-118-publie-le-19-06-2026"
        self.assertEqual(label_month(label, value), "06")

    def test_sans_le(self):
        # doc 167 (2026)
        label = "Recueil des actes administratifs spécial 2026 -167 (publié 17/08/2026)"
        value = "Recueil-des-actes-administratifs-special-2026-167-publie-17-08-2026"
        self.assertEqual(label_month(label, value), "08")

    def test_date_francaise(self):
        # doc 193 (2024)
        label = "Recueil des actes administratifs spécial 2024-193 (publié le 04 novembre 2024)"
        value = "Recueil-des-actes-administratifs-special-2024-193-publie-le-04-novembre-2024"
        self.assertEqual(label_month(label, value), "11")

    def test_sans_date_nulle_part(self):
        # doc 131 (2026), aucune date dans le libellé ni la valeur
        label = "RECUEIL DES ACTES ADMINISTRATIFS SPÉCIAL N°85-2026-131"
        value = "RECUEIL-DES-ACTES-ADMINISTRATIFS-SPECIAL-N-85-2026-131"
        self.assertIsNone(label_month(label, value))

    def test_pas_de_parsing_non_ancre(self):
        # « 2026-118 » seul ne doit pas être lu comme une date du 26/11
        self.assertIsNone(label_month("Recueil des actes administratifs 2026-118", ""))

    def test_slug_en_recul(self):
        label = "Recueil des actes administratifs 2026-119"
        value = "Recueil-des-actes-administratifs-2026-119-publie-le-03-09-2026"
        self.assertEqual(label_month(label, value), "09")


class VendeeArchiveTest(unittest.TestCase):
    def setUp(self):
        self.client = VendeeRaaClient(BASE_2026, "2017")
        self.client._get = lambda url: SimpleNamespace(text=ARCHIVE_2017_HTML)

    def test_url_base_bascule_sur_archives(self):
        self.assertEqual(
            self.client.base_url,
            "https://www.vendee.gouv.fr/Publications/Recueil-des-actes-administratifs/"
            "Consultez-les-archives-1999-2019/2017/2017",
        )

    def test_url_base_inchangee_annee_recente(self):
        client = VendeeRaaClient(BASE_2026, "2020")
        self.assertEqual(client.base_url, BASE_2026)

    def test_documents_for_month_aout(self):
        # Le span CMS (05/08/2023, re-upload) est contredit par les
        # libellés → le libellé « publié le » fait foi.
        result = self.client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            ["2017-48.pdf", "2017-49.pdf", "2017-50.pdf"],
        )

    def test_documents_for_month_octobre(self):
        result = self.client.documents_for_month("10")
        self.assertEqual(
            [name for _, name in result],
            ["2017-70.pdf", "2017-71.pdf", "2017-72.pdf"],
        )


if __name__ == "__main__":
    unittest.main()
