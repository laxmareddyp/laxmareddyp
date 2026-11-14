"""Generate the images used by the profile README.

Run from anywhere:

    python scripts/build_assets.py

This file produces the banners, the tiles and the toolbox bar in `assets/`.
The PR category bars in `assets/categories/` come from
`build_contributions.py`. To add a tile, add one entry to `TILES` and re-run.
"""

from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

FONT = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, "
    "sans-serif"
)
NAVY = "#14182B"
CREAM = "#FFF6E9"
RED = "#FF5C5C"
KERAS_RED = "#D00000"
AMBER = "#FFB454"
RUST = "#C2410C"
YELLOW = "#FFD21E"

# One colour per kind of work.
KIND_COLOURS = {
    "multimodal": AMBER,
    "text": "#B8A4FF",
    "embedding": "#7CC8FF",
    "vision": "#7EDFA4",
    "tooling": "#FF8F70",
    "guide": "#FF9EC4",
    "link": "#C9D1E0",
}

# (slug, name, tag, kind, footer). Models newest first, then the tiles for
# the other README sections.
TILES = [
    (
        "embeddinggemma-2",
        "EmbeddingGemma 2",
        "Multimodal embeddings",
        "embedding",
        "KerasHub · 2026",
    ),
    (
        "qwen-3-5-moe",
        "Qwen 3.5 MoE",
        "Vision + Text",
        "multimodal",
        "KerasHub · 2026",
    ),
    ("qwen-3-5", "Qwen 3.5", "Vision + Text", "multimodal", "KerasHub · 2026"),
    (
        "gemma-3n",
        "Gemma 3n",
        "Text + Vision + Audio",
        "multimodal",
        "KerasHub · 2026",
    ),
    (
        "t5gemma-2",
        "T5Gemma 2",
        "Vision + Text",
        "multimodal",
        "KerasHub · 2026",
    ),
    (
        "text-embedder",
        "TextEmbedder",
        "Sentence embeddings",
        "embedding",
        "KerasHub · 2026",
    ),
    (
        "embeddinggemma",
        "EmbeddingGemma",
        "Text embeddings",
        "embedding",
        "KerasHub · 2026",
    ),
    ("gpt-oss", "GPT-OSS", "Text", "text", "KerasHub · 2025"),
    (
        "functiongemma",
        "FunctionGemma",
        "Function calling",
        "text",
        "KerasHub · 2025",
    ),
    (
        "gemma-3-converter",
        "Gemma 3",
        "HF weight converter",
        "tooling",
        "KerasHub · 2025",
    ),
    ("basnet", "BASNet", "Segmentation", "vision", "KerasHub · 2024"),
    ("mask-rcnn", "Mask R-CNN", "Segmentation", "vision", "KerasCV · 2024"),
    (
        "model-porter",
        "Model Porter",
        "HF to KerasHub script",
        "tooling",
        "KerasHub · 2025",
    ),
    (
        "guide-functiongemma",
        "FunctionGemma",
        "Native function calling",
        "guide",
        "keras.io guide · 2026",
    ),
    (
        "guide-function-calling",
        "Function Calling",
        "With KerasHub models",
        "guide",
        "keras.io guide · 2025",
    ),
    (
        "guide-rag",
        "RAG Pipeline",
        "With KerasHub",
        "guide",
        "keras.io guide · 2025",
    ),
    (
        "guide-hf-checkpoints",
        "HF Checkpoints",
        "Loading into KerasHub",
        "guide",
        "keras.io guide · 2025",
    ),
    (
        "link-hugging-face",
        "Hugging Face",
        "laxmareddyp",
        "link",
        "huggingface.co",
    ),
    ("link-kaggle", "Kaggle", "laxmareddypatlolla", "link", "kaggle.com"),
    ("link-linkedin", "LinkedIn", "laxma-patlolla", "link", "linkedin.com"),
]

TOOLBOX = [
    "Python",
    "Keras",
    "KerasHub",
    "TensorFlow",
    "PyTorch",
    "Docker",
    "GCP",
    "FastAPI",
    "Flask",
]


