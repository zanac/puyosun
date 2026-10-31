"""Make the puyosune set (Puyo Puyo Sun, English) from the arcade puyosun set,
as it comes, and the translated assets of the Puyo Nexus English patch in
assets/puyosune_assets.zip. Python 3 standard library only.

    python3 make_puyosune.py puyosun.zip OUT_DIR [ASSETS_ZIP]

OUT_DIR receives puyosune.zip (the whole set: the three changed ROMs and the
unchanged mask ROMs) and the three changed ROMs as files.
"""
import hashlib
import os
import sys
import zipfile
import zlib

import assets
import build

EXPECTED = {
    'epr19531.13': 'ac81024f', 'mpr19532.1': '985f0c9d', 'mpr19533.2': '17ec54ba',
    'mpr19534.3': '820e4781', 'mpr19535.4': '94fadfa4', 'mpr19536.5': '5765bc9c',
    'mpr19537.6': '8b736686', 'mpr19538.8': '915a723e', 'mpr19539.9': '72a297e5',
}


def crc(d):
    return '%08x' % (zlib.crc32(d) & 0xffffffff)


def read_member(z, name):
    for i in z.infolist():
        if i.filename.lower().replace('\\', '/').endswith(name):
            return z.read(i)
    raise SystemExit('%s: no %s' % (z.filename, name))


def main():
    arcade, dst = sys.argv[1:3]
    pack = assets.load(*sys.argv[3:4])
    za = zipfile.ZipFile(arcade)
    roms = {}
    for name, want in EXPECTED.items():
        d = read_member(za, name)
        if crc(d) != want:
            raise SystemExit('%s: CRC %s, expected %s (puyosun set from MAME)' % (name, crc(d), want))
        roms[name] = d

    reg = bytearray(0x2400000)
    for name, at in build.MASKS:
        reg[at:at + len(roms[name])] = build.word_swap(roms[name])
    out, log = build.build(roms['epr19531.13'], reg, pack)
    for line in log:
        print(line)
    files = {'pse19531.13': out}
    for name, at in build.MASKS:
        d = build.word_swap(bytes(reg[at:at + len(roms[name])]))
        files[build.OUT_NAME[name] if d != roms[name] else name] = d
    os.makedirs(dst, exist_ok=True)
    with zipfile.ZipFile(os.path.join(dst, 'puyosune.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            z.writestr(name, files[name])
    for name in sorted(files):
        d = files[name]
        if name.startswith('pse'):
            open(os.path.join(dst, name), 'wb').write(d)
            print('%-12s %8d  crc %s  sha1 %s' % (name, len(d), crc(d), hashlib.sha1(d).hexdigest()))
    print('wrote', os.path.join(dst, 'puyosune.zip'))


if __name__ == '__main__':
    main()
