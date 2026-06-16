CONFIG ?= config/workers.yml
COMPOSE = docker compose

generate:
	python3 generate_compose.py $(CONFIG) docker-compose.yml
.PHONY: generate

build: generate
	$(COMPOSE) build
.PHONY: build

up: generate
	$(COMPOSE) up -d
.PHONY: up

down:
	$(COMPOSE) down -v
.PHONY: down

produce-all: generate
	$(COMPOSE) --profile producer run --rm producer python main.py --all
.PHONY: produce-all

produce-day: generate
	$(COMPOSE) --profile producer run --rm producer python main.py --day $(day) --month $(month)
.PHONY: produce-day

produce-today: generate
	$(COMPOSE) --profile producer run --rm producer python main.py
.PHONY: produce-today

scale: generate
	$(COMPOSE) up -d \
		--scale fetch=$(or $(FETCH),5) \
		--scale transform=$(or $(TRANSFORM),2) \
		--scale validate=$(or $(VALIDATE),2) \
		--scale load=$(or $(LOAD),1)
.PHONY: scale

logs:
	$(COMPOSE) logs -f $(SERVICE)
.PHONY: logs

logs-all:
	$(COMPOSE) logs -f
.PHONY: logs-all

ps:
	$(COMPOSE) ps
.PHONY: ps

rabbit:
	@echo "RabbitMQ management: http://localhost:15672 (guest/guest)"
.PHONY: rabbit
