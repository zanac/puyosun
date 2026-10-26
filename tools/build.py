"""Build the English Puyo Puyo Sun (ST-V) from the arcade ROMs and the Puyo
Nexus English patch of the Windows version. Python 3 standard library only.

    python3 build.py ARCADE_DIR PC_DIR OUT_DIR

ARCADE_DIR holds epr19531.13 and mpr19533.2 (unzipped puyosun set), PC_DIR
the patched Windows game (puyo3/grp.dat, puyo3/comic.scr). OUT_DIR receives
pse19531.13 and pse19533.2, the new program EPROM and mask ROM 2.
"""
import os
import struct
import sys

import cmpdec
import cmpenc
import grpdat
import aids
import nameentry
import results
import story
import ingame
import ranking
import tutorial
import gfx
import menus
import screens
from quotes import QUOTES

PROG_BASE = 0x06004000      # where the decompressed program runs
PROG_AT = 0x2000            # compressed program in the EPROM
EPROM_SIZE = 0x80000
FREE_AT = 0x73000           # 0xff to the end of the EPROM
EPROM_CPU = 0x22200000      # the EPROM as the SH-2 reads it (cache-through)

# sprite sets of the texts (cartridge region offsets): (offset,
# entries, offset of the next set). The loader takes the size of a set from
# the next entry of the resource table, so they are rewritten in place.
DIALOGUE = (0x411a14, 221, 0x414e4c)      # win quotes: 8x16 0-43, 16x16 44-
STORY = (0x45ffa4, 349, 0x465320)         # scenes: 16x16, balloon from 0x150

# characters: ASCII at their codes, then these two
EXTRA = {'…': 0x7f, '♪': 0x80}
SPACE_W = 6
# dialogue set: 0x20-0x2b are 8x16 letters; their English glyphs go to
# these 16x16 entries (unused kana) and the descriptors are redirected
DIALOGUE_LOW = 0x90

# the win quotes in the program
QUOTE_FIRST = 0x0604cc10
QUOTE_END = 0x0604de32
TEXT_X, TEXT_Y = 0x2e, 0x98


def word_swap(b):
    out = bytearray(len(b))
    out[0::2] = b[1::2]
    out[1::2] = b[0::2]
    return bytes(out)


def be16(b, a):
    return struct.unpack('>H', b[a:a + 2])[0]


def be32(b, a):
    return struct.unpack('>I', b[a:a + 4])[0]


def code(ch):
    return EXTRA[ch] if ch in EXTRA else ord(ch)


# --- font ------------------------------------------------------------------

PC_COLOURS = {0: 0, 1: 1, 12: 9, 15: 15}


def pc_font(grp):
    """{code: (advance, 16x16 cell of colour indices)} from the font of the
    PC patch (grp.dat entry 21, ASCII order; 30 is the ellipsis)"""
    ents = grpdat.entries(grp)
    o, s = ents[21]
    d = grp[o:o + s]
    t, frames, parts, base = grpdat.parse(d)
    out = {}
    for k in list(range(0x21, 0x7f)) + [30]:
        pw, ph, px, py, a, fl, off = parts[k]
        src = d[base + off:base + off + pw * ph]
        cell = [0] * 256
        for y in range(ph):
            for x in range(pw):
                if px + x < 16 and py + y < 16:
                    cell[(py + y) * 16 + px + x] = PC_COLOURS[src[y * pw + x]]
        out[EXTRA['…'] if k == 30 else k] = (pw, cell)
    # the note: only in the quote pictures (entry 1, quote 74, end of line 1)
    o, s = ents[1]
    w, h, px = grpdat.sprites(grp[o:o + s])[74]
    cell = [0] * 256
    for y in range(16):
        for x in range(11):
            cell[y * 16 + 1 + x] = PC_COLOURS[px[y * w + 185 + x]]
    out[EXTRA['♪']] = (11, cell)
    out[0x20] = (SPACE_W, [0] * 256)
    return out


def pack4(cell):
    return bytes((cell[i] << 4) | cell[i + 1] for i in range(0, 256, 2))


def build_set(reg, where, font, redirect):
    """a sprite set with the English glyphs; redirect = {code: entry}
    for codes whose entry is not 16x16 (the glyph goes to that entry)"""
    at, count, nxt = where
    assert be16(reg, at) == count
    desc = bytearray(reg[at + 4:at + 4 + count * 8])
    pix, end = cmpdec.decompress(reg, at + 4 + count * 8)
    pix = bytearray(pix)
    for c, (adv, cell) in font.items():
        e = redirect.get(c, c)
        w, h, off, size = struct.unpack('>4H', desc[e * 8:e * 8 + 8])
        assert (w, h, size) == (16, 16, 0x0210), (hex(c), hex(e))
        pix[off * 8:off * 8 + 128] = pack4(cell)
        if e != c:
            desc[c * 8:c * 8 + 8] = desc[e * 8:e * 8 + 8]
    blob = reg[at:at + 4] + desc + cmpenc.compress(bytes(pix))
    assert len(blob) <= nxt - at, 'sprite set too big (%x > %x)' % (len(blob), nxt - at)
    return blob + bytes(nxt - at - len(blob))


