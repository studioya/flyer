import sys
from PIL import Image
src, out, bg = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(src).convert('RGBA')
c = Image.new('RGBA', im.size, bg); c.alpha_composite(im); c.convert('RGB').save(out, quality=92)
