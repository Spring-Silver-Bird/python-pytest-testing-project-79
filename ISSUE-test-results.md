# Issue: Результаты тестов —-suite ложно-зелёная, реализация-заглушка

## Окружение
- Дата: 2026-09-23 UTC
- Python: 3.12.3 (.venv)
- pytest: 8.4.2, плагины: requests-mock 1.12.1
- ruff: ok
- Ветка: `main...origin/main`, коммит `a042b85 Add README.md`
- Рабочее дерево: не закоммичены `AGENTS.md, Makefile, page_loader/, pyproject.toml, tests/` и др. (см. `git status`)

## Команда запуска
```bash
poetry run pytest -v
poetry run ruff check page_loader tests
poetry check
```

## Фактический результат (зелёный, но нерепрезентативный)
```
tests/test_placeholder.py::test_package_imports PASSED [100%]
1 passed in 0.01s
All checks passed!   # ruff
All set!             # poetry check
```

`make check` (selfcheck + lint + test) — проходит.

## Проблема
Тесты зелёные только за счёт заглушки `tests/test_placeholder.py`:

```python
def test_package_imports():
    assert page_loader.__version__
```

При этом реальный функционал не реализован:

1. `page_loader/loader.py` — только TODO-docstring, нет `download(url, output_dir) -> str`.
   Нет скачивания HTML, нет каталога `<name>_files/`, нет переписывания `img/script/link` на относительные пути, нет проброса сетевых/HTTP ошибок.
2. `page_loader/names.py` — только TODO-docstring, нет контракта:
   `https://ru.hexlet.io/courses` → `ru-hexlet-io-courses.html`,
   ресурсы → `ru-hexlet-io-courses_files/`,
   файл ресурса → `<dir>-<hash-url><ext>`. Не фильтруются внешние хосты.
3. `page_loader/cli.py` — только TODO-docstring, нет `page-loader [--output <dir>] <url>`, нет печати пути и non-zero exit при ошибке.
4. Фикстуры `tests/fixtures/` не используются тестами:
   `page.html`, `scripts/app.js`, `static/pic.png`, `styles/application.css`.
   В тестах нет `requests-mock` и `tmp_path` — побочные эффекты (сеть/диск) не покрыты, что противоречит цели проекта из `AGENTS.md`.
5. Удалённый чек Хекслета (`.github/workflows/hexlet-check.yml` → `hexlet/project-action`) на каждый push будет проверять реальное поведение и упадёт, локальный `pytest` этого не ловит.

## Что сделать
- [ ] Реализовать `page_loader/names.py` по контракту из `AGENTS.md` (+ unit-тесты).
- [ ] Реализовать `page_loader/loader.py::download`:
  - [ ] fetch HTML + save `<name>.html`
  - [ ] качать только same-host `img/script/link` в `<name>_files/`, внешние URL не трогать
  - [ ] переписать HTML на относительные пути
  - [ ] пробрасывать network/HTTP ошибки вызывающему коду
- [ ] Реализовать `page_loader/cli.py` (`argparse`, `--output`, печать пути, exit != 0 при ошибке).
- [ ] Заменить `test_placeholder.py` реальным suite:
  - [ ] именование (`names.py`)
  - [ ] скачивание страницы + ресурсов через `requests-mock`
  - [ ] запись только в `tmp_path`
  - [ ] ошибки сети/HTTP, отсутствующая директория, CLI-кейсы
- [ ] Прогнать `make check` (poetry check + ruff + pytest) и приложить лог.
- [ ] Закоммитить текущие незакоммиченные файлы, иначе удалённый чек увидит другой код.

## Критерии приёмки
- `poetry run pytest -v` показывает >1 реального теста (names/loader/cli/errors), все green.
- `make lint` и `poetry check` без ошибок.
- Ручной smoke: `page-loader --output /tmp/x https://ru.hexlet.io/courses` создаёт `.html` + `_files/`.
- Push в `origin/main` проходит `hexlet-check`.

---
*Сгенерировано из локального прогона. Для переноса в GitHub: `gh auth login && gh issue create --title "Результаты тестов — suite ложно-зелёная" --body-file ISSUE-test-results.md`*
