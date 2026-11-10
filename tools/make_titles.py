"""Title screen still + title music of the eight Korean mod ROMs, for the web first screen.

The first screen shows each game's own title screen and plays the music heard there. Neither exists
as a file: the disassemblies hold tiles and note data (Gen 3 MIDI, Gold/Yellow asm) and the Korean
logos and the Yellow port's Pikachu title live only in the mod ROMs. So each ROM is run once in
libmgba (docker image pokegold-title, tools/title_capture) and the picture and sound are cut out:

- Run: Gold/Silver and FireRed/LeafGreen/Yellow get START during the intro (the frame the old live
  preview used) and go straight to the title. Ruby/Sapphire/Emerald play the intro to its end
  instead: START there swaps the intro song for the title song with no gap (no clean start to
  find), while at the intro's own end Emerald has 4 silent frames and Ruby/Sapphire a soft held
  chord (RMS ~1100) before the title song's first hit (RMS 3700+).
- Music start (ONSET): first frame from `from` on that is loud (RMS > 2000) and 2.5x the median of
  the 6 frames before it; one frame earlier when that frame already rose 1.5x (the hit began
  inside it — FireRed 607/608). Gold's 2-frame click at 726 (RMS 1666) stays out.
- Music end: the title screen leaves (frame mean colour off the title's by > 40 for 5 frames); the
  clip ends at the first 10 silent frames (RMS < 50) after the last loud frame (RMS > 1500) before
  that (not after: Gold's next scene has its own jingle 2.5 s on). Gold/Silver: the song ends a second before the 84/74 s timer (the DC hum left after it stays
  out). Ruby/Sapphire/Emerald: the title leaves when the song ends (its decay is kept). FireRed/
  LeafGreen/Yellow: the 45 s timer fades the song out, the clip keeps the fade.
- None of the eight songs repeats inside its title screen (envelope autocorrelation < 0.3 for
  every lag), so the page loops the whole clip — as the game does by going back to its intro.
- Loudness: every clip to the same RMS (-18 dBFS, peaks under -0.3 dBFS) so turning the
  carousel does not jump in volume; 5 ms fade in, 30 ms fade out (no click at the loop).
- Still: the frame STILL seconds after the music starts — PRESS START shown, the legendary's glow
  lit (Emerald's at 10 s is dark, 14 s is lit).

Out (not in git, tools/deploy_ec2.sh uploads them): web/title/<game>.png (screen size) and
web/title/<game>.m4a (AAC 128 kb/s 48 kHz).
Needs: docker image pokegold-title (docker build -t pokegold-title tools/title_capture, on top of
REA_repo's mgba-headless image), numpy, Pillow.
Usage: python -X utf8 tools/make_titles.py [game ...]
"""
import argparse
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, '..', 'pokefirered', '.build', 'common15')
# the same ROM files tools/deploy_ec2.sh puts on the server
# press: START frame (None = let the intro end), frm: where to look for the music start,
# frames: how long to run, still: seconds after the music start
GAMES = {
    'yellow':    dict(rom=os.path.join(B, 'yellow', 'pokemon_yellow_kr_0.8.0.gba'), press=600, frm=600, frames=3800, still=10),
    'gold':      dict(rom=os.path.join(ROOT, '.build', 'kr', 'pokegold_kr.gbc'), press=720, frm=720, frames=6200, still=10),
    'silver':    dict(rom=os.path.join(ROOT, '.build', 'kr', 'pokesilver_kr.gbc'), press=720, frm=720, frames=6200, still=10),
    'ruby':      dict(rom=os.path.join(B, 'ruby', 'ruby_kr_mod_2.1.0.gba'), press=None, frm=3200, frames=9700, still=10),
    'sapphire':  dict(rom=os.path.join(B, 'sapphire', 'sapphire_kr_mod_2.1.0.gba'), press=None, frm=3200, frames=9700, still=10),
    'firered':   dict(rom=os.path.join(B, 'fr', 'firered_kr_mod_2.1.0.gba'), press=600, frm=600, frames=3800, still=10),
    'leafgreen': dict(rom=os.path.join(B, 'lg', 'leafgreen_kr_mod_2.1.0.gba'), press=600, frm=600, frames=3800, still=10),
    'emerald':   dict(rom=os.path.join(B, 'em', 'emerald_kr_mod_2.2.0.gba'), press=None, frm=3200, frames=9700, still=14),
}
IMAGE = 'pokegold-title'
SHOT_EVERY = 30
TARGET_RMS = 32768 * 10 ** (-18 / 20)
PEAK = 32768 * 10 ** (-0.3 / 20)


