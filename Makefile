# Описание проекта
#
# Makefile для сборки и управления проектом awesome-steinschliff

# --------------------------------------------------------------------------------
# Настройки

# Путь к проекту
PROJECT_PATH := steinschliff

# Исполняемые файлы инструментов
POETRY = poetry
PYTHON = poetry run python
MYPY = poetry run mypy
RUFF = poetry run ruff
BLACK = poetry run black
PYTEST = poetry run pytest

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

.PHONY: help
help:
	@echo "${BLUE}Команды проекта:${DEF}"
	@echo "${GREEN}make help${DEF}              - ${YELLOW}Показать это сообщение справки${DEF}"
	@echo ""
	@echo "${BLUE}Качество и тестирование:${DEF}"
	@echo "${GREEN}make lint${DEF}              - ${YELLOW}Проверка синтаксиса (mypy, ruff, black)${DEF}"
	@echo "${GREEN}make format${DEF}            - ${YELLOW}Форматирование проекта с ruff и black${DEF}"
	@echo "${GREEN}make test${DEF}              - ${YELLOW}Запуск тестов${DEF}"
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
	@echo ""
	@echo "${BLUE}CI/CD:${DEF}"
	@echo "${GREEN}make ci${DEF}                - ${YELLOW}Запуск lint, тестов и сборки${DEF}"
	@exit 0

# --------------------------------------------------------------------------------
# Качество и тестирование

.PHONY: lint
lint:
	@echo "${YELLOW}Запуск проверки синтаксиса...${DEF}"
	$(MYPY) $(PROJECT_PATH)
	$(RUFF) check $(PROJECT_PATH)
	$(BLACK) --check $(PROJECT_PATH)
	@echo "${GREEN}Проверка синтаксиса завершена.${DEF}"

.PHONY: test
test:
	@echo "${YELLOW}Запуск тестов...${DEF}"
	$(PYTEST) -v
	@echo "${GREEN}Тесты завершены.${DEF}"

.PHONY: format
format:
	@echo "${YELLOW}Форматирование проекта...${DEF}"
	$(BLACK) $(PROJECT_PATH)
	$(RUFF) format $(PROJECT_PATH)
	$(RUFF) check --fix --select I $(PROJECT_PATH)
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
	$(POETRY) run python scripts/gen_readme_new.py --sort $(or $(SORT),$(DEFAULT_SORT))
	@echo "${GREEN}Проект собран.${DEF}"

# --------------------------------------------------------------------------------
# CI/CD

.PHONY: ci
ci: lint test build
	@echo "${GREEN}CI/CD пайплайн завершен успешно.${DEF}"