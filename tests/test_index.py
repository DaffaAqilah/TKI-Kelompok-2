"""Tes untuk index.build_index (tugas 2) dan simpan/muat pickle.

Jalankan dari folder root repo:
    python -m unittest discover -s tests -v
atau langsung:
    python tests/test_index.py
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from index import build_index, build_index_freq, load_index, save_index

DOCS = [
    {"id": 0, "text": "Climate policy and climate change"},
    {"id": 1, "headline": "Gaming news today", "short_description": "Climate in gaming"},
    {"id": 2, "text": ""},
]


class TestBuildIndex(unittest.TestCase):
    def setUp(self):
        self.index = build_index(DOCS)

    def test_pemetaan_kata_ke_dokumen(self):
        self.assertEqual(self.index["climate"], {0, 1})
        self.assertEqual(self.index["policy"], {0})
        self.assertEqual(self.index["gaming"], {1})

    def test_hasil_sesuai_kontrak(self):
        self.assertIsInstance(self.index, dict)
        for term, ids in self.index.items():
            self.assertIsInstance(term, str)
            self.assertIsInstance(ids, set)
            for doc_id in ids:
                self.assertIsInstance(doc_id, int)

    def test_kata_berulang_dalam_satu_dokumen_dihitung_satu_kali(self):
        # "climate" muncul 2x di dokumen 0, tetap satu entri.
        self.assertEqual(self.index["climate"], {0, 1})

    def test_stopword_tidak_masuk_index(self):
        self.assertNotIn("and", self.index)

    def test_field_text_cadangan_dari_headline_dan_deskripsi(self):
        # Dokumen 1 tidak punya "text"; build_index memakai
        # headline + short_description.
        self.assertEqual(self.index["news"], {1})
        self.assertEqual(self.index["today"], {1})

    def test_dokumen_kosong_tidak_menghasilkan_kata(self):
        for ids in self.index.values():
            self.assertNotIn(2, ids)

    def test_index_frekuensi_naufal(self):
        # Logika asli tki_inverted_index.py: frekuensi dihitung per dokumen.
        freq = build_index_freq(DOCS)
        self.assertEqual(freq["climate"], {0: 2, 1: 1})
        self.assertEqual(freq["policy"], {0: 1})
        self.assertEqual(freq["gaming"], {1: 2})

    def test_index_boolean_konversi_dari_frekuensi(self):
        # build_index harus sama dengan kunci-kunci index frekuensi.
        freq = build_index_freq(DOCS)
        for term, doc_freqs in freq.items():
            self.assertEqual(self.index[term], set(doc_freqs))

    def test_pickle_bolak_balik(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.pkl"
            save_index(self.index, path)
            self.assertEqual(load_index(path), self.index)


if __name__ == "__main__":
    unittest.main()
