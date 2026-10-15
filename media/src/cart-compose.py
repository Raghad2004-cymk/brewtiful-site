import sys, numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
UP, PHOTO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
WIRES = False  # set True to paint the near-end cart wires back over the boxes
photo = Image.open(PHOTO).convert("RGB")
files = {'colombia':'a6574dcd','honduras':'9efca64b','ethiopia':'7f14ad28','cinnamon':'4d2c96e1','grogg':'68597587'}
def box(name, h, rot):
    im = Image.open(f"{UP}/{files[name]}-image.png").convert("RGBA")
    a = np.array(im)[..., 3]; ys, xs = np.where(a > 8)
    im = im.crop((xs.min(), ys.min(), xs.max()+1, ys.max()+1))
    im = im.resize((round(im.width*h/im.height), h), Image.LANCZOS)
    im = ImageEnhance.Color(im).enhance(0.9)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)
# (name, centre-x, bottom-y, height, rotation) back to front
layout = sorted([
    ('colombia', 390,  830, 340, 6),
    ('cinnamon', 665,  790, 330, 5),
    ('honduras', 880, 1010, 350, 5),
    ('ethiopia', 365, 1085, 360, 7),
    ('honduras', 905, 1215, 365, 5),
    ('grogg',    615, 1290, 375, 6),
], key=lambda r: r[2])
# turn whatever is left of the old black bags into a soft, featureless shadow
P = np.array(photo, np.float32); lumP = P.mean(2)
bagzone = Image.new("L", photo.size, 0)
ImageDraw.Draw(bagzone).polygon([(165, 560), (480, 500), (680, 500), (1065, 1060), (1065, 1240), (560, 1310), (330, 1290)], fill=255)
bz = np.array(bagzone, np.float32)/255
dark = np.clip((95 - lumP)/40, 0, 1)*bz
dark = np.array(Image.fromarray((dark*255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(5)), np.float32)[..., None]/255
smooth = np.array(Image.fromarray(lumP.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28)), np.float32)[..., None]
shadowfill = np.repeat(np.clip(smooth*0.55, 6, 40), 3, axis=2)
photo_clean = Image.fromarray((P*(1-dark) + shadowfill*dark).clip(0, 255).astype(np.uint8))
canvas = photo_clean.convert("RGBA")
for name, cx, by, h, rot in layout:
    b = box(name, h, rot)
    x, y = int(cx - b.width/2), int(by - b.height)
    a = b.getchannel("A")
    sh = Image.new("L", canvas.size, 0)
    sh.paste(a.point(lambda v: int(v*0.85)), (x+18, y+26))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    dark = Image.new("RGBA", canvas.size, (0, 0, 0, 255)); dark.putalpha(sh)
    canvas.alpha_composite(dark)
    canvas.alpha_composite(b, (x, y))
out = np.array(canvas.convert("RGB"), np.float32)
orig = np.array(photo, np.float32); lum = orig.mean(2)
L = Image.fromarray(lum.astype(np.uint8))
local = np.array(L.filter(ImageFilter.GaussianBlur(18)), np.float32)
fine = np.array(L.filter(ImageFilter.GaussianBlur(3)), np.float32)
dark_bg = np.array(Image.fromarray((np.array(L.filter(ImageFilter.MinFilter(15)))<45).astype(np.uint8)*255).filter(ImageFilter.GaussianBlur(4)), np.float32)/255
wire = np.clip((lum - local - 18)/25, 0, 1) * np.clip((lum-60)/40, 0, 1) * dark_bg
zone = Image.new("L", photo.size, 0)   # only the cart's near end sits in front of the cargo
ImageDraw.Draw(zone).polygon([(930, 980), (1200, 980), (1200, 1600), (360, 1600), (360, 1290), (930, 1170)], fill=255)
wire = wire*np.array(zone.filter(ImageFilter.GaussianBlur(6)), np.float32)/255
wire = np.array(Image.fromarray((wire*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None]/255
out = out*(1-wire) + orig*wire if WIRES else out
out += np.random.default_rng(2).normal(0, 3.0, out.shape[:2])[..., None]   # match film grain
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT, quality=95)
