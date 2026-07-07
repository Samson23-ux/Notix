# Notix

---

## Description

Notix is an event driven notification delivery service built with FastAPI, Celery, and RabbitMQ. It is designed to help applications send reliable email and webhook notifications with authentication, API key management, idempotency, retries, queue-based processing, and delivery tracking.

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2C3E50?style=for-the-badge&logo=pydantic&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Sentry](https://img.shields.io/badge/Sentry-362D59?style=for-the-badge&logo=sentry&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Resend](https://img.shields.io/badge/Resend-FF5A5F?style=for-the-badge&logo=resend&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## Core Features

### Authentication and account management
- Email/password sign-up and login
- Email verification via OTP
- Google and GitHub OAuth login
- JWT-based access token flow with refresh tokens
- Account deletion and logout support
- Rate limiting on sensitive auth endpoints

### Notification delivery
- Create email notifications for registered users
- Create webhook notifications for configured endpoints
- Notification idempotency using unique idempotency keys
- Priority-based queue routing for high, medium, and critical traffic
- Delivery status tracking through the database
- Automatic retries for transient failures and dead-letter handling for non-transient failures

### Webhooks
- Register webhook endpoints per user
- Store webhook secrets securely
- Deliver signed webhook payloads with custom headers
- Track webhook notifications with the same persistence model as email

### Infrastructure and reliability
- Async SQLAlchemy with PostgreSQL
- Redis-backed state and idempotency checks
- RabbitMQ + Celery for asynchronous processing
- Docker Compose-based local development environment
- Sentry integration for observability and error tracking

---

## Architecture Overview

Notix follows a layered architecture:

- API layer: FastAPI routers and request handlers
- Service layer: business logic for auth, notifications, webhooks, and API keys
- Repository layer: persistence abstractions for PostgreSQL models
- Worker layer: Celery tasks that process email and webhook delivery asynchronously
- Infrastructure layer: PostgreSQL, Redis, RabbitMQ, and Resend

---

### Concepts Covered
- Idempotency: Prevents duplicate processing by ensuring the same notification can be safely handled more than once.
- At-least-once delivery: Retries transient failures so notifications are not lost even if a delivery attempt fails temporarily.
- Dead-lettering: Failed messages are moved to a dead-letter queue for inspection and recovery instead of being silently dropped.
- Backpressure: Queue depth is checked before accepting new notifications to avoid overwhelming the system and causing backlog buildup.
- Priority queues: Notifications are routed through priority-aware queues so critical messages are processed faster.
- Queue durability: Durable queues and messages help preserve delivery work across restarts, crashes, or temporary outages.

---

### Request flow
1. A client calls one of the API routes.
2. The FastAPI service validates the request and creates or updates a domain entity.
3. For notification requests, the service writes the notification record and publishes work to the broker.
4. Celery workers consume tasks from RabbitMQ and execute delivery logic.
5. Delivery status is updated in PostgreSQL and tracked by the API.

---

## Project Structure

```text
app/
  api/
    models/        # SQLAlchemy models
    repo/          # repositories layer
    routers/       # FastAPI endpoints
    schemas/       # request/response schemas
    services/      # core service logic
  core/            # settings, security, exception handling
  database/        # session and DB utilities
  worker/          # Celery app, tasks, and queue config
  deps.py          # Dependencies
  limiter.py       # Rate limiting
  main.py          # FastAPI entrypoint
alembic/           # database migrations
Dockerfile
docker-compose.yml
test/             # pytest test suite
```

---

## Prerequisites

Before running Notix locally, make sure you have:
- Python 3.12 or newer
- Docker and Docker Compose
- uv (recommended for dependency management)
- access to a PostgreSQL instance, Redis, RabbitMQ, and Resend credentials

---

## Environment Configuration

```bash
cp .env.example .env
```

---

## Running With Docker Compose

The repository includes a full local stack for the API, workers, PostgreSQL, Redis, and RabbitMQ.

### Start all services

```bash
docker compose up --build
```

This will launch:
- PostgreSQL for app data
- PostgreSQL for test data
- Redis
- RabbitMQ management UI at http://localhost:15672
- API server at http://localhost:8000
- Celery worker pools for high, standard, webhook, and batch processing
- Celery beat scheduler

### Stop services

```bash
docker compose down
```

---

## Running Locally Without Docker

### 1. Install dependencies

```bash
uv sync
```

### 2. Apply database migrations

```bash
uv run alembic upgrade head
```

### 3. Start the API

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the workers

```bash
uv run celery -A app.worker.celery_app worker -Q notix.high -P gevent -l info
```

```bash
uv run celery -A app.worker.celery_app worker -Q notix.standard,notix.webhook -P gevent -l info
```

```bash
uv run celery -A app.worker.celery_app worker -Q notix.batch -P gevent -l info
```

```bash
uv run celery -A app.worker.celery_app beat -l info
```

### 5. Test API endpoints via docs
Open your browser and navigate to [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Testing

Run the test suite with:

```bash
uv run pytest
```

Run in verbose mode:

```bash
uv run pytest -v
```

The repository includes tests covering authentication, notifications, webhooks, and worker flows depending on the environment setup.

---

## Development Notes

- Database migrations are managed with Alembic.
- Notification processing is intentionally asynchronous to keep the API responsive.
- The service uses idempotency keys to prevent duplicate processing for repeated requests.
- Worker failures are routed through retry and dead-letter logic for resilience.

---
