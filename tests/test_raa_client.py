import os
import tempfile
import time
import unittest
from unittest import mock
from types import SimpleNamespace

import requests

from src.raa_client import (
    RaaError,
    RaaHttpClient,
    _bulk_reupload_inversion,
    du_day_month,
    parse_day_month,
    parse_month,
    relaxed_day_month,
    select_month_documents,
)


class ParseDayMonthTest(unittest.TestCase):
    def test_date_complete(self):
        self.assertEqual(parse_day_month("29/11/2024"), (29, 11))

    def test_detail_cms(self):
        self.assertEqual(
            parse_day_month("PDF - 19,38 Mb - 29/11/2024"), (29, 11)
        )

    def test_date_francaise(self):
        self.assertEqual(parse_day_month("28 août 2026.pdf"), (28, 8))

    def test_ordinal(self):
        self.assertEqual(parse_day_month("1er juillet 2026"), (1, 7))

    def test_jour_un_chiffre(self):
        self.assertEqual(parse_day_month("du 6 août 2026"), (6, 8))

    def test_sans_date(self):
        self.assertIsNone(parse_day_month("N°85-2026-131"))

    def test_mois_invalide(self):
        self.assertIsNone(parse_day_month("20/13/2026"))


class DuDayMonthTest(unittest.TestCase):
    def test_slug_sans_accents(self):
        # nom de fichier d'archive en slug : tirets bas, sans accents
        self.assertEqual(
            du_day_month("101-raa_secial_du_29_decembre_2017.pdf"), (29, 12)
        )

    def test_slug_ordinal(self):
        self.assertEqual(
            du_day_month("095-raa_special_du_1er_decembre_2017.pdf"), (1, 12)
        )

    def test_texte_classique(self):
        self.assertEqual(du_day_month("RAA du 28 août 2026"), (28, 8))

    def test_sans_du(self):
        self.assertIsNone(du_day_month("recueil_2026_183.pdf"))


class RelaxedDayMonthTest(unittest.TestCase):
    def test_date_complete(self):
        self.assertEqual(relaxed_day_month("RAA du 28 août 2026"), (28, 8))

    def test_mois_seul_slug(self):
        self.assertEqual(
            relaxed_day_month("raa_mensuel_no_89_-decembe_2018.pdf"), (None, 12)
        )

    def test_mois_seul_texte(self):
        self.assertEqual(
            relaxed_day_month("RAA mensuel n° 89 - Décembre 2018"), (None, 12)
        )

    def test_mai_ambigu(self):
        # « mai » doit être reconnu, pas lu dans un autre mot
        self.assertEqual(relaxed_day_month("recueil mai 2026.pdf"), (None, 5))

    def test_sans_date(self):
        self.assertIsNone(relaxed_day_month("recueil-53-2026-183.pdf"))


class ParseMonthConsistencyTest(unittest.TestCase):
    def test_cohérence_avec_day_month(self):
        for text in ("29/11/2024", "28 août 2026", "23062026", "20/13/2026", "x"):
            day_month = parse_day_month(text)
            expected = f"{day_month[1]:02d}" if day_month else None
            self.assertEqual(parse_month(text), expected, text)


class FakePdfResponse:
    """Réponse streamable minimale pour tester RaaHttpClient.download."""

    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size=65536):
        yield self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


COMPLETE_PDF = b"%PDF-1.4\n" + b"x" * 2000 + b"\n%%EOF"
TRUNCATED_PDF = b"%PDF-1.4\n" + b"y" * 2000  # sans %%EOF


class ThrottleTest(unittest.TestCase):
    def test_pause_entre_requetes(self):
        client = RaaHttpClient("http://x", request_delay=5.0)
        client._last_request_ts = time.monotonic()
        with mock.patch("time.sleep") as sleep:
            client._throttle()
        sleep.assert_called_once()
        self.assertTrue(0 < sleep.call_args[0][0] <= 5.0)

    def test_premiere_requete_sans_pause(self):
        client = RaaHttpClient("http://x", request_delay=5.0)
        with mock.patch("time.sleep") as sleep:
            client._throttle()
        sleep.assert_not_called()

    def test_delai_nul_pas_de_pause(self):
        client = RaaHttpClient("http://x", request_delay=0)
        with mock.patch("time.sleep") as sleep:
            client._throttle()
            client._throttle()
        sleep.assert_not_called()


class RetryDelayTest(unittest.TestCase):
    def test_coupure_connexion_cooldown_long(self):
        client = RaaHttpClient("http://x")
        self.assertEqual(
            client._retry_delay(requests.exceptions.ConnectionError(), 10), 90
        )

    def test_timeout_cooldown_long(self):
        client = RaaHttpClient("http://x")
        self.assertEqual(
            client._retry_delay(requests.exceptions.Timeout(), 10), 90
        )

    def test_refus_503_cooldown_long(self):
        client = RaaHttpClient("http://x")
        exc = requests.exceptions.HTTPError(response=SimpleNamespace(status_code=503))
        self.assertEqual(client._retry_delay(exc, 10), 90)

    def test_autre_erreur_backoff_court(self):
        client = RaaHttpClient("http://x")
        exc = requests.exceptions.HTTPError(response=SimpleNamespace(status_code=500))
        self.assertEqual(client._retry_delay(exc, 10), 10)


class DownloadResumeTest(unittest.TestCase):
    def setUp(self):
        self.client = RaaHttpClient("http://x", request_delay=0)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _path(self, name):
        return os.path.join(self._tmp.name, name)

    def test_reprend_fichier_complet(self):
        path = self._path("a.pdf")
        with open(path, "wb") as f:
            f.write(COMPLETE_PDF)
        with mock.patch.object(self.client.session, "get") as get:
            self.client.download("http://x/a.pdf", path)
        get.assert_not_called()

    def test_retélécharge_fichier_tronqué(self):
        path = self._path("a.pdf")
        with open(path, "wb") as f:
            f.write(TRUNCATED_PDF)
        with mock.patch.object(
            self.client.session, "get", return_value=FakePdfResponse(COMPLETE_PDF)
        ) as get:
            self.client.download("http://x/a.pdf", path)
        get.assert_called_once()
        self.assertTrue(self.client._is_complete_pdf(path))

    def test_retente_sur_coupure(self):
        calls = {"n": 0}

        def flaky(url, **kwargs):
            calls["n"] += 1
            if calls["n"] < 3:
                raise requests.exceptions.ConnectionError("RemoteDisconnected")
            return FakePdfResponse(COMPLETE_PDF)

        path = self._path("a.pdf")
        with mock.patch.object(self.client.session, "get", side_effect=flaky) as get, \
                mock.patch("time.sleep") as sleep:
            self.client.download("http://x/a.pdf", path)
        self.assertEqual(calls["n"], 3)
        self.assertTrue(sleep.called)  # cooldown après coupure

    def test_echec_definitif(self):
        def always_fail(url, **kwargs):
            raise requests.exceptions.ConnectionError("RemoteDisconnected")

        path = self._path("a.pdf")
        with mock.patch.object(
            self.client.session, "get", side_effect=always_fail
        ), mock.patch("time.sleep"):
            with self.assertRaises(RaaError):
                self.client.download("http://x/a.pdf", path)


def reupload_docs(n=6):
    """Simule une page d'archives re-publiée en masse le 17/04/2023 :
    tous les spans CMS portent cette date, le nom de fichier porte la
    vraie date de publication (août/septembre 2017)."""
    docs = []
    for i in range(n):
        docs.append(
            (
                f"http://x/file/{i}.pdf",
                f"1{i}-RAA du {10 + i} août 2017.pdf",
                (17, 4),
                (10 + i, 8),
            )
        )
    return docs


class BulkReuploadTest(unittest.TestCase):
    def test_signature_detectee(self):
        self.assertTrue(_bulk_reupload_inversion(reupload_docs()))

    def test_pas_de_signature_dates_dispersionnees(self):
        docs = [
            (f"http://x/{i}.pdf", f"RAA du {d} août 2026.pdf", (d, 8), (d, 8))
            for i, d in enumerate((1, 3, 5, 8, 12, 20), start=1)
        ]
        self.assertFalse(_bulk_reupload_inversion(docs))

    def test_pas_de_signature_dates_secondaires_cohérentes(self):
        # même date CMS partout mais les noms de fichier sont d'accord :
        # pas de re-upload, c'est un vrai même jour de publication
        docs = [
            (f"http://x/{i}.pdf", "RAA du 17 avril 2023.pdf", (17, 4), (17, 4))
            for i in range(6)
        ]
        self.assertFalse(_bulk_reupload_inversion(docs))

    def test_pas_assez_de_dates_cms(self):
        docs = reupload_docs(2)
        self.assertFalse(_bulk_reupload_inversion(docs))

    def test_select_utilise_le_secondaire_en_cas_de_reupload(self):
        result = select_month_documents(reupload_docs(), "08")
        self.assertEqual(
            [name for _, name in result],
            [f"1{i}-RAA du {10 + i} août 2017.pdf" for i in range(6)],
        )

    def test_reupload_mois_seuls_secondaires(self):
        # Cas Sarthe 2018 : re-upload le 01/09, noms en slug avec mois seul
        # (jour perdu) — le mois du nom de fichier fait foi.
        docs = [
            (
                f"http://x/{i}.pdf",
                f"raa_special_no_{80 + i}_-{mois}_2018.pdf",
                (1, 9),
                (None, m),
            )
            for i, (mois, m) in enumerate(
                [("aout", 8), ("septemb", 9), ("decembe", 12)] * 3
            )
        ]
        self.assertTrue(_bulk_reupload_inversion(docs))
        result = select_month_documents(docs, "08")
        self.assertEqual(len(result), 3)
        self.assertTrue(all("aout" in name for _, name in result))

    def test_select_cms_fait_foi_hors_reupload(self):
        docs = [
            ("http://x/a.pdf", "RAA du 17 avril 2023.pdf", (17, 4), (17, 4)),
            ("http://x/b.pdf", "RAA du 2 août 2023.pdf", (2, 8), (2, 8)),
            ("http://x/c.pdf", "RAA du 9 août 2023.pdf", (9, 8), (9, 8)),
        ]
        result = select_month_documents(docs, "08")
        self.assertEqual([name for _, name in result], ["RAA du 2 août 2023.pdf", "RAA du 9 août 2023.pdf"])


if __name__ == "__main__":
    unittest.main()
