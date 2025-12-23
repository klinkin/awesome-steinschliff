set dotenv-load := true
# Используем non-login shell, чтобы не зависеть от пользовательских профилей (например, ~/.bash_profile).
set shell := ["bash", "-c"]

# ------------------------------------------------------------
# Awesome Steinschliff — just recipes (замена Makefile по workflow)
#
# Примеры:
#   just lint
#   just test
#   just build temperature
#   just export-json
#   just export-csv
#
# Параметры:
#   just build <sort>    # sort: name|rating|country|temperature
#   just i18n-init <loc> # loc: ru/en/...

default:
  @just --list

# --- Quality -------------------------------------------------

lint:
  uv run mypy steinschliff scripts tests
  uv run ruff check steinschliff scripts tests
  uv run black --check steinschliff scripts tests

format:
  uv run black steinschliff scripts tests
  uv run ruff format steinschliff scripts tests
  uv run ruff check --fix --select I steinschliff scripts tests

test:
  uv run pytest -v

ci:
  just lint
  just test
  just build temperature
  just webapp-build
  @echo "CI/CD пайплайн завершен успешно."

# --- i18n ----------------------------------------------------

i18n-extract:
  uv run python scripts/manage_translations.py extract

i18n-init locale:
  uv run python scripts/manage_translations.py init -l {{locale}}

i18n-update locale:
  uv run python scripts/manage_translations.py update -l {{locale}}

i18n-update-all:
  uv run python scripts/manage_translations.py update-all

i18n-compile:
  uv run python scripts/manage_translations.py compile

i18n-list:
  uv run python scripts/manage_translations.py list

# --- Build / export ------------------------------------------

build sort="temperature":
  uv run steinschliff generate --sort {{sort}}

export-json:
  uv run steinschliff export-json

export-csv:
  uv run steinschliff export-csv --output structures.csv

# --- Webapp (Astro) ------------------------------------------

webapp-install:
  cd webapp && npm ci

webapp-dev:
  cd webapp && npm run dev

webapp-build:
  cd webapp && npm run build

webapp-preview:
  cd webapp && npm run preview

# --- Bootstrap / clean ---------------------------------------

bootstrap:
  uv sync --extra dev
  cd webapp && npm ci

clean-py:
  find . -name "__pycache__" -type d -prune -exec rm -rf {} \;
  find . -name "*.pyc" -delete
  find . -name "*.pyo" -delete
  find . -name ".pytest_cache" -type d -prune -exec rm -rf {} \;

clean-webapp:
  rm -rf webapp/dist

clean: clean-py clean-webapp