def glyph(kind):
    """Small line doodle for the bottom-right corner of a tile (80x64)."""
    if kind == "text":
        return (
            '<rect x="0" y="4" width="80" height="12" rx="6"/>'
            f'<rect x="0" y="26" width="52" height="12" rx="6" fill="{NAVY}"/>'
            '<rect x="0" y="48" width="68" height="12" rx="6"/>'
        )
    if kind == "vision":
        filled = {(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)}
        cells = []
        for row in range(3):
            for col in range(3):
                fill = NAVY if (col, row) in filled else "none"
                cells.append(
                    f'<rect x="{4 + col * 25}" y="{row * 22}" width="19" '
                    f'height="16" rx="4" fill="{fill}"/>'
                )
        return "".join(cells)
    if kind == "multimodal":
        bars = "".join(
            f'<line x1="{2 + i * 6}" y1="{51 - h}" x2="{2 + i * 6}" '
            f'y2="{51 + h}"/>'
            for i, h in enumerate([4, 10, 6, 12, 5])
        )
        return (
            '<rect x="0" y="0" width="26" height="26" rx="5"/>'
            f'<circle cx="9" cy="9" r="3" fill="{NAVY}"/>'
            f"{bars}"
            '<path d="M32 13 L50 26 M32 51 L50 38"/>'
            f'<rect x="56" y="0" width="22" height="64" rx="6" fill="{NAVY}"/>'
        )
    if kind == "tooling":
        return (
            '<rect x="0" y="18" width="28" height="28" rx="6"/>'
            '<path d="M33 32 H46 M41 26 L47 32 L41 38"/>'
            f'<rect x="52" y="18" width="28" height="28" rx="6" fill="{NAVY}"/>'
        )
    if kind == "embedding":
        dots = "".join(
            f'<circle cx="{14 + i * 13}" cy="32" r="4" fill="{fill}"/>'
            for i, fill in enumerate([NAVY, "none", NAVY, NAVY, "none"])
        )
        return f'<rect x="0" y="16" width="80" height="32" rx="10"/>{dots}'
    if kind == "guide":
        return (
            '<rect x="14" y="0" width="52" height="64" rx="7"/>'
            '<path d="M26 18 H54 M26 32 H54 M26 46 H44"/>'
        )
    if kind == "link":
        return '<path d="M22 54 L60 16 M32 16 H60 V44"/>'
    raise ValueError(f"Unknown kind: {kind}")


def xml(value):
    return escape(value, {'"': "&quot;"})


def tile(name, tag, kind, footer):
    pill_width = 7 * len(tag) + 22
    name_size = 27 if len(name) <= 13 else 23
    name, tag, footer = xml(name), xml(tag), xml(footer)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 170" width="300" height="170" role="img" aria-label="{name}, {tag}, {footer}">
  <rect width="300" height="170" rx="22" fill="{KIND_COLOURS[kind]}"/>
  <g font-family="{FONT}" fill="{NAVY}">
    <text x="24" y="48" font-size="{name_size}" font-weight="800">{name}</text>
    <rect x="24" y="62" width="{pill_width}" height="26" rx="13" fill="none" stroke="{NAVY}" stroke-width="1.5"/>
    <text x="{24 + pill_width / 2}" y="80" font-size="13" font-weight="600" text-anchor="middle">{tag}</text>
    <text x="24" y="148" font-size="12" font-weight="600" opacity="0.65">{footer}</text>
  </g>
  <g transform="translate(196 98)" fill="none" stroke="{NAVY}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    {glyph(kind)}
  </g>
