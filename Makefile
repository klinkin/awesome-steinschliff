PROJECT_PATH := steinschliff

help:
	@echo "make lint                  - Syntax check"
	@echo "make format                - Format project with ruff and black"
	@echo "make i18n-extract          - Extract translatable strings"
	@echo "make i18n-init LOCALE=xx   - Initialize new locale (e.g. LOCALE=de)"
	@echo "make i18n-update LOCALE=xx - Update existing locale"
	@echo "make i18n-update-all       - Update all existing locales"
	@echo "make i18n-compile          - Compile all translations"
	@echo "make i18n-list             - List available locales"
	@echo "make readme                - Generate README.md"
	@echo "make readme_new            - Generate README.md (new)"
	@exit 0

lint:
	poetry run mypy $(PROJECT_PATH)
	poetry run ruff check $(PROJECT_PATH)
	poetry run black --check $(PROJECT_PATH)

format:
	poetry run black $(PROJECT_PATH)
	poetry run ruff format $(PROJECT_PATH)
	poetry run ruff check --fix --select I $(PROJECT_PATH)

# Internationalization (i18n) targets
i18n-extract:
	python scripts/manage_translations.py extract

i18n-init:
	@if [ -z "$(LOCALE)" ]; then \
		echo "Error: LOCALE is required. Usage: make i18n-init LOCALE=xx"; \
		exit 1; \
	fi
	python scripts/manage_translations.py init -l $(LOCALE)

i18n-update:
	@if [ -z "$(LOCALE)" ]; then \
		echo "Error: LOCALE is required. Usage: make i18n-update LOCALE=xx"; \
		exit 1; \
	fi
	python scripts/manage_translations.py update -l $(LOCALE)

i18n-update-all:
	python scripts/manage_translations.py update-all

i18n-compile:
	python scripts/manage_translations.py compile

i18n-list:
	python scripts/manage_translations.py list

readme_new:
	poetry run python scripts/gen_readme_new.py

readme:
	poetry run python scripts/gen_readme.py