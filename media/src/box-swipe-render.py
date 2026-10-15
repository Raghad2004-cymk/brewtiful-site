import sys, os, math, subprocess, wave, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

UP = sys.argv[1]; OUT = sys.argv[2]; TMP = sys.argv[3]
SCALE = float(os.environ.get("SCALE", "1"))   # 1 = 4K, 0.25 = preview
W, H = int(2160*SCALE), int(3840*SCALE)
FPS, DUR = 30, 10.0
N = int(FPS*DUR)
S = lambda v: v*SCALE

files = ['a6574dcd','9efca64b','7f14ad28','4d2c96e1','68597587']  # Colombia, Honduras, Ethiopia, Cinnamon, Grogg

# ---- background: user-supplied ground-coffee photo, cover-fit, gentle light pool ----
rng = np.random.default_rng(7)
BOX_H = S(1500); CX, CBOT = W/2, H*0.70
src = Image.open(os.environ.get("BG_IMG")).convert("RGB")
k = max(W/src.width, H/src.height)
src = src.resize((math.ceil(src.width*k), math.ceil(src.height*k)), Image.LANCZOS)
ox, oy = (src.width-W)//2, (src.height-H)//2
bg = np.array(src.crop((ox, oy, ox+W, oy+H)), np.float32)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
pool = np.exp(-(((xx-W*0.5)/(W*0.75))**2 + ((yy-H*0.52)/(H*0.42))**2))[..., None]
bg = bg*(0.72 + 0.42*pool)
bg += rng.normal(0, 2.0, bg.shape[:2])[..., None]  # restore fine grain lost in upscaling
bg = np.clip(bg, 0, 255).astype(np.float32)

# ---- boxes normalised to identical height + centre (cropped to box+shadow region) ----
boxes = []

for f in files:
    im = Image.open(f"{UP}/{f}-image.png").convert("RGBA")
    a = np.array(im)[..., 3]; ys, xs = np.where(a > 8)
    im = im.crop((xs.min(), ys.min(), xs.max()+1, ys.max()+1))
    k = BOX_H/im.height
    im = im.resize((round(im.width*k), round(BOX_H)), Image.LANCZOS)
    x0 = round(CX - im.width/2); y0 = round(CBOT - im.height)
    layer = np.zeros((H, W, 4), np.float32)
    layer[y0:y0+im.height, x0:x0+im.width] = np.array(im, np.float32)
    rgb = layer[..., :3]; al = layer[..., 3:]/255.0
    # shadows: soft drop + tight contact
    am = Image.fromarray((al[..., 0]*255).astype(np.uint8))
    soft = np.array(am.transform(am.size, Image.AFFINE, (1, 0, S(-25), 0, 1, S(-45)))
                    .filter(ImageFilter.GaussianBlur(S(60))), np.float32)/255*0.45
    contact = Image.new("L", (W, H), 0)
    ImageDraw.Draw(contact).ellipse((x0+S(30), CBOT-S(22), x0+im.width-S(10), CBOT+S(26)), fill=255)
    contact = np.array(contact.filter(ImageFilter.GaussianBlur(S(22))), np.float32)/255*0.8
    shadow = np.clip(soft + contact, 0, 0.85)[..., None]
    boxes.append(dict(rgb=rgb, al=al, shadow=shadow, mask=al[..., 0] > 0.9, bbox=(x0, y0, x0+im.width, CBOT)))


# crop each box layer to the region its box + shadow occupy, so it can be slid cheaply
for b in boxes:
    occ = (b["shadow"][..., 0] > 0.003) | (b["al"][..., 0] > 0)
    ys, xs = np.where(occ)
    y0, y1, x0, x1 = ys.min(), ys.max()+1, xs.min(), xs.max()+1
    b["reg"] = (y0, y1, x0, x1)
    b["c_rgb"] = b["rgb"][y0:y1, x0:x1].copy(); b["c_al"] = b["al"][y0:y1, x0:x1].copy()
    b["c_sh"] = b["shadow"][y0:y1, x0:x1].copy()
    del b["rgb"], b["al"], b["shadow"]

def place(img, b, dx):
    y0, y1, x0, x1 = b["reg"]
    X0, X1 = x0 + dx, x1 + dx
    a, z = max(X0, 0), min(X1, W)
    if a >= z: return
    sa, sz = a - X0, z - X0
    reg = img[y0:y1, a:z]
    sh = b["c_sh"][:, sa:sz]; al = b["c_al"][:, sa:sz]
    reg = reg*(1-sh)
    img[y0:y1, a:z] = reg*(1-al) + b["c_rgb"][:, sa:sz]*al

# ---- timeline: four left swipes ----
swipes = [1.3, 3.1, 4.9, 6.7]
DOWN, DRAG, SETTLE = 0.14, 0.40, 0.42
D = W*1.0                       # spacing between neighbouring boxes on the carousel
FX0, FX1 = W*0.72, W*0.30       # finger travel on the box face
FY = CBOT - BOX_H*0.45

def ease_io(u): u = min(max(u, 0), 1); return 0.5-0.5*math.cos(math.pi*u)
def ease_out(u): u = min(max(u, 0), 1); return 1-(1-u)**3

