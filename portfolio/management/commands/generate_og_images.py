"""
Genera imágenes Open Graph 1200x630 para:
  - Home (og-home.png) — tagline principal
  - Cada proyecto en portfolio (og-{slug}.png)

Output: static/og/og-*.png

Usage:
    python manage.py generate_og_images
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from portfolio.loaders import load_proyectos
from site_config.models import SiteConfig


W, H = 1200, 630
BG = (15, 20, 30)
PANEL = (24, 32, 47)
PRIMARY = (56, 189, 248)
ACCENT = (74, 222, 128)
WHITE = (255, 255, 255)
MUTED = (156, 163, 175)


def load_font(size, bold=False):
    try:
        return ImageFont.truetype(
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            size,
        )
    except Exception:
        return ImageFont.load_default()


def wrap_lines(text, font, max_w):
    words = text.split()
    lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip() if cur else w
        if font.getlength(t) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_og(out_path: Path, title: str, subtitle: str, eyebrow: str = 'Magoreal'):
    img = Image.new('RGBA', (W, H), BG + (255,))

    # Mesh gradient con 3 ellipses translucidas
    for cx, cy, color, r in [
        (200, 180, (56, 189, 248, 60), 500),
        (1000, 100, (139, 92, 246, 50), 500),
        (600, 580, (74, 222, 128, 30), 450),
    ]:
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=color)
        img = Image.alpha_composite(img, overlay)

    # Grid pattern (muy sutil)
    grid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 60):
        gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 8), width=1)
    for y in range(0, H, 60):
        gd.line([(0, y), (W, y)], fill=(255, 255, 255, 8), width=1)
    img = Image.alpha_composite(img, grid)

    d = ImageDraw.Draw(img)

    # Logo top-left
    F_LOGO = load_font(32, bold=True)
    d.text((60, 60), '<', fill=PRIMARY, font=F_LOGO)
    d.text((80, 60), 'M', fill=WHITE, font=F_LOGO)
    d.text((110, 60), '/>', fill=PRIMARY, font=F_LOGO)
    d.text((160, 60), 'magoreal', fill=WHITE, font=load_font(26, bold=True))
    d.ellipse([(340, 75), (352, 87)], fill=ACCENT)

    # Eyebrow
    d.text((60, 180), eyebrow.upper(), fill=PRIMARY, font=load_font(16, bold=True))

    # Title
    F_TITLE = load_font(54, bold=True)
    title_lines = wrap_lines(title, F_TITLE, W - 120)[:3]
    y = 220
    for line in title_lines:
        d.text((60, y), line, fill=WHITE, font=F_TITLE)
        y += 66

    # Subtitle
    F_SUB = load_font(24)
    sub_lines = wrap_lines(subtitle, F_SUB, W - 120)[:3]
    y = max(y + 20, 490)
    for line in sub_lines:
        d.text((60, y), line, fill=MUTED, font=F_SUB)
        y += 32

    # Bottom accent bar
    d.rectangle([(0, H - 4), (W, H)], fill=PRIMARY)

    # Footer
    F_FOOT = load_font(18, bold=True)
    d.text((60, H - 60), 'magoreal.com', fill=WHITE, font=F_FOOT)
    d.text((W - 310, H - 60), '15+ proyectos · 6 industrias', fill=MUTED, font=F_FOOT)

    img.convert('RGB').save(out_path, 'PNG', optimize=True)
    return out_path.stat().st_size


class Command(BaseCommand):
    help = 'Genera imagenes Open Graph 1200x630 para home + cada proyecto'

    def handle(self, *args, **options):
        out_dir = Path(settings.BASE_DIR) / 'static' / 'og'
        out_dir.mkdir(parents=True, exist_ok=True)

        config = SiteConfig.load()

        home_path = out_dir / 'og-home.png'
        size = draw_og(
            home_path,
            title=config.hero_title.split('\n')[0] if config.hero_title else config.tagline,
            subtitle=config.hero_subtitle[:130] if config.hero_subtitle else '',
            eyebrow='Automatizacion · IA · Sistemas a medida',
        )
        self.stdout.write(self.style.SUCCESS(f'  {home_path.name} ({size // 1024} KB)'))

        proyectos = load_proyectos(settings.PROYECTOS_DIR)
        for p in proyectos:
            path = out_dir / f'og-{p["slug"]}.png'
            eyebrow = f'Proyecto {p["num"]:02d} · {p.get("categoria_principal", "Producto")}'
            size = draw_og(
                path,
                title=p.get('titulo', 'Proyecto Magoreal')[:120],
                subtitle=p.get('subtitulo', '')[:160],
                eyebrow=eyebrow,
            )
            self.stdout.write(self.style.SUCCESS(f'  {path.name} ({size // 1024} KB)'))

        self.stdout.write(self.style.SUCCESS(f'\nDone - {1 + len(proyectos)} OG images in {out_dir}'))
