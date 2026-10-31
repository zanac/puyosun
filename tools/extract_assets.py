"""Make assets/puyosune_assets.zip (see assets.py) from the Puyo Nexus English
patch of the Windows version, as it comes. Only needed to remake the zip;
the build does not use the patch. Python 3 standard library only.

    python3 extract_assets.py Puyo_Puyo_Sun__English_Patched_.zip [ASSETS_ZIP]
"""
import sys
import zipfile

import assets
import build
import ingame
import story


def read_member(z, name):
    for i in z.infolist():
        if i.filename.lower().replace('\\', '/').endswith(name):
            return z.read(i)
    raise SystemExit('%s: no %s' % (z.filename, name))


def main():
    patch = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else assets.DEFAULT
    zp = zipfile.ZipFile(patch)
    grp = read_member(zp, 'puyo3/grp.dat')
    comic = read_member(zp, 'puyo3/comic.scr')
    pictures = {}
    for at, k, ids, room in ingame.PICTURES:
        frames = ingame.pc_frames(grp, k)
        for i in ids:
            j = i[1] if isinstance(i, tuple) else i
            pictures[(k, j)] = frames[j]
    a = assets.Assets(build.pc_font(grp), pictures, story.pc_scenes(comic))
    assets.save(dst, a)
    print('wrote %s: %d characters, %d pictures, %d scenes' % (dst, len(a.font), len(pictures), len(a.story)))


if __name__ == '__main__':
    main()
