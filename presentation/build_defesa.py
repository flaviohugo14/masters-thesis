# -*- coding: utf-8 -*-
"""
Gera a apresentacao de defesa (.pptx) da dissertacao
"Digitalizacao Bancaria e Assimetrias Regionais no Brasil".

Identidade visual CEDEPLAR/UFMG: fundo branco, laranja #FF693A, azul #353F56.
Tipografia em Arial (presente em macOS, Windows, Keynote, PowerPoint e Google
Slides), para que o layout nao quebre por substituicao de fonte na maquina da
banca.

Uso:
    pip install python-pptx pymupdf pillow
    python presentation/build_defesa.py

Dependencias de conteudo:
  - assets/logo/logo-cedeplar.png
  - thesis/index_files/figure-pdf/*.pdf  (gerados por `quarto render thesis/index.qmd`)

As figuras em PDF sao rasterizadas para PNG em presentation/.cache-figuras/.
"""
import os
import sys
import subprocess
from pptx import Presentation
from pptx.util import Inches as In, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ metrica real
# Mede o texto com as metricas reais do Arial, para empilhar blocos sem
# sobreposicao e para dimensionar titulos. Evita estimativas por contagem de
# caracteres, que erram feio em portugues.
_FD = "/System/Library/Fonts/Supplemental"
_FF = {(False, False): f"{_FD}/Arial.ttf", (True, False): f"{_FD}/Arial Bold.ttf",
       (False, True): f"{_FD}/Arial Italic.ttf", (True, True): f"{_FD}/Arial Bold Italic.ttf"}
_MDPI = 300
_fcache = {}
_mdraw = ImageDraw.Draw(Image.new("RGB", (10, 10)))


def _mfont(size_pt, bold=False, italic=False):
    key = (round(size_pt, 1), bold, italic)
    if key not in _fcache:
        _fcache[key] = ImageFont.truetype(_FF[(bold, italic)],
                                          max(4, int(round(size_pt * _MDPI / 72.0))))
    return _fcache[key]


def text_w(text, size_pt, bold=False, italic=False):
    """Largura do texto, em polegadas."""
    return _mdraw.textlength(text, font=_mfont(size_pt, bold, italic)) / _MDPI


def n_lines(segments, width_in):
    """segments = [(texto, size_pt, bold, italic)]. Devolve (n_linhas, size_max)."""
    lines, curw, smax = 1, 0.0, 0.0
    for txt, sz, b, i in segments:
        smax = max(smax, sz)
        for chunk in txt.replace("\n", " \n ").split(" "):
            if chunk == "\n":
                lines += 1
                curw = 0.0
                continue
            if not chunk:
                continue
            ww = text_w(chunk + " ", sz, b, i)
            if curw + ww > width_in and curw > 0:
                lines += 1
                curw = ww
            else:
                curw += ww
    return lines, smax


def block_h(segments, width_in, line=1.15):
    """Altura do bloco de texto, em polegadas."""
    n, smax = n_lines(segments, width_in)
    return n * (smax / 72.0) * line

# ----------------------------------------------------------------------------- paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRES = os.path.join(ROOT, "presentation")
FIG = os.path.join(PRES, ".cache-figuras")
FIG_PDF = os.path.join(ROOT, "thesis", "index_files", "figure-pdf")
LOGO_SRC = os.path.join(ROOT, "assets", "logo", "logo-cedeplar.png")
LOGO = LOGO_SRC
LOGO_W = os.path.join(FIG, "_logo-branco.png")   # texto em branco, para fundo escuro
OUT = os.path.join(PRES, "defesa-dissertacao.pptx")


def preparar_figuras():
    """Rasteriza as figuras do Quarto (PDF -> PNG 4x) e gera o logo p/ fundo escuro."""
    os.makedirs(FIG, exist_ok=True)
    if not os.path.isdir(FIG_PDF):
        sys.exit(f"Figuras nao encontradas em {FIG_PDF}.\n"
                 f"Rode antes:  quarto render thesis/index.qmd")
    try:
        import pymupdf
    except ImportError:
        sys.exit("Falta a dependencia pymupdf:  pip install pymupdf")
    for nome in sorted(os.listdir(FIG_PDF)):
        if not nome.endswith(".pdf"):
            continue
        destino = os.path.join(FIG, nome[:-4] + ".png")
        if os.path.exists(destino) and \
                os.path.getmtime(destino) > os.path.getmtime(os.path.join(FIG_PDF, nome)):
            continue
        doc = pymupdf.open(os.path.join(FIG_PDF, nome))
        doc[0].get_pixmap(matrix=pymupdf.Matrix(4, 4), alpha=False).save(destino)

    # variante do logo com o texto em branco, usada nos divisores de secao
    if not os.path.exists(LOGO_W) or \
            os.path.getmtime(LOGO_W) < os.path.getmtime(LOGO_SRC):
        im = Image.open(LOGO_SRC).convert("RGBA")
        larg, alt = im.size
        px = im.load()
        for y in range(alt):
            for x in range(larg):
                r, g, b, a = px[x, y]
                if a > 0 and b >= r and (r + g + b) < 430:   # azul escuro -> branco
                    px[x, y] = (255, 255, 255, a)
        im.save(LOGO_W)


preparar_figuras()

# ----------------------------------------------------------------------------- paleta
BLUE = RGBColor(0x35, 0x3F, 0x56)
ORANGE = RGBColor(0xFF, 0x69, 0x3A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x25, 0x2B, 0x3A)      # texto corrido
GRAY = RGBColor(0x6E, 0x76, 0x88)     # texto secundario
RULE = RGBColor(0xDC, 0xE0, 0xE8)     # filetes
BLUE_L = RGBColor(0xEE, 0xF0, 0xF4)   # fundo de destaque azul
ORANGE_L = RGBColor(0xFF, 0xF1, 0xEC)  # fundo de destaque laranja
GREEN = RGBColor(0x1F, 0x7A, 0x6B)    # positivo (usado com parcimonia)

# Arial: presente em macOS, Windows, Keynote, PowerPoint e Google Slides.
# Evita substituicao de fonte (e quebra de layout) na maquina da banca.
FONT = "Arial"

# ----------------------------------------------------------------------------- geometria
SW, SH = 13.333, 7.5
ML, MR = 0.70, 0.70
CW = SW - ML - MR          # 11.933
TITLE_Y = 0.42
BODY_Y = 1.42
FOOT_Y = 6.90

prs = Presentation()
prs.slide_width = In(SW)
prs.slide_height = In(SH)
BLANK = prs.slide_layouts[6]

SECTION = ""   # secao corrente (rodape)
_n = [0]


