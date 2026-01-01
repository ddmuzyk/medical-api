# Medical System API

Backend API for medical appointment system with PostgreSQL and Redis.

## Prerequisites

- Docker Desktop installed and running
- Git

## Setup

1. **Clone the repository**
  For example:
   ```bash
   git clone https://github.com/ddmuzyk/medical-api.git
   cd modelowanie
   ```

2. **Create environment file**
   
   Copy `.env.example` to `.env` (or create `.env` with these variables):
   ```
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=medical
   POSTGRES_HOST=postgres

   DB_USERNAME=postgres
   DB_PASSWORD=your_password
   DB_NAME=medical
   DB_HOST=postgres

   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_DB=0
   ```

3. **Start the services**
   ```bash
   docker-compose up --build
   ```

   First time will take a few moments to download images and build.

4. **Verify it's running**
   - Flask API: http://localhost:5000
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

## Usage

**Start services:**
```bash
docker-compose up
```

**Start in background:**
```bash
docker-compose up -d
```

**Stop services:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f server
```

**Rebuild after dependency changes:**
```bash
docker-compose up --build
```

**Reset database (deletes all data):**
```bash
docker-compose down -v
docker-compose up
```

## Database

Database schema is automatically initialized from:
- `create_tables.sql` - Table definitions
- `relations.sql` - Foreign key constraints

## Development

Code changes in `./server` are automatically reflected (hot reload enabled).

To add Python dependencies:
1. Add to `server/requirements.txt`
2. Rebuild: `docker-compose up --build`