"""The translated assets of the Puyo Nexus English patch that the build uses,
kept in assets/puyosune_assets.zip so the build needs only the arcade set.

The zip holds JSON files:
  font.json     {code: [advance, 256 colour indices of the 16x16 cell]}: the
                English font of the patch (grp.dat entry 21) and the note
                taken from a win quote picture (entry 1)
  pictures.json {"entry/frame": [w, h, pixels]}: the in-game pictures the
                patch translated (ingame.PICTURES), frames as placed
  story.json    [[[time, text words]]]: the English pages of the 24 story
                scenes (comic.scr), in scene order

extract_assets.py makes the zip from the patched Windows game; the build
reads only the zip.
"""
import json
import os
import zipfile

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets',
                       'puyosune_assets.zip')


class Assets:
    def __init__(self, font, pictures, story):
        self.font = font            # {code: (advance, cell)}
        self.pictures = pictures    # {(entry, frame): (w, h, pixels)}
        self.story = story          # [[(time, words)]]


def load(path=DEFAULT):
    with zipfile.ZipFile(path) as z:
        font = json.loads(z.read('font.json'))
        pictures = json.loads(z.read('pictures.json'))
        story = json.loads(z.read('story.json'))
    return Assets({int(c): (adv, cell) for c, (adv, cell) in font.items()},
                  {tuple(int(x) for x in k.split('/')): tuple(v) for k, v in pictures.items()},
                  [[(t, w) for t, w in scene] for scene in story])


def save(path, a):
    def dump(o):
        return json.dumps(o, separators=(',', ':'), sort_keys=True).encode()
    font = {str(c): [adv, list(cell)] for c, (adv, cell) in a.font.items()}
    pictures = {'%d/%d' % k: [w, h, list(px)] for k, (w, h, px) in a.pictures.items()}
    story = [[[t, list(w)] for t, w in scene] for scene in a.story]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, o in (('font.json', font), ('pictures.json', pictures), ('story.json', story)):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, dump(o))
