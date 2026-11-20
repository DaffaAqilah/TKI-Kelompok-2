"""Inverted index untuk proyek STKI Kelompok 2 (tugas 2: Naufal).

File ini adalah adaptasi resmi dari tki_inverted_index.py milik
Naufal (hasil ekspor notebook Colab-nya) agar sesuai kontrak kelompok
dan bisa dipakai app.py + boolean.py:

    Dipertahankan dari kode Naufal:
    - Cara membangun index: frekuensi setiap kata dihitung dulu per
      dokumen, lalu dimasukkan ke inverted index, sehingga index
      frekuensi (kata -> {id dokumen: jumlah kemunculan}) tetap
      tersedia lewat build_index_freq. Index frekuensi ini modal
      untuk ranking TF-IDF bila kelompok menambahkannya nanti.
    - Penyimpanan index dengan pickle dan pola "muat pickle kalau
      ada, bangun baru kalau belum" (di app.py pola ini diteruskan).

    Disesuaikan:
    - Masukan berupa daftar dokumen hasil load_docs (kontrak:
      build_index(docs)), bukan path file dataset mentah, supaya id
      dokumen selalu id clean.jsonl dan tidak bergeser.
    - Tokenisasi memakai tokenize dari preprocess.py (milik Ardi),
      sesuai kesepakatan kelompok bahwa dokumen dan query diproses
      dengan tokenize yang sama. (Di notebook aslinya Naufal memakai
      regex sendiri tanpa stopword; hasil pencarian Boolean-nya
      terbukti identik, hanya index-nya menyimpan stopword yang
      tidak pernah terpakai query.)
    - build_index mengembalikan dict[str, set[int]] sesuai kontrak,
      dikonversi dari index frekuensi di atas.
    - Tidak ada kode yang langsung berjalan saat file di-import
      (di file asli ada blok eksekusi di bagian bawah).

Kontrak:
    build_index(docs)      -> dict[str, set[int]]
    build_index_freq(docs) -> dict[str, dict[int, int]]
    docs: list[dict] hasil load_docs; setiap dokumen punya "id" dan
    "text" (headline + short_description). Kalau "text" tidak ada,
    dipakai headline + short_description.

Jalankan sebagai skrip untuk membangun index dari data penuh,
mengukur waktu build dan pemakaian memori, lalu menyimpannya:

    python index.py

Hasil disimpan ke data/index.pkl dalam format yang langsung bisa
dipakai app.py (dict berisi index + penanda waktu/path dataset,
sama seperti format cache yang ditulis app.py sendiri), sehingga
server tidak perlu membangun ulang index saat pertama kali start.
"""

import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

from preprocess import load_docs, tokenize


def _peak_ram_mb():
    """RAM puncak proses ini (MB), atau None kalau tidak bisa diukur.

    Modul "resource" hanya ada di Linux/macOS — di Windows modul itu
    tidak tersedia, jadi pengukurannya memakai API Windows lewat
    ctypes. Fungsi ini hanya dipakai mode skrip (python index.py);
    kegagalan pengukuran tidak boleh menggagalkan build index.
    """
    if sys.platform == "win32":
        try:
            import ctypes

            class _ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong),
                    ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = _ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(counters),
                counters.cb,
            )
            if ok:
                return counters.PeakWorkingSetSize / (1024 * 1024)
        except Exception:
            pass
        return None
    try:
        import resource
    except ImportError:
        return None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return peak / (1024 * 1024)  # macOS: satuan byte
    return peak / 1024  # Linux: satuan kilobyte


def _doc_text(doc):
    text = doc.get("text")
    if text is None:
        text = (
            str(doc.get("headline") or "")
            + " "
            + str(doc.get("short_description") or "")
        ).strip()
    return text


def build_index_freq(docs):
    """Bangun inverted index frekuensi: kata -> {id dokumen: frekuensi}.

    Ini logika asli Naufal dari tki_inverted_index.py: frekuensi kata
    dihitung per dokumen lebih dulu, baru dimasukkan ke index.
    """
    inverted_index = defaultdict(dict)
    for doc in docs:
        doc_id = doc["id"]

        # Hitung frekuensi kata di dokumen ini
        term_freqs = defaultdict(int)
        for token in tokenize(_doc_text(doc)):
            term_freqs[token] += 1

        # Masukkan ke dalam inverted index
        for term, freq in term_freqs.items():
            inverted_index[term][doc_id] = freq

    return dict(inverted_index)


def build_index(docs):
    """Bangun inverted index Boolean: kata -> set id dokumen.

    Dikonversi dari index frekuensi Naufal, karena model Boolean
    hanya perlu tahu dokumen mengandung kata atau tidak.
    """
    freq_index = build_index_freq(docs)
    return {term: set(doc_freqs) for term, doc_freqs in freq_index.items()}


def save_index(index, path):
    """Simpan index mentah (dict[str, set[int]]) sebagai pickle."""
    with open(path, "wb") as file:
        pickle.dump(index, file, protocol=pickle.HIGHEST_PROTOCOL)


def load_index(path):
    """Muat index mentah yang disimpan save_index."""
    with open(path, "rb") as file:
        return pickle.load(file)


def _main():
    base_dir = Path(__file__).resolve().parent
    data_path = base_dir / "data" / "clean.jsonl"
    index_path = base_dir / "data" / "index.pkl"

    print(f"Membaca dokumen dari {data_path} ...")
    docs = load_docs(data_path)
    all_ids = {doc["id"] for doc in docs}
    print(f"Dokumen terbaca: {len(docs):,}")

    start = time.perf_counter()
    index = build_index(docs)
    build_seconds = time.perf_counter() - start

    total_postings = sum(len(ids) for ids in index.values())
    peak_mb = _peak_ram_mb()
    print(f"Waktu build index : {build_seconds:.2f} detik")
    print(f"Kata unik (terms) : {len(index):,}")
    print(f"Total posting     : {total_postings:,}")
    if peak_mb is None:
        print("RAM puncak proses : tidak bisa diukur di sistem ini")
    else:
        print(f"RAM puncak proses : {peak_mb:.0f} MB (termasuk dokumen di memori)")

    # Format yang sama dengan cache app.py: app memeriksa dataset_time
    # dan dataset_path sebelum memakai index simpanan ini.
    with index_path.open("wb") as file:
        pickle.dump(
            {
                "dataset_time": data_path.stat().st_mtime_ns,
                "dataset_path": str(data_path.resolve()),
                "index": index,
            },
            file,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    print(f"Index tersimpan   : {index_path} ({index_path.stat().st_size / 1e6:.1f} MB)")
    print(f"all_ids           : {len(all_ids):,} dokumen")


if __name__ == "__main__":
    _main()
