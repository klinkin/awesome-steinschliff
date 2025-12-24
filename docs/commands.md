# CLI и команды

Основной способ работы с проектом в разработке — `just` (см. [development.md](development.md)).
Но CLI можно запускать и напрямую.

## Общая справка

```bash
uv run --frozen steinschliff --help
uv run --frozen steinschliff <command> --help
```

Команды:

- `generate` — генерация README
- `export-json` — экспорт данных в JSON для webapp
- `export-csv` — экспорт списка структур в CSV
- `list` — просмотр/фильтрация структур
- `conditions` — статистика по snow conditions

## `conditions` — статистика по условиям снега

```bash
uv run --frozen steinschliff conditions
uv run --frozen steinschliff conditions --schliffs schliffs
uv run --frozen steinschliff conditions --log-level DEBUG
```

## `generate` — генерация README

Предпочтительно через `just`:

```bash
just build
```

Или напрямую:

```bash
uv run --frozen steinschliff generate --sort temperature
```

## `export-json` / `export-csv`

```bash
just export-json
just export-csv
```

Или напрямую:

```bash
uv run --frozen steinschliff export-json
uv run --frozen steinschliff export-csv --output structures.csv
```

## `list` — список структур

```bash
uv run --frozen steinschliff list
uv run --frozen steinschliff list --service "Fischer"
uv run --frozen steinschliff list --condition "blue"
uv run --frozen steinschliff list --service "Fischer" --condition "blue"
```
