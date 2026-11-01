import sys, subprocess, shutil, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pptlib import Deck

HERE = Path(__file__).parent  # expects tpl/unpacked, icons/ and writes build/ next to this file
TPL = HERE / "tpl/unpacked"
BUILD = HERE / "build"
ICON = lambda n, c="red": str(HERE / "icons" / f"{n}-{c}.png")

RED, DARK, GREY, CARD, PINK, GOLD = "E31836", "1F1F1F", "5F6062", "F6F6F7", "FCEEF0", "C9A04B"
WA_GREEN, WA_DARK, WA_BG, WA_USER = "25D366", "075E54", "EFEAE2", "DCF8C6"
LINE = "E3E3E6"
TITLE_POS = dict(x=0.54, y=0.42, w=10.2, h=0.9)
FOOT = "Illustrative figures for discussion — replace with your own data"

deck = Deck(TPL, BUILD)

def content_slide(title, transition="fade"):
    s = deck.slide(7, transition)
    s.title(title, **TITLE_POS)
    return s

def divider(layout, number, title, sub):
    s = deck.slide(layout, "push")
    num = s.text(1.31, 1.35, 3, 1.0, number, size=54, color=GOLD, bold=True, margin=(0, 0, 0, 0))
    t = s.title(title, x=1.21, y=2.35, w=6.5, h=1.1, size=40)
    st = s.text(1.31, 3.45, 6.5, 1.0, sub, size=18, color=GREY, margin=(0, 0, 0, 0))
    s.animate([(num, "zoom", 0), (t, "float", 150), (st, "fade", 350)], trigger="after")
    return s

def card(s, x, y, w, h, radius=8000, fill=CARD, shadow=True, line=None):
    return s.shape(x, y, w, h, geom="roundRect", fill=fill, line=line, shadow=shadow, radius=radius, name="Card")

def icon_circle(s, cx, cy, d, icon, fill=RED, icon_color="white", pad=0.26):
    s.shape(cx - d / 2, cy - d / 2, d, d, geom="ellipse", fill=fill, name="Icon circle")
    s.image(ICON(icon, icon_color), cx - d / 2 + d * pad, cy - d / 2 + d * pad, d * (1 - 2 * pad), d * (1 - 2 * pad), name=icon)

# ================= 1. COVER =================
s = deck.slide(1, "fade")
t = s.title("WhatsApp Chatbot\nRegistration", x=0.57, y=2.55, w=6.6, h=1.75, size=40)
sub = s.text(0.6, 4.35, 6.4, 0.6, "Member sign-up in one chat — project idea", size=20, color=RED, bold=True, margin=(0, 0, 0, 0))
who = s.text(0.6, 4.95, 6.4, 0.5, "Digital & QA team  ·  [Presenter]  ·  [Date]", size=14, color=GREY, margin=(0, 0, 0, 0))
badge = s.group(0.6, 1.5, 2.9, 0.75, lambda g: (
    g.shape(0.6, 1.5, 2.9, 0.75, geom="roundRect", fill="FFFFFF", radius=50000, shadow=True, name="Badge"),
    g.image(ICON("whatsapp", "green"), 0.72, 1.6, 0.55, 0.55, name="WhatsApp"),
    g.text(1.32, 1.5, 2.1, 0.75, "Powered by WhatsApp\nBusiness Platform", size=11, color=DARK, bold=True, valign="m", margin=(0, 0, 0, 0))), name="WhatsApp badge")
s.animate([(badge, "zoom", 0), (t, "float", 250, 600), (sub, "fade", 700), (who, "fade", 900)], trigger="after")

# ================= 2. AGENDA =================
s = content_slide("Agenda")
items = [("Why now", "Registration today is slow, manual and leaky"),
         ("The idea", "Join as a member inside a WhatsApp chat, in under a minute"),
         ("How it works", "Customer journey, architecture and key features"),
         ("Value", "Benefits for customers, stores and the loyalty programme"),
         ("Plan", "Pilot → rollout roadmap, risks and compliance"),
         ("The ask", "Decision, team and budget to start the pilot")]
