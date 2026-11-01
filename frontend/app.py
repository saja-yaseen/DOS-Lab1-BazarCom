
import os
import requests
from urllib.parse import quote
from flask import Flask, jsonify

app = Flask(__name__)

# Catalog service address
CATALOG_URL = os.getenv(
    "CATALOG_URL",
    "http://127.0.0.1:5101"
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
            f"[Frontend] GET {path} -> {response.status_code}: {data}",
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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
