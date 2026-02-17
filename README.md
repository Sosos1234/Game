# Dungeon Master Roguelike

Теперь проект содержит **полноценную ПК-версию с окном приложения** и две дополнительные версии:

1. **PC Desktop (GUI)** - `desktop_game.py` (рекомендуется)
2. **3D Browser** - папка `web/`
3. **CLI** - `game.py`

## Основные правила

- Ты — Game Master кампании.
- В партии ровно 3 героя.
- Каждый раунд: 5 карт (2 события + 3 монстра).
- Разыграть можно только 2 карты.

## 1) Запуск полноценной ПК-версии (GUI)

### Windows (CMD / PowerShell)

```bash
py desktop_game.py
```

### Linux / macOS

```bash
python3 desktop_game.py
```

Что есть в GUI-версии:

- окно игры с карточками и журналом боёв,
- hotkeys: `1..5` выбрать карту, `Enter` сыграть ход,
- сохранение/загрузка кампании (`Ctrl+S` / `Ctrl+O`),
- кнопки New Campaign / Auto-pick / Play.

## 2) Запуск 3D-версии в браузере

```bash
python3 -m http.server 8000
```

Открой:

```text
http://localhost:8000/web/
```

## 3) Запуск CLI-версии

```bash
python3 game.py
```

## Тесты логики

```bash
python3 -m unittest discover -s tests -v
```
