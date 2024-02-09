.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	@if [ "$(USING_POETRY)" ]; then poetry env info && exit; fi
	@echo "Running using $(ENV_PREFIX)"
	@$(ENV_PREFIX)python -V
	@$(ENV_PREFIX)python -m site

.PHONY: install
install:          ## Install the project in dev mode.
	@if [ "$(USING_POETRY)" ]; then poetry install && exit; fi
	@echo "Don't forget to run 'make virtualenv' if you got errors."
	$(ENV_PREFIX)pip install -e .[test]

.PHONY: runserver
runserver:          ## Django run server.
	$(ENV_PREFIX)python3 cos_registration_server/manage.py runserver

.PHONY: secretkey
secretkey:          ## Generate the django secret key.
	$(ENV_PREFIX)python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'


.PHONY: fmt
fmt:              ## Format code using black & isort.
	$(ENV_PREFIX)isort cos_registration_server/
	$(ENV_PREFIX)black -l 79 cos_registration_server/

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)flake8 cos_registration_server/ --exclude migrations,tests.py
	$(ENV_PREFIX)black -l 79 --check cos_registration_server/
	$(ENV_PREFIX)mypy --ignore-missing-imports cos_registration_server/

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	$(ENV_PREFIX)coverage run --source='.' cos_registration_server/manage.py test api devices
	$(ENV_PREFIX)coverage xml
	$(ENV_PREFIX)coverage html

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build

.PHONY: virtualenv
virtualenv:       ## Create a virtual environment.
	@if [ "$(USING_POETRY)" ]; then poetry install && exit; fi
	@echo "creating virtualenv ..."
	@rm -rf .venv
	@python3 -m venv .venv
	@./.venv/bin/pip install -U pip
	@./.venv/bin/pip install -e .[test]
	@echo
	@echo "!!! Please run 'source .venv/bin/activate' to enable the environment !!!"

.PHONY: release
release:          ## Create a new tag for release.
	@echo "WARNING: This operation will create s version tag and push to github"
	@read -p "Version? (provide the next x.y.z semver) : " TAG
	@echo "$${TAG}" > cos_registration_server/cos_registration_server/VERSION
	@$(ENV_PREFIX)gitchangelog > HISTORY.md
	@git add cos_registration_server/cos_registration_server/VERSION HISTORY.md
	@git commit -m "release: version $${TAG} 🚀"
	@echo "creating git tag : $${TAG}"
	@git tag $${TAG}
	@git push -u origin HEAD --tags
	@echo "Github Actions will detect the new tag and release the new version."
