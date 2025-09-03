VENV_NAME = venv
PYTHON = $(VENV_NAME)/bin/python
PIP = $(VENV_NAME)/bin/pip
COMPOSE = docker compose
SERVICE = web

.PHONY: env help venv test lint manage

help:
	@echo "Makefile commands:"
	@echo "  make env      		- Create env file from template"	
	@echo "  make venv     		- Create virtual environment"
	@echo "  make install  		- Install dependencies"
	@echo "  make freeze   		- Freeze dependencies"
	@echo "  make tests    		- Run tests"
	@echo "  make linters  		- Run ruff formatter and linter"
	@echo "  make up       		- Run project"
	@echo "  make down	   		- Stop project"
	@echo "  make manage   		- Run manage.py command"
	@echo "  make manage-help	- Show available manage.py commands"

generate-env:
	./generate_env.sh

venv:
	python3 -m venv $(VENV_NAME)

install: venv
	$(PIP) install -r requirements.txt

freeze: venv
	$(PIP) freeze > requirements.txt

tests:
	$(COMPOSE) exec -i $(SERVICE) python manage.py test --keepdb

linters:
	ruff format; \
	ruff check --fix; \
	# mypy

migrate:
	./migrate.sh

import-sql: 
	./import-sql.sh

up:
	$(COMPOSE) up --build \
	--remove-orphans \
	--scale migration=0 \

down:
	$(COMPOSE) down

manage-help:
	$(COMPOSE) exec -T $(SERVICE) python manage.py help

manage:
	$(COMPOSE) exec -i $(SERVICE) python manage.py $(filter-out $@,$(MAKECMDGOALS))

%:
	@:
