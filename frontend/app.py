
import os
import requests
from urllib.parse import quote
from flask import Flask, jsonify, request

app = Flask(__name__)

# Service addresses
CATALOG_URL = os.getenv(
    "CATALOG_URL",
    "http://127.0.0.1:5101"
).rstrip("/")

ORDER_URL = os.getenv(
    "ORDER_URL",
    "http://127.0.0.1:5103"
).rstrip("/")


# Send a GET request to Catalog
def catalog_request(path):
    try:
        response = requests.get(
            f"{CATALOG_URL}{path}",
            timeout=5
        )

        data = response.json()

        print(
            f"[Frontend] GET {path} -> "
            f"{response.status_code}: {data}",
            flush=True
        )

        return jsonify(data), response.status_code

    except requests.RequestException:
        return jsonify({
            "error": "Catalog service unavailable"
        }), 503

    except ValueError:
        return jsonify({
            "error": "Invalid Catalog response"
        }), 502


# Search books by topic
@app.get("/search/<path:topic>")
def search(topic):
    encoded_topic = quote(topic, safe="")
    return catalog_request(f"/search/{encoded_topic}")


# Get information about a book
@app.get("/info/<int:item_id>")
def info(item_id):
    return catalog_request(f"/info/{item_id}")


# Purchase a book through Order Service
@app.post("/purchase/<int:item_id>")
def purchase(item_id):
    data = request.get_json(silent=True)

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid JSON"
        }), 400

    try:
        response = requests.post(
            f"{ORDER_URL}/purchase/{item_id}",
            json=data,
            timeout=10
        )

        result = response.json()

        print(
            f"[Frontend] POST /purchase/{item_id} "
            f"-> {response.status_code}: {result}",
            flush=True
        )

        return jsonify(result), response.status_code

    except requests.RequestException:
        return jsonify({
            "error": "Order service unavailable"
        }), 503

    except ValueError:
        return jsonify({
            "error": "Invalid Order response"
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
