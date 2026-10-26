# Puyo Puyo Sun English (Sega ST-V)

An English translation of the ST-V arcade game *Puyo Puyo Sun* (Compile,
1996, MAME set `puyosun`), as a bootleg clone set `puyosune` for
[mame2003-plus](https://github.com/zanac/mame2003-plus-libretro)
(branch `stv-puyosun-english`).

The Windows version of the game has an English translation patch made by
the [Puyo Nexus](https://www.puyonexus.net) community. This project takes
the English text, font and pictures of that patch and puts them into the
arcade cartridge. The arcade parts the PC patch does not cover (the rules
demonstration, the ranking labels, the side tags) are translated here in
the same style.

All the translation work in the story scenes and the win quotes is from
the Puyo Nexus patch; credit for it goes to its authors.

## Status

| Part | State |
|---|---|
| Win quotes (after each match) | English, checked in the emulator |
| Story scenes, 24 | English, checked in the emulator (samples) |
| Game select, character select, practice balloon | English, checked in the emulator |
| Map screen: plaque, character names | English, checked in the emulator |
| In-game: chain tag, YEAH!/OH NO!, All Clear!, Offset, curry labels | English (PC patch pictures), checked in the emulator |
| Side tags: WINS, JOIN OK, COME ON, RIVAL, NO ENTRY | English, checked in the emulator |
| Ranking: difficulty labels, CHAIN | English, checked in the emulator |
| Rules demonstration (attract mode) | English, checked in the emulator |
| Score tally: character names, Total | English (PC patch picture), not yet seen in the emulator |
| ROM set `puyosune`, build script, driver entry | done |

Left in Japanese:

- the "Act Against AIDS" charity screen of the attract mode;
- the ending and staff roll pictures (not reached in testing);
- the name entry screen (not seen in testing).

The story texts use a proportional font: a small patch in the text
engine advances each character by its width from a table, instead of a
fixed step. Page timings were measured per scene, so the English pages
stay on screen as long as the Japanese ones and follow the animation.

## Screenshots

Japanese arcade original on the left, `puyosune` on the right.

| | |
|---|---|
| Game select | ![game select](screenshots/game_select.png) |
| Character select | ![character select](screenshots/character_select.png) |
| Map | ![map](screenshots/map.png) |
| Story scene | ![story](screenshots/story.png) |

`puyosune` only:

| | |
|---|---|
| All Clear! | ![all clear](screenshots/all_clear.png) |
| Win quote | ![win quote](screenshots/win_quote.png) |
| YEAH! / OH NO! | ![yeah](screenshots/yeah.png) |
| Rules demonstration | ![rules](screenshots/rules.png) |
| Ranking | ![ranking](screenshots/ranking.png) |

## Building the ROM set

You need:

- the MAME `puyosun` set (`puyosun.zip`, the 9 ROMs below are checked by
  CRC);
- the Puyo Nexus English patch of the Windows version as it is
  distributed (`Puyo_Puyo_Sun__English_Patched_.zip`, which contains
  `puyo3/grp.dat` and `puyo3/comic.scr`);
- Python 3 (standard library only).

```
cd tools
python3 make_puyosune.py puyosun.zip Puyo_Puyo_Sun__English_Patched_.zip OUT_DIR
```

`OUT_DIR/puyosune.zip` is the whole set (the three new ROMs and the
unchanged mask ROMs). Put it next to `puyosun.zip` and `stvbios.zip` in
the mame2003-plus ROM folder.

Expected output:

| File | Size | CRC32 | SHA1 |
|---|---|---|---|
| pse19531.13 | 0x080000 | 7d482532 | bd9fbe308ff1c8360bbf63a32bd3402d38c6a63f |
| pse19533.2 | 0x400000 | b7bbaf62 | 87ebc2016ec0b8317fb35ca17bbb3169464942fc |
| pse19534.3 | 0x400000 | 981689c9 | 2f26468eee0c9d4b571dea802d86af447a3d1639 |

Unchanged from `puyosun`: mpr19532.1, mpr19535.4, mpr19536.5,
mpr19537.6, mpr19538.8, mpr19539.9.

## How it works

The tools in `tools/`:

| File | Purpose |
|---|---|
| `make_puyosune.py` | release script: checks the inputs, builds, writes the set |
| `build.py` | the whole build; program decompression and recompression, font, width table, text engine patch |
| `cmpdec.py`, `cmpenc.py` | the LZ format of the program and of the compressed sprite sets |
| `grpdat.py` | reader of the PC `grp.dat` pictures |
| `gfx.py` | sprite sets of the cartridge, drawing English lettering into them |
| `quotes.py` | win quotes |
| `story.py`, `windows.py` | story scenes: PC pages matched to the arcade events, page timings |
| `tutorial.py` | rules demonstration texts |
| `menus.py`, `screens.py` | menus, cabinets, character names, map |
| `ingame.py` | in-game pictures from the PC patch and side tags |
| `ranking.py` | ranking labels |
| `dlgchars.py` | dialogue font codes |

The program is stored compressed in the EPROM and unpacked to work RAM
at boot; it is unpacked, patched and packed again. The arcade sprite sets
match the PC `grp.dat` pictures one to one (set k is PC entry k−1, same
colour numbers), so the PC patch pictures go in directly; sets are
rewritten in place.