ids = []
for i, (h, d) in enumerate(items):
    col, row = i % 2, i // 2
    x, y = 0.54 + col * 6.2, 1.55 + row * 1.55
    def b(g, x=x, y=y, i=i, h=h, d=d):
        card(g, x, y, 5.9, 1.3)
        g.shape(x + 0.25, y + 0.3, 0.7, 0.7, geom="ellipse", fill=RED, name="Number")
        g.text(x + 0.25, y + 0.3, 0.7, 0.7, f"{i + 1:02d}", size=16, color="FFFFFF", bold=True, align="ctr", valign="m", margin=(0, 0, 0, 0))
        g.text(x + 1.15, y + 0.22, 4.5, 0.45, h, size=18, color=DARK, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 1.15, y + 0.68, 4.5, 0.5, d, size=13, color=GREY, margin=(0, 0, 0, 0))
    ids.append(s.group(x, y, 5.9, 1.3, b, name=f"Agenda {i + 1}"))
s.stagger(ids, "float", step=120)

# ================= 3. DIVIDER =================
divider(3, "01", "Why now", "Registration today is slow, manual and leaky")

# ================= 4. PROBLEM =================
s = content_slide("Today's registration loses customers at every step")
stats = [("8 min", "average time to register\nat the counter", "clock"),
         ("40%", "start the web form\nbut never finish it", "warning"),
         ("3 systems", "staff touch for a single\nnew member", "database")]
sids = []
for i, (n, l, ic) in enumerate(stats):
    x = 0.54 + i * 4.12
    def b(g, x=x, n=n, l=l, ic=ic):
        card(g, x, 1.55, 3.9, 2.0)
        g.text(x + 0.3, 1.7, 2.6, 0.95, n, size=40, color=RED, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 0.3, 2.65, 2.9, 0.8, l, size=13, color=GREY, margin=(0, 0, 0, 0))
        icon_circle(g, x + 3.3, 2.15, 0.8, ic, fill=PINK, icon_color="red")
    sids.append(s.group(x, 1.55, 3.9, 2.0, b, name="Stat"))
s.stagger(sids, "zoom", step=200)
pains = [("clipboard", "Paper and web forms ask for 12+ fields before the customer sees any value"),
         ("mobile", "Mobile numbers are typed, not verified — duplicate and dead records follow"),
         ("comments", "Customers already talk to us on WhatsApp; registration lives somewhere else"),
         ("search", "No single view of where sign-ups drop off, so nobody fixes it")]
pids = []
for i, (ic, txt) in enumerate(pains):
    col, row = i % 2, i // 2
    x, y = 0.54 + col * 6.2, 3.85 + row * 1.05
    def b(g, x=x, y=y, ic=ic, txt=txt):
        icon_circle(g, x + 0.4, y + 0.42, 0.7, ic, fill=RED)
        g.text(x + 0.95, y, 4.9, 0.85, txt, size=14, color=DARK, valign="m", margin=(0, 0, 0, 0))
    pids.append(s.group(x, y, 5.9, 0.85, b, name="Pain"))
s.stagger(pids, "float", step=150)
s.text(0.54, 6.05, 8, 0.3, FOOT, size=10, color=GREY, italic=True, margin=(0, 0, 0, 0))

# ================= 5. THE IDEA (phone mock-up) =================
s = content_slide("The idea: join as a member inside a WhatsApp chat")
big = s.text(0.54, 1.55, 7.4, 1.4, [("Register in ", {}), ("under 60 seconds", {"color": RED}), (" — no form, no app, no queue", {})],
             size=28, color=DARK, bold=True, margin=(0, 0, 0, 0), line_spacing=100)
pts = [("whatsapp", "Say hi or scan a QR code at the shelf, receipt or ad"),
       ("mobile", "The number is verified by WhatsApp itself plus a one-time code"),
       ("idcard", "The e-member card and welcome offer arrive in the same chat"),
       ("headset", "A colleague can take over the chat whenever the bot is stuck")]
bids = []
for i, (ic, txt) in enumerate(pts):
    y = 3.15 + i * 0.75
    def b(g, y=y, ic=ic, txt=txt):
        icon_circle(g, 0.9, y + 0.3, 0.6, ic, fill=PINK, icon_color="red", pad=0.24)
        g.text(1.4, y, 6.4, 0.6, txt, size=15, color=DARK, valign="m", margin=(0, 0, 0, 0))
    bids.append(s.group(0.54, y, 7.3, 0.6, b, name="Point"))
