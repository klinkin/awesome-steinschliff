from unittest.mock import patch

from steinschliff.i18n import get_translation_directory, load_translations


def test_get_translation_directory_returns_absolute_path():
    path = get_translation_directory()
    assert path and path.startswith("/")


def test_load_translations_success(monkeypatch):
    class DummyTranslations:
        def gettext(self, s):
            return s

    with patch("steinschliff.i18n.Translations.load") as mocked:
        mocked.return_value = DummyTranslations()
        tr = load_translations("ru")
        assert hasattr(tr, "gettext")


def test_load_translations_fallback_oserror(monkeypatch):
    with patch("steinschliff.i18n.Translations.load", side_effect=OSError("boom")):
        tr = load_translations("xx")
        # Возвращаем объект, совместимый с Translations
        assert hasattr(tr, "gettext")
