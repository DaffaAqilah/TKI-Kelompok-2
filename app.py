from pathlib import Path
import pickle

from flask import Flask, jsonify, render_template, request

from boolean import search
from index import build_index
from preprocess import load_docs

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "clean.jsonl"
INDEX_PATH = BASE_DIR / "index.pkl"
PER_PAGE = 5

DOCS = load_docs(DATA_PATH)
ALL_IDS = {doc["id"] for doc in DOCS}
DOCS_BY_ID = {doc["id"]: doc for doc in DOCS}


def load_or_build_index():
    dataset_time = DATA_PATH.stat().st_mtime_ns
    if INDEX_PATH.exists():
        try:
            with INDEX_PATH.open("rb") as file:
                saved = pickle.load(file)
            if saved.get("dataset_time") == dataset_time and saved.get("dataset_path") == str(DATA_PATH.resolve()):
                return saved["index"]
        except (OSError, EOFError, pickle.PickleError, AttributeError, TypeError):
            pass
    built = build_index(DOCS)
    with INDEX_PATH.open("wb") as file:
        pickle.dump({"dataset_time": dataset_time, "dataset_path": str(DATA_PATH.resolve()), "index": built}, file, protocol=pickle.HIGHEST_PROTOCOL)
    return built


INDEX = load_or_build_index()


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/search")
def search_endpoint():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip().casefold()
    author = request.args.get("author", "").strip().casefold()
    year_from = request.args.get("year_from", type=int)
    year_to = request.args.get("year_to", type=int)
    page = max(request.args.get("page", default=1, type=int), 1)

    try:
        matching_ids = search(query, INDEX, ALL_IDS)
    except ValueError as error:
        return jsonify({"error": str(error), "query": query}), 400

    results = [DOCS_BY_ID[doc_id] for doc_id in matching_ids if doc_id in DOCS_BY_ID]
    if category:
        results = [doc for doc in results if str(doc.get("category", "")).casefold() == category]
    if author:
        results = [doc for doc in results if author in str(doc.get("authors", "")).casefold()]
    if year_from is not None:
        results = [doc for doc in results if str(doc.get("date", ""))[:4].isdigit() and int(str(doc["date"])[:4]) >= year_from]
    if year_to is not None:
        results = [doc for doc in results if str(doc.get("date", ""))[:4].isdigit() and int(str(doc["date"])[:4]) <= year_to]

    results.sort(key=lambda doc: doc["id"])
    total = len(results)
    start = (page - 1) * PER_PAGE
    return jsonify({
        "query": query,
        "page": page,
        "per_page": PER_PAGE,
        "total_results": total,
        "total_pages": (total + PER_PAGE - 1) // PER_PAGE,
        "results": results[start:start + PER_PAGE],
    })


if __name__ == "__main__":
    app.run(debug=True)