s.animate([(big, "float", 0, 600)] + [(b, "float", 300 + i * 150) for i, b in enumerate(bids)], trigger="after")
# phone
PX, PY, PW, PH = 8.75, 1.2, 3.3, 5.15
phone = s.group(PX, PY, PW, PH, lambda g: (
    g.shape(PX, PY, PW, PH, geom="roundRect", fill=DARK, radius=12000, shadow=True, name="Phone"),
    g.shape(PX + 0.13, PY + 0.13, PW - 0.26, PH - 0.26, geom="roundRect", fill=WA_BG, radius=9000, name="Screen"),
    g.shape(PX + 0.13, PY + 0.13, PW - 0.26, 0.62, geom="roundRect", fill=WA_DARK, radius=9000, name="Header"),
    g.shape(PX + 0.13, PY + 0.45, PW - 0.26, 0.3, fill=WA_DARK, name="Header fill"),
    g.image(ICON("whatsapp", "white"), PX + 0.3, PY + 0.28, 0.34, 0.34, name="WA"),
    g.text(PX + 0.72, PY + 0.2, 2.2, 0.5, [("AS Watson Member Bot", {"bold": True, "size": 11}), ("\n", {}), ("online", {"size": 8.5, "color": "CDEFE4"})], size=11, color="FFFFFF", valign="m", margin=(0, 0, 0, 0), line_spacing=95),
    g.shape(PX + 0.13, PY + PH - 0.6, PW - 0.26, 0.47, geom="roundRect", fill="FFFFFF", radius=9000, name="Input bar"),
    g.text(PX + 0.3, PY + PH - 0.58, 2.3, 0.43, "Type a message", size=10, color="9AA0A6", valign="m", margin=(0, 0, 0, 0)),
    g.shape(PX + PW - 0.6, PY + PH - 0.56, 0.38, 0.38, geom="ellipse", fill=WA_GREEN, name="Send"),
), name="Phone")
bubbles = [("bot", "Hi 👋 Welcome to AS Watson! Reply JOIN to become a member in 1 minute."),
           ("me", "JOIN"),
           ("bot", "We'll use this WhatsApp number. Please enter the 6-digit SMS code."),
           ("me", "482913"),
           ("bot", "You're in 🎉 Here is your e-member card — show it at the till.")]
ids = []
y = PY + 0.9
for who, txt in bubbles:
    lines = 1 + (len(txt) - 1) // 38
    h = 0.2 + 0.165 * lines
    w = 2.35 if who == "bot" else min(2.35, 0.4 + 0.085 * len(txt))
    x = PX + 0.25 if who == "bot" else PX + PW - 0.25 - w
    def b(g, x=x, y=y, w=w, h=h, who=who, txt=txt):
        g.shape(x, y, w, h, geom="roundRect", fill="FFFFFF" if who == "bot" else WA_USER, radius=14000, shadow=True, name="Bubble")
        g.text(x, y, w, h, txt, size=9.5, color=DARK, valign="m", margin=(0.1, 0.03, 0.1, 0.03))
    ids.append(s.group(x, y, w, h, b, name="Bubble"))
    y += h + 0.08
cardid = s.group(PX + 0.25, y, 2.35, 0.72, lambda g, y=y: (
    g.shape(PX + 0.25, y, 2.35, 0.72, geom="roundRect", fill=RED, radius=12000, shadow=True, name="Member card"),
    g.image(ICON("qrcode", "white"), PX + 0.38, y + 0.12, 0.48, 0.48, name="QR"),
    g.text(PX + 0.98, y + 0.06, 1.55, 0.6, [("MEMBER CARD", {"bold": True, "size": 9}), ("\n", {}), ("8001 2345 6789", {"size": 9}), ("\n", {}), ("Welcome offer: $20 off", {"size": 8, "color": "FFD6DC"})], size=9, color="FFFFFF", valign="m", margin=(0, 0, 0, 0), line_spacing=95)), name="Member card")
s.animate([(phone, "flyright", 0, 600)], trigger="after")
s.animate([(ids[0], "float", 0, 400)] + [(b, "float", 500 + i * 650, 400) for i, b in enumerate(ids[1:])] + [(cardid, "zoom", 500 + (len(ids) - 1) * 650 + 300, 500)], trigger="click")

# ================= 6. DIVIDER =================
divider(4, "02", "How it works", "Customer journey, architecture and key features")

# ================= 7. JOURNEY =================
s = content_slide("Customer journey: five steps, one chat")
steps = [("qrcode", "Start", "Scan the QR or message the number; the bot greets in the customer's language"),
         ("mobile", "Verify", "WhatsApp number confirmed, 6-digit OTP for a second check"),
         ("clipboard", "Profile", "Name, birthday month, preferred store — via quick-reply buttons, 3 taps"),
         ("shield", "Consent", "PICS / marketing opt-in shown in-chat and recorded with a timestamp"),
         ("idcard", "Welcome", "E-member card with QR, points balance and a welcome offer")]
