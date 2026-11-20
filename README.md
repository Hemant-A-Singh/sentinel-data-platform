# Sentinel Data Platform

## Overview
Development sandbox for the Sentinel Analytics Data Engineering team. It hosts an ELT pipeline for the Sentinel platform: extract raw files, load them into PostgreSQL, transform them with SQL, and orchestrate everything with Apache Airflow running in Docker.

## Tech Stack
- **Orchestration:** Apache Airflow 3.3.2 (LocalExecutor, Task SDK)
- **Database:** PostgreSQL 16
- **Containerization:** Docker & Docker Compose
- **Language:** Python 3.12 (`psycopg2`, `python-dotenv`)
- **Transformation:** SQL (PostgreSQL dialect)

## Project Structure
```
sentinel-data-platform/
├── dags/
│   └── sentinel_daily.py        # Airflow DAG (sentinel_daily_task_method)
├── src/sentinel/                # Python package (on PYTHONPATH in the container)
│   ├── extract/
│   │   ├── raw_orders.py        # Working pipeline: create raw table, COPY CSV, transform
│   │   └── salesforce_extractor.py   # placeholder
│   ├── load/                    # placeholder
│   ├── transform/               # placeholder
│   ├── cli.py, config.py, db.py # placeholders (planned shared helpers)
├── sql/
│   ├── raw_orders.sql           # DROP/CREATE raw_orders (all TEXT columns)
│   ├── transform_orders.sql     # Clean + upsert into transformed_orders
│   ├── ddl/  transform/        # reserved for the planned SQL layout
├── data/
│   ├── raw/raw_orders.csv       # Sample source file (20 orders)
│   └── processed/
├── docs/                        # Architecture ERD, source map, data quirks
├── plugins/  scripts/  tests/   # currently empty
├── Dockerfile                   # apache/airflow:3.3.2 + requirements.txt
├── docker-compose.yml           # Postgres + Airflow services
├── requirements.txt
└── .env.example                 # Template for environment variables (currently empty)
```

## What Has Been Built

### 1. PostgreSQL (Docker)
- `postgres:16` container `sentinel-postgres`, data persisted in the `postgres_data` volume.
- Exposed on host port **5433** (container 5432) so it does not clash with a local Postgres.
- Healthcheck via `pg_isready`; Airflow services wait for it to be healthy.
- The same instance serves as both the Airflow metadata DB (`airflow` database) and the Sentinel data DB.

### 2. Airflow (Docker)
Custom image (`Dockerfile`) built on `apache/airflow:3.3.2`, installs `requirements.txt` and sets `PYTHONPATH=/opt/airflow/src` so DAGs can `import sentinel...`.

Services in `docker-compose.yml`:

| Service | Purpose |
|---|---|
| `airflow-init` | Runs `airflow db migrate` once, builds the image |
| `airflow-apiserver` | UI + API on http://localhost:8080 |
| `airflow-scheduler` | Schedules DAG runs |
| `airflow-dag-processor` | Parses DAG files (required in Airflow 3) |

Notable configuration: LocalExecutor, example DAGs disabled, Execution API URL pointing at the api-server, shared JWT secret from `.env`, and Simple Auth Manager (all users are admins). Local folders `dags`, `src`, `sql`, `data`, `logs` are mounted into `/opt/airflow/`.

### 3. Orders ELT pipeline
`src/sentinel/extract/raw_orders.py` (`main()`):
1. Connects to Postgres using env vars (manual transaction, `autocommit=False`).
2. Runs `sql/raw_orders.sql` — drops and recreates `raw_orders` (every column `TEXT`, so nothing is rejected on load).
3. Bulk-loads `data/raw/raw_orders.csv` with `COPY ... FROM STDIN`.
4. Runs `sql/transform_orders.sql`, which creates `transformed_orders` if needed and upserts into it:
   - trims whitespace, converts empty strings to `NULL`
   - casts `order_id`/`quantity` to `INT`, `unit_price` to `NUMERIC(10,2)`
   - normalizes four date formats (`YYYY/MM/DD`, `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`) to `DATE`
   - `ON CONFLICT (order_id) DO UPDATE` refreshes `delivery_status` and `updated_at`; `loaded_at` / `updated_at` audit columns
5. Commits on success, rolls back on any error, always closes the connection.

The sample CSV intentionally contains messy data (padded values, mixed date formats, inconsistent country names like `india` / `United States` / `USA`, missing names).

### 4. Airflow DAG
`dags/sentinel_daily.py` defines `sentinel_daily_task_method` using the TaskFlow API:
`print_task` → `extract_orders` (calls the pipeline above). An earlier `PythonOperator`-based `sentinel_daily` version (`@daily`, `catchup=False`) is kept commented out for reference. The DAG has been run manually and on schedule successfully (see `logs/`).

### 5. Documentation (`docs/`)
- `architecture-erd.md` — Mermaid ERD for the wider Nexora estate (accounts, orders, products, invoices, shipments, inventory, support, subscriptions).
- `source-map.md` — the 12 source systems, key tables, keys and refresh notes.
- `data-quirks.md` — five highest-priority data quirks and mitigation tests.

## Getting Started

### Prerequisites
Docker Desktop (with Compose v2).

### 1. Configure environment
Create a `.env` (git-ignored) with: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `AIRFLOW_UID`, `AIRFLOW_JWT_SECRET`. `.env.example` exists but is currently empty — fill it with these keys (no real secrets).

### 2. Start the stack
```bash
docker compose up -d --build
```
The first run builds the image and runs the DB migration before the other Airflow services start.

### 3. Open Airflow
http://localhost:8080 — log in with the Simple Auth Manager credentials (`admin` / `admin` in `docker-compose.yml`, for local use only). Unpause and trigger the DAG.

### 4. Inspect the results
```bash
docker exec -it sentinel-postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "SELECT * FROM transformed_orders;"
```
Or connect from the host at `localhost:5433`.

### Running the pipeline without Airflow
With a local venv and Postgres running on port 5433:
```bash
pip install -r requirements.txt
python -m sentinel.extract.raw_orders   # with PYTHONPATH=src
```

### Stopping
```bash
docker compose down        # keep data
docker compose down -v     # also delete the Postgres volume
```

## Roadmap
- Populate `requirements.txt` (it is empty; the pipeline needs `psycopg2-binary` and `python-dotenv`) and `.env.example`.
- Fill in the placeholder modules (`config.py`, `db.py`, `load/`, `transform/`, `cli.py`) and move shared DB logic out of `raw_orders.py`.
- Implement the Salesforce extractor.
- Move SQL into `sql/ddl` and `sql/transform`; make loads incremental instead of drop-and-recreate.
- Standardize country names and status values; add data-quality checks.
- Add tests in `tests/`.
- Re-enable a `@daily` schedule on the DAG and pass `run_date` through.
- Clean up repo hygiene: stop tracking `logs/` and `__pycache__`, remove the duplicate `README2.md`.
