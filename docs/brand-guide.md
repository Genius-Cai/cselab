# cselab Brand Guide

> Single source of truth for visual identity. All code references `src/cselab/theme.py`.

## Mascot: Zap

16x16 pixel art bug. Expressive, minimal, recognizable at tiny sizes.

**Default color**: Teal (#4ecdc4)

**Why teal**: Sits between green (success) and cyan (info) — both core terminal semantics. Pops on dark backgrounds without clashing with red (error) or yellow (warning).

### Seasonal Variants

Drop PNGs into `~/.config/cselab/mascots/` to override:

```
~/.config/cselab/mascots/
├── default.png          # permanent override
├── christmas.png        # Dec 15–31
├── lunar-new-year.png   # Jan 20–Feb 15
├── halloween.png        # Oct 25–31
├── valentines.png       # Feb 13–15
└── mid-autumn.png       # Sep 10–20
```

Auto-detected by date. User overrides take priority over bundled default.

### Terminal Rendering

Zap renders inline via:
- **iTerm2 protocol**: `\033]1337;File=inline=1;...`
- **Kitty/Ghostty protocol**: `\033_Ga=T,f=100,...\033\\`

Falls back gracefully to text-only banner when terminal doesn't support images.

---

## Color Palette

### ANSI (print output)

| Role | ANSI Code | Constant | Usage |
|------|-----------|----------|-------|
| Primary | `\033[36m` | `TEAL` | Brand name, primary accent |
| Success | `\033[32m` | `GREEN` | Connected, OK, pass |
| Error | `\033[31m` | `RED` | Failed, disconnected |
| Warning | `\033[33m` | `YELLOW` | Command echo |
| Accent | `\033[35m` | `MAGENTA` | Separators |
| Secondary | `\033[90m` | `DIM` | Hints, timestamps, labels |
| Emphasis | `\033[1m` | `BOLD` | Headers, brand name |

### prompt_toolkit (hex, toolbar)

| Role | Hex | Constant | Usage |
|------|-----|----------|-------|
| Toolbar BG | `#1a1a2e` | `TOOLBAR_BG` | Dark navy background |
| Toolbar text | `#8888aa` | `TOOLBAR_FG` | Default toolbar text |
| Connected | `#4ecdc4` | `TOOLBAR_ACCENT` | Teal dot + status |
| Disconnected | `#ff6b6b` | `TOOLBAR_DANGER` | Red dot + status |
| Dim info | `#666688` | `TOOLBAR_DIM` | Sync time, secondary |

---

## Typography

Terminal is monospace. Emphasis through ANSI weight:

- **Brand name**: BOLD + GREEN (`cselab`)
- **Headers**: BOLD only (e.g. `Commands`, `Built-in`, `Tips`)
- **User info**: TEAL (e.g. `z5502277@cse.unsw.edu.au`)
- **Labels/hints**: DIM
- **Errors**: RED
- **Success**: GREEN

---

## Box Drawing

Rounded corners (Unicode), matching Ink's `borderStyle: "round"`:

```
╭──────────────────────────────────╮
│  cselab v0.2.0                   │
│  z5502277@cse.unsw.edu.au        │
│  ~/COMP1521/lab01                │
│  Run CSE commands locally        │
╰──────────────────────────────────╯
```

Characters: `╭ ╮ ╰ ╯ │ ─`

Constants in `theme.py`: `TL TR BL BR V H`

---

## Status Indicators

| Symbol | Meaning | Color |
|--------|---------|-------|
| ● (`\u25cf`) | Connected | Teal |
| ○ (`\u25cb`) | Disconnected | Red |

---

## Prompt

```
> _
```

Green bold. Minimal. No prefix text, no path — that's in the toolbar.

---

## Toolbar Layout

```
 z5502277@cse.unsw.edu.au  ● connected  ~/COMP1521/lab01  sync 0.3s
 ├─ TOOLBAR_FG ──────────┤ ├ ACCENT ──┤ ├─ TOOLBAR_FG ──┤ ├ DIM ──┤
```

Single background (`#1a1a2e`). No separators, no borders. Information density through spacing.

---

## Tone of Voice

- **Concise**: `ok`, `failed`, `Bye.` — not `Successfully connected!`
- **Lowercase**: Status messages are lowercase, not title case
- **No exclamation marks** in status output
- **Dim for secondary**: Timestamps, paths, hints are always `DIM`
- **First-year friendly**: Help text explains everything, errors suggest fixes

---

## File Reference

| File | Role |
|------|------|
| `src/cselab/theme.py` | All color/style constants |
| `src/cselab/mascot.py` | Mascot rendering + seasonal logic |
| `src/cselab/banner.py` | Welcome box with optional mascot |
| `src/cselab/assets/zap-default.png` | Bundled default mascot |
| `~/.config/cselab/mascots/` | User seasonal overrides |