n = len(steps); w = 2.3; gap = (12.26 - n * w) / (n - 1); cy = 2.55
line = s.line(0.54 + w / 2, cy, 12.8 - w / 2, cy, color=LINE, w=3)
sids = []
for i, (ic, h, d) in enumerate(steps):
    x = 0.54 + i * (w + gap)
    def b(g, x=x, i=i, ic=ic, h=h, d=d):
        icon_circle(g, x + w / 2, cy, 1.05, ic, fill=RED, pad=0.27)
        g.text(x, 3.25, w, 0.4, f"{i + 1}. {h}", size=17, color=DARK, bold=True, align="ctr", margin=(0, 0, 0, 0))
        g.text(x, 3.7, w, 1.5, d, size=12.5, color=GREY, align="ctr", margin=(0, 0, 0, 0))
    sids.append(s.group(x, cy - 0.55, w, 3.3, b, name="Step"))
s.animate([(line, "wipe", 0, 900)] + [(sid, "float", 200 + i * 250) for i, sid in enumerate(sids)], trigger="after")
box = s.group(0.54, 5.35, 12.26, 0.85, lambda g: (
    card(g, 0.54, 5.35, 12.26, 0.85, fill=PINK, shadow=False),
    g.image(ICON("bolt", "red"), 0.8, 5.55, 0.45, 0.45, name="bolt"),
    g.text(1.4, 5.35, 11.2, 0.85, [("Target: ", {"bold": True, "color": RED}), ("under 60 seconds from first message to member card, with no store staff involved. Every step has a fallback: ", {}), ("“Talk to a colleague”", {"bold": True}), (" hands the chat to a human.", {})], size=13.5, color=DARK, valign="m", margin=(0, 0, 0, 0))), name="Target")
s.animate([(box, "float", 0)])

# ================= 8. ARCHITECTURE =================
s = content_slide("Solution architecture")
flow = [("users", "Customer", "WhatsApp app\non any phone"),
        ("whatsapp", "WhatsApp Business\nPlatform", "Meta Cloud API\nverified sender"),
        ("robot", "Chatbot engine", "Flows, NLU, quick replies,\nEnglish and 繁體中文"),
        ("cog", "Integration layer", "REST APIs, queue,\nretry & audit"),
        ("database", "CRM / Loyalty", "Member master,\npoints, e-card")]
bw, bh, by = 2.2, 1.75, 1.75
gap = (12.26 - 5 * bw) / 4
bids, aids = [], []
for i, (ic, h, d) in enumerate(flow):
    x = 0.54 + i * (bw + gap)
    def b(g, x=x, ic=ic, h=h, d=d, i=i):
        card(g, x, by, bw, bh, fill="FFFFFF", line=LINE)
        icon_circle(g, x + bw / 2, by + 0.5, 0.62, ic, fill=RED if i in (1, 2) else DARK, pad=0.25)
        g.text(x + 0.1, by + 0.85, bw - 0.2, 0.45, h, size=12.5, color=DARK, bold=True, align="ctr", margin=(0, 0, 0, 0), line_spacing=90)
        g.text(x + 0.1, by + 1.28, bw - 0.2, 0.45, d, size=10, color=GREY, align="ctr", margin=(0, 0, 0, 0), line_spacing=90)
    bids.append(s.group(x, by, bw, bh, b, name="Box"))
    if i < 4:
        aids.append(s.line(x + bw + 0.05, by + bh / 2, x + bw + gap - 0.05, by + bh / 2, color=RED, w=2, arrow=True))
seq = []
for i, bid in enumerate(bids):
    seq.append((bid, "float", i * 350))
    if i < 4:
        seq.append((aids[i], "wipe", i * 350 + 220, 300))
s.animate(seq, trigger="after")
side = [("sms", "OTP / SMS gateway", "second-factor code"),
        ("filealt", "Consent & audit log", "PICS, opt-in, timestamps"),
        ("chart", "Analytics", "funnel, drop-off, SLA"),
        ("headset", "Live agent handover", "store / CS desk inbox")]
