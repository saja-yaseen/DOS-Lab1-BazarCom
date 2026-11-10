# Bazar.com – Lab 1 Design Report

**Course:** Distributed and Operating Systems – Fall 2026  
**Project:** A Multi-tier Online Book Store

## 1. Architecture and Design

Bazar.com is a distributed bookstore built using three lightweight Python Flask microservices: **Frontend, Catalog, and Order**. Each runs in a separate Docker container and communicates using HTTP REST requests and JSON responses.

The Frontend receives client requests and forwards Search and Info operations to Catalog and Purchase operations to Order. Catalog stores four books, their topics, prices, and stock quantities in SQLite. Order processes purchases and records successful orders in a separate SQLite database.

Docker Compose manages the services, networking, and persistent database volumes. Service addresses and database paths are configured using environment variables.

## 2. How the System Works

**Search:** A client sends `GET /search/<topic>` to Frontend. Catalog queries its database and returns matching book IDs and titles.

**Info:** A client sends `GET /info/<item_id>`. Catalog returns the book title, price, and available quantity.

**Purchase:** A client sends `POST /purchase/<item_id>` to Frontend, which forwards it to Order. Order queries Catalog to verify the book and check stock availability. If stock is insufficient, HTTP 409 is returned. Otherwise, Order requests an atomic inventory decrement from Catalog and records the purchase in SQLite.

Catalog uses SQLite's `BEGIN IMMEDIATE` transaction to protect stock updates from concurrent requests. Successful purchases generate a log message such as `bought book RPCs for Noobs`.

## 3. Design Decisions and Trade-offs

Flask provides lightweight REST services with concurrent request handling. SQLite provides persistence without requiring a separate database server. Docker Compose simplifies deployment, while independent containers make service responsibilities clear.

The main trade-off is between implementation simplicity and distributed fault tolerance. Inventory updates are atomic inside Catalog, but stock changes and order recording occur in different databases and cannot be committed as one transaction.

## 4. Testing and Results

The implementation was tested using a host-side PowerShell client and web browser. Search and Info returned the expected book data. Purchases created order records and reduced stock. Purchases exceeding available inventory returned HTTP 409 without decreasing stock.

All three services ran successfully in Docker containers. SQLite orders and catalog inventory remained available after container restarts. The required `bought book <book_name>` message was also verified in Order logs.

Test output and screenshots are stored in `docs/`, including `catalog_test_results.md` and `order_test_results.md`.

## 5. Limitations and Improvements

The system does not provide a fully atomic distributed purchase transaction. If the order database fails after Catalog reduces stock, Order attempts a compensating stock increase, but crashes, timeouts, and uncertain network outcomes may still cause inconsistencies.

Future improvements include idempotent purchase IDs, durable transaction tracking, safer retries, automated concurrency tests, authentication, monitoring, and a production HTTP server.

## 6. How to Run

Docker and Docker Compose are required. From the repository root, run:

`docker compose up -d --build`

The host ports are **5100 (Frontend)**, **5101 (Catalog)**, and **5103 (Order)**.

Example operations:

- Search: `GET http://127.0.0.1:5100/search/distributed%20systems`
- Info: `GET http://127.0.0.1:5100/info/2`
- Purchase: `POST http://127.0.0.1:5100/purchase/2` with JSON body `{"quantity":1}`

Use `docker compose ps` to view running services and `docker compose logs` to inspect output. Stop services with `docker compose down`. Database volumes persist unless explicitly deleted with `docker compose down -v`.

## 7. Conclusion

Bazar.com demonstrates a working three-service REST architecture with book queries, purchases, inventory updates, concurrent request handling, and persistent storage. The design meets the lab's core requirements while identifying distributed transaction reliability as an important area for improvement.