
import os
import sqlite3
from pathlib import Path

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_PATH = Path(os.getenv(
    "DB_PATH",
    str(Path(__file__).with_name("orders.db"))
))

CATALOG_URL = os.getenv(
    "CATALOG_URL",
    "http://127.0.0.1:5101"
).rstrip("/")


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


@app.get("/health")
def health():
    return jsonify({
        "service": "order",
        "status": "running"
    })


@app.post("/purchase/<int:item_id>")
def purchase(item_id):
    data = request.get_json(silent=True)

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    quantity = data.get("quantity", 1)

    if type(quantity) is not int or quantity <= 0:
        return jsonify({"error": "Invalid quantity"}), 400

    # Ask Catalog to decrease the stock
    try:
        response = requests.patch(
            f"{CATALOG_URL}/update/{item_id}",
            json={"quantity_change": -quantity},
            timeout=5
        )
    except requests.RequestException:
        return jsonify({
            "error": "Catalog service unavailable"
        }), 503

    if response.status_code in (404, 409):
        return jsonify(response.json()), response.status_code

    if response.status_code != 200:
        return jsonify({
            "error": "Catalog update failed"
        }), 502

    try:
        book = response.json()
        price = book["price"]

        # Save successful purchase
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.execute(
                """INSERT INTO orders
                   (book_id, quantity, price)
                   VALUES (?, ?, ?)""",
                (item_id, quantity, price)
            )
            order_id = cursor.lastrowid

    except (sqlite3.Error, KeyError, ValueError, TypeError):
        # Try restoring stock if saving the order fails
        try:
            requests.patch(
                f"{CATALOG_URL}/update/{item_id}",
                json={"quantity_change": quantity},
                timeout=5
            )
        except requests.RequestException:
            pass

        return jsonify({
            "error": "Order could not be saved"
        }), 500

    print(
        f"[Order] Purchased book {item_id}, "
        f"quantity={quantity}, order_id={order_id}",
        flush=True
    )

    return jsonify({
        "message": "Book purchased successfully",
        "order_id": order_id,
        "book_id": item_id,
        "quantity": quantity,
        "total_price": price * quantity
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(
        host="0.0.0.0",
        port=5003,
        threaded=True
    )
