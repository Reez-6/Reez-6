#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Time House REEL renderer — the app_render.py approach (HTML+Chrome overlay -> ffmpeg burn-in),
restyled for Time House: brand red, no presenter name, title card + lower caption cards, EN + AR.

USAGE
  python3 timehouse_render.py --video graded.mp4 --script script.json --lang en --out OUT_EN.mp4
  python3 timehouse_render.py --video graded.mp4 --script script.json --lang ar --out OUT_AR.mp4

SCRIPT (JSON) — a list of states, contiguous in time. End the last one BEFORE the brand end card.
  {"id":"t","t0":0,"t1":3.6,"kind":"title","en_title":"Your next watch is <b>waiting</b>","ar_title":"..."}
  {"id":"c1","t0":3.6,"t1":10.8,"kind":"caption","en_lab":"TORNADO","ar_lab":"تورنادو",
   "en_cap":"Explore the collection","ar_cap":"..."}
  <b>…</b> in a title renders as a brand-red pill. *_lab is an optional small red tag above the caption.
"""
import os, json, argparse, subprocess, tempfile
from app_render import CHROME, KIT

CSS = """
@font-face{font-family:'Q';src:url('KITDIR/Quicksand-Bold.ttf');font-weight:700;}
@font-face{font-family:'T';src:url('KITDIR/fonts/Tajawal-Bold.ttf');font-weight:700;}
@font-face{font-family:'Tm';src:url('KITDIR/fonts/Tajawal-Medium.ttf');font-weight:500;}
*{margin:0;padding:0;box-sizing:border-box;-webkit-print-color-adjust:exact;}
:root{--red:#A10102;--ink:#1B1B1F;--paper:rgba(255,255,255,.96);}
html,body{background:transparent;}
.stage{position:relative;width:1080px;height:1920px;overflow:hidden;}
.title{position:absolute;left:60px;right:60px;bottom:330px;text-align:center;background:rgba(15,12,12,.55);border-radius:34px;padding:34px 30px 40px;backdrop-filter:blur(6px);}
.title .big{color:#fff;font-family:FAM;font-weight:700;font-size:84px;line-height:1.18;text-shadow:0 6px 30px rgba(0,0,0,.65);}
.title .big b{display:inline-block;background:var(--red);color:#fff;padding:0 26px 6px;border-radius:22px;text-shadow:none;box-shadow:0 12px 30px rgba(161,1,2,.45);}
.cap{position:absolute;left:60px;right:60px;bottom:250px;display:flex;flex-direction:column;align-items:center;gap:16px;}
.cap .lab{background:var(--red);color:#fff;font-family:FAM;font-weight:700;font-size:28px;LABELSPACEpadding:10px 24px;border-radius:100px;box-shadow:0 10px 24px rgba(161,1,2,.4);}
.cap .t{background:var(--paper);color:var(--ink);font-family:FAM;font-weight:700;font-size:50px;line-height:1.25;text-align:center;
        padding:22px 40px;border-radius:26px;box-shadow:0 18px 44px rgba(0,0,0,.35);BARSIDE}
"""

def stage_inner(s, ar):
    if s["kind"] == "title":
        return f'<div class="title"><div class="big">{s["ar_title" if ar else "en_title"]}</div></div>'
    lab = s.get("ar_lab" if ar else "en_lab")
    lab = f'<span class="lab">{lab}</span>' if lab else ""
    return f'<div class="cap">{lab}<span class="t">{s["ar_cap" if ar else "en_cap"]}</span></div>'

def build(video, script_path, lang, out):
    ar = (lang == "ar")
    states = json.load(open(script_path, encoding="utf-8"))
    css = (CSS.replace("KITDIR", KIT).replace("FAM", "T" if ar else "Q")
              .replace("LABELSPACE", "" if ar else "letter-spacing:.14em;")
              .replace("BARSIDE", "border-right:10px solid var(--red);" if ar else "border-left:10px solid var(--red);"))
    nosb = ["--no-sandbox"] if hasattr(os, "geteuid") and os.geteuid() == 0 else []
    tmp = tempfile.mkdtemp(prefix=f"thov_{lang}_")
    pngs = []
    for i, s in enumerate(states):
        doc = (f'<!doctype html><html{" dir=rtl" if ar else ""}><head><meta charset="utf-8"><style>{css}</style>'
               f'</head><body><div class="stage">{stage_inner(s, ar)}</div></body></html>')
        hp = os.path.join(tmp, f"ov_{i}.html"); open(hp, "w", encoding="utf-8").write(doc)
        pp = os.path.join(tmp, f"ov_{i}.png"); pngs.append(pp)
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--default-background-color=00000000", "--window-size=1080,1920", *nosb,
                        f"--screenshot={pp}", f"file://{hp}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    inputs, filt, last = [], [], "0:v"
    for i, s in enumerate(states):
        inputs += ["-i", pngs[i]]
        # stop 0.02s early so a boundary frame never shows two states (between() is inclusive)
        filt.append(f"[{last}][{i+1}:v]overlay=0:0:enable='between(t,{s['t0']:.3f},{s['t1']-0.02:.3f})'[v{i}]")
        last = f"v{i}"
    subprocess.run(["ffmpeg", "-v", "error", "-stats", "-i", video] + inputs +
                   ["-filter_complex", ";".join(filt), "-map", f"[{last}]", "-map", "0:a?",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", "-movflags", "+faststart", out, "-y"], check=True)
    print("->", out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True); ap.add_argument("--script", required=True)
    ap.add_argument("--lang", default="en", choices=["en", "ar"]); ap.add_argument("--out", required=True)
    a = ap.parse_args(); build(a.video, a.script, a.lang, a.out)
