# Makefile targets simplify daily operatons:
#   make: Same as "make test"
#   make test: Runs all testing (lint, unit, integ) in sequence
#   make setup: Installs packages and builds the vault password file
#   make lint: Runs YAML and Python linters
#   make unit: Runs function-level testing on Python filters
#   make integ: Runs the test playbook (integration test)

.DEFAULT_GOAL := test
.PHONY: test
test:	lint unit integ

.PHONY: setup
setup:
	@echo "Starting  setup"
	pip install -r requirements.txt
	echo "brkrst3310" > ~/vault_pass_file.txt
	@echo "Completed setup"


.PHONY: lint
lint:
	@echo "Starting  lint"
	find . -name "*.yml" | xargs yamllint -s
	find . -name "*.py" | xargs pylint
	find . -name "*.py" | xargs bandit
	@echo "Completed lint"

.PHONY: unit
unit:
	@echo "Starting  unit tests"
	ansible-playbook tests/unittest_playbook.yml
	@echo "Completed unit tests"

.PHONY: integ
integ:
	@echo "Starting  integration tests"
	ansible-playbook tests/integration_playbook.yml
	@echo "Completed integration tests"
