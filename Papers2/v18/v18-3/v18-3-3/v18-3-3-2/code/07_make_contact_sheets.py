from pathlib import Path
from PIL import Image, ImageDraw

base = Path(__file__).resolve().parents[1] / "rendered" / "pages"
files = sorted(base.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
for sheet_no, start in enumerate(range(0, len(files), 12), 1):
    group = files[start:start + 12]
    canvas = Image.new("RGB", (1200, 1600), "#d8dde5")
    draw = ImageDraw.Draw(canvas)
    for k, path in enumerate(group):
        im = Image.open(path).convert("RGB")
        im.thumbnail((280, 480))
        x = 15 + (k % 4) * 295
        y = 28 + (k // 4) * 520
        canvas.paste(im, (x, y))
        draw.text((x, 8 + (k // 4) * 520), f"Page {start+k+1}", fill="#111827")
    canvas.save(base / f"contact-{sheet_no}.png", quality=92)
print({"pages": len(files), "sheets": (len(files)+11)//12})
