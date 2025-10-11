PYTEST:=./venv/bin/pytest
PIP:=./venv/bin/pip

.PHONY: clean
clean:
	rm -rf ./venv

.PHONY: venv
venv: clean
	python3.11 -m venv venv
	$(PIP) install -r requirements.txt

.PHONY: test
test:
	$(PYTEST)
