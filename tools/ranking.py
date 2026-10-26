"""The ranking (high score) screens: difficulty label and the 'chains' tag
of the MAX column.

Their glyphs are 16x16 cells of the name entry set (236, compressed); the
set also has 8x16 block letters; the English labels are drawn with them,
in the white of the Japanese labels, into the cells of the kana (82-91,
used by these labels only), and the label texts are rewritten for them,
centred where the Japanese was. The two cells of the 'chain' kanji become
a narrow CHAIN.
"""
import struct

from gfx import Canvas, SpriteSet

ENTRY_SET = 0xa89d90
CHAIN_CELLS = (92, 93)

# (text address, English): the labels are centred at x 52 (sprites are
# placed by their centre)
LABELS = [(0x06042c08, 'EASY'), (0x06042c22, 'NORMAL'), (0x06042c3a, 'HARD')]
CENTRE = 52
LABEL_CELLS, LABEL_END = 82, 92
# block letter shades -> the white of the labels (outline 1, body 10, light 13/15)
WHITE = {2: 1, 3: 1, 4: 1, 5: 10, 6: 13, 7: 13, 8: 15, 9: 15, 10: 15}


def read_text(prog, base, addr):
    w = []
    a = addr - base
    while True:
        x = struct.unpack('>H', prog[a:a + 2])[0]
        w.append(x)
        a += 2
        if x == 0xff00:
            return w


def build(reg, prog, base, block, room, place):
    ss = SpriteSet(reg, ENTRY_SET, room=room(ENTRY_SET))
    cell = LABEL_CELLS
    for addr, text in LABELS:
        old = read_text(prog, base, addr)
        assert old[:5] == [0xff0f, 0x0700, 0xff11, 0x10, 0x10] and old[5] == 0xff06, hex(addr)
        n = (8 * len(text) + 15) // 16
        cv = Canvas(16 * n, 16)
        block.draw(cv, text, (16 * n - 8 * len(text)) // 2, 0, WHITE)
        cells = list(range(cell, cell + n))
        cell += n
        assert cell <= LABEL_END
        for k, c in enumerate(cells):
            ss.put(c, [cv.px[y * 16 * n + 16 * k + x] for y in range(16) for x in range(16)])
        w = [0xff0f, 0x0700, 0xff11, 0x10, 0x10, 0xff06, CENTRE - 8 * (n - 1), old[7]] + cells + [0xff00]
        at = place(struct.pack('>%dH' % len(w), *w), 2)
        pat = struct.pack('>I', addr)
        refs = [i for i in range(0, len(prog) - 3, 2) if prog[i:i + 4] == pat]
        assert refs, hex(addr)
        for r in refs:
            prog[r:r + 4] = struct.pack('>I', at)
    # CHAIN in the two cells, block letters 6 pixels apart
    cv = Canvas(40, 16)
    block.draw(cv, 'CHAIN', 0, 0, {})
    narrow = Canvas(32, 16)
    for y in range(16):
        for x in range(32):
            narrow.px[y * 32 + x] = cv.px[y * 40 + x * 40 // 32]
    for k, cell in enumerate(CHAIN_CELLS):
        ss.put(cell, [narrow.px[y * 32 + 16 * k + x] for y in range(16) for x in range(16)])
    ss.write()
    return ['ranking: difficulty labels, CHAIN']
