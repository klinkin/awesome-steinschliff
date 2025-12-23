from unittest.mock import patch

from steinschliff.i18n import compile_translations, extract_messages, init_locale, update_locale


def test_extract_messages_success():
    # Мы не будем реально создавать шаблоны, замокаем subprocess.run и glob
    with patch("glob.glob") as glob_mock, patch("subprocess.run") as run_mock:
        glob_mock.return_value = ["/tmp/a.jinja2", "/tmp/b.jinja2"]
        run_mock.return_value.returncode = 0

        # Имитируем создание непустого messages.pot чтением
        with patch("builtins.open", create=True) as open_mock:
            open_mock.return_value.__enter__.return_value.read.return_value = 'msgid "x"\nmsgstr ""'
            extract_messages()


def test_extract_messages_failure():
    with patch("glob.glob", return_value=["/tmp/a.jinja2"]), patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 1
        extract_messages()


def test_init_update_compile_success():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        init_locale("ru")
        update_locale("ru")
        compile_translations()