# --- texts -------------------------------------------------------------------

def encode(text, font):
    w = [0xff0f, 0x0500 | story.PROP,   # clear flags 5, set proportional
         0xff11, 0x0000, 0x0018,        # spacing: x from the glyphs, 24 per line
         0xff06, TEXT_X, TEXT_Y]
    for k, line in enumerate(text.split('/')):
        if k:
            w.append(0xff02)
        width = 0
        for ch in line:
            w.append(code(ch))
            width += font[code(ch)][0]
        assert width <= 244, 'line too wide: %r (%d)' % (line, width)
    w.append(0xff00)
    return struct.pack('>%dH' % len(w), *w)


def quote_starts(prog):
    a = QUOTE_FIRST - PROG_BASE
    out = []
    while a < QUOTE_END - PROG_BASE:
        assert prog[a:a + 4] == b'\xff\x0f\x05\x00'
        out.append(a)
        while be16(prog, a) != 0xff00:
            a += 2
        a += 2
    return out


def find_pointers(prog, value):
    pat = struct.pack('>I', value)
    return [i for i in range(0, len(prog) - 3, 2) if prog[i:i + 4] == pat]


# --- code --------------------------------------------------------------------

def asm(*words):
    return struct.pack('>%dH' % len(words), *words)


def patch_code(prog, widths_cpu):
    """text engine (0x060140ea-0x06014146): with flag 0x40 the x advance of
    a character is widths[code], otherwise as in the arcade. The glyph table
    load for zero spacing is the original one, only shorter."""
    a = 0x060140ea - PROG_BASE
    old = prog[a:0x06014146 - PROG_BASE]
    assert old[:4] == bytes.fromhex('63822338') and old[-8:] == bytes.fromhex('638251e8313c1e18')
    code = asm(
        # 060140ea: spacing 0,0 -> from the glyph table (w, h of this char)
        0x6382,     # mov.l @r8,r3
        0x2338,     # tst r3,r3
        0x8b12,     # bf 0x06014116
        0x63f2,     # mov.l @r15,r3
        0x6132,     # mov.l @r3,r1
        0x2118,     # tst r1,r1
        0x8b0e,     # bf 0x06014116
        0x6192,     # mov.l @r9,r1
        0xe040,     # mov #64,r0
        0x02ed,     # mov.w @(r0,r14),r2
        0x622d,     # extu.w r2,r2
        0x321c,     # add r1,r2
        0x4208,     # shll2 r2
        0x4200,     # shll r2
        0xd088,     # mov.l @(0x06014328),r0   ; 0x060aab9c
        0x012d,     # mov.w @(r0,r2),r1
        0x7002,     # add #2,r0
        0x002d,     # mov.w @(r0,r2),r0
        0x4128,     # shll16 r1
        0x2812,     # mov.l r1,@r8
        0x4028,     # shll16 r0
        0x2302,     # mov.l r0,@r3
        # 06014116: advance
        0x60b1,     # mov.w @r11,r0
        0xc802,     # tst #2,r0
        0x8b0b,     # bf 0x06014134 (vertical)
        0xc840,     # tst #64,r0
        0x8d05,     # bt/s 0x0601412c (fixed)
        0x6382,     # mov.l @r8,r3
        0xe040,     # mov #64,r0
        0x03ed,     # mov.w @(r0,r14),r3
        0xd006,     # mov.l @(0x06014140),r0  ; widths
        0x033c,     # mov.b @(r0,r3),r3
        0x4328,     # shll16 r3
        # 0601412c
        0x51e8,     # mov.l @(32,r14),r1
        0x313c,     # add r3,r1
        0xa009,     # bra 0x06014146
        0x1e18,     # mov.l r1,@(32,r14)
        # 06014134
        0x63f2,     # mov.l @r15,r3
        0x52e9,     # mov.l @(36,r14),r2
        0x6332,     # mov.l @r3,r3
        0x323c,     # add r3,r2
        0xa003,     # bra 0x06014146
        0x1e29,     # mov.l r2,@(36,r14)
    ) + struct.pack('>I', widths_cpu) + asm(0x0009)
    assert len(code) == len(old)
    prog[a:a + len(code)] = code


def next_set(prog, at):
    """region offset of the resource after the one at `at` (its room)"""
    t = 0x0602e81c - PROG_BASE
    ptrs = set()
    for k in range(363):
        p = be32(prog, t + k * 16 + 8)
        if 0x22000000 <= p < 0x24400000:
            ptrs.add(p - 0x22000000)
    return min(p for p in ptrs if p > at)


# --- everything ----------------------------------------------------------------

