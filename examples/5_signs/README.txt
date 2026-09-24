Reference build for the App-Video Kit.
Source shoot: "5 signs removing all stocks and effects.mp4" (9:16, ~37s, Dr. Medhat + nurse + baby mannequin).
Reproduce (from the pack root, after grading + de-wrinkling the raw per CLAUDE.md §4):
  python3 app_render.py --video graded_smooth.mp4 --script examples/5_signs/script.json --lang en --out "5 SIGNS CALL THE DOCTOR NOW_EN.mp4"
  python3 app_render.py --video graded_smooth.mp4 --script examples/5_signs/script.json --lang ar --out "5 SIGNS CALL THE DOCTOR NOW_AR.mp4"
pip_breath.png is the mannequin demo-zoom used by sign 4 (breathing).
