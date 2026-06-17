---
description: Docker helper commands. Supports all services.
---

# /docker

Action: $ARGUMENTS (start|stop|restart|logs|shell|rebuild|status)

Optional service filter: `--service <name>` or `-s <name>`

Services: `be`, `celery-worker`, `celery-beat`, `postgres`, `redis`, `rabbitmq`

---

## Commands

### start
```bash
# All services
docker compose up -d
docker compose ps

# Specific service
docker compose up -d <service>
```

### stop
```bash
# All services
docker compose down

# Specific service
docker compose stop <service>
```

### restart
```bash
# All services
docker compose restart
docker compose ps

# Specific service
docker compose restart <service>
```

### logs
```bash
# Django backend
docker compose logs -f be

# Celery worker
docker compose logs -f celery-worker

# All services
docker compose logs -f
```

### shell
```bash
# Django shell
docker compose exec be python manage.py shell

# Django bash
docker compose exec be bash

# Postgres
docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Redis
docker compose exec redis redis-cli
```

### rebuild
```bash
# All services
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose exec be python manage.py migrate

# Specific service
docker compose build --no-cache <service>
docker compose up -d <service>
```

### status
```bash
docker compose ps
docker compose exec be python manage.py check
```

### db-reset
```bash
docker compose down -v
docker compose up -d
docker compose exec be python manage.py migrate
docker compose exec be python manage.py loaddata <fixture>
```

---

## Quick Reference

### Django Backend (be)
| Action | Command |
|--------|---------|
| Start | `docker compose up -d be` |
| Logs | `docker compose logs -f be` |
| Shell | `docker compose exec be python manage.py shell` |
| Bash | `docker compose exec be bash` |
| Test | `docker compose exec be python manage.py test` |
| Migrate | `docker compose exec be python manage.py migrate` |
| Make migrations | `docker compose exec be python manage.py makemigrations` |

### Celery
| Action | Command |
|--------|---------|
| Worker logs | `docker compose logs -f celery-worker` |
| Beat logs | `docker compose logs -f celery-beat` |
| Flower UI | http://localhost:5555 |

### Databases
| Service | Port | Access |
|---------|------|--------|
| Postgres | 5433 | `docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB` |
| Redis | 6379 | `docker compose exec redis redis-cli` |
| RabbitMQ | 5672 | Management UI if enabled |

---

## Service Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Django (be) | 8000 | 8001 |
| Postgres | 5432 | 5433 |
| Redis | 6379 | 6379 |
| RabbitMQ | 5672 | 5672 |
| Flower | 5555 | 5555 |
