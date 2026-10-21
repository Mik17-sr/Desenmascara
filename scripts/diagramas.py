"""Draw the README's animated flow diagrams into docs/img/.

    python scripts/diagramas.py

SVG with CSS animations, because GitHub runs no JavaScript inside images. Without animation
(or with "reduce motion") each diagram shows its finished state. The example scores are a
real API answer; change them here if the judge's points change.
"""
import math
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'Cascadia Mono', Consolas, Menlo, monospace"

THEME = """
svg{--card:#f4f6f5;--box:#ffffff;--ink:#131a18;--muted:#5f6b68;--line:#d5dedb;--edge:#97a9a5;
--brand:#0e9f8e;--brand-ink:#0b7f72;--brand-soft:#e3f5f2;--bubble:#eef3f1;
--low:#1e8449;--mid:#b7860b;--high:#c0392b;--low-soft:#d6ede0;--mid-soft:#f6e9c2;--high-soft:#f7d9d5}
@media (prefers-color-scheme:dark){svg{--card:#0b100f;--box:#131b1a;--ink:#e9efee;--muted:#94a3a0;--line:#26332f;
--edge:#55706a;--brand:#2bb5a3;--brand-ink:#3cc9b6;--brand-soft:#12312c;--bubble:#1a2422;
--low:#3fb071;--mid:#e0b33a;--high:#e5544a;--low-soft:#143222;--mid-soft:#322a14;--high-soft:#351a19}}
text{font-family:FONT;fill:var(--ink)}
.h1{font-size:22px;font-weight:700}
.sub{font-size:14px;fill:var(--muted)}
.t{font-size:15px;font-weight:600}
.tb{font-size:13.5px;font-weight:600}
.s{font-size:12.5px;fill:var(--muted)}
.m{font-size:12.5px}
.xs{font-size:11px;fill:var(--muted)}
.tag{font-size:10.5px;fill:var(--muted);letter-spacing:.03em}
.mono{font-family:MONO;font-weight:700}
.b{font-weight:700}
.card{fill:var(--card)}
.box{fill:var(--box);stroke:var(--line);stroke-width:1.2}
.act{fill:var(--brand-soft);stroke:var(--brand);stroke-width:2}
.done{fill:none;stroke:var(--brand);stroke-width:1.5;stroke-opacity:.55}
.frame{fill:none;stroke:var(--line);stroke-width:1.2;stroke-dasharray:4 4}
.edge{fill:none;stroke:var(--edge);stroke-width:1.6}
.reply{stroke-dasharray:6 4}
.call{stroke-dasharray:2 4;stroke-width:2}
.loop{fill:none;stroke:var(--brand);stroke-width:1.8;stroke-dasharray:6 5}
.life{stroke:var(--line);stroke-width:1.4;stroke-dasharray:3 5}
.badge{fill:var(--brand-soft)}
.badge-n{font-size:12.5px;font-weight:700;fill:var(--brand-ink)}
.chk{fill:var(--brand)}
.chk-p{fill:none;stroke:var(--box);stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.pkt{fill:var(--brand)}
.halo{fill:var(--brand);opacity:.22}
.bubble{fill:var(--bubble)}
.rail{fill:var(--line)}
.rail-f{fill:var(--brand)}
.low{fill:var(--low)}.mid{fill:var(--mid)}.high{fill:var(--high)}
.low-s{fill:var(--low-soft)}.mid-s{fill:var(--mid-soft)}.high-s{fill:var(--high-soft)}
.bar{fill:var(--edge);opacity:.55}
.pill{fill:var(--brand)}
.pill-t{font-size:11.5px;font-weight:700;fill:var(--box)}
.chip{fill:var(--box);stroke:var(--line);stroke-width:1.2}
.ring{fill:none;stroke:var(--high);stroke-width:2}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
""".replace("FONT", FONT).replace("MONO", MONO)

TONE = {"low": "var(--low)", "mid": "var(--mid)", "high": "var(--high)", "brand": "var(--brand)", None: "var(--edge)"}


