"""
Regenera 01-whatsapp-chat-bot.png — mockup WhatsApp donde el bot conversa
como humano: multi-mensaje corto, tono casual, imperfecciones intencionales,
indicador "escribiendo…" visible en medio de la conversación.

Output: 460x900 PNG dark mode.

Uso: python generate_mockup.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "screenshots" / "01-whatsapp-chat-bot.png"

W, H = 460, 900
BG              = (17, 23, 34)
HEADER_BG       = (24, 32, 47)
MSG_USER_BG     = (7, 94, 84)
MSG_USER_FG     = (235, 245, 235)
MSG_BOT_BG      = (32, 42, 60)
MSG_BOT_FG      = (203, 213, 225)
META_FG         = (120, 140, 160)
ACCENT          = (74, 222, 128)
INPUT_BG        = (24, 32, 47)

def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()

F_TITLE    = load_font(16, bold=True)
F_SUBTITLE = load_font(11)
F_MSG      = load_font(13)
F_META     = load_font(10)

img = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(img)

# ═══ HEADER ═══════════════════════════════════════════
d.rectangle([(0, 0), (W, 70)], fill=HEADER_BG)
d.ellipse([(14, 18), (54, 58)], fill=ACCENT)
# Avatar con letras centradas (aprox)
d.text((24, 28), "AI", fill=BG, font=F_TITLE)
d.text((66, 18), "Asistente virtual", fill=(255, 255, 255), font=F_TITLE)
d.text((66, 42), "en línea · escribiendo como humano", fill=META_FG, font=F_SUBTITLE)
d.text((W - 24, 26), "⋮", fill=META_FG, font=F_TITLE)

# ═══ MESSAGES ═════════════════════════════════════════
y = 90

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current = ''
    for w in words:
        trial = (current + ' ' + w).strip() if current else w
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [text]

def user_msg(text, time, y):
    lines = wrap_text(text, F_MSG, 280)
    height = len(lines) * 20 + 28
    max_w = max(F_MSG.getlength(l) for l in lines) + 24
    x2 = W - 16
    x1 = x2 - int(max_w)
    d.rounded_rectangle([(x1, y), (x2, y + height)], radius=10, fill=MSG_USER_BG)
    for i, line in enumerate(lines):
        d.text((x1 + 12, y + 10 + i * 20), line, fill=MSG_USER_FG, font=F_MSG)
    d.text((x2 - 36, y + height - 16), time, fill=(200, 220, 200), font=F_META)
    return y + height + 8

def bot_msg(text, time, y, is_last=True):
    """Mensajes multi-línea con \n, gap chico entre mensajes seguidos del bot."""
    lines = []
    for para in text.split('\n'):
        if para.strip() == '':
            lines.append('')
            continue
        lines.extend(wrap_text(para, F_MSG, 260))
    height = len(lines) * 20 + 18 + (12 if time else 4)
    non_empty = [l for l in lines if l]
    max_w = (max(F_MSG.getlength(l) for l in non_empty) if non_empty else 60) + 24
    x1, x2 = 16, 16 + int(max_w)
    d.rounded_rectangle([(x1, y), (x2, y + height)], radius=10, fill=MSG_BOT_BG)
    for i, line in enumerate(lines):
        if line:
            d.text((x1 + 12, y + 10 + i * 20), line, fill=MSG_BOT_FG, font=F_MSG)
    if time:
        d.text((x1 + 12, y + height - 16), time, fill=META_FG, font=F_META)
    gap = 3 if not is_last else 8  # mensajes seguidos del bot pegados (chunking humano)
    return y + height + gap

def typing_bubble(y):
    x1, x2, h = 16, 72, 26
    d.rounded_rectangle([(x1, y), (x2, y + h)], radius=13, fill=MSG_BOT_BG)
    for cx in [28, 42, 56]:
        d.ellipse([(cx - 3, y + 10), (cx + 3, y + 16)], fill=(180, 200, 200))
    return y + h + 3

# ═══ CONVERSATION — tono casual humano ═══════════
# Cliente entra
y = user_msg("Hola, necesito una cotización", "14:22", y)

# Bot responde: 3 burbujas cortas, casual, con modismo real. NO lista.
# "Dale, contame qué necesitás" es como respondería una persona real.
y = bot_msg("¡Hola!", "", y, is_last=False)
y = bot_msg("Dale, contame qué necesitás", "", y, is_last=False)
y = bot_msg("¿Es para tu casa o para una obra?", "14:22", y)

# Cliente responde
y = user_msg("Para mi casa", "14:22", y)

# Bot responde humano — pregunta específica, 1 burbuja
y = bot_msg("Perfecto", "", y, is_last=False)
y = bot_msg("Me pasás la dirección?", "14:23", y)

# Cliente
y = user_msg("Av. del Parque 1234", "14:23", y)

# Typing indicator (pausa realista mientras "consulta")
y = typing_bubble(y)

# Bot: 2 burbujas cortas como resultado de consulta
y = bot_msg("Ahí te veo", "", y, is_last=False)
y = bot_msg("Desde nuestra base más cercana son 12 km\nel servicio te sale USD 45 con traslado incluido", "14:24", y)

# Bot: pregunta de follow-up en burbuja separada (muy humano — partir el msg)
y = bot_msg("¿Agendamos?", "14:24", y)

# Cliente
y = user_msg("Sí, mañana 10am", "14:24", y)

# Bot confirma casual (NO lista con viñetas)
y = bot_msg("Genial, reservado", "", y, is_last=False)
y = bot_msg("Te confirmo por acá a primera hora\nel técnico te va a llamar 15 min antes de llegar", "14:24", y)

# ═══ INPUT BAR ═══════════════════════════════════════
INPUT_Y = H - 56
d.rectangle([(0, INPUT_Y), (W, H)], fill=HEADER_BG)
d.rounded_rectangle([(16, INPUT_Y + 10), (W - 60, H - 10)], radius=18, fill=INPUT_BG)
d.text((30, INPUT_Y + 18), "Escribí un mensaje...", fill=META_FG, font=F_MSG)
CX, CY = W - 30, INPUT_Y + 28
d.ellipse([(CX - 18, CY - 18), (CX + 18, CY + 18)], fill=ACCENT)
d.polygon([(CX - 4, CY - 7), (CX + 7, CY), (CX - 4, CY + 7)], fill=BG)

img.save(OUT, optimize=True)
print(f"Written: {OUT}  ({OUT.stat().st_size // 1024} KB)")
