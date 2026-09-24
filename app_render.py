#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myPediaclinic APP-VIDEO renderer  (calm-clinical, bilingual EN/AR, doctor always full-frame)

Renders the on-screen layer (title / sign cards + progress + PIP / red-flag grid / captions)
via HTML+Chrome so ARABIC shapes and runs RTL correctly, then burns it onto graded footage.

USAGE
  python3 app_render.py --video graded.mp4 --script script.json --lang en --out OUT_EN.mp4
  python3 app_render.py --video graded.mp4 --script script.json --lang ar --out OUT_AR.mp4

SCRIPT (JSON)  — a list of state objects, contiguous in time so they tile the clip:
  {"id":"s1","t0":5.2,"t1":11.0,"kind":"sign","n":1,"icon":"thermo",
   "en_lab":"Fever","ar_lab":"حمّى",
   "en_cap":"Fever of 38°C ...","ar_cap":"حمّى ٣٨° ..."}
  kinds: "title" (en_title/ar_title) · "sign" (n, icon OR pip, *_lab, *_cap) ·
         "redflags" (en_head/ar_head, en_chips/ar_chips) · "cta" (en_title/ar_title)
  icon keys -> app-tinted chips (see ICONSET): thermo(fever) | bottle(feeding) | eye(hard-to-wake)
         | drop(diaper) | lungs(breathing).  Use "pip":"file.png" instead for a mannequin demo-zoom.
