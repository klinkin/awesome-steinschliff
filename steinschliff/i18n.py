"""Интернационализация (i18n) проекта Steinschliff через Babel.

Модуль содержит:
- загрузку переводов для Jinja2
- утилиты для извлечения/инициализации/обновления/компиляции переводов через `pybabel`
"""

import glob
import logging
import subprocess
from gettext import NullTranslations

from babel.support import Translations

from steinschliff.ui.rich import print_kv_panel

from .paths import project_root
from .paths import templates_dir as package_templates_dir
from .paths import translations_dir as package_translations_dir

logger = logging.getLogger(__name__)


def get_translation_directory() -> str:
    """Получить директорию с переводами.

    Returns:
        Абсолютный путь к директории с переводами.
    """
    return str(package_translations_dir())


def load_translations(locale: str) -> Translations | NullTranslations:
    """Загрузить переводы для указанной локали.

    Args:
        locale: Код локали (например, `"ru"` или `"en"`).

    Returns:
        Объект `Translations` (или пустые переводы при ошибке загрузки).
    """
    translations_dir = get_translation_directory()

    try:
        translations = Translations.load(translations_dir, [locale])
        print_kv_panel("Переводы", [("Локаль", locale), ("Статус", "загружены")], border_style="magenta")
        return translations
    except OSError as e:
        print_kv_panel(
            "Переводы",
            [("Локаль", locale), ("Статус", "не загружены"), ("Ошибка", str(e))],
            border_style="red",
        )
        # Возвращаем пустые переводы корректного типа
        return Translations()


def extract_messages() -> None:
    """Извлечь сообщения для перевода (через `pybabel extract`).

    Использует `subprocess.run` и логирует ошибки/предупреждения.
    """
    try:
        # Определяем пути
        templates_dir = package_templates_dir()
        babel_cfg = project_root() / "babel.cfg"
        output_pot = project_root() / "messages.pot"

        # Находим все шаблоны .jinja2
        templates = glob.glob(str(templates_dir / "*.jinja2"))
        if not templates:
            logger.error("Не найдены шаблоны в директории %s", templates_dir)
            return

        logger.info("Найдено %d шаблонов в %s", len(templates), templates_dir)

        # Запускаем pybabel через subprocess, явно указывая пути к шаблонам
        cmd = [
            "pybabel",
            "extract",
            "-F",
            str(babel_cfg),
            "-k",
            "gettext",
            "-k",
            "_",
            "-o",
            str(output_pot),
        ]
        cmd.extend(templates)  # Добавляем пути ко всем шаблонам

        logger.info("Выполнение команды: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            text=True,
        )

        if result.returncode != 0:
            logger.error("Ошибка извлечения сообщений: %s", result.stderr)
        else:
            logger.info("Сообщения успешно извлечены в %s", output_pot)

            # Проверка, что файл не пустой
            with open(output_pot, encoding="utf-8") as f:
                content = f.read()

            if "msgid" not in content or len(content.strip()) < 50:
                logger.warning("Файл messages.pot пустой или содержит мало строк.")
                logger.debug("Содержимое файла: %s", content[:200])

    except (subprocess.SubprocessError, OSError) as e:
        logger.error("Ошибка при извлечении сообщений: %s", e)


def init_locale(locale: str) -> None:
    """Инициализировать новую локаль (через `pybabel init`).

    Args:
        locale: Код локали (например, `"ru"` или `"en"`).
    """
    try:
        result = subprocess.run(
            ["pybabel", "init", "-i", "messages.pot", "-d", get_translation_directory(), "-l", locale],
            capture_output=True,
            check=False,
            text=True,
        )

        if result.returncode != 0:
            logger.error("Ошибка инициализации локали %s: %s", locale, result.stderr)
        else:
            logger.info("Локаль %s успешно инициализирована", locale)

    except (subprocess.SubprocessError, OSError) as e:
        logger.error("Ошибка при инициализации локали %s: %s", locale, e)


def update_locale(locale: str) -> None:
    """Обновить существующую локаль (через `pybabel update`).

    Args:
        locale: Код локали (например, `"ru"` или `"en"`).
    """
    try:
        result = subprocess.run(
            ["pybabel", "update", "-i", "messages.pot", "-d", get_translation_directory(), "-l", locale],
            capture_output=True,
            check=False,
            text=True,
        )

        if result.returncode != 0:
            logger.error("Ошибка обновления локали %s: %s", locale, result.stderr)
        else:
            logger.info("Локаль %s успешно обновлена", locale)

    except (subprocess.SubprocessError, OSError) as e:
        logger.error("Ошибка при обновлении локали %s: %s", locale, e)


def compile_translations() -> None:
    """Скомпилировать все переводы (через `pybabel compile`)."""
    try:
        result = subprocess.run(
            ["pybabel", "compile", "-d", get_translation_directory()],
            capture_output=True,
            check=False,
            text=True,
        )

        if result.returncode != 0:
            logger.error("Ошибка компиляции переводов: %s", result.stderr)
        else:
            logger.info("Переводы успешно скомпилированы")

    except (subprocess.SubprocessError, OSError) as e:
        logger.error("Ошибка при компиляции переводов: %s", e)
