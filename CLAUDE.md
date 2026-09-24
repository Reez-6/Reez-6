# myPediaclinic — Dr. Medhat APP-VIDEO Kit (CLAUDE.md)

**Read this whole file, then follow it.** You (Claude) are producing finished **in-app educational
videos** of Dr. Medhat for parents. The goal is that anyone with this pack gets the **exact same
look and rules** as the original studio. When the human gives you a raw shoot, run the pipeline in
§4 and deliver a bilingual **EN + AR** pair. Everything you need is in this folder.

---

## 1. The idea (what these videos are)

Dr. Medhat records short clips (a warning-signs list, a how-to, a myth-buster) for parents to watch
**inside the myPediaclinic app**. This is a **different job from the social reels**:

| | Social reel | **App video (this kit)** |
|---|---|---|
| Viewer | scrolling, must be hooked in 1s | **opted in** — already wants to learn |
| Goal | reach, stop the scroll | **comprehension, trust, reference** |
| Doctor | may cut to full-screen b-roll | **on screen the WHOLE time — never replaced** |
| On-screen text | key-words only | **structured cards + full bottom captions** |
| Languages | EN | **EN + AR (two deliverables)** |
| Tone | high energy | **calm, clinical, reassuring** |

**Non-negotiables:** the doctor (and the demo) stay full-frame the entire time; the graphics are a
*layer*, never a cutaway. Everything lives in the dark studio space (top) and the tablecloth space
(bottom) — never over his face or the demo. Calm clinical tone. Bilingual. Colored to the app theme.

---

## 2. Prerequisites & install (do this once)

Needs: **ffmpeg**, **Python 3** with **Pillow**, **Google Chrome** (for correct Arabic shaping), and
**one whisper backend** for transcription (`pip install sherpa-onnx soundfile` — used by `transcribe.py`;
models auto-download from GitHub releases, so it works where huggingface.co is blocked).

**macOS**
```bash
brew install ffmpeg
pip3 install --break-system-packages pillow faster-whisper       # or: mlx-whisper (Apple Silicon)
# Google Chrome: https://www.google.com/chrome/  (or `brew install --cask google-chrome`)
```
**Linux (Debian/Ubuntu)**
```bash
sudo apt install ffmpeg python3-pip google-chrome-stable
pip3 install pillow faster-whisper
```
**Windows**: install ffmpeg (ffmpeg.org) + Google Chrome + `pip install pillow faster-whisper`.

Chrome is auto-detected on all three OSes; if yours is in a custom place set `CHROME_PATH=/path/to/chrome`.
Fonts (Quicksand + Tajawal) and icons are **bundled in this folder** — nothing to install for those.

---

## 3. Tech stack (how it works)

- **ffmpeg / ffprobe** — grade the footage, gently de-wrinkle the tablecloth, and burn the overlay PNGs
  onto the video with time windows (`overlay ... enable='between(t,a,b)'`).
- **HTML + headless Chrome** renders each on-screen "state" to a transparent 1080×1920 PNG. **Arabic is
  rendered this way on purpose** — Chrome shapes/join Arabic and runs RTL correctly (Pillow does NOT).
- **whisper** (via `transcribe.py`) gives accurate wording + timings from the audio.
- **Pillow** only for small helpers (masks, demo-zoom crops).

Files in this folder:
- `app_render.py` — the overlay renderer (reads a JSON script, outputs the finished mp4). JSON-driven.
- `prep.py` — grade + tablecloth de-wrinkle + demo-zoom inset cutter + mask maker.
- `transcribe.py` — cross-platform transcription.
- `Quicksand-Bold.ttf` (Latin display) · `fonts/Tajawal-*.ttf` (Arabic).
- `icons/` — the approved best-of icon set (see §6).
- `tablecloth_mask.png` — feathered mask for the de-wrinkle step (this locked studio).
- `examples/5_signs/` — a complete reference build: `script.json` + `pip_breath.png`.

---

## 4. The pipeline (run in this order)

Let `RAW` = the raw shoot (9:16, 1080×1920).

1. **Transcribe** for accurate wording + timings, then **sanity-check** it:
   `python3 transcribe.py "RAW.mp4"`  → read the segments. Whisper mishears (it wrote "Dr. Medarth"
   for "Dr. Medhat") — fix obvious errors from context. Do NOT caption verbatim; you will condense.
