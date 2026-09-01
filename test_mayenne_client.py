import unittest
from types import SimpleNamespace

from mayenne_client import MayenneRaaClient

BASE_URL = "https://www.mayenne.gouv.fr/Publications/Recueil-Actes-Administratifs/Annee-2026"

# Layout 2025+ : cartes mois sur la page annuelle
ANNUAL_CARDS_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueil-Actes-Administratifs/Annee-2026/Juin-2026">Juin 2026</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueil-Actes-Administratifs/Annee-2026/Aout-2026">Août 2026</a></h2>
</body></html>
"""

# Page mensuelle : un doublon de nom (183 posté deux fois, la 1re fois
# avec span CMS), un doc daté du texte, un doc hors mois, un doc sans date.
MONTH_AOUT_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/recueil-53-2026-183-special.pdf">
<span class="fr-link__detail">PDF - 0,26 Mb - 28/08/2026</span>Télécharger recueil-53-2026-183-special.pdf</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/2/2/file/recueil-53-2026-184-special.pdf">
RAA spécial du 28 août 2026</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/3/3/file/recueil-53-2026-183-special.pdf">
RAA spécial du 24 août 2026</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/4/4/file/recueil-53-2026-185-special.pdf">
RAA spécial du 1er septembre 2026</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/5/5/file/recueil-53-2026-999.pdf">
RAA sans date</a>
</body></html>
"""

# Page juin : un doc de juin (exclu du run d'août) + un doc dont le mois
# CMS (février) diffère du mois de la page (balayeur).
MONTH_JUIN_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/6/6/file/recueil-53-2026-150.pdf">
<span class="fr-link__detail">PDF - 1,0 Mb - 15/06/2026</span>RAA du 15 juin 2026</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/7/7/file/recueil-53-2026-151.pdf">
<span class="fr-link__detail">PDF - 1,0 Mb - 02/02/2026</span>RAA du 2 février 2026</a>
</body></html>
"""

# Layout ancien (2024) : liens directs sur la page annuelle, dates dans le texte
ANNUAL_DIRECT_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/6/6/file/recueil-53-2024-200.pdf">
RAA du 31 décembre 2024</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/7/7/file/recueil-53-2024-199-special.pdf">
RAA spécial du 30 décembre 2024</a>
</body></html>
"""


def fake_get(pages):
    def _get(url):
        return SimpleNamespace(text=pages[url])
    return _get


class MayenneClientCardsTest(unittest.TestCase):
    """Layout 2025+ : cartes mois puis page mensuelle (balayeur de l'année)."""

    def setUp(self):
        self.client = MayenneRaaClient(BASE_URL)
        pages = {
            BASE_URL: ANNUAL_CARDS_HTML,
            BASE_URL + "/Aout-2026": MONTH_AOUT_HTML,
            BASE_URL + "/Juin-2026": MONTH_JUIN_HTML,
        }
        self.client._get = fake_get(pages)

    def test_balaie_toutes_les_pages_mois(self):
        documents = self.client.list_documents()
        names = [name for _, name, _, _ in documents]
        # 4 docs d'août (doublon 183 fusionné) + 2 docs de juin
        self.assertEqual(len(names), 6)

    def test_dedoublonne_prefere_span_cms(self):
        documents = self.client.list_documents()
        names = [name for _, name, _, _ in documents]
        self.assertEqual(names.count("recueil-53-2026-183-special.pdf"), 1)
        kept = [d for d in documents if d[1] == "recueil-53-2026-183-special.pdf"][0]
        self.assertEqual(kept[2], (28, 8))

    def test_documents_for_month(self):
        result = self.client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            ["recueil-53-2026-183-special.pdf", "recueil-53-2026-184-special.pdf"],
        )
        self.assertTrue(
            result[0][0].endswith("/file/recueil-53-2026-183-special.pdf")
        )


class MayenneClientDirectTest(unittest.TestCase):
    """Layout ancien : liens directs sur la page annuelle."""

    def setUp(self):
        url_2024 = (
            "https://www.mayenne.gouv.fr/Publications/"
            "Recueil-Actes-Administratifs/Annee-2024"
        )
        self.client = MayenneRaaClient(url_2024)
        self.client._get = fake_get({url_2024: ANNUAL_DIRECT_HTML})

    def test_documents_for_month_decembre(self):
        result = self.client.documents_for_month("12")
        self.assertEqual(
            [name for _, name in result],
            ["recueil-53-2024-199-special.pdf", "recueil-53-2024-200.pdf"],
        )

    def test_mais_pas_autre_mois(self):
        self.assertEqual(self.client.documents_for_month("01"), [])


if __name__ == "__main__":
    unittest.main()
