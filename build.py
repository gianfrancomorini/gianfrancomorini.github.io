#!/usr/bin/env python3
"""
Builds the website into _site/ from the files in content/.

You normally never run this yourself: every time a change is saved on GitHub
(directly or through Pages CMS) a GitHub Action runs it and publishes the site.

To preview on your own computer:
    pip install pyyaml markdown jinja2
    python3 build.py --serve        # then open http://localhost:8000
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import markdown as md
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "_site"
IMG_DIR = ROOT / "assets" / "img"


# ───────────────────────── helpers ─────────────────────────
def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


LIVEBOOKS = load_yaml(ROOT / "scripts" / "livebooks-images.yml")


def img_url(src):
    """Local image if it exists, otherwise the original Livebooks copy."""
    if not src:
        return ""
    if src.startswith("http"):
        return src
    name = src.rsplit("/", 1)[-1]
    if src.startswith("/assets/img/") and not (IMG_DIR / name).exists():
        remote = LIVEBOOKS.get("images", {}).get(name)
        if remote:
            return LIVEBOOKS["base"] + remote
    return src


def parse_video(provider, raw):
    """Accepts a bare id ("123456"), id with hash ("123?h=abc") or a full URL."""
    raw = str(raw).strip()
    provider = (provider or "").lower()
    if "youtu" in raw or provider == "youtube":
        provider = "youtube"
        vid = raw
        if "youtu" in raw:
            u = urlparse(raw)
            if "youtu.be" in u.netloc:
                vid = u.path.strip("/")
            elif "/embed/" in u.path or "/shorts/" in u.path:
                vid = u.path.rstrip("/").split("/")[-1]
            else:
                vid = parse_qs(u.query).get("v", [""])[0]
        return {"provider": "youtube", "id": vid, "hash": "",
                "embed": f"https://www.youtube.com/embed/{vid}",
                "thumb": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "page": f"https://www.youtube.com/watch?v={vid}"}
    # vimeo
    vid, vhash = raw, ""
    if "vimeo.com" in raw:
        u = urlparse(raw)
        parts = [p for p in u.path.split("/") if p]
        nums = [p for p in parts if p.isdigit()]
        vid = nums[0] if nums else parts[-1]
        idx = parts.index(vid) if vid in parts else -1
        if 0 <= idx < len(parts) - 1 and re.fullmatch(r"[0-9a-f]{6,}", parts[idx + 1]):
            vhash = parts[idx + 1]
        vhash = parse_qs(u.query).get("h", [vhash])[0]
    elif "?h=" in raw:
        vid, vhash = raw.split("?h=", 1)
    params = "byline=0&portrait=0&badge=0&dnt=1"
    if vhash:
        params = f"h={vhash}&" + params
    return {"provider": "vimeo", "id": vid, "hash": vhash,
            "embed": f"https://player.vimeo.com/video/{vid}?{params}",
            "thumb": "",  # filled in by the browser from Vimeo (site.js)
            "page": f"https://vimeo.com/{vid}" + (f"/{vhash}" if vhash else "")}


def markdownify(text):
    if not text:
        return ""
    out = md.markdown(str(text), extensions=["extra", "sane_lists", "nl2br"])
    # links to other sites open in a new tab
    return re.sub(r'<a href="(https?://[^"]+)"',
                  r'<a href="\1" target="_blank" rel="noopener"', out)


def page_url(slug):
    slug = (slug or "").strip("/")
    return "/" if not slug else f"/{slug}"


ICONS = {
    "instagram": '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.3" cy="6.7" r="1.3" fill="currentColor"/></svg>',
    "x": '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M17.8 3h3.1l-6.8 7.7L22 21h-6.2l-4.9-6.4L5.3 21H2.2l7.2-8.3L1.9 3h6.4l4.4 5.8L17.8 3Zm-1.1 16.2h1.7L7.4 4.7H5.6l11.1 14.5Z"/></svg>',
    "vimeo": '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M22 7.4c-.1 2-1.5 4.7-4.2 8.1-2.8 3.6-5.1 5.4-7.1 5.4-1.2 0-2.2-1.1-3-3.3L6.1 11.6C5.5 9.4 4.9 8.3 4.2 8.3c-.1 0-.7.3-1.6 1L1.6 8c1-.9 2-1.8 3-2.6C6 4.2 7 3.6 7.7 3.5c1.6-.2 2.6 1 3 3.4.4 2.6.7 4.2.8 4.8.5 2.1 1 3.2 1.5 3.2.4 0 1.1-.7 2-2.1.9-1.4 1.4-2.5 1.5-3.2.1-1.2-.4-1.9-1.5-1.9-.5 0-1 .1-1.6.4 1-3.4 3-5.1 6-5 2.2.1 3.2 1.5 3.1 4.3Z"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 2H4a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2ZM8.3 18.5H5.5V9.6h2.8v8.9ZM6.9 8.4a1.6 1.6 0 1 1 0-3.3 1.6 1.6 0 0 1 0 3.3Zm11.6 10.1h-2.8v-4.3c0-1 0-2.4-1.5-2.4s-1.7 1.1-1.7 2.3v4.4H9.8V9.6h2.7v1.2c.4-.7 1.3-1.5 2.7-1.5 2.9 0 3.4 1.9 3.4 4.4v4.8Z"/></svg>',
    "youtube": '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8ZM9.7 15V9l5.8 3-5.8 3Z"/></svg>',
    "twitch": '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M4.3 2 3 5.4v13.8h4.6V22h2.6l2.7-2.8h3.8l5.3-5.3V2H4.3Zm15.8 10.9-3 3h-4.8l-2.6 2.6v-2.6H5.6V3.8h14.5v9.1ZM17.3 6.6h-1.8v5.3h1.8V6.6Zm-4.9 0h-1.8v5.3h1.8V6.6Z"/></svg>',
    "github": '<svg viewBox="0 0 16 16"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>',
    "tiktok": '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M16.6 2h-3.4v13.6a2.9 2.9 0 1 1-2-2.8V9.3a6.3 6.3 0 1 0 5.4 6.3V8.7a8 8 0 0 0 4.4 1.4V6.7a4.5 4.5 0 0 1-4.4-4.7Z"/></svg>',
    "email": '<svg viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" d="M3 5h18v14H3z M3 6l9 7 9-7"/></svg>',
}


# ───────────────────────── build ─────────────────────────
def prepare_block(b):
    b = dict(b or {})
    t = b.get("type")
    if t == "image":
        b["src_url"] = img_url(b.get("src"))
    elif t == "cards":
        for it in b.get("items") or []:
            it["image_url"] = img_url(it.get("image"))
            it["excerpt_html"] = markdownify(it.get("excerpt"))
    elif t == "videos":
        b["parsed"] = []
        for v in b.get("videos") or []:
            if isinstance(v, dict):
                pv = parse_video(v.get("provider") or b.get("provider"), v.get("id") or v.get("url"))
                pv["title"] = v.get("title", "")
            else:
                pv = parse_video(b.get("provider"), v)
                pv["title"] = ""
            b["parsed"].append(pv)
    elif t == "video":
        b["parsed"] = parse_video(b.get("provider"), b.get("id") or b.get("url"))
    elif t == "episode":
        b["parsed"] = parse_video("youtube", b.get("youtube"))
    elif t == "text":
        b["body_html"] = markdownify(b.get("body"))
    elif t == "embed":
        pass  # raw HTML, trusted (only editable by the site owner)
    return b


def build():
    site = load_yaml(CONTENT / "site.yml")
    for n in site.get("nav") or []:
        n["external"] = str(n.get("url", "")).startswith("http")
    for key in ("social_top", "social_bottom"):
        for s in site.get(key) or []:
            s["svg"] = ICONS.get(str(s.get("icon", "")).lower(), "")

    pages = []
    for p in sorted((CONTENT / "pages").glob("*.yml")):
        data = load_yaml(p)
        if data.get("draft"):
            continue
        data["url"] = page_url(data.get("slug"))
        data["blocks"] = [prepare_block(b) for b in data.get("blocks") or []]
        for i, b in enumerate(data["blocks"]):
            b["lazy"] = i > 3
        pages.append(data)

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]))
    tpl = env.get_template("page.html")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")

    for page in pages:
        dest = OUT / page["url"].strip("/") / "index.html" if page["url"] != "/" else OUT / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        active = page.get("nav_parent") or page["url"]
        dest.write_text(tpl.render(site=site, page=page, active=active,
                                   logo=img_url("/assets/img/logo_GFM.png")), encoding="utf-8")
        print("  built", page["url"])

    # 404 page
    notfound = {"title": "Page not found", "url": "/404", "description": "",
                "blocks": [prepare_block({"type": "text", "heading": "Page not found",
                                          "body": "Sorry, that page doesn't exist. [Go to the home page](/)"})]}
    (OUT / "404.html").write_text(tpl.render(site=site, page=notfound, active="",
                                             logo=img_url("/assets/img/logo_GFM.png")), encoding="utf-8")

    domain = site.get("domain", "").strip()
    if domain:
        (OUT / "CNAME").write_text(domain + "\n")
        urls = "\n".join(f"  <url><loc>https://{domain}{p['url']}</loc></url>" for p in pages)
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: https://{domain}/sitemap.xml\n")
    (OUT / ".nojekyll").write_text("")
    print(f"Done: {len(pages)} pages → {OUT}")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import http.server, functools
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Preview at http://localhost:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()