# ============================================================== helpers de baixo nivel
def _fmt(run, size=16, bold=False, color=INK, italic=False, font=FONT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font
    # garante a fonte tambem para o conjunto latino/complexo
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", font)


SUB = "ᵢ"   # marcador: vira um run subscrito de "i" (Arial nao cobre U+1D62)


def _emit(p, text, size, bold, color, italic, font=FONT):
    """Escreve o texto no paragrafo, convertindo o marcador SUB em subscrito real."""
    for k, piece in enumerate(text.split(SUB)):
        if piece:
            r = p.add_run()
            r.text = piece
            _fmt(r, size, bold, color, italic, font)
        if k < len(text.split(SUB)) - 1:
            r = p.add_run()
            r.text = "i"
            _fmt(r, size * 0.92, bold, color, italic, font)
            r._r.get_or_add_rPr().set("baseline", "-25000")


def textbox(slide, l, t, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, wrap=True):
    tb = slide.shapes.add_textbox(In(l), In(t), In(w), In(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    tf.paragraphs[0].alignment = align
    return tf


def para(tf, text, size=16, bold=False, color=INK, italic=False, space_before=0,
         space_after=4, align=PP_ALIGN.LEFT, line=1.15, first=False, font=FONT):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    p.line_spacing = line
    _emit(p, text, size, bold, color, italic, font)
    return p


def rich(tf, chunks, size=16, space_before=0, space_after=4, align=PP_ALIGN.LEFT,
         line=1.15, first=False):
    """chunks = [(texto, {bold, color, size, italic}), ...]"""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    p.line_spacing = line
    for txt, sty in chunks:
        if sty.get("sub"):          # indice subscrito real (nao depende de glifo)
            r = p.add_run()
            r.text = txt
            _fmt(r, sty.get("size", size), sty.get("bold", False),
                 sty.get("color", INK), sty.get("italic", False))
            r._r.get_or_add_rPr().set("baseline", "-25000")
            continue
        _emit(p, txt, sty.get("size", size), sty.get("bold", False),
              sty.get("color", INK), sty.get("italic", False))
    return p


def rect(slide, l, t, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, In(l), In(t), In(w), In(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = In(0.14)
    tf.margin_top = tf.margin_bottom = In(0.08)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return s


def pic(slide, path, l, t, w, h, align="center"):
    """Insere imagem ajustada a caixa (l,t,w,h) preservando proporcao."""
    iw, ih = Image.open(path).size
    k = min(w / iw, h / ih)
    nw, nh = iw * k, ih * k
    if align == "center":
        lx = l + (w - nw) / 2
    elif align == "left":
        lx = l
    else:
        lx = l + (w - nw)
    ty = t + (h - nh) / 2
    return slide.shapes.add_picture(path, In(lx), In(ty), In(nw), In(nh))


def notes(slide, text):
    tf = slide.notes_slide.notes_text_frame
    tf.text = text
    for p in tf.paragraphs:
        for r in p.runs:
            r.font.size = Pt(12)
            r.font.name = FONT


# ============================================================== layouts de slide
def s_blank():
    return prs.slides.add_slide(BLANK)


def footer(slide, show_number=True):
    """Filete + rodape institucional."""
    rect(slide, ML, FOOT_Y, CW, 0.012, fill=RULE)
    tf = textbox(slide, ML, FOOT_Y + 0.10, CW * 0.72, 0.28)
    para(tf, SECTION, 10.5, color=GRAY, first=True, space_after=0)
    if show_number:
        _n[0] += 1
        tf2 = textbox(slide, SW - MR - 1.6, FOOT_Y + 0.10, 1.6, 0.28, align=PP_ALIGN.RIGHT)
        para(tf2, str(_n[0]), 10.5, bold=True, color=BLUE, first=True, space_after=0)
    slide.shapes.add_picture(LOGO, In(SW - MR - 1.28), In(FOOT_Y + 0.36), In(1.28), In(0.32))


def s_content(title, kicker=None, count=True):
    """Slide padrao: titulo azul + filete laranja + rodape.

    O corpo sempre comeca em BODY_Y: o titulo encolhe ate caber em uma linha,
    para que nenhum slide tenha a area util invadida pela chamada.
    """
    sl = s_blank()
    y = TITLE_Y
    if kicker:
        tf = textbox(sl, ML, y - 0.06, CW, 0.26)
        para(tf, kicker.upper(), 11, bold=True, color=ORANGE, first=True, space_after=0)
        y += 0.30
    avail = CW - 1.80
    size = 27
    while size > 18 and text_w(title, size, bold=True) > avail:
        size -= 0.5
    tf = textbox(sl, ML, y, CW - 1.40, 0.55)
    para(tf, title, size, bold=True, color=BLUE, first=True, space_after=0, line=1.0)
    rect(sl, ML, y + (size / 72.0) * 1.30, 1.05, 0.045, fill=ORANGE)
    footer(sl, count)
    return sl


def s_divider(num, title, items):
    """Divisor de secao: fundo azul cheio."""
    sl = s_blank()
    rect(sl, 0, 0, SW, SH, fill=BLUE)
    rect(sl, 0, 0, 0.22, SH, fill=ORANGE)

    tf = textbox(sl, 1.35, 2.24, 2.0, 0.7)
    para(tf, num, 54, bold=True, color=ORANGE, first=True, space_after=0, line=1.0)

    tf = textbox(sl, 1.35, 3.05, 8.6, 1.0)
    para(tf, title, 34, bold=True, color=WHITE, first=True, space_after=0, line=1.05)

    rect(sl, 1.35, 4.20, 1.05, 0.045, fill=ORANGE)

    tf = textbox(sl, 1.35, 4.50, 8.6, 1.4)
    for i, it in enumerate(items):
        para(tf, it, 15, color=RGBColor(0xC6, 0xCC, 0xD8), first=(i == 0), space_after=6)

    slide_logo = sl.shapes.add_picture(LOGO_W, In(SW - 2.55), In(SH - 1.15), In(1.85), In(0.46))
    _n[0] += 1
    tf = textbox(sl, SW - 2.55, SH - 0.58, 1.85, 0.3, align=PP_ALIGN.RIGHT)
    para(tf, str(_n[0]), 10.5, bold=True, color=RGBColor(0x8A, 0x93, 0xA6), first=True, space_after=0)
    return sl


# ============================================================== componentes
def bullets(slide, items, l, t, w, size=16, gap=0.10, marker=ORANGE, lead=None,
            line=1.18):
    """items: str  ou  (titulo, texto)"""
    y = t
    for it in items:
        if isinstance(it, tuple):
            head, body = it
        else:
            head, body = None, it
        rect(slide, l, y + 0.085, 0.085, 0.085, fill=marker, shape=MSO_SHAPE.OVAL)
        tf = textbox(slide, l + 0.28, y, w - 0.28, 0.4)
        if head:
            rich(tf, [(head + "  ", {"bold": True, "color": BLUE, "size": size}),
                      (body, {"size": size, "color": INK})],
                 size=size, first=True, space_after=0, line=line)
        else:
            para(tf, body, size, color=INK, first=True, space_after=0, line=line)
        segs = ([(head + "  ", size, True, False)] if head else []) + [(body, size, False, False)]
        y += block_h(segs, w - 0.28, line) + gap
    return y


def kpi(slide, l, t, w, h, value, label, sub=None, accent=ORANGE, tint=ORANGE_L,
        vsize=30, lsize=12.5):
    rect(slide, l, t, w, h, fill=tint)
    rect(slide, l, t, 0.055, h, fill=accent)
    tf = textbox(slide, l + 0.24, t + 0.16, w - 0.40, h - 0.28)
    para(tf, value, vsize, bold=True, color=accent, first=True, space_after=2, line=1.0)
    para(tf, label, lsize, bold=True, color=BLUE, space_after=1, line=1.1)
    if sub:
        para(tf, sub, 10.5, color=GRAY, space_after=0, line=1.1)


def callout(slide, l, t, w, h, title, text, accent=BLUE, tint=BLUE_L, tsize=14, bsize=13.5):
    rect(slide, l, t, w, h, fill=tint)
    rect(slide, l, t, 0.055, h, fill=accent)
    tf = textbox(slide, l + 0.26, t + 0.16, w - 0.46, h - 0.30)
    para(tf, title, tsize, bold=True, color=accent, first=True, space_after=4, line=1.05)
    para(tf, text, bsize, color=INK, space_after=0, line=1.16)


def _cell_border(cell, edges=("L", "R", "T", "B"), color="DCE0E8", w=6350):
    tcPr = cell._tc.get_or_add_tcPr()
    tags = {"L": "a:lnL", "R": "a:lnR", "T": "a:lnT", "B": "a:lnB"}
    for e in edges:
        tag = tags[e]
        for old in tcPr.findall(qn(tag)):
            tcPr.remove(old)
        ln = tcPr.makeelement(qn(tag), {"w": str(w), "cap": "flat", "cmpd": "sng", "algn": "ctr"})
        fill = ln.makeelement(qn("a:solidFill"), {})
        clr = fill.makeelement(qn("a:srgbClr"), {"val": color})
        fill.append(clr)
        ln.append(fill)
        # ordem correta no schema: lnL, lnR, lnT, lnB antes de fill
        tcPr.insert(0, ln)


def table(slide, l, t, w, rows, col_w, head_size=12.5, body_size=12.5,
          row_h=0.34, head_h=0.40, align=None, head_fill=BLUE, zebra=True,
          bold_col0=True, highlight_rows=()):
    """rows[0] = cabecalho. col_w = fracoes que somam 1. align = lista de PP_ALIGN."""
    nrow, ncol = len(rows), len(rows[0])
    h = head_h + row_h * (nrow - 1)
    gf = slide.shapes.add_table(nrow, ncol, In(l), In(t), In(w), In(h))
    tbl = gf.table
    tbl.first_row = False
    tbl.horz_banding = False
    # remove estilo padrao (banding azul do Office)
    tblPr = tbl._tbl.find(qn('a:tblPr'))
    if tblPr is not None:
        for e in list(tblPr):
            if e.tag == qn('a:tableStyleId'):
                tblPr.remove(e)
        tblPr.set('firstRow', '0')
        tblPr.set('bandRow', '0')

    for j, f in enumerate(col_w):
        tbl.columns[j].width = Emu(int(In(w) * f))
    tbl.rows[0].height = In(head_h)
    for i in range(1, nrow):
        tbl.rows[i].height = In(row_h)

    if align is None:
        align = [PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * (ncol - 1)

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = In(0.10)
            c.margin_top = c.margin_bottom = In(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            if i == 0:
                c.fill.fore_color.rgb = head_fill
            elif i in highlight_rows:
                c.fill.fore_color.rgb = ORANGE_L
            elif zebra and i % 2 == 0:
                c.fill.fore_color.rgb = RGBColor(0xF6, 0xF7, 0xFA)
            else:
                c.fill.fore_color.rgb = WHITE
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = align[j]
            p.line_spacing = 1.02
            # valor pode ser (texto, cor) para destacar sinais
            color_over = None
            if isinstance(val, tuple):
                val, color_over = val
            r = p.add_run()
            r.text = str(val)
            if i == 0:
                _fmt(r, head_size, True, WHITE)
            else:
                col = color_over or (BLUE if (j == 0 and bold_col0) else INK)
                _fmt(r, body_size, (j == 0 and bold_col0) or color_over is not None, col)
            _cell_border(c, ("T", "B"))
    return gf


def source(slide, text, t=None, l=None, w=None, size=10):
    tf = textbox(slide, l if l is not None else ML, t if t is not None else FOOT_Y - 0.34,
                 w if w is not None else CW, 0.26)
    para(tf, text, size, color=GRAY, italic=True, first=True, space_after=0)


F = lambda name: os.path.join(FIG, name)

# =============================================================================
# 1. CAPA
# =============================================================================
sl = s_blank()
rect(sl, 0, 0, 0.26, SH, fill=ORANGE)
rect(sl, 0.26, 0, 0.09, SH, fill=BLUE)

sl.shapes.add_picture(LOGO, In(1.05), In(0.62), In(2.55), In(0.64))

tf = textbox(sl, 1.05, 1.62, 10.6, 0.3)
para(tf, "UNIVERSIDADE FEDERAL DE MINAS GERAIS  ·  FACULDADE DE CIÊNCIAS ECONÔMICAS",
     11, bold=True, color=GRAY, first=True, space_after=2)
para(tf, "CENTRO DE DESENVOLVIMENTO E PLANEJAMENTO REGIONAL (CEDEPLAR)",
     11, bold=True, color=GRAY, space_after=0)

tf = textbox(sl, 1.05, 2.28, 10.4, 1.5)
para(tf, "Digitalização Bancária e Assimetrias\nRegionais no Brasil",
     36, bold=True, color=BLUE, first=True, space_after=0, line=1.02)

rect(sl, 1.05, 3.55, 1.35, 0.05, fill=ORANGE)

tf = textbox(sl, 1.05, 3.78, 10.4, 0.6)
para(tf, "Reconfiguração das redes de agências, qualidade do crédito\ne deslocamento espacial (2009–2023)",
     17, color=INK, first=True, space_after=0, line=1.2)

tf = textbox(sl, 1.05, 4.72, 10.4, 0.3)
para(tf, "DEFESA DE DISSERTAÇÃO DE MESTRADO EM ECONOMIA", 11.5, bold=True,
     color=ORANGE, first=True, space_after=0)

# bloco autor / banca
rect(sl, 1.05, 5.10, 5.05, 1.32, fill=BLUE_L)
rect(sl, 1.05, 5.10, 0.055, 1.32, fill=BLUE)
tf = textbox(sl, 1.32, 5.26, 4.65, 1.05)
para(tf, "Flávio Hugo Pangracio Silva", 16, bold=True, color=BLUE, first=True, space_after=3)
para(tf, "Mestrando em Economia — CEDEPLAR/UFMG", 12, color=GRAY, space_after=7)
rich(tf, [("Orientador:  ", {"bold": True, "color": BLUE, "size": 12}),
          ("Prof. Dr. Marco Aurélio Crocco Afonso", {"size": 12, "color": INK})],
     size=12, space_after=0)

rect(sl, 6.42, 5.10, 5.05, 1.32, fill=RGBColor(0xF6, 0xF7, 0xFA))
rect(sl, 6.42, 5.10, 0.055, 1.32, fill=ORANGE)
tf = textbox(sl, 6.69, 5.26, 4.65, 1.05)
para(tf, "BANCA EXAMINADORA", 11, bold=True, color=ORANGE, first=True, space_after=5)
para(tf, "Prof. Dr. Marco Aurélio Crocco Afonso  (orientador)", 12, color=INK, space_after=3)
para(tf, "Prof. Dr. Igor Santos Tupy", 12, color=INK, space_after=3)
para(tf, "Prof. Dr. Frederico Gonzaga Jayme Jr.", 12, color=INK, space_after=0)

tf = textbox(sl, 1.05, 6.66, 10.4, 0.3)
para(tf, "Belo Horizonte (MG)  ·  10 de agosto de 2026", 12, bold=True, color=GRAY,
     first=True, space_after=0)

notes(sl, "TEMPO ALVO TOTAL: 25 minutos.\n\n"
          "Bom dia/boa tarde. Agradeço à banca. Vou apresentar a dissertação "
          "'Digitalização Bancária e Assimetrias Regionais no Brasil', orientada pelo "
          "Prof. Marco Crocco. (~20s)")

# =============================================================================
# 2. ROTEIRO
# =============================================================================
SECTION = "Roteiro"
sl = s_content("Roteiro da apresentação")
rows = [
    ("I", "Motivação e problema de pesquisa", "Lacuna, pergunta, objetivos e hipóteses", "3 min"),
    ("II", "Referencial teórico", "Hierarquia financeira, preferência pela liquidez e digitalização", "3 min"),
    ("III", "Base empírica", "Fontes, painel municipal e indicadores construídos", "3 min"),
    ("IV", "Estratégia empírica", "Shift-share, datação do choque e exposição ex-ante", "3 min"),
    ("V", "Resultados", "DiD contínuo, heterogeneidade, spillovers, mediação e quantílica", "7 min"),
    ("VI", "Estudos de caso (MG)", "Belo Horizonte, Juiz de Fora, Betim e Almenara", "3 min"),
    ("VII", "Implicações e conclusões", "Contrafactuais, balanço das hipóteses e limitações", "3 min"),
]
y = 1.62
for num, tit, desc, tempo in rows:
    rect(sl, ML, y, CW, 0.63, fill=RGBColor(0xFA, 0xFB, 0xFC))
    rect(sl, ML, y, 0.05, 0.63, fill=ORANGE if num in ("I", "V") else BLUE)
    tf = textbox(sl, ML + 0.26, y + 0.10, 0.85, 0.45, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, num, 20, bold=True, color=ORANGE, first=True, space_after=0)
    tf = textbox(sl, ML + 1.05, y + 0.09, 3.5, 0.45, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, tit, 15.5, bold=True, color=BLUE, first=True, space_after=0)
    tf = textbox(sl, ML + 4.60, y + 0.09, 5.8, 0.45, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, desc, 13, color=GRAY, first=True, space_after=0)
    tf = textbox(sl, SW - MR - 1.1, y + 0.09, 1.0, 0.45, align=PP_ALIGN.RIGHT,
                 anchor=MSO_ANCHOR.MIDDLE)
    para(tf, tempo, 12.5, bold=True, color=BLUE, first=True, space_after=0)
    y += 0.72
source(sl, "Ao final: slides de anexo com resultados complementares e testes de robustez.")
notes(sl, "Apresento em sete blocos. O núcleo é o bloco V (resultados quantitativos) "
          "e o VI (estudos de caso). Aproximadamente 25 minutos. (~30s)")

# =============================================================================
# I. MOTIVAÇÃO
# =============================================================================
SECTION = "I. Motivação e problema de pesquisa"
s_divider("I", "Motivação e problema de pesquisa",
          ["A lacuna da moeda na teoria regional  ·  O duplo movimento brasileiro",
           "Pergunta de pesquisa, objetivos e hipóteses"])
notes(prs.slides[-1], "Bloco I. (~5s)")

# --- 4. Motivação
sl = s_content("O ponto de partida: moeda, território e o duplo movimento",
               kicker="Motivação")
tf = textbox(sl, ML, 1.50, 7.35, 0.9)
rich(tf, [("“", {"size": 15, "color": ORANGE, "bold": True}),
          ("Modelos consagrados, sejam neoclássicos, de causação cumulativa ou de "
           "insumo-produto, tratam a moeda e os fluxos monetários como exógenos, "
           "incapazes de explicar as assimetrias regionais.", {"size": 15, "italic": True, "color": BLUE}),
          ("”", {"size": 15, "color": ORANGE, "bold": True})], first=True, line=1.25)
tf = textbox(sl, ML, 2.34, 7.35, 0.25)
para(tf, "CROCCO et al. (2006)", 11, bold=True, color=GRAY, first=True, space_after=0)
rect(sl, ML, 2.74, 7.35, 0.012, fill=RULE)

bullets(sl, [
    ("A promessa.", "A digitalização financeira é celebrada como mecanismo democratizante "
     "do acesso a serviços bancários."),
    ("O duplo movimento.", "Municípios periféricos enfrentam, ao mesmo tempo, retração "
     "acelerada da rede física e exclusão digital."),
    ("A hipótese de fundo.", "A tecnologia não suspende a hierarquia financeira herdada — "
     "ela pode reorganizá-la sob nova lógica."),
], ML, 2.94, 7.35, size=15, gap=0.20)

callout(sl, 8.42, 1.50, 4.21, 3.28,
        "O paradoxo a explicar",
        "A maior expansão digital da história do sistema financeiro brasileiro conviveu com "
        "a persistência — e, em dimensões-chave, o aprofundamento — da exclusão financeira "
        "qualitativa nas periferias.\n\n"
        "Não se trata de perguntar se a digitalização chegou ao território, mas o que ela fez "
        "com a natureza do crédito que ali circula.",
        accent=ORANGE, tint=ORANGE_L, tsize=15, bsize=13.5)

tf = textbox(sl, ML, 4.92, CW, 0.28)
para(tf, "O TERRITÓRIO SOBRE O QUAL O CHOQUE DIGITAL OPEROU", 11.5, bold=True,
     color=BLUE, first=True, space_after=0)
kpi(sl, ML, 5.26, 2.90, 1.28, "43,8%", "dos municípios sem agência",
    "2.440 de 5.570, em 2022", accent=ORANGE, tint=ORANGE_L, vsize=26, lsize=12)
kpi(sl, 3.71, 5.26, 2.90, 1.28, "25,8%", "do estoque em 10 cidades",
    "que reúnem 54,5% do saldo de crédito", accent=BLUE, tint=BLUE_L, vsize=26, lsize=12)
kpi(sl, 6.72, 5.26, 2.90, 1.28, "10,5%", "dos municípios com IRC > 1",
    "recebem mais crédito do que produzem", accent=BLUE, tint=BLUE_L, vsize=26, lsize=12)
kpi(sl, 9.73, 5.26, 2.90, 1.28, "2009–2023", "expansão do mobile banking",
    "de ~0 a 288 transações per capita/ano", accent=ORANGE, tint=ORANGE_L, vsize=23, lsize=12)
source(sl, "Fonte: elaboração própria a partir da ESTBAN/BCB, do PIB municipal do IBGE e das Pesquisas FEBRABAN de Tecnologia Bancária (2013–2024).")
notes(sl, "A economia regional tratou historicamente a moeda como variável exógena. "
          "O Brasil de hoje mostra por que isso é insuficiente: 43,8% dos municípios "
          "não têm agência, 10 cidades concentram um quarto da rede e mais da metade do "
          "crédito, e só 10,5% recebem crédito proporcional ao que produzem — tudo isso "
          "durante a maior expansão digital da história do sistema. É esse paradoxo que "
          "a dissertação investiga. (~70s)")

# --- 5. Pergunta e objetivos
sl = s_content("Pergunta de pesquisa, objetivo e eixos analíticos", kicker="Recorte")
callout(sl, ML, 1.50, CW, 0.95,
        "Pergunta de pesquisa",
        "Em que medida a digitalização do sistema bancário, ao mudar a geografia da prestação "
        "de serviços financeiros, redefine, atenua ou aprofunda as desigualdades regionais brasileiras?",
        accent=ORANGE, tint=ORANGE_L, tsize=13.5, bsize=15)

tf = textbox(sl, ML, 2.62, CW, 0.3)
para(tf, "TRÊS EIXOS ANALÍTICOS", 11.5, bold=True, color=BLUE, first=True, space_after=0)

eixos = [
    ("i", "Reconfiguração espacial\ndas redes bancárias",
     "Como a digitalização influencia o fechamento de agências físicas.",
     "Desfecho: ln(n. de agências)"),
    ("ii", "Viés metropolitano\nda digitalização",
     "Concentração de serviços financeiros em polos urbanos já consolidados.",
     "Desfechos: IRC, ICO"),
    ("iii", "Efeitos assimétricos sobre\na qualidade do crédito",
     "Diferença centro–periferia em disponibilidade, diversidade e condições de acesso.",
     "Desfecho: razão IRF/IRE"),
]
x = ML
for num, tit, desc, out in eixos:
    rect(sl, x, 2.96, 3.84, 2.30, fill=RGBColor(0xFA, 0xFB, 0xFC))
    rect(sl, x, 2.96, 3.84, 0.055, fill=ORANGE)
    tf = textbox(sl, x + 0.28, 3.14, 3.3, 0.30)
    para(tf, "EIXO " + num, 11.5, bold=True, color=ORANGE, first=True, space_after=0)
    tf = textbox(sl, x + 0.28, 3.46, 3.3, 0.72)
    para(tf, tit, 16, bold=True, color=BLUE, first=True, space_after=0, line=1.08)
    tf = textbox(sl, x + 0.28, 4.24, 3.3, 0.8)
    para(tf, desc, 13, color=INK, first=True, space_after=0, line=1.18)
    rect(sl, x + 0.28, 4.90, 3.3, 0.012, fill=RULE)
    tf = textbox(sl, x + 0.28, 4.99, 3.3, 0.3)
    para(tf, out, 11.5, bold=True, color=GRAY, first=True, space_after=0)
    x += 4.05

callout(sl, ML, 5.44, CW, 0.98,
        "Objetivo geral",
        "Investigar como a digitalização do sistema financeiro redefine as desigualdades regionais "
        "no Brasil, com foco nas transformações qualitativas do acesso ao crédito, articulando "
        "análise espacial de dados georreferenciados e estudos de caso territoriais comparativos.",
        accent=BLUE, tint=BLUE_L, tsize=13.5, bsize=13.5)
notes(sl, "A pergunta central é essa. Ela se desdobra em três eixos, e cada eixo tem um "
          "desfecho empírico próprio: agências (eixo i), IRC e ICO (eixo ii) e a razão "
          "IRF/IRE (eixo iii). Esse mapeamento eixo→desfecho organiza todo o Capítulo 3. (~60s)")

# --- 6. Hipóteses
sl = s_content("As cinco hipóteses de trabalho", kicker="Hipóteses")
hip = [
    ("H1", "Existe uma quebra estrutural empiricamente identificável na intensidade da digitalização "
           "bancária entre 2015 e 2020, com impacto detectável sobre indicadores municipais.", "Datação"),
    ("H2", "O efeito sobre o fechamento de agências é maior em municípios com alta dependência inicial "
           "de canais físicos e baixa centralidade financeira.", "Eixo i"),
    ("H3", "A digitalização aprofunda o viés metropolitano, ampliando a divergência dos indicadores de "
           "centralidade entre faixas de porte municipal após o choque.", "Eixo ii"),
    ("H4", "O efeito sobre a qualidade do crédito é assimétrico: serviços básicos se difundem, mas os "
           "financiamentos de longo prazo se concentram nos centros.", "Eixo iii"),
    ("H5", "Parte substancial do efeito sobre o crédito periférico opera através do fechamento de agências "
           "— canal de mediação entre tecnologia e território.", "Mecanismo"),
]
y = 1.58
for tag, txt, eixo in hip:
    rect(sl, ML, y, CW, 0.90, fill=RGBColor(0xFA, 0xFB, 0xFC))
    rect(sl, ML, y, 0.05, 0.90, fill=ORANGE)
    tf = textbox(sl, ML + 0.28, y + 0.16, 0.75, 0.5)
    para(tf, tag, 21, bold=True, color=ORANGE, first=True, space_after=0)
    tf = textbox(sl, ML + 1.05, y + 0.14, 9.05, 0.62, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, txt, 14, color=INK, first=True, space_after=0, line=1.16)
    tf = textbox(sl, SW - MR - 1.5, y + 0.14, 1.4, 0.62, align=PP_ALIGN.RIGHT,
                 anchor=MSO_ANCHOR.MIDDLE)
    para(tf, eixo, 11.5, bold=True, color=BLUE, first=True, space_after=0)
    y += 1.00
notes(sl, "Cinco hipóteses. H1 é de datação, H2 a H4 mapeiam os três eixos e H5 testa o "
          "mecanismo de transmissão. Volto a elas no balanço final: quatro se sustentam, "
          "mas duas precisaram ser reformuladas. (~50s)")

# =============================================================================
# II. REFERENCIAL TEÓRICO
# =============================================================================
SECTION = "II. Referencial teórico (Capítulo 1)"
s_divider("II", "Referencial teórico",
          ["Capítulo 1 — Das definições de centralidade e digitalização financeira",
           "aos seus impactos regionais"])

# --- 8. Hierarquia financeira
sl = s_content("Moeda, hierarquia financeira e desenvolvimento regional", kicker="Capítulo 1")
tf = textbox(sl, ML, 1.50, CW, 0.3)
para(tf, "A CADEIA TEÓRICA", 11.5, bold=True, color=BLUE, first=True, space_after=0)

blocos = [
    ("Economia monetária\nde produção",
     "Keynes (1973); Carvalho (1992)",
     "A moeda não é neutra: sob incerteza, o agente pode reter riqueza na forma líquida em vez de produzir."),
    ("Preferência pela liquidez\nregional diferenciada",
     "Dow (1982); Chick & Dow (1988)",
     "Na periferia, incerteza informacional maior → bancos retêm ativos líquidos e contraem o crédito longo."),
    ("Lugar central aplicado\nàs finanças",
     "Christaller (1966); Parr & Budd (2000)",
     "Serviços complexos se concentram hierarquicamente; serviços básicos se dispersam."),
    ("Drenagem de liquidez\ne distância funcional",
     "Amado (2006); Crocco (2010, 2012); Alessandrini et al. (2009)",
     "A poupança periférica migra para os centros e volta como crédito em piores condições."),
]
x = ML
for k, (tit, ref, txt) in enumerate(blocos):
    rect(sl, x, 1.86, 2.87, 2.14, fill=RGBColor(0xFA, 0xFB, 0xFC))
    rect(sl, x, 1.86, 2.87, 0.05, fill=BLUE)
    tf = textbox(sl, x + 0.24, 2.04, 2.4, 0.62)
    para(tf, tit, 14.5, bold=True, color=BLUE, first=True, space_after=0, line=1.08)
    tf = textbox(sl, x + 0.24, 2.74, 2.4, 0.4)
    para(tf, ref, 10.5, bold=True, color=ORANGE, first=True, space_after=0, line=1.1)
    tf = textbox(sl, x + 0.24, 3.16, 2.4, 0.8)
    para(tf, txt, 12, color=INK, first=True, space_after=0, line=1.15)
    if k < len(blocos) - 1:   # conector entre cartoes, exceto apos o ultimo
        cn = sl.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, In(x + 2.92), In(2.86),
                                 In(0.11), In(0.13))
        cn.fill.solid(); cn.fill.fore_color.rgb = ORANGE
        cn.line.fill.background(); cn.shadow.inherit = False
    x += 3.02

callout(sl, ML, 4.20, 5.85, 1.16,
        "Reestruturação bancária: a evidência",
        "Leyshon et al. (2008): fechamento de −25% em áreas pobres vs. −16,9% em áreas ricas no Reino Unido.  "
        "Nguyen (2019): cada fechamento reduz o crédito a pequenas empresas em US$ 453 mil/ano, "
        "efeito local e persistente por até 6 anos.",
        accent=BLUE, tint=BLUE_L, tsize=13, bsize=12.5)
callout(sl, 6.79, 4.20, 5.84, 1.16,
        "No Brasil",
        "Fonseca & Matray (2024): a entrada de agências eleva depósitos, crédito, emprego e "
        "empreendedorismo — com mais força em desertos bancários.  "
        "Schuster (2023): onde a agência rural fecha, a alternativa raramente é digital.",
        accent=ORANGE, tint=ORANGE_L, tsize=13, bsize=12.5)

tf = textbox(sl, ML, 5.56, CW, 0.9)
rich(tf, [("Síntese: ", {"bold": True, "color": BLUE, "size": 14}),
          ("a concentração financeira nos centros gera eficiência para as instituições e, "
           "simultaneamente, barreiras de acesso que reproduzem dualidades espaciais. "
           "O crédito de longo prazo, intensivo em informação tácita, é o primeiro a recuar "
           "quando a relação interpessoal se rompe.", {"size": 14, "color": INK})],
     first=True, line=1.18)
notes(sl, "A base é pós-keynesiana. Quatro elos: moeda não neutra → preferência pela liquidez "
          "que varia no espaço → teoria do lugar central aplicada às finanças → drenagem de "
          "liquidez e distância funcional. A evidência internacional e nacional converge: o "
          "fechamento de agência tem efeito local, persistente, e o canal digital não o "
          "substitui. (~65s)")

# --- 9. Digitalização + lacuna
sl = s_content("A dialética da digitalização e a lacuna que a dissertação preenche",
               kicker="Capítulo 1")

rect(sl, ML, 1.50, 5.85, 2.42, fill=BLUE_L)
rect(sl, ML, 1.50, 0.055, 2.42, fill=BLUE)
tf = textbox(sl, ML + 0.28, 1.68, 5.4, 2.1)
para(tf, "A PROMESSA", 11.5, bold=True, color=BLUE, first=True, space_after=8)
para(tf, "Plataformas digitais ampliam o alcance de serviços financeiros básicos "
         "(pagamentos, saques, transferências) e reduzem custos de operação.",
     13.5, color=INK, space_after=8, line=1.16)
para(tf, "No Brasil: Pix, Mobile Banking e correspondentes ampliam a bancarização "
         "elementar mesmo onde não há agência.", 13.5, color=INK, space_after=0, line=1.16)

rect(sl, 6.79, 1.50, 5.84, 2.42, fill=ORANGE_L)
rect(sl, 6.79, 1.50, 0.055, 2.42, fill=ORANGE)
tf = textbox(sl, 6.79 + 0.28, 1.68, 5.4, 2.1)
para(tf, "A CONTRAPARTIDA", 11.5, bold=True, color=ORANGE, first=True, space_after=8)
para(tf, "Operações de maior valor agregado seguem dependendo de provedores nos "
         "grandes centros (Hashimoto et al., 2022): a lógica do lugar central "
         "persiste em chave digital.", 13.5, color=INK, space_after=8, line=1.16)
para(tf, "Forma-se uma “periferia digital” (Guerra-Leal et al., 2021; Malaquias, 2020): "
         "excluída até da bancarização elementar.", 13.5, color=INK, space_after=0, line=1.16)

tf = textbox(sl, ML, 4.14, CW, 0.3)
para(tf, "A LACUNA IDENTIFICADA E A CONTRIBUIÇÃO DESTA DISSERTAÇÃO", 11.5, bold=True,
     color=ORANGE, first=True, space_after=0)

lac = [
    ("A tradição pós-keynesiana brasileira", "documentou o peso da concentração espacial sobre a "
     "preferência pela liquidez regional, mas não incorporou a digitalização como variável capaz "
     "de mudar a natureza da intermediação."),
    ("A evidência internacional", "sobre a assimetria territorial da substituição de canais nunca "
     "havia sido testada em escala municipal no Brasil, com indicadores que separem volume de qualidade do crédito."),
    ("Limitações metodológicas", "na aplicação de econometria espacial e subexploração dos efeitos "
     "diferenciados por tipo de serviço financeiro."),
]
bullets(sl, lac, ML, 4.52, CW, size=13.5, gap=0.13)
notes(sl, "A digitalização é dialética: difunde o serviço simples e concentra o complexo. "
          "A lacuna é precisa — ninguém havia testado isso em escala municipal no Brasil com "
          "indicadores que separassem volume de qualidade de crédito. É exatamente o que os "
          "capítulos 2 e 3 fazem. (~55s)")

# =============================================================================
# III. BASE EMPÍRICA
# =============================================================================
SECTION = "III. Base empírica (Capítulo 2)"
s_divider("III", "Base empírica",
          ["Capítulo 2 — Fundamentos empíricos da digitalização financeira no Brasil",
           "Fontes, painel municipal, indicadores e fatos estilizados"])

# --- 12. Dados
sl = s_content("Fontes de dados e o painel municipal construído", kicker="Capítulo 2")
rows = [
    ["Fonte", "Cobertura", "Uso na dissertação"],
    ["ESTBAN / BCB", "2009–2023", "Estatística bancária mensal por município e por instituição (contas COSIF)"],
    ["IBGE — PIB municipal", "2002–2023", "Denominador dos índices locacionais; deflacionamento pelo IPCA (base 2021)"],
    ["Pesquisas FEBRABAN", "2009–2024", "Séries nacionais de digitalização: penetração, utilização e composição"],
    ["UNICAD / BCB", "—", "Classificação de porte e conglomerado das instituições financeiras"],
    ["geobr (malha IBGE)", "2020", "Malha municipal para construção da matriz de pesos espaciais W"],
    ["RAIS e IBGE (VAB)", "2009–2023", "Controles reais: emprego formal, composição setorial e SIMPLES"],
]
table(sl, ML, 1.52, 7.55, rows, [0.235, 0.165, 0.60], body_size=11.5, row_h=0.42,
      head_h=0.38, head_size=12,
      align=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT])

kpi(sl, 8.55, 1.52, 3.90, 0.95, "5.570", "municípios brasileiros",
    "cobertura censitária, sem amostragem", accent=BLUE, tint=BLUE_L, vsize=25, lsize=12)
kpi(sl, 8.55, 2.62, 3.90, 0.95, "2009–2023", "15 anos de painel anual",
    "≈ 83,5 mil observações município-ano", accent=ORANGE, tint=ORANGE_L, vsize=25, lsize=12)
kpi(sl, 8.55, 3.72, 3.90, 0.95, "12", "indicadores originais",
    "liquidez, centralidade e qualidade do crédito", accent=BLUE, tint=BLUE_L, vsize=25, lsize=12)

callout(sl, 8.55, 4.82, 3.90, 1.35,
        "Pipeline reprodutível",
        "Toda a construção roda em R (renv + Quarto), da extração via BigQuery à renderização "
        "do documento. Código e dependências versionados e públicos.",
        accent=ORANGE, tint=ORANGE_L, tsize=13, bsize=12.5)
source(sl, "Ressalvas de cobertura: o estoque de agências de 2023 está subnotificado na base — as análises de cobertura física são truncadas em 2022.")
notes(sl, "A base integra seis fontes que, na literatura nacional, eram usadas separadamente. "
          "O painel é censitário: 5.570 municípios, 15 anos. Uma ressalva importante: 2023 tem "
          "subnotificação de agências, então trunquei as análises de cobertura física em 2022. (~50s)")

# --- 13. Indicadores
sl = s_content("Os indicadores construídos: separando volume de qualidade", kicker="Capítulo 2")

grupos = [
    ("PREFERÊNCIA PELA LIQUIDEZ", BLUE, [
        ("PLP", "Depósitos à vista / depósitos totais", "Preferência pela liquidez do público"),
        ("PLB", "Depósitos à vista / operações de crédito", "Preferência pela liquidez dos bancos"),
    ]),
    ("CENTRALIDADE E CONCENTRAÇÃO", ORANGE, [
        ("IRC", "Quociente locacional do crédito sobre o PIB", "Centralidade creditícia do município"),
        ("ICO", "HHI das modalidades de crédito", "Diversidade do portfólio local"),
        ("ICB", "HHI dos conglomerados bancários", "Estrutura concorrencial local"),
    ]),
    ("QUALIDADE E CONDIÇÕES DO CRÉDITO", BLUE, [
        ("IRF / IRE", "Financiamentos de longo prazo (162) ÷ empréstimos de curto prazo (161)",
         "Proxy central de qualidade do crédito"),
        ("IRD, IRR, IRL", "Quocientes locacionais de depósitos, risco e lucro bancário",
         "Distribuição espacial de depósitos, risco e rentabilidade"),
    ]),
]
COL_F, COL_L = 5.60, 4.15         # colunas: formula e leitura
y = 1.48
for tit, cor, itens in grupos:
    hs = [max(0.30, block_h([(f, 12.5, False, False)], COL_F, 1.10),
              block_h([(l, 12, False, True)], COL_L, 1.10)) for _, f, l in itens]
    rect(sl, ML, y, 0.05, 0.26 + sum(h + 0.10 for h in hs), fill=cor)
    tf = textbox(sl, ML + 0.24, y, CW, 0.24)
    para(tf, tit, 11.5, bold=True, color=cor, first=True, space_after=0)
    yy = y + 0.28
    for (sig, form, leitura), hh in zip(itens, hs):
        tf = textbox(sl, ML + 0.24, yy, 1.35, hh, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, sig, 14.5, bold=True, color=BLUE, first=True, space_after=0)
        tf = textbox(sl, ML + 1.62, yy, COL_F, hh, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, form, 12.5, color=INK, first=True, space_after=0, line=1.10)
        tf = textbox(sl, ML + 7.40, yy, COL_L, hh, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, leitura, 12, color=GRAY, italic=True, first=True, space_after=0, line=1.10)
        rect(sl, ML + 0.24, yy + hh + 0.05, CW - 0.24, 0.008, fill=RULE)
        yy += hh + 0.10
    y = yy + 0.18

callout(sl, ML, 5.58, CW, 0.86,
        "Por que a razão IRF/IRE é o indicador-chave",
        "Valores altos indicam um portfólio voltado a operações estruturadas e relacionais; valores baixos, "
        "um crédito predominantemente curto e padronizado. É o termômetro que permite testar se a digitalização "
        "mexeu no volume ou na natureza do crédito — a pergunta que a literatura nacional ainda não havia respondido.",
        accent=ORANGE, tint=ORANGE_L, tsize=13.5, bsize=13)
notes(sl, "Doze indicadores em três famílias. O ponto não trivial é o último: a razão IRF/IRE. "
          "Ela é a proxy de qualidade — divide financiamento de longo prazo por empréstimo de "
          "curto prazo. É ela que permite dizer se a digitalização mudou o volume ou a natureza "
          "do crédito. Esse é o indicador que carrega o argumento da dissertação. (~55s)")

# --- 14. Fato estilizado 1
sl = s_content("Fato estilizado 1 — o salto digital é recente e abrupto", kicker="Capítulo 2")
pic(sl, F("fig-transacoes-1.png"), ML, 1.48, 7.55, 4.95)
tf = textbox(sl, 8.50, 1.52, 3.95, 0.3)
para(tf, "LEITURA", 11.5, bold=True, color=ORANGE, first=True, space_after=8)
bullets(sl, [
    "O Mobile Banking ultrapassa o Internet Banking como canal predominante em 2015–2016.",
    "O volume de transações móveis per capita dispara a partir de 2020, com a pandemia e o Pix.",
    "A série é nacional: há variação temporal, mas nenhuma variação espacial no tratamento.",
], 8.50, 1.90, 3.95, size=13, gap=0.16)
callout(sl, 8.50, 4.34, 3.95, 2.08,
        "A restrição que define a estratégia",
        "As Pesquisas FEBRABAN são a única fonte sistemática sobre intensidade de digitalização "
        "bancária no país — e não têm desagregação subnacional.\n\n"
        "Sem variação espacial no tratamento, as estratégias clássicas de painel com tratamento "
        "heterogêneo ficam descartadas. É esse obstáculo que motiva o desenho shift-share.",
        accent=BLUE, tint=BLUE_L, tsize=13, bsize=12.5)
notes(sl, "Dois fatos: a virada IB→MB em 2015-16 e a explosão de uso em 2020. Mas repare no "
          "problema que isso cria: a série é nacional. Tenho quando o choque aconteceu, não "
          "onde ele bateu mais forte. Essa restrição define toda a estratégia de identificação. (~50s)")

# --- 15. Fato estilizado 2
sl = s_content("Fato estilizado 2 — a geografia bancária é profundamente desigual",
               kicker="Capítulo 2")
pic(sl, F("fig-mapa-brasil-1.png"), ML - 0.20, 1.42, 7.30, 5.10)
tf = textbox(sl, 7.55, 1.52, 4.90, 0.3)
para(tf, "MUNICÍPIOS SEM AGÊNCIA (2022)", 11.5, bold=True, color=ORANGE, first=True, space_after=8)
rows = [["Região", "% sem agência"],
        ["Nordeste", ("59,8%", ORANGE)],
        ["Norte", "40,7%"],
        ["Sul", "36,0%"],
        ["Sudeste", ("33,6%", BLUE)],
        ["Brasil", "43,8%"]]
table(sl, 7.55, 1.88, 4.90, rows, [0.6, 0.4], body_size=12.5, row_h=0.30, head_h=0.34,
      head_size=11.5, highlight_rows=(5,))
bullets(sl, [
    "Apenas 14 municípios reuniam 100 ou mais agências; 1.660 eram atendidos por uma ou duas.",
    "Os 10 maiores (SP, RJ, BH, POA, Curitiba, Brasília, Salvador, Campinas, Goiânia e Fortaleza) "
    "concentravam 25,8% do estoque e 54,5% do saldo de crédito.",
    "Só 10,5% dos municípios com presença bancária tinham IRC > 1.",
], 7.55, 4.05, 4.90, size=13, gap=0.14)
callout(sl, 7.55, 5.72, 4.90, 0.72,
        "",
        "A maior parte do território recebe menos crédito do que produz — e o excedente se acumula "
        "nos poucos nós metropolitanos onde a rede física permanece densa.",
        accent=ORANGE, tint=ORANGE_L, tsize=1, bsize=13)
notes(sl, "O mapa mostra o padrão centro-periferia em estado bruto. Cinza = sem agência: "
          "quase 60% no Nordeste. Os círculos são o estoque de agências. E a cor mostra que "
          "só 10,5% dos municípios com banco recebem crédito proporcional ao que produzem. "
          "Este é o território sobre o qual o choque digital vai operar. (~50s)")

# =============================================================================
# IV. ESTRATÉGIA EMPÍRICA
# =============================================================================
SECTION = "IV. Estratégia empírica (Capítulo 3)"
s_divider("IV", "Estratégia empírica",
          ["Capítulo 3 — Identificação shift-share, datação do choque",
           "e construção da exposição ex-ante"])

# --- 17. Identificação
sl = s_content("O desafio de identificação e a solução shift-share", kicker="Capítulo 3")

rect(sl, ML, 1.50, 5.62, 1.28, fill=ORANGE_L)
rect(sl, ML, 1.50, 0.055, 1.28, fill=ORANGE)
tf = textbox(sl, ML + 0.28, 1.66, 5.15, 1.0)
para(tf, "O PROBLEMA", 11.5, bold=True, color=ORANGE, first=True, space_after=6)
para(tf, "O tratamento (intensidade da digitalização) varia no tempo, mas é idêntico para "
         "todos os municípios. Sem variação cross-section, não há grupo de controle.",
     13.5, color=INK, space_after=0, line=1.16)

rect(sl, 7.02, 1.50, 5.62, 1.28, fill=BLUE_L)
rect(sl, 7.02, 1.50, 0.055, 1.28, fill=BLUE)
tf = textbox(sl, 7.02 + 0.28, 1.66, 5.15, 1.0)
para(tf, "A SOLUÇÃO (BORUSYAK et al., 2024)", 11.5, bold=True, color=BLUE, first=True, space_after=6)
para(tf, "Desenho shift-share à la Bartik: multiplica-se o shifter nacional por uma medida "
         "cross-section de exposição ex-ante. A uniformidade espacial vira vantagem analítica.",
     13.5, color=INK, space_after=0, line=1.16)

# equação
rect(sl, ML, 3.00, CW, 1.02, fill=RGBColor(0xFA, 0xFB, 0xFC), line=RULE, lw=0.75)
tf = textbox(sl, ML, 3.14, CW, 0.42, align=PP_ALIGN.CENTER)
rich(tf, [("Y", {"size": 19, "bold": True, "color": BLUE}),
          ("it", {"size": 12, "color": BLUE, "sub": True}),
          ("  =  α", {"size": 19, "color": INK}),
          ("i", {"size": 12, "color": INK, "sub": True}),
          ("  +  λ", {"size": 19, "color": INK}),
          ("t", {"size": 12, "color": INK, "sub": True}),
          ("  +  β · (Post", {"size": 19, "color": INK}),
          ("t", {"size": 12, "color": INK, "sub": True}),
          (" × E", {"size": 19, "bold": True, "color": ORANGE}),
          ("i", {"size": 12, "bold": True, "color": ORANGE, "sub": True}),
          (")  +  γ X", {"size": 19, "color": INK}),
          ("it", {"size": 12, "color": INK, "sub": True}),
          ("  +  ε", {"size": 19, "color": INK}),
          ("it", {"size": 12, "color": INK, "sub": True})],
     first=True, space_after=0, align=PP_ALIGN.CENTER)
tf = textbox(sl, ML, 3.62, CW, 0.32, align=PP_ALIGN.CENTER)
para(tf, "efeitos fixos de município e de ano  ·  Post = 1{t ≥ 2020}  ·  controle ln(PIB real)  "
         "·  erros-padrão clusterizados por município",
     11.5, color=GRAY, first=True, space_after=0, align=PP_ALIGN.CENTER)

tf = textbox(sl, ML, 4.22, CW, 0.3)
para(tf, "AS TRÊS CAMADAS DO CAPÍTULO 3", 11.5, bold=True, color=BLUE, first=True, space_after=0)
camadas = [
    ("QUANTITATIVA", "Datação do choque (Bai-Perron, Quandt-Andrews, Chow) · Exposição ex-ante por ACP · "
     "Event study e DiD contínuo · SLX-DiD · Mediação causal (IKT) · Quantílica espacial (Canay)"),
    ("QUALITATIVA", "Quatro estudos de caso territoriais em Minas Gerais, selecionados a partir dos "
     "resíduos e dos efeitos heterogêneos da camada quantitativa"),
    ("NORMATIVA", "Tradução dos coeficientes em simulações contrafactuais e recomendações regulatórias"),
]
y = 4.58
for tit, txt in camadas:
    rect(sl, ML, y, CW, 0.62, fill=RGBColor(0xFA, 0xFB, 0xFC))
    rect(sl, ML, y, 0.05, 0.62, fill=ORANGE if tit == "QUANTITATIVA" else BLUE)
    tf = textbox(sl, ML + 0.26, y + 0.10, 1.85, 0.42, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, tit, 12.5, bold=True, color=BLUE, first=True, space_after=0)
    tf = textbox(sl, ML + 2.20, y + 0.08, 9.4, 0.46, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, txt, 12.5, color=INK, first=True, space_after=0, line=1.14)
    y += 0.70
notes(sl, "Aqui está a chave metodológica. Como o tratamento é nacional, uso o desenho "
          "shift-share: o choque agregado vezes a exposição ex-ante de cada município. "
          "β mede o efeito de um desvio-padrão adicional de exposição depois de 2020. "
          "O capítulo tem três camadas: quantitativa, qualitativa e normativa. (~60s)")

# --- 18. Datação
sl = s_content("Datação do choque: t* = 2020", kicker="Capítulo 3 · Etapa 1")
pic(sl, F("fig-quebras-1.png"), ML, 1.46, 7.15, 4.95)
tf = textbox(sl, 8.12, 1.50, 4.33, 0.3)
para(tf, "TRÊS PROCEDIMENTOS", 11.5, bold=True, color=ORANGE, first=True, space_after=6)
bullets(sl, [
    ("Bai-Perron (2003)", "— até m quebras endógenas, m* escolhido por BIC."),
    ("Quandt-Andrews (1993)", "— sup-Wald para quebra única de data desconhecida."),
    ("Chow", "— datas com motivação teórica: 2015, março/2020 e novembro/2020 (Pix)."),
], 8.12, 1.86, 4.33, size=12.5, gap=0.12)

tf = textbox(sl, 8.12, 3.52, 4.33, 0.3)
para(tf, "RESULTADO", 11.5, bold=True, color=ORANGE, first=True, space_after=0)
rows = [["Dimensão", "Quebra dominante"],
        ["Penetração (MB, IB)", ("2020–2021", ORANGE)],
        ["Utilização (transações)", ("2020–2021", ORANGE)],
        ["Composição (% MB)", "2016"]]
table(sl, 8.12, 3.86, 4.33, rows, [0.55, 0.45], body_size=12, row_h=0.30, head_h=0.32,
      head_size=11)

callout(sl, 8.12, 5.26, 4.33, 1.06,
        "Por que 2020 e não 2016",
        "É a única data identificada simultaneamente nas dimensões de penetração e utilização, "
        "aparece como quebra dominante em 5 das 6 séries (p < 0,01) e coincide com marcos "
        "institucionais conhecidos.",
        accent=BLUE, tint=BLUE_L, tsize=13, bsize=12)
source(sl, "Janela adotada: 2014–2019 (pré) e 2020–2023 (pós).  Ressalva assumida: o Bai-Perron também detecta quebras em 2014–2016 e 2018–2019 — janelas de ruptura institucional.",
       t=6.52, w=7.30)
notes(sl, "Antes de comparar antes e depois, preciso saber quando. Três testes formais. "
          "O sup-Wald aponta 2020-2021 em cinco das seis séries. Escolho t* = 2020 porque é "
          "a única data que aparece ao mesmo tempo em penetração e utilização, e porque tem "
          "interpretação econômica clara: pandemia e Pix. A ressalva do rodapé é importante e "
          "eu volto a ela. (~55s)")

# --- 19. Exposição
sl = s_content("Construção da exposição ex-ante Eᵢ", kicker="Capítulo 3 · Etapa 2")
tf = textbox(sl, ML, 1.48, 6.10, 0.3)
para(tf, "CINCO VARIÁVEIS PRÉ-CHOQUE (2009–2013) → PRIMEIRA COMPONENTE PRINCIPAL",
     11, bold=True, color=ORANGE, first=True, space_after=0)
rows = [["Variável", "Leitura teórica", "Loading"],
        ["− ln(PIB real)", "Municípios menores absorvem pior a perda de cobertura", ("0,64", ORANGE)],
        ["ICB", "Mercados concentrados são vulneráveis à saída de uma instituição", ("0,59", ORANGE)],
        ["Densidade ag./PIB", "Maior dependência da infraestrutura física", "0,43"],
        ["− IRC", "Sistema bancário sub-representado frente ao PIB", "0,17"],
        ["PLP", "Público menos bancarizado, menos propenso a migrar de canal", "0,16"]]
table(sl, ML, 1.82, 6.10, rows, [0.26, 0.56, 0.18], body_size=11.5, row_h=0.44,
      head_h=0.34, head_size=11,
      align=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER])

kpi(sl, ML, 4.32, 2.95, 0.98, "44,6%", "da variância na PC1",
    "todos os loadings com o mesmo sinal", accent=BLUE, tint=BLUE_L, vsize=23, lsize=11.5)
kpi(sl, 3.83, 4.32, 2.97, 0.98, "1.904", "municípios sem cobertura prévia",
    "34% do total — quarto braço analítico", accent=ORANGE, tint=ORANGE_L, vsize=23, lsize=11.5)

callout(sl, ML, 5.46, 6.10, 1.00,
        "Leitura do score",
        "Eᵢ é um gradiente unidimensional de “vulnerabilidade à substituição digital”. "
        "Quanto maior, mais o município dependia da infraestrutura física e menos tinha como "
        "absorver o choque sem perder cobertura. Só dados pré-2014 entram, para evitar "
        "contaminação por antecipação.",
        accent=BLUE, tint=BLUE_L, tsize=13, bsize=12.5)

pic(sl, F("fig-mapa-exposicao-1.png"), 7.10, 1.44, 5.45, 5.00)
tf = textbox(sl, 7.10, 6.44, 5.45, 0.26)
para(tf, "Medianas: Nordeste +0,77 · Norte +0,50 · Centro-Oeste +0,04 · Sudeste −0,05 · "
         "semiárido +0,88", 10, color=GRAY, italic=True, first=True, space_after=0)
notes(sl, "A exposição é a primeira componente principal de cinco variáveis pré-2014. "
          "Explica 44,6% da variância, com todos os loadings do mesmo sinal — o que valida a "
          "leitura unidimensional. Os maiores pesos: tamanho econômico e concentração bancária. "
          "O mapa mostra que a exposição tem geografia contígua — e é isso que justifica o "
          "modelo espacial mais adiante. (~55s)")

# =============================================================================
# V. RESULTADOS
# =============================================================================
SECTION = "V. Resultados (Capítulo 3)"
s_divider("V", "Resultados",
          ["Event study e DiD contínuo · Heterogeneidade por porte · Spillovers espaciais",
           "Mediação causal · Assimetria distribucional · Robustez"])

# --- 21. Event study
sl = s_content("Event study: a convergência interrompida", kicker="Resultados · Eixo i")
pic(sl, F("fig-eventstudy-nag-1.png"), ML, 1.46, 7.30, 4.90)
tf = textbox(sl, 8.30, 1.50, 4.15, 0.3)
para(tf, "TRÊS PADRÕES", 11.5, bold=True, color=ORANGE, first=True, space_after=6)
bullets(sl, [
    "Coeficientes pré-2020 positivos e caindo monotonicamente rumo a zero (+0,043 em k=−6 → +0,013 em k=−2).",
    "Coeficientes pós-2020 estabilizam em ≈ +0,007, claramente fora da trajetória que apontava para zero.",
    "O ponto de inflexão coincide exatamente com t* = 2020.",
], 8.30, 1.86, 4.15, size=12.5, gap=0.12)

callout(sl, 8.30, 3.86, 4.15, 2.56,
        "A leitura correta (e a ressalva honesta)",
        "Coeficientes pré positivos implicam que tendências paralelas estritas são rejeitadas: "
        "entre 2014 e 2019 havia convergência intermunicipal no acesso à infraestrutura física.\n\n"
        "Depois de 2020 essa convergência cessa e o gap congela.\n\n"
        "Logo, o coeficiente médio negativo do DiD deve ser lido como efeito contrafactual sobre "
        "a continuidade da convergência — não como redução absoluta do estoque nos municípios expostos.",
        accent=ORANGE, tint=ORANGE_L, tsize=13, bsize=12)
notes(sl, "Este slide exige precisão. Os coeficientes pré-tratamento são positivos e "
          "decrescentes — ou seja, havia convergência entre municípios. Tendências paralelas "
          "estritas são rejeitadas, e eu digo isso abertamente. O que 2020 faz é congelar essa "
          "convergência. Por isso o coeficiente negativo do DiD é 'convergência interrompida', "
          "não 'queda absoluta'. Essa distinção volta na mediação e na robustez. (~60s)")

# --- 22. DiD principal
sl = s_content("DiD com tratamento contínuo: os efeitos médios", kicker="Resultados · Tabela central")
rows = [
    ["Desfecho", "Eixo", "Post × Eᵢ", "Leitura"],
    ["ln(n. de agências + 1)", "i", ("−0,016 ***", ORANGE),
     "cada d.p. de exposição associa-se a −1,6% no log do estoque"],
    ["IRC — centralidade", "ii", "−0,003  (p ≈ 0,40)",
     "efeito médio indistinguível de zero — mas esconde sinais opostos"],
    ["ICO — concentração do portfólio", "ii", ("+0,011 ***", ORANGE),
     "o portfólio de crédito local ficou mais concentrado em poucas modalidades"],
    ["IRF / IRE — qualidade do crédito", "iii", ("−0,021 ***", ORANGE),
     "queda de ≈ 2,1% por d.p.: o crédito que sobrou é mais curto e padronizado"],
    ["PLP — liquidez do público", "—", "−  (p < 0,05)", "recuo marginal nos municípios expostos"],
    ["PLB — liquidez dos bancos", "—", "n.s.", "sem resposta estatisticamente distinguível"],
]
table(sl, ML, 1.50, CW, rows, [0.275, 0.075, 0.175, 0.475], body_size=12, row_h=0.42,
      head_h=0.38, head_size=12,
      align=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT])
source(sl, "Painel 2014–2023 (agências truncado em 2022). Efeitos fixos de município e ano, controle ln(PIB real), erros-padrão clusterizados. *** p < 0,01.",
       t=4.50)

tf = textbox(sl, ML, 4.82, CW, 0.3)
para(tf, "OS TRÊS ACHADOS QUE SUSTENTAM O ARGUMENTO", 11.5, bold=True, color=ORANGE,
     first=True, space_after=0)
x = ML
for i, (t1, t2) in enumerate([
        ("Menos agências", "A convergência intermunicipal em cobertura física congela após 2020."),
        ("Portfólio mais concentrado", "Menos modalidades de crédito disponíveis localmente."),
        ("Menos crédito longo", "Queda da participação dos financiamentos frente aos empréstimos curtos.")]):
    rect(sl, x, 5.16, 3.84, 1.24, fill=BLUE_L)
    rect(sl, x, 5.16, 0.05, 1.24, fill=BLUE)
    tf = textbox(sl, x + 0.26, 5.34, 3.35, 0.92)
    para(tf, t1, 14.5, bold=True, color=BLUE, first=True, space_after=5)
    para(tf, t2, 12.5, color=INK, space_after=0, line=1.15)
    x += 4.05
notes(sl, "Esta é a tabela central. Três resultados: menos agências, portfólio mais "
          "concentrado e queda expressiva da qualidade do crédito. E um resultado aparentemente "
          "nulo — o IRC. Guardem esse zero: os próximos três slides mostram que ele é a soma de "
          "movimentos opostos que se cancelam. Longe de democratizar o crédito periférico, a "
          "digitalização alterou-o qualitativamente para pior. (~65s)")

# --- 23. Heterogeneidade
sl = s_content("Heterogeneidade por porte: o viés metropolitano é qualificado",
               kicker="Resultados · H3")
tf = textbox(sl, ML, 1.46, CW, 0.28)
para(tf, "Desvios em relação à faixa P4 (PIB acima de R$ 2 bilhões, referência). "
         "δp < 0 indica que a faixa piorou mais que as metrópoles.",
     12.5, color=GRAY, italic=True, first=True, space_after=0)
rows = [
    ["Faixa de PIB real (2009)", "ln(n. agências)", "IRC", "IRF / IRE", "ICO"],
    ["P1 — até R$ 100 mi", "n.s.", ("−2,5 p.p. ***", ORANGE), "—", "—"],
    ["P2 — R$ 100–500 mi", "n.s.", ("−2,9 p.p. ***", ORANGE), ("−17 p.p. ***", ORANGE), ("+ ***", ORANGE)],
    ["P3 — R$ 500 mi–2 bi", ("+8,1 p.p. ***", GREEN), ("−2,7 p.p. ***", ORANGE), ("−13 p.p. ***", ORANGE), ("+ ***", ORANGE)],
    ["P4 — acima de R$ 2 bi", "referência", "referência", "referência", "referência"],
]
table(sl, ML, 1.86, CW, rows, [0.30, 0.18, 0.16, 0.18, 0.18], body_size=12.5,
      row_h=0.40, head_h=0.38, head_size=12)

callout(sl, ML, 4.02, 5.85, 1.44,
        "Cobertura física: efeito nas duas pontas",
        "A retração não é monotônica na dependência física. Ela se concentra nas metrópoles "
        "(substituição ativa pela digitalização avançada) e nas pequenas (inviabilidade econômica). "
        "A faixa médio-grande preservou melhor a rede — provavelmente pelo papel de hub regional.",
        accent=BLUE, tint=BLUE_L, tsize=13, bsize=12.5)
callout(sl, 6.79, 4.02, 5.84, 1.44,
        "Centralidade e qualidade: gradiente inequívoco",
        "O IRC caiu mais nas três faixas inferiores do que nas metrópoles, e a razão IRF/IRE traz "
        "o gradiente mais pronunciado (−17 p.p. em P2). O crédito sofisticado se concentrou nas "
        "grandes cidades; às médias sobrou uma carteira dominada por empréstimos curtos.",
        accent=ORANGE, tint=ORANGE_L, tsize=13, bsize=12.5)

tf = textbox(sl, ML, 5.62, CW, 0.9)
rich(tf, [("H3 é confirmada, mas qualificada: ", {"bold": True, "color": BLUE, "size": 14}),
          ("o viés metropolitano não se manifesta da mesma forma em todas as dimensões. "
           "No estoque de agências ele opera nas pontas; nas variáveis de centralidade e "
           "qualidade, opera de forma monotônica, com os centros consolidando posições relativas. "
           "A dependência de canais físicos não se traduz linearmente em perda de agências — "
           "o que decide é a função que a agência cumpre no território.",
           {"size": 14, "color": INK})], first=True, line=1.18)
notes(sl, "Aqui a hipótese inicial precisou ser corrigida. Eu esperava um gradiente linear na "
          "dependência física. Não é isso. No estoque de agências o efeito é em U invertido: as "
          "pontas perdem, o meio se preserva. Já em centralidade e qualidade o gradiente é "
          "monotônico e claro. A lição: o que decide não é o quanto o município dependia da "
          "agência, é a função que aquela agência cumpria. (~60s)")

# --- 24. SLX
sl = s_content("Spillovers espaciais (SLX-DiD): o território como vasos comunicantes",
               kicker="Resultados · achado central")
tf = textbox(sl, ML, 1.46, CW, 0.36, align=PP_ALIGN.CENTER)
rich(tf, [("Y", {"size": 17, "bold": True, "color": BLUE}), ("it", {"size": 11, "color": BLUE, "sub": True}),
          ("  =  α", {"size": 17, "color": INK}), ("i", {"size": 11, "color": INK, "sub": True}),
          ("  +  λ", {"size": 17, "color": INK}), ("t", {"size": 11, "color": INK, "sub": True}),
          ("  +  β · (Post × E", {"size": 17, "color": INK}), ("i", {"size": 11, "color": INK, "sub": True}),
          (")  +  ", {"size": 17, "color": INK}),
          ("θ · (Post × W E", {"size": 17, "bold": True, "color": ORANGE}),
          ("i", {"size": 11, "bold": True, "color": ORANGE, "sub": True}),
          (")", {"size": 17, "bold": True, "color": ORANGE}),
          ("  +  γ X", {"size": 17, "color": INK}), ("it", {"size": 11, "color": INK, "sub": True}),
          ("  +  ε", {"size": 17, "color": INK}), ("it", {"size": 11, "color": INK, "sub": True})],
     first=True, space_after=0, align=PP_ALIGN.CENTER)
tf = textbox(sl, ML, 1.86, CW, 0.28, align=PP_ALIGN.CENTER)
para(tf, "W = contiguidade rainha, row-normalizada (malha IBGE 2020 via geobr; 5.568 municípios em subgrafo único)  ·  "
         "β = efeito direto, θ = spillover", 11.5, color=GRAY, first=True, space_after=0,
     align=PP_ALIGN.CENTER)

rows = [["Desfecho", "Efeito direto (β)", "Spillover (θ)", "Interpretação"],
        ["ln(n. de agências)", ("−2,2%", ORANGE), ("+2,7%", GREEN),
         "o município perde a agência; a vizinhança a ganha"],
        ["IRC — centralidade", ("negativo", ORANGE), ("positivo", GREEN),
         "a centralidade migra para os polos adjacentes"],
        ["ICO — concentração", ("positivo", ORANGE), ("negativo", GREEN),
         "o portfólio local se estreita; o dos vizinhos se diversifica"],
        ["IRF / IRE — qualidade", ("fortemente negativo", ORANGE), ("positivo", GREEN),
         "o crédito longo sai da periferia e reaparece no entorno"]]
table(sl, ML, 2.30, CW, rows, [0.235, 0.185, 0.16, 0.42], body_size=12.5, row_h=0.42,
      head_h=0.38, head_size=12,
      align=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT])

callout(sl, ML, 4.58, 5.85, 1.42,
        "Nos quatro desfechos, efeito direto e spillover têm sinais opostos",
        "A digitalização não eliminou agências, centralidade, diversidade ou crédito longo do "
        "território. Ela os reorganizou no espaço, transferindo-os dos municípios mais vulneráveis "
        "para suas vizinhanças mais centrais.",
        accent=ORANGE, tint=ORANGE_L, tsize=13, bsize=12.5)
callout(sl, 6.79, 4.58, 5.84, 1.42,
        "Por que isso explica o “zero” do IRC",
        "|θ| é da mesma ordem de |β|, às vezes maior. O coeficiente médio do DiD não espacial é "
        "uma mistura de efeitos diretos e indiretos de sinais opostos: parte do efeito direto "
        "negativo era cancelada por um spillover positivo.",
        accent=BLUE, tint=BLUE_L, tsize=13, bsize=12.5)
tf = textbox(sl, ML, 6.10, CW, 0.5)
rich(tf, [("Evidência mais robusta da dissertação: ", {"bold": True, "color": BLUE, "size": 14}),
          ("o viés metropolitano não é apenas declínio diferenciado entre faixas — é uma "
           "transferência territorial identificável, das próprias periferias para os polos adjacentes.",
           {"size": 14, "color": INK})], first=True, line=1.18)
notes(sl, "Este é o resultado mais forte do trabalho. Nos quatro desfechos, efeito direto e "
          "spillover têm sinais opostos e magnitudes comparáveis. O que sai de um município "
          "reaparece no vizinho. Isso resolve o enigma do slide anterior: o IRC médio dá zero "
          "porque o efeito direto negativo é cancelado por um spillover positivo que os efeitos "
          "fixos absorviam sem aviso. É deslocamento, não desaparecimento. (~70s)")

# --- 25. Mediação
sl = s_content("Mediação causal: por onde o efeito viaja?", kicker="Resultados · H5")
tf = textbox(sl, ML, 1.44, CW, 0.28)
para(tf, "Arcabouço de Imai, Keele & Tingley (2010) adaptado a painel com efeitos fixos  ·  "
         "3.636 municípios, 29.970 observações, 2014–2022  ·  bootstrap de blocos (B = 500)",
     11.5, color=GRAY, italic=True, first=True, space_after=0)

# diagrama
box_t = 1.90
rect(sl, ML, box_t + 0.62, 2.65, 0.92, fill=ORANGE_L)
rect(sl, ML, box_t + 0.62, 0.05, 0.92, fill=ORANGE)
tf = textbox(sl, ML + 0.24, box_t + 0.74, 2.25, 0.70)
para(tf, "TRATAMENTO", 10.5, bold=True, color=ORANGE, first=True, space_after=3)
para(tf, "Post × Eᵢ", 15, bold=True, color=BLUE, space_after=1)
para(tf, "exposição ao choque digital", 10.5, color=GRAY, space_after=0)

rect(sl, 4.72, box_t, 2.65, 0.92, fill=BLUE_L)
rect(sl, 4.72, box_t, 0.05, 0.92, fill=BLUE)
tf = textbox(sl, 4.72 + 0.24, box_t + 0.12, 2.25, 0.70)
para(tf, "MEDIADORA (M)", 10.5, bold=True, color=BLUE, first=True, space_after=3)
para(tf, "ln(n. agências + 1)", 15, bold=True, color=BLUE, space_after=1)
para(tf, "estoque físico municipal", 10.5, color=GRAY, space_after=0)

rect(sl, 9.44, box_t + 0.62, 3.19, 0.92, fill=ORANGE_L)
rect(sl, 9.44, box_t + 0.62, 0.05, 0.92, fill=ORANGE)
tf = textbox(sl, 9.44 + 0.24, box_t + 0.74, 2.8, 0.70)
para(tf, "DESFECHO (Y)", 10.5, bold=True, color=ORANGE, first=True, space_after=3)
para(tf, "IRF / IRE", 15, bold=True, color=BLUE, space_after=1)
para(tf, "qualidade do crédito local", 10.5, color=GRAY, space_after=0)

# setas
def arrow(l, t, w, h, rot=0):
    s = sl.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, In(l), In(t), In(w), In(h))
    s.fill.solid(); s.fill.fore_color.rgb = RGBColor(0xC3, 0xC9, 0xD4)
    s.line.fill.background(); s.shadow.inherit = False
    s.rotation = rot
    return s

arrow(3.45, box_t + 0.72, 1.15, 0.20, rot=-22)
arrow(7.52, box_t + 0.72, 1.75, 0.20, rot=22)
arrow(3.45, box_t + 1.72, 5.82, 0.22, rot=0)

tf = textbox(sl, 3.32, box_t + 0.36, 1.45, 0.3, align=PP_ALIGN.CENTER)
para(tf, "δ = +0,0200 ***", 12, bold=True, color=BLUE, first=True, space_after=0)
tf = textbox(sl, 7.55, box_t + 0.36, 1.75, 0.3, align=PP_ALIGN.CENTER)
para(tf, "ψ = +0,2346 ***", 12, bold=True, color=BLUE, first=True, space_after=0)
tf = textbox(sl, 4.30, box_t + 1.98, 4.20, 0.3, align=PP_ALIGN.CENTER)
para(tf, "ADE  φ = −0,0105 **   (canal direto, tecnológico)", 12, bold=True, color=ORANGE,
     first=True, space_after=0)

rows = [["Componente", "Estimativa", "IC 95% (bootstrap)", "Sinal"],
        ["ACME — efeito mediado (δ × ψ)", "+0,0047", "[+0,003 ; +0,006]", ("positivo", GREEN)],
        ["ADE — efeito direto (φ)", "−0,0105", "significativo a 5%", ("negativo", ORANGE)],
        ["τ — efeito total", "−0,0058", "[−0,015 ; +0,003]", "atenuado, inclui zero"]]
table(sl, ML, 4.56, 6.62, rows, [0.40, 0.20, 0.24, 0.16], body_size=11.5, row_h=0.42,
      head_h=0.34, head_size=11,
      align=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER])

