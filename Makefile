# Makefile targets simplify daily operatons:
#   make: Same as "make all"
#   make all: Runs the production playbook on live network
#   make setup: Installs packages and builds the vault password file
#   make lint: Runs YAML and Python linters
#   make unit: Runs function-level testing on Python filters
#   make int: Runs the test playbook (integration test)

.DEFAULT_GOAL := all
.PHONY: all
all:
	ansible-playbook nots_playbook.yml

.PHONY: setup
setup:
	@echo "Starting  setup"
	pip install -r requirements.txt
	echo "brkrst3310" > ~/vault_pass_file.txt
	@echo "Completed setup"

.PHONY: test
test:	lint unit int

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

.PHONY: int
int:
	@echo "Starting  playbook tests"
	ansible-playbook tests/test_playbook.yml
	@echo "Completed playbook tests"