Fonts + icons/ load from THIS folder; "pip" images resolve next to the script.
Default layout is the APPROVED lower stepper (--variant bottom). Chrome auto-detected (or set CHROME_PATH).
"""
import os, sys, json, argparse, subprocess, tempfile, shutil

KIT = os.path.dirname(os.path.abspath(__file__))

def _find_chrome():
    """Locate a headless-capable Chromium browser on macOS / Linux / Windows.
    Override with the CHROME_PATH env var if yours is elsewhere."""
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("Chrome/Chromium not found. Install Google Chrome, or set CHROME_PATH to its executable.")
CHROME = _find_chrome()

# Best-of icon set (Phosphor + Fluent), each sign in its own app-style tinted chip: (svg file, tile bg, icon color).
ICON_DIR = os.path.join(KIT, "icons")
ICONSET = {
    "thermo": ("fever.svg",   "#FCE1EC", "#D6417B"),   # fever    — pink tile
    "bottle": ("feeding.svg", "#EAE4FC", "#7A5AF5"),   # feeding  — lilac tile
    "eye":    ("sleepy.svg",  "#E1E7FC", "#5566DB"),   # hard to wake — periwinkle tile
    "drop":   ("diaper.svg",  "#DAECFB", "#3E8ED0"),   # wet diapers — blue tile
    "lungs":  ("breath.svg",  "#DCEFF6", "#2F93B8"),   # breathing (fallback) — soft-blue tile
}
BREATH_TINT = "#C7DCE8"   # tile border for the breathing demo-zoom chip
def load_icon(key):
    fn, bg, col = ICONSET.get(key, ICONSET["drop"])
    return open(os.path.join(ICON_DIR, fn), encoding="utf-8").read(), bg, col

CSS = """
@font-face{font-family:'Q';src:url('KITDIR/Quicksand-Bold.ttf');font-weight:700;}
@font-face{font-family:'T';src:url('KITDIR/fonts/Tajawal-Bold.ttf');font-weight:700;}
@font-face{font-family:'Tm';src:url('KITDIR/fonts/Tajawal-Medium.ttf');font-weight:500;}
*{margin:0;padding:0;box-sizing:border-box;-webkit-print-color-adjust:exact;}
:root{--ink:#241E45;--teal:#7A5AF5;--blue:#6D4AE8;--berry:#C5396B;--pink:#FF97C4;--cloud:#EDE9FB;}
html,body{background:transparent;}
.stage{position:relative;width:1080px;height:1920px;overflow:hidden;}
.logo{position:absolute;top:42px;left:50px;} .logo img{height:70px;display:block;filter:drop-shadow(0 4px 14px rgba(0,0,0,.45));}
.name{position:absolute;top:56px;left:52px;color:#fff;text-align:left;text-shadow:0 2px 10px rgba(0,0,0,.6);}
.name .a{font-family:FAM;font-weight:700;font-size:30px;line-height:1.1;}
.name .b{font-family:FBODY;font-size:23px;opacity:.82;margin-top:2px;}
.prog{position:absolute;top:52px;right:48px;text-align:right;}
.prog .p{display:inline-flex;align-items:center;gap:12px;background:rgba(10,18,30,.6);border:1px solid rgba(255,255,255,.16);border-radius:100px;padding:12px 22px;backdrop-filter:blur(4px);}
.prog .lab{font-family:FAM;font-weight:700;color:#fff;font-size:28px;letter-spacing:.05em;}
.dots{display:flex;gap:10px;} .dot{width:14px;height:14px;border-radius:50%;background:rgba(255,255,255,.3);}
.dot.on{background:var(--teal);box-shadow:0 0 0 4px rgba(122,90,245,.2);}
.subtag{margin-top:12px;display:inline-block;background:var(--teal);color:#fff;font-family:FAM;font-weight:700;font-size:26px;padding:8px 20px;border-radius:100px;box-shadow:0 8px 20px rgba(122,90,245,.35);}
.pip{position:absolute;top:470px;right:52px;width:250px;background:#fff;border-radius:26px;padding:22px 20px 18px;box-shadow:0 20px 46px rgba(0,0,0,.4);text-align:center;}
.pip svg{width:120px;height:120px;} .pip img{width:210px;height:auto;border-radius:16px;display:block;}
.pip .cap{margin-top:10px;color:var(--ink);font-family:FAM;font-weight:700;font-size:28px;}
.pip .tag{position:absolute;top:-15px;left:20px;background:var(--teal);color:#fff;font-family:FAM;font-weight:700;font-size:22px;letter-spacing:.06em;padding:6px 16px;border-radius:100px;}
.capbar{position:absolute;left:50px;right:50px;bottom:112px;background:rgba(26,20,54,.94);border-radius:28px;padding:24px 32px;box-shadow:0 20px 50px rgba(0,0,0,.42);display:flex;gap:26px;align-items:center;CAPDIR}
.capbar .media{flex:none;width:104px;height:104px;border-radius:22px;background:#fff;display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:0 8px 20px rgba(0,0,0,.35);border:2px solid rgba(255,255,255,.4);}
.capbar .media svg{width:60px;height:60px;} .capbar .media img{width:104px;height:104px;object-fit:cover;}
.capbar .t{flex:1;color:#fff;font-family:FBODY;font-size:43px;line-height:1.26;CAPALIGN}
.center{position:absolute;left:70px;right:70px;top:140px;text-align:center;}
.center .big{color:#fff;font-family:FAM;font-weight:700;font-size:86px;line-height:1.12;letter-spacing:-.01em;text-shadow:0 6px 30px rgba(0,0,0,.6);} .center .big b{color:var(--pink);font-weight:700;}
.center .rule{width:130px;height:8px;border-radius:6px;background:var(--pink);margin:34px auto 0;}
.cta-h{margin-top:30px;display:inline-block;background:#fff;color:var(--ink);font-family:FAM;font-weight:700;font-size:40px;padding:16px 34px;border-radius:100px;box-shadow:0 14px 34px rgba(0,0,0,.35);}
.rf{position:absolute;left:56px;right:56px;top:232px;text-align:center;}
.rf .head{display:inline-block;background:var(--berry);color:#fff;font-family:FAM;font-weight:700;font-size:32px;letter-spacing:.08em;padding:12px 26px;border-radius:100px;box-shadow:0 10px 26px rgba(197,57,107,.35);}
.rf .grid{margin-top:26px;display:flex;flex-wrap:wrap;gap:16px;justify-content:center;RFDIR}
.rf .chip{background:rgba(255,255,255,.96);color:var(--ink);font-family:FBODY;font-weight:700;font-size:36px;padding:16px 26px;border-radius:18px;box-shadow:0 10px 26px rgba(0,0,0,.3);display:flex;align-items:center;gap:12px;}
.rf .chip .d{width:14px;height:14px;border-radius:50%;background:var(--berry);flex:none;}
/* v2 lower stepper */
.stepwrap{position:absolute;left:50px;right:50px;bottom:302px;display:flex;flex-direction:column;align-items:center;gap:18px;}
.steplabel{color:#fff;font-family:FAM;font-weight:700;font-size:34px;LABELSPACEtext-shadow:0 2px 12px rgba(0,0,0,.65);}
.stepper{display:flex;align-items:center;justify-content:center;STEPDIR}
.node{width:66px;height:66px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:FAM;font-weight:700;font-size:34px;box-shadow:0 6px 16px rgba(0,0,0,.35);}
.node.done{background:var(--teal);color:#fff;}
.node.cur{background:var(--teal);color:#fff;box-shadow:0 0 0 6px rgba(122,90,245,.28),0 8px 18px rgba(0,0,0,.4);}
.node.todo{background:rgba(255,255,255,.16);color:rgba(255,255,255,.72);}
.conn{width:38px;height:6px;background:rgba(255,255,255,.24);}
.conn.done{background:var(--teal);}
"""

def stage_inner(s, lang, script_dir, variant="top"):
    ar = (lang == "ar")
    nm_a = "د. مدحت أبو شعبان" if ar else "Dr. Medhat Abu-Shaaban"
    parts = [f'<div class="name"><div class="a">{nm_a}</div></div>']
    k = s["kind"]
    if k in ("title", "cta"):
        inner = f'<div class="big">{s["ar_title" if ar else "en_title"]}</div><div class="rule"></div>'
        if k == "cta":
            inner += f'<div class="cta-h">{s.get("handle","@mypediaclinic")}</div>'
        parts.append(f'<div class="center">{inner}</div>')
    elif k == "sign":
        n = s["n"]
        prognum = "١٢٣٤٥٦٧٨٩"[n-1] if ar else str(n)
        tot = s.get("total", 5); tota = "٥" if (ar and tot==5) else str(tot)
        proglab = f'علامة {prognum} / {tota}' if ar else f'SIGN {n} / {tot}'
        dots = "".join(f'<span class="dot{" on" if i < n else ""}"></span>' for i in range(tot))
        lab = s["ar_lab" if ar else "en_lab"]
        if variant == "top":
            parts.append(f'<div class="prog"><span class="p"><span class="lab">{proglab}</span>'
                         f'<span class="dots">{dots}</span></span><br><span class="subtag">{lab}</span></div>')
        else:  # v2 — numbered stepper in the lower zone, above the caption bar
            nodes = []
            for i in range(1, tot+1):
                num = "١٢٣٤٥٦٧٨٩"[i-1] if ar else str(i)
                cls = "done" if i < n else ("cur" if i == n else "todo")
                nodes.append(f'<span class="node {cls}">{num}</span>')
                if i < tot:
                    nodes.append(f'<span class="conn {"done" if i < n else ""}"></span>')
            parts.append(f'<div class="stepwrap"><div class="steplabel">{lab}</div>'
                         f'<div class="stepper">{"".join(nodes)}</div></div>')
        if s.get("pip"):
            pth = s["pip"] if os.path.isabs(s["pip"]) else os.path.join(script_dir, s["pip"])
            media = f'<span class="media" style="border-color:{BREATH_TINT}"><img src="{pth}"></span>'
        else:
            svgmarkup, bg, col = load_icon(s.get("icon", "drop"))
            media = (f'<span class="media" style="background:{bg};color:{col};border-color:{col}55">'
                     f'{svgmarkup}</span>')
        parts.append(f'<div class="capbar">{media}'
                     f'<span class="t">{s["ar_cap" if ar else "en_cap"]}</span></div>')
    elif k == "redflags":
        head = s["ar_head" if ar else "en_head"]
        chips = "".join(f'<div class="chip"><span class="d"></span>{c}</div>'
                        for c in s["ar_chips" if ar else "en_chips"])
        parts.append(f'<div class="rf"><span class="head">{head}</span><div class="grid">{chips}</div></div>')
    return "\n".join(parts)

def build(video, script_path, lang, out, variant="bottom"):
    ar = (lang == "ar")
    states = json.load(open(script_path, encoding="utf-8"))
    script_dir = os.path.dirname(os.path.abspath(script_path))
    css = (CSS.replace("KITDIR", KIT)
              .replace("FAM", "T" if ar else "Q")
              .replace("FBODY", "Tm" if ar else "system-ui,'Segoe UI',sans-serif")
              .replace("CAPDIR", "direction:rtl;" if ar else "")
              .replace("CAPALIGN", "text-align:right;" if ar else "text-align:center;")
              .replace("RFDIR", "direction:rtl;" if ar else "")
              .replace("STEPDIR", "direction:rtl;" if ar else "")
              .replace("LABELSPACE", "" if ar else "letter-spacing:.14em;text-transform:uppercase;"))
    pngdir = tempfile.mkdtemp(prefix=f"appov_{lang}_")
    pngs = []
    for i, s in enumerate(states):
        doc = (f'<!doctype html><html{" dir=rtl" if ar else ""}><head><meta charset="utf-8">'
               f'<style>{css}</style></head><body><div class="stage">{stage_inner(s,lang,script_dir,variant)}</div></body></html>')
        hp = os.path.join(pngdir, f"ov_{i}.html"); open(hp, "w", encoding="utf-8").write(doc)
        pp = os.path.join(pngdir, f"ov_{i}.png"); pngs.append(pp)
        # Chrome refuses to start as root (Linux containers) unless the sandbox is disabled.
        nosb = ["--no-sandbox"] if hasattr(os, "geteuid") and os.geteuid() == 0 else []
        subprocess.run([CHROME,"--headless","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1",
                        "--default-background-color=00000000","--window-size=1080,1920", *nosb,
                        f"--screenshot={pp}", f"file://{hp}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    inputs, filt, last = [], [], "0:v"
    for i, s in enumerate(states):
        inputs += ["-i", pngs[i]]; nxt = f"v{i}"
        # end 0.02s (< 1 frame @30fps) before t1 so the boundary frame belongs to the NEXT state only —
        # otherwise between() is inclusive on both ends and two overlays double-draw for one frame (a flash).
        filt.append(f"[{last}][{i+1}:v]overlay=0:0:enable='between(t,{s['t0']:.3f},{s['t1']-0.02:.3f})'[{nxt}]")
        last = nxt
    cmd = (["ffmpeg","-v","error","-stats","-i",video] + inputs +
           ["-filter_complex",";".join(filt),"-map",f"[{last}]","-map","0:a?",
            "-c:v","libx264","-preset","slow","-crf","16","-pix_fmt","yuv420p",
            "-c:a","copy","-movflags","+faststart", out, "-y"])
    subprocess.run(cmd, check=True); print("->", out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True); ap.add_argument("--script", required=True)
    ap.add_argument("--lang", default="en", choices=["en","ar"]); ap.add_argument("--out", required=True)
    ap.add_argument("--variant", default="bottom", choices=["top","bottom"],
                    help="bottom = numbered stepper in lower zone (APPROVED v2, default); top = old top-right pill (v1, deprecated)")
    a = ap.parse_args(); build(a.video, a.script, a.lang, a.out, a.variant)
