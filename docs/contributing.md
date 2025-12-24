# Вклад в проект (Contributing)

Содержание:

- [Кодекс поведения](#кодекс-поведения)
- [Вопрос или проблема](#вопрос-или-проблема)
- [Баги и фичи](#баги-и-фичи)
- [Pull Request](#pull-request)
- [Конвенция сообщений коммитов](#конвенция-сообщений-коммитов)
- [Слияние Pull Request](#слияние-pull-request)

## Кодекс поведения

Пожалуйста, ознакомьтесь и следуйте: [`CODE_OF_CONDUCT.md`](https://github.com/klinkin/awesome-steinschliff/blob/main/CODE_OF_CONDUCT.md).

## Вопрос или проблема

Для обсуждений и вопросов:

- Telegram: `https://t.me/+wddxUugE0gwxMGU6`
- Тема на skisport.ru: `https://www.skisport.ru/forum/cross-country/104594`

GitHub Issues лучше оставлять для багов и фич-реквестов.

## Баги и фичи

- Баг-репорты: `https://github.com/klinkin/awesome-steinschliff/issues`
- Фич-реквесты: `https://github.com/klinkin/awesome-steinschliff/issues/new/choose`

Для крупных изменений лучше сначала открыть ишью и согласовать дизайн/направление.

## Pull Request

Рекомендации перед PR:

1. Ветка от `main`, PR в `main`.
2. Не дублируйте работу: `https://github.com/klinkin/awesome-steinschliff/pulls`
3. Запустите локальные проверки:

```bash
just check
# или полный набор:
just format
just lint
just test
just build
```

4. При необходимости обновите документацию (`docs/`).

### Ревью и правки

- Внесите правки по замечаниям, повторите проверки, запушьте — PR обновится автоматически.

## Конвенция сообщений коммитов

Используем Conventional Commits (`v1.0.0`). Примеры:

```bash
git commit -m "feat: add new structure attributes"
git commit -m "fix: correct temperature formatting for ranges"
git commit -m "docs: update docs index"
```

## Слияние Pull Request

Предпочтительно `Squash and merge`.
Подробнее: `https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-commits`
