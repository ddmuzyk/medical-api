# Medical System API

Backend API for medical appointment system with PostgreSQL and Redis.

## Prerequisites

- Docker Desktop installed and running
- Git

## Setup

1. **Clone the repository**
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

## Creating an Admin User

After starting the services, create an admin user using the CLI script:

```bash
docker exec -it flask_server python create_admin.py <email> <password> <first_name> <last_name>
```

**Example:**
```bash
docker exec -it flask_server python create_admin.py admin@hospital.com Admin123! Jane Smith
```

**Note:** Only admins can create doctor accounts and other admins through the API. Regular users can self-register.

## Seeding Database

### 1. Seed Doctors and Users

First, create basic doctors (required for availability):

```bash
docker compose exec server python scripts/seed_doctors_and_users.py
```

This creates 3 doctors:
- Jan Kowalski (cardiology) - jan.kowalski@hospital.com
- Anna Nowak (dermatology) - anna.nowak@hospital.com  
- Piotr Zieliński (pediatrics) - piotr.zielinski@hospital.com

Password for all: `Doctor123!`

### 2. Seed Doctor Availability

Then generate availability slots (Mon-Fri, 09:00-17:00, 4 weeks ahead):

```bash
docker compose exec server python scripts/seed_weekday_availability.py
```

This will:
- Create 1-hour slots from 09:00 to 16:00 for each weekday
- Skip weekends automatically
- Generate slots for 4 weeks from today
- Skip duplicates if slots already exist
- Set `is_available = TRUE` for all slots

### 3. Seed Additional Test Data (Optional)

For more test data (patients, appointments):

```bash
docker exec -it flask_server python seed_database.py
```

**Note:** Run seeds in order: doctors → availability → test data.

## Testing Endpoints

### Test Availability Endpoint (No Auth Required)

The availability endpoint is public and should return 200 without redirects:

```bash
curl "http://localhost:5000/availability?specialization=cardiology&date=2026-01-13"
```

Expected response:
```json
{
  "status": "success",
  "availabilities": [
    {
      "availability_id": 1,
      "start_time": "2026-01-13 09:00:00",
      "end_time": "2026-01-13 10:00:00",
      "is_available": true,
      "doctor": {
        "doctor_id": 1,
        "first_name": "Jan",
        "last_name": "Kowalski",
        "specialization": "cardiology",
        "license_number": "PWZ12345"
      }
    }
  ]
}
```

**Note:** This endpoint uses empty string route (`''`) instead of `'/'` to avoid 308 redirects when called without trailing slash.