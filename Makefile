# Chat with Tools Framework - Makefile
# Convenient commands for development and deployment

.PHONY: help install dev test clean build upload docs run-chat run-council run-tools

# Default target
help:
	@echo "Chat with Tools Framework - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev          - Install development dependencies"
	@echo "  make clean        - Clean build artifacts and caches"
	@echo ""
	@echo "Running the Framework:"
	@echo "  make run          - Launch interactive menu"
	@echo "  make chat         - Run single agent chat"
	@echo "  make council      - Run multi-agent council mode"
	@echo "  make tools        - Test tools interactively"
	@echo ""
	@echo "Development:"
	@echo "  make test         - Run test suite"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run code linters"
	@echo "  make format       - Format code with black"
	@echo "  make type-check   - Run type checking with mypy"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         - Generate documentation"
	@echo "  make docs-serve   - Serve documentation locally"
	@echo ""
	@echo "Package Management:"
	@echo "  make build        - Build distribution packages"
	@echo "  make upload-test  - Upload to TestPyPI"
	@echo "  make upload       - Upload to PyPI (requires credentials)"
	@echo ""
	@echo "Utilities:"
	@echo "  make check-config - Verify configuration"
	@echo "  make benchmark    - Run performance benchmarks"
	@echo "  make clean-memory - Clear agent memory storage"

# Installation targets
install:
	@echo "Installing production dependencies..."
	uv pip install -r requirements.txt
	@echo "✅ Installation complete!"

dev:
	@echo "Installing development dependencies..."
	uv pip install -e ".[dev]"
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Development setup complete!"

# Running targets
run:
	@echo "Launching Chat with Tools Framework..."
	@python main.py

chat:
	@echo "Starting Single Agent Chat..."
	@python demos/main.py

council:
	@echo "Starting Multi-Agent Council Mode..."
	@python demos/council_chat.py

tools:
	@echo "Starting Tool Testing Interface..."
	@python demos/demo_standalone.py

# Testing targets
test:
	@echo "Running test suite..."
	@python -m pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	@python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

test-quick:
	@echo "Running quick tests (no integration tests)..."
	@python -m pytest tests/ -v -m "not slow and not requires_api"

# Code quality targets
lint:
	@echo "Running linters..."
	@echo "Running flake8..."
	@flake8 src/ demos/ tests/ --max-line-length=100 --ignore=E203,W503
	@echo "Running pylint..."
	@pylint src/ demos/ tests/ --max-line-length=100 || true
	@echo "✅ Linting complete!"

format:
	@echo "Formatting code with black..."
	@black src/ demos/ tests/ main.py cwt
	@echo "Sorting imports with isort..."
	@isort src/ demos/ tests/ main.py cwt
	@echo "✅ Code formatted!"

type-check:
	@echo "Running type checking with mypy..."
	@mypy src/ --ignore-missing-imports
	@echo "✅ Type checking complete!"

# Documentation targets
docs:
	@echo "Generating documentation..."
	@cd docs && sphinx-build -b html . _build
	@echo "Documentation generated in docs/_build/index.html"

docs-serve:
	@echo "Serving documentation at http://localhost:8000..."
	@cd docs/_build && python -m http.server

# Build and distribution targets
build:
	@echo "Building distribution packages..."
	@python -m pip install --upgrade build
	@python -m build
	@echo "✅ Packages built in dist/"

