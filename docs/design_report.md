# Bazar.com – Lab 1 Design Report

**Course:** Distributed and Operating Systems – Fall 2026  
**Project:** Bazar.com: A Multi-tier Online Book Store

## 1. System Architecture

Bazar.com is a multi-tier online bookstore implemented using three independent Python Flask microservices: Frontend, Catalog, and Order. Each service runs in its own Docker container and communicates with the other services using HTTP REST APIs with JSON responses.

The Frontend Service is the entry point for client requests. It forwards search and book information requests to the Catalog Service and purchase requests to the Order Service. The Catalog Service manages information about four books, including their titles, topics, prices, and available stock. The Order Service handles purchases and maintains a persistent record of successful orders.

The system is managed using Docker Compose. The services communicate through Docker's internal network using their service names.

## 2. How the System Works

### Search Operation

A client sends a GET request to `/search/<topic>` through the Frontend Service. The Frontend forwards the request to the Catalog Service, which queries its SQLite database and returns matching book titles and item numbers.

### Info Operation

A client sends a GET request to `/info/<item_id>`. The Frontend retrieves the corresponding book information from Catalog, including its title, price, and quantity in stock.

### Purchase Operation

A client sends a POST request to `/purchase/<item_id>` through Frontend. The request is forwarded to the Order Service.

The Order Service first queries Catalog to obtain the book information and check the available quantity. If insufficient stock is available, the operation returns HTTP 409. Otherwise, Order requests a stock decrease through Catalog's update endpoint.

Catalog uses an SQLite transaction with `BEGIN IMMEDIATE` to prevent concurrent updates from making the inventory negative. After a successful stock update, Order saves the purchase in its own SQLite database and returns the order details to the client.

For each successful purchase, Order also prints a message in the required format, such as:

`bought book RPCs for Noobs`

## 3. Design Decisions and Trade-offs

**Flask and REST:** Flask was chosen because it is lightweight and supports HTTP endpoints with minimal code. REST and JSON provide simple communication between independent services.

**SQLite:** Separate SQLite databases are used for Catalog and Order. SQLite provides disk persistence without the complexity of a heavyweight database server.

**Docker Compose:** Docker Compose simplifies starting and managing the three services. Environment variables are used to configure internal service addresses and database paths.

**Concurrency:** Flask accepts concurrent requests, while Catalog uses an immediate SQLite transaction to serialize inventory updates and prevent negative stock.

**Trade-off:** The system prioritizes simplicity and clear separation between services over advanced fault tolerance and scalability.

## 4. Testing and Results

The system was tested by issuing HTTP requests from Windows PowerShell and a web browser to the Docker-based services.

Tests included successful searches, information requests, successful purchases, insufficient-stock errors, and persistent database storage.

Successful purchases decreased Catalog inventory and created records in the Order database. Requests exceeding available stock returned HTTP 409 without reducing inventory. All three services were confirmed running in separate Docker containers.

Catalog inventory and saved orders remained available after restarting the containers. The Order Service also successfully printed the required `bought book <book_name>` log message.

Screenshots and detailed results are provided in the `docs` directory.

## 5. Limitations and Possible Improvements

The system currently uses SQLite databases hosted in separate services. Although Catalog's stock update is atomic, the inventory update and Order database insertion are not part of one distributed transaction.

If a failure occurs after inventory is decreased but before the order is saved, Order attempts to restore the stock. However, this compensation is best-effort and does not guarantee full recovery from crashes or network failures.

A possible improvement would be to introduce unique purchase request IDs, durable transaction states, and an idempotent retry or compensation mechanism to improve fault tolerance.

Other possible extensions include authentication, customer accounts, a web-based user interface, automated concurrency tests, monitoring, and more extensive error logging.

## 6. How to Run the System

The project requires Docker and Docker Compose.

From the project root directory, run:

```bash
docker compose up -d --build
```

The services are accessible from the host at:

- Frontend: `http://127.0.0.1:5100`
- Catalog: `http://127.0.0.1:5101`
- Order: `http://127.0.0.1:5103`

Example requests:

**Search for books:**

```text
GET http://127.0.0.1:5100/search/distributed%20systems
```

**Retrieve book information:**

```text
GET http://127.0.0.1:5100/info/2
```

**Purchase a book:**

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5100/purchase/2" -Method POST -ContentType "application/json" -Body '{"quantity":1}'
```

To inspect service logs:

```bash
docker compose logs
```

To stop the services without deleting database volumes:

```bash
docker compose down
```

The databases are stored in persistent Docker volumes. Running `docker compose down -v` deletes these volumes and should be avoided when preserving test data.

## 7. Conclusion

Bazar.com demonstrates a multi-tier client-server architecture using three communicating REST microservices. The system supports searching for books, retrieving book information, processing purchases, updating stock, and storing order history.

The implementation fulfills the core lab functionality while providing a foundation for future improvements in fault tolerance, scalability, and distributed transaction handling.
