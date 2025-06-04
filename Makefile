PYTHON:=venv/bin/python
PIP:=venv/bin/pip
PYTEST:=venv/bin/py.test
COV:=venv/bin/coverage

.PHONY: clean venv run test cov test-build test-docker
clean:
	rm -rf venv

venv: clean
	python3.11 -m venv venv
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) console --run

test:
	$(PYTEST) test

cov:
	$(COV) run -m pytest test || true
	$(COV) html
	open htmlcov/index.html

test-build:
	docker build . -t elekto-test --target test

test-docker: test-build
	docker run -it --rm --entrypoint=./test-entrypoint.sh elekto-test
