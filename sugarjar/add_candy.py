# -*- coding: utf-8 -*-
"""
sugar jar · 往罐子里丢一颗糖
用法：
  python3 add_candy.py --text "今天她说了句特别好笑的" --color plum --shape twist
  python3 add_candy.py --text "..." --color 桃 --shape wrapped

不给 color / shape 就按文本哈希随机挑 —— 同一句话永远挑到同一颗糖。
"""
import os, json, hashlib, argparse, datetime

BASE = os.path.dirname(os.path.abspath(__file__)) + '/'
DB = BASE + 'candies.jsonl'

COLORS = ['plum', 'peach', 'mint', 'lemon', 'berry', 'grape',
          'apricot', 'rose', 'lime', 'caramel', 'sky', 'cherry']
SHAPES = ['round', 'twist', 'drop', 'star', 'cube', 'bean', 'heart', 'ring']
SIZES = [0.82, 0.92, 1.0, 1.08, 1.18, 1.3]   # 多重的一颗糖


def pick(text, pool):
    h = hashlib.md5(text.encode('utf-8')).hexdigest()
    return pool[int(h[:8], 16) % len(pool)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--text', required=True, help='那颗糖要说的话')
    ap.add_argument('--color', default=None)
    ap.add_argument('--shape', default=None)
    ap.add_argument('--size', type=float, default=None)
    ap.add_argument('--date', default=None, help='默认今天')
    ap.add_argument('--src', default='碎片集', help='来源，默认碎片集')
    a = ap.parse_args()

    txt = a.text.strip()
    rec = {
        'id': datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
        'date': a.date or datetime.date.today().isoformat(),
        'text': txt,
        'color': a.color or pick(txt, COLORS),
        'shape': a.shape or pick(txt + 's', SHAPES),
        'size': a.size or pick(txt + 'z', SIZES),
        'src': a.src,
    }
    with open(DB, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    n = sum(1 for _ in open(DB, encoding='utf-8'))
    print('丢进去了一颗：%s / %s / %.2f' % (rec['color'], rec['shape'], rec['size']))
    print('“%s”' % txt)
    print('罐子里现在一共有 %d 颗。' % n)


if __name__ == '__main__':
    main()
