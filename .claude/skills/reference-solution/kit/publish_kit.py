#!/usr/bin/env python3
"""Turn a finished video into what YouTube and LinkedIn need: chapters from the MP4 itself, paste-ready text, a thumbnail,
an optional native teaser, and a check of each platform's limits. Publishes nothing.

    publish_kit.py VIDEO_DIR/publish/meta.json                        # writes the kit beside meta.json
    publish_kit.py VIDEO_DIR/publish/meta.json --youtube-url URL      # after the upload: fills the link in everywhere

meta.json: see templates/publish.meta.example.json. {DURATION} {SLIDES} {FOLLOWUPS} and {YOUTUBE_URL} are filled in.
Run with any python3; the thumbnail step re-invokes the pdf-kit venv for Playwright.
"""
import os as _os, pathlib as _pl
_os.environ.setdefault("PANGOCAIRO_BACKEND", "fc")   # rsvg-convert: use fontconfig so the bundled Google Fonts resolve
import sys as _sys; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parent)); import paths as _paths
_os.environ.setdefault("FONTCONFIG_FILE", str(_paths.FONTS_CONF))
import argparse, html, json, os, pathlib, re, subprocess, sys

VENV = _paths.PY
LIMITS = {"YouTube title": 100, "YouTube description": 5000, "YouTube tags": 500, "LinkedIn post": 3000, "LinkedIn first comment": 1250}
FOLD_MOBILE = 140                 # third-party measurements; LinkedIn does not document the "see more" cut
PENDING = "[YouTube link: rerun publish_kit.py with --youtube-url]"

def clock(s):
    s = int(s); h, m, s = s // 3600, s // 60 % 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def chapters(mp4):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_chapters", "-show_format", "-of", "json", str(mp4)],
                         check=True, capture_output=True, text=True).stdout
    d = json.loads(out)
    return [(float(c["start_time"]), float(c["end_time"]), c["tags"]["title"]) for c in d["chapters"]], float(d["format"]["duration"])

def check_chapters(ch):
    errs = []
    if len(ch) < 3: errs.append("YouTube needs at least 3 chapters")
    if ch and ch[0][0] > 0.5: errs.append(f"the first chapter must start at 0:00, it starts at {clock(ch[0][0])}")
    errs += [f"chapter under 10 s, YouTube drops the whole list: {t!r} ({e - s:.1f} s)" for s, e, t in ch if e - s < 10]
    return errs

FONTS = (_paths.PDFKIT / "fonts/google").as_uri()
THUMB = """<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:"Plus Jakarta Sans";src:url("{fonts}/PlusJakartaSans-Variable.ttf");font-weight:200 800}}
@font-face{{font-family:"Inter";src:url("{fonts}/Inter-Variable.ttf");font-weight:100 900}}
html,body{{margin:0;width:1280px;height:720px;background:#fff;color:#202124;font-family:Inter,Roboto,sans-serif;overflow:hidden}}
.bar{{position:absolute;left:0;top:0;right:0;height:14px;background:linear-gradient(90deg,#4285F4 0 25%,#EA4335 25% 50%,#FBBC05 50% 75%,#34A853 75%)}}
.w{{position:absolute;inset:0;padding:64px 72px;display:flex;flex-direction:column;justify-content:center}}
.k{{font-family:"Plus Jakarta Sans",sans-serif;font-size:30px;font-weight:700;letter-spacing:.12em;color:#1967D2;text-transform:uppercase;margin-bottom:28px}}
.t{{font-family:"Plus Jakarta Sans",sans-serif;font-size:108px;line-height:1.04;font-weight:700;letter-spacing:-.03em}} .t em{{font-style:normal;color:#4285F4}}
.s{{font-size:42px;line-height:1.25;margin-top:34px;color:#5F6368;font-weight:500;max-width:1040px}}
.id{{position:absolute;left:72px;bottom:40px;font-size:26px;color:#5F6368;font-weight:600}}</style>
<div class="bar"></div><div class="w"><div class="k">{kicker}</div><div class="t">{title}</div><div class="s">{sub}</div></div><div class="id">{id}</div>"""

