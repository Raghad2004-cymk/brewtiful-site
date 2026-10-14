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

# ---- background: warm off-white studio sweep ----
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
base = np.array([244, 238, 228], np.float32)
r = np.sqrt(((xx-W*0.5)/W)**2 + ((yy-H*0.36)/H*0.75)**2)
light = 1.035 - 0.16*np.clip(r, 0, 1.2)**1.6
floor = np.clip((yy - H*0.62)/(H*0.38), 0, 1)
light = light - 0.035*floor
bg = np.clip(base[None, None, :]*light[..., None], 0, 255)
rng = np.random.default_rng(1)
bg += rng.normal(0, 0.9, bg.shape[:2])[..., None]  # fine grain against banding
bg = np.clip(bg, 0, 255).astype(np.float32)

# ---- boxes normalised to identical height + centre ----
BOX_H = S(1500); CX, CBOT = W/2, H*0.66
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
                    .filter(ImageFilter.GaussianBlur(S(60))), np.float32)/255*0.20
    contact = Image.new("L", (W, H), 0)
    ImageDraw.Draw(contact).ellipse((x0+S(30), CBOT-S(22), x0+im.width-S(10), CBOT+S(26)), fill=255)
    contact = np.array(contact.filter(ImageFilter.GaussianBlur(S(22))), np.float32)/255*0.45
    shadow = np.clip(soft + contact, 0, 0.7)[..., None]
    boxes.append(dict(rgb=rgb, al=al, shadow=shadow, mask=al[..., 0] > 0.9, bbox=(x0, y0, x0+im.width, CBOT)))

def comp_box(i):
    b = boxes[i]
    img = bg*(1-b["shadow"]) + np.array([60, 45, 35], np.float32)*b["shadow"]*0.0
    return img*(1-b["al"]) + b["rgb"]*b["al"], b["al"]

# ---- cursor (macOS-style arrow) ----
def make_cursor(h):
    s = h/22.0
    pts = [(0,0),(0,17),(4,13),(7,20),(10,19),(7,12),(12.5,12)]
    pts = [(x*s+s*2, y*s+s*2) for x, y in pts]
    sz = (int(16*s), int(26*s))
    shadow = Image.new("L", sz, 0); ImageDraw.Draw(shadow).polygon([(x+s*0.6, y+s*1.0) for x, y in pts], fill=110)
    shadow = shadow.filter(ImageFilter.GaussianBlur(s*0.9))
    cur = Image.new("RGBA", sz, (0,0,0,0)); d = ImageDraw.Draw(cur)
    d.polygon(pts, fill=(255,255,255,255))
    inner = [(0,0),(0,17),(4,13),(7,20),(10,19),(7,12),(12.5,12)]
    cx_, cy_ = 4.5, 11
    inner = [((x-cx_)*0.78+cx_)*s+s*2 for x, y in inner], [((y-cy_)*0.84+cy_)*s+s*2 for x, y in inner]
    d.polygon(list(zip(*inner)), fill=(18,18,18,255))
    out = Image.new("RGBA", sz, (0,0,0,0)); out.paste((0,0,0,255), mask=shadow); out.alpha_composite(cur)
    return out, (s*2, s*2)  # hotspot
CUR_H = S(175)
cursor_cache = {}
def cursor(scale):
    key = round(scale, 3)
    if key not in cursor_cache: cursor_cache[key] = make_cursor(CUR_H*scale)
    return cursor_cache[key]

# ---- timeline ----
clicks = [1.7, 3.5, 5.3, 7.1]
# click targets (inside the front face, chosen to be on BOTH outgoing and incoming box)
targets = [(0.47, 0.42), (0.40, 0.66), (0.55, 0.33), (0.44, 0.55)]
def target_px(j):
    fx, fy = targets[j]
    x0, y0, x1, y1 = boxes[0]["bbox"]
    # use intersection of bboxes of box j and j+1 for safety
    xa = max(boxes[j]["bbox"][0], boxes[j+1]["bbox"][0]); xb = min(boxes[j]["bbox"][2], boxes[j+1]["bbox"][2])
    ya = max(boxes[j]["bbox"][1], boxes[j+1]["bbox"][1]); yb = min(boxes[j]["bbox"][3], boxes[j+1]["bbox"][3])
    p = (xa + fx*(xb-xa), ya + fy*(yb-ya))
    for k in (j, j+1):
        assert boxes[k]["mask"][int(p[1]), int(p[0])], f"click {j} misses box {k}"
    return p
keys = [(0.0, (W*0.93, H*0.88)), (0.35, (W*0.86, H*0.82))]
for j, t in enumerate(clicks):
    keys.append((t, target_px(j)))
keys.append((8.4, (W*0.80, H*0.76)))
keys.append((10.0, (W*0.82, H*0.78)))