def docker(*args):
    subprocess.run(['docker', 'run', '--rm', *args], check=True, stdout=subprocess.DEVNULL)


def capture(game, g, tmp):
    rom = os.path.abspath(g['rom'])
    if not os.path.isfile(rom):
        sys.exit(f'{game}: ROM not found: {rom}')
    docker('-v', f'{os.path.dirname(rom)}:/roms:ro', '-v', f'{tmp}:/out', IMAGE,
           'capture', f'/roms/{os.path.basename(rom)}', '/out',
           str(g['press'] if g['press'] is not None else 1 << 30), str(g['frames']), str(SHOT_EVERY))
    info = dict(line.split() for line in open(os.path.join(tmp, 'info.txt')))
    rate, w, h = int(info['rate']), int(info['width']), int(info['height'])
    audio = np.fromfile(os.path.join(tmp, 'audio.raw'), dtype='<i2').reshape(-1, 2).astype(np.float64)
    video = np.fromfile(os.path.join(tmp, 'video.raw'), dtype=np.uint8).reshape(-1, h, w, 4)[..., :3]
    sig = np.fromfile(os.path.join(tmp, 'sig.raw'), dtype=np.uint8).reshape(-1, 3).astype(int)
    # frames per second of the machine: Game Boy 4194304 / 70224 cycles, Advance 16777216 / 280896
    fps = 4194304 / 70224 if w == 160 else 16777216 / 280896
    return rate, rate / fps, audio, video, sig


def cut(game, g, spf, audio, sig):
    nfr = len(sig)
    rms = np.array([np.sqrt((audio[int(i * spf):int((i + 1) * spf)] ** 2).mean()) for i in range(nfr)])
    onset = None
    for f in range(g['frm'], g['frm'] + 300):
        base = np.median(rms[f - 6:f])
        if rms[f] > 2000 and rms[f] > 2.5 * base:
            onset = f - 1 if rms[f - 1] > 1.5 * base else f
            break
    if onset is None:
        sys.exit(f'{game}: no title music start after frame {g["frm"]}')
    ref = np.median(sig[onset + 600:onset + 1200], axis=0)
    dev = np.abs(sig - ref).sum(1)
    leave = next((f for f in range(onset + 600, nfr - 5) if (dev[f:f + 5] > 40).all()), None)
    if leave is None:
        sys.exit(f'{game}: the title screen did not end within {nfr} frames')
    # loud frames up to the screen leaving only: after it comes the next scene (Gold's copyright jingle)
    last = max(f for f in range(onset, leave) if rms[f] > 1500)
    end = next((f for f in range(last + 1, nfr - 10) if (rms[f:f + 10] < 50).all()), None)
    if end is None:
        sys.exit(f'{game}: no silence after the title music')
    return onset, leave, end


def write_audio(path, rate, x, tmp):
    x = x - x.mean(0)
    rms = np.sqrt((x ** 2).mean())
    gain = min(TARGET_RMS / rms, PEAK / np.abs(x).max())
    x = x * gain
    fi, fo = int(0.005 * rate), int(0.030 * rate)
    x[:fi] *= np.linspace(0, 1, fi)[:, None]
    x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    wav = os.path.join(tmp, 'clip.wav')
    with wave.open(wav, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(np.clip(np.round(x), -32768, 32767).astype('<i2').tobytes())
    out = os.path.dirname(os.path.abspath(path))
    docker('-v', f'{tmp}:/in:ro', '-v', f'{out}:/out', IMAGE, 'ffmpeg', '-loglevel', 'error', '-y',
           '-i', '/in/clip.wav', '-ar', '48000', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
           f'/out/{os.path.basename(path)}')
    return gain


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('games', nargs='*', help='default: all eight')
    a = ap.parse_args()
    out = os.path.join(ROOT, 'web', 'title')
    os.makedirs(out, exist_ok=True)
    for game in a.games or GAMES:
        g = GAMES[game]
        with tempfile.TemporaryDirectory() as tmp:
            rate, spf, audio, video, sig = capture(game, g, tmp)
            fps = rate / spf
            onset, leave, end = cut(game, g, spf, audio, sig)
            shot = round((onset + g['still'] * fps) / SHOT_EVERY)
            Image.fromarray(video[shot]).save(os.path.join(out, f'{game}.png'), optimize=True)
            gain = write_audio(os.path.join(out, f'{game}.m4a'), rate,
                               audio[int(onset * spf):int(end * spf)], tmp)
        print(f'{game}: music frames {onset}-{end} ({(end - onset) / fps:.1f} s, title left at {leave}), '
              f'gain {gain:.2f}, still frame {shot * SHOT_EVERY}')


if __name__ == '__main__':
    main()
