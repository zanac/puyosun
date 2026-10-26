"""In-game lettering from the Puyo Nexus patch: the Windows version uses the
same sprite sets as the arcade (sprite set k of the cartridge is grp.dat
entry k - 1) with the same colour numbers, so the pictures the patch
translated are copied as they are.
"""
import struct

import grpdat
from gfx import SpriteSet

# (set in the cartridge, grp.dat entry, pictures)
PICTURES = [
    (0x400000, 0, [379, 380, 381], None),       # 'chain' tag, YEAH! (win), OH NO! (lose)
    (0x416ce8, 5, list(range(27, 49)), None),   # All Clear! (animation), Offset
    (0x45b9e0, 19, [7], 0x45c9a4),              # 'Rules' of the rules demo (compressed set)
    # curry strength labels (Sweet .. Hot): the PC set has them after its
    # own frames, (arcade picture, PC frame)
    (0x416ce8, 5, [(61, 138), (62, 139), (63, 140), (64, 141), (65, 142)], None),
]


def pc_frames(grp, k):
    """[(w, h, pixels)] of the frames of grp.dat entry k, parts placed"""
    o, s = grpdat.entries(grp)[k]
    d = grp[o:o + s]
    t, frames, parts, base = grpdat.parse(d)
    out = []
    for (w, h), (pw, ph, px, py, a, fl, off) in zip(frames, parts):
        px = px - 0x10000 if px & 0x8000 else px
        py = py - 0x10000 if py & 0x8000 else py
        img = [0] * (w * h)
        src = d[base + off:base + off + pw * ph]
        for y in range(ph):
            for x in range(pw):
                X, Y = x + px, y + py
                if 0 <= X < w and 0 <= Y < h:
                    img[Y * w + X] = src[y * pw + x]
        out.append((w, h, img))
    return out


def build(reg, grp):
    n = 0
    for at, k, ids, room in PICTURES:
        ss = SpriteSet(reg, at, room=room, compressed=room is not None)
        frames = pc_frames(grp, k)
        for i in ids:
            i, j = i if isinstance(i, tuple) else (i, i)
            w, h, px = frames[j]
            assert (w, h) == tuple(ss.desc[i][:2]) and max(px) < 16, (k, i)
            ss.put(i, px)
            n += 1
        ss.write()
    return ['in-game pictures from the PC patch: %d' % n]


# the vertical tags at the sides of the playfields (arcade only: the PC
# version has none): 'n wins', 'join in', 'bring it on', 'challenger',
# 'no joining'. English block letters turned a quarter to the right.
TAG_SET = 0x416ce8
TAGS = {128: 'WINS', 129: 'JOIN OK', 130: 'COME ON', 131: 'RIVAL', 132: 'NO ENTRY'}


def tags(reg, block):
    from gfx import Canvas
    ss = SpriteSet(reg, TAG_SET, compressed=False)
    for i, text in TAGS.items():
        w, h, old = ss.get(i)
        wd = block.width(text)
        assert w == 16 and wd <= h, (text, wd, h)
        cv = Canvas(h, 16)
        block.draw(cv, text, (h - wd) // 2, 0, {})
        # turn right: column x of the sprite is row 15 - x of the line
        px = [cv.px[(15 - x) * h + y] for y in range(h) for x in range(16)]
        ss.put(i, px)
    ss.write()
    return ['side tags: %d' % len(TAGS)]