def build(epr, reg, grp, comic):
    """English EPROM from the arcade one, the mask ROMs changed in reg (the
    cartridge region from 0x400000, CPU byte order); returns (eprom, log)"""
    log = []
    assert len(epr) == EPROM_SIZE
    prog, end = cmpdec.decompress(epr, PROG_AT)
    prog = bytearray(prog)
    assert all(b == 0xff for b in epr[FREE_AT:])
    out = bytearray(epr)
    free = [FREE_AT]

    def place(blob, align=4):
        at = (free[0] + align - 1) & ~(align - 1)
        assert at + len(blob) <= EPROM_SIZE, 'EPROM full'
        out[at:at + len(blob)] = blob
        free[0] = at + len(blob)
        return EPROM_CPU + at

    font = pc_font(grp)
    # sprite sets
    block = gfx.block_font(gfx.SpriteSet(reg, DIALOGUE[0]))
    low = {c: DIALOGUE_LOW + c - 0x20 for c in range(0x20, 0x2c)}
    for name, where, redirect in (('dialogue', DIALOGUE, low), ('story', STORY, {})):
        blob = build_set(reg, where, font, redirect)
        reg[where[0]:where[2]] = blob
        log.append('%s set %x bytes' % (name, len(blob.rstrip(b'\0'))))
    pc = gfx.pc_font(font)
    log += menus.build(reg, pc, block)
    log += ingame.build(reg, grp)
    log += ingame.tags(reg, block)
    log += screens.build(reg, prog, PROG_BASE, pc, block, lambda at: next_set(prog, at), place)
    log += ranking.build(reg, prog, PROG_BASE, block, lambda at: next_set(prog, at), place)
    log += nameentry.build(reg, prog, PROG_BASE, pc, next_set(prog, nameentry.NAME_SET))
    log += results.build(reg, next_set(prog, results.RESULTS_SET))
    log += aids.build(reg, pc, next_set(prog, aids.AIDS_SET))
    # advance widths by character code, and the text engine
    widths = bytearray([16] * 256)
    for c, (adv, cell) in font.items():
        widths[c] = adv
    patch_code(prog, place(bytes(widths)))
    # win quotes
    starts = quote_starts(prog)
    assert len(starts) == len(QUOTES)
    tsize = 0
    for s, text in zip(starts, QUOTES):
        ptrs = find_pointers(prog, PROG_BASE + s)
        assert len(ptrs) == 1, hex(PROG_BASE + s)
        blob = encode(text, font)
        tsize += len(blob)
        prog[ptrs[0]:ptrs[0] + 4] = struct.pack('>I', place(blob, 2))
    log.append('%d quotes, %x bytes' % (len(starts), tsize))
    # story scenes; the PC patch writes ", " as one character 0x1f
    charmap = {c: [c] for c in font}
    charmap[0x1f] = [0x2c, 0x20]
    log += story.build(prog, PROG_BASE, comic, charmap, widths, place)
    log += tutorial.build(prog, PROG_BASE, widths, place)
    # program
    comp = cmpenc.compress(bytes(prog))
    assert PROG_AT + len(comp) <= end, 'program does not fit (%x > %x)' % (len(comp), end - PROG_AT)
    out[PROG_AT:PROG_AT + len(comp)] = comp
    out[PROG_AT + len(comp):end] = bytes(end - PROG_AT - len(comp))
    assert cmpdec.decompress(out, PROG_AT)[0] == bytes(prog)
    log.append('program %x bytes (was %x), EPROM used to %x of %x' % (len(comp), end - PROG_AT, free[0], EPROM_SIZE))
    return bytes(out), log


MASKS = [('mpr19533.2', 0x400000), ('mpr19534.3', 0x800000), ('mpr19535.4', 0xc00000),
         ('mpr19536.5', 0x1000000), ('mpr19537.6', 0x1400000), ('mpr19532.1', 0x1800000),
         ('mpr19538.8', 0x1c00000), ('mpr19539.9', 0x2000000)]
OUT_NAME = {'epr19531.13': 'pse19531.13', 'mpr19533.2': 'pse19533.2', 'mpr19534.3': 'pse19534.3',
            'mpr19535.4': 'pse19535.4', 'mpr19536.5': 'pse19536.5', 'mpr19537.6': 'pse19537.6',
            'mpr19532.1': 'pse19532.1', 'mpr19538.8': 'pse19538.8', 'mpr19539.9': 'pse19539.9'}


def main():
    src, pc, dst = sys.argv[1:4]
    epr = open(os.path.join(src, 'epr19531.13'), 'rb').read()
    reg = bytearray(0x2400000)
    orig = {}
    for name, at in MASKS:
        d = open(os.path.join(src, name), 'rb').read()
        orig[name] = d
        reg[at:at + len(d)] = word_swap(d)
    grp = open(os.path.join(pc, 'puyo3', 'grp.dat'), 'rb').read()
    comic = open(os.path.join(pc, 'puyo3', 'comic.scr'), 'rb').read()
    out, log = build(epr, reg, grp, comic)
    for line in log:
        print(line)
    os.makedirs(dst, exist_ok=True)
    files = {'epr19531.13': out}
    for name, at in MASKS:
        d = word_swap(bytes(reg[at:at + len(orig[name])]))
        if d != orig[name]:
            files[name] = d
    for name, d in files.items():
        open(os.path.join(dst, OUT_NAME[name]), 'wb').write(d)
        print('wrote', OUT_NAME[name])


if __name__ == '__main__':
    main()
