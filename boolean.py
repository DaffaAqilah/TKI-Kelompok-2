"""Boolean retrieval untuk proyek STKI Kelompok 2 (tugas 3: Daffa).

Kontrak (disepakati kelompok):
    search(query, index, all_ids) -> set[int]
    index   : dict[str, set[int]]  hasil build_index di index.py
    all_ids : set[int]             semua id dokumen (dibutuhkan NOT)

Sintaks query yang disepakati (20 Nov 2026):
    - Operator AND, OR, NOT boleh huruf besar atau kecil.
    - Tanda kurung didukung untuk mengelompokkan.
    - Frasa dalam tanda kutip TIDAK didukung: kata-kata di dalamnya
      diperlakukan sebagai kata terpisah yang digabung AND.
    - Kata tanpa operator dianggap AND, contoh: "climate change"
      sama dengan "climate AND change".
    - Prioritas operator: NOT > AND > OR.
    - Kata yang tidak ada di index menghasilkan himpunan kosong.
    - Query kosong (atau hanya berisi stopword) menghasilkan
      himpunan kosong.
    - Query tidak sah melempar ValueError: kurung tidak berpasangan,
      dua operator berturutan ("a AND OR b"), operator di awal/akhir
      query, atau kelompok kurung kosong "()".
      app.py menangkap ValueError ini dan mengubahnya menjadi
      respons HTTP 400.

Kata pada query diproses dengan tokenize yang sama dengan dokumen
(preprocess.tokenize), supaya cara memecah kata selalu konsisten.
Operator dikenali SEBELUM tokenize, karena "and"/"or" termasuk
stopword di preprocess dan akan hilang kalau query langsung
di-tokenize, sedangkan "not" bukan stopword dan akan ikut tercari
sebagai kata biasa.
"""

from preprocess import tokenize

_OPERATORS = {"AND", "OR", "NOT"}

# Token hasil lexer:
#   ("TERM", (kata, ...))  satu potongan kata dari query; bisa menjadi
#                          lebih dari satu kata setelah tokenize,
#                          contoh "covid-19" -> ("covid", "19"),
#                          dan kata-kata itu digabung dengan AND.
#   ("AND",) ("OR",) ("NOT",) ("LPAREN",) ("RPAREN",)


def _lex(query):
    """Pecah query mentah menjadi token operator/kurung/kata."""
    raw_parts = query.replace("(", " ( ").replace(")", " ) ").split()
    tokens = []
    for part in raw_parts:
        if part == "(":
            tokens.append(("LPAREN",))
        elif part == ")":
            tokens.append(("RPAREN",))
        elif part.upper() in _OPERATORS:
            tokens.append((part.upper(),))
        else:
            words = tuple(tokenize(part))
            if words:
                tokens.append(("TERM", words))
            # Potongan yang isinya hanya stopword/tanda baca dibuang,
            # sama seperti stopword dibuang dari dokumen.
    return tokens


class _Parser:
    """Recursive-descent parser yang langsung mengevaluasi himpunan.

    Tata bahasa (prioritas NOT > AND > OR):
        or_expr   : and_expr (OR and_expr)*
        and_expr  : not_expr ((AND | <tanpa operator>) not_expr)*
        not_expr  : NOT not_expr | primary
        primary   : TERM | '(' or_expr ')'
    """

    def __init__(self, tokens, index, all_ids):
        self.tokens = tokens
        self.pos = 0
        self.index = index
        self.all_ids = all_ids

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos][0]
        return None

    def _next(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse(self):
        result = self._parse_or()
        leftover = self._peek()
        if leftover is not None:
            if leftover == "RPAREN":
                raise ValueError("Kurung tutup ')' tanpa kurung buka '(' yang cocok.")
            raise ValueError("Query tidak sah di dekat akhir query.")
        return result

    def _parse_or(self):
        result = self._parse_and()
        while self._peek() == "OR":
            self._next()
            result = result | self._parse_and()
        return result

    def _parse_and(self):
        result = self._parse_not()
        while True:
            kind = self._peek()
            if kind == "AND":
                self._next()
                result = result & self._parse_not()
            elif kind in ("TERM", "NOT", "LPAREN"):
                # Kata/kelompok yang bersebelahan tanpa operator = AND.
                result = result & self._parse_not()
            else:
                return result

    def _parse_not(self):
        if self._peek() == "NOT":
            self._next()
            if self._peek() in (None, "AND", "OR", "RPAREN"):
                raise ValueError("Operator NOT harus diikuti kata atau kelompok kurung.")
            return self.all_ids - self._parse_not()
        return self._parse_primary()

    def _parse_primary(self):
        kind = self._peek()
        if kind is None:
            raise ValueError("Query tidak lengkap: ada operator tanpa kata sesudahnya.")
        if kind == "TERM":
            _, words = self._next()
            result = None
            for word in words:
                posting = self.index.get(word, set())
                result = set(posting) if result is None else result & posting
            return result if result is not None else set()
        if kind == "LPAREN":
            self._next()
            if self._peek() == "RPAREN":
                raise ValueError("Kelompok kurung kosong '()' tidak diperbolehkan.")
            result = self._parse_or()
            if self._peek() != "RPAREN":
                raise ValueError("Kurung buka '(' tanpa kurung tutup ')' yang cocok.")
            self._next()
            return result
        if kind == "RPAREN":
            raise ValueError("Kurung tutup ')' tanpa kurung buka '(' yang cocok.")
        # AND/OR muncul di posisi yang seharusnya berisi kata.
        raise ValueError(
            f"Operator {kind} tidak boleh di sini: operator harus di antara dua kata/kelompok."
        )


def search(query, index, all_ids):
    """Jalankan query Boolean dan kembalikan set id dokumen yang cocok."""
    if not query or not query.strip():
        return set()
    tokens = _lex(query)
    if not tokens:
        # Query hanya berisi stopword/tanda baca.
        return set()
    return _Parser(tokens, index, set(all_ids)).parse()
