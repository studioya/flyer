"""Swap the Aumbry renders in the portfolio PDFs for new ones, keeping every page's layout and text."""
import io, sys
from PIL import Image
from pypdf import PdfReader, PdfWriter
R = sys.argv[1]  # folder with the RGBA renders
BIRCH, WHITE = '#f1e9dc', '#ffffff'
def flat(name, ground, size):
    im = Image.open(f'{R}/{name}.png').convert('RGBA')
    g = Image.new('RGBA', im.size, ground); g.alpha_composite(im)
    return g.convert('RGB').resize(size, Image.LANCZOS)
# object id of the image XObject -> (render, ground)
JOBS = {
    'aumbry-2.0.pdf': ({46: ('cover', WHITE), 211: ('door', BIRCH), 291: ('tracery', BIRCH), 293: ('dowels', BIRCH),
                        297: ('tracks', BIRCH), 393: ('back', WHITE), 295: ('rfid', BIRCH), 391: ('display', WHITE)}, 1.0),
    'aumbry-2.0-mobile.pdf': ({57: ('cover', WHITE), 222: ('door', WHITE), 302: ('tracery', WHITE), 304: ('dowels', WHITE),
                               308: ('tracks', WHITE), 404: ('back', WHITE), 306: ('rfid', WHITE), 402: ('display', WHITE)}, 1.0),
}
src, out = sys.argv[2], sys.argv[3]
for fn, (jobs, _) in JOBS.items():
    rd = PdfReader(f'{src}/{fn}')
    # the writer renumbers objects: find each target by page and image name in the original
    where = {(pi, im.name): im.indirect_reference.idnum for pi, pg in enumerate(rd.pages) for im in pg.images}
    w = PdfWriter(clone_from=rd)
    done = set()
    for pi, page in enumerate(w.pages):
        for img in page.images:
            oid = where.get((pi, img.name))
            if oid in jobs and oid not in done:
                name, ground = jobs[oid]
                ow, oh = img.image.size
                # keep the aspect, at up to 1600 px wide
                k = 1600 / ow if ow < 1600 else 1
                img.replace(flat(name, ground, (round(ow * k), round(oh * k))), quality=88)
                done.add(oid)
    assert done == set(jobs), (fn, set(jobs) - done)
    w.write(f'{out}/{fn}')
    print(fn, 'replaced', sorted(done))
