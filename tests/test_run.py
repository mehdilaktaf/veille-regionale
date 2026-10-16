import unittest

from run import limit_to_recent, merged_filename, resolve_department, resolve_month


class LimitToRecentTest(unittest.TestCase):
    def test_no_limit(self):
        links = [("u1", "a.pdf"), ("u2", "b.pdf"), ("u3", "c.pdf")]
        self.assertEqual(limit_to_recent(links, 0), links)

    def test_limit_larger_than_list(self):
        links = [("u1", "a.pdf"), ("u2", "b.pdf")]
        self.assertEqual(limit_to_recent(links, 5), links)

    def test_keeps_most_recent(self):
        links = [("u1", "a.pdf"), ("u2", "b.pdf"), ("u3", "c.pdf"), ("u4", "d.pdf")]
        self.assertEqual(limit_to_recent(links, 3), links[1:])

    def test_exact_size(self):
        links = [("u1", "a.pdf"), ("u2", "b.pdf")]
        self.assertEqual(limit_to_recent(links, 2), links)

    def test_empty(self):
        self.assertEqual(limit_to_recent([], 3), [])


class MergedFilenameTest(unittest.TestCase):
    def test_full(self):
        self.assertEqual(
            merged_filename("août", "2026", "Mayotte"),
            "RAA_fusionne_août_2026_Mayotte.pdf",
        )

    def test_partial(self):
        self.assertEqual(
            merged_filename("août", "2026", "Mayotte", partial=True),
            "RAA_fusionne_partiel_août_2026_Mayotte.pdf",
        )


class ResolveTest(unittest.TestCase):
    def test_resolve_month_code(self):
        self.assertEqual(resolve_month("08"), "08")

    def test_resolve_month_name(self):
        self.assertEqual(resolve_month("Août"), "08")
        self.assertEqual(resolve_month("aout"), "08")

    def test_resolve_month_unknown(self):
        with self.assertRaises(SystemExit):
            resolve_month("13")

    def test_resolve_department_accents(self):
        self.assertEqual(resolve_department("reunion"), "Réunion")
        self.assertEqual(resolve_department("Réunion"), "Réunion")

    def test_resolve_department_unknown(self):
        with self.assertRaises(SystemExit):
            resolve_department("Paris")


if __name__ == "__main__":
    unittest.main()
