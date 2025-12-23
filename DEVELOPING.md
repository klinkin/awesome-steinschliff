# Руководство по разработке

- [Руководство по разработке](#руководство-по-разработке)
  - [ Получение исходников](#-получение-исходников)
  - [ Подготовка окружения](#-подготовка-окружения)
  - [ Повседневная разработка](#-повседневная-разработка)
  - [ Тестирование](#-тестирование)
  - [ Локализация (i18n)](#-локализация-i18n)
  - [ Генерация README](#-генерация-readme)
  - [ Схема YAML для структур](#-схема-yaml-для-структур)
  - [ Правила вкладов](#-правила-вкладов)

## <a name="get"></a> Получение исходников

1. Клонируйте репозиторий:

```bash
git clone https://github.com/klinkin/awesome-steinschliff.git
cd awesome-steinschliff
```

1. Убедитесь, что у вас установлен Git и доступ к GitHub.

## <a name="setup"></a> Подготовка окружения

Требования:

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) для управления зависимостями и окружением

Установка зависимостей (включая dev-зависимости):

```bash
uv sync --extra dev
```

Полезные инструменты для IDE: Ruff, Black, mypy (конфигурация в `pyproject.toml`).

## <a name="dev"></a> Повседневная разработка

Проект исторически использовал `make`, но основной workflow теперь — **через `just`**.
`Makefile` оставлен для обратной совместимости (как набор алиасов).

```bash
just help                 # список команд
just lint                 # mypy + ruff check + black --check
just format               # форматирование ruff/black + сортировка импортов
just test                 # запустить тесты pytest
just i18n-extract         # извлечь строки перевода из Python/Jinja2
just i18n-init <locale>   # инициализировать новую локаль (например, just i18n-init de)
just i18n-update <locale> # обновить существующую локаль
just i18n-update-all      # обновить все локали
just i18n-compile         # скомпилировать переводы (.mo)
just i18n-list            # показать доступные локали
just build                # сгенерировать README (параметр sort: name|snow_type|service|temperature|rating|country)
```

Рекомендации:

- Перед коммитом выполняйте `just format && just lint`.
- Соблюдайте стиль кода (смотри `pyproject.toml`: Black line-length 120, Ruff правила).

## <a name="test"></a> Тестирование

Запуск тестов:

```bash
just test
```

Конфигурация pytest находится в `tests/pytest.ini`.

## <a name="i18n"></a> Локализация (i18n)

Экстракция и обновление переводов управляется через `scripts/manage_translations.py` и `babel.cfg`:

```bash
just i18n-extract                  # собрать сообщения в messages.pot
just i18n-init de                  # создать новую локаль
just i18n-update ru                # обновить существующую локаль
just i18n-update-all               # обновить все локали
just i18n-compile                  # скомпилировать .po в .mo
just i18n-list                     # список локалей
```

Jinja2-шаблоны читаются с расширением `i18n`, Python-файлы — напрямую. Конфигурация в `babel.cfg`.

## <a name="readme"></a> Генерация README

Генератор (`steinschliff/generator.py`) собирает YAML-файлы из `schliffs/`, группирует по сервисам/странам и рендерит шаблон Jinja2 в `README.md` и `README_en.md`:

```bash
just build                 # генератор (сортировка по температуре по умолчанию)
just build temperature     # сортировка по максимуму температуры (теплые сверху)
just build name            # сортировка по имени
just build rating          # сортировка по рейтингу
```

Шаблоны находятся в `steinschliff/templates/`. Переводы подключаются через `steinschliff/i18n.py`.

## <a name="yaml"></a> Схема YAML для структур

Каждый файл `schliffs/<service>/<NAME>.yaml` описывает одну структуру. Поддерживаемые поля (см. `steinschliff/models.py`):

```yaml
name: RW691                    # строка или число, уникальное имя структуры
description: null              # описание (английский), необязательно
description_ru: "..."          # описание (русский), необязательно
snow_type:                     # список строк (допускаются пустые элементы, будут отфильтрованы)
  - wet
temperature:                   # список диапазонов; используется первый элемент
  - min: -5
    max: 3
condition: ""                  # произвольная строка (необязательно)
manufactory: Rossignol         # производитель/бренд (необязательно)
service:                       # объект сервиса (минимум name)
  name: Rossignol
author: ""                     # автор структуры (необязательно)
country: France                # страна сервиса/бренда (необязательно)
tags:                          # список тегов
  - очень мокрый
  - жесткий снег
similars: []                   # список похожих структур по имени; будут превращены в ссылки
features:                      # особенности; выводятся строкой через запятую
  - ""
images:                        # список путей к изображениям (опционально)
  - path/to/image.jpg
updated_at: 2025-10-01         # метаданные (опционально)
updated_by: https://github.com/klinkin
archived: false
```

Замечания:

- Для температур выводится формат `+3 °C … –5 °C` (теплое → холодное), берется первый диапазон.
- Поле `similars` может содержать имена структур; ссылки формируются автоматически при генерации README.
- Дополнительные поля допускаются и не ломают генерацию (pydantic `extra=allow`).

Минимально достаточный пример:

```yaml
name: X25
description_ru: "структура для свежего и нового натурального снега"
snow_type: [all]
temperature:
  - {min: -8, max: 0}
service: {name: Skipole}
country: Russia
```

## <a name="contributing"></a> Правила вкладов

- Перед PR запускайте `just format`, `just lint`, `just test`.
- Следите за корректностью `YAML`: валидные типы, первый диапазон температуры — основной.
- Для новых сервисов добавляйте мета-файл `schliffs/<service>/_meta.yaml` с полями `name`, `country`, `city`, `contact` (см. существующие примеры).
- Коммиты на русском/английском допустимы; будьте конкретны (что и зачем меняете).