callout(sl, 7.55, 4.56, 5.08, 1.88,
        "Suppression effect: H5 precisa ser reformulada",
        "Os dois canais empurram o IRF/IRE em direções opostas e quase se cancelam — a mediação "
        "inconsistente de MacKinnon et al. (2007).\n\n"
        "A relação estrutural agência → crédito longo se confirma (ψ > 0), mas nesta subamostra o "
        "canal dominante é o tecnológico. H5 vale para as periferias mais frágeis — justamente as "
        "que a restrição amostral exclui.",
        accent=ORANGE, tint=ORANGE_L, tsize=13, bsize=11.5)
notes(sl, "Aqui a hipótese H5 foi corrigida pelos dados. ψ positivo e forte confirma o elo "
          "teórico: onde há agência, há mais crédito longo. Mas o efeito mediado deu positivo e "
          "o efeito direto negativo — eles se cancelam. É um suppression effect. A explicação é "
          "amostral: a razão IRF/IRE só é definida onde existe mercado de crédito, o que exclui "
          "justamente as periferias onde o fechamento foi agudo. Conclusão: a agência não é um "
          "elo causal universal — seu papel mediador é ele próprio territorialmente heterogêneo. (~75s)")

# --- 26. Quantílica
sl = s_content("Assimetria distribucional: o que a média esconde",
               kicker="Resultados · quantílica espacial (Canay, 2011)")
