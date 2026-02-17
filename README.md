# Dungeon Master Roguelike

Теперь проект содержит **Godot-версию**, полноценную ПК-версию на Python и дополнительные сборки:

1. **Godot (рекомендуется для дальнейшей разработки)** - папка `godot/`
2. **PC Desktop (GUI, Python/tkinter)** - `desktop_game.py`
3. **3D Browser** - папка `web/`
4. **CLI** - `game.py`

## Основные правила

- Ты — Game Master кампании.
- В партии ровно 3 героя.
- Каждый раунд: 5 карт (2 события + 3 монстра).
- Разыграть можно только 2 карты.

## 1) Запуск Godot-версии

### Через редактор Godot 4.2+

1. Открой Godot.
2. Нажми **Import**.
3. Выбери файл: `godot/project.godot`.
4. Запусти сцену (Play).

### Что уже реализовано в Godot

- отдельная игровая сцена `godot/scenes/Main.tscn`,
- игровая логика в `godot/scripts/main.gd`,
- правила: 3 героя, рука 5 карт (2 события + 3 монстра), можно сыграть только 2,
- UI карточек, лог боя, hotkeys `1..5` + `Enter`.

## 2) Запуск полноценной ПК-версии (GUI)

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

## 3) Запуск 3D-версии в браузере

```bash
python3 -m http.server 8000
```

Открой:

```text
http://localhost:8000/web/
```

## 4) Запуск CLI-версии

```bash
python3 game.py
```

## Тесты логики

```bash
python3 -m unittest discover -s tests -v
```
