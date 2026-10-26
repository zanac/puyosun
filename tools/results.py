"""The results screen after the last game (VS, SCORE, CLEAR TIME, MAX
chains, CONTINUE): one 8bpp picture, set 234 (compressed). 'MAX' is
followed by the kanji 'rensa' (chain); they become CHAIN, in the letters
of the picture itself (C, A, I, N), with an H made of the U and the bar
of the A.
"""
from gfx import SpriteSet

RESULTS_SET = 0xa885b0
# letter cells (8x14) in the picture: x, y of the top left
CELL = {'C': (136, 109), 'A': (160, 109), 'I': (192, 109), 'N': (152, 189), 'U': (184, 189)}
ROW_Y = 149                  # the MAX line
KANJI = (160, 145, 200, 166)  # cleared
CHAIN_X = 163


def build(reg, room):
    ss = SpriteSet(reg, RESULTS_SET, room=room, bpp=8)
    w, h, px = ss.get(0)

    def cell(x0, y0):
        return [px[(y0 + y) * w + x0:(y0 + y) * w + x0 + 8] for y in range(14)]
    letters = {k: cell(*v) for k, v in CELL.items()}
    u, a, n = letters['U'], letters['A'], letters['N']
    letters['H'] = u[0:6] + a[7:9] + u[6:10] + n[12:14]
    out = list(px)
    x0, y0, x1, y1 = KANJI
    for y in range(y0, y1):
        for x in range(x0, x1):
            out[y * w + x] = 0
    for i, ch in enumerate('CHAIN'):
        for y, row in enumerate(letters[ch]):
            for x, v in enumerate(row):
                out[(ROW_Y + y) * w + CHAIN_X + 8 * i + x] = v
    ss.put(0, out)
    ss.write()
    return ['results screen: MAX CHAIN']