pic(sl, F("fig-quantilica-1.png"), ML, 1.50, 7.20, 4.00)
tf = textbox(sl, ML, 5.62, 7.20, 0.28)
para(tf, "Estimador em duas etapas de Canay (2011); IC 95% por bootstrap de blocos por município (B = 200).",
     10.5, color=GRAY, italic=True, first=True, space_after=0)

tf = textbox(sl, 8.20, 1.52, 4.25, 0.3)
para(tf, "IRC — EROSÃO CONCENTRADA NO TOPO", 11, bold=True, color=BLUE, first=True, space_after=6)
tf = textbox(sl, 8.20, 1.86, 4.25, 0.9)
para(tf, "OLS-FE médio: −0,003 (p ≈ 0,40). Os quantis 0,10 a 0,75 ficam próximos de zero; só em "
         "τ = 0,90 aparece coeficiente claramente negativo (−0,007; IC [−0,012; −0,001]).",
     12.5, color=INK, first=True, space_after=0, line=1.16)
tf = textbox(sl, 8.20, 2.86, 4.25, 0.6)
para(tf, "A digitalização não mexeu no nível de centralidade da maioria — erodiu, na margem, "
         "a posição relativa de quem já estava no topo.", 12.5, color=GRAY, italic=True,
     first=True, space_after=0, line=1.16)

