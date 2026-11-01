"""Tiny OOXML slide builder on top of an unpacked template: shapes,
pictures, groups, entrance animations and transitions."""
import os, re, shutil, html
from pathlib import Path

EMU = 914400
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
E = lambda v: int(round(v * EMU))
esc = lambda s: html.escape(str(s), quote=False)


class Deck:
    def __init__(self, template_dir, build_dir):
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        shutil.copytree(template_dir, build_dir)
        self.dir = Path(build_dir)
        self.slides = []          # Slide objects in order
        self.media_n = max([int(m) for m in re.findall(r'image(\d+)\.', " ".join(os.listdir(self.dir / "ppt/media")))] + [0])
        self.media_cache = {}
        # drop the template's own slides from the list (clean.py removes the files)
        pres = (self.dir / "ppt/presentation.xml").read_text(encoding="utf-8")
        self._old_sld_ids = re.findall(r'<p:sldId [^>]*/>', pres)

    def add_media(self, path):
        path = str(path)
        if path in self.media_cache:
            return self.media_cache[path]
        self.media_n += 1
        ext = Path(path).suffix.lower().lstrip(".")
        name = f"image{self.media_n}.{ext}"
        shutil.copy(path, self.dir / "ppt/media" / name)
        self.media_cache[path] = name
        return name

    def slide(self, layout, transition="fade"):
        s = Slide(self, len(self.slides) + 1, layout, transition)
        self.slides.append(s)
        return s

    def save(self):
        rels_path = self.dir / "ppt/_rels/presentation.xml.rels"
        rels = rels_path.read_text(encoding="utf-8")
        pres_path = self.dir / "ppt/presentation.xml"
        pres = pres_path.read_text(encoding="utf-8")
        # remove old slide rels + ids
        for sid in self._old_sld_ids:
            rid = re.search(r'r:id="([^"]+)"', sid).group(1)
            rels = re.sub(rf'<Relationship Id="{rid}"[^>]*/>', "", rels)
        next_rid = max(int(x) for x in re.findall(r'Id="rId(\d+)"', rels)) + 1
        ids, new_rels = [], []
        for i, s in enumerate(self.slides):
            n = 100 + i
            fname = f"slide{n}.xml"
            (self.dir / "ppt/slides" / fname).write_text(s.xml(), encoding="utf-8")
            (self.dir / "ppt/slides/_rels" / f"{fname}.rels").write_text(s.rels_xml(), encoding="utf-8")
            rid = f"rId{next_rid}"; next_rid += 1
            new_rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/{fname}"/>')
            ids.append(f'<p:sldId id="{1000 + i}" r:id="{rid}"/>')
        rels = rels.replace("</Relationships>", "".join(new_rels) + "</Relationships>")
        rels_path.write_text(rels, encoding="utf-8")
        pres = re.sub(r'<p:sldIdLst>.*?</p:sldIdLst>', "<p:sldIdLst>" + "".join(ids) + "</p:sldIdLst>", pres, flags=re.S)
        pres_path.write_text(pres, encoding="utf-8")
        ct_path = self.dir / "[Content_Types].xml"
        ct = ct_path.read_text(encoding="utf-8")
        ct = re.sub(r'<Override PartName="/ppt/slides/slide\d+\.xml"[^>]*/>', "", ct)
        ct = ct.replace("</Types>", "".join(
            f'<Override PartName="/ppt/slides/slide{100 + i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            for i in range(len(self.slides))) + "</Types>")
        ct_path.write_text(ct, encoding="utf-8")


# ---------- effects ----------

def _set_visible(cid, spid):
    return (f'<p:set><p:cBhvr><p:cTn id="{cid}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>'
            f'</p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>')

def _anim(cid, spid, attr, frm, to, dur):
    return (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="{cid}" dur="{dur}" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:tavLst><p:tav tm="0"><p:val><p:strVal val="{frm}"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="{to}"/></p:val></p:tav></p:tavLst></p:anim>')

def _fx(cid, spid, filt, dur):
    return (f'<p:animEffect transition="in" filter="{filt}"><p:cBhvr><p:cTn id="{cid}" dur="{dur}"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>')

def _rot(cid, spid, by, dur):
    return (f'<p:animRot by="{by}"><p:cBhvr><p:cTn id="{cid}" dur="{dur}" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
            f'<p:attrNameLst><p:attrName>r</p:attrName></p:attrNameLst></p:cBhvr></p:animRot>')

def _scale(cid, spid, frm, to, dur, autorev=False):
    ar = ' autoRev="1"' if autorev else ""
    return (f'<p:animScale><p:cBhvr><p:cTn id="{cid}" dur="{dur}" fill="hold"{ar}/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr>'
            f'<p:from x="{frm}" y="{frm}"/><p:to x="{to}" y="{to}"/></p:animScale>')

def _motion(cid, spid, path, dur):
    return (f'<p:animMotion origin="layout" path="{path}" pathEditMode="relative" ptsTypes=""><p:cBhvr><p:cTn id="{cid}" dur="{dur}" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>ppt_x</p:attrName><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr></p:animMotion>')

EFFECTS = {
    # name: (presetID, presetSubtype, builder(cid_iter, spid, dur) -> xml[, presetClass, extra cTn attrs])
    "fade":  (10, 0,  lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "fade", d)),
    "wheel": (21, 1,  lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "wheel(1)", d)),
    "split": (16, 16, lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "barn(inVertical)", d)),
    "spinin": (53, 16, lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "fade", d) + _scale(next(c), s, 10000, 100000, d) + _rot(next(c), s, 21600000, d)),
    # emphasis (object already visible)
    "spin":     (8, 0, lambda c, s, d: _rot(next(c), s, 21600000, d), "emph", ""),
    "spinloop": (8, 0, lambda c, s, d: _rot(next(c), s, 21600000, d), "emph", ' repeatCount="indefinite"'),
    "spinback": (8, 0, lambda c, s, d: _rot(next(c), s, -21600000, d), "emph", ' repeatCount="indefinite"'),
    "pulse":    (26, 0, lambda c, s, d: _scale(next(c), s, 100000, 108000, d, autorev=True), "emph", ' repeatCount="indefinite"'),
    "grow":     (6, 0, lambda c, s, d: _scale(next(c), s, 100000, 115000, d), "emph", ""),
    # motion path (relative to slide size)
    "slideright": (0, 0, lambda c, s, d: _motion(next(c), s, "M 0 0 L 0.18 0 E", d), "path", ""),
    "bounce":     (0, 0, lambda c, s, d: _motion(next(c), s, "M 0 0 C 0.02 -0.08 0.06 -0.08 0.08 0 C 0.09 -0.04 0.11 -0.04 0.12 0 E", d), "path", ""),
    "float": (42, 4,  lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "fade", d) + _anim(next(c), s, "ppt_y", "#ppt_y+0.06", "#ppt_y", d)),
    "wipe":  (22, 8,  lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "wipe(left)", d)),
    "wipedown": (22, 4, lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "wipe(down)", d)),
    "zoom":  (53, 16, lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "fade", d) +
              f'<p:animScale><p:cBhvr><p:cTn id="{next(c)}" dur="{d}" fill="hold"/><p:tgtEl><p:spTgt spid="{s}"/></p:tgtEl></p:cBhvr><p:from x="30000" y="30000"/><p:to x="100000" y="100000"/></p:animScale>'),
    "flyleft":  (2, 8, lambda c, s, d: _set_visible(next(c), s) + _anim(next(c), s, "ppt_x", "0-#ppt_w/2", "#ppt_x", d) + _anim(next(c), s, "ppt_y", "#ppt_y", "#ppt_y", d)),
    "flyright": (2, 2, lambda c, s, d: _set_visible(next(c), s) + _anim(next(c), s, "ppt_x", "1+#ppt_w/2", "#ppt_x", d) + _anim(next(c), s, "ppt_y", "#ppt_y", "#ppt_y", d)),
    "flyup":    (2, 4, lambda c, s, d: _set_visible(next(c), s) + _anim(next(c), s, "ppt_x", "#ppt_x", "#ppt_x", d) + _anim(next(c), s, "ppt_y", "1+#ppt_h/2", "#ppt_y", d)),
    "rise":     (42, 4, lambda c, s, d: _set_visible(next(c), s) + _fx(next(c), s, "fade", d) + _anim(next(c), s, "ppt_y", "#ppt_y+0.12", "#ppt_y", d)),
}