class Anim:
    """One timeline: every element loops with the same period, so they stay in step."""

    def __init__(self, period: float, hold: float):
        self.T, self.hold, self.rules, self.n = period, hold, [], 0

    def kf(self, frames: list[tuple[float, str]]) -> str:
        self.n += 1
        name = f"k{self.n}"
        body = "".join(f"{min(100.0, t / self.T * 100):.3f}%{{{props}}}" for t, props in frames)
        self.rules.append(f"@keyframes {name}{{{body}}}")
        return f"animation:{name} {self.T}s linear infinite"

    def pulses(self, intervals: list[tuple[float, float]], fade=0.15, out=0.3) -> str:
        frames = [(0, 0)]
        for on, off in intervals:
            frames += [(on, 0), (on + fade, 1), (off, 1), (off + out, 0)]
        frames.append((self.T, 0))
        return "opacity:0;" + self.kf([(t, f"opacity:{o}") for t, o in frames])

    def reveal(self, t: float, fade=0.25, frm="", to="") -> str:
        hidden, shown = f"opacity:0;{frm}", f"opacity:1;{to}"
        return self.kf([(0, hidden), (t, hidden), (t + fade, shown), (self.hold, shown),
                        (self.hold + 0.4, f"opacity:0;{to}"), (self.T, hidden)])

    def grow(self, steps: list[tuple[float, float]], axis="X") -> str:
        """Scale from 0 through (time, scale) steps, keep it, fade it out at the end of the loop."""
        frames = [(0, f"transform:scale{axis}(0);opacity:1")]
        frames += [(t, f"transform:scale{axis}({s:.4f});opacity:1") for t, s in steps]
        last = steps[-1][1]
        frames += [(self.hold, f"transform:scale{axis}({last:.4f});opacity:1"),
                   (self.hold + 0.4, f"transform:scale{axis}({last:.4f});opacity:0"),
                   (self.T, f"transform:scale{axis}(0);opacity:0")]
        return self.kf(frames)

    def packet(self, legs: list[tuple[list[tuple[float, float]], float, float]]) -> str:
        """Visible only while travelling a leg; moves out of sight between legs."""
        def at(t, p, o):
            return (t, f"transform:translate({p[0]:.1f}px,{p[1]:.1f}px);opacity:{o}")

        frames = [at(0, legs[0][0][0], 0)]
        for points, t0, t1 in legs:
            frames.append(at(t0 - 0.05, points[0], 0))
            segs = [math.dist(p, q) for p, q in zip(points, points[1:])]
            total, acc = sum(segs), 0.0
            frames.append(at(t0, points[0], 1))
            for seg, q in zip(segs, points[1:]):
                acc += seg
                frames.append(at(t0 + (t1 - t0) * acc / total, q, 1))
            frames.append(at(t1 + 0.05, points[-1], 0))
        frames.append(at(self.T, legs[-1][0][-1], 0))
        return "opacity:0;" + self.kf(frames)

    def style(self) -> str:
        return THEME + "\n".join(self.rules)


