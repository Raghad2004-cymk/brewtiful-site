import sys, wave, numpy as np
SR, DUR = 48000, 10.0
clicks = [1.7, 3.5, 5.3, 7.1]
rng = np.random.default_rng(3)
def tick(f1, f2, amp, decay):
    n = int(SR*0.09); t = np.arange(n)/SR
    # sharp plastic transient + two resonant modes + a little low "thock" body
    s = (np.sin(2*np.pi*f1*t)*0.6 + np.sin(2*np.pi*f2*t)*0.4)*np.exp(-t*decay)
    s += np.sin(2*np.pi*420*t)*np.exp(-t*90)*0.45
    s += rng.normal(0, 1, n)*np.exp(-t*1400)*0.9
    att = np.clip(t/0.0004, 0, 1)
    return s*att*amp
press = tick(2300, 4100, 1.0, 140)
release = tick(2900, 5200, 0.55, 190)
audio = np.zeros(int(SR*DUR))
for c in clicks:
    i = int((c-0.01)*SR); audio[i:i+len(press)] += press
    j = i + int(0.075*SR); audio[j:j+len(release)] += release
audio = np.tanh(audio*1.6)/np.tanh(1.6)   # gentle saturation = louder, punchier
audio = audio/np.abs(audio).max()*0.89
stereo = np.repeat(audio[:, None], 2, axis=1)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((stereo*32767).astype(np.int16).tobytes())
