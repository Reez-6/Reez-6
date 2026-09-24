myPediaclinic — Dr. Medhat APP-VIDEO Editor Pack
=================================================

WHAT THIS IS
  Everything needed to produce Dr. Medhat's in-app educational videos in the exact approved
  style — bilingual English + Arabic, calm-clinical, app-themed. Same result as the studio.

QUICKEST START  (recommended — let Claude do it)
  Open this folder in Claude Code, or drop the whole folder into Claude, and say:
     "Read CLAUDE.md and make the app video from <path to my raw shoot>."
  Claude reads CLAUDE.md and runs the whole pipeline (transcribe -> grade -> de-wrinkle ->
  write the script -> render EN + AR -> verify). You get two files: <TITLE>_EN.mp4 and _AR.mp4.

DO IT YOURSELF
  1. Install the tools once — see "Prerequisites & install" in CLAUDE.md (ffmpeg, Python+Pillow,
     Google Chrome, one whisper backend).
  2. Follow "The pipeline" (section 4) in CLAUDE.md.
  3. A complete worked example is in examples/5_signs/ (script.json). Render it to reproduce the
     approved videos and see how a script maps to the screen.

WHAT'S INSIDE
  CLAUDE.md             <- THE MASTER. Read first: idea, rules, colours, icons, pipeline, everything.
  app_render.py         <- renders the finished video from a JSON script (EN + AR, RTL-correct)
  prep.py               <- grade + de-wrinkle the tablecloth + cut demo-zoom insets
  transcribe.py         <- accurate wording + timings from the audio (cross-platform whisper)
  Quicksand-Bold.ttf    <- Latin display font (bundled)
  fonts/Tajawal-*.ttf   <- Arabic font (bundled)
  icons/                <- the approved sign icons (fever/feeding/sleepy/diaper/breath)
  tablecloth_mask.png   <- de-wrinkle mask for this studio's framing
  examples/5_signs/     <- reference build: script.json + demo-zoom image

IMPORTANT
  * Works on macOS, Linux and Windows. Chrome is auto-detected (or set CHROME_PATH).
  * Always have a NATIVE SPEAKER review the medical Arabic before publishing.
  * Deliver two files named after the source video: <TITLE>_EN.mp4 and <TITLE>_AR.mp4.
