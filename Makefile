.PHONY: install test lint

install:
	pip install --upgrade pip setuptools
	pip install -r requirements.txt

test: install
	pytest -q

lint:
	python -m compileall -q shipping tests
