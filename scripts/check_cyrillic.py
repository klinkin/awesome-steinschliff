import os
import re
import sys
from pathlib import Path

# Предкомпилированный паттерн для быстрого поиска кириллицы
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")

# Разрешённые верхнеуровневые директории для проверки
ALLOWED_TOP_DIRS: tuple[str, ...] = ("schliffs",)


def contains_cyrillic(text: str) -> bool:
    """Проверяет, содержит ли строка символы кириллицы.

    Args:
        text: Входная строка для проверки.

    Returns:
        True, если найдены символы кириллицы; иначе False.
    """
    return bool(CYRILLIC_RE.search(text))


def check_yaml_file(repo_root: Path, abs_path: Path) -> list[str]:
    """Проверяет YAML-файл на наличие кириллицы в полях name и similars.

    Args:
        repo_root: Корень репозитория (для формирования относительных путей в отчетах).
        abs_path: Абсолютный путь к YAML-файлу.

    Returns:
        Список сообщений о нарушениях. Каждое сообщение — одна строка.
    """
    violations: list[str] = []
    rel_path = abs_path.relative_to(repo_root).as_posix()

    # Проверка пути файла и поддиректорий
    if contains_cyrillic(rel_path):
        violations.append(f"Cyrillic in file path: {rel_path}")

    # Лёгкий парсер без внешних зависимостей
    name_re = re.compile(r"^name:\s*(.+)")
    similars_start_re = re.compile(r"^similars:\s*$")
    similars_item_re = re.compile(r"^\s*-\s*(.+)")

    try:
        with abs_path.open(encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return violations

    in_similars = False
    for line_no, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        m_name = name_re.match(line)
        if m_name:
            value = m_name.group(1) or ""
            if contains_cyrillic(value):
                violations.append(f"{rel_path}:{line_no}: Cyrillic found in name field")
            in_similars = False
            continue

        if similars_start_re.match(line):
            in_similars = True
            continue

        if in_similars:
            if line.startswith(" ") or line.startswith("\t"):
                m_item = similars_item_re.match(line)
                if m_item and contains_cyrillic(m_item.group(1) or ""):
                    violations.append(f"{rel_path}:{line_no}: Cyrillic found in similars item")
            else:
                in_similars = False

    return violations


def iter_yaml_files(repo_root: Path) -> list[Path]:
    """Возвращает список YAML-файлов из разрешённых директорий.

    Args:
        repo_root: Корень репозитория.

    Returns:
        Список абсолютных путей к YAML-файлам.
    """
    results: list[Path] = []
    for top in ALLOWED_TOP_DIRS:
        top_dir = repo_root / top
        if not top_dir.exists():
            continue
        for root, _dirs, files in os.walk(top_dir):
            for fname in files:
                if fname.endswith(".yaml"):
                    results.append(Path(root) / fname)
    return results


def main() -> int:
    """Точка входа pre-commit-проверки на кириллицу.

    - Запрещает кириллицу в путях файлов внутри ``schliffs``.
    - Запрещает кириллицу в полях ``name`` и элементах списка ``similars`` YAML-файлов.

    Returns:
        Код возврата совместимый с pre-commit: 0 — всё хорошо, 1 — есть нарушения.
    """
    repo_root = Path(__file__).resolve().parent.parent
    all_violations: list[str] = []

    for abs_path in iter_yaml_files(repo_root):
        all_violations.extend(check_yaml_file(repo_root, abs_path))

    if all_violations:
        sys.stderr.write("Pre-commit: Cyrillic usage is not allowed in file names and YAML name/similars.\n")
        for item in all_violations:
            sys.stderr.write(f" - {item}\n")
        return 1

    # Дружественный вывод об успешной проверке для pre-commit
    sys.stdout.write("check-cyrillic: OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