sids2 = []
sw = (12.26 - 3 * 0.3) / 4
for i, (ic, h, d) in enumerate(side):
    x = 0.54 + i * (sw + 0.3)
    def b(g, x=x, ic=ic, h=h, d=d):
        card(g, x, 4.35, sw, 1.0, fill=CARD, shadow=False)
        icon_circle(g, x + 0.5, 4.85, 0.6, ic, fill=PINK, icon_color="red", pad=0.25)
        g.text(x + 0.95, 4.42, sw - 1.05, 0.45, h, size=13, color=DARK, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 0.95, 4.85, sw - 1.05, 0.45, d, size=11, color=GREY, margin=(0, 0, 0, 0))
    sids2.append(s.group(x, 4.35, sw, 1.0, b, name="Side"))
dash = s.line(0.54, 4.1, 12.8, 4.1, color=LINE, w=1, dash="dash")
s.text(0.54, 5.55, 12.2, 0.6, [("Build options: ", {"bold": True}), ("Microsoft Copilot Studio (fits the existing agents work) or Meta’s native flows; both talk to the same integration layer, so the CRM side is built once.", {})], size=12.5, color=GREY, margin=(0, 0, 0, 0))
s.animate([(dash, "wipe", 0, 500)] + [(x, "float", 200 + i * 150) for i, x in enumerate(sids2)])

# ================= 9. FEATURES =================
s = content_slide("Key features of the registration bot")
feats = [("language", "Bilingual by default", "English and 繁體中文 detected from the first message; switch any time"),
         ("shield", "Verified mobile", "WhatsApp number plus SMS OTP — no more typos or duplicate members"),
         ("clipboard", "Quick-reply forms", "Buttons and list pickers instead of typing; 3–4 taps to finish"),
         ("lock", "Consent built in", "PICS and marketing opt-in shown, accepted and logged with a timestamp"),
         ("idcard", "Instant e-card", "Member QR delivered in chat and usable at the till immediately"),
         ("headset", "Human handover", "“Talk to a colleague” routes the chat to the store or CS inbox")]
fids = []
cw, ch = 3.9, 2.1
for i, (ic, h, d) in enumerate(feats):
    col, row = i % 3, i // 3
    x, y = 0.54 + col * (cw + 0.28), 1.6 + row * (ch + 0.3)
    def b(g, x=x, y=y, ic=ic, h=h, d=d):
        card(g, x, y, cw, ch)
        icon_circle(g, x + 0.65, y + 0.6, 0.72, ic, fill=RED, pad=0.26)
        g.text(x + 1.2, y + 0.3, cw - 1.4, 0.6, h, size=16, color=DARK, bold=True, valign="m", margin=(0, 0, 0, 0))
        g.text(x + 0.3, y + 1.1, cw - 0.6, 0.9, d, size=12.5, color=GREY, margin=(0, 0, 0, 0))
    fids.append(s.group(x, y, cw, ch, b, name="Feature"))
s.stagger(fids, "zoom", step=120, dur=400)

# ================= 10. DIVIDER =================
divider(5, "03", "Value & plan", "Benefits, roadmap, risks and the ask")

# ================= 11. BENEFITS =================
s = content_slide("What it changes for customers and stores")
ben = [("< 60 s", "to become a member", "vs. ~8 minutes at the counter", "clock"),
       ("+30%", "sign-up completion", "quick replies instead of a 12-field form", "chart"),
       ("24 / 7", "always open", "registration outside store hours and queues", "store"),
       ("−50%", "cost per sign-up", "no staff time, no paper, fewer bad records", "money")]
bids = []
for i, (n, l, d, ic) in enumerate(ben):
    col, row = i % 2, i // 2
    x, y = 0.54, 1.55 + i * 1.12
    def b(g, x=x, y=y, n=n, l=l, d=d, ic=ic):
        card(g, x, y, 6.4, 0.95, fill="FFFFFF", line=LINE, shadow=False)
        g.text(x + 0.25, y + 0.08, 1.9, 0.8, n, size=28, color=RED, bold=True, valign="m", margin=(0, 0, 0, 0))
        g.text(x + 2.2, y + 0.1, 3.5, 0.4, l, size=15, color=DARK, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 2.2, y + 0.5, 3.6, 0.4, d, size=11.5, color=GREY, margin=(0, 0, 0, 0))
        icon_circle(g, x + 5.95, y + 0.47, 0.55, ic, fill=PINK, icon_color="red", pad=0.25)
    bids.append(s.group(x, y, 6.4, 0.95, b, name="Benefit"))
