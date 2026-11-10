# Maintaining the Third + Grove brand guide

The guide is one self-contained `index.html`, including its inline fonts, photos,
logo vectors, animations, and interaction code. Keep edits surgical. `source/`
is the original artifact export for reference and is never deployed.

## Replace an asset

1. Work on a branch and replace the relevant file under `assets/`, keeping the
   filename when possible. For renamed files, update every reference in
   `index.html` and the recipes in `scripts/build_downloads.py`.
2. The page deliberately retains inline previews. Update the corresponding inline
   font, photo, or vector too if its preview must change; replacing the standalone
   asset only changes the downloaded file. Keep the single-page format.
3. Rebuild the ZIPs and refresh the visible size labels next to affected download
   links in `index.html`. Generated cards use `LOCKUP_DOWNLOADS`, `ICON_DOWNLOADS`,
   and `FAMILY_DOWNLOADS`; the lightbox uses `PHOTO_DOWNLOADS`. Sizes use decimal
   KB (bytes / 1,000) and MB (bytes / 1,000,000), rounded to one decimal place.

## Rebuild packages

Python 3.10+ is sufficient; no packages need installing.

```sh
python3 scripts/build_downloads.py
```

This intentionally overwrites `downloads/*.zip` from `assets/`. The recipes retain
all 31 package names and internal paths, including `Managed Services` photography
folders and the video poster names. The brand kit includes logos, fonts, icons,
animations, palette, and photos. Brand videos have a separate ZIP.

To prove the recipes match existing packages without changing them:

```sh
python3 scripts/build_downloads.py --output-dir /tmp/tagbrand-download-check --verify
```

The verifier compares ZIP entry paths and per-file SHA-256; ZIP ordering,
compression, and timestamps do not need to be byte-identical.

## Update the manifest

After an intentional asset, ZIP, library, or page change, refresh the existing
entries and add any new assets/downloads. Review this diff so unexpected changes
are not silently accepted. Run from the repository root:

```sh
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

path = Path('manifest.json')
manifest = json.loads(path.read_text())
for folder in ('assets', 'downloads'):
    for file in sorted(Path(folder).rglob('*')):
        if file.is_file():
            manifest['files'].setdefault(file.as_posix(), {'role': 'Brand asset or download'})
for name, entry in manifest['files'].items():
    data = Path(name).read_bytes()
    entry['bytes'] = len(data)
    entry['sha256'] = hashlib.sha256(data).hexdigest()
path.write_text(json.dumps(manifest, indent=2) + '\n')
PY
python3 scripts/check_manifest.py
```

For a deliberate deletion, remove its manifest entry and all page/package
references explicitly. Keep the original `source/` export untouched.

## Preview and publish

```sh
mkdir -p _site
cp index.html 404.html robots.txt _site/
cp -R assets downloads _site/
python3 scripts/check_manifest.py
python3 scripts/check_site.py _site
python3 -m http.server 8765 --directory _site
```

For a fresh stage, remove the old `_site/` directory first so deleted files do not
linger. Visit http://localhost:8765 and check navigation, motion, downloads, and
the lightbox on desktop and mobile.

Open a PR. Merging to `main` deploys only `index.html`, `404.html`, `robots.txt`,
`assets/`, and `downloads/` through `.github/workflows/pages.yml`. Deployment can
also be started with the workflow's manual trigger. `source/`, `scripts/`, `docs/`,
and `manifest.json` are not published.

The page has `noindex, nofollow`. Keep `robots.txt` allowing access so crawlers
can read that directive.

## Domain and HTTPS

The Pages custom domain is `brand.thirdandgrove.com`. Cloudflare must have a
DNS-only CNAME named `brand` targeting `thirdandgrove.github.io`. Verify the parent
domain in the organization's Pages settings and permit `letsencrypt.org` in CAA
when the parent domain uses CAA.

Run this idempotent command after DNS propagates:

```sh
./scripts/configure_pages.sh
```

It enables workflow-based Pages, preserves the custom domain, polls DNS and the
certificate for up to 20 minutes, and enforces HTTPS once GitHub reports an
approved certificate. A timeout prints the same command to run later. Requires
an authenticated `gh` CLI and `dig`.

## Rollback

Revert the shipping PR to restore the previous deployed revision when one exists.
This repository's initial baseline predates the workflow; reverting the first
shipping PR removes automatic deployment and does not erase an already-published
site. To immediately take the site down:

```sh
gh api -X DELETE repos/thirdandgrove/tagbrand/pages
```

Re-enable it later with `./scripts/configure_pages.sh`, then run the deployment
workflow from `main`.
