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

[group("meta")]
[doc("Показать список доступных команд (рецептов).")]
default:
  @just --list

# --- Quality -------------------------------------------------

[group("quality")]
[doc("Статический анализ: mypy + ruff + black --check.")]
lint:
  uv run mypy steinschliff scripts tests
  uv run ruff check steinschliff scripts tests
  uv run black --check steinschliff scripts tests

[group("quality")]
[doc("Форматирование: black + ruff format + фиксация import-порядка.")]
format:
  uv run black steinschliff scripts tests
  uv run ruff format steinschliff scripts tests
  uv run ruff check --fix --select I steinschliff scripts tests

[group("quality")]
[doc("Запуск тестов (pytest).")]
test:
  uv run pytest -v

[group("quality")]
[doc("Локальный CI-пайплайн: lint + test + build temperature + webapp-build.")]
ci:
  just lint
  just test
  just build temperature
  just webapp-build
  @echo "CI/CD пайплайн завершен успешно."

# --- i18n ----------------------------------------------------

[group("i18n")]
[doc("Извлечь переводимые строки (pybabel extract).")]
i18n-extract:
  uv run python scripts/manage_translations.py extract

[group("i18n")]
[doc("Инициализировать новую локаль: just i18n-init <locale>.")]
i18n-init locale:
  uv run python scripts/manage_translations.py init -l {{locale}}

[group("i18n")]
[doc("Обновить существующую локаль: just i18n-update <locale>.")]
i18n-update locale:
  uv run python scripts/manage_translations.py update -l {{locale}}

[group("i18n")]
[doc("Обновить все существующие локали.")]
i18n-update-all:
  uv run python scripts/manage_translations.py update-all

[group("i18n")]
[doc("Скомпилировать переводы (pybabel compile).")]
i18n-compile:
  uv run python scripts/manage_translations.py compile

[group("i18n")]
[doc("Показать список доступных локалей.")]
i18n-list:
  uv run python scripts/manage_translations.py list

# --- Build / export ------------------------------------------

[group("build")]
[doc("Сборка README (по умолчанию sort=temperature). Пример: just build name")]
build sort="temperature":
  uv run steinschliff generate --sort {{sort}}

[group("build")]
[doc("Экспорт JSON для webapp.")]
export-json:
  uv run steinschliff export-json

[group("build")]
[doc("Экспорт CSV в structures.csv.")]
export-csv:
  uv run steinschliff export-csv --output structures.csv

# --- Webapp (Astro) ------------------------------------------

[group("webapp")]
[doc("Установить npm-зависимости webapp (npm ci).")]
webapp-install:
  cd webapp && npm ci

[group("webapp")]
[doc("Запуск dev-сервера Astro.")]
webapp-dev:
  cd webapp && npm run dev

[group("webapp")]
[doc("Сборка webapp (Astro build).")]
webapp-build:
  cd webapp && npm run build

[group("webapp")]
[doc("Предпросмотр сборки webapp.")]
webapp-preview:
  cd webapp && npm run preview

# --- Bootstrap / clean ---------------------------------------

[group("setup")]
[doc("Установить Python deps (uv sync --extra dev) и webapp deps (npm ci).")]
bootstrap:
  uv sync --extra dev
  cd webapp && npm ci

[group("clean")]
[doc("Очистить python артефакты (__pycache__, .pytest_cache, *.pyc).")]
clean-py:
  find . -name "__pycache__" -type d -prune -exec rm -rf {} \;
  find . -name "*.pyc" -delete
  find . -name "*.pyo" -delete
  find . -name ".pytest_cache" -type d -prune -exec rm -rf {} \;

[group("clean")]
[doc("Очистить артефакты webapp (webapp/dist).")]
clean-webapp:
  rm -rf webapp/dist

[group("clean")]
[doc("Очистить python + webapp артефакты.")]
clean: clean-py clean-webapp