rect(sl, 8.20, 3.62, 4.25, 0.012, fill=RULE)
tf = textbox(sl, 8.20, 3.78, 4.25, 0.3)
para(tf, "IRF/IRE — PERFIL EM U ASSIMÉTRICO", 11, bold=True, color=ORANGE, first=True, space_after=6)
rows = [["τ", "Coeficiente"],
        ["0,10", ("−0,023 ***", ORANGE)],
        ["0,25", ("−0,016 ***", ORANGE)],
        ["0,50", ("−0,009 ***", ORANGE)],
        ["0,75", "−0,002  n.s."],
        ["0,90", ("−0,012 ***", ORANGE)],
        ["OLS-FE", "−0,022 ***"]]
table(sl, 8.20, 4.12, 2.05, rows, [0.42, 0.58], body_size=11.5, row_h=0.29, head_h=0.30,
      head_size=11, highlight_rows=(6,))
tf = textbox(sl, 10.45, 4.16, 2.00, 2.30)
para(tf, "Onde o crédito longo já era escasso, a digitalização aprofundou a escassez.",
     12.5, color=INK, first=True, space_after=8, line=1.16)
para(tf, "Mesmo o topo perdeu: a distribuição foi achatada em direção à mediana.",
     12.5, color=INK, space_after=8, line=1.16)
