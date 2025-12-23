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

В проекте есть `Makefile` с основными командами (запуск идёт через `uv run`, активировать venv вручную не требуется):

```bash
make help                 # список команд
make lint                 # mypy + ruff check + black --check
make format               # форматирование ruff/black + сортировка импортов
make test                 # запустить тесты pytest
make i18n-extract         # извлечь строки перевода из Python/Jinja2
make i18n-init LOCALE=xx  # инициализировать новую локаль (например, LOCALE=de)
make i18n-update LOCALE=xx# обновить существующую локаль
make i18n-update-all      # обновить все локали
make i18n-compile         # скомпилировать переводы (.mo)
make i18n-list            # показать доступные локали
make build                # сгенерировать README.md (параметр SORT=name|snow_type|service|temperature|rating|country)
```

Рекомендации:

- Перед коммитом выполняйте `make format && make lint`.
- Соблюдайте стиль кода (смотри `pyproject.toml`: Black line-length 120, Ruff правила).

## <a name="test"></a> Тестирование

Запуск тестов:

```bash
make test
```

Конфигурация pytest находится в `tests/pytest.ini`.

## <a name="i18n"></a> Локализация (i18n)

Экстракция и обновление переводов управляется через `scripts/manage_translations.py` и `babel.cfg`:

```bash
make i18n-extract                  # собрать сообщения в messages.pot
make i18n-init LOCALE=de           # создать новую локаль
make i18n-update LOCALE=ru         # обновить существующую локаль
make i18n-update-all               # обновить все локали
make i18n-compile                  # скомпилировать .po в .mo
make i18n-list                     # список локалей
```

Jinja2-шаблоны читаются с расширением `i18n`, Python-файлы — напрямую. Конфигурация в `babel.cfg`.

## <a name="readme"></a> Генерация README

Генератор (`steinschliff/generator.py`) собирает YAML-файлы из `schliffs/`, группирует по сервисам/странам и рендерит шаблон Jinja2 в `README.md` и `README_en.md`:

```bash
make build            # генератор (сортировка по температуре по умолчанию)
make build SORT=temperature  # сортировка по максимуму температуры (теплые сверху)
make build SORT=name  # сортировка по имени
make build SORT=rating # сортировка по рейтингу
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
snow_temperature:              # список диапазонов; используется первый элемент
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
snow_temperature:
  - {min: -8, max: 0}
service: {name: Skipole}
country: Russia
```

## <a name="contributing"></a> Правила вкладов

- Перед PR запускайте `make format`, `make lint`, `make test`.
- Следите за корректностью `YAML`: валидные типы, первый диапазон температуры — основной.
- Для новых сервисов добавляйте мета-файл `schliffs/<service>/_meta.yaml` с полями `name`, `country`, `city`, `contact` (см. существующие примеры).
- Коммиты на русском/английском допустимы; будьте конкретны (что и зачем меняете).
