from __future__ import annotations

import argparse
import base64
import html
import io
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BLUE = "#155EEF"
RED = "#F04438"
GREEN = "#12B76A"
MASK = "#24272E"
STRIPE = "#353945"
WHITE = "#FFFFFF"


def find_font(bold: bool = False) -> Path:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc") if bold else Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc") if bold else Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("No usable font found")


REGULAR = find_font(False)
BOLD = find_font(True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD if bold else REGULAR), size=size)


def box(value: list[int], image: Image.Image) -> tuple[int, int, int, int]:
    if len(value) != 4:
        raise ValueError(f"Box must have four integers: {value}")
    x1, y1, x2, y2 = map(int, value)
    if not (0 <= x1 < x2 <= image.width and 0 <= y1 < y2 <= image.height):
        raise ValueError(f"Box outside {image.width}x{image.height}: {value}")
    return x1, y1, x2, y2


def fitted_font(draw: ImageDraw.ImageDraw, text: str, width: int, start: int = 34) -> ImageFont.FreeTypeFont:
    for size in range(start, 19, -2):
        candidate = font(size, True)
        bounds = draw.textbbox((0, 0), text, font=candidate)
        if bounds[2] - bounds[0] <= width:
            return candidate
    return font(20, True)


def redact(image: Image.Image, coords: tuple[int, int, int, int], label: str) -> None:
    draw = ImageDraw.Draw(image)
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle(coords, radius=22, fill=MASK, outline="#525866", width=3)
    for offset in range(-(y2 - y1), x2 - x1 + y2 - y1, 38):
        points = []
        for x in range(x1, x2 + 1, 4):
            y = y1 + (x - x1) - offset
            if y1 <= y <= y2:
                points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=STRIPE, width=10)
    if label:
        fnt = fitted_font(draw, label, max(60, x2 - x1 - 24), 36)
        bounds = draw.textbbox((0, 0), label, font=fnt)
        draw.text(((x1 + x2 - bounds[2]) / 2, (y1 + y2 - bounds[3]) / 2), label, font=fnt, fill="#E4E7EC")


def tag(draw: ImageDraw.ImageDraw, image: Image.Image, label: str, x: int, y: int, color: str) -> None:
    fnt = fitted_font(draw, label, min(520, image.width - 70), 32)
    bounds = draw.textbbox((0, 0), label, font=fnt)
    width, height = bounds[2] - bounds[0] + 38, bounds[3] - bounds[1] + 26
    x = max(18, min(x, image.width - width - 18))
    y = max(18, min(y, image.height - height - 18))
    draw.rounded_rectangle((x, y, x + width, y + height), radius=16, fill=WHITE, outline=color, width=3)
    draw.text((x + 19, y + 10), label, font=fnt, fill=color)


def action(image: Image.Image, item: dict) -> None:
    draw = ImageDraw.Draw(image)
    coords = box(item["box"], image)
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle(coords, radius=22, outline=RED, width=9)
    radius = 35
    cx, cy = x1 + radius, y1 + radius
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=RED, outline=WHITE, width=4)
    number = str(item.get("number", ""))
    fnt = font(34 if len(number) == 1 else 28, True)
    bounds = draw.textbbox((0, 0), number, font=fnt)
    draw.text((cx - (bounds[2] - bounds[0]) / 2, cy - (bounds[3] - bounds[1]) / 2 - 3), number, font=fnt, fill=WHITE)
    label_y = y1 - 74 if y1 >= 95 else y2 + 18
    tag(draw, image, item.get("label", "操作位置"), x1, label_y, RED)


def highlight(image: Image.Image, item: dict) -> None:
    draw = ImageDraw.Draw(image)
    coords = box(item["box"], image)
    x1, y1, x2, _ = coords
    draw.rounded_rectangle(coords, radius=22, outline=GREEN, width=9)
    tag(draw, image, item.get("label", "完成结果"), x1, y1 - 74, "#027A48")