upload-test:
	@echo "Uploading to TestPyPI..."
	@python -m pip install --upgrade twine
	@python -m twine upload --repository testpypi dist/*
	@echo "✅ Uploaded to TestPyPI"
	@echo "Install with: pip install -i https://test.pypi.org/simple/ chat-with-tools"

upload:
	@echo "⚠️  This will upload to PyPI. Are you sure? (Press Ctrl+C to cancel)"
	@read -p "Press Enter to continue..."
	@python -m pip install --upgrade twine
	@python -m twine upload dist/*
	@echo "✅ Uploaded to PyPI"
	@echo "Install with: pip install chat-with-tools"

# Utility targets
check-config:
	@echo "Checking configuration..."
	@python -c "import yaml; import sys; \
		config = yaml.safe_load(open('config/config.yaml')); \
		api_key = config.get('openrouter', {}).get('api_key', ''); \
		if not api_key or api_key == 'YOUR API KEY HERE': \
			print('❌ API key not configured in config/config.yaml'); \
			sys.exit(1); \
		else: \
			print('✅ Configuration valid'); \
			print(f'   Model: {config.get(\"openrouter\", {}).get(\"model\", \"Not set\")}'); \
			print(f'   API Key: {\"*\" * 20}{api_key[-4:] if len(api_key) > 4 else \"****\"}');"

benchmark:
	@echo "Running performance benchmarks..."
	@python -c "print('📊 Benchmark suite coming soon...')"

clean:
	@echo "Cleaning build artifacts and caches..."
	@rm -rf build/ dist/ *.egg-info
	@rm -rf src/__pycache__ demos/__pycache__ tests/__pycache__
	@rm -rf src/tools/__pycache__
	@rm -rf .pytest_cache/ .coverage htmlcov/
	@rm -rf .mypy_cache/
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "✅ Cleaned!"

clean-memory:
	@echo "Clearing agent memory storage..."
	@rm -rf agent_memory/memories/*
	@echo "✅ Agent memory cleared!"

# Development workflow shortcuts
check: lint type-check test
	@echo "✅ All checks passed!"

fix: format
	@echo "✅ Code formatted and fixed!"

# Watch for changes and run tests (requires pytest-watch)
watch:
	@echo "Watching for changes..."
	@pytest-watch tests/ --clear

# Create a new tool from template
new-tool:
	@read -p "Enter tool name (e.g., 'web_scraper'): " name; \
	python -c "import sys; \
		name = '$$name'; \
		class_name = ''.join(word.capitalize() for word in name.split('_')) + 'Tool'; \
		content = '''from .base_tool import BaseTool\n\n\
class ' + class_name + '(BaseTool):\n\
    \"\"\"Tool description here\"\"\"\n\n\
    @property\n\
    def name(self) -> str:\n\
        return \"' + name + '\"\n\n\
    @property\n\
    def description(self) -> str:\n\
        return \"Describe what this tool does\"\n\n\
    @property\n\
    def parameters(self) -> dict:\n\
        return {\n\
            \"type\": \"object\",\n\
            \"properties\": {\n\
                \"param\": {\"type\": \"string\", \"description\": \"Parameter description\"}\n\
            },\n\
            \"required\": [\"param\"]\n\
        }\n\n\
    def execute(self, **kwargs) -> dict:\n\
        \"\"\"Execute the tool\"\"\"\n\
        param = kwargs.get(\"param\")\n\
        # Tool implementation here\n\
        return {\"status\": \"success\", \"result\": f\"Processed: {param}\"}\n'''; \
		with open(f'src/tools/{name}_tool.py', 'w') as f: \
			f.write(content); \
		print(f'✅ Created src/tools/{name}_tool.py');"

# Docker targets (if you add Docker support later)
docker-build:
	@echo "Building Docker image..."
	@docker build -t chat-with-tools:latest .

docker-run:
	@echo "Running in Docker container..."
	@docker run -it --rm -v $(PWD)/config:/app/config chat-with-tools:latest

# Virtual environment management
venv:
	@echo "Creating virtual environment with uv..."
	@uv venv
	@echo "✅ Virtual environment created!"
	@echo "Activate with: source .venv/bin/activate"

venv-clean:
	@echo "Removing virtual environment..."
	@rm -rf .venv/
	@echo "✅ Virtual environment removed!"

# Git helpers
pre-commit:
	@echo "Running pre-commit checks..."
	@pre-commit run --all-files

# Default target when just typing 'make'
.DEFAULT_GOAL := help
