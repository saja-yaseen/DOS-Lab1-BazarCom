
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

    # Step 1: Query Catalog before attempting purchase
    try:
        info_response = requests.get(
            f"{CATALOG_URL}/info/{item_id}",
            timeout=5
        )
    except requests.RequestException:
        return jsonify({
            "error": "Catalog service unavailable"
        }), 503

    if info_response.status_code == 404:
        return jsonify({"error": "Book not found"}), 404

    if info_response.status_code != 200:
        return jsonify({
            "error": "Catalog query failed"
        }), 502

    try:
        book_info = info_response.json()
        book_title = book_info["title"]
        available_stock = book_info["quantity"]

        if (
            not isinstance(book_title, str)
            or type(available_stock) is not int
        ):
            raise ValueError("Invalid book information")

    except (ValueError, KeyError, TypeError):
        return jsonify({
            "error": "Invalid Catalog response"
        }), 502

    if available_stock < quantity:
        return jsonify({
            "error": "Not enough stock"
        }), 409

    # Step 2: Atomically decrease stock in Catalog
    # Catalog checks availability again to prevent overselling
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
        try:
            return jsonify(response.json()), response.status_code
        except ValueError:
            return jsonify({
                "error": "Invalid Catalog response"
            }), 502

    if response.status_code != 200:
        return jsonify({
            "error": "Catalog update failed"
        }), 502

    # Step 3: Save the order in SQLite
    try:
        updated_book = response.json()
        price = updated_book["price"]

        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
        ):
            raise ValueError("Invalid price")

        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.execute(
                """
                INSERT INTO orders (book_id, quantity, price)
                VALUES (?, ?, ?)
                """,
                (item_id, quantity, price)
            )
            order_id = cursor.lastrowid

    except (sqlite3.Error, ValueError, KeyError, TypeError):
        # Best-effort compensation if the order cannot be saved
        try:
            requests.patch(
                f"{CATALOG_URL}/update/{item_id}",
                json={"quantity_change": quantity},
                timeout=5
            )
        except requests.RequestException:
            app.logger.exception(
                "Failed to restore stock for book %s",
                item_id
            )

        return jsonify({
            "error": "Order could not be saved"
        }), 500

    # Required output for the DOS lab
    print(
        f"bought book {book_title}",
        flush=True
    )

    print(
        f"[Order] order_id={order_id}, "
        f"book_id={item_id}, quantity={quantity}",
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
