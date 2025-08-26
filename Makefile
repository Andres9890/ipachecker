.PHONY: test test-verbose test-coverage test-html clean install-dev check-env help

# Default Python interpreter
PYTHON ?= python3

# Test directories and files
TEST_DIR = tests
SRC_DIR = ipachecker

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	$(PYTHON) -m pip install -e .

install-dev: ## Install development dependencies
	$(PYTHON) -m pip install -e .
	$(PYTHON) -m pip install -r test-requirements.txt

test: ## Run all tests
	$(PYTHON) -m pytest $(TEST_DIR) -v

test-fast: ## Run tests without coverage
	$(PYTHON) run_tests.py --no-coverage

test-verbose: ## Run tests with verbose output  
	$(PYTHON) run_tests.py --verbose

test-coverage: ## Run tests with coverage report
	$(PYTHON) run_tests.py

test-html: ## Run tests with HTML coverage report
	$(PYTHON) run_tests.py --html-coverage

test-performance: ## Run performance tests
	$(PYTHON) run_tests.py --performance

check-env: ## Check test environment setup
	$(PYTHON) run_tests.py --check-env

test-unit: ## Run only unit tests
	$(PYTHON) -m pytest $(TEST_DIR)/test_*.py -v

test-utils: ## Run only utility tests  
	$(PYTHON) -m pytest $(TEST_DIR)/test_utils.py -v

test-main: ## Run only main module tests
	$(PYTHON) -m pytest $(TEST_DIR)/test_ipachecker.py -v

lint: ## Run code linting
	$(PYTHON) -m flake8 $(SRC_DIR) $(TEST_DIR) --max-line-length=120

format: ## Format code with black
	$(PYTHON) -m black $(SRC_DIR) $(TEST_DIR) --line-length=120

type-check: ## Run type checking with mypy
	$(PYTHON) -m mypy $(SRC_DIR) --ignore-missing-imports

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ *.egg-info/ dist/ build/
	rm -rf $(TEST_DIR)/__pycache__/ $(SRC_DIR)/__pycache__/

docs: ## Generate documentation
	$(PYTHON) -m pydoc -w $(SRC_DIR)

clean-all: clean ## Clean everything including test artifacts
	rm -rf .tox/ .coverage.* htmlcov/

# Continuous Integration targets
ci-test: install-dev test-coverage ## Run CI test suite

ci-lint: lint type-check ## Run CI linting

ci-all: ci-lint ci-test ## Run full CI pipeline

# Development workflow targets  
dev-setup: install-dev check-env ## Set up development environment

dev-test: test-fast lint ## Quick development test cycle

dev-full: clean install-dev test-coverage lint ## Full development test cycle

# Release preparation
pre-release: clean install-dev test-coverage lint type-check ## Pre-release checks

# Docker targets (if using Docker)
docker-test: ## Run tests in Docker
	docker build -t ipachecker-test -f Dockerfile.test .
	docker run --rm ipachecker-test

# Coverage targets
coverage-report: ## Generate detailed coverage report
	$(PYTHON) -m coverage report --show-missing

coverage-xml: ## Generate XML coverage report  
	$(PYTHON) -m coverage xml

coverage-erase: ## Clear coverage data
	$(PYTHON) -m coverage erase

# Quality assurance
qa: lint type-check test-coverage ## Run all quality assurance checks

qa-quick: lint test-fast ## Quick quality assurance

# Benchmark targets
benchmark: ## Run performance benchmarks
	$(PYTHON) -m pytest $(TEST_DIR) -v --benchmark-only

profile: ## Profile test execution
	$(PYTHON) -m cProfile -o profile.stats run_tests.py
	$(PYTHON) -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"