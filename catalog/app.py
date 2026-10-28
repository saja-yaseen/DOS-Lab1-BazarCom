
from flask import Flask, jsonify, request
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)

DB = Path(os.getenv(
    "DB_PATH",
    str(Path(__file__).with_name("catalog.db"))
))


def init_db():
    conn = sqlite3.connect(DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT,
            topic TEXT,
            price REAL,
            quantity INTEGER
        )
    """)

    books = [
        (1, "How to get a good grade in DOS in 40 minutes a day",
         "distributed systems", 40, 10),
        (2, "RPCs for Noobs",
         "distributed systems", 50, 5),
        (3, "Xen and the Art of Surviving Undergraduate School",
         "undergraduate school", 30, 8),
        (4, "Cooking for the Impatient Undergrad",
         "undergraduate school", 20, 12)
    ]

    conn.executemany(
        "INSERT OR IGNORE INTO books VALUES (?, ?, ?, ?, ?)",
        books
    )

    conn.commit()
    conn.close()


@app.get("/search/<path:topic>")
def search(topic):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT id, title FROM books WHERE topic = ? COLLATE NOCASE",
        (topic,)
    ).fetchall()

    result = [dict(row) for row in rows]
    conn.close()
    return jsonify(result)


@app.get("/info/<int:item_id>")
def info(item_id):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        "SELECT title, quantity, price FROM books WHERE id = ?",
        (item_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return jsonify({"error": "Book not found"}), 404

    return jsonify(dict(row))

@app.patch("/update/<int:item_id>")
def update(item_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    if "price" not in data and "quantity_change" not in data:
        return jsonify({"error": "No updates provided"}), 400

    price = data.get("price")
    change = data.get("quantity_change", 0)

    if not isinstance(change, int) or isinstance(change, bool):
        return jsonify({"error": "Invalid quantity change"}), 400

    if "price" in data and (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or price < 0
    ):
        return jsonify({"error": "Invalid price"}), 400

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("BEGIN IMMEDIATE")

        book = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (item_id,)
        ).fetchone()

        if book is None:
            conn.rollback()
            return jsonify({"error": "Book not found"}), 404

        new_quantity = book["quantity"] + change

        if new_quantity < 0:
            conn.rollback()
            return jsonify({"error": "Not enough stock"}), 409

        new_price = price if "price" in data else book["price"]

        conn.execute(
            "UPDATE books SET price = ?, quantity = ? WHERE id = ?",
            (new_price, new_quantity, item_id)
        )

        conn.commit()

        return jsonify({
            "message": "Book updated successfully",
            "id": item_id,
            "price": new_price,
            "quantity": new_quantity
        })

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, threaded=True)