s.stagger(bids, "flyleft", step=150, dur=450)
kpi = s.group(7.3, 1.55, 5.5, 4.4, lambda g: (
    card(g, 7.3, 1.55, 5.5, 4.4, fill=PINK, shadow=False),
    g.text(7.6, 1.75, 5, 0.5, "KPIs we will track from day one", size=17, color=RED, bold=True, margin=(0, 0, 0, 0)),
    g.text(7.6, 2.35, 5.0, 3.5, ["Registrations per day per store and per channel (QR, ad, organic)",
                                 "Completion rate and the step where customers drop off",
                                 "Median time from first message to member card",
                                 "OTP success rate and duplicate-member rate",
                                 "Handover rate to a human colleague",
                                 "Welcome-offer redemption within 14 days"], size=13.5, color=DARK, bullets=True, space_after=7, margin=(0, 0, 0, 0))), name="KPIs")
s.animate([(kpi, "float", 0)])
s.text(0.54, 6.05, 8, 0.3, FOOT, size=10, color=GREY, italic=True, margin=(0, 0, 0, 0))

# ================= 12. ROADMAP =================
s = content_slide("Roadmap: pilot first, then scale")
phases = [("Discover & design", "4 weeks", ["Journey, PICS wording, bot flows", "WhatsApp Business account & number", "CRM API spec with IT"]),
          ("Pilot", "6 weeks", ["2 stores + 1 online campaign", "QA scripts via the workstation", "Measure the KPIs weekly"]),
          ("Rollout", "8 weeks", ["All stores, QR on receipts & shelves", "Store colleague handover inbox", "Fallback & monitoring runbook"]),
          ("Enhance", "ongoing", ["Points balance, offers, reminders", "Cross-brand sign-up", "Campaign broadcasts (opt-in)"])]
pw = (12.26 - 3 * 0.25) / 4
pids = []
for i, (h, dur, bl) in enumerate(phases):
    x = 0.54 + i * (pw + 0.25)
    chev = s.shape(x, 1.6, pw, 0.85, geom="homePlate" if i == 0 else "chevron", fill=RED if i < 3 else GOLD, name="Phase")
    s.text(x + (0.25 if i == 0 else 0.4), 1.6, pw - 0.6, 0.85, [(f"Phase {i + 1}", {"size": 10.5, "color": "FFE3E7"}), ("\n", {}), (h, {"bold": True, "size": 14})], size=14, color="FFFFFF", valign="m", margin=(0, 0, 0, 0), line_spacing=95)
    def b(g, x=x, dur=dur, bl=bl):
        card(g, x, 2.65, pw, 2.75)
        g.text(x + 0.25, 2.8, pw - 0.5, 0.4, dur, size=13, color=RED, bold=True, margin=(0, 0, 0, 0))
        g.text(x + 0.25, 3.25, pw - 0.45, 2.1, bl, size=12.5, color=DARK, bullets=True, space_after=5, margin=(0, 0, 0, 0))
    pids.append((chev, s.shapes.__len__()))  # placeholder
    gid = s.group(x, 2.65, pw, 2.75, b, name="Phase detail")
    pids[-1] = (chev, gid)
# chevron label text boxes were added before the groups; animate chevrons + labels: find label ids = chev+1
seq = []
for i, (chev, gid) in enumerate(pids):
    seq += [(chev, "wipe", i * 300, 400), (chev + 1, "fade", i * 300 + 150, 300), (gid, "float", i * 300 + 250, 450)]
s.animate(seq, trigger="after")
ms = s.group(0.54, 5.6, 12.26, 0.6, lambda g: (
    g.image(ICON("flag", "red"), 0.6, 5.68, 0.42, 0.42, name="flag"),
    g.text(1.15, 5.6, 11.5, 0.6, [("Go / no-go after the pilot: ", {"bold": True, "color": RED}), ("completion rate ≥ 70 %, median time < 90 s, zero consent gaps in the QA sign-off.", {})], size=13.5, color=DARK, valign="m", margin=(0, 0, 0, 0))), name="Milestone")
s.animate([(ms, "float", 0)])

