# Разработка

Основной workflow проекта — через `just`. `Makefile` оставлен как набор алиасов для обратной совместимости.

Содержание:

- [Быстрый старт](#быстрый-старт)
- [Воспроизводимые прогоны через uv](#воспроизводимые-прогоны-через-uv)
- [Повседневные команды](#повседневные-команды)
- [i18n](#i18n)
- [Документация (MkDocs)](#документация-mkdocs)
- [Webapp (Astro)](#webapp-astro)
- [Эквиваленты make → just](#эквиваленты-make--just)

## Быстрый старт

Требования:

- Python 3.13+
- `uv`
- Node.js (только если работаете с `webapp/`)

Установка зависимостей (Python + webapp):

```bash
just bootstrap
```

Быстрая проверка (ruff + mypy + pre-commit):

```bash
just check
```

## Воспроизводимые прогоны через uv

`justfile` использует `uv run --frozen` и `uv sync --frozen`, чтобы команды выполнялись строго по `uv.lock`.

Если нужен только Python-стек без webapp:

```bash
uv sync --frozen --extra dev
```

## Повседневные команды

Список команд: `just help`.

```bash
just check                 # ruff check + mypy + pre-commit run --all-files
just lint                  # mypy + ruff format --check + ruff check
just format                # форматирование + сортировка импортов
just test                  # pytest
just build                 # генерация README (sort=temperature)
just build name            # генерация README с сортировкой
just export-json           # экспорт JSON для webapp
just export-csv            # экспорт CSV (structures.csv)
just ci                    # lint + test + build + webapp-build
```

Про контент (структуры/YAML/snow conditions) см. [content.md](content.md).

## i18n

```bash
just i18n-extract
just i18n-init ru
just i18n-update ru
just i18n-update-all
just i18n-compile
just i18n-list
```

## Документация (MkDocs)

Локальный сайт документации собирается из `docs/` (конфиг: `mkdocs.yml`).

Запуск dev-сервера:

```bash
just docs-dev
```

Сборка статического сайта в `site/`:

```bash
just docs-build
```

## Webapp (Astro)

```bash
just webapp-install
just webapp-dev
just webapp-build
just webapp-preview
```

## Эквиваленты make → just

- `make lint` → `just lint`
- `make test` → `just test`
- `make format` → `just format`
- `make build SORT=temperature` → `just build temperature`
- `make export-json` → `just export-json`
- `make export-csv` → `just export-csv`
- `make ci` → `just ci`
