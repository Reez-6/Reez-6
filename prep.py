#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prep.py — footage prep for myPediaclinic app videos.

grade   : gentle calm-clinical grade
          python3 prep.py grade --in raw.mp4 --out graded.mp4
inset   : cut a demo-zoom PIP inset (magnify a region of the mannequin)
          python3 prep.py inset --in graded.mp4 --t 18.2 --box 300,1200,350,270 --out pip_breath.png
mkmask  : make a feathered vertical mask (transparent above y0, opaque below y1) for `smooth`
          python3 prep.py mkmask --y0 1420 --y1 1520 --out tablecloth_mask.png
smooth  : gently BLUR a masked region (e.g. a wrinkled tablecloth) — brightness preserved, NOT darkened.
          Feathered by the mask; `--until` limits it to the talking-head so an end card stays sharp.
          python3 prep.py smooth --in graded.mp4 --mask tablecloth_mask.png --sigma 16 --until 33.5 --out graded_smooth.mp4

Pipeline for the standard locked-studio setup (doctor + nurse + baby-mannequin table):
  grade  ->  smooth (de-wrinkle the sheet)  ->  app_render.py  (EN + AR)
"""
import os, sys, argparse, subprocess
# Clean, NON-darkening grade: lift midtones (gamma>1) + tiny brightness, neutral contrast.
# (The old contrast=1.05 deepened the already-dark studio — client said it read too dark.)
GRADE = "eq=contrast=1.0:brightness=0.02:saturation=1.05:gamma=1.06"
CRF_INT = "12"   # high-quality intermediate (grade/smooth) so generations don't soften
W, H = 1080, 1920

def grade(inp, out):
    subprocess.run(["ffmpeg","-v","error","-stats","-i",inp,"-vf",GRADE,
                    "-c:v","libx264","-preset","slow","-crf",CRF_INT,"-pix_fmt","yuv420p",
                    "-c:a","copy","-movflags","+faststart",out,"-y"], check=True)
    print("graded ->", out)

def inset(inp, t, box, out, size=360):
    x,y,w,h = [int(v) for v in box.split(",")]
    subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",inp,"-frames:v","1",
                    "-vf",f"crop={w}:{h}:{x}:{y},scale={size}:-1",out,"-y"], check=True)
    print("inset ->", out)

def mkmask(y0, y1, out):
    from PIL import Image
    m = Image.new("L", (W, H), 0); px = m.load()
    for y in range(H):
        if   y <= y0: v = 0
        elif y >= y1: v = 255
        else:
            t = (y - y0) / (y1 - y0); v = int(255 * (t*t*t*(t*(t*6-15)+10)))  # quintic smootherstep (edge-free)
        for x in range(W): px[x, y] = v
    m.save(out); print("mask ->", out)

def smooth(inp, mask, sigma, until, out):
    enable = f":enable='between(t,0,{until})'" if until else ""
    fc = (f"[0:v]split=2[a][b];[b]gblur=sigma={sigma}[bb];"
          f"[bb][1:v]alphamerge[bm];[a][bm]overlay=0:0{enable}[v]")
    subprocess.run(["ffmpeg","-v","error","-stats","-i",inp,"-i",mask,"-filter_complex",fc,
                    "-map","[v]","-map","0:a?","-c:v","libx264","-preset","slow","-crf",CRF_INT,
                    "-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart",out,"-y"], check=True)
    print("smoothed ->", out)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    ap = argparse.ArgumentParser(); ap.add_argument("mode")
    if mode == "grade":
        ap.add_argument("--in",dest="inp",required=True); ap.add_argument("--out",required=True)
        a=ap.parse_args(); grade(a.inp,a.out)
    elif mode == "inset":
        ap.add_argument("--in",dest="inp",required=True); ap.add_argument("--t",required=True)
        ap.add_argument("--box",required=True); ap.add_argument("--out",required=True)
        a=ap.parse_args(); inset(a.inp,a.t,a.box,a.out)
    elif mode == "mkmask":
        ap.add_argument("--y0",type=int,default=1342); ap.add_argument("--y1",type=int,default=1500)
        ap.add_argument("--out",required=True); a=ap.parse_args(); mkmask(a.y0,a.y1,a.out)
    elif mode == "smooth":
        ap.add_argument("--in",dest="inp",required=True); ap.add_argument("--mask",required=True)
        ap.add_argument("--sigma",type=float,default=16); ap.add_argument("--until",type=float,default=0)
        ap.add_argument("--out",required=True)
        a=ap.parse_args(); smooth(a.inp,a.mask,a.sigma,a.until,a.out)
    else:
        print(__doc__); sys.exit(1)
