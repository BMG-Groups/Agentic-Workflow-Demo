.PHONY: setup install test clean help

help:
	@echo "WAT Framework - Available commands:"
	@echo "  make setup    - Set up development environment"
	@echo "  make install  - Install dependencies"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean temporary files"

setup:
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  venv\\Scripts\\activate     (Windows)"
	@echo "  source venv/bin/activate  (Linux/Mac)"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

clean:
	rm -rf .tmp/*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