# ================= 13. RISKS =================
s = content_slide("Risks and how we handle them")
rows = [("lock", "Personal data & consent (PDPO)", "PICS shown before any data is asked; consent text and time stored; data kept in the existing CRM, not in the bot"),
        ("whatsapp", "WhatsApp policy & opt-in", "Customer always messages first; templates approved by Meta; opt-out keyword honoured instantly"),
        ("shield", "OTP abuse / fraud", "Rate limits per number and device, OTP expiry, duplicate check against the member master"),
        ("cloud", "Dependency on the API", "Health checks and a fallback message with the web form link; queue and retry on CRM outages"),
        ("money", "Conversation costs", "Registration fits one service conversation; broadcasts only to opted-in members with a budget cap")]
rids = []
for i, (ic, h, d) in enumerate(rows):
    y = 1.55 + i * 0.92
    def b(g, y=y, ic=ic, h=h, d=d):
        card(g, 0.54, y, 12.26, 0.8, fill="FFFFFF", line=LINE, shadow=False)
        icon_circle(g, 1.0, y + 0.4, 0.56, ic, fill=RED, pad=0.26)
        g.text(1.5, y, 3.6, 0.8, h, size=14.5, color=DARK, bold=True, valign="m", margin=(0, 0, 0, 0))
        g.image(ICON("arrow", "grey"), 5.1, y + 0.27, 0.26, 0.26, name="arrow")
        g.text(5.5, y, 7.1, 0.8, d, size=12.5, color=GREY, valign="m", margin=(0, 0, 0, 0))
    rids.append(s.group(0.54, y, 12.26, 0.8, b, name="Risk"))
s.stagger(rids, "flyleft", step=150, dur=450)
s.text(0.54, 6.18, 12, 0.3, "QA sign-off covers every consent path, OTP edge case and fallback before the pilot opens to customers.", size=11, color=GREY, italic=True, margin=(0, 0, 0, 0))

# ================= 14. THE ASK =================
s = content_slide("What we need to start the pilot")
asks = [("check", "Decision", "Approve a 6-week pilot in 2 stores and one online campaign", "by end of this month"),
        ("users", "Team", "Product owner, bot developer, QA (workstation + scripts), CRM integration engineer", "~2.5 FTE for 10 weeks"),
        ("money", "Budget", "WhatsApp Business number & conversation fees, bot platform licence, SMS OTP", "pilot budget to be confirmed")]
aids = []
for i, (ic, h, d, t) in enumerate(asks):
    x = 0.54 + i * 4.12
    def b(g, x=x, ic=ic, h=h, d=d, t=t):
        card(g, x, 1.6, 3.9, 3.5)
        icon_circle(g, x + 0.75, 2.3, 0.95, ic, fill=RED, pad=0.27)
        g.text(x + 1.45, 2.0, 2.3, 0.6, h, size=22, color=DARK, bold=True, valign="m", margin=(0, 0, 0, 0))
        g.text(x + 0.3, 3.0, 3.3, 1.3, d, size=14, color=DARK, margin=(0, 0, 0, 0))
        g.text(x + 0.3, 4.45, 3.3, 0.5, t, size=12.5, color=RED, bold=True, margin=(0, 0, 0, 0))
    aids.append(s.group(x, 1.6, 3.9, 3.5, b, name="Ask"))
s.stagger(aids, "zoom", step=200)
cta = s.group(0.54, 5.35, 12.26, 0.85, lambda g: (
    card(g, 0.54, 5.35, 12.26, 0.85, fill=RED, shadow=True),
    g.image(ICON("whatsapp", "white"), 0.85, 5.52, 0.5, 0.5, name="wa"),
    g.text(1.55, 5.35, 11.0, 0.85, [("Next step: ", {"bold": True}), ("a 30-minute working session to pick the pilot stores and the bot platform — then we can show the first flow in two weeks.", {})], size=14.5, color="FFFFFF", valign="m", margin=(0, 0, 0, 0))), name="CTA")
s.animate([(cta, "float", 0)])

# ================= 15. THANK YOU =================
s = deck.slide(1, "fade")
t = s.title("Thank you", x=0.57, y=2.75, w=6.0, h=1.1, size=40)
q = s.text(0.6, 3.9, 6.4, 0.6, "Questions & discussion", size=20, color=RED, bold=True, margin=(0, 0, 0, 0))
c = s.text(0.6, 4.55, 6.4, 0.5, "[Presenter name]  ·  [email]  ·  [team]", size=14, color=GREY, margin=(0, 0, 0, 0))
s.animate([(t, "float", 0, 600), (q, "fade", 400), (c, "fade", 650)], trigger="after")

deck.save()
print("slides:", len(deck.slides))
