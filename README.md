# TKI Kelompok 2 — NusaNews

Website pencarian berita berbasis **Boolean retrieval** untuk proyek UAS
mata kuliah STKI (Sistem Temu Kembali Informasi).

Sistem menerima query dengan operator `AND`, `OR`, `NOT` (dan tanda kurung),
mencarinya di **inverted index**, lalu menerapkan filter kategori, rentang
tahun, dan penulis. Hasil ditampilkan per halaman (pagination). Tidak ada
ranking: dokumen hanya cocok atau tidak cocok.

## Dataset

News Category Dataset (artikel HuffPost, 2012–2022), format JSON Lines.

- Dataset mentah: `data/raw/News_Category_Dataset_v3.json` — 209.527 record.
- Hasil cleaning: `data/clean.jsonl` — **209.069 record bersih, 34 kategori**
  (dibuat oleh `data/raw/clean.py`; 458 record dibuang: 6 headline kosong,
  41 duplikat link, 411 duplikat headline + tanggal).
- Kedua file dataset sengaja disimpan di repo ini.

Setiap record bersih berisi: `id, link, headline, category,
short_description, authors, year, date`. `id` adalah nomor baris di
`clean.jsonl` (0, 1, 2, ...) dan dipakai di seluruh sistem.

## Cara menjalankan

Butuh Python 3.10+.

```bash
pip install -r requirements.txt
python app.py
```

Lalu buka http://127.0.0.1:5000

Saat pertama kali start, server membaca `data/clean.jsonl` dan membangun
inverted index secara otomatis (sekitar 10 detik), lalu menyimpannya ke
`data/index.pkl`. Start berikutnya memakai index simpanan itu dan jauh
lebih cepat. Index juga bisa dibangun lebih dulu secara manual:

```bash
python index.py
```

Perintah itu juga mencetak waktu build dan pemakaian memori. Hasil
pengukuran pada data penuh: build ±5 detik, 88.457 kata unik, index
tersimpan 19,2 MB, dan server memakai sekitar 790 MB RAM saat berjalan
(dokumen + index dimuat di memori) — jadi hosting gratis 512 MB tidak
cukup; jalankan di localhost atau hosting dengan RAM lebih besar.

Untuk melihat tampilan saja tanpa backend pencarian:

```bash
python preview.py
```

## Sintaks query

| Contoh | Arti |
|---|---|
| `climate` | Dokumen yang mengandung kata "climate" |
| `climate AND policy` | Mengandung kedua kata |
| `climate OR policy` | Mengandung salah satu kata |
| `climate AND NOT policy` | Mengandung "climate" tapi tidak "policy" |
| `(climate OR energy) AND policy` | Pengelompokan dengan kurung |
| `climate policy` | Tanpa operator dianggap AND |

Aturan: operator boleh huruf besar/kecil; prioritas `NOT` > `AND` > `OR`;
frasa dalam tanda kutip tidak didukung; kata yang tidak ada di index
menghasilkan himpunan kosong; query tidak sah (kurung tidak berpasangan,
dua operator berturutan) menghasilkan error HTTP 400.

Endpoint: `GET /search?q=...&category=...&year_from=...&year_to=...&author=...&page=...`
mengembalikan JSON berisi `query, page, per_page, total_results,
total_pages, results`.

## Struktur proyek

```
├── app.py                  # Saddam: server Flask + endpoint /search
├── preprocess.py           # Ardi: load_docs, tokenize
├── index.py                # Naufal: build_index, simpan/muat pickle
├── boolean.py              # Daffa: search(query, index, all_ids)
├── tki_inverted_index.py   # Naufal: versi Colab asli (index frekuensi), sumber adaptasi index.py
├── preview.py              # Daffa: server khusus pratinjau frontend
├── data/
│   ├── raw/
│   │   ├── News_Category_Dataset_v3.json   # dataset asli
│   │   └── clean.py                        # Ardi: data cleaning
│   ├── clean.jsonl                         # hasil clean.py
│   └── index.pkl                           # hasil build index (tidak di-commit)
├── templates/
│   └── index.html          # Mike: tampilan (NusaNews)
├── static/
│   ├── style.css
│   └── app.js              # fetch ke /search
├── tests/
│   ├── test_preprocess.py
│   ├── test_index.py
│   └── test_boolean.py     # tes parser
├── docs/
│   └── filetree.txt
├── requirements.txt        # flask
├── .gitignore
└── README.md
```

Kontrak antarmuka antar bagian:

```python
load_docs(path) -> list[dict]
tokenize(text) -> list[str]
build_index(docs) -> dict[str, set[int]]
search(query, index, all_ids) -> set[int]
```

## Pembagian tugas

| # | Anggota | Tugas |
|---|---|---|
| 1 | Ardi Mustakim | Data cleaning & preprocessing (`clean.py`, `preprocess.py`) |
| 2 | Naufal | Inverted index (`index.py`) |
| 3 | Mohammad Daffa Aqilah | Boolean parser (`boolean.py`) |
| 4 | Saddam | Endpoint Flask, filter, pagination (`app.py`) |
| 5 | Mike | Tampilan (`templates/index.html`, `static/`) |

## Tes

```bash
python -m unittest discover -s tests -v
```
