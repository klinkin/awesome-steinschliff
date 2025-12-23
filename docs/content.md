# Контент: структуры и snow conditions

Документ описывает формат данных и правила добавления/редактирования структур.

## Структура директорий

- `schliffs/` — YAML-файлы структур, сгруппированные по сервисам/производителям
  - `schliffs/<service>/_meta.yaml` — метаданные сервиса (обязательно для нового сервиса)
  - `schliffs/<service>/<structure>.yaml` — описание структуры
  - `schliffs/<service>/<structure>/` — изображения структуры (опционально)
- `snow_conditions/` — справочник snow conditions (`blue.yaml`, `red.yaml`, …)

## Правила добавления/редактирования структур

1. **Файл структуры**: `schliffs/<service>/<NAME>.yaml`.
2. **Новый сервис**: добавьте `schliffs/<service>/_meta.yaml`.
3. **Проверки перед PR**: `just check` (или минимум `just format && just lint && just test`), затем `just build`.

## Именование файлов и папок

### Папка сервиса

- Папка сервиса — это `schliffs/<service>/`. Это ключ, по которому структура группируется в README.
- Для **новых** сервисов рекомендуется использовать **ASCII** и простой формат: `kebab-case` или `lowercase` без пробелов
  (например, `my-service`, `fischer26`).
- В репозитории есть исторические исключения (например, папка с пробелом), но лучше так не делать в новых данных.

### Файл структуры

- Имя файла структуры: `schliffs/<service>/<NAME>.yaml`.
- Рекомендуем, чтобы `<NAME>` совпадал со значением поля `name` (с учётом регистра), например: `W28.yaml` и `name: W28`.
- Допустимы числовые имена (`729.yaml` и `name: 729`).

### Ограничения на кириллицу

В pre-commit включена проверка `check-cyrillic`:

- запрещает **кириллицу в путях файлов** внутри `schliffs/`
- запрещает **кириллицу в полях `name`** и элементах списка **`similars`**

## Схема YAML структуры (основное)

Поддерживаемые поля см. в `steinschliff/models.py`. Минимально полезный набор:

```yaml
---
name: AW7
description_ru: "описание структуры"
snow_type:
  - coarse
  - wet
temperature:
  - min: -5
    max: 5
condition: red
tags:
  - крупнозернистый
similars:
  - S13-5
features:
  - накатка для водянистого снега
service:
  name: ekiptime
```

Замечания:

- **Температура**: используется первый диапазон из `temperature`.
- **similars**: список имён структур (значения поля `name`), по которым строятся ссылки.
- **extra-поля**: допускаются и не ломают генерацию (pydantic `extra=allow`).

## `similars`: как ссылаться на похожие структуры

Формат: список **имён структур** (то есть значений `name`), без путей:

```yaml
similars:
  - SV100
  - B2211
  - 729
```

Как это работает:

- при генерации README проект строит индекс `name -> file_path` и превращает элементы `similars` в Markdown-ссылки
- если имя не найдено — элемент останется обычным текстом

Рекомендация:

- старайтесь держать `name` **уникальным по всему репозиторию**, иначе ссылка может стать неоднозначной

## `images`: как добавлять изображения

Поле `images` — список путей к изображениям (строки).
Пути обычно указываются **от корня репозитория**, например:

```yaml
images:
  - schliffs/skipole/W28/skipole_w28.jpeg
  - schliffs/skipole/W28/skipole_w28_1.jpeg
```

Где хранить файлы:

- рекомендуется складывать изображения в папку рядом со структурой:
  `schliffs/<service>/<NAME>/...`

Важно:

- в таблице README используется **только первое изображение** из списка `images`

## `snow_type`: словарь значений (рекомендуемый)

Поле `snow_type` — это список строк (или строка). Жёсткой схемы-энума сейчас нет, поэтому важно держать единый словарь.

Значения, которые уже используются в репозитории:

- `all`
- `artificial`
- `classic`
- `coarse`
- `cold`
- `damp`
- `dirty`
- `dry`
- `extreme_humidity`
- `extremely_cold`
- `falling`
- `fine`
- `fine_grained`
- `fresh`
- `frozen`
- `glazed`
- `groomed`
- `hard`
- `high_humidity`
- `icy`
- `natural`
- `new`
- `old`
- `rain`
- `refrozen`
- `scandinavian`
- `slightly_transformed`
- `spring`
- `thawed`
- `transformed`
- `universal`
- `used`
- `warm`
- `water`
- `watery`
- `wet`

## Метаданные сервиса `_meta.yaml`

Пример:

```yaml
---
name: Ekiptime
description_ru: Структуры для беговых лыж от компании Ekiptime
website_url: https://ekiptime.ru/services/base_tuning.php
country: Россия
city: Москва
contact:
  phones:
    - "+74997043525"
  address: Москва, стадион Динамо
```

## Snow conditions

Справочник лежит в `snow_conditions/*.yaml`.
Ключ `condition` в структуре должен соответствовать одному из файлов (например, `blue`, `red`, `green`, …).