para(tf, "Só o 3º quartil escapou — hipótese institucional: cooperativas e bancos públicos.",
     12.5, color=GRAY, italic=True, space_after=0, line=1.16)
notes(sl, "A média responde se o efeito é positivo ou negativo no município típico. Não é a "
          "minha pergunta. A quantílica mostra duas coisas. No IRC, o zero médio não é "
          "cancelamento simétrico: é efeito concentrado no topo. No IRF/IRE, o perfil é em U "
          "assimétrico — a perda é máxima exatamente onde o crédito longo já era escasso. "
          "Centralidade e qualidade do crédito se descolaram. (~60s)")

# --- 27. Robustez
sl = s_content("Robustez: o que resiste e o que exige cautela", kicker="Resultados · validação")
rows = [
    ["Exercício", "Procedimento", "Resultado", "Veredito"],
    ["Controles reais", "Composição setorial do VAB, ln(vínculos RAIS) e share SIMPLES",
     "Sinal, magnitude e significância mantidos; variação típica < 10%", ("Sustenta", GREEN)],
    ["Placebo (t falso = 2014)", "Janela 2009–2018, anterior ao choque real",
     "IRF/IRE: −0,0017 n.s. vs. −0,021 real (>10×). ICO e agências: razão ≈ 4×", ("Sustenta", GREEN)],
    ["DiD sintético", "Tercil superior vs. inferior de Eᵢ (Arkhangelsky et al., 2021)",
     "Sinais divergem em IRF/IRE, ICO, agências e IRC na comparação binária", ("Cautela", ORANGE)],
    ["Matrizes W alternativas", "k = 5 vizinhos mais próximos e distância inversa (corte 200 km)",
     "Spillovers de magnitude comparável aos diretos persistem; sinal pontual varia", ("Sustenta", GREEN)],
]
table(sl, ML, 1.50, CW, rows, [0.19, 0.28, 0.375, 0.155], body_size=11.5, row_h=0.62,
      head_h=0.38, head_size=12,
      align=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER])

callout(sl, ML, 4.42, 5.85, 1.32,
        "A ressalva que assumo",
        "O DiD sintético exige binarização e corrige tendências pré via pesos sintéticos. O tercil "
        "inferior de Eᵢ concentra as metrópoles — que também perderam agências. O estimador acaba "
        "comparando perda na periferia contra perda no centro, e a magnitude relativa pode inverter o sinal.",
        accent=ORANGE, tint=ORANGE_L, tsize=13, bsize=12)
callout(sl, 6.79, 4.42, 5.84, 1.32,
        "O que fica de pé",
        "O cerne da inferência é o gradiente contínuo do DiD, complementado pelos achados espaciais e "
        "de heterogeneidade. Estimadores que exigem binarização ou correção sintética entram como apoio, "
        "não como substitutos. O sentido dos achados se mantém; a magnitude média em subamostras "
        "balanceadas é sensível ao estimador.",
        accent=BLUE, tint=BLUE_L, tsize=13, bsize=12)
notes(sl, "Quatro exercícios. Controles reais, placebo e matrizes alternativas sustentam os "
          "achados. O DiD sintético diverge, e eu não escondo isso: reporto e explico por quê. "
          "A binarização compara perda na periferia contra perda no centro, e nessa comparação o "
          "sinal pode inverter. Reconheço como limitação nas considerações finais. (~55s)")

# =============================================================================
# VI. ESTUDOS DE CASO
# =============================================================================
SECTION = "VI. Estudos de caso territoriais (Minas Gerais)"
s_divider("VI", "Estudos de caso territoriais",
          ["Minas Gerais — Belo Horizonte, Juiz de Fora, Betim e Almenara",
           "O que o coeficiente médio esconde"])

# --- 29. Mapa MG
sl = s_content("Os quatro casos no território mineiro", kicker="Capítulo 3 · camada qualitativa")
pic(sl, F("fig-mapa-mg-1.png"), ML - 0.15, 1.42, 7.05, 5.05)
tf = textbox(sl, 7.45, 1.50, 5.00, 0.3)
para(tf, "CRITÉRIO DE SELEÇÃO", 11.5, bold=True, color=ORANGE, first=True, space_after=6)
tf = textbox(sl, 7.45, 1.84, 5.00, 0.95)
para(tf, "Quatro níveis distintos de centralidade financeira, percorrendo o eixo centro–periferia "
         "que organiza a leitura pós-keynesiana. Mesmo estado: banco de fomento (BDMG), fontes "
         "auxiliares e regulação estadual constantes.",
     13, color=INK, first=True, space_after=0, line=1.16)
kpi(sl, 7.45, 2.94, 2.42, 1.16, "49,1%", "dos municípios de MG\nsem agência",
    "419 de 853, em 2022", accent=ORANGE, tint=ORANGE_L, vsize=22, lsize=11)
kpi(sl, 10.03, 2.94, 2.42, 1.16, "0,076", "mediana estadual\nde IRF/IRE", 
    "abaixo da mediana nacional (0,102)", accent=BLUE, tint=BLUE_L, vsize=22, lsize=11)
callout(sl, 7.45, 4.28, 5.00, 2.14,
        "Estrutura de cada caso",
        "1.  Caracterização do município e posição no score Eᵢ\n"
        "2.  Trajetória 2009–2023 dos indicadores municipais\n"
        "3.  Confronto entre o previsto pelo modelo e o observado\n"
        "4.  Leitura do contexto institucional local\n\n"
        "Mesmo em um estado com banco de fomento próprio, o financiamento de longo prazo "
        "responde por parcela pequena do crédito local.",
        accent=BLUE, tint=BLUE_L, tsize=13, bsize=12.5)
notes(sl, "Os modelos trabalham com a média de 3.666 municípios. Aqui eu desço ao território. "
          "Quatro casos em Minas, percorrendo o eixo centro-periferia, com o estado mantido "
          "constante para evitar ruído de comparação interestadual. (~40s)")

# --- 30. Gradiente comparativo
sl = s_content("O gradiente dos quatro casos: mesma média, trajetórias opostas",
               kicker="Estudos de caso · síntese")
