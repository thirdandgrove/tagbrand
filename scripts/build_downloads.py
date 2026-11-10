#!/usr/bin/env python3
"""Rebuild the supplied download packages from assets, preserving internal paths."""
import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("Agentic", "Strategy", "Creative", "Technology", "ManagedServices")
LOCKUPS = ("TAG_Primary_Horizontal", "TAG_Primary_Stacked", "TAG_Secondary", "TAG_Favicon")


def recipes():
    packages = {}

    def add(name, pairs):
        packages[name + ".zip"] = list(pairs)

    def tree(folder, prefix):
        return [(prefix + "/" + p.relative_to(ROOT / "assets" / folder).as_posix(), p)
                for p in sorted((ROOT / "assets" / folder).rglob("*")) if p.is_file()]

    logos = tree("logos", "TAG_Logos")
    add("TAG_Logos", logos)
    for lockup in LOCKUPS:
        add(lockup, [(lockup + "/" + p.name, p) for _, p in logos if p.stem.startswith(lockup + "_")])
    fonts = tree("fonts", "FK_Grotesk")
    add("FK_Grotesk_woff2", fonts)
    for weight, styles in {"Light": ("Light", "LightItalic"), "Regular": ("Regular", "Italic"),
                           "Medium": ("Medium", "MediumItalic")}.items():
        prefix = "FK_Grotesk_" + weight
        add(prefix, [(prefix + "/FKGrotesk-" + style + ".woff2",
                      ROOT / "assets/fonts" / ("FKGrotesk-" + style + ".woff2")) for style in styles])
    for fmt in ("SVG", "MP4"):
        pairs = tree("icons/" + fmt, "TG_Service_Icons/" + fmt)
        add("TG_Service_Icons_" + fmt, pairs)
        for family in (*FAMILIES, "Services"):
            subset = [(family + "_" + fmt + "/" + p.name, p)
                      for _, p in pairs if p.name.startswith(family + "_")]
            if subset:
                add(family + "_" + fmt, subset)
    photos = []
    for family in FAMILIES:
        display = "Managed Services" if family == "ManagedServices" else family
        pairs = tree("photography/" + display, "TG_Photography/" + display)
        add("TG_Photography_" + family, pairs)
        photos.extend(pairs)
    add("TG_Photography", photos)
    palette = tree("palette", "TG_Palette")
    add("TG_Palette", palette)
    add("TG_Brand_Video", [("TG_Brand_Video/posters/family-" + p.name, p)
                           for _, p in tree("photography/posters", "unused")]
        + tree("video", "TG_Brand_Video"))
    kit = []
    for pairs, old, new in ((logos, "TAG_Logos", "Logos"),
                            (photos, "TG_Photography", "Photography"),
                            (palette, "TG_Palette", "Palette"),
                            (fonts, "FK_Grotesk", "Fonts")):
        kit.extend((name.replace(old, "TG_Brand_Kit/" + new, 1), p) for name, p in pairs)
    kit.extend(tree("icons", "TG_Brand_Kit/Icons"))
    add("TG_Brand_Kit", kit)
    return packages


def signatures(path):
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate ZIP entries in {path}")
        return {name: hashlib.sha256(archive.read(name)).hexdigest() for name in names}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "downloads")
    parser.add_argument("--verify", action="store_true", help="Compare entry paths and SHA-256 with committed packages")
    args = parser.parse_args()
    if args.verify and args.output_dir.resolve() == (ROOT / "downloads").resolve():
        parser.error("Use a temporary --output-dir with --verify; committed ZIPs must stay untouched")
    packages = recipes()
    committed = {p.name for p in (ROOT / "downloads").glob("*.zip")}
    if set(packages) != committed:
        raise ValueError(f"ZIP recipe coverage differs: {set(packages) ^ committed}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    entries = 0
    for filename, pairs in packages.items():
        target = args.output_dir / filename
        with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=9) as archive:
            for name, source in pairs:
                archive.write(source, name)
        entries += len(pairs)
        if args.verify and signatures(target) != signatures(ROOT / "downloads" / filename):
            raise ValueError(f"Entry paths or file SHA-256 differ: {filename}")
    print(f"Built {len(packages)} ZIPs ({entries} entries) into {args.output_dir}")
    if args.verify:
        print("Every entry path and per-file SHA-256 matches the committed ZIPs")


if __name__ == "__main__":
    main()
