# Catalog Service - Test Results

## 1. Overview

This document summarizes the tests performed on the Catalog Service of the Bazar.com project.

The service was tested locally using Flask and inside Docker containers.

## 2. REST API Testing

### Test 1: Info API

**Request:** `GET /info/2`

**Result:**
```json
{
  "price": 50.0,
  "quantity": 5,
  "title": "RPCs for Noobs"
}
```

**Status:** Passed

### Test 2: Search API

**Request:** `GET /search/distributed%20systems`

**Result:** The server returned two books:

1. How to get a good grade in DOS in 40 minutes a day.
2. RPCs for Noobs.

**Status:** Passed

### Test 3: Update API

**Request:** `PATCH /update/2`

**Request Body:**
```json
{"quantity_change": 2}
```

**Result:** The stock quantity increased from 5 to 7.

**Status:** Passed

## 3. SQLite Persistence Test

The Catalog Service was stopped and restarted after updating the stock.

The quantity remained 7 after restarting the server.

**Status:** Passed

## 4. Docker Testing

The Docker image was built successfully, and the Catalog Service was started in a Linux container.

The Info API was tested on port 5002 and returned the expected book information.

**Status:** Passed

## 5. Docker Compose Testing

The Catalog Service was deployed using Docker Compose on port 5101.

The following operations were tested:

- Started the Catalog container.
- Retrieved book information through the REST API.
- Updated the stock quantity to 9.
- Removed and recreated the container without deleting the Docker volume.
- Verified that the quantity remained 9.

**Status:** Passed

## 6. Conclusion

The Catalog Service successfully passed the performed functional and persistence tests.

The Order Service, Frontend Service, and complete three-service integration still require development and testing.