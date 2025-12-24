# Описание проекта
#
# Makefile для сборки и управления проектом awesome-steinschliff

# --------------------------------------------------------------------------------
# Настройки

# Путь к проекту
PROJECT_ROOT := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# Исполняемые файлы инструментов
UV = uv
PYTHON = uv run --frozen python
MYPY = uv run --frozen mypy
RUFF = uv run --frozen ruff
PYTEST = uv run --frozen pytest

# Пути проекта и webapp
WEBAPP_DIR   := $(PROJECT_ROOT)/webapp
WEBAPP_NPM   := cd $(WEBAPP_DIR) && npm

# Пути исходников Python (относительно корня проекта)
PY_SRC_DIRS := steinschliff scripts tests
PY_SRC := $(addprefix $(PROJECT_ROOT)/,$(PY_SRC_DIRS))

# Опциональная загрузка переменных окружения
-include .env
export

# Настройки для генерации README
DEFAULT_SORT := temperature
SORT_FIELDS := name snow_type service temperature rating country

# ANSI цвета для стилизованного вывода
RED = \033[31m
BLUE = \033[34m
GREEN = \033[32m
YELLOW = \033[33m
DEF = \033[0m

# --------------------------------------------------------------------------------
# Основные цели

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "${BLUE}Команды проекта:${DEF}"
	@echo "${GREEN}make help${DEF}              - ${YELLOW}Показать это сообщение справки${DEF}"
	@echo ""
	@echo "${BLUE}Качество и тестирование:${DEF}"
	@echo "${GREEN}make lint${DEF}              - ${YELLOW}Проверка синтаксиса (mypy, ruff check, ruff format --check)${DEF}"
	@echo "${GREEN}make format${DEF}            - ${YELLOW}Форматирование проекта (ruff format) + сортировка импортов${DEF}"
	@echo "${GREEN}make test${DEF}              - ${YELLOW}Запуск тестов${DEF}"
	@echo "${GREEN}make check${DEF}             - ${YELLOW}Быстрый прогон (ruff + mypy + pre-commit --all-files)${DEF}"
	@echo ""
	@echo "${BLUE}Интернационализация (i18n):${DEF}"
	@echo "${GREEN}make i18n-extract${DEF}      - ${YELLOW}Извлечение переводимых строк${DEF}"
	@echo "${GREEN}make i18n-init LOCALE=xx${DEF} - ${YELLOW}Инициализация новой локали (например LOCALE=de)${DEF}"
	@echo "${GREEN}make i18n-update LOCALE=xx${DEF} - ${YELLOW}Обновление существующей локали${DEF}"
	@echo "${GREEN}make i18n-update-all${DEF}  - ${YELLOW}Обновление всех существующих локалей${DEF}"
	@echo "${GREEN}make i18n-compile${DEF}     - ${YELLOW}Компиляция всех переводов${DEF}"
	@echo "${GREEN}make i18n-list${DEF}        - ${YELLOW}Список доступных локалей${DEF}"
	@echo ""
	@echo "${BLUE}Генерация документации:${DEF}"
	@echo "${GREEN}make build [SORT=field]${DEF} - ${YELLOW}Сборка проекта (генерация README)${DEF}"
	@echo "${GREEN}make export-json${DEF}        - ${YELLOW}Экспорт JSON для веб-приложения${DEF}"
	@echo "${GREEN}make export-csv${DEF}         - ${YELLOW}Экспорт списка структур в CSV${DEF}"
	@echo ""
	@echo "${BLUE}Веб-сайт (Astro):${DEF}"
	@echo "${GREEN}make webapp-install${DEF}    - ${YELLOW}Установка npm-зависимостей${DEF}"
	@echo "${GREEN}make webapp-dev${DEF}        - ${YELLOW}Локальная разработка (astro dev)${DEF}"
	@echo "${GREEN}make webapp-build${DEF}      - ${YELLOW}Сборка сайта (astro build + pagefind)${DEF}"
	@echo "${GREEN}make webapp-preview${DEF}    - ${YELLOW}Предпросмотр сборки${DEF}"
	@echo "${GREEN}make site-build${DEF}        - ${YELLOW}Алиас на webapp-build${DEF}"
	@echo ""
	@echo "${BLUE}Документация (MkDocs):${DEF}"
	@echo "${GREEN}make docs-dev${DEF}          - ${YELLOW}Запуск MkDocs dev-сервера${DEF}"
	@echo "${GREEN}make docs-build${DEF}        - ${YELLOW}Сборка MkDocs в site/${DEF}"
	@echo "${GREEN}make docs-check${DEF}        - ${YELLOW}Проверка сборки MkDocs (--strict)${DEF}"
	@echo ""
	@echo "${BLUE}CI/CD:${DEF}"
	@echo "${GREEN}make ci${DEF}                - ${YELLOW}Запуск lint, тестов и сборки${DEF}"
	@echo ""
	@echo "${BLUE}Сервисные задачи:${DEF}"
	@echo "${GREEN}make bootstrap${DEF}         - ${YELLOW}uv sync --extra dev + npm ci${DEF}"
	@echo "${GREEN}make clean${DEF}             - ${YELLOW}Очистка артефактов (py, webapp)${DEF}"
	@exit 0

# --------------------------------------------------------------------------------
# Качество и тестирование

.PHONY: lint
lint:
	@echo "${YELLOW}Запуск проверки синтаксиса...${DEF}"
	$(MYPY) $(PY_SRC)
	$(RUFF) format --check $(PY_SRC)
	$(RUFF) check $(PY_SRC)
	@echo "${GREEN}Проверка синтаксиса завершена.${DEF}"

.PHONY: check
check:
	@echo "${YELLOW}Быстрый прогон (ruff + mypy + pre-commit)...${DEF}"
	$(RUFF) check $(PY_SRC)
	$(MYPY) $(PY_SRC)
	$(UV) run --frozen pre-commit run --all-files
	@echo "${GREEN}Быстрый прогон завершён.${DEF}"

.PHONY: test
test:
	@echo "${YELLOW}Запуск тестов...${DEF}"
	$(PYTEST) -v
	@echo "${GREEN}Тесты завершены.${DEF}"

.PHONY: format
format:
	@echo "${YELLOW}Форматирование проекта...${DEF}"
	$(RUFF) format $(PY_SRC)
	$(RUFF) check --fix --select I $(PY_SRC)
	@echo "${GREEN}Форматирование завершено.${DEF}"

# --------------------------------------------------------------------------------
# Интернационализация (i18n)

.PHONY: i18n-extract
i18n-extract:
	@echo "${YELLOW}Извлечение переводимых строк...${DEF}"
	$(PYTHON) scripts/manage_translations.py extract
	@echo "${GREEN}Извлечение строк завершено.${DEF}"

.PHONY: i18n-init
i18n-init:
	@if [ -z "$(LOCALE)" ]; then \
		echo "${RED}Ошибка: LOCALE обязателен. Использование: make i18n-init LOCALE=xx${DEF}"; \
		exit 1; \
	fi
	@echo "${YELLOW}Инициализация локали $(LOCALE)...${DEF}"
	$(PYTHON) scripts/manage_translations.py init -l $(LOCALE)
	@echo "${GREEN}Локаль $(LOCALE) инициализирована.${DEF}"

.PHONY: i18n-update
i18n-update:
	@if [ -z "$(LOCALE)" ]; then \
		echo "${RED}Ошибка: LOCALE обязателен. Использование: make i18n-update LOCALE=xx${DEF}"; \
		exit 1; \
	fi
	@echo "${YELLOW}Обновление локали $(LOCALE)...${DEF}"
	$(PYTHON) scripts/manage_translations.py update -l $(LOCALE)
	@echo "${GREEN}Локаль $(LOCALE) обновлена.${DEF}"

.PHONY: i18n-update-all
i18n-update-all:
	@echo "${YELLOW}Обновление всех локалей...${DEF}"
	$(PYTHON) scripts/manage_translations.py update-all
	@echo "${GREEN}Все локали обновлены.${DEF}"

.PHONY: i18n-compile
i18n-compile:
	@echo "${YELLOW}Компиляция переводов...${DEF}"
	$(PYTHON) scripts/manage_translations.py compile
	@echo "${GREEN}Переводы скомпилированы.${DEF}"

.PHONY: i18n-list
i18n-list:
	@echo "${YELLOW}Список доступных локалей:${DEF}"
	$(PYTHON) scripts/manage_translations.py list

# --------------------------------------------------------------------------------
# Генерация документации

.PHONY: build
build:
	@echo "${YELLOW}Сборка проекта...${DEF}"
	$(UV) run --frozen steinschliff generate --sort $(or $(SORT),$(DEFAULT_SORT))
	@echo "${GREEN}Проект собран.${DEF}"

.PHONY: export-json
export-json:
	@echo "${YELLOW}Экспорт JSON данных...${DEF}"
	$(UV) run --frozen steinschliff export-json
	@echo "${GREEN}JSON экспортирован.${DEF}"

.PHONY: export-csv
export-csv:
	@echo "${YELLOW}Экспорт CSV данных...${DEF}"
	$(UV) run --frozen steinschliff export-csv --output structures.csv
	@echo "${GREEN}CSV экспортирован в structures.csv${DEF}"

# --------------------------------------------------------------------------------
# Веб-сайт (Astro)

.PHONY: bootstrap webapp-install webapp-dev webapp-build webapp-preview site-build

bootstrap:
	$(UV) sync --frozen --extra dev
	$(WEBAPP_NPM) ci

webapp-install:
	$(WEBAPP_NPM) ci

webapp-dev:
	$(WEBAPP_NPM) run dev

webapp-build:
	$(WEBAPP_NPM) run build

webapp-preview:
	$(WEBAPP_NPM) run preview

site-build: webapp-build

# --------------------------------------------------------------------------------
# Документация (MkDocs)

.PHONY: docs-dev docs-build docs-check

docs-dev:
	$(UV) run --frozen mkdocs serve

docs-build:
	$(UV) run --frozen mkdocs build

docs-check:
	$(UV) run --frozen mkdocs build --strict

# --------------------------------------------------------------------------------
# Очистка

.PHONY: clean-py clean-webapp clean

clean-py:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} \;
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".pytest_cache" -type d -prune -exec rm -rf {} \;

clean-webapp:
	rm -rf $(WEBAPP_DIR)/dist

clean: clean-py clean-webapp

# --------------------------------------------------------------------------------
# CI/CD

.PHONY: ci
ci: lint test build site-build
	@echo "${GREEN}CI/CD пайплайн завершен успешно.${DEF}"