casos = [
    ("Belo Horizonte", "Metrópole consolidada", "314 agências", [
        ("Agências 2014–22", "−33%", ORANGE),
        ("IRC", "1,79 → 2,62  (+47%)", GREEN),
        ("IRF/IRE 2015→2022", "1,28 → 0,52", ORANGE)],
     "Perde rede física, mas ganha centralidade relativa porque o entorno perde mais."),
    ("Juiz de Fora", "Cidade média de centralidade regional", "46 agências", [
        ("Agências 2014–22", "−21%", GREEN),
        ("IRC", "0,76 (estável)", GREEN),
        ("IRF/IRE 2022", "0,24", INK)],
     "Âncoras institucionais (UFJF, base de serviços) sustentam a função bancária local."),
    ("Betim", "Polo industrial, periferia financeira", "16 agências", [
        ("Agências 2014–22", "−36%", ORANGE),
        ("IRC", "−70%  →  0,12", ORANGE),
        ("IRF/IRE 2022", "0,19", INK)],
     "PIB acima de R$ 20 bi e acesso digital pleno não impediram a perda: falta base financeira própria."),
    ("Almenara", "Polo microrregional do Baixo Jequitinhonha", "5 agências", [
        ("Agências 2014–22", "0%  (nenhuma fechou)", GREEN),
        ("IRC", "1,10", GREEN),
        ("IRF/IRE 2014–22", "−43%", ORANGE)],
     "Bancos públicos preservam a rede, mas não impedem a deterioração do crédito longo."),
]
x = ML
for nome, sub, ag, met, leitura in casos:
    rect(sl, x, 1.48, 2.87, 4.34, fill=RGBColor(0xFA, 0xFB, 0xFC))
    rect(sl, x, 1.48, 2.87, 0.05, fill=ORANGE)
    tf = textbox(sl, x + 0.24, 1.66, 2.42, 0.34)
    para(tf, nome, 16, bold=True, color=BLUE, first=True, space_after=2)
    tf = textbox(sl, x + 0.24, 2.00, 2.42, 0.55)
    para(tf, sub, 11.5, color=GRAY, first=True, space_after=3, line=1.1)
    tf = textbox(sl, x + 0.24, 2.56, 2.42, 0.26)
    para(tf, ag + " (2022)", 12, bold=True, color=ORANGE, first=True, space_after=0)
    yy = 2.92
    for lab, val, cor in met:
        tf = textbox(sl, x + 0.24, yy, 2.42, 0.22)
        para(tf, lab, 10.5, color=GRAY, first=True, space_after=1)
        tf = textbox(sl, x + 0.24, yy + 0.20, 2.42, 0.26)
        para(tf, val, 13.5, bold=True, color=cor, first=True, space_after=0)
        yy += 0.52
    rect(sl, x + 0.24, 4.56, 2.42, 0.012, fill=RULE)
    tf = textbox(sl, x + 0.24, 4.70, 2.42, 1.0)
    para(tf, leitura, 12, color=INK, first=True, space_after=0, line=1.16)
    x += 3.02

callout(sl, ML, 5.96, CW, 0.62,
        "",
        "O mesmo β da regressão agrega municípios cuja função financeira é completamente diferente. "
        "Uma recomendação de política baseada na média agregada falharia em três dos quatro territórios estudados.",
        accent=ORANGE, tint=ORANGE_L, tsize=1, bsize=13.5)
notes(sl, "Aqui está a razão de existir da camada qualitativa. BH perde um terço da rede e ainda "
          "assim ganha 47% de centralidade — porque o entorno perde mais. Betim tem PIB de 20 "
          "bilhões, acesso digital pleno, e perde mais que Juiz de Fora, que tem metade do PIB. "
          "E Almenara não fechou nenhuma agência e mesmo assim viu o crédito longo cair 43%. "
          "Quatro trajetórias radicalmente diferentes sob o mesmo coeficiente médio. (~70s)")

# --- 31. Quadrantes
sl = s_content("O plano centralidade × qualidade do crédito", kicker="Estudos de caso · síntese comparativa")
pic(sl, F("fig-quadrantes-1.png"), ML - 0.15, 1.42, 7.05, 5.05)
tf = textbox(sl, 7.45, 1.50, 5.00, 0.3)
para(tf, "DUAS LEITURAS APRESSADAS QUE CAEM POR TERRA", 11, bold=True, color=ORANGE,
     first=True, space_after=8)
bullets(sl, [
    ("O quadrante desejável não é metropolitano.", "As três melhores posições são de Tangará da Serra (MT), "
     "Querência (MT) e Chapadão do Sul (MS): o crédito rural direcionado eleva simultaneamente "
     "financiamento e participação no crédito nacional. O Centro-Oeste é 8,9% da amostra e 19,6% do quadrante I."),
    ("Cobertura física ≠ função financeira.", "Almenara, com 5 agências no Jequitinhonha, ocupa posição melhor "
     "no plano do que Betim, com 16 agências na RMBH. Betim é o único dos quatro casos fora do quadrante I."),
], 7.45, 1.88, 5.00, size=12.5, gap=0.14)

kpi(sl, 7.45, 4.38, 2.42, 1.08, "323", "municípios com IRF = 0",
    "sem razão a calcular:\nexclusão qualitativa extrema", accent=ORANGE, tint=ORANGE_L,
    vsize=22, lsize=11)
kpi(sl, 10.03, 4.38, 2.42, 1.08, "67%", "dos municípios de MG",
    "nos quadrantes II e III,\nabaixo da mediana nacional", accent=BLUE, tint=BLUE_L,
    vsize=22, lsize=11)
callout(sl, 7.45, 5.58, 5.00, 0.86,
        "O avesso: São Francisco do Conde (BA)",
        "Sede de refinaria e um dos maiores PIB per capita do país, ocupa a pior posição do plano — "
        "produz muito e retém quase nada de crédito. É a drenagem financeira de Crocco et al. (2006) "
        "em estado quase puro.",
        accent=BLUE, tint=BLUE_L, tsize=12.5, bsize=12)
notes(sl, "Este plano cruza os eixos ii e iii. Duas surpresas. Primeira: o quadrante desejável "
          "não pertence às metrópoles — pertence ao agronegócio do Centro-Oeste, onde o crédito "
          "rural direcionado sustenta o financiamento longo. Segunda: Almenara, com 5 agências, "
          "está melhor posicionada que Betim, com 16. Cobertura física e função financeira são "
          "dimensões distintas. (~55s)")

# =============================================================================
# VII. IMPLICAÇÕES E CONCLUSÕES
# =============================================================================
SECTION = "VII. Implicações e considerações finais"
s_divider("VII", "Implicações e conclusões",
          ["Simulações contrafactuais e implicações regulatórias",
           "Balanço das hipóteses, contribuições e limitações"])

# --- 33. Contrafactuais
sl = s_content("Três simulações contrafactuais", kicker="Camada normativa")
cen = [
    ("CENÁRIO 1", "Redução de 50% no fechamento de agências",
     "E se o fechamento nos municípios mais expostos tivesse caído pela metade após 2020?",
     "Um município com Eᵢ = +1 perderia 0,8% em vez de 1,6% do log do estoque. É alívio, não reversão. "
     "E o SLX acrescenta: o fechamento não é só perda líquida, é realocação — a agência fecha em um "
     "lugar e reabre alguns quilômetros adiante.",
     "Reduzir o fechamento na origem frearia a concentração espacial induzida por essa realocação."),
    ("CENÁRIO 2", "Homogeneização da exposição digital",
     "Se todos os municípios tivessem, em 2014, a infraestrutura digital de uma metrópole?",
     "Reduziria a vulnerabilidade, mas não eliminaria o problema. O que determina a resiliência da "
     "cobertura não é só conectividade — é a densidade do mercado bancário local. Betim tinha acesso "
     "digital pleno e perdeu 36% das agências; Juiz de Fora, metade do PIB, perdeu 21%.",
     "Inclusão digital sozinha não resolve exclusão financeira territorial."),
    ("CENÁRIO 3", "Piso de uma agência por município",
     "Se todo município com ao menos uma agência em 2019 a mantivesse até 2023?",
     "A mediação responde pela negativa: o suppression effect mostra que a digitalização reduz o "
     "IRF/IRE por um canal que não passa pela quantidade de agências. Almenara é o caso-limite — "
     "5 agências mantidas e queda de 43% na razão.",
     "O que muda não é a presença da agência, é o que a agência faz."),
]
y = 1.48
for tag, tit, perg, res, concl in cen:
    rect(sl, ML, y, CW, 1.62, fill=RGBColor(0xFA, 0xFB, 0xFC))
    rect(sl, ML, y, 0.05, 1.62, fill=ORANGE)
    tf = textbox(sl, ML + 0.26, y + 0.14, 3.20, 0.26)
    para(tf, tag, 10.5, bold=True, color=ORANGE, first=True, space_after=3)
    tf = textbox(sl, ML + 0.26, y + 0.40, 3.20, 0.55)
    para(tf, tit, 14, bold=True, color=BLUE, first=True, space_after=4, line=1.08)
    tf = textbox(sl, ML + 0.26, y + 1.00, 3.20, 0.50)
    para(tf, perg, 11, color=GRAY, italic=True, first=True, space_after=0, line=1.14)
    tf = textbox(sl, ML + 3.72, y + 0.16, 5.35, 1.30)
    para(tf, res, 12, color=INK, first=True, space_after=0, line=1.16)
    rect(sl, ML + 9.22, y + 0.16, 0.012, 1.30, fill=RULE)
    tf = textbox(sl, ML + 9.42, y + 0.16, 2.42, 1.30, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, concl, 12, bold=True, color=BLUE, first=True, space_after=0, line=1.16)
    y += 1.72
notes(sl, "Traduzo os coeficientes em três exercícios. Reduzir fechamento alivia mas não "
          "reverte. Homogeneizar conectividade não basta — Betim prova isso. E um piso de "
          "agências não teria evitado a deterioração do crédito longo, porque o canal dominante "
          "é tecnológico. Almenara é o caso-limite dessa terceira conclusão. (~55s)")

# --- 34. Implicações regulatórias
sl = s_content("Implicações regulatórias", kicker="Camada normativa")
imp = [
    ("1", "Migrar a regulação de quantidade de agências para funções financeiras mantidas no território",
     "Manter a agência não garante manter o crédito de longo prazo. O fechamento pode ser compensado por "
     "correspondentes e canais digitais assistidos — desde que tenham escopo funcional equivalente. Os modelos "
     "de service obligation dos setores postal e de telecomunicações são referência adaptável, calibrada por "
     "tempo de deslocamento e vulnerabilidade (Eᵢ), não por quilômetros em linha reta."),
    ("2", "Calibrar os instrumentos de crédito conforme a heterogeneidade espacial",
     "O SLX mostra que o crédito se desloca no espaço; a quantílica mostra que o efeito depende do ponto de "
     "partida de cada município na distribuição. Uma política uniforme produz resultados distintos em Almenara "
     "(bancos públicos sustentam a função) e em Betim (crédito privado curto, função financeira rasa). "
     "Instrumentos possíveis: percentual mínimo de carteira em modalidades longas para municípios abaixo de "
     "certo porte e redesconto condicionado à manutenção de operações de financiamento em regiões periféricas."),
    ("3", "Coordenar regulação bancária, infraestrutura digital e desenvolvimento regional",
     "A dissertação mostrou que conectividade digital não substitui presença institucional (Betim) e que "
     "presença institucional não impede a deterioração do crédito (Almenara). O problema é estrutural: exige "
     "que Banco Central, BNDES e bancos estaduais, ANATEL e o Ministério da Integração atuem de forma "
     "articulada, e não em trilhos separados."),
]
y = 1.50
for num, tit, txt in imp:
    h = 1.62
    rect(sl, ML, y, CW, h, fill=RGBColor(0xFA, 0xFB, 0xFC))
    rect(sl, ML, y, 0.05, h, fill=BLUE)
    tf = textbox(sl, ML + 0.28, y + 0.18, 0.55, 0.45)
    para(tf, num, 26, bold=True, color=ORANGE, first=True, space_after=0)
    tf = textbox(sl, ML + 1.00, y + 0.16, 10.55, 0.4)
    para(tf, tit, 15, bold=True, color=BLUE, first=True, space_after=0, line=1.08)
    tf = textbox(sl, ML + 1.00, y + 0.62, 10.55, 0.92)
    para(tf, txt, 12, color=INK, first=True, space_after=0, line=1.17)
    y += 1.72
notes(sl, "Três recomendações. A primeira é a mais importante e sai diretamente da mediação: "
          "regular funções financeiras, não contagem de agências. A segunda vem do SLX e da "
          "quantílica: política uniforme sobre território heterogêneo produz resultados "
          "desiguais. A terceira é de coordenação institucional. (~50s)")

# --- 35. Balanço das hipóteses
sl = s_content("Balanço das cinco hipóteses", kicker="Considerações finais")
rows = [
    ["", "O que a hipótese previa", "O que a evidência mostrou", "Veredito"],
    ["H1", "Quebra estrutural identificável entre 2015 e 2020",
     "2020 confirmado como inflexão dominante. O choque não é um ponto único: é uma sequência de rupturas (2014–16, 2018–19, 2020–21)",
     ("Sustentada", GREEN)],
    ["H2", "Efeito maior onde havia alta dependência de canais físicos",
     "Direção confirmada, forma desmentida: a contração é não monotônica, concentrada nas duas pontas da distribuição de porte",
     ("Reformulada", ORANGE)],
    ["H3", "A digitalização aprofunda o viés metropolitano",
     "A mais fortalecida. Não é só declínio diferenciado: é transferência territorial identificável (efeito direto e spillover com sinais opostos)",
     ("Sustentada +", GREEN)],
    ["H4", "Efeito assimétrico sobre a qualidade do crédito",
     "Confirmada. Efeito médio nulo sobre centralidade, mas o crédito longo se concentra nos centros e recua nas periferias",
     ("Sustentada", GREEN)],
    ["H5", "O canal de transmissão é o fechamento de agências",
     "Suppression effect. O elo agência → crédito longo se confirma, mas o canal dominante é o tecnológico. Vale só para as periferias mais frágeis",
     ("Reformulada", ORANGE)],
]
table(sl, ML, 1.50, CW, rows, [0.05, 0.245, 0.545, 0.16], body_size=11.5, row_h=0.72,
      head_h=0.36, head_size=11.5,
      align=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER])

callout(sl, ML, 5.62, CW, 0.98,
        "A tese que as cinco convergem para sustentar",
        "A digitalização financeira não é territorialmente neutra. O aprendizado da pesquisa, porém, está "
        "menos no fato de quatro hipóteses terem se sustentado e mais nos pontos em que a evidência obrigou "
        "a abandonar a linearidade: o fechamento não segue a dependência física ponto a ponto, a deterioração "
        "do crédito não vem de um canal só, e o empobrecimento das periferias não é subtração pura — o que "
        "sai delas reaparece nos centros.",
        accent=ORANGE, tint=ORANGE_L, tsize=13.5, bsize=12.5)
notes(sl, "O balanço honesto: quatro sustentadas, duas delas com reformulação. H3 sai mais forte "
          "do que entrou, porque ganhou um mecanismo espacial explícito. H2 e H5 foram corrigidas "
          "pelos dados. E é justamente aí que a pesquisa aprendeu o que não sabia ao começar: "
          "ao desmontar as suposições de uniformidade. (~65s)")

# --- 36. Contribuições e limitações
sl = s_content("Contribuições e limitações", kicker="Considerações finais")
tf = textbox(sl, ML, 1.48, 5.85, 0.3)
para(tf, "QUATRO CONTRIBUIÇÕES", 11.5, bold=True, color=ORANGE, first=True, space_after=0)
contrib = [
    ("Base de dados.", "Painel de indicadores financeiros municipais 2009–2023, integrando fontes "
     "antes usadas separadamente."),
    ("Analítica.", "Decomposição do efeito em canal direto, canal mediado e spillovers espaciais, "
     "combinada à decomposição quantílica."),
    ("Empírica.", "A digitalização não é territorialmente neutra: seus efeitos variam com porte, "
     "posição na hierarquia urbana e base institucional."),
    ("Aplicada.", "Mapeamento entre coeficientes estimados e instrumentos de política — subsídios "
     "regulatórios ancorados em resultados quantificados."),
]
bullets(sl, contrib, ML, 1.84, 5.85, size=13, gap=0.14)