def state(t):
    """returns (index of left box, carousel offset of that box, finger (x,y,alpha,scale) or None)"""
    idx, off, finger = 0, 0.0, None
    for k, ts in enumerate(swipes):
        if t < ts: break
        dt = t - ts
        if dt < DOWN:
            idx, off = k, 0.0
            u = dt/DOWN
            finger = (FX0, FY, ease_out(u), 0.75+0.25*ease_out(u))
        elif dt < DOWN + DRAG:
            u = (dt-DOWN)/DRAG
            fx = FX0 + (FX1-FX0)*ease_io(u)
            idx, off = k, fx - FX0
            finger = (fx, FY, 1.0, 1.0)
        elif dt < DOWN + DRAG + SETTLE:
            u = (dt-DOWN-DRAG)/SETTLE
            rel = FX1 - FX0
            idx, off = k, rel + (-D - rel)*ease_out(u)
            fu = min(u/0.45, 1)
            finger = (FX1 - S(90)*ease_out(fu), FY, 1-fu, 1.0+0.25*fu)
        else:
            idx, off = k+1, 0.0
    return idx, off, finger

frames_dir = f"{TMP}/frames"; os.makedirs(frames_dir, exist_ok=True)
trail = []
for n in range(N):
    t = n/FPS
    idx, off, finger = state(t)
    img = bg.copy()
    place(img, boxes[idx], int(round(off)))
    if off != 0 and idx+1 < 5:
        place(img, boxes[idx+1], int(round(off + D)))
    frame = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(ov)
    # carousel dots: active dot follows the box nearest centre
    active = idx + (1 if off < -D/2 else 0)
    gap = S(46); y = H*0.925; xs0 = W/2 - gap*2
    for k in range(5):
        x = xs0 + gap*k
        if k == active:
            d.rounded_rectangle((x-S(22), y-S(7), x+S(22), y+S(7)), radius=S(7), fill=(241,233,219,240))
        else:
            d.ellipse((x-S(7), y-S(7), x+S(7), y+S(7)), fill=(241,233,219,90))
    # touch indicator with a short fading trail
    if finger:
        fx, fy, fa, fs = finger
        trail.append((fx, fy)); trail = trail[-6:]
        for j, (tx, ty) in enumerate(trail[:-1]):
            k_ = (j+1)/len(trail)
            r = S(40)*k_*fs
            d.ellipse((tx-r, ty-r, tx+r, ty+r), fill=(255,255,255,int(45*k_*fa)))
        r = S(62)*fs
        d.ellipse((fx-r-S(10), fy-r-S(10), fx+r+S(10), fy+r+S(10)), fill=(0,0,0,int(35*fa)))
        d.ellipse((fx-r, fy-r, fx+r, fy+r), fill=(255,255,255,int(115*fa)), outline=(255,255,255,int(225*fa)), width=max(1, int(S(5))))
    else:
        trail = []
    frame.alpha_composite(ov)
    frame.convert("RGB").save(f"{frames_dir}/{n:04d}.png", compress_level=1)
    if n % 30 == 0: print("frame", n, flush=True)

# ---- swipe sound: airy whoosh on the flick + soft tick when the box lands ----
SR = 48000; audio = np.zeros((int(SR*DUR),), np.float64)
rng_a = np.random.default_rng(5)
def whoosh(dur=0.42):
    n = int(SR*dur); t = np.arange(n)/SR
    noise = rng_a.normal(0, 1, n)
    out = np.zeros(n); lp = 0.0; hp_prev_in = 0.0; hp = 0.0
    for i in range(n):
        u = i/n
        fc = 500 + 3200*math.sin(math.pi*min(u*1.3, 1))   # sweep up then down
        a_lp = 1 - math.exp(-2*math.pi*fc/SR)
        lp += a_lp*(noise[i]-lp)
        hp = 0.985*(hp + lp - hp_prev_in); hp_prev_in = lp
        out[i] = hp
    env = np.sin(np.pi*np.clip(t/dur, 0, 1))**1.6
    return out*env
def tick():
    n = int(SR*0.05); t = np.arange(n)/SR
    return (np.sin(2*np.pi*1800*t)*0.5 + np.sin(2*np.pi*520*t)*0.5)*np.exp(-t*160) + rng_a.normal(0, 1, n)*np.exp(-t*1600)*0.4
w = whoosh(); w /= np.abs(w).max(); tk = tick(); tk /= np.abs(tk).max()
for ts in swipes:
    i = int((ts + DOWN + DRAG*0.35)*SR); audio[i:i+len(w)] += w*0.9
    j = int((ts + DOWN + DRAG + SETTLE*0.55)*SR); audio[j:j+len(tk)] += tk*0.35
audio = np.tanh(audio*1.4)/np.tanh(1.4); audio = audio/np.abs(audio).max()*0.89
st = np.repeat(audio[:, None], 2, axis=1)
with wave.open(f"{TMP}/swipe.wav", "wb") as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
    wv.writeframes((st*32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{frames_dir}/%04d.png",
                "-i", f"{TMP}/swipe.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-level", "5.1", "-tag:v", "avc1", "-c:a", "aac", "-b:a", "256k",
                "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT)
