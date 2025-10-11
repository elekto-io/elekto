# Elekto integration tests
This directory contains the integration tests for Elekto. These test focus on the integration with Github and the way
Github usernames flow through the Elekto application.

## Running tests
The setup is not bootstrapped (yet), so various manual steps are required to run the required local infra. Then the
integration tests can be run.

### Infra
These tests require the following to be running:
- elekto
  - Change the Github endpoints in `elekto/constants.py` to:
    - GITHUB_AUTHORIZE = 'http://localhost:9000/login/oauth/authorize'
    - GITHUB_ACCESS = 'http://localhost:9000/login/oauth/access_token'
    - GITHUB_PROFILE = 'http://localhost:9000/user'
  - Start with `python console --run` (in the Elekto project).
  - Optionally also do `docker compose up` if you want to use the Postgres database it provides.
- github-static-mock
  - https://github.com/oduludo/github-oauth-mock
  - Start the required Redis server with `docker compose up` in the github-oauth-mock project.
  - Install dependencies with `poetry install`.
  - Start the mock server with `poetry run start`.

### Tests
Tests can be run from the `elekto/integration_tests` directory. Tests runner is Pytest, headless browser testing is done
using Playwright. A virtual environment is required to run the tests. Tests assume all infra runs at the default ports.
- Create the virtual env with `make venv`. This will also install dependencies.
- Run tests with `make test`.
