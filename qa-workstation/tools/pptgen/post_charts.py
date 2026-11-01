"""Add native charts + a styled table with python-pptx (slide numbers from the build)."""
import sys
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

path, chart_no, table_no = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
RED, PURPLE, BLUE, GOLD, DARK, GREY, LINE, PINK = "E31836", "A27EC6", "01C2ED", "C9A04B", "1F1F1F", "5F6062", "E3E3E6", "FCEEF0"
rgb = lambda h: RGBColor.from_string(h)
prs = Presentation(path)

def quiet(chart, title):
    chart.has_title = True
    chart.chart_title.text_frame.text = title
    p = chart.chart_title.text_frame.paragraphs[0]
    p.runs[0].font.size = Pt(12); p.runs[0].font.bold = True; p.runs[0].font.color.rgb = rgb(DARK)
    chart.font.size = Pt(10); chart.font.color.rgb = rgb(GREY)
    va = chart.value_axis; va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(LINE); va.major_gridlines.format.line.width = Pt(0.75)
    va.format.line.fill.background(); va.tick_labels.font.size = Pt(10); va.tick_labels.font.color.rgb = rgb(GREY)
    ca = chart.category_axis; ca.has_major_gridlines = False; ca.format.line.color.rgb = rgb(LINE)
    ca.tick_labels.font.size = Pt(10); ca.tick_labels.font.color.rgb = rgb(GREY)

# ---- charts
s = prs.slides[chart_no - 1]
cd = CategoryChartData(); cd.categories = ["Q1", "Q2", "Q3", "Q4"]
cd.add_series("This year", (42, 55, 61, 78)); cd.add_series("Last year", (35, 41, 48, 52))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.54), Inches(1.95), Inches(5.9), Inches(3.95), cd)
ch = gf.chart; quiet(ch, "Series by quarter (replace in Edit Data)")
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(10)
pl = ch.plots[0]; pl.gap_width = 80; pl.overlap = -10; pl.has_data_labels = True
pl.data_labels.font.size = Pt(9); pl.data_labels.font.color.rgb = rgb(GREY); pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
for ser, col in zip(pl.series, (RED, LINE)):
    ser.format.fill.solid(); ser.format.fill.fore_color.rgb = rgb(col)
gf.name = "Column chart"

cd2 = CategoryChartData(); cd2.categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
cd2.add_series("Metric A", (12, 18, 15, 24, 30, 36)); cd2.add_series("Metric B", (8, 9, 14, 13, 19, 22))
gf2 = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(6.89), Inches(1.95), Inches(5.9), Inches(3.95), cd2)
ch2 = gf2.chart; quiet(ch2, "Trend by month (replace in Edit Data)")
ch2.has_legend = True; ch2.legend.position = XL_LEGEND_POSITION.BOTTOM; ch2.legend.include_in_layout = False; ch2.legend.font.size = Pt(10)
for ser, col in zip(ch2.plots[0].series, (RED, PURPLE)):
    ser.format.line.color.rgb = rgb(col); ser.format.line.width = Pt(2.5); ser.smooth = True
    ser.marker.format.fill.solid(); ser.marker.format.fill.fore_color.rgb = rgb(col); ser.marker.format.line.color.rgb = rgb(col)
gf2.name = "Line chart"

# ---- table
s = prs.slides[table_no - 1]
rows = [["Item", "Owner", "Status", "Q1", "Q2", "Q3", "Total"],
        ["Line item one", "Team A", "On track", "120", "135", "150", "405"],
        ["Line item two", "Team B", "At risk", "80", "70", "95", "245"],
        ["Line item three", "Team A", "Done", "60", "60", "60", "180"],
        ["Line item four", "Team C", "On track", "40", "55", "70", "165"],
        ["Total", "", "", "300", "320", "375", "995"]]
gt = s.shapes.add_table(len(rows), len(rows[0]), Inches(0.54), Inches(1.6), Inches(12.26), Inches(0.5) * len(rows))
tbl = gt.table; gt.name = "Styled table"
widths = [3.3, 1.8, 1.7, 1.3, 1.3, 1.3, 1.56]
for i, w in enumerate(widths):
    tbl.columns[i].width = Inches(w)
for r, row in enumerate(rows):
    tbl.rows[r].height = Inches(0.5)
    for c, val in enumerate(row):
        cell = tbl.cell(r, c); cell.text = val
        p = cell.text_frame.paragraphs[0]; run = p.runs[0] if p.runs else p.add_run()
        run.font.size = Pt(12); run.font.color.rgb = rgb(DARK)
        cell.margin_left = cell.margin_right = Inches(0.12)
        if c >= 3:
            from pptx.enum.text import PP_ALIGN
            p.alignment = PP_ALIGN.RIGHT
        cell.fill.solid()
        if r == 0:
            cell.fill.fore_color.rgb = rgb(RED); run.font.color.rgb = rgb("FFFFFF"); run.font.bold = True
        elif r == len(rows) - 1:
            cell.fill.fore_color.rgb = rgb(PINK); run.font.bold = True; run.font.color.rgb = rgb(RED)
        else:
            cell.fill.fore_color.rgb = rgb("FFFFFF" if r % 2 else "F6F6F7")
        if r not in (0, len(rows) - 1) and c == 2:
            run.font.bold = True
            run.font.color.rgb = rgb({"On track": "1E8E3E", "At risk": "D97706", "Done": GREY}.get(val, DARK))
# drop the default table style banding flags so our fills win
tblPr = tbl._tbl.tblPr
tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
prs.save(path)
print("charts + table added")
