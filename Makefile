.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: install
install:          ## Install the project in dev mode.
	@echo "Don't forget to run 'make virtualenv' if you got errors."
	pip install -e .[test]

.PHONY: runserver
runserver:          ## Django run server.
	python3 cos_registration_server/manage.py runserver

.PHONY: secretkey
secretkey:          ## Generate the django secret key.
	python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'


.PHONY: fmt
fmt:              ## Format code using black & isort.
	isort --profile black cos_registration_server/
	black -l 79 cos_registration_server/

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	black -l 79 --check cos_registration_server/
	flake8 cos_registration_server/ --exclude migrations,tests.py
	mypy --strict cos_registration_server

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	coverage run --source='.' cos_registration_server/manage.py test api devices applications
	coverage xml
	coverage html

.PHONY: install-test-requirements
install-test-requirements: ## Install test requirements.
	pip install -r requirements-test.txt

.PHONY: pytest
pytest: install-test-requirements ## Run pytest in the cos_registration_server folder.
	cd cos_registration_server && pytest .



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
	@gitchangelog > HISTORY.md
	@git add cos_registration_server/cos_registration_server/VERSION HISTORY.md
	@git commit -m "release: version $${TAG} 🚀"
	@echo "creating git tag : $${TAG}"
	@git tag $${TAG}
	@git push -u origin HEAD --tags
	@echo "Github Actions will detect the new tag and release the new version."
