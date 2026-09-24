#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcribe.py — wording + timings from a video's audio (cross-platform, CPU).

  python3 transcribe.py "RAW.mp4"                 # Whisper medium.en (default)
  python3 transcribe.py "RAW.mp4" --model small.en

Uses sherpa-onnx (pip install sherpa-onnx soundfile) with a Silero VAD to split speech into segments,
then Whisper on each segment. Models download once from GitHub releases into ~/.cache/sherpa-whisper
(GitHub is reachable in environments where huggingface.co is blocked).
Prints "[t0-t1] text" per segment. Sanity-check the result (CLAUDE.md §4.1): whisper mishears names.
"""
import os, sys, argparse, subprocess, tempfile, tarfile, urllib.request
import numpy as np

REL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "sherpa-whisper")

def fetch(name):
    """Download a release asset into CACHE (extracting .tar.bz2) and return its local path."""
    os.makedirs(CACHE, exist_ok=True)
    if name.endswith(".tar.bz2"):
        d = os.path.join(CACHE, name[:-len(".tar.bz2")])
        if not os.path.isdir(d):
            print("downloading", name, "...", file=sys.stderr)
            tmp = os.path.join(CACHE, name); urllib.request.urlretrieve(f"{REL}/{name}", tmp)
            with tarfile.open(tmp) as t: t.extractall(CACHE)
            os.remove(tmp)
        return d
    p = os.path.join(CACHE, name)
    if not os.path.exists(p):
        urllib.request.urlretrieve(f"{REL}/{name}", p)
    return p

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video")
    ap.add_argument("--model", default="medium.en", help="tiny.en | base.en | small.en | medium.en")
    a = ap.parse_args()
    import sherpa_onnx, soundfile as sf
    md = fetch(f"sherpa-onnx-whisper-{a.model}.tar.bz2"); m = os.path.join(md, f"{a.model}-")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=m + "encoder.int8.onnx", decoder=m + "decoder.int8.onnx",
                                                     tokens=m + "tokens.txt", language="en", task="transcribe", num_threads=4)
    cfg = sherpa_onnx.VadModelConfig(); cfg.sample_rate = 16000
    v = cfg.silero_vad; v.model = fetch("silero_vad.onnx")
    v.min_silence_duration = 0.25; v.min_speech_duration = 0.25; v.max_speech_duration = 8
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
    wav = os.path.join(tempfile.mkdtemp(), "a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-ac", "1", "-ar", "16000", wav, "-y"], check=True)
    audio, sr = sf.read(wav, dtype="float32")
    for i in range(0, len(audio), v.window_size):
        vad.accept_waveform(audio[i:i + v.window_size])
    vad.flush()
    while not vad.empty():
        seg = vad.front; s = rec.create_stream(); s.accept_waveform(sr, np.array(seg.samples)); rec.decode_stream(s)
        t0 = seg.start / sr; print(f"[{t0:6.2f}-{t0 + len(seg.samples) / sr:6.2f}] {s.result.text.strip()}")
        vad.pop()

if __name__ == "__main__":
    main()
