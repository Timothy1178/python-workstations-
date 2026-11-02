"""Design catalog / skills showcase deck on the ASW 185 template.
Every text is placeholder copy; every icon and image is a real picture
(right-click > Change Picture); cards are groups (move / duplicate as one)."""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pptlib import Deck

HERE = Path(__file__).parent
TPL, BUILD = HERE / "tpl/unpacked", HERE / "build_showcase"
ICON = lambda n, c="red": str(HERE / "icons" / f"{n}-{c}.png")
PH = lambda kind="wide": str(HERE / "icons" / f"ph-{kind}.png")

RED, RED2, DARK, GREY, CARD, PINK, GOLD, LINE = "E31836", "B3122A", "1F1F1F", "5F6062", "F6F6F7", "FCEEF0", "C9A04B", "E3E3E6"
PURPLE, BLUE, YELLOW, MAGENTA = "A27EC6", "01C2ED", "F7BC00", "EF00A6"   # theme accents
TITLE = dict(x=0.54, y=0.42, w=10.2, h=0.9)
L, R, TOP, BOT = 0.54, 12.8, 1.5, 6.35
W = R - L

deck = Deck(TPL, BUILD)

def content(title, transition="fade", layout=7):
    s = deck.slide(layout, transition)
    s.title(title, **TITLE)
    return s

def card(s, x, y, w, h, fill=CARD, shadow=True, line=None, radius=8000, name="Card"):
    return s.shape(x, y, w, h, geom="roundRect", fill=fill, line=line, shadow=shadow, radius=radius, name=name)

def icon_circle(s, cx, cy, d, icon, fill=RED, color="white", pad=0.26, name=None):
    s.shape(cx - d / 2, cy - d / 2, d, d, geom="ellipse", fill=fill, name="Icon circle")
    s.image(ICON(icon, color), cx - d / 2 + d * pad, cy - d / 2 + d * pad, d * (1 - 2 * pad), d * (1 - 2 * pad), name=name or f"Icon {icon}")

def tag(s, x, y, text, fill=PINK, color=RED, w=None):
    w = w or (0.25 + 0.085 * len(text))
    s.shape(x, y, w, 0.32, geom="roundRect", fill=fill, radius=50000, name="Tag")
    s.text(x, y, w, 0.32, text, size=10, color=color, bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))

def skill_note(s, text):
    """Small grey note at the bottom explaining the technique shown."""
    s.text(L, 6.08, W, 0.3, [("Skill: ", {"bold": True, "color": RED}), (text, {})], size=10.5, color=GREY, italic=True, margin=(0, 0, 0, 0))

SECTIONS = [("A", "Openers & dividers", 4, 3), ("B", "Text & layout", 7, 5), ("C", "Numbers & data", 13, 5), ("D", "Process & structure", 19, 8), ("E", "Visual effects", 28, 6), ("F", "Slide transitions", 35, 23), ("G", "Rotate & transform", 58, 10)]

# ================= 1 COVER =================
s = deck.slide(1, "fade")
t = s.title("Presentation title\ngoes here", x=0.57, y=2.55, w=6.6, h=1.75, size=40)
sub = s.text(0.6, 4.35, 6.4, 0.6, "Subtitle or one-line summary — replace me", size=20, color=RED, bold=True, margin=(0, 0, 0, 0))
who = s.text(0.6, 4.95, 6.4, 0.5, "Team  ·  Presenter  ·  Date", size=14, color=GREY, margin=(0, 0, 0, 0))
badge = s.group(0.6, 1.5, 3.3, 0.75, lambda g: (
    g.shape(0.6, 1.5, 3.3, 0.75, geom="roundRect", fill="FFFFFF", radius=50000, shadow=True, name="Badge"),
    g.image(ICON("palette", "red"), 0.72, 1.6, 0.55, 0.55, name="Badge icon"),
    g.text(1.32, 1.5, 2.5, 0.75, "Design catalog &\nPowerPoint skills showcase", size=11, color=DARK, bold=True, valign="m", margin=(0, 0, 0, 0))), name="Badge")
s.animate([(badge, "spinin", 0, 700), (t, "float", 300, 600), (sub, "fade", 750), (who, "fade", 950)], trigger="after")

# ================= 2 HOW TO USE =================
s = content("How to use this template")
tips = [("font", "Replace the text", "Click any text and type. Sizes and colours are set per box; titles use the template's title style."),
        ("image", "Swap pictures and icons", "Right-click an icon or grey image frame › Change Picture. Icons are PNGs in brand colours; keep the size."),
        ("layer", "Cards are groups", "Each card is one group: move, duplicate (Ctrl+D) or delete it as a unit. Ungroup to edit inside."),
        ("play", "Animations are pre-set", "Open Animations › Animation Pane to see the builds. Spin effects repeat until the slide ends."),
        ("link", "Clickable catalog", "The catalog page links to each section; the small ↑ on dividers jumps back."),
        ("palette", "Colour palette", "Red E31836 · Dark 1F1F1F · Grey 5F6062 · Gold C9A04B · Pink FCEEF0 — plus theme accents purple, blue, yellow.")]
ids = []
for i, (ic, h, d) in enumerate(tips):
    col, row = i % 2, i // 2
    x, y = L + col * 6.2, 1.55 + row * 1.5
    def b(g, x=x, y=y, ic=ic, h=h, d=d):
        card(g, x, y, 6.05, 1.3)
        icon_circle(g, x + 0.65, y + 0.65, 0.78, ic)
        g.text(x + 1.25, y + 0.18, 4.6, 0.4, h, size=16, color=DARK, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 1.25, y + 0.58, 4.65, 0.7, d, size=11.5, color=GREY, margin=(0, 0, 0, 0))
    ids.append(s.group(x, y, 6.05, 1.3, b, name=f"Tip {i + 1}"))
s.stagger(ids, "float", 120)