def thumbnail(t, out):
    page = THUMB.format(kicker=html.escape(t["kicker"]), title=t["title"], sub=html.escape(t["sub"]), id=html.escape(t["id"]), fonts=FONTS)
    src = out.with_suffix(".html"); src.write_text(page, encoding="utf-8")
    code = ("import sys; from playwright.sync_api import sync_playwright as P\n"
            "with P() as p:\n b=p.chromium.launch(); g=b.new_page(viewport={'width':1280,'height':720})\n"
            " g.goto('file://'+sys.argv[1]); g.evaluate('document.fonts.ready.then(()=>true)'); g.screenshot(path=sys.argv[2]); b.close()")
    subprocess.run([str(VENV), "-c", code, str(src), str(out)], check=True)
    src.unlink()

def teaser(mp4, ch, title, out):
    hit = [c for c in ch if c[2] == title]
    if not hit: sys.exit(f"teaser chapter not found: {title!r}; chapters are {[c[2] for c in ch]}")
    s, e, _ = hit[0]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.2f}", "-to", f"{e:.2f}", "-i", str(mp4), "-map", "0:v", "-map", "0:a",
                    "-map_chapters", "-1", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", str(out)], check=True)
    return e - s

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("meta"); ap.add_argument("--youtube-url")
    a = ap.parse_args()
    mpath = pathlib.Path(a.meta).resolve(); pub = mpath.parent; vid = pub.parent
    m = json.loads(mpath.read_text(encoding="utf-8"))
    if a.youtube_url:
        m["youtube_url"] = a.youtube_url; mpath.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    url = m.get("youtube_url") or PENDING
    mp4 = vid / m["mp4"]; ch, dur = chapters(mp4)
    slides = len(list((vid / "frames").glob("v-*.png"))); fu = sum(bool(re.match(r"follow-up", c[2], re.I)) for c in ch)
    def fill(s):
        for k, v in {"{DURATION}": str(round(dur / 60)), "{SLIDES}": str(slides), "{FOLLOWUPS}": str(fu), "{YOUTUBE_URL}": url}.items():
            s = s.replace(k, v)
        return s
    y, l = m["youtube"], m["linkedin"]
    chap = "\n".join(f"{clock(s)} {t}" for s, _, t in ch)
    desc = fill("\n\n".join(y["description_top"]) + "\n\nCHAPTERS\n" + chap + "\n\n" + "\n\n".join(y["description_bottom"]))
    post, comment = fill("\n\n".join(l["post"])), fill(l["first_comment"])
    title, tags = fill(y["title"]), ", ".join(y["tags"])
    errs = check_chapters(ch)
    for name, text in [("YouTube title", title), ("YouTube description", desc), ("YouTube tags", tags),
                       ("LinkedIn post", post), ("LinkedIn first comment", comment)]:
        if len(text) > LIMITS[name]: errs.append(f"{name}: {len(text)} characters, limit {LIMITS[name]}")
    if re.search(r"[<>]", title + desc): errs.append("YouTube rejects < and > in the title or description")
    hook = l["post"][0]
    if len(hook) > FOLD_MOBILE: errs.append(f"LinkedIn hook is {len(hook)} characters; the mobile fold is about {FOLD_MOBILE}")
    if errs: sys.exit("publish kit: fix these first:\n- " + "\n- ".join(errs))

    (pub / "youtube-description.txt").write_text(desc + "\n", encoding="utf-8")
    (pub / "linkedin-post.txt").write_text(post + "\n", encoding="utf-8")
    thumbnail(m["thumbnail"], pub / "thumbnail.png")
    doc = l.get("document")
    if doc and not (mpath.parent / doc["pdf"]).resolve().exists():
        print("publish kit: no PDF (the written design is Markdown only since 2026-11-25): no document attachment; link the Markdown design in the post")
        doc = None
    if doc:
        pdf = (mpath.parent / doc["pdf"]).resolve()
        pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
        size = pdf.stat().st_size / 1e6
        if pages > 300 or size > 100: sys.exit(f"publish kit: {pdf.name} is {pages} pages, {size:.0f} MB; LinkedIn's limit is 300 pages, 100 MB")
    tease = ""
    if m.get("teaser_chapter"):
        secs = teaser(mp4, ch, m["teaser_chapter"], pub / "linkedin-teaser.mp4")
        tease = f"`linkedin-teaser.mp4` ({clock(secs)}, the chapter \"{m['teaser_chapter']}\")"
    _srt = mp4.with_suffix(".srt")
    captions_step = (f"5. **Captions:** Subtitles → Add language → English → Upload file → With timing → `{_srt.name}` (sidecar captions, "
                     f"nothing is burned in; viewers can toggle and auto-translate them)." if _srt.exists() else
                     "5. Captions are burned in: **do not upload an SRT**, it would draw over the band.")
    (pub / "youtube.md").write_text(f"""# YouTube kit: {title}

Generated by `publish_kit.py` from `meta.json` and the MP4's own chapters; edit `meta.json`, not this file.

| Field | Value |
|---|---|
| File | `{mp4.name}` ({mp4.stat().st_size / 1e6:.0f} MB, {clock(dur)}, {len(ch)} chapters) |
| Title ({len(title)}/100) | {title} |
| Description ({len(desc)}/5000) | `pbcopy < youtube-description.txt` |
| Thumbnail | `thumbnail.png` (1280x720) |
| Tags ({len(tags)}/500) | {tags} |
| Playlist | {y["playlist"]} |

## Upload, in YouTube Studio

1. **Once per channel:** verify the phone at youtube.com/verify. Without it, uploads over 15 minutes and custom thumbnails are blocked.
2. Create → Upload videos → `{mp4.name}`. Paste the title and description. Upload the thumbnail. Add to the playlist.
3. Audience: not made for kids. Show more: tags, language English, category Education, standard licence, allow embedding.
4. **AI use / altered content:** answer **Yes**. The voices are synthetic and could pass for real people; the description says so too.
{captions_step}
6. Visibility: **Unlisted**, then Save. Wait until 1080p has processed. Check the chapters on the seek bar, the thumbnail, and a minute at the start and the end.
7. Switch to **Public**. Pin a comment with the repository link. Add an end screen pointing at the playlist.
8. Then, with the URL: `publish_kit.py {mpath.name} --youtube-url https://youtu.be/…`, post LinkedIn (`linkedin.md`), and fill the row in `solutions/VIDEOS.md`.
""", encoding="utf-8")
    if doc:
        media = f"""**Media: attach the reference design.** In the post composer, More (+) → Add a document → `{os.path.relpath(pdf, pub)}` ({pages} pages, {size:.1f} MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **{doc["title"]}**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed."""
    else:
        media = "**Media.** The full video is too long to upload natively (about 15 minutes at most, from a computer), so it goes by link, and its preview shows the thumbnail." + (f" Optional instead: attach {tease} as the post's native video, keeping the link in the text." if tease else "")
    (pub / "linkedin.md").write_text(f"""# LinkedIn kit: {title}

Post from a computer, after the YouTube video is public. {"The link is still pending: rerun with --youtube-url." if url == PENDING else ""}

**Post** ({len(post)}/3000; hook {len(hook)} characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
{post}
```

**First comment** ({len(comment)}/1250):

```text
{comment}
```

{media}
""", encoding="utf-8")
    print(f"publish kit → {pub}\n  title {len(title)}/100 · description {len(desc)}/5000 · post {len(post)}/3000 · hook {len(hook)} · {len(ch)} chapters · {clock(dur)}")

if __name__ == "__main__":
    main()
