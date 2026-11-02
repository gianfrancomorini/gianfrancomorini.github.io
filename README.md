# gianfrancomorini.com

The website of Gian Franco Morini — moved off Livebooks to **free** hosting on GitHub Pages.

| What | Where | Cost |
|---|---|---|
| Hosting | GitHub Pages (this repository) | Free |
| Editor | Pages CMS — <https://app.pagescms.org> | Free |
| Domain DNS | Aruba (unchanged registrar) | what you pay now |
| gianfrancomorini.xyz | GoDaddy → forwards to .com | what you pay now |

---

## Editing the site (no code)

1. Go to **<https://app.pagescms.org>** and sign in with GitHub.
2. Open this repository.
3. **Site settings & menu** — name, phone, email, social icons and the left menu (drag to reorder, add/remove items).
4. **Pages** — each page is a list of **sections** you can add, remove and drag:
   - *Image / GIF* — upload, choose left/centre/right and a width
   - *Video gallery* — paste Vimeo or YouTube numbers or links; style *grid* (plays in place) or *popup* (thumbnails open a lightbox, like Fashion)
   - *Single video*, *Podcast episode*, *Text*, *Cards* (Books), *Button*, *3D scene (Spline)*, *Contact*, *Custom HTML*, *Empty space*
5. Press **Save**. The site republishes itself in about a minute.

**Add a new page:** Pages → *Add an entry* → give it a title and address (e.g. `music`) → add sections → Save. Then add it to the menu in *Site settings & menu* with the link `/music`.

You can also edit the files directly on github.com: everything lives in `content/` (plain, commented YAML files).

### Preview on your Mac (optional)

```bash
pip3 install pyyaml markdown jinja2
python3 build.py --serve      # open http://localhost:8000
```

---

## How it's built

```
content/site.yml        name, contact, social icons, menu
content/pages/*.yml     one file per page, a list of sections
templates/              HTML for the page and each section type
assets/                 style.css, site.js, images (assets/img)
build.py                turns content/ into the website (_site/)
.github/workflows/      publish on every change + one-time Livebooks image import
.pages.yml              Pages CMS editor setup
```

---

## Going live (one-time)

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. **Actions → "Import images from Livebooks" → Run workflow** (copies every image into the repo; do this *before* cancelling Livebooks).
3. **Settings → Pages → Custom domain:** `www.gianfrancomorini.com` → Save.
4. **Aruba DNS** (Pannello di controllo → Gestione DNS for gianfrancomorini.com). Replace the Livebooks records — **leave MX/email records alone**:

   | Type | Name | Value |
   |---|---|---|
   | A | @ (gianfrancomorini.com) | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | gianfrancomorini.github.io. |

5. Wait for DNS (minutes to a few hours), then tick **Enforce HTTPS** in Settings → Pages.
6. **GoDaddy (.xyz):** Domain → *Forwarding* → forward `gianfrancomorini.xyz` to `https://www.gianfrancomorini.com`, *Permanent (301)*. If it already forwards, nothing to do.
7. Check every page on phone and desktop, then cancel Livebooks.
