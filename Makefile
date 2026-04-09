PYTHON ?= python

.PHONY: setup run test coverage lint

setup:
	$(PYTHON) -m venv .venv
	. .venv/Scripts/activate; pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --port 8000

test:
	pytest

coverage:
	pytest --cov=app --cov-report=term-missing --cov-report=xml

lint:
	ruff check app tests
