import os
import tempfile
import time
import unittest
from unittest import mock
from types import SimpleNamespace

import requests

from raa_client import RaaError, RaaHttpClient, parse_day_month, parse_month


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


if __name__ == "__main__":
    unittest.main()
