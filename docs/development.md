## Разработка: workflow через just

Проект исторически использовал `make`, но основной workflow теперь — **через `just`**.
`Makefile` пока оставлен для обратной совместимости.

### Быстрый старт

- **Установка зависимостей**:

```bash
just bootstrap
```

- **Проверки качества**:

```bash
just lint
just test
```

- **Форматирование**:

```bash
just format
```

### Сборка и экспорт

- **Сборка README** (сортировка по умолчанию `temperature`):

```bash
just build
```

- **Сборка README с явной сортировкой**:

```bash
just build name
just build temperature
```

- **Экспорт JSON для webapp**:

```bash
just export-json
```

- **Экспорт CSV**:

```bash
just export-csv
```

### i18n

```bash
just i18n-extract
just i18n-init ru
just i18n-update ru
just i18n-update-all
just i18n-compile
just i18n-list
```

### Webapp (Astro)

```bash
just webapp-install
just webapp-dev
just webapp-build
just webapp-preview
```

### Эквиваленты make → just

- `make lint` → `just lint`
- `make test` → `just test`
- `make format` → `just format`
- `make build SORT=temperature` → `just build temperature`
- `make export-json` → `just export-json`
- `make export-csv` → `just export-csv`
- `make ci` → `just ci`


