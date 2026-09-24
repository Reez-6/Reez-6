# Time House reels

Same approach as the myPediaclinic kit (`CLAUDE.md`), restyled for Time House. Uses brand red `#A10102` from the end-card logo. No presenter name and no tablecloth step.

```
python3 prep.py grade --in RAW.mp4 --out graded.mp4
python3 timehouse_render.py --video graded.mp4 --script timehouse/<VIDEO>/script.json --lang en --out "<VIDEO>_EN.mp4"
python3 timehouse_render.py --video graded.mp4 --script timehouse/<VIDEO>/script.json --lang ar --out "<VIDEO>_AR.mp4"
```

States: `title` (the `<b>` word becomes a red pill) and `caption` (with an optional small red `*_lab` tag). End the last state before the brand end card so it plays clean. For `HANAN_SHA_` the card cuts in at 18.125s.