def ease(u): return u*u*(3-2*u) if u < 1 else 1.0
def ease_io(u): u = min(max(u, 0), 1); return 0.5-0.5*math.cos(math.pi*u)
def cursor_pos(t):
    # hold briefly at each click, glide between with ease-in-out and a gentle arc
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            hold_a = 0.18 if any(abs(t0-c) < 1e-6 for c in clicks) else 0
            hold_b = 0.12 if any(abs(t1-c) < 1e-6 for c in clicks) else 0
            u = (t - t0 - hold_a)/max(t1 - t0 - hold_a - hold_b, 1e-6)
            e = ease_io(u)
            arc = math.sin(math.pi*min(max(u,0),1))*S(60)
            return (p0[0]+(p1[0]-p0[0])*e + arc*0.4, p0[1]+(p1[1]-p0[1])*e - arc)
    return keys[-1][1]

SNAP = 0.12   # crossfade length (s) — near-instant "snap"
def box_state(t):
    idx = sum(1 for c in clicks if t >= c + 0.04)
    if idx == 0: return 0, None, 0
    c = clicks[idx-1] + 0.04
    u = (t - c)/SNAP
    return idx, idx-1, (1-ease(u)) if u < 1 else 0  # (current, previous, prev weight)

def press(t):
    for c in clicks:
        d = t - c
        if -0.06 <= d <= 0.14: return 1 - 0.14*math.sin(math.pi*(d+0.06)/0.20)
    return 1.0

frames_dir = f"{TMP}/frames"; os.makedirs(frames_dir, exist_ok=True)
box_imgs = [comp_box(i) for i in range(5)]
for n in range(N):
    t = n/FPS
    cur, prev, wprev = box_state(t)
    img = box_imgs[cur][0]
    if prev is not None and wprev > 0:
        img = img*(1-wprev) + box_imgs[prev][0]*wprev
    # subtle highlight lift on the box right after a click (light catch, not a zoom)
    for c in clicks:
        d = t - c - 0.04
        if 0 <= d < 0.45:
            g = 0.06*math.exp(-d*9)
            img = img + (255-img)*g*box_imgs[cur][1]
    frame = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(ov)
    # click ripple
    for j, c in enumerate(clicks):
        dt = t - c
        if 0 <= dt < 0.55:
            px, py = target_px(j); u = dt/0.55
            rad = S(30) + S(150)*(1-(1-u)**3)
            alpha = int(200*(1-u)**1.6); wdt = max(1, int(S(7)*(1-u)+S(2)))
            d.ellipse((px-rad, py-rad, px+rad, py+rad), outline=(255,255,255,alpha), width=wdt)
            if dt < 0.16:
                r0 = S(26)*(1-dt/0.16)+S(8)
                d.ellipse((px-r0, py-r0, px+r0, py+r0), fill=(255,255,255,int(150*(1-dt/0.16))))
    # selection dots (website UI)
    cur_idx = cur
    gap = S(46); y = H*0.80; xs0 = W/2 - gap*2
    for k in range(5):
        x = xs0 + gap*k
        if k == cur_idx:
            d.rounded_rectangle((x-S(22), y-S(7), x+S(22), y+S(7)), radius=S(7), fill=(23,52,44,235))
        else:
            d.ellipse((x-S(7), y-S(7), x+S(7), y+S(7)), fill=(23,52,44,70))
    frame.alpha_composite(ov)
    cimg, (hx, hy) = cursor(press(t))
    px, py = cursor_pos(t)
    frame.alpha_composite(cimg, (int(round(px-hx)), int(round(py-hy))))
    frame.convert("RGB").save(f"{frames_dir}/{n:04d}.png", compress_level=1)
    if n % 30 == 0: print("frame", n, flush=True)

# ---- click sound ----
SR = 48000; audio = np.zeros(int(SR*DUR), np.float32)
def click_snd():
    n = int(SR*0.05); tt = np.arange(n)/SR
    body = np.sin(2*np.pi*3200*tt)*np.exp(-tt*260)*0.55 + np.sin(2*np.pi*1500*tt)*np.exp(-tt*180)*0.35
    noise = np.random.default_rng(3).normal(0, 1, n)*np.exp(-tt*900)*0.35
    rel_n = int(SR*0.035); rel = np.zeros(n); tr = np.arange(n-rel_n)/SR
    rel[rel_n:] = np.sin(2*np.pi*4200*tr)*np.exp(-tr*400)*0.18
    return (body + noise + rel).astype(np.float32)
cs = click_snd()
for c in clicks:
    i = int(c*SR); audio[i:i+len(cs)] += cs*0.8
audio = np.clip(audio, -1, 1)
with wave.open(f"{TMP}/click.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((audio*32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{frames_dir}/%04d.png",
                "-i", f"{TMP}/click.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-level", "5.1", "-tag:v", "avc1", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT)