# ================= 3 CATALOG =================
s = content("Catalog — click a section to jump")
ids = []
cw = (W - 6 * 0.2) / 7
for i, (letter, name, first, count) in enumerate(SECTIONS):
    x = L + i * (cw + 0.22)
    def b(g, x=x, letter=letter, name=name, first=first, count=count, i=i):
        card(g, x, 1.6, cw, 3.4, fill="FFFFFF", line=LINE, shadow=True)
        g.shape(x, 1.6, cw, 1.25, geom="round2SameRect", fill=[RED, PURPLE, BLUE, GOLD, DARK, MAGENTA, "8E0E22"][i], radius=8000, name="Card head", link=first)
        g.text(x, 1.6, cw, 1.25, letter, size=40, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
        g.text(x + 0.12, 3.0, cw - 0.24, 0.7, name, size=12.5, color=DARK, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 0.15, 3.7, cw - 0.3, 0.4, f"{count} slides", size=11.5, color=GREY, margin=(0, 0, 0, 0))
        g.text(x + 0.15, 4.4, cw - 0.3, 0.4, [("Open →", {"link": first})], size=12, color=RED, bold=True, margin=(0, 0, 0, 0))
    ids.append(s.group(x, 1.6, cw, 3.4, b, name=f"Section {letter}"))
s.stagger(ids, "float", 120)
tag(s, L, 5.3, "A · 3 openers", w=1.5); tag(s, L + 1.6, 5.3, "B · 5 text layouts", w=1.8); tag(s, L + 3.5, 5.3, "C · 5 data slides", w=1.7); tag(s, L + 5.3, 5.3, "D · 8 structure", w=1.6); tag(s, L + 7.0, 5.3, "E · 6 visual", w=1.4); tag(s, L + 8.5, 5.3, "F · 23 transitions", w=1.9); tag(s, L + 10.5, 5.3, "G · 10 rotate & transform", w=2.4)
skill_note(s, "internal hyperlinks (ppaction://hlinksldjump) on shapes and text runs · staggered Float In builds")

# ================= helpers for dividers =================
def divider_a(layout, letter, title, sub):
    s = deck.slide(layout, "push")
    num = s.text(1.31, 1.3, 3, 1.0, letter, size=60, color=GOLD, bold=True, margin=(0, 0, 0, 0))
    t = s.title(title, x=1.21, y=2.35, w=6.5, h=1.1, size=40)
    st = s.text(1.31, 3.45, 6.5, 1.0, sub, size=18, color=GREY, margin=(0, 0, 0, 0))
    back = s.shape(12.3, 6.0, 0.4, 0.4, geom="ellipse", fill=CARD, name="Back to catalog", link=3)
    s.text(12.3, 6.0, 0.4, 0.4, "↑", size=14, color=RED, bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
    s.animate([(num, "spinin", 0, 600), (t, "float", 200), (st, "fade", 450)], trigger="after")
    return s

# ================= A =================
divider_a(3, "A", "Openers & dividers", "Two divider styles and a hero statement")

# 5 divider style B — full-bleed gradient
s = deck.slide(7, "cover")
s.gradient_rect(0, 0, 13.333, 7.5, RED, "8E0E22", angle=35, name="Full-bleed background")
ring = s.shape(8.1, 1.15, 4.9, 4.9, geom="ellipse", fill=None, line="FFFFFF", line_w=28, name="Decor ring", transparency=0)
ring2 = s.shape(9.05, 2.1, 3.0, 3.0, geom="ellipse", fill=None, line="FFFFFF", line_w=6, dash="dash", name="Decor ring 2")
num = s.text(1.0, 1.6, 4, 1.6, "02", size=96, color="FFFFFF", bold=True, margin=(0, 0, 0, 0))
t = s.text(1.0, 3.15, 6.9, 1.5, "Section title on a full-bleed slide", size=36, color="FFFFFF", bold=True, margin=(0, 0, 0, 0), font="Ubuntu", line_spacing=95)
st = s.text(1.0, 4.75, 6.9, 0.9, "A darker divider for contrast — the gradient is a real PowerPoint fill, so recolour it from Shape Format › Fill", size=15, color="FFD6DC", margin=(0, 0, 0, 0))
s.animate([(ring, "wheel", 0, 1200), (ring2, "spinback", 0, 20000), (num, "spinin", 200, 700), (t, "float", 500), (st, "fade", 800)], trigger="after")
s.text(L, 6.9, 8, 0.3, "Skill: gradient fill · wheel reveal · continuous counter-rotation on the dashed ring", size=10.5, color="FFD6DC", italic=True, margin=(0, 0, 0, 0))

# 6 big statement
s = content("Hero statement", layout=7)
q = s.text(L, 1.9, 9.2, 2.4, [("One ", {}), ("bold sentence", {"color": RED}), (" that carries the whole slide — keep it under twelve words.", {})], size=40, color=DARK, bold=True, margin=(0, 0, 0, 0), line_spacing=100, font="Ubuntu")
sub = s.text(L, 4.5, 8.5, 0.6, "Supporting line in grey — a fact, a source or the “so what”.", size=16, color=GREY, margin=(0, 0, 0, 0))
burst = s.shape(9.7, 1.4, 3.1, 3.1, geom="star24", fill=GOLD, transparency=70, name="Spinning burst")
burst2 = s.shape(10.1, 1.8, 2.3, 2.3, geom="star12", fill=GOLD, transparency=40, name="Spinning burst 2")
s.shape(10.6, 2.3, 1.3, 1.3, geom="ellipse", fill=RED, name="Bulb disc")
s.image(ICON("lightbulb", "white"), 10.85, 2.55, 0.8, 0.8, name="Bulb icon")
s.animate([(burst, "spinloop", 0, 24000), (burst2, "spinback", 0, 16000), (q, "float", 0, 700), (sub, "fade", 500)], trigger="after")
skill_note(s, "highlighted run inside a headline · decorative starbursts with transparency spinning in opposite directions")

# ================= B =================
divider_a(4, "B", "Text & layout", "Columns, cards, feature rows and comparisons")

# 8 two-column text + image
s = content("Two columns: text beside an image")
pic = s.image(PH("wide"), 7.1, 1.55, 5.7, 3.55, name="Image placeholder — Change Picture")
cap = s.text(7.1, 5.15, 5.7, 0.35, "Caption for the image — source or description", size=10.5, color=GREY, italic=True, margin=(0, 0, 0, 0))
head = s.text(L, 1.6, 6.2, 0.9, "Section heading in two lines maximum", size=24, color=DARK, bold=True, margin=(0, 0, 0, 0))
body = s.text(L, 2.6, 6.2, 2.7, ["First point of body copy — one idea per bullet, two lines at most.", "Second point with a specific fact or number that the audience will remember.", "Third point: what you want them to do with the information."], size=15, color=DARK, bullets=True, space_after=10, margin=(0, 0, 0, 0))
cta = s.group(L, 5.3, 3.2, 0.55, lambda g: (g.shape(L, 5.3, 3.2, 0.55, geom="roundRect", fill=RED, radius=50000, name="Button"), g.text(L, 5.3, 3.2, 0.55, "Button-style call to action →", size=12.5, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))), name="Button")
s.animate([(head, "float", 0), (body, "float", 200), (pic, "fade", 300, 700), (cap, "fade", 700), (cta, "zoom", 900)], trigger="after")
skill_note(s, "grey image frame is a real picture — right-click › Change Picture keeps size and position · rounded button is a shape with text")

# 9 three cards
s = content("Three cards with icons")
cw = (W - 2 * 0.3) / 3
ids = []
for i, ic in enumerate(["rocket", "shield", "heart"]):
    x = L + i * (cw + 0.3)
    def b(g, x=x, ic=ic, i=i):
        card(g, x, 1.6, cw, 3.9)
        icon_circle(g, x + cw / 2, 2.45, 1.1, ic, fill=[RED, PURPLE, BLUE][i], pad=0.27)
        g.text(x + 0.3, 3.2, cw - 0.6, 0.5, f"Card heading {i + 1}", size=18, color=DARK, bold=True, align="ctr", margin=(0, 0, 0, 0))
        g.text(x + 0.35, 3.75, cw - 0.7, 1.3, "Two or three lines of supporting copy. Keep every card the same length so the row stays balanced.", size=12.5, color=GREY, align="ctr", margin=(0, 0, 0, 0))
        g.text(x + 0.3, 5.0, cw - 0.6, 0.35, "Learn more →", size=12, color=RED, bold=True, align="ctr", margin=(0, 0, 0, 0))
    ids.append(s.group(x, 1.6, cw, 3.9, b, name=f"Card {i + 1}"))
s.stagger(ids, "zoom", 200, dur=450)
skill_note(s, "theme accent colours (red / purple / blue) on identical cards · Zoom entrance staggered 0.2 s")

# 10 feature rows
s = content("Icon + text rows")
rows = [("check", "Feature or benefit title", "One sentence of explanation that fits on a single line of this width."),
        ("clock", "Second feature title", "Short, concrete and parallel to the lines above and below."),
        ("users", "Third feature title", "Use the same sentence shape in every row for rhythm."),
        ("globe", "Fourth feature title", "Four to five rows is the comfortable maximum at this size.")]
ids = []
for i, (ic, h, d) in enumerate(rows):
    y = 1.6 + i * 1.1
    def b(g, y=y, ic=ic, h=h, d=d, i=i):
        if i % 2 == 0:
            g.shape(L, y, W, 0.95, geom="roundRect", fill=CARD, radius=10000, name="Row band")
        icon_circle(g, L + 0.6, y + 0.475, 0.66, ic, fill=RED, pad=0.26)
        g.text(L + 1.2, y + 0.12, 4.0, 0.4, h, size=16, color=DARK, bold=True, margin=(0, 0, 0, 0))
        g.text(L + 1.2, y + 0.5, 10.8, 0.4, d, size=12.5, color=GREY, margin=(0, 0, 0, 0))
        g.image(ICON("arrow", "grey"), R - 0.6, y + 0.33, 0.3, 0.3, name="arrow")
    ids.append(s.group(L, y, W, 0.95, b, name=f"Row {i + 1}"))
s.stagger(ids, "flyleft", 150, dur=400)
skill_note(s, "zebra bands on alternate rows · Fly In from the left, staggered")

# 11 before / after
s = content("Before / after comparison")
for i, (lab, fill, ic, items) in enumerate([("BEFORE", GREY, "times", ["Manual step one", "Slow hand-over", "No visibility", "Errors found late"]), ("AFTER", RED, "check2", ["Automated step one", "Instant hand-over", "Live dashboard", "Errors caught early"])]):
    x = L + i * (W / 2 + 0.15)
    w = W / 2 - 0.15
    def b(g, x=x, w=w, lab=lab, fill=fill, ic=ic, items=items):
        card(g, x, 1.6, w, 4.3, fill="FFFFFF", line=LINE)
        g.shape(x, 1.6, w, 0.7, geom="round2SameRect", fill=fill, radius=8000, name="Panel head")
        g.text(x, 1.6, w, 0.7, lab, size=16, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
        for k, it in enumerate(items):
            yy = 2.6 + k * 0.78
            g.shape(x + 0.4, yy, 0.46, 0.46, geom="ellipse", fill=PINK if fill == RED else CARD, name="Dot")
            g.image(ICON(ic, "red" if fill == RED else "grey"), x + 0.51, yy + 0.11, 0.24, 0.24, name=ic)
            g.text(x + 1.05, yy, w - 1.3, 0.46, it, size=14.5, color=DARK, valign="m", margin=(0, 0, 0, 0))
    gid = s.group(x, 1.6, w, 4.3, b, name=lab)
    s.animate([(gid, "flyleft" if i == 0 else "flyright", 0, 500)], trigger="after" if i == 0 else "click")
arrow = s.group(6.3, 3.4, 0.75, 0.75, lambda g: (g.shape(6.3, 3.4, 0.75, 0.75, geom="ellipse", fill=GOLD, shadow=True, name="Arrow disc"), g.image(ICON("arrow", "white"), 6.5, 3.6, 0.35, 0.35, name="arrow")), name="Arrow")
s.animate([(arrow, "spinin", 0, 600)], trigger="after")
skill_note(s, "two panels fly in from opposite sides · gold connector disc spins in · grey vs red marks the change")

# 12 options A/B/C
s = content("Options side by side")
cw = (W - 2 * 0.25) / 3
crit = ["Cost", "Time to launch", "Risk", "Scales to all stores", "Needs IT change"]
marks = [["check2", "times", "check2", "times", "check2"], ["check2", "check2", "check2", "check2", "times"], ["times", "check2", "times", "check2", "check2"]]
ids = []
for i in range(3):
    x = L + i * (cw + 0.25)
    rec = i == 1
    def b(g, x=x, i=i, rec=rec):
        card(g, x, 1.6, cw, 4.35, fill=PINK if rec else "FFFFFF", line=None if rec else LINE, shadow=rec)
        g.text(x + 0.3, 1.75, cw - 0.6, 0.5, f"Option {'ABC'[i]}", size=20, color=RED if rec else DARK, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 0.3, 2.2, cw - 0.6, 0.4, "one-line description", size=11.5, color=GREY, margin=(0, 0, 0, 0))
        for k, c in enumerate(crit):
            yy = 2.75 + k * 0.58
            g.image(ICON(marks[i][k], "red" if marks[i][k] == "check2" else "grey"), x + 0.35, yy + 0.08, 0.3, 0.3, name=marks[i][k])
            g.text(x + 0.8, yy, cw - 1.1, 0.46, c, size=13, color=DARK, valign="m", margin=(0, 0, 0, 0))
        if rec:
            g.shape(x + cw - 1.75, 1.45, 1.55, 0.34, geom="roundRect", fill=RED, radius=50000, name="Recommended tag")
            g.text(x + cw - 1.75, 1.45, 1.55, 0.34, "RECOMMENDED", size=9.5, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
    ids.append(s.group(x, 1.45, cw, 4.5, b, name=f"Option {'ABC'[i]}"))
s.stagger(ids, "float", 200)
s.animate([(ids[1], "pulse", 0, 900)])
skill_note(s, "recommended option lifted with tint, shadow and tag · click once more and it pulses to draw the eye")

# ================= C =================
divider_a(5, "C", "Numbers & data", "KPI tiles, native charts, rings, a table and a funnel")

# 14 KPI tiles
s = content("KPI tiles")
kpis = [("1,234", "metric label", "+12% vs last month", "chart", RED), ("98.5%", "another metric", "target 97%", "check", PURPLE), ("4.8", "rating out of 5", "from 2,100 reviews", "star", GOLD), ("< 2 s", "response time", "p95, last 30 days", "clock", BLUE)]
ids = []
cw = (W - 3 * 0.25) / 4
for i, (n, l, d, ic, col) in enumerate(kpis):
    x = L + i * (cw + 0.25)
    def b(g, x=x, n=n, l=l, d=d, ic=ic, col=col):
        card(g, x, 1.6, cw, 2.75)
        icon_circle(g, x + cw - 0.6, 2.05, 0.6, ic, fill=col, pad=0.25)
        g.text(x + 0.3, 1.75, cw - 1.2, 0.9, n, size=40, color=col, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 0.3, 2.65, cw - 0.6, 0.4, l, size=14, color=DARK, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 0.3, 3.02, cw - 0.6, 0.35, d, size=11.5, color=GREY, margin=(0, 0, 0, 0))
        # mini bar sparkline
        for k, hgt in enumerate([0.22, 0.36, 0.28, 0.5, 0.4, 0.62]):
            g.shape(x + 0.3 + k * 0.22, 4.15 - hgt, 0.14, hgt, fill=col, transparency=0 if k == 5 else 55, name="Spark bar")
    ids.append(s.group(x, 1.6, cw, 2.75, b, name=f"KPI {i + 1}"))
s.stagger(ids, "zoom", 150)
note = s.group(L, 4.6, W, 1.3, lambda g: (
    card(g, L, 4.6, W, 1.3, fill=PINK, shadow=False),
    g.image(ICON("lightbulb", "red"), L + 0.3, 4.95, 0.6, 0.6, name="bulb"),
    g.text(L + 1.1, 4.7, W - 1.4, 1.1, [("Insight line: ", {"bold": True, "color": RED}), ("one sentence that tells the audience what the four numbers mean together. Big numbers 40 pt, labels 14 pt, context 11.5 pt — keep the hierarchy.", {})], size=14, color=DARK, valign="m", margin=(0, 0, 0, 0))), name="Insight")
s.animate([(note, "float", 0)])
skill_note(s, "large-number tiles with accent per tile · hand-drawn sparkline bars (shapes) · insight band")

# 15 charts (added by python-pptx post-step)
s = content("Native charts")
s.text(L, 1.5, 5.9, 0.4, "Column chart — editable data", size=14, color=DARK, bold=True, margin=(0, 0, 0, 0))
s.text(L + 6.35, 1.5, 5.9, 0.4, "Line chart — editable data", size=14, color=DARK, bold=True, margin=(0, 0, 0, 0))
skill_note(s, "real PowerPoint charts (right-click › Edit Data) in brand colours, quiet gridlines, data labels on")
CHART_SLIDE = len(deck.slides)

# 16 progress rings
s = content("Progress rings")
vals = [(72, "Completion", RED), (45, "Adoption", PURPLE), (88, "Satisfaction", BLUE), (60, "Coverage", GOLD)]
cw = W / 4
ids = []
for i, (v, lab, col) in enumerate(vals):
    cx = L + cw * i + cw / 2
    cy = 3.2
    d = 2.2
    s.shape(cx - d / 2, cy - d / 2, d, d, geom="ellipse", fill=None, line=LINE, line_w=18, name="Ring track")
    start = 16200000
    end = int((270 + 360 * v / 100) % 360 * 60000)
    arc = s.shape(cx - d / 2, cy - d / 2, d, d, geom="blockArc", fill=col, adj={"adj1": start, "adj2": end, "adj3": 11000}, name=f"Ring {v}%")
    num = s.text(cx - 1, cy - 0.45, 2, 0.7, f"{v}%", size=30, color=col, bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
    lb = s.text(cx - 1.2, cy + 1.35, 2.4, 0.4, lab, size=14, color=DARK, bold=True, align="ctr", margin=(0, 0, 0, 0))
    s.animate([(arc, "wheel", 0, 900), (num, "zoom", 500), (lb, "fade", 700)], trigger="after" if i else "click")
skill_note(s, "block-arc shapes as progress rings (edit the yellow handle to change the value) · Wheel entrance draws each ring")

# 17 table (python-pptx post-step)
s = content("Styled table")
skill_note(s, "native table with banded rows, header in brand red and a highlighted total row — edit like any table")
TABLE_SLIDE = len(deck.slides)

# 18 funnel
s = content("Funnel")
stages = [("Visitors", "10,000"), ("Sign-ups", "4,200"), ("Active", "2,650"), ("Paying", "900"), ("Advocates", "310")]
ids = []
cols = [RED, "D8243C", "B3122A", "8E0E22", DARK]
for i, (lab, val) in enumerate(stages):
    wtop = 7.2 - i * 1.15
    x = L + 0.6 + (7.2 - wtop) / 2
    y = 1.6 + i * 0.86
    def b(g, x=x, y=y, wtop=wtop, lab=lab, val=val, i=i):
        g.shape(x, y, wtop, 0.78, geom="trapezoid", fill=cols[i], adj={"adj": 18000}, rot=180, name="Funnel stage")
        g.text(x, y, wtop, 0.78, [(lab, {"bold": True}), ("   ", {}), (val, {"color": "FFD6DC"})], size=14, color="FFFFFF", align="ctr", valign="m", margin=(0, 0, 0, 0))
    ids.append(s.group(x, y, wtop, 0.78, b, name=f"Stage {i + 1}"))
s.stagger(ids, "wipedown", 180, dur=400)
side = s.group(9.2, 1.6, 3.6, 4.2, lambda g: (
    card(g, 9.2, 1.6, 3.6, 4.2, fill=CARD, shadow=False),
    g.text(9.45, 1.8, 3.1, 0.5, "Conversion between stages", size=14, color=RED, bold=True, margin=(0, 0, 0, 0)),
    g.text(9.45, 2.35, 3.1, 3.3, ["42% visitors → sign-ups", "63% sign-ups → active", "34% active → paying", "34% paying → advocates", "Biggest leak: active → paying"], size=13, color=DARK, bullets=True, space_after=8, margin=(0, 0, 0, 0))), name="Side note")
s.animate([(side, "float", 0)])
skill_note(s, "trapezoids rotated 180° form the funnel · darker shade per stage · Wipe Down reveals top to bottom")

# ================= D =================
divider_a(6, "D", "Process & structure", "Timelines, cycles, hierarchies, matrices and spinners")

# 20 timeline
s = content("Horizontal timeline")
n = 5; w = 2.3; gap = (W - n * w) / (n - 1); cy = 2.75
ln = s.line(L + w / 2, cy, R - w / 2, cy, color=LINE, w=4)
ids = []
for i in range(n):
    x = L + i * (w + gap)
    def b(g, x=x, i=i):
        g.shape(x + w / 2 - 0.5, cy - 0.5, 1.0, 1.0, geom="ellipse", fill=RED if i < 3 else "FFFFFF", line=RED, line_w=3, name="Milestone")
        g.text(x + w / 2 - 0.5, cy - 0.5, 1.0, 1.0, f"Q{i + 1}" if i < 4 else "Q1+", size=15, color="FFFFFF" if i < 3 else RED, bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
        g.text(x, 3.5, w, 0.4, f"Milestone {i + 1}", size=15, color=DARK, bold=True, align="ctr", margin=(0, 0, 0, 0))
        g.text(x, 3.9, w, 1.2, "What happens in this period — two short lines.", size=12, color=GREY, align="ctr", margin=(0, 0, 0, 0))
        if i < 3:
            g.text(x, 1.75, w, 0.4, "done", size=10.5, color=RED, bold=True, align="ctr", margin=(0, 0, 0, 0))
    ids.append(s.group(x, 1.75, w, 3.4, b, name=f"Milestone {i + 1}"))
s.animate([(ln, "wipe", 0, 1000)] + [(g, "float", 150 + i * 220) for i, g in enumerate(ids)], trigger="after")
tag(s, L, 5.35, "filled = done · outline = planned", w=3.3)
skill_note(s, "line wipes left to right, milestones float in along it · filled vs outlined circles show status")

# 21 chevrons
s = content("Process chevrons")
n = 5; pw = (W - 4 * 0.2) / 5
ids = []
for i in range(n):
    x = L + i * (pw + 0.2)
    def b(g, x=x, i=i):
        g.shape(x, 1.7, pw, 1.0, geom="homePlate" if i == 0 else "chevron", fill=RED if i % 2 == 0 else RED2, name="Chevron")
        g.text(x + (0.2 if i == 0 else 0.6), 1.7, pw - 0.8, 1.0, [(f"STEP {i + 1}", {"size": 10, "color": "FFD6DC"}), ("\n", {}), ("Step name", {"bold": True, "size": 15})], size=15, color="FFFFFF", valign="m", margin=(0, 0, 0, 0), line_spacing=95)
        card(g, x, 2.95, pw, 2.4)
        g.text(x + 0.25, 3.1, pw - 0.5, 2.1, ["Input or owner", "Key activity", "Output / exit criteria"], size=12.5, color=DARK, bullets=True, space_after=6, margin=(0, 0, 0, 0))
    ids.append(s.group(x, 1.7, pw, 3.65, b, name=f"Step {i + 1}"))
s.stagger(ids, "wipe", 220, dur=450)
skill_note(s, "Home Plate + Chevron shapes, alternating shades · Wipe from left in sequence")

# 22 cycle with spinning ring
s = content("Cycle diagram — the ring keeps turning")
cx, cy, rad = 4.2, 3.85, 1.85
ring = s.group(cx - rad, cy - rad, 2 * rad, 2 * rad, lambda g: (
    g.shape(cx - rad, cy - rad, 2 * rad, 2 * rad, geom="ellipse", fill=None, line=RED, line_w=4, dash="dash", name="Spinning ring"),
    [g.shape(cx + rad * math.cos(math.radians(a)) - 0.11, cy + rad * math.sin(math.radians(a)) - 0.11, 0.22, 0.22, geom="ellipse", fill=GOLD, name="Ring dot") for a in range(0, 360, 60)]), name="Spinning ring")
core = s.group(cx - 0.9, cy - 0.9, 1.8, 1.8, lambda g: (g.shape(cx - 0.9, cy - 0.9, 1.8, 1.8, geom="ellipse", fill=RED, shadow=True, name="Core"), g.text(cx - 0.9, cy - 0.9, 1.8, 1.8, "Core\nidea", size=16, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))), name="Core")
nodes = []
icons6 = ["lightbulb", "cog1", "users", "chart", "sync", "trophy"]
for i, a in enumerate(range(-90, 270, 60)):
    nx, ny = cx + rad * math.cos(math.radians(a)), cy + rad * math.sin(math.radians(a))
    def b(g, nx=nx, ny=ny, i=i):
        icon_circle(g, nx, ny, 0.8, icons6[i], fill="FFFFFF", color="red", pad=0.25)
        g.shape(nx - 0.4, ny - 0.4, 0.8, 0.8, geom="ellipse", fill=None, line=RED, line_w=2, name="Node ring")
    nodes.append(s.group(nx - 0.4, ny - 0.4, 0.8, 0.8, b, name=f"Node {i + 1}"))
steps = s.group(7.3, 1.6, 5.5, 4.4, lambda g: (
    card(g, 7.3, 1.6, 5.5, 4.4, fill=CARD, shadow=False),
    [(g.text(7.6, 1.8 + k * 0.7, 0.45, 0.45, str(k + 1), size=13, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0), fill=RED, geom="ellipse"),
      g.text(8.2, 1.8 + k * 0.7, 4.4, 0.45, f"Stage {k + 1} — short label and what it produces", size=13, color=DARK, valign="m", margin=(0, 0, 0, 0))) for k in range(6)]), name="Stage list")
s.animate([(core, "zoom", 0, 500), (ring, "wheel", 200, 900)] + [(nd, "zoom", 600 + i * 120, 350) for i, nd in enumerate(nodes)] + [(steps, "float", 1300)], trigger="after")
s.animate([(ring, "spinloop", 0, 14000)], trigger="after")
skill_note(s, "dashed ring + dots grouped and set to Spin · Repeat until end of slide — nodes stay upright because they are outside the group")

# 23 spin showcase
s = content("Spinning animations")
cw = (W - 2 * 0.3) / 3
labels = [("Gears — counter-rotation", "one spins clockwise, the other anti-clockwise"),
          ("Pinwheel — continuous spin", "six pie slices in theme colours grouped and spinning"),
          ("Orbit — satellites around a core", "dots orbit on a hidden ring; the core pulses")]
for i, (h, d) in enumerate(labels):
    x = L + i * (cw + 0.3)
    card(s, x, 1.6, cw, 3.6, fill="FFFFFF", line=LINE, shadow=False)
    s.text(x + 0.25, 4.55, cw - 0.5, 0.35, h, size=13.5, color=DARK, bold=True, align="ctr", margin=(0, 0, 0, 0))
    s.text(x + 0.25, 4.9, cw - 0.5, 0.3, d, size=10.5, color=GREY, align="ctr", margin=(0, 0, 0, 0))
# gears
g1 = s.shape(L + 0.55, 2.0, 1.7, 1.7, geom="gear6", fill=RED, name="Gear big")
g2 = s.shape(L + 2.05, 2.95, 1.2, 1.2, geom="gear9", fill=GOLD, name="Gear small")
s.animate([(g1, "spinloop", 0, 8000), (g2, "spinback", 0, 6000)], trigger="after")
# pinwheel
px = L + cw + 0.3 + cw / 2; py = 3.0
pin = s.group(px - 1.0, py - 1.0, 2.0, 2.0, lambda g: [g.shape(px - 1.0, py - 1.0, 2.0, 2.0, geom="pie", fill=c, adj={"adj1": int(a * 60000), "adj2": int((a + 60) * 60000)}, name="Slice") for a, c in zip(range(0, 360, 60), [RED, PURPLE, BLUE, YELLOW, MAGENTA, GOLD])], name="Pinwheel")
s.shape(px - 0.3, py - 0.3, 0.6, 0.6, geom="ellipse", fill="FFFFFF", shadow=True, name="Pin")
s.animate([(pin, "spinloop", 0, 5000)], trigger="after")
# orbit
ox = L + 2 * (cw + 0.3) + cw / 2; oy = 3.0
orbit = s.group(ox - 1.2, oy - 1.2, 2.4, 2.4, lambda g: (
    g.shape(ox - 1.2, oy - 1.2, 2.4, 2.4, geom="ellipse", fill=None, line=LINE, line_w=1.5, dash="sysDot", name="Orbit path"),
    [g.shape(ox + 1.2 * math.cos(math.radians(a)) - 0.17, oy + 1.2 * math.sin(math.radians(a)) - 0.17, 0.34, 0.34, geom="ellipse", fill=c, name="Satellite") for a, c in zip((0, 120, 240), (RED, PURPLE, BLUE))]), name="Orbit")
corex = s.group(ox - 0.45, oy - 0.45, 0.9, 0.9, lambda g: (g.shape(ox - 0.45, oy - 0.45, 0.9, 0.9, geom="ellipse", fill=RED, shadow=True, name="Core"), g.image(ICON("sync", "white"), ox - 0.22, oy - 0.22, 0.44, 0.44, name="sync")), name="Orbit core")
s.animate([(orbit, "spinloop", 0, 9000), (corex, "pulse", 0, 1200)], trigger="after")
skill_note(s, "Spin emphasis with Repeat: Until End of Slide · negative rotation for counter-spin · Pulse emphasis on the core")

# 24 org chart
s = content("Hierarchy / org chart")
def box(g, x, y, w, h, title, sub, fill="FFFFFF", tc=DARK):
    card(g, x, y, w, h, fill=fill, line=LINE if fill == "FFFFFF" else None, shadow=fill != "FFFFFF")
    g.text(x + 0.1, y + 0.1, w - 0.2, 0.4, title, size=13, color=tc, bold=True, align="ctr", margin=(0, 0, 0, 0))
    g.text(x + 0.1, y + 0.48, w - 0.2, 0.35, sub, size=10.5, color="FFD6DC" if fill == RED else GREY, align="ctr", margin=(0, 0, 0, 0))
top = s.group(5.5, 1.5, 2.4, 0.9, lambda g: box(g, 5.5, 1.5, 2.4, 0.9, "Head of team", "name", fill=RED, tc="FFFFFF"), name="Top")
mids, kids, lines = [], [], []
lines.append(s.line(6.7, 2.4, 6.7, 2.75, color=GREY, w=1.5))
lines.append(s.line(2.1, 2.75, 11.3, 2.75, color=GREY, w=1.5))
for i, mx in enumerate([2.1, 5.17, 8.23, 11.3]):
    lines.append(s.line(mx, 2.75, mx, 3.05, color=GREY, w=1.5))
    mids.append(s.group(mx - 1.2, 3.05, 2.4, 0.9, lambda g, mx=mx, i=i: box(g, mx - 1.2, 3.05, 2.4, 0.9, f"Lead {i + 1}", "function", fill=PINK, tc=RED), name=f"Lead {i + 1}"))
    for k in range(2):
        yy = 4.2 + k * 0.82
        lines.append(s.line(mx, 3.95 + k * 0.82, mx, yy, color=LINE, w=1.5))
        kids.append(s.group(mx - 1.1, yy, 2.2, 0.7, lambda g, mx=mx, yy=yy, k=k: box(g, mx - 1.1, yy, 2.2, 0.7, f"Member {k + 1}", "role"), name="Member"))
s.animate([(top, "zoom", 0)] + [(l, "wipe", 200, 300) for l in lines[:2]] + [(m, "float", 400 + i * 120) for i, m in enumerate(mids)] + [(k, "fade", 900 + i * 60, 300) for i, k in enumerate(kids)], trigger="after")
skill_note(s, "three-level hierarchy from boxes and connectors · reveal top-down")

# 25 hub & spoke
s = content("Hub and spoke")
hx, hy = 6.67, 3.72
hub = s.group(hx - 1.1, hy - 1.1, 2.2, 2.2, lambda g: (g.shape(hx - 1.1, hy - 1.1, 2.2, 2.2, geom="ellipse", fill=RED, shadow=True, name="Hub"), g.text(hx - 1.1, hy - 1.1, 2.2, 2.2, "Central\ntopic", size=18, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))), name="Hub")
spokes, labels = [], []
for i, a in enumerate(range(-90, 270, 45)):
    ex, ey = hx + 3.6 * math.cos(math.radians(a)), hy + 1.75 * math.sin(math.radians(a))
    spokes.append(s.line(hx + 1.1 * math.cos(math.radians(a)), hy + 1.1 * math.sin(math.radians(a)), ex, ey, color=LINE, w=2))
    def b(g, ex=ex, ey=ey, i=i):
        g.shape(ex - 0.95, ey - 0.36, 1.9, 0.72, geom="roundRect", fill="FFFFFF", line=[RED, PURPLE, BLUE, GOLD][i % 4], line_w=2, radius=50000, shadow=True, name="Spoke")
        g.text(ex - 0.95, ey - 0.36, 1.9, 0.72, f"Branch {i + 1}", size=13, color=DARK, bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
    labels.append(s.group(ex - 0.95, ey - 0.36, 1.9, 0.72, b, name=f"Branch {i + 1}"))
s.animate([(hub, "zoom", 0)] + [x for i in range(8) for x in ((spokes[i], "wipe", 300 + i * 150, 300), (labels[i], "zoom", 400 + i * 150, 350))], trigger="after")
skill_note(s, "eight branches on an ellipse around the hub · spokes wipe then pills zoom, clockwise")

# 26 matrix
s = content("2 × 2 matrix")
mx, my, mw, mh = 1.4, 1.6, 7.2, 4.1
quads = [("Quick wins", PINK), ("Big bets", RED), ("Fill-ins", CARD), ("Avoid", "FFFFFF")]
qids = []
for i, (lab, fill) in enumerate(quads):
    qx = mx + (i % 2) * mw / 2; qy = my + (i // 2) * mh / 2
    def b(g, qx=qx, qy=qy, lab=lab, fill=fill):
        g.shape(qx + 0.05, qy + 0.05, mw / 2 - 0.1, mh / 2 - 0.1, geom="roundRect", fill=fill, line=LINE if fill in ("FFFFFF", CARD) else None, radius=6000, name="Quadrant")
        g.text(qx + 0.25, qy + 0.2, mw / 2 - 0.5, 0.4, lab, size=15, color="FFFFFF" if fill == RED else DARK, bold=True, margin=(0, 0, 0, 0))
    qids.append(s.group(qx, qy, mw / 2, mh / 2, b, name=lab))
s.text(mx, my + mh + 0.02, mw, 0.3, "Effort  →", size=11, color=GREY, bold=True, align="ctr", margin=(0, 0, 0, 0))
s.text(0.4, my + mh / 2 - 0.15, 1.0, 0.3, "Impact ↑", size=11, color=GREY, bold=True, align="ctr", margin=(0, 0, 0, 0), rot=-90)
dots = []
for i, (dx, dy, c) in enumerate([(0.9, 0.9, RED), (2.2, 1.4, RED), (5.0, 0.7, PURPLE), (5.8, 1.6, PURPLE), (1.3, 3.2, BLUE), (5.4, 3.5, GREY)]):
    dots.append(s.group(mx + dx - 0.28, my + dy - 0.28, 0.56, 0.56, lambda g, dx=dx, dy=dy, c=c, i=i: (g.shape(mx + dx - 0.28, my + dy - 0.28, 0.56, 0.56, geom="ellipse", fill=c, shadow=True, name="Item"), g.text(mx + dx - 0.28, my + dy - 0.28, 0.56, 0.56, str(i + 1), size=11, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))), name=f"Item {i + 1}"))
leg = s.group(9.1, 1.6, 3.7, 4.1, lambda g: (card(g, 9.1, 1.6, 3.7, 4.1, fill=CARD, shadow=False), g.text(9.35, 1.8, 3.2, 0.4, "Items", size=14, color=RED, bold=True, margin=(0, 0, 0, 0)), g.text(9.35, 2.25, 3.2, 3.6, [f"{k + 1}. Initiative name" for k in range(6)], size=13, color=DARK, space_after=6, margin=(0, 0, 0, 0))), name="Legend")
s.animate([(q, "fade", i * 120, 350) for i, q in enumerate(qids)] + [(leg, "float", 500)], trigger="after")
s.stagger(dots, "zoom", 120, dur=350)
skill_note(s, "quadrants as tinted shapes · numbered items zoom in on click · rotated axis label")

# 27 gantt
s = content("Gantt roadmap")
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
gx, gw = L + 2.6, W - 2.6
mw = gw / len(months)
for i, m in enumerate(months):
    s.text(gx + i * mw, 1.55, mw, 0.3, m, size=11, color=GREY, bold=True, align="ctr", margin=(0, 0, 0, 0))
    s.line(gx + i * mw, 1.9, gx + i * mw, 5.7, color=LINE, w=0.75, dash="dash")
s.line(gx + 3.5 * mw, 1.9, gx + 3.5 * mw, 5.7, color=RED, w=1.5)
s.text(gx + 3.5 * mw - 0.5, 5.72, 1.0, 0.3, "today", size=10, color=RED, bold=True, align="ctr", margin=(0, 0, 0, 0))
bars = [("Workstream 1", 0, 2.5, RED), ("Workstream 2", 1.5, 3, PURPLE), ("Workstream 3", 3, 2, BLUE), ("Workstream 4", 4, 3.5, GOLD), ("Launch", 6.5, 0.5, DARK)]
bids = []
for i, (lab, st, ln, c) in enumerate(bars):
    y = 2.05 + i * 0.72
    s.text(L, y, 2.4, 0.5, lab, size=13, color=DARK, bold=True, valign="m", margin=(0, 0, 0, 0))
    bids.append(s.group(gx + st * mw, y + 0.05, ln * mw, 0.4, lambda g, y=y, st=st, ln=ln, c=c: (g.shape(gx + st * mw, y + 0.05, ln * mw, 0.4, geom="roundRect", fill=c, radius=50000, name="Bar"), g.shape(gx + st * mw, y + 0.05, ln * mw * 0.55, 0.4, geom="roundRect", fill="FFFFFF", radius=50000, transparency=65, name="Bar progress")), name=lab))
s.stagger(bids, "wipe", 150, dur=500)
skill_note(s, "month grid with dashed lines · today marker · rounded bars with a lighter progress overlay · Wipe reveals each bar")

# ================= E =================
# 28 divider B dark
s = deck.slide(7, "cover")
s.gradient_rect(0, 0, 13.333, 7.5, "2B2B2E", DARK, angle=60, name="Dark background")
stars = s.shape(8.0, 0.4, 6.0, 6.0, geom="star32", fill=RED, transparency=82, name="Burst")
num = s.text(1.0, 1.6, 4, 1.6, "E", size=96, color=GOLD, bold=True, margin=(0, 0, 0, 0))
t = s.text(1.0, 3.2, 7.5, 1.2, "Visual effects", size=40, color="FFFFFF", bold=True, margin=(0, 0, 0, 0), font="Ubuntu")
st = s.text(1.0, 4.45, 7.5, 0.8, "Photo grids, device mock-ups, quotes, team and a closing call to action", size=15, color="C9CCD2", margin=(0, 0, 0, 0))
s.animate([(stars, "spinloop", 0, 30000), (num, "spinin", 0, 700), (t, "float", 300), (st, "fade", 600)], trigger="after")
s.text(L, 6.9, 8, 0.3, "Skill: dark gradient variant · slow 32-point star rotating behind the title", size=10.5, color="9AA0A6", italic=True, margin=(0, 0, 0, 0))

# 29 photo grid
s = content("Photo grid")
pics = [(L, 1.55, 6.0, 3.9, "wide"), (6.85, 1.55, 2.85, 1.85, "square"), (9.95, 1.55, 2.85, 1.85, "square"), (6.85, 3.6, 5.95, 1.85, "wide")]
ids = []
for i, (x, y, w, h, k) in enumerate(pics):
    def b(g, x=x, y=y, w=w, h=h, k=k, i=i):
        g.image(PH(k), x, y, w, h, name=f"Photo {i + 1} — Change Picture")
        g.shape(x + 0.2, y + h - 0.6, 1.9, 0.4, geom="roundRect", fill=DARK, radius=50000, transparency=25, name="Caption pill")
        g.text(x + 0.2, y + h - 0.6, 1.9, 0.4, f"Caption {i + 1}", size=10.5, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
    ids.append(s.group(x, y, w, h, b, name=f"Photo {i + 1}"))
s.stagger(ids, "zoom", 150, dur=450)
s.text(L, 5.6, W, 0.4, "Mixed sizes keep the grid lively — one hero image, two squares, one strip. Captions sit on translucent pills.", size=12.5, color=GREY, margin=(0, 0, 0, 0))
skill_note(s, "picture placeholders with translucent caption pills · Change Picture keeps the crop box")

# 30 device mock-ups
s = content("Device mock-ups")
# laptop
lx, ly = L + 0.3, 1.75
lap = s.group(lx, ly, 6.6, 4.1, lambda g: (
    g.shape(lx + 0.5, ly, 5.6, 3.5, geom="roundRect", fill=DARK, radius=5000, shadow=True, name="Laptop lid"),
    g.image(PH("wide"), lx + 0.68, ly + 0.18, 5.24, 3.14, name="Laptop screen — Change Picture"),
    g.shape(lx, ly + 3.5, 6.6, 0.3, geom="roundRect", fill="3A3A3E", radius=50000, name="Laptop base"),
    g.shape(lx + 2.6, ly + 3.5, 1.4, 0.1, geom="roundRect", fill="6B6B70", radius=50000, name="Notch")), name="Laptop")
# phone
phx, phy = 8.6, 1.4
ph = s.group(phx, phy, 2.4, 4.6, lambda g: (
    g.shape(phx, phy, 2.4, 4.6, geom="roundRect", fill=DARK, radius=12000, shadow=True, name="Phone"),
    g.image(PH("tall"), phx + 0.12, phy + 0.12, 2.16, 4.36, name="Phone screen — Change Picture"),
    g.shape(phx + 0.8, phy + 0.18, 0.8, 0.16, geom="roundRect", fill=DARK, radius=50000, name="Speaker")), name="Phone")
s.animate([(lap, "float", 0, 600), (ph, "flyright", 300, 600)], trigger="after")
pill = s.group(11.3, 1.8, 1.5, 1.5, lambda g: (g.shape(11.3, 1.8, 1.5, 1.5, geom="ellipse", fill=GOLD, shadow=True, name="Sticker"), g.text(11.3, 1.8, 1.5, 1.5, "NEW\nUI", size=16, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))), name="Sticker")
s.animate([(pill, "spinin", 0, 700), (pill, "pulse", 700, 1500)], trigger="after")
skill_note(s, "laptop and phone frames from rounded rectangles · drop a screenshot on the grey screen · sticker spins in then pulses")

# 31 dark hero with spinning sparkle
s = deck.slide(7, "fade")
s.gradient_rect(0, 0, 13.333, 7.5, "8E0E22", RED, angle=120, name="Red background")
sp1 = s.shape(7.6, 0.6, 5.4, 5.4, geom="star24", fill=GOLD, transparency=65, name="Sparkle large")
sp2 = s.shape(8.6, 1.6, 3.4, 3.4, geom="star8", fill="FFFFFF", transparency=75, name="Sparkle small")
badge = s.group(9.3, 2.3, 2.0, 2.0, lambda g: (g.shape(9.3, 2.3, 2.0, 2.0, geom="ellipse", fill="FFFFFF", shadow=True, name="Badge"), g.image(ICON("trophy", "red"), 9.75, 2.75, 1.1, 1.1, name="trophy")), name="Badge")
big = s.text(0.8, 1.6, 6.8, 2.6, "Big moment\nheadline", size=54, color="FFFFFF", bold=True, margin=(0, 0, 0, 0), font="Ubuntu", line_spacing=95)
sub = s.text(0.8, 4.3, 6.8, 0.9, "Use this for a launch, a milestone or the single number you want remembered.", size=16, color="FFD6DC", margin=(0, 0, 0, 0))
s.animate([(sp1, "spinloop", 0, 20000), (sp2, "spinback", 0, 12000), (badge, "spinin", 0, 800), (big, "float", 400, 700), (sub, "fade", 900)], trigger="after")
s.text(L, 6.9, 10, 0.3, "Skill: two sparkles rotating in opposite directions behind a spin-in badge · white-on-red hierarchy", size=10.5, color="FFD6DC", italic=True, margin=(0, 0, 0, 0))

# 32 quote
s = content("Quote")
s.image(ICON("quote", "red"), L + 0.1, 1.6, 1.1, 1.1, name="Quote mark", transparency=70)
q = s.text(L + 1.4, 1.7, 7.4, 2.6, "“A short, memorable quotation that supports the message of this section — keep it to three lines.”", size=26, color=DARK, italic=True, margin=(0, 0, 0, 0), font="Ubuntu", line_spacing=105)
who = s.group(L + 1.4, 4.5, 6, 1.0, lambda g: (g.shape(L + 1.4, 4.5, 1.0, 1.0, geom="ellipse", fill=PINK, name="Avatar ring"), g.image(ICON("user", "red"), L + 1.65, 4.75, 0.5, 0.5, name="avatar"), g.text(L + 2.6, 4.55, 4.5, 0.45, "Name Surname", size=15, color=DARK, bold=True, margin=(0, 0, 0, 0)), g.text(L + 2.6, 4.98, 4.5, 0.4, "Role, Company", size=12, color=GREY, margin=(0, 0, 0, 0))), name="Attribution")
pic = s.image(PH("tall"), 9.6, 1.6, 3.2, 4.3, name="Portrait — Change Picture")
s.animate([(pic, "fade", 0, 700), (q, "float", 200, 700), (who, "fade", 800)], trigger="after")
skill_note(s, "oversized faded quotation mark · avatar ring (swap the icon for a cropped photo) · portrait frame")

# 33 team
s = content("Team")
cw = (W - 3 * 0.3) / 4
ids = []
for i in range(4):
    x = L + i * (cw + 0.3)
    def b(g, x=x, i=i):
        card(g, x, 1.6, cw, 4.1)
        g.image(PH("square"), x + cw / 2 - 0.9, 1.9, 1.8, 1.8, name=f"Photo {i + 1} — Change Picture")
        g.shape(x + cw / 2 - 0.9, 1.9, 1.8, 1.8, geom="ellipse", fill=None, line=[RED, PURPLE, BLUE, GOLD][i], line_w=4, name="Photo ring")
        g.text(x + 0.2, 3.9, cw - 0.4, 0.45, "Name Surname", size=16, color=DARK, bold=True, align="ctr", margin=(0, 0, 0, 0))
        g.text(x + 0.2, 4.33, cw - 0.4, 0.4, "Role · team", size=12, color=RED, bold=True, align="ctr", margin=(0, 0, 0, 0))
        g.text(x + 0.3, 4.8, cw - 0.6, 0.8, "One line about what this person brings to the project.", size=11.5, color=GREY, align="ctr", margin=(0, 0, 0, 0))
    ids.append(s.group(x, 1.6, cw, 4.1, b, name=f"Member {i + 1}"))
s.stagger(ids, "float", 150)
skill_note(s, "square photo placeholder behind a circular ring — crop the photo to a circle with Picture Format › Crop to Shape")

# 34 CTA
s = content("Closing call to action")
big = s.text(L, 1.7, 8.5, 1.6, [("What should happen ", {}), ("next week", {"color": RED}), ("?", {})], size=36, color=DARK, bold=True, margin=(0, 0, 0, 0), font="Ubuntu")
pts = s.text(L, 3.4, 8.0, 1.6, ["Decision you need from this audience", "Who does what, by when", "How you will report back"], size=15, color=DARK, bullets=True, space_after=8, margin=(0, 0, 0, 0))
btn = s.group(L, 5.15, 3.6, 0.7, lambda g: (g.shape(L, 5.15, 3.6, 0.7, geom="roundRect", fill=RED, radius=50000, shadow=True, name="CTA button"), g.text(L, 5.15, 3.6, 0.7, "Approve the next step  →", size=15, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))), name="CTA button")
plane = s.image(ICON("paperplane", "red"), 9.3, 3.0, 1.1, 1.1, name="Paper plane", rot=20)
trail = s.line(9.0, 4.5, 11.8, 2.9, color=LINE, w=2, dash="sysDash")
ringd = s.shape(9.6, 1.7, 3.0, 3.0, geom="ellipse", fill=PINK, name="Disc")
s.animate([(ringd, "zoom", 0, 500), (big, "float", 100, 600), (pts, "float", 400), (btn, "zoom", 700), (trail, "wipe", 900, 600), (plane, "bounce", 1000, 1800)], trigger="after")
s.animate([(btn, "pulse", 0, 1200)], trigger="after")
skill_note(s, "motion path (custom curve) on the paper plane · button pulses until the slide ends · dashed trail wipes in")

# ================= F · SLIDE TRANSITIONS =================
divider_a(6, "F", "Slide transitions", "Each stage arrives with a different transition — press Next and watch")

STAGES = [
    ("gallery", "Gallery", "The slide spins in like a carousel — the classic stage-to-stage turn", "film", "light"),
    ("cube", "Cube", "The stage rotates on a 3-D box; the new slide is the next face", "layer", "tint"),
    ("rotate", "Rotate", "Dynamic content: only the content turns in, the background stays", "sync", "light"),
    ("orbit", "Orbit", "The next stage swings around you like a planet", "globe", "red"),
    ("ferris", "Ferris Wheel", "Slides ride a wheel into view — big, slow, theatrical", "star", "light"),
    ("vortex", "Vortex", "The scene dissolves into a spinning stream of particles", "magic", "dark"),
    ("switch", "Switch", "Two stages swap places in 3-D space", "sync", "light"),
    ("flip", "Flip", "The slide turns over like a card", "th", "tint"),
    ("doors", "Doors", "Double doors open onto the next stage", "store", "light"),
    ("prestige", "Prestige", "Curtain and spotlight — the showman's reveal", "trophy", "red"),
    ("origami", "Origami", "The slide folds itself into the next one", "leaf", "light"),
    ("airplane", "Airplane", "Folds into a paper plane and flies away", "paperplane", "tint"),
    ("pagecurl", "Page Curl", "Turn the page — good for chapter breaks", "filealt", "light"),
    ("honeycomb", "Honeycomb", "Hex cells assemble the new stage", "th", "dark"),
    ("ripple", "Ripple", "A drop in water from the centre", "heart", "light"),
    ("fracture", "Fracture", "The glass shatters into the next slide", "bolt", "tint"),
    ("curtains", "Curtains", "The stage curtain draws open", "play", "red"),
    ("wheel", "Wheel", "Clock-hand reveal with eight spokes — the classic spinner", "clock", "light"),
    ("flythrough", "Fly Through", "The camera flies into the next stage, with a bounce", "rocket", "dark"),
]
N = len(STAGES) + 3  # + morph pair + guide
STYLE = {
    "light": dict(bg=None, ink=DARK, sub=GREY, acc=RED, disc=PINK, dot=LINE),
    "tint": dict(bg=("FCEEF0", "FFFFFF"), ink=DARK, sub=GREY, acc=RED, disc="FFFFFF", dot="E8C9CF"),
    "red": dict(bg=(RED, "8E0E22"), ink="FFFFFF", sub="FFD6DC", acc=GOLD, disc="FFFFFF", dot="F08A9A"),
    "dark": dict(bg=("2B2B2E", DARK), ink="FFFFFF", sub="C9CCD2", acc=GOLD, disc="3A3A3E", dot="55575C"),
}

def progress(s, i, st):
    n = N
    dw = 0.16; gap = 0.1
    x0 = 6.667 - (n * dw + (n - 1) * gap) / 2
    for k in range(n):
        s.shape(x0 + k * (dw + gap), 6.55, dw, dw, geom="ellipse", fill=st["acc"] if k == i else st["dot"], name="Progress dot")
    s.text(0.54, 6.45, 3.0, 0.35, f"Stage {i + 1} of {n}", size=11, color=st["sub"], bold=True, margin=(0, 0, 0, 0))
    s.text(9.8, 6.45, 3.0, 0.35, "Next ▶", size=11, color=st["sub"], bold=True, align="r", margin=(0, 0, 0, 0))

def stage(i, key, name, desc, icon, style):
    st = STYLE[style]
    s = deck.slide(7, (key, 1500))
    if st["bg"]:
        s.gradient_rect(0, 0, 13.333, 7.5, st["bg"][0], st["bg"][1], angle=45, name="Stage background")
    lab = s.text(1.0, 1.25, 4, 0.4, "STAGE", size=13, color=st["acc"], bold=True, margin=(0, 0, 0, 0))
    num = s.text(1.0, 1.55, 4, 1.6, f"{i + 1:02d}", size=96, color=st["acc"], bold=True, margin=(0, 0, 0, 0), font="Ubuntu")
    t = s.text(1.0, 3.25, 6.8, 0.8, f"{name}", size=36, color=st["ink"], bold=True, margin=(0, 0, 0, 0), font="Ubuntu")
    d = s.text(1.0, 4.05, 6.6, 0.9, desc, size=15, color=st["sub"], margin=(0, 0, 0, 0))
    ticket = s.group(1.0, 5.05, 6.4, 1.1, lambda g: (
        g.shape(1.0, 5.05, 6.4, 1.1, geom="roundRect", fill="FFFFFF" if style != "light" else CARD, radius=12000, shadow=style != "light", transparency=12 if style in ("red", "dark") else 0, name="Ticket"),
        g.shape(1.0, 5.05, 0.12, 1.1, geom="rect", fill=st["acc"], name="Ticket stub"),
        g.text(1.35, 5.15, 5.9, 0.4, [("Transition applied to this slide: ", {"color": GREY}), (name, {"bold": True, "color": RED})], size=12.5, color=DARK, margin=(0, 0, 0, 0)),
        g.text(1.35, 5.55, 5.9, 0.5, "Duration 1.5 s · change it in Transitions › Duration, or pick Effect Options for direction. Copy this slide to reuse the effect.", size=10.5, color=GREY, margin=(0, 0, 0, 0))), name="Ticket")
    cx, cy = 10.25, 3.55
    disc = s.shape(cx - 1.9, cy - 1.9, 3.8, 3.8, geom="ellipse", fill=st["disc"], name="Stage disc", transparency=0 if style == "light" else 10)
    ring = s.shape(cx - 2.25, cy - 2.25, 4.5, 4.5, geom="ellipse", fill=None, line=st["acc"], line_w=3, dash="dash", name="Stage ring")
    badge = s.group(cx - 0.8, cy - 0.8, 1.6, 1.6, lambda g: (g.shape(cx - 0.8, cy - 0.8, 1.6, 1.6, geom="ellipse", fill=st["acc"], shadow=True, name="Icon disc"), g.image(ICON(icon, "white"), cx - 0.42, cy - 0.42, 0.84, 0.84, name=icon)), name="Stage icon")
    progress(s, i, st)
    s.animate([(ring, "spinloop", 0, 24000), (badge, "spinin", 0, 700), (lab, "fade", 200), (num, "float", 250), (t, "float", 400), (d, "fade", 600), (ticket, "float", 750)], trigger="after")
    return s

for i, (key, name, desc, icon, style) in enumerate(STAGES):
    stage(i, key, name, desc, icon, style)

# ---- Morph pair (shapes with identical names glide between the two slides)
BALLS = [RED, PURPLE, BLUE, GOLD, MAGENTA]
def morph_slide(after):
    s = deck.slide(7, ("morph", 1500) if after else ("fade", 700))
    s.title("Morph — " + ("after: same shapes, new positions" if after else "before: five balls in a row"), **TITLE)
    for k, c in enumerate(BALLS):
        if after:
            ang = math.radians(200 + k * 35)
            d2 = 0.7 + 0.35 * k
            x, y = 9.3 + 2.7 * math.cos(ang) - d2 / 2, 3.9 + 1.9 * math.sin(ang) - d2 / 2
            s.shape(x, y, d2, d2, geom="ellipse", fill=c, shadow=True, name=f"!!Ball {k + 1}")
        else:
            s.shape(1.0 + k * 1.3, 3.2, 0.9, 0.9, geom="ellipse", fill=c, shadow=True, name=f"!!Ball {k + 1}")
    if after:
        s.shape(0.9, 1.7, 5.2, 2.0, geom="roundRect", fill=RED, radius=10000, shadow=True, name="!!Card", rot=-4)
        s.text(1.2, 1.9, 4.6, 1.6, [("Morph", {"bold": True, "size": 24}), ("\n", {}), ("The card grew, turned and changed colour; the balls flew into an arc — PowerPoint tweened everything.", {"size": 13})], size=13, color="FFFFFF", valign="m", margin=(0, 0, 0, 0), name="!!Card text")
        s.shape(1.0, 4.6, 5.0, 0.35, geom="roundRect", fill=GOLD, radius=50000, name="!!Bar")
        s.text(1.0, 5.1, 5.6, 0.9, "Rule: give matching shapes the same name on both slides (Selection Pane). Names starting with !! are matched even if the shapes differ.", size=11.5, color=GREY, margin=(0, 0, 0, 0))
    else:
        s.shape(8.3, 4.5, 3.2, 1.2, geom="roundRect", fill=CARD, radius=10000, shadow=False, name="!!Card")
        s.text(8.5, 4.6, 2.8, 1.0, [("Morph", {"bold": True, "size": 16}), ("\n", {}), ("press Next →", {"size": 12})], size=12, color=DARK, valign="m", margin=(0, 0, 0, 0), name="!!Card text")
        s.shape(1.0, 4.6, 2.0, 0.35, geom="roundRect", fill=LINE, radius=50000, name="!!Bar")
        s.text(1.0, 5.1, 7.0, 0.9, "Next slide uses the Morph transition. Every shape here has a twin with the same name there — watch them move, grow and recolour.", size=12.5, color=GREY, margin=(0, 0, 0, 0))
    progress(s, len(STAGES) + (1 if after else 0), STYLE["light"])
    skill_note(s, "Morph transition (PowerPoint 2019 / 365) — objects matched by name; works for position, size, rotation and colour")
    return s
morph_slide(False); morph_slide(True)

# ---- guide
s = deck.slide(7, ("glitter", 1500))
s.title("Transition guide — which one, when", **TITLE)
cols3 = [("Subtle · everyday", RED, ["Fade · Push · Wipe", "Split · Wheel · Reveal", "Use on content slides", "0.7–1 s"]),
         ("Exciting · dividers", PURPLE, ["Gallery · Cube · Doors · Flip", "Prestige · Curtains · Origami", "Page Curl · Airplane · Fracture", "Honeycomb · Ripple · Vortex · Switch", "1.5 s, one family per deck"]),
         ("Dynamic content · stages", BLUE, ["Rotate · Orbit · Ferris Wheel", "Conveyor · Pan · Window · Fly Through", "Background stays, content moves —", "perfect for stage-to-stage flows", "1.5–2 s"])]
cw = (W - 2 * 0.3) / 3
ids = []
for i, (h, c, items) in enumerate(cols3):
    x = L + i * (cw + 0.3)
    def b(g, x=x, h=h, c=c, items=items):
        card(g, x, 1.6, cw, 3.3)
        g.shape(x, 1.6, cw, 0.6, geom="round2SameRect", fill=c, radius=8000, name="Head")
        g.text(x, 1.6, cw, 0.6, h, size=15, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
        g.text(x + 0.3, 2.4, cw - 0.6, 2.4, items, size=12.5, color=DARK, bullets=True, space_after=5, margin=(0, 0, 0, 0))
    ids.append(s.group(x, 1.6, cw, 3.3, b, name=h))
s.stagger(ids, "float", 150)
tipb = s.group(L, 5.1, W, 0.85, lambda g: (card(g, L, 5.1, W, 0.85, fill=PINK, shadow=False), g.image(ICON("lightbulb", "red"), L + 0.3, 5.3, 0.45, 0.45, name="bulb"),
    g.text(L + 1.0, 5.1, W - 1.3, 0.85, [("Morph", {"bold": True, "color": RED}), (" replaces most animation work: duplicate a slide, move things, apply Morph. Keep transitions consistent — one subtle effect for content, one showpiece for section breaks.", {})], size=13, color=DARK, valign="m", margin=(0, 0, 0, 0))), name="Tip")
s.animate([(tipb, "float", 0)])
progress(s, N - 1, STYLE["light"])
skill_note(s, "this slide arrives with Glitter · every stage in this section is a copy-ready example of one transition")

# ================= G · ROTATE & TRANSFORM (Morph) =================
divider_a(5, "G", "Rotate & transform", "Morph sequences: duplicate a slide, rotate or resize the twins, press Next")

# ---- G1: rotating wheel menu — 4 slides, the wheel turns 90° each time (true rotation via a rotated group)
WHEEL = [("rocket", "Launch", "The first stage of the story — what we set out to do"),
         ("shield", "Protect", "Second stage — the safeguards and the rules of the game"),
         ("heart", "Delight", "Third stage — what the customer feels at the end"),
         ("star", "Celebrate", "Fourth stage — results, thanks and what comes next")]
WCX, WCY, WR = -0.5, 3.95, 2.55   # wheel centre sits off the left edge
def wheel_slide(i):
    s = deck.slide(7, ("morph", 1300) if i else ("fade", 700))
    s.title("Rotating wheel — press Next", x=2.7, y=0.42, w=8.1, h=0.9)
    # rotating part: a group with the disc, dashed ring and 12 tick marks; rotated -90° per step
    def ring(g):
        g.shape(WCX - WR, WCY - WR, 2 * WR, 2 * WR, geom="ellipse", fill=PINK, name="!!Wheel disc")
        g.shape(WCX - WR + 0.35, WCY - WR + 0.35, 2 * WR - 0.7, 2 * WR - 0.7, geom="ellipse", fill=None, line=RED, line_w=3, dash="dash", name="!!Wheel ring")
        for k in range(12):
            a = math.radians(k * 30)
            r1 = WR - 0.75
            g.shape(WCX + r1 * math.cos(a) - 0.06, WCY + r1 * math.sin(a) - 0.06, 0.12, 0.12, geom="ellipse", fill=RED if k % 3 == 0 else "E8C9CF", name=f"!!Tick {k}")
    s.group(WCX - WR, WCY - WR, 2 * WR, 2 * WR, ring, name="!!Wheel", rot=-90 * i)
    # nodes stay upright: positioned on the wheel, active one at the right (angle 0)
    for k, (ic, h, d) in enumerate(WHEEL):
        a = math.radians((k - i) * 90)
        active = k == i
        dsz = 1.3 if active else 0.85
        nx, ny = WCX + (WR - 0.15) * math.cos(a), WCY + (WR - 0.15) * math.sin(a)
        s.shape(nx - dsz / 2, ny - dsz / 2, dsz, dsz, geom="ellipse", fill=RED if active else "FFFFFF", line=None if active else RED, line_w=2, shadow=active, name=f"!!Node {k}")
        isz = dsz * 0.5
        s.image(ICON(ic, "white" if active else "red"), nx - isz / 2, ny - isz / 2, isz, isz, name=f"!!Node icon {k}")
    # content panel transforms: number grows, title and text change, accent bar slides
    ic, h, d = WHEEL[i]
    s.text(4.3, 1.7, 2.5, 1.6, f"{i + 1:02d}", size=84, color=PINK, bold=True, margin=(0, 0, 0, 0), font="Ubuntu", name="!!Step number")
    s.shape(4.4, 3.35, 0.9 + 0.6 * i, 0.12, geom="roundRect", fill=RED, radius=50000, name="!!Accent bar")
    s.text(4.4, 3.6, 4.2, 0.8, h, size=36, color=DARK, bold=True, margin=(0, 0, 0, 0), font="Ubuntu", name="!!Stage title")
    s.text(4.4, 4.45, 4.1, 1.1, d, size=15, color=GREY, margin=(0, 0, 0, 0), name="!!Stage text")
    pic = s.image(PH("wide"), 9.1 - 0.15 * i, 1.75 + 0.1 * i, 3.5 + 0.2 * i, 2.0 + 0.12 * i, name="!!Stage image", rot=6 - 4 * i)
    for k in range(4):
        s.shape(4.4 + k * 0.32, 5.75, 0.2 if k != i else 0.6, 0.2, geom="roundRect", fill=RED if k == i else LINE, radius=50000, name=f"!!Pager {k}")
    s.text(2.7, 6.08, 10.0, 0.3, [("Skill: ", {"bold": True, "color": RED}), ("Morph + a rotated group: the wheel group turns −90° per slide, nodes stay upright, the panel resizes and the picture straightens" if i == 0 else f"wheel group rotation = {-90 * i}° · active node grows · picture rotation {6 - 4 * i}°", {})], size=10.5, color=GREY, italic=True, margin=(0, 0, 0, 0))
    return s
for i in range(4):
    wheel_slide(i)

# ---- G2: rotate & transform hero card — 3 slides
def hero_slide(i):
    s = deck.slide(7, ("morph", 1400) if i else ("fade", 700))
    s.title("Rotate & transform a hero card", **TITLE)
    cards = [dict(x=1.2, y=2.0, w=5.2, h=3.2, rot=-8, fill=RED, txt="A tilted card…"),
             dict(x=3.6, y=1.75, w=6.2, h=3.9, rot=0, fill=DARK, txt="…straightens and grows…"),
             dict(x=7.0, y=2.2, w=5.4, h=3.1, rot=6, fill=GOLD, txt="…then turns the other way.")][i]
    s.shape(cards["x"], cards["y"], cards["w"], cards["h"], geom="roundRect", fill=cards["fill"], radius=10000, shadow=True, rot=cards["rot"], name="!!Hero card")
    s.text(cards["x"] + 0.4, cards["y"] + 0.4, cards["w"] - 0.8, cards["h"] - 0.8, [(cards["txt"], {"bold": True, "size": 26}), ("\n", {}), ("Same shape, same name on every slide — only position, size, rotation and colour change.", {"size": 13, "color": "FFE3E7" if i != 1 else "C9CCD2"})], size=13, color="FFFFFF", valign="m", margin=(0, 0, 0, 0), rot=cards["rot"], name="!!Hero text")
    orb = [dict(x=8.9, y=1.5, d=1.6, rot=0), dict(x=10.6, y=4.9, d=1.0, rot=120), dict(x=1.4, y=3.6, d=1.7, rot=-150)][i]
    s.shape(orb["x"], orb["y"], orb["d"], orb["d"], geom="star8", fill=GOLD if i != 2 else RED, rot=orb["rot"], name="!!Orb")
    badge = [dict(x=1.0, y=1.5), dict(x=10.5, y=1.5), dict(x=1.0, y=1.5)][i]
    s.group(badge["x"], badge["y"], 1.5, 1.5, lambda g, b=badge: (g.shape(b["x"], b["y"], 1.5, 1.5, geom="ellipse", fill="FFFFFF", shadow=True, name="!!Badge disc"), g.image(ICON("sync", "red"), b["x"] + 0.4, b["y"] + 0.4, 0.7, 0.7, name="!!Badge icon")), name="!!Badge", rot=[0, 180, 360 - 20][i])
    skill_note(s, ["three slides, one card: rotation −8° → 0° → 6°, size and colour change with it · the badge group spins 180° per step", "Morph takes the shortest rotation path — keep each step under 180°", "to add a stage: duplicate the last slide, move / rotate the twins, Morph is already applied"][i])
    return s
for i in range(3):
    hero_slide(i)

# ---- G3: photos spin from a scatter into a grid — 2 slides
def photo_slide(after):
    s = deck.slide(7, ("morph", 1500) if after else ("fade", 700))
    s.title("Scatter → grid: frames rotate into place", **TITLE)
    scatter = [(1.2, 1.9, 3.2, 2.0, -12), (4.9, 1.5, 2.6, 2.6, 9), (2.2, 4.0, 2.8, 1.75, 7), (8.6, 2.3, 3.6, 2.25, -6)]
    grid = [(L, 1.6, 6.0, 3.75, 0), (6.84, 1.6, 2.85, 1.78, 0), (9.95, 1.6, 2.85, 1.78, 0), (6.84, 3.57, 5.96, 1.78, 0)]
    kinds = ["wide", "square", "wide", "wide"]
    for k, ((x, y, w, h, r), kind) in enumerate(zip(grid if after else scatter, kinds)):
        s.shape(x - 0.06, y - 0.06, w + 0.12, h + 0.12, geom="roundRect", fill="FFFFFF", radius=4000, shadow=True, rot=r, name=f"!!Frame {k}")
        s.image(PH(kind), x, y, w, h, rot=r, name=f"!!Photo {k}")
    if after:
        for k, (x, y, w, h, r) in enumerate(grid):
            s.shape(x + 0.2, y + h - 0.55, 1.6, 0.36, geom="roundRect", fill=DARK, radius=50000, transparency=25, name=f"Caption pill {k}")
            s.text(x + 0.2, y + h - 0.55, 1.6, 0.36, f"Caption {k + 1}", size=10.5, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
    else:
        s.text(8.2, 5.0, 4.6, 0.8, "Four frames thrown on the table — press Next and they rotate into a tidy grid.", size=13, color=GREY, margin=(0, 0, 0, 0))
    skill_note(s, "same frames and pictures on both slides (names !!Frame n / !!Photo n); rotation and size are the only differences — Morph does the choreography")
    return s
photo_slide(False); photo_slide(True)

# ================= THANK YOU =================
s = deck.slide(1, "fade")
t = s.title("Thank you", x=0.57, y=2.75, w=6.0, h=1.1, size=40)
q = s.text(0.6, 3.9, 6.4, 0.6, "Questions & discussion", size=20, color=RED, bold=True, margin=(0, 0, 0, 0))
c = s.text(0.6, 4.55, 6.4, 0.5, "Name  ·  email  ·  team", size=14, color=GREY, margin=(0, 0, 0, 0))
s.animate([(t, "float", 0, 600), (q, "fade", 400), (c, "fade", 650)], trigger="after")

# reorder fix: shapes added after a group in slide 6 (bulb) — fine.
deck.save()
print("slides:", len(deck.slides), "chart slide:", CHART_SLIDE, "table slide:", TABLE_SLIDE)