def text(x, y, s, cls="s", anchor=None, style=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    st = f' style="{style}"' if style else ""
    return f'<text x="{x}" y="{y}" class="{cls}"{a}{st}{extra}>{escape(s)}</text>'


def spans(x, y, parts, anchor=None, cls="m"):
    """One line with mixed styles: parts are (text, class, tone or None)."""
    a = f' text-anchor="{anchor}"' if anchor else ""
    inner = ""
    for s, c, tone in parts:
        color = f' style="fill:{TONE[tone]}"' if tone else ""
        inner += f'<tspan class="{c}"{color}>{escape(s)}</tspan>'
    return f'<text x="{x}" y="{y}" class="{cls}"{a}>{inner}</text>'


def markers():
    out = []
    for name, color in TONE.items():
        mid = name or "edge"
        out.append(f'<marker id="ar-{mid}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
                   f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:{color}"/></marker>')
    return "<defs>" + "".join(out) + "</defs>"


def check(x, y):
    return (f'<circle cx="{x}" cy="{y}" r="8" class="chk"/>'
            f'<path d="M{x - 3.6} {y + 0.2} L{x - 1} {y + 2.8} L{x + 3.8} {y - 2.6}" class="chk-p"/>')


def svg(w, h, a, label, body):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-labelledby="titulo"><title id="titulo">{escape(label)}</title>'
            f'<style>{a.style()}</style>{markers()}'
            f'<rect width="{w}" height="{h}" rx="18" class="card"/>{body}</svg>\n')


# ---------------------------------------------------------------- 1 · a message through the six reviews

def main_flow() -> str:
    a = Anim(16.0, 15.4)
    W, H = 960, 676
    o = []
    o.append(text(40, 46, "Así se revisa un mensaje", "h1"))
    o.append(text(40, 70, "De lo que te llegó a un semáforo con sus razones, en menos de 8 segundos.", "sub"))

    # Example chip
    o.append('<rect x="40" y="88" width="880" height="34" rx="17" class="chip"/>')
    o.append('<rect x="46" y="94" width="76" height="22" rx="11" class="pill"/>')
    o.append(text(84, 109.5, "EJEMPLO", "pill-t", "middle"))
    o.append(text(134, 110, "«BancoAndino: tu cuenta será bloqueada hoy. Valida tus datos en bancoandino-seguro.co antes de las 6 pm»", "m"))

    # Row A
    ay, ah = 140, 92
    row_a = [
        (56, "1", "Lo que te llegó", "Mensaje, captura, nota de voz", "o el número que te llamó", [(0.0, 1.0), (14.0, 14.8)], 1.0),
        (352, "2", "Bot de Telegram", "Reconoce qué le enviaste", "y pide consentimiento (Ley 1581)", [(1.5, 2.5)], 2.5),
        (648, "3", "API FastAPI", "Secreto por rol y límite por IP", "Anonimiza antes de guardar", [(3.0, 4.0)], 4.0),
    ]
    for x, n, title, l1, l2, active, done in row_a:
        w = 256
        o.append(f'<rect x="{x}" y="{ay}" width="{w}" height="{ah}" rx="12" class="box"/>')
        o.append(f'<rect x="{x}" y="{ay}" width="{w}" height="{ah}" rx="12" class="act" style="{a.pulses(active)}"/>')
        o.append(f'<g style="{a.reveal(done, 0.3)}"><rect x="{x}" y="{ay}" width="{w}" height="{ah}" rx="12" class="done"/>'
                 f'{check(x + w - 20, ay + 20)}</g>')
        o.append(f'<circle cx="{x + 26}" cy="{ay + 28}" r="13" class="badge"/>')
        o.append(text(x + 26, ay + 32.5, n, "badge-n", "middle"))
        o.append(text(x + 48, ay + 33, title, "t"))
        o.append(text(x + 20, ay + 60, l1))
        o.append(text(x + 20, ay + 78, l2))
    o.append('<path d="M312 186 H348" class="edge" marker-end="url(#ar-edge)"/>')
    o.append('<path d="M608 186 H644" class="edge" marker-end="url(#ar-edge)"/>')
    o.append('<path d="M776 232 V242 Q776 250 768 250 H130 Q122 250 122 258 V300" class="edge" marker-end="url(#ar-edge)"/>')

    # The brain
    o.append('<rect x="40" y="266" width="880" height="162" rx="14" class="frame"/>')
    o.append(spans(146, 292, [("El Cerebro", "tb", None), ("  ·  seis revisiones en orden, cada una suma o resta puntos", "s", None)], cls="m"))
    bx0, by, bw, bh, gap = 56, 304, 133, 104, 10
    reviews = [
        ("Traductor", "Lee capturas y", "notas de voz", "OCR · WHISPER", (5.0, 5.6)),
        ("Pistas", "Enlaces, números", "y llaves Bre-B", "REGLAS", (5.6, 6.2)),
        ("Enlaces", "¿Página oficial", "o imitación?", "RDAP · HOMOGLIFOS", (6.2, 6.8)),
        ("Psicólogo", "IA local: qué pide", "y si presiona", "LLAMA3.2 · OLLAMA", (6.8, 7.8)),
        ("Archivista", "¿Campaña ya", "reportada hoy?", "MINHASH", (7.8, 8.4)),
        ("Juez", "Suma los puntos", "y da cada razón", "0 – 100", (8.4, 9.2)),
    ]
    for i, (name, l1, l2, tag, (on, off)) in enumerate(reviews):
        x = bx0 + i * (bw + gap)
        o.append(f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="10" class="box"/>')
        o.append(f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="10" class="act" style="{a.pulses([(on, off)])}"/>')
        o.append(f'<g style="{a.reveal(off, 0.3)}"><rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="10" class="done"/>'
                 f'{check(x + bw - 16, by + 17)}</g>')
        o.append(f'<circle cx="{x + 20}" cy="{by + 24}" r="11" class="badge"/>')
        o.append(text(x + 20, by + 28.5, str(i + 1), "badge-n", "middle"))
        o.append(text(x + 37, by + 29, name, "tb"))
        o.append(text(x + 14, by + 56, l1))
        o.append(text(x + 14, by + 73, l2))
        o.append(text(x + 14, by + 94, tag, "tag"))
    o.append('<rect x="56" y="415" width="848" height="4" rx="2" class="rail"/>')
    rail = [(5.6, 1 / 6), (6.2, 2 / 6), (6.8, 3 / 6), (7.8, 4 / 6), (8.4, 5 / 6), (9.2, 1)]
    o.append(f'<rect x="56" y="415" width="848" height="4" rx="2" class="rail-f" '
             f'style="transform-box:fill-box;transform-origin:left center;{a.grow([(5.0, 0)] + rail)}"/>')
    o.append('<path d="M837 428 V438 Q837 446 829 446 H534 Q526 446 526 454 V460" class="edge" marker-end="url(#ar-edge)"/>')

    # Row C
    cy, ch = 464, 188
    mid = cy + 94
    # C1 · reply in Telegram
    c1x, c1w = 56, 296
    o.append(f'<rect x="{c1x}" y="{cy}" width="{c1w}" height="{ch}" rx="12" class="box"/>')
    o.append(f'<rect x="{c1x}" y="{cy}" width="{c1w}" height="{ch}" rx="12" class="act" style="{a.pulses([(12.4, 13.0)])}"/>')
    o.append(f'<rect x="{c1x}" y="{cy}" width="{c1w}" height="{ch}" rx="12" class="done" style="{a.reveal(13.0, 0.3)}"/>')
    o.append(text(c1x + 20, cy + 30, "Respuesta en Telegram", "t"))
    bubble = [
        f'<rect x="{c1x + 16}" y="{cy + 44}" width="264" height="132" rx="12" class="bubble"/>',
        f'<circle cx="{c1x + 35}" cy="{cy + 62}" r="5.5" class="high"/>',
        spans(c1x + 48, cy + 66.5, [("ALTO RIESGO · 80/100", "b", "high")]),
        text(c1x + 30, cy + 84, "Posible suplantación"),
        text(c1x + 30, cy + 104, "Por qué:", "m b"),
        text(c1x + 30, cy + 120, "• El enlace no es la página oficial", "m"),
        spans(c1x + 39, cy + 135, [("de BancoAndino.", "m", None), (" (y 2 razones más)", "s", None)]),
        spans(c1x + 30, cy + 154, [("Qué hacer: ", "b", None), ("no abras, no respondas,", "m", None)]),
        text(c1x + 30, cy + 169, "no pagues.", "m"),
    ]
    o.append(f'<g style="{a.reveal(12.4, 0.3, "transform:translateY(6px)", "transform:translateY(0)")}">{"".join(bubble)}</g>')

    # C2 · judge
    c2x, c2w = 376, 300
    o.append(f'<rect x="{c2x}" y="{cy}" width="{c2w}" height="{ch}" rx="12" class="box"/>')
    o.append(f'<rect x="{c2x}" y="{cy}" width="{c2w}" height="{ch}" rx="12" class="act" style="{a.pulses([(10.0, 12.0)])}"/>')
    o.append(f'<rect x="{c2x}" y="{cy}" width="{c2w}" height="{ch}" rx="12" class="done" style="{a.reveal(12.0, 0.3)}"/>')
    o.append(text(c2x + 20, cy + 30, "Semáforo y Rayos X", "t"))
    o.append(f'<g style="{a.reveal(10.85, 0.2)}">' + spans(c2x + c2w - 18, cy + 30, [("80", "t", "high"), ("/100", "s", None)], anchor="end") + "</g>")
    bx, bw_ = c2x + 18, 264
    zones = [(0, 0.4, "low", "Bajo", "0–39"), (0.4, 0.7, "mid", "Sospechoso", "40–69"), (0.7, 1.0, "high", "Alto", "70–100")]
    for z0, z1, tone, name, rng in zones:
        zx, zw = bx + bw_ * z0, bw_ * (z1 - z0)
        o.append(f'<rect x="{zx:.1f}" y="{cy + 44}" width="{zw:.1f}" height="10" class="{tone}-s"/>')
        o.append(text(round(zx + zw / 2, 1), cy + 72, name, "xs b", "middle", style=f"fill:{TONE[tone]}"))
        o.append(text(round(zx + zw / 2, 1), cy + 85, rng, "xs", "middle"))
    fills = [(0, 0.4, "low", 10.0, 10.4), (0.4, 0.7, "mid", 10.4, 10.7), (0.7, 0.8, "high", 10.7, 10.85)]
    for z0, z1, tone, t0, t1 in fills:
        zx, zw = bx + bw_ * z0, bw_ * (z1 - z0)
        o.append(f'<rect x="{zx:.1f}" y="{cy + 44}" width="{zw:.1f}" height="10" class="{tone}" '
                 f'style="transform-box:fill-box;transform-origin:left center;{a.grow([(t0, 0), (t1, 1)])}"/>')
    mx = bx + bw_ * 0.8
    o.append(f'<path d="M{mx:.1f} {cy + 40} V{cy + 58}" style="stroke:var(--ink);stroke-width:2;{a.reveal(10.85, 0.15)}"/>')
    rayos = [("+30", "Enlace imita a BancoAndino", "ENLACES"), ("+20", "Igual a una campaña de hoy", "ARCHIVISTA"),
             ("+15", "Página sin registro", "ENLACES"), ("+10", "Urgencia o presión", "PISTAS"),
             ("+5", "Dice ser BancoAndino", "PISTAS")]
    for i, (pts, label, src) in enumerate(rayos):
        y = cy + 108 + i * 16
        row = (text(c2x + 18, y, pts, "m mono", style="fill:var(--high)") + text(c2x + 54, y, label, "m")
               + text(c2x + c2w - 18, y, src, "tag", "end"))
        o.append(f'<g style="{a.reveal(10.95 + i * 0.2, 0.2, "transform:translateX(-6px)", "transform:translateX(0)")}">{row}</g>')

    # C3 · dashboard radar
    c3x, c3w = 700, 204
    o.append(f'<rect x="{c3x}" y="{cy}" width="{c3w}" height="{ch}" rx="12" class="box"/>')
    o.append(f'<rect x="{c3x}" y="{cy}" width="{c3w}" height="{ch}" rx="12" class="act" style="{a.pulses([(12.4, 13.0)])}"/>')
    o.append(f'<rect x="{c3x}" y="{cy}" width="{c3w}" height="{ch}" rx="12" class="done" style="{a.reveal(13.0, 0.3)}"/>')
    o.append(text(c3x + 20, cy + 30, "Radar en vivo", "t"))
    o.append(text(c3x + 20, cy + 52, "El Dashboard recibe un aviso"))
    o.append(text(c3x + 20, cy + 68, "anónimo: solo el nivel de"))
    o.append(text(c3x + 20, cy + 84, "riesgo, sin texto ni números."))
    base = cy + 164
    for i, hgt in enumerate([22, 34, 18, 40, 28, 46]):
        o.append(f'<rect x="{c3x + 20 + i * 24}" y="{base - hgt}" width="16" height="{hgt}" rx="3" class="bar"/>')
    nx, nh = c3x + 20 + 6 * 24, 38
    o.append(f'<rect x="{nx}" y="{base - nh}" width="16" height="{nh}" rx="3" class="high" '
             f'style="transform-box:fill-box;transform-origin:center bottom;{a.grow([(12.4, 0), (12.8, 1)], "Y")}"/>')
    o.append(f'<circle cx="{nx + 8}" cy="{base - nh - 8}" r="6" class="ring" style="transform-box:fill-box;transform-origin:center;'
             + a.kf([(0, "opacity:0;transform:scale(.4)"), (12.8, "opacity:0;transform:scale(.4)"),
                     (12.85, "opacity:1;transform:scale(.4)"), (13.6, "opacity:0;transform:scale(1.8)"),
                     (16, "opacity:0;transform:scale(.4)")]) + '"/>')
    o.append(text(c3x + 20, base + 16, "SUPABASE REALTIME", "tag"))

    o.append(f'<path d="M376 {mid} H356" class="edge" marker-end="url(#ar-edge)"/>')
    o.append(f'<path d="M676 {mid} H696" class="edge" marker-end="url(#ar-edge)"/>')
    # The answer goes back to the person
    o.append(f'<path d="M56 {mid} H38 Q30 {mid} 30 {mid - 8} V194 Q30 186 38 186 H52" class="loop" marker-end="url(#ar-brand)"/>')
    o.append(text(19, 372, "VUELVE POR EL BOT · MENOS DE 8 S", "tag", "middle",
                  style="fill:var(--brand-ink);font-weight:700", extra=' transform="rotate(-90 19 372)"'))

    # Packets
    main = a.packet([
        ([(312, 186), (352, 186)], 1.0, 1.5),
        ([(608, 186), (648, 186)], 2.5, 3.0),
        ([(776, 232), (776, 250), (122, 250), (122, 304)], 4.0, 5.0),
        ([(837, 428), (837, 446), (526, 446), (526, 464)], 9.2, 10.0),
        ([(376, mid), (352, mid)], 12.0, 12.4),
        ([(56, mid), (30, mid), (30, 186), (56, 186)], 12.8, 14.0),
    ])
    side = a.packet([([(676, mid), (700, mid)], 12.0, 12.4)])
    dot = '<circle r="12" class="halo"/><circle r="6" class="pkt"/>'
    o.append(f'<g style="{main}">{dot}</g><g style="{side}">{dot}</g>')

    label = ("Flujo de Desenmascara: lo que te llegó pasa por el bot de Telegram y la API, luego por las seis revisiones "
             "(Traductor, Pistas, Enlaces, Psicólogo, Archivista y Juez). El juez da un semáforo de 0 a 100 con cada razón; "
             "la respuesta vuelve por Telegram y el Radar del Dashboard recibe un aviso anónimo.")
    return svg(W, H, a, label, "".join(o))


# ---------------------------------------------------------------- 2 and 3 · confirm with the source

def sequence(title, subtitle, actors, steps, note, footnote, label) -> str:
    a = Anim(14.0, 12.6)
    W, H = 960, 520
    o = [text(40, 46, title, "h1"), text(40, 70, subtitle, "sub")]
    xs = {}
    for key, x, name, sub, w in actors:
        xs[key] = x
        o.append(f'<line x1="{x}" y1="146" x2="{x}" y2="466" class="life"/>')
        o.append(f'<rect x="{x - w / 2}" y="96" width="{w}" height="50" rx="10" class="box"/>')
        o.append(text(x, 118, name, "tb", "middle"))
        o.append(text(x, 136, sub, "xs", "middle"))
    dot = '<circle r="10" class="halo"/><circle r="5" class="pkt"/>'
    for i, (frm, to, kind, parts, tone, label_x) in enumerate(steps):
        t = 0.6 + i * 1.4
        y = 186 + i * 42
        x1, x2 = xs[frm], xs[to]
        d = 1 if x2 > x1 else -1
        cls = {"msg": "edge", "reply": "edge reply", "call": "edge call"}[kind]
        stroke = f"stroke:{TONE[tone]};" if tone else ""
        mk = f"ar-{tone or 'edge'}"
        o.append(f'<path d="M{x1 + 6 * d} {y} H{x2 - 8 * d}" class="{cls}" marker-end="url(#{mk})" style="{stroke}{a.reveal(t, 0.2)}"/>')
        o.append(f'<g style="{a.packet([([(x1, y), (x2, y)], t + 0.15, t + 0.75)])}">{dot}</g>')
        lx = label_x if label_x else (x1 + x2) / 2
        o.append(f'<g style="{a.reveal(t + 0.7, 0.25, "transform:translateY(3px)", "transform:translateY(0)")}">'
                 + spans(lx, y - 10, parts, anchor="middle") + "</g>")
    nx, nw, ntext, ntone = note
    nt = 0.6 + len(steps) * 1.4
    ny = 186 + len(steps) * 42 - 18
    o.append(f'<g style="{a.reveal(nt, 0.3, "transform:translateY(4px)", "transform:translateY(0)")}">'
             f'<rect x="{nx - nw / 2}" y="{ny}" width="{nw}" height="30" rx="8" class="{ntone}-s"/>'
             + text(nx, ny + 20, ntext, "m b", "middle", style=f"fill:{TONE[ntone]}") + "</g>")
    o.append(f'<circle cx="49" cy="{H - 29}" r="8" class="badge"/>' + text(49, H - 25, "i", "badge-n", "middle"))
    o.append(text(64, H - 25, footnote, "s"))
    return svg(W, H, a, label, "".join(o))


def llamada() -> str:
    return sequence(
        "Llamada Verificada: ¿de verdad es tu banco?",
        "El banco avisa antes de llamar. Tú preguntas en Telegram y compruebas el código con quien te llama.",
        [("banco", 170, "BancoAndino", "Panel de la entidad", 220), ("des", 480, "Desenmascara", "API y bot", 220),
         ("tu", 790, "Tú", "en Telegram", 220)],
        [
            ("banco", "des", "msg", [("Registra la llamada a tu número", "m", None)], None, None),
            ("des", "banco", "reply", [("Le da el código 4817 · dura 15 min", "m", None)], None, None),
            ("banco", "tu", "call", [("El asesor te llama", "m", None)], None, 325),
            ("tu", "des", "msg", [("«¿BancoAndino me está llamando?»", "m", None)], None, None),
            ("des", "tu", "msg", [("SÍ, ES REAL", "b", "low"), (" · pídele el código 4 8 1 7", "m", None)], "low", None),
            ("banco", "tu", "call", [("«Su código es 4817»", "m", None)], None, 325),
        ],
        (790, 270, "Coincide: es BancoAndino de verdad", "low"),
        "Si el banco no registró ninguna llamada a tu número: «NO ES TU BANCO». Cuelga y llama tú a la línea de tu tarjeta.",
        "Llamada Verificada: BancoAndino registra la llamada y recibe un código de 4 dígitos que vence en 15 minutos. "
        "Cuando el asesor te llama, preguntas al bot si es real; el bot te muestra el código y lo compruebas con quien te llama.",
    )


def circulo() -> str:
    return sequence(
        "Círculo de Confianza: ¿de verdad es tu familiar?",
        "Tu familiar entra al Círculo con una invitación. Si alguien dice ser él y pide plata, Desenmascara le pregunta.",
        [("est", 120, "Estafador", "número desconocido", 190), ("tu", 360, "Tú", "en Telegram", 190),
         ("des", 600, "Desenmascara", "bot", 190), ("fam", 840, "Tu familiar", "en tu Círculo", 190)],
        [
            ("est", "tu", "msg", [("«Mami, préstame plata, es urgente»", "m", None)], None, None),
            ("tu", "des", "msg", [("Reenvías el mensaje", "m", None)], None, None),
            ("des", "tu", "msg", [("SOSPECHOSO", "b", "mid"), (" · no transfieras aún", "m", None)], "mid", None),
            ("des", "fam", "msg", [("«¿Fuiste tú?» · Sí / No", "m", None)], None, None),
            ("fam", "des", "reply", [("«No fui yo»", "m", None)], None, None),
            ("des", "tu", "msg", [("ES UNA ESTAFA", "b", "high"), (" · no transfieras", "m", None)], "high", None),
        ],
        (720, 290, "Y avisa al resto de tu Círculo", "high"),
        "Si tu familiar no responde en 5 minutos: «NO PUDIMOS CONFIRMARLO». No transfieras y llámalo a su número de siempre.",
        "Círculo de Confianza: te llega un mensaje de alguien que dice ser tu familiar y pide plata. Lo reenvías, el bot "
        "lo marca sospechoso y le pregunta a tu familiar en su Telegram si fue él. Si responde que no, te avisa que es una "
        "estafa y alerta al resto de tu Círculo.",
    )


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "docs" / "img"
    out.mkdir(parents=True, exist_ok=True)
    for name, build in [("flujo-mensaje.svg", main_flow), ("flujo-llamada-verificada.svg", llamada),
                        ("flujo-circulo.svg", circulo)]:
        (out / name).write_text(build(), encoding="utf-8")
        print(out / name)
