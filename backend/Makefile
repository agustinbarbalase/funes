API_URL ?= http://localhost:8000

include .env
export

up:
	docker compose up --build -d
.PHONY: up

down:
	docker compose down -v --remove-orphans
.PHONY: down

dev:
	docker compose run --name funes-api --build --rm --service-ports api bash
.PHONY: dev

db:
	docker compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}
.PHONY: db

migrate:
	docker compose run --rm migrate
.PHONY: migrate

populate:
	python3 scripts/populate.py
.PHONY: populate

populate-day:
	python3 scripts/populate.py --day $(day) --month $(month)
.PHONY: populate-day

populate-all:
	python3 scripts/populate.py --all
.PHONY: populate-all

logs:
	docker compose logs -f
.PHONY: logs

logs-%:
	docker compose logs -f $*
.PHONY: logs-%