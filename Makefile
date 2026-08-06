# ------------------------------------------------------------------------------
# Configuration
#
# Every variable uses `?=`, so all of them can be overridden from the
# environment or on the command line, e.g.:
#
#   make push-version PLATFORMS=linux/amd64 REGISTRY=quay.io
#   make test PYTHON=python3.13
# ------------------------------------------------------------------------------

DOCKER ?= docker
BUILDX ?= $(DOCKER) buildx

# Image coordinates.
REGISTRY   ?= ghcr.io
IMAGE_NAME ?= elekto-dev/elekto
IMAGE      ?= $(REGISTRY)/$(IMAGE_NAME)
LATEST_TAG ?= latest

# Target platforms for published images.
PLATFORMS ?= linux/amd64,linux/arm64

# Python toolchain.
PYTHON_VERSION ?= 3.13
VENV           ?= venv
# Prefer the virtualenv when one exists, otherwise fall back to the interpreter
# on PATH. CI installs into the runner's Python and never creates a venv, so
# this keeps the workflows from having to override PYTHON themselves.
PYTHON         ?= $(shell \
	if [ -x $(VENV)/bin/python ]; then echo $(VENV)/bin/python; \
	else command -v python3 || echo python; fi)
PYTEST         ?= $(VENV)/bin/py.test
COV            ?= $(VENV)/bin/coverage
VENV_PYTHON    ?= python$(PYTHON_VERSION)

# Registry credentials, consumed by `make login`.
REGISTRY_USER     ?=
REGISTRY_PASSWORD ?=

# Build inputs.
TEST_IMAGE ?= elekto-test
BUILD_ARGS ?= --build-arg PYTHON_VERSION=$(PYTHON_VERSION)

# Multi-arch tooling. The default docker driver cannot build more than one
# platform, so a docker-container builder is required. binfmt is pinned by
# digest because `buildx-setup` runs it as a privileged container.
BUILDX_BUILDER ?= elekto
BINFMT_IMAGE   ?= tonistiigi/binfmt:qemu-v8.1.5-43@sha256:46c5a036f13b8ad845d6703d38f8cce6dd7c0a1e4d42ac80792279cabaeff7fb

# Ask setuptools-scm directly, falling back to package metadata for an installed
# copy with no git history. Reading it from git means nothing has to be built to
# learn the version. The `+local` segment is not a legal image tag, so `+`
# becomes `-`. Errors are swallowed so `help` still works in a checkout with
# neither available; the push targets enforce it via `require-version`.
VERSION     = $(shell \
	$(PYTHON) -c "from setuptools_scm import get_version; print(get_version())" 2>/dev/null \
	|| $(PYTHON) -c "from importlib.metadata import version; print(version('elekto'))" 2>/dev/null)
VERSION_TAG = $(subst +,-,$(VERSION))

.DEFAULT_GOAL := help

.PHONY: help print-% clean venv version-deps version require-version run test cov \
        image push-version push-latest test-build test-container \
        test-container-notty test-docker test-docker-notty buildx-setup buildx-teardown login

# ------------------------------------------------------------------------------
# Meta
# ------------------------------------------------------------------------------

help: ## Show this help text.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Every variable is overridable, e.g. make push-version PLATFORMS=linux/amd64"

print-%: ## Print any variable, e.g. make print-VERSION_TAG
	@echo "$($*)"

# ------------------------------------------------------------------------------
# Python
# ------------------------------------------------------------------------------

clean: ## Remove the virtualenv.
	rm -rf $(VENV)

venv: clean ## Create the virtualenv and install the project.
	$(VENV_PYTHON) -m venv $(VENV)
	# Explicit paths, not $(PYTHON): the venv does not exist when this rule is
	# expanded, so the autodetect above would resolve to the system interpreter.
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pip install --no-deps -e .

version-deps: ## Install the tooling needed to compute the version.
	$(PYTHON) -m pip install setuptools-scm

version: ## Print the package version.
	@echo "$(VERSION)"

require-version:
	@test -n "$(VERSION_TAG)" || { \
	  echo "Cannot determine the version."; \
	  echo "Run 'make version-deps', or 'make venv' for a full environment."; \
	  exit 1; }

run: ## Run the app locally.
	$(PYTHON) console --run

test: ## Run the test suite.
	$(PYTEST) test

cov: ## Run tests with coverage and open the report.
	$(COV) run -m pytest test || true
	$(COV) html
	open htmlcov/index.html

# ------------------------------------------------------------------------------
# Images
#
# buildx cannot --load a multi-platform result, so the published targets build
# and push in a single invocation with every tag attached. Only `image`, which
# is meant to leave something in the local image store, is single-platform.
# ------------------------------------------------------------------------------

image: ## Build a single-arch image into the local image store.
	$(BUILDX) build --load -t $(IMAGE):$(LATEST_TAG) $(BUILD_ARGS) .

push-version: require-version ## Build all PLATFORMS and push the version tag.
	$(BUILDX) build --platform $(PLATFORMS) --push \
	  -t $(IMAGE):$(VERSION_TAG) \
	  $(BUILD_ARGS) .

push-latest: require-version ## Build all PLATFORMS, push the version tag and latest.
	$(BUILDX) build --platform $(PLATFORMS) --push \
	  -t $(IMAGE):$(VERSION_TAG) -t $(IMAGE):$(LATEST_TAG) \
	  $(BUILD_ARGS) .

# ------------------------------------------------------------------------------
# Containerised tests
# ------------------------------------------------------------------------------

test-build: ## Build the test-stage image.
	$(BUILDX) build --load --target test -t $(TEST_IMAGE) $(BUILD_ARGS) .

test-container: test-build ## Run the test suite in a container.
	$(DOCKER) run -it --rm --entrypoint=./test-entrypoint.sh $(TEST_IMAGE)

test-container-notty: test-build ## Run the test suite in a container without a TTY (CI).
	$(DOCKER) run --rm --entrypoint=./test-entrypoint.sh $(TEST_IMAGE)

# Aliases for the names these targets had before the rename.
test-docker: test-container
test-docker-notty: test-container-notty

# ------------------------------------------------------------------------------
# CI orchestration
#
# The workflows call these targets and nothing else, so the full release path is
# reproducible locally with the same commands CI runs.
# ------------------------------------------------------------------------------

buildx-setup: ## Install QEMU emulators and a multi-platform builder.
	$(DOCKER) run --privileged --rm $(BINFMT_IMAGE) --install all
	$(BUILDX) inspect $(BUILDX_BUILDER) >/dev/null 2>&1 \
	  || $(BUILDX) create --name $(BUILDX_BUILDER) --driver docker-container --use
	$(BUILDX) use $(BUILDX_BUILDER)

buildx-teardown: ## Stop the multi-platform builder created by buildx-setup.
	-$(BUILDX) stop $(BUILDX_BUILDER)

login: ## Log in to the registry using REGISTRY_USER/REGISTRY_PASSWORD.
	@test -n "$(REGISTRY_USER)" || { echo "REGISTRY_USER is required"; exit 1; }
	@test -n "$(REGISTRY_PASSWORD)" || { echo "REGISTRY_PASSWORD is required"; exit 1; }
	@echo "$(REGISTRY_PASSWORD)" | $(DOCKER) login $(REGISTRY) \
	  --username "$(REGISTRY_USER)" --password-stdin
