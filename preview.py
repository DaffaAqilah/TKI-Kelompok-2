# Preview frontend saja (tanpa boolean.py / index.py / preprocess.py).
# Jalankan: python preview.py  -> buka http://127.0.0.1:5000
from flask import Flask, render_template

app = Flask(__name__)


@app.get("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
