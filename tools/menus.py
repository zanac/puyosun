"""English lettering of the menu sprites (game select, character select).

Sprite set 180 of the resource table (raw, in mpr19534.3): the screen
titles are rows of 16x16 cells that the text engine puts at fixed places;
the English line is drawn across the same places and cut into the cells.
"""
from gfx import Canvas, SpriteSet

MENU_SET = 0x90b9d4

# title cells: (first entry, screen x of each cell, English per run of cells)
TITLES = [
    (6, [51, 67, 83, 99, 123, 139, 155, 171, 187], ['SELECT', 'A GAME']),
    (15, [27, 43, 59, 75, 91, 107, 123, 147, 163, 179, 195, 211], ['SELECT YOUR', 'FIGHTER']),
]

TITLE_COLOURS = {1: 2, 9: 9, 15: 15}       # outline, AA, body
LABEL_COLOURS = {1: 1, 9: 9, 15: 15}


def runs(xs):
    """cells next to each other: [(first cell, x0, x1)]"""
    out = []
    for i, x in enumerate(xs):
        if out and out[-1][2] == x:
            out[-1][2] = x + 16
        else:
            out.append([i, x, x + 16])
    return out


def title(ss, first, xs, words, font):
    rs = runs(xs)
    assert len(rs) == len(words)
    x0 = xs[0]
    cv = Canvas(xs[-1] + 16 - x0, 16)
    for (i, a, b), word in zip(rs, words):
        track = 0
        while font.width(word, track) > b - a and track > -2:
            track -= 1
        wd = font.width(word, track)
        assert wd <= b - a, (word, wd, b - a)
        # the words meet at the gap between the runs of cells
        pos = a - x0 + (b - a - wd) if i == 0 and len(rs) > 1 else a - x0 if len(rs) > 1 else a - x0 + (b - a - wd) // 2
        font.draw(cv, word, pos, 0, TITLE_COLOURS, track)
    for k, x in enumerate(xs):
        px = []
        for y in range(16):
            px += cv.px[y * cv.w + x - x0:y * cv.w + x - x0 + 16]
        ss.put(first + k, px)


def label(ss, k, text, font, colours, track=0, align='center'):
    """a sprite that is only lettering: replaced by the English text"""
    w, h, old = ss.get(k)
    cv = Canvas(w, h)
    wd = font.width(text, track)
    assert wd <= w, (text, wd, w)
    x = (w - wd) // 2 if align == 'center' else 0
    font.draw(cv, text, x, (h - font.height) // 2, colours, track)
    ss.put(k, cv.px)


def segments(px, w, h, gap=6):
    cols = [any(px[y * w + x] for y in range(h)) for x in range(w)]
    out = []
    x = 0
    while x < w:
        if cols[x]:
            a = x
            while x < w and any(cols[x:x + gap]):
                x += 1
            out.append((a, x))
        x += 1
    return out


def build(reg, pc, block):
    ss = SpriteSet(reg, MENU_SET, compressed=False)
    for first, xs, words in TITLES:
        title(ss, first, xs, words, pc)
    # the controls line: [stick] SELECT   [button] CONFIRM
    w, h, px = ss.get(27)
    seg = segments(px, w, h)
    assert len(seg) == 4, seg
    cv = Canvas(w, h)
    for (a, b), word in ((seg[0], 'SELECT'), (seg[2], 'CONFIRM')):
        pc.draw(cv, word, a, 0, LABEL_COLOURS)
    ss.put(27, cv.px)
    # difficulty and names, 8 pixels per letter
    for k, text in ((76, 'EASY'), (77, 'NORMAL'), (78, 'HARD'),
                    (141, 'DRACO'), (142, 'ARLE'), (143, 'SCHEZO')):
        label(ss, k, text, block, BLOCK_COLOURS)
    practice(ss, pc)
    ss.write()
    log = ['menu sprites: titles, controls, difficulty, names, practice note']
    log += cabinets(reg, block)
    return log


# the two cabinets of the game select (8bpp): text on the screen
CAB_SET = 0x9505d8
CAB_TEXT = [['1 PLAYER', 'PUYO PUYO'], ['2 PLAYER', 'PUYO PUYO']]
CAB_BG = 0x4b
CAB_COLOURS = {2: 0x4c, 3: 0x4c, 4: 0x4d, 5: 0x4e, 6: 0x4e, 7: 0x0f, 8: 0x0f, 9: 0x0f, 10: 0x0f, 11: 0x0f}


def cabinets(reg, block):
    ss = SpriteSet(reg, CAB_SET, compressed=False, bpp=8)
    for k, lines in enumerate(CAB_TEXT):
        w, h, px = ss.get(k)
        cv = Canvas(w, h, px)
        # the screen: the run of background colour on the text rows
        ys = [y for y in range(h) if px[y * w:(y + 1) * w].count(CAB_BG) > 40]
        y0, y1 = ys[0] + 1, ys[-1]
        x0, x1 = w, 0
        for y in range(y0, y1):
            row = px[y * w:(y + 1) * w]
            a, b = row.index(CAB_BG), w - 1 - row[::-1].index(CAB_BG)
            x0, x1 = min(x0, a), max(x1, b)
            for x in range(a, b):
                if cv.px[y * w + x] in (0x0f, 0x4c, 0x4d, 0x4e):
                    cv.px[y * w + x] = CAB_BG
        x0, x1 = x0 + 1, x1
        top = y0 + (y1 - y0 - 32) // 2
        for i, t in enumerate(lines):
            wd = block.width(t)
            assert wd <= x1 - x0, (t, wd, x1 - x0)
            block.draw(cv, t, x0 + (x1 - x0 - wd) // 2, top + 16 * i, CAB_COLOURS)
        ss.put(k, cv.px)
    ss.write()
    return ['cabinets: screen text']


# the block letters are shaded 2 (dark) .. 0xa; in white for the labels
BLOCK_COLOURS = {2: 1, 3: 1, 4: 2, 5: 9, 6: 9, 7: 15, 8: 15, 9: 15, 10: 15, 11: 15}


def practice(ss, pc):
    """the balloon of the practice game: '3 stages and it is over, this is
    the practice mode'"""
    w, h, px = ss.get(79)
    cv = Canvas(w, h, px)
    cv.clear(16, 8, 126, 56, keep=())
    # the dotted inner border is kept: redraw it from the original rows
    for x in range(w):
        for y in (7, 56):
            cv.px[y * w + x] = px[y * w + x]
    lines = [('Practice', {1: 3, 9: 13, 15: 12}),
             ('mode: just', {1: 3, 9: 13, 15: 15}),
             ('3 stages!', {1: 3, 9: 13, 15: 12})]
    for i, (t, col) in enumerate(lines):
        track = 0 if pc.width(t) <= 108 else -1
        wd = pc.width(t, track)
        assert wd <= 108, (t, wd)
        pc.draw(cv, t, 17 + (108 - wd) // 2, 8 + 16 * i, col, track)
    ss.put(79, cv.px)
