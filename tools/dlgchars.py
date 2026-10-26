"""Characters of the dialogue font of the arcade Puyo Puyo Sun (cart block
0x4120ed, glyph i at 0xb94 + i * 0x80; text code = i + 0x2c)."""
CHARS = (
    '・?!ー~Xあいうえおか'
    'きくけこさしすせそたちつ'
    'てとなにぬねのはひふへほ'
    'まみむめもやよらりるれろ'
    'わをんがぎぐげござじずぜ'
    'ぞだづでどばぶべぼぷぁぇ'
    'っゃゅょアイウオカキクコ'
    'サシスセタチツテトナニハ'
    'ヒフヘホマミメユラルレロ'
    'ングジゼゾダデドバビブボ'
    'パピプポァィェォッャュ連'
    '鎖目回転消大勝負茶歌顔気'
    '見魔導師文句闇王勇者操作'
    '全力出怒暗電光石火主役名'
)
assert len(CHARS) == 168
OFFSET = 0x2c


def decode(words):
    out = []
    for w in words:
        if OFFSET <= w < OFFSET + len(CHARS):
            out.append(CHARS[w - OFFSET])
        elif w == 0xff02:
            out.append('\n')
        else:
            out.append('{%04x}' % w)
    return ''.join(out)
