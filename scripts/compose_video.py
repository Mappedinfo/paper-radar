#!/usr/bin/env python3
"""Compose the episode video: slide PNGs timed to per-scene TTS wavs + narration.wav.

Usage: python compose_video.py <project_dir>
Inputs : tts-scenes/scene-NN.wav, deck/svg/slide-NN.png (00=cover, 01..N=scenes)
Outputs: final.mp4 (1920x1080 30fps h264 + aac), cover.png
"""
import argparse
import json
import pathlib
import subprocess
import sys


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    p = pathlib.Path(args.project).resolve()
    scenes = sorted((p / "tts-scenes").glob("scene-*.wav"))
    if not scenes:
        sys.exit("no tts-scenes/*.wav found")
    slides = {i.stem.replace("slide-", ""): i for i in (p / "deck" / "svg").glob("slide-*.png")}
    entries = []
    for wav in scenes:
        idx = wav.stem.replace("scene-", "")
        png = slides.get(idx) or slides.get(f"{int(idx):02d}")
        if not png:
            sys.exit(f"missing slide for scene {idx}")
        entries.append((png.resolve(), probe(wav)))
    lst = p / "deck" / "concat.txt"
    with lst.open("w", encoding="utf-8") as f:
        for png, d in entries:
            f.write("file '{}'\nduration {:.3f}\n".format(str(png).replace("\\", "/"), d))
        f.write("file '{}'\n".format(str(entries[-1][0]).replace("\\", "/")))
    out = p / "final.mp4"
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
           "-i", str(p / "narration.wav"),
           "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-tune", "stillimage",
           "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-t", str(sum(d for _, d in entries) + 0.35*(len(entries)-1)), str(out)]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        sys.exit("ffmpeg failed:\n" + e.stderr.decode("utf-8", "ignore")[-2000:])
    cover = slides.get("00-cover") or slides.get("00")
    if cover:
        (p / "cover.png").write_bytes(cover.read_bytes())
    dur = probe(out)
    print(json.dumps({"final": str(out), "duration_seconds": round(dur, 2),
                      "scenes": len(entries)}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