def process(step: dict, base: Path, max_width: int, quality: int) -> tuple[str, int]:
    source = Path(step["source"])
    if not source.is_absolute():
        source = base / source
    image = Image.open(source).convert("RGB")
    redaction_count = 0
    for item in step.get("redactions", []):
        redact(image, box(item["box"], image), item.get("label", "隐私信息已隐藏"))
        redaction_count += 1
    for item in step.get("actions", []):
        action(image, item)
    for item in step.get("highlights", []):
        highlight(image, item)
    if image.width > max_width:
        image = image.resize((max_width, round(image.height * max_width / image.width)), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=quality, optimize=True, progressive=True)
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return "data:image/jpeg;base64," + data, redaction_count


def safe_id(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return cleaned or fallback


def build(manifest: dict, base: Path, max_width: int, quality: int) -> tuple[str, dict]:
    sections_html, nav_html = [], []
    step_count = image_count = redaction_count = 0
    section_ids: set[str] = set()
    for s_index, section in enumerate(manifest["sections"], start=1):
        section_id = safe_id(section.get("id", f"sop{s_index}"), f"sop{s_index}")
        if section_id in section_ids:
            raise ValueError(f"Duplicate section id: {section_id}")
        section_ids.add(section_id)
        number = section.get("number", f"SOP {s_index:02d}")
        steps = section.get("steps", [])
        sections_html.append(f'''<section class="sop-head" id="{section_id}"><div class="sop-number">{html.escape(number)}</div><div><h2>{html.escape(section['title'])}</h2><p>{html.escape(section.get('subtitle',''))}</p></div><div class="outcome"><span>完成结果</span>{html.escape(section.get('outcome','完成本节所有设置。'))}</div><div class="step-count">{len(steps)}<small>步骤</small></div></section>''')
        nav_html.append(f'<div class="nav-group" data-section="{section_id}"><a class="nav-title" href="#{section_id}">{html.escape(number)} · {html.escape(section["title"])}</a>')
        for local_index, step in enumerate(steps, start=1):
            step_count += 1
            image_count += 1
            data_url, count = process(step, base, max_width, quality)
            redaction_count += count
            step_id = f"{section_id}-step-{local_index}"
            title = step["title"]
            instruction = step.get("instruction", "按图示完成操作。")
            check = step.get("check", "确认页面状态与图示一致。")
            sections_html.append(f'''<article class="step-card" id="{step_id}" data-section="{section_id}"><div class="step-copy"><div class="eyebrow">{html.escape(number)} · STEP {local_index:02d}</div><h3>{html.escape(title)}</h3><p>{html.escape(instruction)}</p><div class="check"><span>✓</span><div><b>完成检查</b><br>{html.escape(check)}</div></div></div><button class="shot" type="button" aria-label="查看{html.escape(title)}大图" onclick="openLightbox(this)"><img src="{data_url}" alt="{html.escape(title)}（已标注并完成隐私遮挡）"><span class="zoom">点击查看大图</span></button></article>''')
            nav_html.append(f'<a class="step-link" data-section="{section_id}" href="#{step_id}"><span>{local_index:02d}</span>{html.escape(title)}</a>')
        nav_html.append("</div>")

    title = manifest["title"]
    subtitle = manifest.get("subtitle", "图示操作指南")
    section_count = len(manifest["sections"])
    css = '''
:root{--blue:#155eef;--ink:#101828;--muted:#475467;--bg:#f4f7fb;--green:#12b76a}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;line-height:1.7}.hero{padding:72px 24px;background:linear-gradient(135deg,#fff,#dce9ff);border-bottom:1px solid #cbdcfb}.hero-inner{max-width:1160px;margin:auto}.kicker{display:inline-block;padding:7px 13px;border:1px solid #b8cdf8;border-radius:999px;background:#fff9;color:var(--blue);font-weight:800}.hero h1{margin:22px 0 12px;font-size:clamp(40px,6vw,72px);line-height:1.08;letter-spacing:-.04em}.hero p{max-width:800px;margin:0;color:var(--muted);font-size:18px}.stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}.stat{padding:10px 14px;border:1px solid #d7e2f6;border-radius:14px;background:#fff}.stat b{color:var(--blue)}.layout{max-width:1320px;margin:auto;padding:48px 24px 90px;display:grid;grid-template-columns:280px minmax(0,1fr);gap:30px;align-items:start}.side{position:sticky;top:18px;max-height:calc(100vh - 36px);overflow:auto;padding:18px;border:1px solid #e4e7ec;border-radius:20px;background:#fff;box-shadow:0 12px 36px #1018280a}.side h2{margin:0 0 12px;font-size:15px}.nav-group{padding:6px 0 14px;border-bottom:1px solid #eaecf0}.side a{display:flex;gap:9px;padding:8px;border-radius:10px;color:#667085;text-decoration:none;font-size:12px;line-height:1.4;transition:.18s}.side a span{min-width:26px;color:var(--blue);font-weight:800}.side .nav-title{color:#344054;font-weight:800}.side a.active{background:var(--blue);color:#fff;box-shadow:0 6px 18px #155eef38}.side a.active span{color:#fff}.side .nav-title.section-active{background:#eaf1ff;color:var(--blue)}.privacy-note{margin-top:14px;padding:12px;border:1px solid #eaecf0;border-radius:12px;background:#f9fafb;color:#667085;font-size:12px}.content{min-width:0}.sop-head{position:relative;display:grid;grid-template-columns:auto minmax(0,1fr);gap:12px 18px;margin:34px 0 22px;padding:28px 100px 28px 28px;border:1px solid #c9d9f8;border-radius:24px;background:linear-gradient(135deg,#fff,#edf4ff);scroll-margin-top:18px}.sop-number{align-self:start;padding:7px 12px;border-radius:999px;background:var(--blue);color:#fff;font-size:12px;font-weight:800}.sop-head h2{margin:0;font-size:30px}.sop-head p{grid-column:2;margin:0;color:#475467}.outcome{grid-column:2;padding:12px 14px;border:1px solid #abefc6;border-radius:13px;background:#ecfdf3;color:#067647;font-size:13px}.outcome span{display:block;font-weight:800}.step-count{position:absolute;right:25px;top:27px;color:var(--blue);font-size:38px;font-weight:900}.step-count small{display:block;color:#667085;font-size:11px;text-align:center}.step-card{display:grid;grid-template-columns:minmax(260px,.7fr) minmax(390px,1fr);gap:22px;margin-bottom:24px;padding:22px;border:1px solid #e4e7ec;border-radius:24px;background:#fff;box-shadow:0 14px 42px #1018280b;scroll-margin-top:18px}.step-copy{padding:12px 8px}.eyebrow{color:var(--blue);font-size:13px;font-weight:800}.step-copy h3{margin:10px 0 13px;font-size:26px;line-height:1.25}.step-copy p{margin:0;color:#475467}.check{display:flex;gap:11px;margin-top:22px;padding:14px;border:1px solid #abefc6;border-radius:15px;background:#ecfdf3;color:#067647;font-size:13px}.check>span{display:grid;place-items:center;flex:0 0 28px;height:28px;border-radius:50%;background:var(--green);color:#fff;font-weight:900}.shot{position:relative;width:100%;padding:0;overflow:hidden;border:0;border-radius:18px;background:#07090d;cursor:zoom-in}.shot img{display:block;width:100%;max-height:820px;object-fit:contain;margin:auto}.zoom{position:absolute;right:12px;bottom:12px;padding:7px 10px;border-radius:999px;background:#fff;color:#344054;font:700 12px "Microsoft YaHei",sans-serif}.lightbox{position:fixed;z-index:50;inset:0;display:none;align-items:center;justify-content:center;padding:30px;background:#101828e8}.lightbox.open{display:flex}.lightbox img{max-width:96vw;max-height:94vh;object-fit:contain}.close{position:fixed;right:22px;top:18px;width:44px;height:44px;border:0;border-radius:50%;background:#fff;font-size:26px}@media(max-width:920px){.layout{display:block;padding:28px 14px 70px}.side{position:relative;max-height:none;margin-bottom:22px}.step-card{grid-template-columns:1fr;padding:16px}.shot img{max-height:none}.sop-head{padding-right:28px}.step-count{position:static;grid-column:1/3;font-size:20px}.step-count small{display:inline;margin-left:5px}}'''
    script = '''
function openLightbox(btn){const b=document.getElementById('lightbox');document.getElementById('lightboxImg').src=btn.querySelector('img').src;b.classList.add('open');document.body.style.overflow='hidden'}
function closeLightbox(){document.getElementById('lightbox').classList.remove('open');document.body.style.overflow=''}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLightbox()});
const side=document.querySelector('.side');const steps=[...document.querySelectorAll('.step-card')];const links=[...document.querySelectorAll('.step-link')];let ticking=false;
function setActive(){ticking=false;if(!steps.length)return;const line=innerHeight*.32;let current=steps[0];for(const item of steps){if(item.getBoundingClientRect().top<=line)current=item;else break}if(innerHeight+scrollY>=document.documentElement.scrollHeight-4)current=steps[steps.length-1];const id=current.id;const section=current.dataset.section;let active=null;for(const link of links){const on=link.getAttribute('href')==='#'+id;link.classList.toggle('active',on);if(on){link.setAttribute('aria-current','step');active=link}else link.removeAttribute('aria-current')}document.querySelectorAll('.nav-title').forEach(link=>link.classList.toggle('section-active',link.closest('.nav-group')?.dataset.section===section));if(active&&side){const top=active.offsetTop;const low=side.scrollTop+48;const high=side.scrollTop+side.clientHeight-active.offsetHeight-48;if(top<low)side.scrollTop=Math.max(0,top-70);else if(top>high)side.scrollTop=top-side.clientHeight+active.offsetHeight+70}}
function requestActive(){if(!ticking){ticking=true;requestAnimationFrame(setActive)}}addEventListener('scroll',requestActive,{passive:true});addEventListener('resize',requestActive);addEventListener('hashchange',()=>setTimeout(setActive,80));setActive();'''
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>{html.escape(title)}｜完整 SOP</title><style>{css}</style></head><body><header class="hero"><div class="hero-inner"><div class="kicker">完整可视化 SOP</div><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p><div class="stats"><div class="stat"><b>{section_count}</b> 个 SOP</div><div class="stat"><b>{step_count}</b> 个图示步骤</div><div class="stat">图片已内嵌，可离线查看</div><div class="stat">目录自动高亮当前位置</div></div></div></header><main class="layout"><aside class="side"><h2>完整目录</h2><nav>{''.join(nav_html)}</nav><div class="privacy-note">红色＝操作位置<br>绿色＝完成结果<br>斜纹＝隐私信息已隐藏</div></aside><div class="content">{''.join(sections_html)}</div></main><div class="lightbox" id="lightbox" onclick="closeLightbox()"><button class="close" aria-label="关闭">×</button><img id="lightboxImg" alt="步骤大图"></div><script>{script}</script></body></html>'''
    return document, {"sections": section_count, "steps": step_count, "images": image_count, "redactions": redaction_count}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an annotated, privacy-safe, single-file visual SOP")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-width", type=int, default=920)
    parser.add_argument("--quality", type=int, default=88)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = args.output or manifest_path.parent / manifest.get("output_name", "visual-SOP.html")
    document, stats = build(manifest, manifest_path.parent, args.max_width, args.quality)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(json.dumps({"output": str(output.resolve()), "bytes": output.stat().st_size, **stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
