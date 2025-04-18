"""
Модуль для интернационализации (i18n) в проекте steinschliff с использованием Babel.
"""

import logging
import os
from typing import Any, Dict, Optional

from babel.support import Translations

logger = logging.getLogger(__name__)


def get_translation_directory() -> str:
    """
    Возвращает директорию с переводами.

    Returns:
        Абсолютный путь к директории с переводами.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "translations"))


def load_translations(locale: str) -> Translations:
    """
    Загружает переводы для указанной локали.

    Args:
        locale: Код локали (например, 'ru' или 'en').

    Returns:
        Объект Translations с переводами.
    """
    translations_dir = get_translation_directory()

    try:
        translations = Translations.load(translations_dir, [locale])
        logger.info(f"Загружены переводы для локали {locale}")
        return translations
    except Exception as e:
        logger.warning(f"Не удалось загрузить переводы для локали {locale}: {e}")
        return Translations()


def extract_messages():
    """
    Запускает извлечение сообщений для перевода.
    Использует subprocess для вызова pybabel напрямую.
    """
    import glob
    import os
    import subprocess

    try:
        # Определяем пути
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        babel_cfg = os.path.join(os.path.dirname(os.path.dirname(__file__)), "babel.cfg")
        output_pot = os.path.join(os.path.dirname(os.path.dirname(__file__)), "messages.pot")

        # Находим все шаблоны .jinja2
        templates = glob.glob(os.path.join(templates_dir, "*.jinja2"))
        if not templates:
            logger.error(f"Не найдены шаблоны в директории {templates_dir}")
            return

        logger.info(f"Найдено {len(templates)} шаблонов в {templates_dir}")

        # Запускаем pybabel через subprocess, явно указывая пути к шаблонам
        cmd = ["pybabel", "extract", "-F", babel_cfg, "-k", "gettext", "-k", "_", "-o", output_pot]
        cmd.extend(templates)  # Добавляем пути ко всем шаблонам

        logger.info(f"Выполнение команды: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Ошибка извлечения сообщений: {result.stderr}")
        else:
            logger.info(f"Сообщения успешно извлечены в {output_pot}")

            # Проверка, что файл не пустой
            with open(output_pot, "r", encoding="utf-8") as f:
                content = f.read()

            if "msgid" not in content or len(content.strip()) < 50:
                logger.warning("Файл messages.pot пустой или содержит мало строк.")
                logger.debug(f"Содержимое файла: {content[:200]}")

    except Exception as e:
        logger.error(f"Ошибка при извлечении сообщений: {e}")


def init_locale(locale: str):
    """
    Инициализирует новую локаль.

    Args:
        locale: Код локали (например, 'ru' или 'en').
    """
    import subprocess

    try:
        result = subprocess.run(
            ["pybabel", "init", "-i", "messages.pot", "-d", get_translation_directory(), "-l", locale],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Ошибка инициализации локали {locale}: {result.stderr}")
        else:
            logger.info(f"Локаль {locale} успешно инициализирована")

    except Exception as e:
        logger.error(f"Ошибка при инициализации локали {locale}: {e}")


def update_locale(locale: str):
    """
    Обновляет существующую локаль.

    Args:
        locale: Код локали (например, 'ru' или 'en').
    """
    import subprocess

    try:
        result = subprocess.run(
            ["pybabel", "update", "-i", "messages.pot", "-d", get_translation_directory(), "-l", locale],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Ошибка обновления локали {locale}: {result.stderr}")
        else:
            logger.info(f"Локаль {locale} успешно обновлена")

    except Exception as e:
        logger.error(f"Ошибка при обновлении локали {locale}: {e}")


def compile_translations():
    """
    Компилирует все переводы.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["pybabel", "compile", "-d", get_translation_directory()], capture_output=True, text=True
        )

        if result.returncode != 0:
            logger.error(f"Ошибка компиляции переводов: {result.stderr}")
        else:
            logger.info("Переводы успешно скомпилированы")

    except Exception as e:
        logger.error(f"Ошибка при компиляции переводов: {e}")
