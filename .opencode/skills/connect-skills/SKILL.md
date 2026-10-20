---
name: connect-skills
description: Use when creating, connecting, or debugging opencode skills and SKILL.md files. Covers SKILL.md layout, frontmatter, project vs global scope, and activation.
---

# Connect Skills

Как подключать скилы в opencode для этого проекта.

## Где лежат скилы

| Scope | Path |
| ----- | ---- |
| Project | `.opencode/skills/<name>/SKILL.md` |
| Global | `~/.config/opencode/skills/<name>/SKILL.md` |

Имя папки = `name` из frontmatter, строго lowercase через дефис, до 64 символов.
Файл называется ровно `SKILL.md` и лежит в своей папке:

```text
.opencode/skills/my-skill/SKILL.md
```

Лоадер ищет `**/SKILL.md` внутри skill-директорий. Нестандартные пути регистрируются через `skills.paths` в `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": [".opencode/skills"]
  }
}
```

## Минимальный SKILL.md

```markdown
---
name: my-skill
description: Use when <что делает> and <когда срабатывать>. Front-load keywords.
---

# My Skill

Инструкции, примеры, ссылки.
```

Правила:

- `name` обязателен, совпадает с именем папки.
- `description` фактически обязателен: без него скилл отфильтровывается и модели не виден. Пиши от третьего лица, в начале — триггерные слова, которые скажет пользователь. Для узкого скилла начни с `Use ONLY when...`.
- Опционально: `license`, `compatibility`, `metadata` (map string-string).
- Тело — markdown: инструкции, примеры, ссылки на скрипты относительно папки скилла.

## Как подключить новый скилл

1. Создай папку `.opencode/skills/<name>/`.
2. Положи туда `SKILL.md` с корректным frontmatter.
3. Не ломай `$schema` и существующие поля в `opencode.json`, если правишь его.
4. Перезапусти opencode: конфиг и скиллы читаются один раз на старте, hot-reload нет.

## Проверка

- Скилл виден в списке скиллов после рестарта.
- Триггерная фраза из `description` активирует его.
- Если не подхватился: проверь имя файла (`SKILL.md` заглавными), совпадение `name` с папкой, наличие `description`, запуск из корня проекта.
- Сломанный `opencode.json` чинится через `OPENCODE_DISABLE_PROJECT_CONFIG=1` (старт только с глобального конфига), правка, рестарт без флага.

## Пример для этого репозитория

Триггер: `подключи скилл`, `создай SKILL.md`, `не видит скилл`.
Действие: положи файл в `.opencode/skills/<name>/SKILL.md`, сверься с этим документом, перезапусти opencode из корня проекта.
