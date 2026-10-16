import unittest
from types import SimpleNamespace

from martinique_client import MartiniqueRaaClient

BASE_URL = "https://www.martinique.gouv.fr/Publications/Recueils-des-actes-administratifs-publies"

# Page publications : carte RAA 2026 directe, cartes d'années anciennes
# sous « Archives ».
PUBLICATIONS_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs-publies/Archives">Archives</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs-publies/RAA-2026">RAA 2026</a></h2>
</body></html>
"""

ARCHIVES_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs-publies/Archives/RAAP-2024">RAAP 2024</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs-publies/Archives/RAA-2025">RAA 2025</a></h2>
</body></html>
"""

# Page annuelle 2026 : deux sous-cartes (RAA + spécial)
ANNUAL_2026_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs-publies/RAA-2026/Recueil-des-Actes-Administratifs">Recueil des Actes Administratifs</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs-publies/RAA-2026/Recueil-des-Actes-Administratifs-Special">Recueil des Actes Administratifs Spécial</a></h2>
</body></html>
"""

SUB_RAA_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/1/1/file/recueil-r02-2026-267.pdf">
<span class="fr-link__detail">PDF - 4,34 Mb - 26/08/2026</span>Télécharger</a>
<a class="fr-link fr-link--download" href="/contenu/telechargement/2/2/file/recueil-r02-2026-260.pdf">
<span class="fr-link__detail">PDF - 0,59 Mb - 01/08/2026</span>Télécharger</a>
</body></html>
"""

SUB_SPECIAL_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/3/3/file/recueil-r02-2026-268-special.pdf">
<span class="fr-link__detail">PDF - 2,04 Mb - 26/08/2026</span>Télécharger</a>
</body></html>
"""

ANNUAL_2024_HTML = """
<html><body>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs-publies/Archives/RAAP-2024/RAAP">RAAP</a></h2>
<h2 class="fr-card__title"><a href="/Publications/Recueils-des-actes-administratifs-publies/Archives/RAAP-2024/Editions-speciales">Éditions spéciales</a></h2>
</body></html>
"""

SUB_RAAP_2024_HTML = """
<html><body>
<a class="fr-link fr-link--download" href="/contenu/telechargement/4/4/file/recueil-r02-2024-300.pdf">
<span class="fr-link__detail">PDF - 1,00 Mb - 31/12/2024</span>Télécharger</a>
</body></html>
"""


def pages_2026():
    return {
        BASE_URL: PUBLICATIONS_HTML,
        BASE_URL + "/Archives": ARCHIVES_HTML,
        BASE_URL + "/RAA-2026": ANNUAL_2026_HTML,
        BASE_URL + "/RAA-2026/Recueil-des-Actes-Administratifs": SUB_RAA_HTML,
        BASE_URL + "/RAA-2026/Recueil-des-Actes-Administratifs-Special": SUB_SPECIAL_HTML,
    }


class MartiniqueClientTest(unittest.TestCase):
    def test_annual_page_annee_recente(self):
        client = MartiniqueRaaClient(BASE_URL, "2026")
        client._get = lambda url: SimpleNamespace(text=pages_2026()[url])
        self.assertEqual(
            client.find_annual_page(), BASE_URL + "/RAA-2026"
        )

    def test_annual_page_via_archives(self):
        client = MartiniqueRaaClient(BASE_URL, "2024")
        all_pages = pages_2026()
        all_pages[BASE_URL + "/Archives/RAAP-2024"] = ANNUAL_2024_HTML
        client._get = lambda url: SimpleNamespace(text=all_pages[url])
        self.assertEqual(
            client.find_annual_page(),
            BASE_URL + "/Archives/RAAP-2024",
        )

    def test_list_documents_toutes_les_sous_pages(self):
        client = MartiniqueRaaClient(BASE_URL, "2026")
        client._get = lambda url: SimpleNamespace(text=pages_2026()[url])
        documents = client.list_documents()
        self.assertEqual(
            sorted(name for _, name, _, _ in documents),
            [
                "recueil-r02-2026-260.pdf",
                "recueil-r02-2026-267.pdf",
                "recueil-r02-2026-268-special.pdf",
            ],
        )

    def test_documents_for_month_aout(self):
        client = MartiniqueRaaClient(BASE_URL, "2026")
        client._get = lambda url: SimpleNamespace(text=pages_2026()[url])
        result = client.documents_for_month("08")
        self.assertEqual(
            [name for _, name in result],
            [
                "recueil-r02-2026-260.pdf",
                "recueil-r02-2026-267.pdf",
                "recueil-r02-2026-268-special.pdf",
            ],
        )


if __name__ == "__main__":
    unittest.main()
