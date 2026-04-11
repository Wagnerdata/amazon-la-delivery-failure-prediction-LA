"""
patch_genai_section.py — Replace the GenAI Usage section in 07_final_report.docx.

The section heading ("3. Generative AI Usage") is kept in place.
All body paragraphs belonging to that section (currently paragraphs
66–76) are removed and replaced with the corrected text.
"""

from pathlib import Path
from copy import deepcopy
import lxml.etree as etree

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOC_PATH = Path(__file__).parent.parent / "deliverables" / "07_final_report.docx"

DARK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x55, 0x55, 0x55)
NAVY = RGBColor(0x2C, 0x3E, 0x50)


def make_para(doc, text, bold=False, italic=False, font_size=11,
              color=None, space_before=0, space_after=8, align=None):
    """Build a new paragraph object without inserting it anywhere yet."""
    para = OxmlElement("w:p")
    pPr  = OxmlElement("w:pPr")

    # Spacing
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), str(int(space_before * 20)))
    spacing.set(qn("w:after"),  str(int(space_after  * 20)))
    pPr.append(spacing)

    # Alignment
    if align == "center":
        jc = OxmlElement("w:jc")
        jc.set(qn("w:val"), "center")
        pPr.append(jc)

    para.append(pPr)

    # Run
    r   = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(font_size * 2))
    rPr.append(sz)

    sz_cs = OxmlElement("w:szCs")
    sz_cs.set(qn("w:val"), str(font_size * 2))
    rPr.append(sz_cs)

    if bold:
        b = OxmlElement("w:b"); rPr.append(b)
    if italic:
        i = OxmlElement("w:i"); rPr.append(i)
    if color:
        clr = OxmlElement("w:color")
        clr.set(qn("w:val"), f"{color[0]:02X}{color[1]:02X}{color[2]:02X}")
        rPr.append(clr)

    r.append(rPr)
    t = OxmlElement("w:t")
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    r.append(t)
    para.append(r)
    return para


def make_bullet(doc, text, font_size=11):
    """Return an XML paragraph element styled as List Bullet."""
    para = OxmlElement("w:p")
    pPr  = OxmlElement("w:pPr")

    # Apply List Bullet style
    pStyle = OxmlElement("w:pStyle")
    pStyle.set(qn("w:val"), "ListBullet")
    pPr.append(pStyle)

    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "720")
    pPr.append(ind)

    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:after"), "80")
    pPr.append(spacing)

    para.append(pPr)

    r   = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    sz  = OxmlElement("w:sz"); sz.set(qn("w:val"), str(font_size * 2))
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement("w:t")
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    r.append(t)
    para.append(r)
    return para


# ── Load document ──────────────────────────────────────────────────────────────
doc  = Document(str(DOC_PATH))
body = doc.element.body
all_paras = body.findall(qn("w:p"))

# ── Locate section boundaries ─────────────────────────────────────────────────
# Find "3. Generative AI Usage" heading paragraph
heading_idx = None
end_idx     = None   # last para belonging to this section (inclusive)

for i, p in enumerate(all_paras):
    text = "".join(r.text or "" for r in p.findall(".//" + qn("w:t")))
    if "3. Generative AI Usage" in text:
        heading_idx = i
    if heading_idx is not None and i > heading_idx:
        if "4. Challenges" in text:
            end_idx = i - 1   # stop just before section 4
            break

if heading_idx is None:
    raise RuntimeError("Could not find '3. Generative AI Usage' in the document.")

print(f"Section heading paragraph index : {heading_idx}")
print(f"Last paragraph in section       : {end_idx}")
print(f"Paragraphs to replace           : {heading_idx + 1} → {end_idx}")

# ── Remove old body paragraphs (66 → end_idx) ─────────────────────────────────
to_remove = all_paras[heading_idx + 1 : end_idx + 1]
for p in to_remove:
    body.remove(p)

print(f"Removed {len(to_remove)} old paragraphs.")

# ── Build replacement paragraphs ──────────────────────────────────────────────
new_paras = []

# Intro paragraph
new_paras.append(make_para(
    doc,
    "This project has two distinct layers of development.",
    space_before=6, space_after=8,
))

# First body paragraph
new_paras.append(make_para(
    doc,
    "The technical system \u2014 including the Random Forest classifier, CrewAI agent "
    "architecture, REST API, and data pipeline \u2014 was developed independently starting "
    "in October 2025, originally using synthetic delivery data. The system was designed "
    "from scratch to predict last-mile delivery failure before a package leaves the "
    "fulfillment center.",
    space_before=0, space_after=8,
))

# Second body paragraph
new_paras.append(make_para(
    doc,
    "In April 2026, the system was adapted for the Correlation One Data Analytics program "
    "using real operational data from the Amazon Last Mile Routing Research Challenge "
    "(Los Angeles, 2018). This required rebuilding the data pipeline around the real LMRC "
    "schema, revalidating all features against actual delivery outcomes, and retraining "
    "the model on 3,559 real packages.",
    space_before=0, space_after=8,
))

# Claude subheading
new_paras.append(make_para(
    doc, "Claude (Anthropic)",
    bold=True, font_size=11, color=NAVY, space_before=12, space_after=6,
))

# Claude body
new_paras.append(make_para(
    doc,
    "Claude was used as a writing and editing tool for the academic deliverables \u2014 "
    "project description, project scoping, data curation report, and EDA document. "
    "Claude helped structure arguments, correct prose, and ensure the documents met "
    "Correlation One requirements. All analytical findings, technical decisions, and data "
    "interpretations are the author\u2019s own.",
    space_before=0, space_after=8,
))

# CrewAI subheading
new_paras.append(make_para(
    doc, "CrewAI Agents",
    bold=True, font_size=11, color=NAVY, space_before=12, space_after=6,
))

# CrewAI body
new_paras.append(make_para(
    doc,
    "CrewAI agents are part of the original system architecture, not a tool used for "
    "document generation. They generate per-package executive reports for dispatch "
    "supervisors, explaining model predictions in plain language. Given a package\u2019s "
    "feature values and the trained model\u2019s predicted failure probability, the agent "
    "produces a risk assessment formatted for a dispatcher: the risk tier, the primary "
    "contributing factors, and an actionable recommendation.",
    space_before=0, space_after=8,
))

# Closing paragraph
new_paras.append(make_para(
    doc,
    "This use of generative AI is consistent with Correlation One guidelines, which "
    "explicitly encourage transparent use of AI tools in the analytics workflow.",
    space_before=0, space_after=8,
))

# ── Insert after the heading paragraph ────────────────────────────────────────
# Re-fetch the heading element (its position in body is now heading_idx)
all_paras_after = body.findall(qn("w:p"))
heading_el = all_paras_after[heading_idx]
insert_after = heading_el

for new_p in new_paras:
    insert_after.addnext(new_p)
    insert_after = new_p

print(f"Inserted {len(new_paras)} replacement paragraphs.")

# ── Save ───────────────────────────────────────────────────────────────────────
doc.save(str(DOC_PATH))
print(f"\nSaved \u2192 {DOC_PATH}")
print(f"File size: {DOC_PATH.stat().st_size / 1024:.1f} KB")
