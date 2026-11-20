"""Tes untuk boolean.search (tugas 3).

Jalankan dari folder root repo:
    python -m unittest discover -s tests -v
atau langsung:
    python tests/test_boolean.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boolean import search

INDEX = {
    "climate": {0, 1, 2, 3},
    "policy": {1, 2, 4},
    "energy": {2, 3, 5},
    "gaming": {5, 6},
    "health": {0, 6},
    "covid": {3, 6},
    "19": {3},
}
ALL_IDS = set(range(7))


class TestBooleanSearch(unittest.TestCase):
    def test_kata_tunggal(self):
        self.assertEqual(search("climate", INDEX, ALL_IDS), {0, 1, 2, 3})

    def test_and(self):
        self.assertEqual(search("climate AND policy", INDEX, ALL_IDS), {1, 2})

    def test_or(self):
        self.assertEqual(search("policy OR gaming", INDEX, ALL_IDS), {1, 2, 4, 5, 6})

    def test_not_saja(self):
        self.assertEqual(search("NOT climate", INDEX, ALL_IDS), {4, 5, 6})

    def test_and_not(self):
        self.assertEqual(search("climate AND NOT policy", INDEX, ALL_IDS), {0, 3})

    def test_or_not(self):
        self.assertEqual(search("health OR NOT gaming", INDEX, ALL_IDS), {0, 1, 2, 3, 4, 6})

    def test_kurung(self):
        self.assertEqual(search("(climate OR energy) AND policy", INDEX, ALL_IDS), {1, 2})

    def test_kurung_bersarang(self):
        self.assertEqual(
            search("((climate OR gaming) AND NOT energy)", INDEX, ALL_IDS),
            {0, 1, 6},
        )

    def test_prioritas_and_di_atas_or(self):
        # AND dikerjakan dulu: climate OR (policy AND energy) = {0,1,2,3}
        # Kalau dari kiri ke kanan hasilnya {2,3}.
        self.assertEqual(search("climate OR policy AND energy", INDEX, ALL_IDS), {0, 1, 2, 3})

    def test_prioritas_not_paling_tinggi(self):
        # (NOT climate) AND policy = {4}
        self.assertEqual(search("NOT climate AND policy", INDEX, ALL_IDS), {4})

    def test_tanpa_operator_dianggap_and(self):
        self.assertEqual(search("climate policy", INDEX, ALL_IDS), {1, 2})

    def test_tanpa_operator_dengan_kurung(self):
        self.assertEqual(search("climate (policy OR gaming)", INDEX, ALL_IDS), {1, 2})

    def test_operator_huruf_kecil(self):
        self.assertEqual(search("Climate aNd Policy", INDEX, ALL_IDS), {1, 2})
        self.assertEqual(search("climate or gaming", INDEX, ALL_IDS), {0, 1, 2, 3, 5, 6})
        self.assertEqual(search("not climate", INDEX, ALL_IDS), {4, 5, 6})

    def test_kata_tidak_dikenal(self):
        self.assertEqual(search("zelda", INDEX, ALL_IDS), set())
        self.assertEqual(search("climate AND zelda", INDEX, ALL_IDS), set())
        self.assertEqual(search("climate OR zelda", INDEX, ALL_IDS), {0, 1, 2, 3})

    def test_query_kosong(self):
        self.assertEqual(search("", INDEX, ALL_IDS), set())
        self.assertEqual(search("   ", INDEX, ALL_IDS), set())

    def test_query_hanya_stopword(self):
        self.assertEqual(search("the", INDEX, ALL_IDS), set())
        self.assertEqual(search("the climate", INDEX, ALL_IDS), {0, 1, 2, 3})

    def test_kata_bertanda_hubung(self):
        # "covid-19" di-tokenize dokumen menjadi "covid" dan "19",
        # jadi query-nya harus menemukan dokumen yang mengandung dua-duanya.
        self.assertEqual(search("covid-19", INDEX, ALL_IDS), {3})

    def test_index_tidak_berubah(self):
        snapshot = {k: set(v) for k, v in INDEX.items()}
        search("NOT climate OR policy", INDEX, ALL_IDS)
        self.assertEqual(INDEX, snapshot)
        self.assertEqual(ALL_IDS, set(range(7)))

    def test_query_tidak_sah(self):
        for bad in [
            "(climate",            # kurung tidak berpasangan
            "climate)",            # kurung tutup berlebih
            "climate AND",         # operator di akhir
            "AND climate",         # operator biner di awal
            "OR climate",
            "climate AND OR policy",  # dua operator berturutan
            "NOT",                 # NOT tanpa kata
            "climate AND NOT",     # NOT di akhir
            "()",                  # kurung kosong
            "(climate AND)",       # operator sebelum kurung tutup
        ]:
            with self.subTest(query=bad):
                with self.assertRaises(ValueError):
                    search(bad, INDEX, ALL_IDS)


if __name__ == "__main__":
    unittest.main()
