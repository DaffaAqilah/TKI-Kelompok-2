import json
import re

STOPWORDS = {
    "a", "an", "the", "and", "or", "but",
    "is", "are", "was", "were", "be", "been",
    "to", "of", "in", "on", "at", "for",
    "from", "by", "with", "as", "it", "this",
    "that", "these", "those", "he", "she",
    "they", "we", "you", "i", "has", "have",
    "had", "do", "does", "did", "will",
    "would", "can", "could", "about", "after",
    "before", "into", "than", "then"
}


def load_docs(path):
    docs = []

    with open(path, "r", encoding="utf-8") as file:
        content = file.read().strip()

    if not content:
        return docs

    # Membaca JSON biasa atau JSON Lines
    try:
        data = json.loads(content)
        records = data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        records = []
        for line in content.splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    for row_id, data in enumerate(records):
        headline = str(data.get("headline") or "").strip()
        description = str(
            data.get("short_description") or ""
        ).strip()

        if not headline and not description:
            continue

        data["id"] = row_id
        data["text"] = (headline + " " + description).strip()

        docs.append(data)

    return docs


def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]|_", " ", text)

    tokens = text.split()

    return [
        word for word in tokens
        if word not in STOPWORDS
    ]