</svg>
"""


def banner(background, foreground, label_colour, accent):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 340" width="1200" height="340" role="img" aria-label="Laxma Reddy Patlolla. I port frontier models to KerasHub.">
  <style>
    .dash {{ stroke-dasharray: 10 12; animation: march 1.2s linear infinite; }}
    .weight {{ animation: fly 2.4s linear infinite backwards; }}
    .weight.b {{ animation-delay: 0.8s; }}
    .weight.c {{ animation-delay: 1.6s; }}
    @keyframes march {{ to {{ stroke-dashoffset: -22; }} }}
    @keyframes fly {{
      0% {{ transform: translateX(0); opacity: 0; }}
      15% {{ opacity: 1; }}
      85% {{ opacity: 1; }}
      100% {{ transform: translateX(96px); opacity: 0; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .dash, .weight {{ animation: none; }}
    }}
  </style>
  <rect width="1200" height="340" rx="28" fill="{background}"/>
  <g fill="none" stroke="{label_colour}" stroke-width="3" stroke-linecap="round" opacity="0.8">
    <path d="M700 58 v18 M691 67 h18"/>
    <path d="M1126 268 v18 M1117 277 h18"/>
    <circle cx="760" cy="290" r="7"/>
    <circle cx="1140" cy="70" r="5"/>
  </g>
  <g font-family="{FONT}" fill="{foreground}">
    <text x="64" y="92" font-size="18" font-weight="700" letter-spacing="4" fill="{label_colour}">LAXMA REDDY PATLOLLA</text>
    <text x="64" y="168" font-size="60" font-weight="800">I port frontier models</text>
    <text x="64" y="240" font-size="60" font-weight="800">to <tspan fill="{accent}">KerasHub</tspan></text>
    <text x="64" y="292" font-size="22" font-weight="500" opacity="0.75">Model ports · weight converters · keras.io guides</text>
    <text x="852" y="262" font-size="15" font-weight="600" opacity="0.7" text-anchor="middle">Hugging Face</text>
    <text x="1062" y="262" font-size="15" font-weight="600" opacity="0.7" text-anchor="middle">KerasHub</text>
  </g>
  <circle cx="852" cy="170" r="56" fill="{YELLOW}"/>
  <g fill="none" stroke="{NAVY}" stroke-width="5" stroke-linecap="round">
    <path d="M832 156 v8 M872 156 v8"/>
    <path d="M828 182 q24 24 48 0"/>
  </g>
  <path class="dash" d="M924 170 H990" fill="none" stroke="{foreground}" stroke-width="4" stroke-linecap="round" opacity="0.5"/>
  <g fill="{label_colour}">
    <rect class="weight" x="914" y="140" width="12" height="12" rx="3"/>
    <rect class="weight b" x="914" y="164" width="12" height="12" rx="3"/>
    <rect class="weight c" x="914" y="188" width="12" height="12" rx="3"/>
  </g>
  <rect x="1006" y="114" width="112" height="112" rx="22" fill="{KERAS_RED}"/>
  <text x="1062" y="198" font-family="{FONT}" font-size="80" font-weight="800" fill="#FFFFFF" text-anchor="middle">K</text>
</svg>
"""


def bar(label, value, colour, size=30):
    """Full-width strip with a label on the left and a value on the right."""
    aria = xml(f"{label} {value}".strip())
    label, value = xml(label), xml(value)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 84" width="1200" height="84" role="img" aria-label="{aria}">
  <rect width="1200" height="84" rx="20" fill="{colour}"/>
  <g font-family="{FONT}" fill="{NAVY}" font-weight="800">
    <text x="36" y="{42 + round(size * 0.36)}" font-size="{size}">{label}</text>
    <text x="1164" y="54" font-size="34" text-anchor="end">{value}</text>
  </g>
</svg>
"""


def write(path, text):
    # Fixed encoding and newlines keep the output identical on every platform.
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    tiles_dir = ASSETS / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    for slug, name, tag, kind, footer in TILES:
        write(tiles_dir / f"{slug}.svg", tile(name, tag, kind, footer))
    write(ASSETS / "banner-dark.svg", banner(NAVY, "#FFFFFF", AMBER, RED))
    light = banner(CREAM, NAVY, RUST, KERAS_RED)
    write(ASSETS / "banner-light.svg", light)
    toolbox = bar(" · ".join(TOOLBOX), "", KIND_COLOURS["link"], size=24)
    write(ASSETS / "toolbox.svg", toolbox)
    print(f"Wrote {len(TILES)} tiles, 2 banners and 1 bar to {ASSETS}")


if __name__ == "__main__":
    main()
