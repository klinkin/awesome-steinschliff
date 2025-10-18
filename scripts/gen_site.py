"""
Генерация Jekyll-сайта (docs/) на основе текущей логики генерации README.

Результат:
- docs/index.md (RU)
- docs/en/index.md (EN)
- docs/_config.yml, docs/_layouts/default.html (минимальные, если отсутствуют)
"""

import argparse
import sys
from pathlib import Path


def ensure_jekyll_scaffold(docs_dir: Path) -> None:
    """Создаёт минимальный скелет Jekyll-сайта, если он отсутствует."""
    docs_dir.mkdir(parents=True, exist_ok=True)

    # _config.yml
    config_path = docs_dir / "_config.yml"
    if not config_path.exists():
        config_path.write_text(
            "\n".join(
                [
                    "title: Steinschliff",
                    "description: Catalog of ski grinding structures",
                    # Без темы по умолчанию, чтобы не требовать установки minima
                    # "theme: minima",
                    "markdown: kramdown",
                    "plugins:",
                    "  - jekyll-seo-tag",
                    "url: https://example.com",
                    "baseurl: ''",
                    "exclude:",
                    "  - vendor",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        # Санитизируем существующий конфиг: убираем зависимость от темы minima
        try:
            content = config_path.read_text(encoding="utf-8").splitlines()
            filtered = [line for line in content if not line.strip().startswith("theme:")]
            if filtered != content:
                config_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")
        except OSError:
            # Игнорируем ошибки чтения/записи конфигурации Jekyll
            return

    # _layouts/default.html
    layouts_dir = docs_dir / "_layouts"
    layouts_dir.mkdir(exist_ok=True)
    default_layout = layouts_dir / "default.html"
    if not default_layout.exists():
        default_layout.write_text(
            (
                "<!DOCTYPE html>\n"
                "<html lang=\"{{ page.lang | default: 'ru' }}\">\n"
                "  <head>\n"
                '    <meta charset="utf-8" />\n'
                '    <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
                "    <title>{{ page.title | default: site.title }}</title>\n"
                "    {%- seo -%}\n"
                "    <link rel=\"stylesheet\" href=\"{{ '/assets/style.css' | relative_url }}\" />\n"
                "  </head>\n"
                "  <body>\n"
                '    <main class="container">{{ content }}</main>\n'
                "  </body>\n"
                "  </html>\n"
            ),
            encoding="utf-8",
        )

    # assets/style.css (минимальный стиль)
    assets_dir = docs_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    style_css = assets_dir / "style.css"
    if not style_css.exists():
        style_css.write_text(
            (
                "body { font-family: -apple-system, system-ui, Segoe UI, Roboto, Ubuntu, "
                "Cantarell, Noto Sans, Arial, 'Apple Color Emoji', 'Segoe UI Emoji';\n"
                "       line-height: 1.6; margin: 0; padding: 0; }\n"
                ".container { max-width: 1100px; margin: 0 auto; padding: 24px; }\n"
                "table { border-collapse: collapse; width: 100%; }\n"
                "th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; }\n"
                "th { background: #f5f5f5; text-align: left; }\n"
                "img { max-width: 240px; height: auto; }\n"
            ),
            encoding="utf-8",
        )
    else:
        # Идемпотентное обновление: удаляем ранее добавленные правила сайдбара, если были
        css = style_css.read_text(encoding="utf-8")
        if ".toc-sidebar" in css or ".layout" in css:
            # Простая очистка: перегенерируем базовый минимальный CSS
            base_css = (
                "body { font-family: -apple-system, system-ui, Segoe UI, Roboto, Ubuntu, "
                "Cantarell, Noto Sans, Arial, 'Apple Color Emoji', 'Segoe UI Emoji';\n"
                "       line-height: 1.6; margin: 0; padding: 0; }\n"
                ".container { max-width: 1100px; margin: 0 auto; padding: 24px; }\n"
                "table { border-collapse: collapse; width: 100%; }\n"
                "th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; }\n"
                "th { background: #f5f5f5; text-align: left; }\n"
                "img { max-width: 240px; height: auto; }\n"
            )
            style_css.write_text(base_css, encoding="utf-8")


def prepend_front_matter(file_path: Path, title: str, lang: str) -> None:
    """Добавляет YAML фронт-маттер в начало Markdown-файла, если его нет."""
    content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
    if content.lstrip().startswith("---\n"):
        return
    fm = "\n".join(
        [
            "---",
            "layout: default",
            f"title: {title}",
            f"lang: {lang}",
            "---",
            "",
        ]
    )
    file_path.write_text(fm + content, encoding="utf-8")


def generate_site(sort_field: str) -> None:
    project_dir = Path(__file__).resolve().parents[1]
    # Импортируем генератор из проекта
    sys.path.insert(0, str(project_dir))
    from steinschliff.generator import ReadmeGenerator  # type: ignore

    docs_dir = project_dir / "docs"
    ensure_jekyll_scaffold(docs_dir)

    # Настраиваем генератор для вывода прямо в docs/
    config = {
        "schliffs_dir": str(project_dir / "schliffs"),
        "readme_file": str(docs_dir / "en" / "index.md"),
        "readme_ru_file": str(docs_dir / "index.md"),
        "sort_field": sort_field,
    }

    # Убедимся, что подкаталог en существует
    (docs_dir / "en").mkdir(parents=True, exist_ok=True)

    generator = ReadmeGenerator(config)
    generator.run()

    # Добавляем фронт-маттер
    prepend_front_matter(docs_dir / "index.md", title="Steinschliff — Каталог структур", lang="ru")
    prepend_front_matter(docs_dir / "en" / "index.md", title="Steinschliff — Structures Catalog", lang="en")


def main() -> None:
    parser = argparse.ArgumentParser(description="Генерация Jekyll-сайта в docs/")
    parser.add_argument(
        "--sort",
        default="name",
        choices=["name", "rating", "country", "temperature"],
        help="Поле для сортировки структур (по умолчанию: name)",
    )
    args = parser.parse_args()

    generate_site(args.sort)


if __name__ == "__main__":
    main()