2. **Grade** (gentle, must not darken):
   `python3 prep.py grade --in "RAW.mp4" --out graded.mp4`
3. **De-wrinkle the tablecloth** (this studio's sheet is creased — client asked for this):
   `python3 prep.py smooth --in graded.mp4 --mask tablecloth_mask.png --sigma 22 --until 33.5 --out graded_smooth.mp4`
   Gentle feathered blur of the sheet only, **brightness preserved (never darker)**; `--until` keeps it
   off the end card so that stays sharp. If the framing differs, regenerate the mask:
   `python3 prep.py mkmask --y0 1342 --y1 1500 --out tablecloth_mask.png` (y0 just above the tabletop
   edge, above the baby; y1 = where full blur is reached).
4. **Cut demo-zoom insets** for body signs (optional — e.g. breathing shows a magnified mannequin torso):
   `python3 prep.py inset --in graded_smooth.mp4 --t 18.2 --box x,y,w,h --out examples/<vid>/pip_breath.png`
5. **Write the script** `script.json` — one state per beat, contiguous in time, EN + AR for each. See §7.
6. **Render both languages** (default layout = the approved lower stepper):
   ```
   python3 app_render.py --video graded_smooth.mp4 --script script.json --lang en --out "<TITLE>_EN.mp4"
   python3 app_render.py --video graded_smooth.mp4 --script script.json --lang ar --out "<TITLE>_AR.mp4"
   ```
7. **Verify** — pull a frame at each state and check: right words, synced, Arabic shapes/RTL, the layer
   never covers his face or the demo, the title clears his head, boundaries are clean, end card is sharp.

**Output naming:** after the SOURCE video + language, e.g. `5 SIGNS CALL THE DOCTOR NOW_EN.mp4` / `..._AR.mp4`.

---

## 5. Design system — colours & type (the app theme)

**Colours** (defined in `app_render.py` `:root`; matched to the myPediaclinic app):
- **Purple `#7A5AF5`** — primary/structural: progress, stepper, sign labels, icon default.
- **Pink `#FF97C4`** — the ONE highlight word in the title, and the title underline.
- **Deep rose `#C5396B`** — alerts only: the "also seek care" red-flag header + dots.
- **Deep-indigo caption panel `rgba(26,20,54,.94)`**, ink text `#241E45`, cloud `#EDE9FB`.

**Type:** **Quicksand Bold** (Latin, friendly) for headings/labels; **Tajawal** for Arabic; system sans
for Latin body captions. All bundled — no downloads (CSP-safe; fonts load from this folder).

**Grade:** neutral contrast + a small midtone lift (`gamma 1.06`, `brightness +0.02`) so faces read
brighter/cleaner than raw. **Never darken** (an earlier `contrast=1.05` was rejected for reading too dark).
**Encode quality:** crf-12 slow intermediates (grade/smooth), crf-16 slow finals — don't lower it.

---

## 6. Layout (what's on screen)

- **Top:** just `Dr. Medhat Abu-Shaaban` (name only — the client dropped the "Consultant Pediatrician"
  sub-line). No logo overlay (the raw's own myPediaclinic end card closes each video).
- **Title card** (opening): centred, big, one **pink** highlight word + pink underline. It MUST end
  **before** the intro settles on his face — keep it high (top:140) so it clears his head; pin the exact
  window with a frame scan if the framing changes.
- **Lower numbered stepper** (the APPROVED layout, `--variant bottom`): the sign label + a connected
  **1→N stepper** (done + current in purple, current ringed, upcoming faint), sitting just above the caption.
- **Bottom caption bar** (deep-indigo panel over the tablecloth): the spoken line, localized, with a small
  **media chip** on the leading edge (see icons below). This is the main text; it's at the bottom so it
  swaps cleanly between EN and AR. **Do NOT float a card mid-frame** — it covered his face (rejected).
- **Media chip = app-style tinted tile.** Each sign has its own soft pastel tile + icon tone:
  fever=pink, feeding=lilac, hard-to-wake=periwinkle, diaper=blue. Body signs (breathing/ribs) use the
  **mannequin demo-zoom** image instead of an icon. Icons are a **best-of Phosphor + Fluent** set in
  `icons/` (`fever.svg feeding.svg sleepy.svg diaper.svg breath.svg`); the file + tile-bg + icon-colour
  map is `ICONSET` in `app_render.py`. To change an icon: drop a new SVG in `icons/` (from iconify.design)
  or edit `ICONSET`.
- **Red-flag grid** (for a bonus "also watch for" list): rose header pill + white chips with rose dots.

---

## 7. Scripting — the JSON (how the video is structured)

`script.json` is a **list of state objects, contiguous in time** (each `t1` == the next `t0`, so they tile
the whole clip with no gaps). Kinds:

```jsonc
// opening title (text he says as the hook). Wrap the highlight word in <b>…</b> (renders pink).
{"id":"title","t0":0.1,"t1":5.2,"kind":"title",
 "en_title":"5 signs to call the doctor <b>now</b> — not tomorrow",
 "ar_title":"٥ علامات تستدعي الاتصال بالطبيب <b>الآن</b> — وليس غدًا"}

// a numbered sign: n of total, an icon key (§6) OR "pip" for a demo-zoom, a short label + the spoken line.
{"id":"s1","t0":5.2,"t1":11.0,"kind":"sign","n":1,"total":5,"icon":"thermo",
 "en_lab":"Fever","ar_lab":"حمّى",
 "en_cap":"Fever of 38°C or more — in a baby 3 months or younger.",
 "ar_cap":"حمّى ٣٨° مئوية أو أكثر لدى رضيع عمره ٣ أشهر أو أقل."}

// a body sign that uses the mannequin demo-zoom instead of an icon:
{"id":"s4","t0":16.9,"t1":20.6,"kind":"sign","n":4,"total":5,"pip":"pip_breath.png", …}

// bonus "also watch for" list:
{"id":"rf","t0":23.1,"t1":33.3,"kind":"redflags",
 "en_head":"ALSO SEEK CARE NOW","ar_head":"اطلب الرعاية فورًا أيضًا",
 "en_chips":["Blue / grey skin","Seizures","Forceful vomiting","Blood in stool","Bulging soft spot"],
 "ar_chips":["ازرقاق الجلد","تشنّجات","قيء نافوري","دم في البراز","انتفاخ اليافوخ"]}
```
icon keys: `thermo` (fever) · `bottle` (feeding) · `eye` (hard to wake) · `drop` (diaper) · `lungs`
(breathing). The full worked example is `examples/5_signs/script.json`.

**Caption rules (this is the taste — follow them):**
- **Condense to key points**, but **keep HIS ACTUAL WORDS** for the lines you keep (his real phrasing,
  lightly trimmed) — select what to keep; don't paraphrase what you keep.
- **Don't drop the ending** of a kept sentence — the tail carries the payoff.
- **Count against a numbered title** — "5 signs" ⇒ all five must appear.
- **Sync to speech** — a state starts WHEN he says it (use the transcript timings).
- **Sanity-check the transcription** — never caption a mis-heard nonsense word.
- **End-card:** if the raw ends on its own myPediaclinic end card, let it play CLEAN — end your last state
  before the crossfade to it (pin the cut with a frame scan). Don't stack a CTA over the brand card.

---

## 8. Multilingual (EN + AR)

- Ship **two files**, `_EN` and `_AR`. Same edit, same English audio; only the on-screen text is localized
  (AR = subtitles for Arabic-speaking parents).
- Arabic is rendered by Chrome so it **shapes/joins and runs RTL** correctly; font = **Tajawal**. Use
  **Arabic-Indic numerals** (٥ ٤ ٣) — the renderer already does this for the stepper/progress.
- **Have a native speaker confirm the medical Arabic** before publishing. The example translations are
  solid MSA but medical wording should be signed off.

---

## 9. Do / Don't

**DO:** doctor full-frame always · calm-clinical · app palette (purple/pink/rose) · lower stepper ·
tinted media chips · condense but keep his words · sync to speech · de-wrinkle the sheet · title clears
his head · two clean `_EN`/`_AR` files · high-quality encode.

**DON'T:** cut away from the doctor · float a card over his face · darken the footage · paraphrase kept
lines · caption a whisper mis-hear · let the title land on his head · stack a CTA on the brand end card ·
drop the encode quality.

---

*Reference build: `examples/5_signs/` (source: "5 signs removing all stocks and effects.mp4"). Render it
with the §4 commands to reproduce the exact approved videos.*
