from pathlib import Path
from unittest.mock import patch

from steinschliff.i18n import compile_translations, extract_messages, init_locale, update_locale


def test_extract_messages_success():
    # Мы не будем реально создавать шаблоны, замокаем subprocess.run и Path.glob/read_text
    with (
        patch("pathlib.Path.glob") as glob_mock,
        patch("pathlib.Path.read_text") as read_text_mock,
        patch("subprocess.run") as run_mock,
    ):
        glob_mock.return_value = [Path("/tmp/a.jinja2"), Path("/tmp/b.jinja2")]
        run_mock.return_value.returncode = 0

        # Имитируем создание непустого messages.pot чтением
        read_text_mock.return_value = 'msgid "x"\nmsgstr ""'
        extract_messages()


def test_extract_messages_failure():
    with patch("pathlib.Path.glob", return_value=[Path("/tmp/a.jinja2")]), patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 1
        extract_messages()


def test_init_update_compile_success():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        init_locale("ru")
        update_locale("ru")
        compile_translations()
