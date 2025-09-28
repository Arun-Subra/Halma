# Halma Game 🎲

A full-featured **Halma board game** implemented in Python with a modern **CustomTkinter** GUI.  
Play against another player, challenge the AI, or analyze past games with move-by-move replay and evaluation.

---

## Features ✨

- 🖼️ Modern GUI with **CustomTkinter**
- 🎨 Customizable **board colors** and **themes** (Light, Dark, System)
- 🤖 **AI opponent** with adjustable difficulty using Minimax + alpha-beta pruning
- 📊 **Game analysis mode** with replay and best-move evaluation
- 👥 **Player management**: add, disable, and view stats
- 💾 **Game persistence**: stores games and moves in a local SQLite database
- 🔄 **Move history navigation** with keyboard shortcuts and buttons

---

## Requirements 📦

- Python 3.9+
- Install dependencies:

```bash
pip install customtkinter CTkMessagebox pillow
```

- Project files needed:
  - `module.py` → Database and helper classes (`DatabaseManager`, `MultiColumnListbox`)
  - `red.png`, `blue.png` → Player piece images
  - `halma.db` → SQLite database (created automatically if missing)

---

## Running the Game ▶️

```bash
python halma.py
```

Opens the GUI window to start playing.

---

## How to Play 🎮

- **Play vs Player**: Two players take turns moving pieces.
- **Play vs AI**: Choose difficulty and first mover.
- **Analyse Game**: Replay saved games and view best-move suggestions.
- **Manage Players**: Add/disable players and view their statistics.
- **Settings**: Adjust board size, color scheme, and theme.

---

## Controls ⌨️

- **Mouse**: Click a piece → click destination square.
- **Enter**: Confirm multi-jump moves.
- **Arrow Keys**:
  - ← / →: Step backward/forward through moves
  - ↑ / ↓: Jump to end/beginning of move history

---

## AI Details 🧠

- Minimax algorithm with alpha-beta pruning.
- Evaluates board positions based on piece advancement.
- Dynamically adjusts move analysis based on difficulty setting.

---

## Project Structure 📂

```
halma/
├── halma.py             # Main game script (HalmaGame class)
├── module.py            # Database and helper classes
├── red.png              # Player 1 piece image
├── blue.png             # Player 2 piece image
└── halma.db             # SQLite database (auto-generated)
```

---

## Future Improvements 🚀

- Network multiplayer
- Stronger AI heuristics
- Customizable pieces and themes
- Enhanced statistics and analytics

---

## License 📝

MIT License – free to use, modify, and distribute.

