# NusaNews

**Sistem Temu Kembali Berita berbasis Boolean Retrieval dan Inverted Index**

Proyek UAS mata kuliah STKI (Sistem Temu Kembali Informasi) — TKI Kelompok 2.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-backend-black)
![Dataset](https://img.shields.io/badge/dataset-209.069%20dokumen-informational)

---

## Daftar Isi

- [Tentang proyek](#tentang-proyek)
- [Dataset](#dataset)
- [Cara menjalankan](#cara-menjalankan)
- [Sintaks query](#sintaks-query)
- [Endpoint API](#endpoint-api)
- [Struktur proyek](#struktur-proyek)
- [Kontrak antarmuka](#kontrak-antarmuka)
- [Pembagian tugas](#pembagian-tugas)
- [Tes](#tes)

---

## Tentang proyek

NusaNews adalah website pencarian berita berbasis **Boolean retrieval**.

Sistem menerima query dengan operator `AND`, `OR`, `NOT` (dan tanda kurung),
mencarinya di **inverted index**, lalu menerapkan filter kategori, rentang
tahun, dan penulis. Hasil ditampilkan per halaman (pagination).

> **Tanpa ranking.** Dokumen hanya cocok atau tidak cocok — tidak ada skor
> relevansi. Semua dokumen yang lolos query dianggap sama relevannya.

---

## Dataset

**News Category Dataset** (artikel HuffPost, 2012–2022), format JSON Lines.

| Berkas | Isi |
| --- | --- |
| `data/raw/News_Category_Dataset_v3.json` | Dataset mentah — 209.527 record |
| `data/clean.jsonl` | Hasil cleaning — **209.069 record bersih, 34 kategori** |

Pembersihan dilakukan oleh `data/raw/clean.py`. Dari 209.527 record mentah,
**458 record dibuang**:

- 6 headline kosong
- 41 duplikat link
- 411 duplikat headline + tanggal

Kedua file dataset sengaja disimpan di repo ini.

Setiap record bersih berisi:

```json
["id", "link", "headline", "category", "short_description", "authors", "year", "date"]
```

`id` adalah nomor baris di `clean.jsonl` (0, 1, 2, ...) dan dipakai secara
konsisten di seluruh sistem.

---

## Cara menjalankan

Butuh **Python 3.10+**.

```bash
pip install -r requirements.txt
python app.py
```

Lalu buka <http://127.0.0.1:5000>

Saat pertama kali start, server membaca `data/clean.jsonl` dan membangun
inverted index secara otomatis (sekitar **10 detik**), lalu menyimpannya ke
`data/index.pkl`. Start berikutnya memakai index simpanan itu dan jauh lebih
cepat.

Index juga bisa dibangun lebih dulu secara manual:

```bash
python index.py
```

Perintah tersebut juga mencetak waktu build dan pemakaian memori. Hasil
pengukuran pada data penuh:

| Metrik | Nilai |
| --- | --- |
| Waktu build | ±5 detik |
| Kata unik | 88.457 |
| Ukuran `index.pkl` | 19,2 MB |
| RAM server saat berjalan | ±790 MB |

> **Catatan hosting:** dokumen + index dimuat seluruhnya di memori, sehingga
> hosting gratis dengan batas 512 MB **tidak cukup**. Jalankan di localhost
> atau di hosting dengan RAM lebih besar.

Untuk melihat tampilan saja tanpa backend pencarian:

```bash
python preview.py
```

---

## Sintaks query

| Contoh | Arti |
| --- | --- |
| `climate` | Dokumen yang mengandung kata "climate" |
| `climate AND policy` | Mengandung kedua kata |
| `climate OR policy` | Mengandung salah satu kata |
| `climate AND NOT policy` | Mengandung "climate" tapi tidak "policy" |
| `(climate OR energy) AND policy` | Pengelompokan dengan kurung |
| `climate policy` | Tanpa operator dianggap `AND` |

**Aturan:**

- Operator boleh huruf besar/kecil.
- Prioritas: `NOT` > `AND` > `OR`.
- Frasa dalam tanda kutip **tidak** didukung.
- Kata yang tidak ada di index menghasilkan himpunan kosong.
- Query tidak sah (kurung tidak berpasangan, dua operator berturutan)
  menghasilkan **HTTP 400**.

---

## Endpoint API

```
GET /search?q=...&category=...&year_from=...&year_to=...&author=...&page=...
```

Mengembalikan JSON dengan field:

| Field | Keterangan |
| --- | --- |
| `query` | Query yang diproses |
| `page` | Halaman yang diminta |
| `per_page` | Jumlah hasil per halaman |
| `total_results` | Total dokumen yang cocok |
| `total_pages` | Total halaman |
| `results` | Daftar dokumen pada halaman tersebut |

---

## Struktur proyek

```
├── app.py                  # Saddam: server Flask + endpoint /search
├── preprocess.py           # Ardi: load_docs, tokenize
├── index.py                # Naufal: build_index, simpan/muat pickle
├── boolean.py              # Daffa: search(query, index, all_ids)
├── tki_inverted_index.py   # Naufal: versi Colab asli (index frekuensi),
│                           #         sumber adaptasi index.py
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

---

## Kontrak antarmuka

Kesepakatan antar bagian, supaya tiap modul bisa dikerjakan terpisah:

```python
load_docs(path) -> list[dict]
tokenize(text) -> list[str]
build_index(docs) -> dict[str, set[int]]
search(query, index, all_ids) -> set[int]
```

| Fungsi | Modul | Penanggung jawab |
| --- | --- | --- |
| `load_docs`, `tokenize` | `preprocess.py` | Ardi |
| `build_index` | `index.py` | Naufal |
| `search` | `boolean.py` | Daffa |

---

## Pembagian tugas

| # | Anggota | Tugas |
| --- | --- | --- |
| 1 | Ardi Mustakim | Data cleaning & preprocessing (`clean.py`, `preprocess.py`) |
| 2 | Naufal | Inverted index (`index.py`) |
| 3 | Mohammad Daffa Aqilah | Boolean parser (`boolean.py`) |
| 4 | Saddam | Endpoint Flask, filter, pagination (`app.py`) |
| 5 | Mike | Tampilan (`templates/index.html`, `static/`) |

---

## Tes

```bash
python -m unittest discover -s tests -v
```