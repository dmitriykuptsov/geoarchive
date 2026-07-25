# GeoArchive Backend

Backend service for the GeoArchive geological information system.

The system is designed to store and manage:

- Geological deposits
- Geological maps
- Map layers
- Documents and PDF reports
- Deposit information
- Access groups and group members
- Deposit-level access permissions
- Full-text searchable geological information

The backend is built with:

- Python
- FastAPI
- SQLAlchemy
- Alembic
- MySQL
- Docker
- Docker Compose

---

## Requirements

Install the following software:

- Docker
- Docker Compose

Verify the installation:

```bash
docker --version
docker compose version
```

##Project Structure

The project currently has a structure similar to:

```
backend/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   └── users.py
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── bootstrap.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── access_group.py
│   │   ├── group_member.py
│   │   ├── deposit.py
│   │   ├── deposit_access.py
│   │   ├── document.py
│   │   ├── map.py
│   │   └── layer.py
│   │
│   └── schemas/
│       ├── auth.py
│       └── user.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Environment Configuration

Create a .env file in the project root.

```
MYSQL_DATABASE=geoarchive
MYSQL_USER=geoarchive
MYSQL_PASSWORD=geoarchive_password
MYSQL_ROOT_PASSWORD=root_password

DATABASE_URL=mysql+pymysql://geoarchive:geoarchive_password@mysql:3306/geoarchive

JWT_SECRET_KEY=change-this-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Complete First-Time Setup

For a fresh installation:

1. Build the backend image

```
docker compose build backend
```
2. Start MySQL

```
docker compose up -d mysql
```
3. Apply database migrations

```
docker compose run --rm backend \
    alembic upgrade head
```
4. Bootstrap the system
```
docker compose run --rm backend \
    python -m app.cli bootstrap
```
5. Start the backend
```
docker compose up -d backend
```