class Slide:
    def __init__(self, deck, n, layout, transition):
        self.deck, self.n, self.layout, self.transition = deck, n, layout, transition
        self.shapes = []       # xml strings
        self.rels = [('rId1', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout', f'../slideLayouts/slideLayout{layout}.xml')]
        self.next_id = 2
        self.groups = []       # animation click groups: list of list of (spid, effect, delay_ms, dur_ms)
        self.anim_ids = []
        self.notes = ""

    # ----- ids / rels -----
    def _id(self):
        i = self.next_id; self.next_id += 1; return i

    def _img_rel(self, path):
        name = self.deck.add_media(path)
        rid = f"rId{len(self.rels) + 1}"
        self.rels.append((rid, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image', f'../media/{name}'))
        return rid

    # ----- helpers -----
    @staticmethod
    def _fill(color, transparency=0):
        if color is None:
            return "<a:noFill/>"
        alpha = f'<a:alpha val="{int((100 - transparency) * 1000)}"/>' if transparency else ""
        return f'<a:solidFill><a:srgbClr val="{color}">{alpha}</a:srgbClr></a:solidFill>'

    @staticmethod
    def _line(color, w=0.75, dash=None):
        if color is None:
            return '<a:ln><a:noFill/></a:ln>'
        d = f'<a:prstDash val="{dash}"/>' if dash else ""
        return f'<a:ln w="{int(w * 12700)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{d}</a:ln>'

    @staticmethod
    def _shadow(on):
        if not on:
            return ""
        return ('<a:effectLst><a:outerShdw blurRad="152400" dist="38100" dir="5400000" algn="t" rotWithShape="0">'
                '<a:srgbClr val="000000"><a:alpha val="16000"/></a:srgbClr></a:outerShdw></a:effectLst>')

    def _runs(self, text, size, color, bold=False, italic=False, font=None):
        """text: str or list of (str, {size,color,bold,italic,font,link}) runs."""
        if isinstance(text, str):
            text = [(text, {})]
        out = []
        for t, o in text:
            sz = o.get("size", size); col = o.get("color", color)
            b = ' b="1"' if o.get("bold", bold) else ''
            i = ' i="1"' if o.get("italic", italic) else ''
            f = o.get("font", font)
            latin = f'<a:latin typeface="{f}"/>' if f else ""
            fill = f'<a:solidFill><a:srgbClr val="{col}"/></a:solidFill>' if col else ""
            if t == "\n":
                out.append("<a:br/>"); continue
            link = ""
            if o.get("link"):
                rid = f"rId{len(self.rels) + 1}"
                self.rels.append((rid, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide', f'slide{99 + int(o["link"])}.xml'))
                link = f'<a:hlinkClick r:id="{rid}" action="ppaction://hlinksldjump"/>'
            rpr = f'<a:rPr lang="en-US" sz="{int(sz * 100)}"{b}{i} dirty="0">{fill}{latin}{link}</a:rPr>'
            parts = str(t).split("\n")
            for k, part in enumerate(parts):
                if k:
                    out.append(f'<a:br>{rpr}</a:br>')
                if part:
                    out.append(f'<a:r>{rpr}<a:t>{esc(part)}</a:t></a:r>')
        return "".join(out)

    def _paras(self, paras, size, color, bold, italic, align, font, bullets, space_after, line_spacing):
        out = []
        for ptxt in paras:
            bu = ""
            if bullets:
                bu = '<a:buFont typeface="Arial"/><a:buChar char="&#8226;"/>'
                marl = ' marL="228600" indent="-228600"'
            else:
                bu = "<a:buNone/>"; marl = ""
            sa = f'<a:spcAft><a:spcPts val="{int(space_after * 100)}"/></a:spcAft>' if space_after else ""
            ls = f'<a:lnSpc><a:spcPct val="{int(line_spacing * 1000)}"/></a:lnSpc>' if line_spacing else ""
            out.append(f'<a:p><a:pPr{marl} algn="{align}">{ls}{sa}{bu}</a:pPr>{self._runs(ptxt, size, color, bold, italic, font)}</a:p>')
        return "".join(out)

    # ----- shapes -----
    def text(self, x, y, w, h, paras, size=14, color="1F1F1F", bold=False, italic=False, align="l",
             valign="t", font=None, bullets=False, space_after=0, line_spacing=0, name="Text",
             fill=None, line=None, shadow=False, geom="rect", radius=None, margin=(0.05, 0.03, 0.05, 0.03),
             autofit=False, anchor_ctr=False, rot=0):
        """paras: str | list[str | list[(text, opts)]]"""
        if isinstance(paras, (str, list)) and (isinstance(paras, str) or (paras and isinstance(paras[0], tuple))):
            paras = [paras]
        sid = self._id()
        adj = f'<a:avLst><a:gd name="adj" fmla="val {int(radius)}"/></a:avLst>' if radius is not None else "<a:avLst/>"
        l, t, r, b = [int(m * EMU) for m in margin]
        va = {"t": "t", "m": "ctr", "b": "b"}[valign]
        fit = "<a:normAutofit/>" if autofit else ""
        rotation = f' rot="{int(rot * 60000)}"' if rot else ""
        actr = ' anchorCtr="1"' if anchor_ctr else ""
        body = self._paras(paras, size, color, bold, italic, align, font, bullets, space_after, line_spacing)
        xml = (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)} {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
               f'<p:spPr><a:xfrm{rotation}><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm>'
               f'<a:prstGeom prst="{geom}">{adj}</a:prstGeom>{self._fill(fill)}{self._line(line)}{self._shadow(shadow)}</p:spPr>'
               f'<p:txBody><a:bodyPr wrap="square" lIns="{l}" tIns="{t}" rIns="{r}" bIns="{b}" rtlCol="0" anchor="{va}"{actr}>{fit}</a:bodyPr><a:lstStyle/>'
               f'{body}</p:txBody></p:sp>')
        self.shapes.append(xml)
        return sid

    def shape(self, x, y, w, h, geom="rect", fill="E31836", line=None, line_w=0.75, shadow=False, radius=None, name="Shape", rot=0, transparency=0, dash=None, link=None, adj=None):
        sid = self._id()
        hl = ""
        if link:
            rid = f"rId{len(self.rels) + 1}"
            self.rels.append((rid, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide', f'slide{99 + int(link)}.xml'))
            hl = f'<a:hlinkClick r:id="{rid}" action="ppaction://hlinksldjump"/>'
        if adj is not None:
            adjx = "<a:avLst>" + "".join(f'<a:gd name="{k}" fmla="val {int(v)}"/>' for k, v in adj.items()) + "</a:avLst>"
        else:
            adjx = f'<a:avLst><a:gd name="adj" fmla="val {int(radius)}"/></a:avLst>' if radius is not None else "<a:avLst/>"
        adj = adjx
        rotation = f' rot="{int(rot * 60000)}"' if rot else ""
        xml = (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)} {sid}">{hl}</p:cNvPr><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
               f'<p:spPr><a:xfrm{rotation}><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm>'
               f'<a:prstGeom prst="{geom}">{adj}</a:prstGeom>{self._fill(fill, transparency)}{self._line(line, line_w, dash)}{self._shadow(shadow)}</p:spPr>'
               f'<p:txBody><a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="ctr"/><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
        self.shapes.append(xml)
        return sid

    def gradient_rect(self, x, y, w, h, c1, c2, angle=90, name="Gradient", geom="rect", radius=None, transparency=0):
        """Two-stop linear gradient fill (not possible in pptxgenjs)."""
        sid = self._id()
        adj = f'<a:avLst><a:gd name="adj" fmla="val {int(radius)}"/></a:avLst>' if radius is not None else "<a:avLst/>"
        a = f'<a:alpha val="{int((100 - transparency) * 1000)}"/>' if transparency else ""
        xml = (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)} {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
               f'<p:spPr><a:xfrm><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm><a:prstGeom prst="{geom}">{adj}</a:prstGeom>'
               f'<a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:srgbClr val="{c1}">{a}</a:srgbClr></a:gs><a:gs pos="100000"><a:srgbClr val="{c2}">{a}</a:srgbClr></a:gs></a:gsLst>'
               f'<a:lin ang="{int(angle * 60000)}" scaled="0"/></a:gradFill><a:ln><a:noFill/></a:ln></p:spPr>'
               f'<p:txBody><a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="ctr"/><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
        self.shapes.append(xml)
        return sid

    def line(self, x1, y1, x2, y2, color="E31836", w=1.5, arrow=False, dash=None, name="Connector"):
        sid = self._id()
        x, y = min(x1, x2), min(y1, y2)
        cw, ch = abs(x2 - x1), abs(y2 - y1)
        flipH = ' flipH="1"' if x2 < x1 else ""
        flipV = ' flipV="1"' if y2 < y1 else ""
        head = '<a:tailEnd type="triangle" w="med" len="med"/>' if arrow else ""
        d = f'<a:prstDash val="{dash}"/>' if dash else ""
        xml = (f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{sid}" name="{name} {sid}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
               f'<p:spPr><a:xfrm{flipH}{flipV}><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(cw)}" cy="{E(ch)}"/></a:xfrm>'
               f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="{int(w * 12700)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{d}{head}</a:ln></p:spPr></p:cxnSp>')
        self.shapes.append(xml)
        return sid

    def image(self, path, x, y, w, h, name="Picture", rot=0, transparency=0):
        sid = self._id()
        rid = self._img_rel(path)
        rotation = f' rot="{int(rot * 60000)}"' if rot else ""
        alpha = f'<a:alphaModFix amt="{int((100 - transparency) * 1000)}"/>' if transparency else ""
        xml = (f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{esc(name)} {sid}" descr="{esc(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
               f'<p:blipFill><a:blip r:embed="{rid}">{alpha}</a:blip><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
               f'<p:spPr><a:xfrm{rotation}><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
        self.shapes.append(xml)
        return sid

    def title(self, text, x=None, y=None, w=None, h=None, size=None, color=None):
        """The layout's title placeholder, optionally repositioned."""
        sid = self._id()
        sppr = "<p:spPr/>" if x is None else f'<p:spPr><a:xfrm><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm></p:spPr>'
        szattr = f' sz="{int(size * 100)}"' if size else ""
        rpr = f'<a:rPr lang="en-US"{szattr} dirty="0">{self._fill(color) if color else ""}</a:rPr>'
        xml = (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Title {sid}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
               f'{sppr}<p:txBody><a:bodyPr><a:normAutofit/></a:bodyPr><a:lstStyle/><a:p>{"".join((f"<a:br>{rpr}</a:br>" if k else "") + f"<a:r>{rpr}<a:t>{esc(part)}</a:t></a:r>" for k, part in enumerate(str(text).split(chr(10))))}</a:p></p:txBody></p:sp>')
        self.shapes.append(xml)
        return sid

    def group(self, x, y, w, h, build, name="Group"):
        """build(slide) adds child shapes (absolute coordinates); they are
        wrapped into one group so they animate as a unit."""
        start = len(self.shapes)
        gid = self._id()
        build(self)
        children = self.shapes[start:]
        del self.shapes[start:]
        xml = (f'<p:grpSp><p:nvGrpSpPr><p:cNvPr id="{gid}" name="{esc(name)} {gid}"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
               f'<p:grpSpPr><a:xfrm><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/><a:chOff x="{E(x)}" y="{E(y)}"/><a:chExt cx="{E(w)}" cy="{E(h)}"/></a:xfrm></p:grpSpPr>'
               + "".join(children) + '</p:grpSp>')
        self.shapes.append(xml)
        return gid

    # ----- animation -----
    def animate(self, items, trigger="click"):
        """items: [(spid, effect, delay_ms[, dur_ms])] — one click (or
        'after' previous) group; the first item starts the group."""
        norm = []
        for it in items:
            spid, eff, delay = it[0], it[1], it[2] if len(it) > 2 else 0
            dur = it[3] if len(it) > 3 else 500
            norm.append((spid, eff, delay, dur))
        self.groups.append((trigger, norm))

    def stagger(self, spids, effect="float", step=150, trigger="click", dur=500, start=0):
        self.animate([(s, effect, start + i * step, dur) for i, s in enumerate(spids)], trigger)

    def _timing(self):
        if not self.groups:
            return ""
        cid = iter(range(3, 100000))
        groups_xml = []
        build_ids = []
        for trigger, items in self.groups:
            outer = next(cid); inner = next(cid)
            effs = []
            for k, (spid, eff, delay, dur) in enumerate(items):
                ent = EFFECTS[eff]
                pid, psub, builder = ent[0], ent[1], ent[2]
                pclass = ent[3] if len(ent) > 3 else "entr"
                extra = ent[4] if len(ent) > 4 else ""
                node = "clickEffect" if (k == 0 and trigger == "click") else ("afterEffect" if (k == 0) else "withEffect")
                eid = next(cid)
                effs.append(f'<p:par><p:cTn id="{eid}" presetID="{pid}" presetClass="{pclass}" presetSubtype="{psub}" fill="hold" grpId="0" nodeType="{node}"{extra}>'
                            f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>{builder(cid, spid, dur)}</p:childTnLst></p:cTn></p:par>')
                build_ids.append(spid)
            outer_delay = "indefinite" if trigger == "click" else "0"
            groups_xml.append(f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst><p:cond delay="{outer_delay}"/></p:stCondLst><p:childTnLst>'
                              f'<p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{"".join(effs)}</p:childTnLst></p:cTn></p:par>'
                              f'</p:childTnLst></p:cTn></p:par>')
        bld = "".join(f'<p:bldP spid="{s}" grpId="0" animBg="1"/>' for s in dict.fromkeys(build_ids))
        return ('<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
                '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
                + "".join(groups_xml) +
                '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
                '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
                f'</p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>{bld}</p:bldLst></p:timing>')

    def _transition(self):
        t = self.transition
        if not t:
            return ""
        inner = {"fade": "<p:fade/>", "push": '<p:push dir="l"/>', "wipe": '<p:wipe dir="r"/>', "cover": '<p:cover dir="l"/>', "split": '<p:split orient="horz" dir="out"/>'}[t]
        return f'<p:transition spd="med">{inner}</p:transition>'

    def xml(self):
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                f'<p:sld {NS}><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
                + "".join(self.shapes) +
                '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>'
                + self._transition() + self._timing() + '</p:sld>')

    def rels_xml(self):
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + "".join(f'<Relationship Id="{i}" Type="{t}" Target="{g}"/>' for i, t, g in self.rels) + '</Relationships>')
