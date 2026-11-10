"""Data cleaning untuk News Category Dataset (JSON Lines).

Pakai:
    python clean.py [input] [output]

Default:
    data/raw/News_Category_Dataset.json -> data/clean.jsonl

Output: satu record JSON per baris dengan field
    id, link, headline, category, short_description, authors (list), year, date
`id` = nomor baris di clean.jsonl (0, 1, 2, ...) dan dipakai di seluruh sistem.
Hanya memakai library standar Python.
"""
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import date

IN_PATH = "data/raw/News_Category_Dataset_v3.json"
OUT_PATH = "data/clean.jsonl"

YEAR_MIN, YEAR_MAX = 2012, 2022

# Kategori kembar yang digabung. UBAH sesuai keputusan kelompok,
# lalu catat aturannya di laporan. Cek daftar asli lewat laporan di akhir run.
CATEGORY_MERGE = {
    "THE WORLDPOST": "WORLD NEWS",
    "WORLDPOST": "WORLD NEWS",
    "PARENTS": "PARENTING",
    "ARTS": "CULTURE & ARTS",
    "ARTS & CULTURE": "CULTURE & ARTS",
    "GREEN": "ENVIRONMENT",
    "STYLE": "STYLE & BEAUTY",
    "TASTE": "FOOD & DRINK",
}

# Nama "penulis" yang sebenarnya kantor berita, dibuang dari daftar penulis.
DROP_AUTHORS = {"ap"}

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
AUTHOR_SPLIT_RE = re.compile(r"\s*(?:,|;|&|\band\b)\s*", re.IGNORECASE)


def clean_text(value):
    """Normalisasi unicode (mis. spasi non-breaking), buang tag HTML, rapikan spasi."""
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKC", value)
    value = TAG_RE.sub(" ", value)
    return SPACE_RE.sub(" ", value).strip()


def strip_accents(value):
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def author_key(name):
    """Kunci pembanding: tanpa aksen dan huruf kecil (Dánica == DANICA == Danica)."""
    return strip_accents(name).lower()


def split_authors(raw):
    """'A and B, AP' -> ['A', 'B']. Nama HURUF BESAR diubah ke Title Case."""
    names = []
    for part in AUTHOR_SPLIT_RE.split(clean_text(raw)):
        part = part.strip()
        if not part or part.lower() in DROP_AUTHORS:
            continue
        if part.isupper():
            part = part.title()
        names.append(part)
    return names


def load_and_filter(path, stats):
    seen_links = set()
    seen_headline_date = set()
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stats["record dibaca"] += 1
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                stats["buang: baris rusak"] += 1
                continue
            if not isinstance(r, dict):
                stats["buang: baris rusak"] += 1
                continue

            headline = clean_text(r.get("headline"))
            if not headline:
                stats["buang: headline kosong"] += 1
                continue

            try:
                d = date.fromisoformat(clean_text(r.get("date")))
            except ValueError:
                stats["buang: tanggal rusak"] += 1
                continue
            if not YEAR_MIN <= d.year <= YEAR_MAX:
                stats["buang: tahun di luar rentang"] += 1
                continue

            link = clean_text(r.get("link"))
            if link and link in seen_links:
                stats["buang: duplikat link"] += 1
                continue
            hd_key = (headline.lower(), d.isoformat())
            if hd_key in seen_headline_date:
                stats["buang: duplikat headline+tanggal"] += 1
                continue
            if link:
                seen_links.add(link)
            seen_headline_date.add(hd_key)

            category = clean_text(r.get("category")).upper() or "UNKNOWN"
            category = CATEGORY_MERGE.get(category, category)

            rows.append({
                "link": link,
                "headline": headline,
                "category": category,
                "short_description": clean_text(r.get("short_description")),
                "authors": split_authors(r.get("authors")),
                "year": d.year,
                "date": d.isoformat(),
            })
    return rows


def unify_author_names(rows):
    """Satukan ejaan beda untuk orang yang sama, pakai ejaan paling sering muncul."""
    variants = {}
    for row in rows:
        for name in row["authors"]:
            variants.setdefault(author_key(name), Counter())[name] += 1
    canonical = {k: c.most_common(1)[0][0] for k, c in variants.items()}
    for row in rows:
        seen = set()
        unified = []
        for name in row["authors"]:
            name = canonical[author_key(name)]
            if name not in seen:  # buang nama ganda dalam satu artikel
                seen.add(name)
                unified.append(name)
        row["authors"] = unified or ["Unknown"]


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else IN_PATH
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT_PATH

    stats = {
        "record dibaca": 0,
        "buang: baris rusak": 0,
        "buang: headline kosong": 0,
        "buang: tanggal rusak": 0,
        "buang: tahun di luar rentang": 0,
        "buang: duplikat link": 0,
        "buang: duplikat headline+tanggal": 0,
    }
    rows = load_and_filter(in_path, stats)
    unify_author_names(rows)

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for i, row in enumerate(rows):
            f.write(json.dumps({"id": i, **row}, ensure_ascii=False) + "\n")

    print("=== Laporan cleaning ===")
    for k, v in stats.items():
        print(f"{k:<36}{v:>9,}")
    print(f"{'record bersih':<36}{len(rows):>9,}")
    print(f"{'deskripsi kosong (tetap disimpan)':<36}"
          f"{sum(1 for r in rows if not r['short_description']):>9,}")
    print(f"{'penulis Unknown':<36}"
          f"{sum(1 for r in rows if r['authors'] == ['Unknown']):>9,}")

    cats = Counter(r["category"] for r in rows)
    print(f"\n=== {len(cats)} kategori setelah penggabungan ===")
    for cat, n in sorted(cats.items()):
        print(f"{cat:<24}{n:>9,}")
    print(f"\nTersimpan: {out_path}")


if __name__ == "__main__":
    main()
