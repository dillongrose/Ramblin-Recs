setup:
	pip install -r backend/requirements.txt || true

dev:
	docker compose up --build

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python scripts/seed.py --events 10000 --users 2000 --interactions 100000

down:
	docker compose down