tf = textbox(sl, 6.79, 1.48, 5.84, 0.3)
para(tf, "QUATRO LIMITAÇÕES ASSUMIDAS", 11.5, bold=True, color=BLUE, first=True, space_after=0)
limit = [
    ("Dados.", "A série FEBRABAN é nacional. Não há dados municipais de juros, prazos ou "
     "inadimplência. A ESTBAN registra saldos, não operações novas — a direção da causalidade "
     "na margem de crédito permanece ambígua."),
    ("Identificação temporal.", "Quebras em 2014–16 e 2018–19 coincidem com rupturas "
     "institucionais (Lei das Estatais, Lei da Liberdade Econômica, Agenda BC#). Uma data única "
     "de tratamento não separa esses componentes."),
    ("Unidade espacial.", "A função financeira transborda o limite municipal: Almenara é polo de "
     "seis municípios sem agência; Betim integra o mercado metropolitano de BH."),
    ("Interpretação qualitativa.", "O contexto institucional dos casos se apoia em fontes "
     "secundárias e foi marcado como hipotético ao longo do texto."),
]
bullets(sl, limit, 6.79, 1.84, 5.84, size=13, gap=0.14, marker=BLUE)

rect(sl, ML, 5.30, CW, 0.012, fill=RULE)
tf = textbox(sl, ML, 5.48, CW, 0.3)
para(tf, "AGENDA DE PESQUISA", 11.5, bold=True, color=ORANGE, first=True, space_after=6)
tf = textbox(sl, ML, 5.80, CW, 0.8)
para(tf, "Incorporar dados desagregados do SCR/BCB para testar diretamente a mudança de composição "
         "da carteira  ·  mudar a escala para microrregiões ou regiões funcionais  ·  investigar os "
         "mecanismos institucionais com métodos qualitativos  ·  separar o choque digital das rupturas "
         "institucionais contemporâneas com desenhos que explorem variação exógena subnacional na "
         "adoção de tecnologia.",
     12.5, color=INK, first=True, space_after=0, line=1.18)
notes(sl, "Quatro contribuições e quatro limitações que eu assumo abertamente. A mais séria é a "
          "primeira das limitações: a ESTBAN registra saldos contábeis, não operações novas, "
          "então não consigo separar contração de oferta de mudança de demanda. A segunda é a "
          "identificação temporal — o choque de 2020 operou sobre um território que já estava em "
          "movimento. (~60s)")

# --- 37. Conclusão
sl = s_content("Considerações finais", kicker="")
rect(sl, ML, 1.50, CW, 1.72, fill=BLUE_L)
rect(sl, ML, 1.50, 0.06, 1.72, fill=ORANGE)
tf = textbox(sl, ML + 0.42, 1.72, CW - 0.90, 1.32)
para(tf, "Moeda e crédito não são variáveis exógenas ao desenvolvimento regional. "
         "São forças que estruturam a geografia das oportunidades.",
     21, bold=True, color=BLUE, first=True, space_after=10, line=1.14)
para(tf, "A digitalização financeira não suspendeu essa dinâmica: reorganizou-a.",
     17, color=INK, space_after=0, line=1.16)

achados = [
    ("A rede física recuou seletivamente", "e a convergência intermunicipal em cobertura, que vinha "
     "ocorrendo até 2019, congelou a partir de 2020."),
    ("A qualidade do crédito se descolou do volume", "— a razão IRF/IRE caiu em quase toda a distribuição, "
     "com intensidade máxima onde o crédito longo já era escasso."),
    ("O efeito é um deslocamento, não um desaparecimento", "— efeito direto e spillover têm sinais opostos: "
     "o que sai da periferia reaparece nos polos adjacentes."),
    ("O canal dominante é tecnológico, não mecânico", "— a transformação qualitativa da carteira não depende "
     "de a agência fechar; ela ocorre também com a agência aberta."),
]
bullets(sl, achados, ML, 3.48, CW, size=13.5, gap=0.16)

rect(sl, ML, 5.88, CW, 0.66, fill=ORANGE_L)
rect(sl, ML, 5.88, 0.055, 0.66, fill=ORANGE)
tf = textbox(sl, ML + 0.30, 5.98, CW - 0.60, 0.46, anchor=MSO_ANCHOR.MIDDLE)
para(tf, "Cabe à pesquisa e à política pública entender como — para que a promessa de inclusão "
         "não vire, na prática, mais um vetor de desigualdade.",
     14.5, bold=True, color=BLUE, first=True, space_after=0, line=1.14)
notes(sl, "Fecho onde comecei. A moeda não é exógena ao desenvolvimento regional. A "
          "digitalização não suspendeu a hierarquia financeira — reorganizou-a. Quatro achados "
          "sustentam isso. E a lição de política é a última linha: sem desenho regulatório "
          "atento ao território, a promessa de inclusão vira mais um vetor de desigualdade. (~60s)")

# --- 38. Encerramento
sl = s_blank()
rect(sl, 0, 0, 0.26, SH, fill=ORANGE)
rect(sl, 0.26, 0, 0.09, SH, fill=BLUE)
sl.shapes.add_picture(LOGO, In(1.15), In(1.15), In(2.75), In(0.69))
tf = textbox(sl, 1.15, 2.42, 10.4, 1.0)
para(tf, "Obrigado.", 42, bold=True, color=BLUE, first=True, space_after=0, line=1.0)
rect(sl, 1.15, 3.42, 1.35, 0.05, fill=ORANGE)
tf = textbox(sl, 1.15, 3.72, 10.4, 0.5)
para(tf, "Coloco-me à disposição da banca para as arguições.", 18, color=INK, first=True,
     space_after=0)

rect(sl, 1.15, 4.52, 5.05, 1.55, fill=BLUE_L)
rect(sl, 1.15, 4.52, 0.055, 1.55, fill=BLUE)
tf = textbox(sl, 1.42, 4.72, 4.6, 1.25)
para(tf, "Flávio Hugo Pangracio Silva", 15, bold=True, color=BLUE, first=True, space_after=5)
para(tf, "flaviohugo.14@gmail.com", 12.5, color=INK, space_after=3)
para(tf, "ORCID 0000-0003-4045-101X", 12.5, color=INK, space_after=3)
para(tf, "github.com/flaviohugo14/masters-thesis", 12.5, color=INK, space_after=0)

rect(sl, 6.52, 4.52, 5.05, 1.55, fill=RGBColor(0xF6, 0xF7, 0xFA))
rect(sl, 6.52, 4.52, 0.055, 1.55, fill=ORANGE)
tf = textbox(sl, 6.79, 4.72, 4.6, 1.25)
para(tf, "REPRODUTIBILIDADE", 11, bold=True, color=ORANGE, first=True, space_after=6)
para(tf, "Todo o pipeline — extração, construção dos indicadores, estimação e renderização — "
         "roda em R (renv + Quarto), com dependências pinadas e código público.",
     12.5, color=INK, space_after=0, line=1.16)

tf = textbox(sl, 1.15, 6.45, 10.4, 0.3)
para(tf, "CEDEPLAR/UFMG  ·  Belo Horizonte  ·  2026", 11.5, bold=True, color=GRAY,
     first=True, space_after=0)
notes(sl, "Obrigado. À disposição para as arguições. (~10s)\n\nTEMPO ACUMULADO ESTIMADO: ~25 min.")

# =============================================================================
# ANEXOS
# =============================================================================
SECTION = "Anexos"
s_divider("A", "Anexos",
          ["Material de apoio para as arguições",
           "Séries complementares, indicadores por porte e trajetórias dos estudos de caso"])

anexos = [
    ("fig-penetracao-1.png",
     "Penetração dos canais digitais (2009–2024)",
     "Taxas de habilitação de Internet Banking e Mobile Banking sobre o total de contas ativas. "
     "A virada IB→MB ocorre em 2015–2016 — a quebra dominante da dimensão de composição.",
     "Anexo · Capítulo 2"),
    ("fig-participacao-1.png",
     "Participação do Mobile Banking no total de transações",
     "Série de composição usada nos testes de quebra estrutural. Quebra dominante em 2016, quando "
     "o Mobile Banking ultrapassa o Internet Banking como canal predominante.",
     "Anexo · Capítulo 2"),
    ("fig-pctfin-1.png",
     "Proporção de transações com movimentação financeira efetiva",
     "Distingue consultas de transações que movimentam recursos — dimensão de composição do uso "
     "dos canais digitais.",
     "Anexo · Capítulo 2"),
    ("fig-agencias-total-1.png",
     "Estoque total de agências bancárias no Brasil (2009–2022)",
     "A retração da rede física em nível agregado. A série é truncada em 2022 por subnotificação "
     "do estoque de agências em 2023 na base utilizada.",
     "Anexo · Capítulo 2"),
    ("fig-agencias-porte-1.png",
     "Estoque de agências por faixa de PIB municipal",
     "Decomposição da retração por porte econômico. Base da análise de heterogeneidade "
     "apresentada no Capítulo 3.",
     "Anexo · Capítulo 2"),
    ("fig-credito-pib-1.png",
     "Razão crédito/PIB por faixa de porte municipal",
     "Profundidade financeira local ao longo do período. Permite separar o efeito de nível "
     "do efeito de dinâmica pós-2020.",
     "Anexo · Capítulo 2"),
    ("fig-plp-plb-1.png",
     "Preferência pela liquidez do público (PLP) e dos bancos (PLB)",
     "Medianas por porte econômico. O padrão teórico esperado — PLP e PLB mais elevados em "
     "municípios menores — se confirma empiricamente.",
     "Anexo · Capítulo 2"),
    ("fig-concentracao-1.png",
     "Concentração de operações (ICO) e concentração bancária (ICB)",
     "Municípios periféricos combinam alta concentração bancária e baixa diversificação de "
     "produtos: o padrão de exclusão financeira qualitativa.",
     "Anexo · Capítulo 2"),
    ("fig-exposicao-porte-1.png",
     "Distribuição do score de exposição Eᵢ por faixa de PIB",
     "Gradiente monotônico: mediana de +2,1 d.p. nos municípios até R$ 100 milhões e −2,6 nos "
     "acima de R$ 2 bilhões. A sobreposição entre faixas justifica a medida contínua.",
     "Anexo · Capítulo 3"),
    ("fig-caso-bh-1.png",
     "Belo Horizonte (MG): trajetória 2009–2023",
     "Agências: 415 (2009) → 466 (2014) → 314 (2022), −33% no recorte 2014–2022. IRC de 1,79 para "
     "2,62 (+47%). IRF/IRE: 0,63 → 1,28 (2015) → 0,52 (2022).",
     "Anexo · Estudos de caso"),
    ("fig-caso-jf-1.png",
     "Juiz de Fora (MG): trajetória 2009–2023",
     "Cidade média de centralidade regional, 540 mil habitantes e 46 agências em 2022. "
     "Perda de 21% da rede e IRC estável em 0,76 — a trajetória mais preservada dos quatro casos.",
     "Anexo · Estudos de caso"),
    ("fig-caso-betim-1.png",
     "Betim (MG): trajetória 2009–2023",
     "Polo industrial da RMBH com PIB acima de R$ 20 bilhões e apenas 16 agências. Perda de 36% da "
     "rede e queda de 70% no IRC: periferia financeira dentro da própria região metropolitana.",
     "Anexo · Estudos de caso"),
    ("fig-caso-almenara-1.png",
     "Almenara (MG): trajetória 2009–2023",
     "Polo do Baixo Jequitinhonha, 40 mil habitantes e 5 agências mantidas em todo o período por "
     "bancos públicos. Ainda assim, a razão IRF/IRE caiu 43% entre 2014 e 2022.",
     "Anexo · Estudos de caso"),
    ("fig-credito-composicao-1.png",
     "Composição do crédito: empréstimos e financiamentos",
     "Decomposição das contas 161 e 162 da ESTBAN que originam a razão IRF/IRE, proxy central de "
     "qualidade do crédito nesta dissertação.",
     "Anexo · Capítulo 2"),
    ("fig-movfin-1.png",
     "Transações com movimentação financeira por canal",
     "Série auxiliar da dimensão de utilização usada na datação do choque digital.",
     "Anexo · Capítulo 2"),
]
for fname, tit, desc, kick in anexos:
    path = F(fname)
    if not os.path.exists(path):
        continue
    sl = s_content(tit, kicker=kick)
    iw, ih = Image.open(path).size
    if iw / ih < 1.25:   # figura alta → layout lateral
        pic(sl, path, ML, 1.44, 7.10, 5.05)
        tf = textbox(sl, 7.90, 1.60, 4.55, 2.4)
        para(tf, desc, 14, color=INK, first=True, space_after=0, line=1.2)
    else:
        pic(sl, path, ML, 1.44, CW, 4.35)
        tf = textbox(sl, ML, 5.94, CW, 0.6)
        para(tf, desc, 13.5, color=INK, first=True, space_after=0, line=1.2)

# --- anexo: quadro de robustez detalhado
sl = s_content("Anexo — desenho de identificação em uma página", kicker="Anexo · Capítulo 3")
rows = [
    ["Etapa", "Método", "Referência", "Saída"],
    ["1. Datação do choque", "Bai-Perron, Quandt-Andrews e Chow sobre 7 séries FEBRABAN",
     "Bai & Perron (2003); Andrews (1993)", "t* = 2020 (2016 secundário)"],
    ["2. Exposição ex-ante", "ACP sobre 5 variáveis pré-2014, PC1 como score contínuo",
     "Borusyak et al. (2024)", "Eᵢ — 44,6% da variância"],
    ["3. Dinâmica do efeito", "Event study com interações ano a ano, referência k = −1",
     "fixest::feols", "Convergência interrompida"],
    ["4. Efeito médio", "DiD com tratamento contínuo, EF de município e ano",
     "—", "β por desfecho"],
    ["5. Heterogeneidade", "Interação tripla Post × faixa de porte, P4 como referência",
     "—", "δp por faixa"],
    ["6. Spillovers", "SLX-DiD com W de contiguidade rainha row-normalizada",
     "Halleck Vega & Elhorst (2015)", "β direto e θ spillover"],
    ["7. Mecanismo", "Mediação causal em painel, Sobel + bootstrap de blocos (B = 500)",
     "Imai, Keele & Tingley (2010)", "ACME, ADE, τ"],
    ["8. Distribuição", "Quantílica em painel em duas etapas, τ de 0,10 a 0,90",
     "Canay (2011)", "βτ por quantil"],
    ["9. Robustez", "Controles reais, placebo 2014, DiD sintético e W alternativas",
     "Arkhangelsky et al. (2021)", "Validação e ressalvas"],
]
table(sl, ML, 1.50, CW, rows, [0.19, 0.375, 0.235, 0.20], body_size=11, row_h=0.46,
      head_h=0.36, head_size=11.5,
      align=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
source(sl, "Painel município-ano 2009–2023 (5.570 municípios). Modelos estimados em R com fixest, quantreg, mediation, synthdid, sf/spdep e geobr.",
       t=6.30)

prs.save(OUT)
print("OK ->", OUT)
print("slides:", len(prs.slides._sldIdLst))
