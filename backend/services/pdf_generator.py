"""
Medical Portfolio PDF generator using ReportLab.

Produces a clean, branded A4 document containing:
  - Patient personal information
  - Emergency contact
  - Allergies (highlighted)
  - Chronic conditions
  - Current medications
  - Surgical history
  - Doctor notes
  - Selected medical documents embedded as images (actual file previews)
"""

from datetime import datetime
from io import BytesIO
from typing import Any

import fitz  # PyMuPDF
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Page metrics ──────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 2 * cm
AVAIL_W = PAGE_W - 2 * MARGIN   # ≈ 481 pt  ≈ 17 cm

# ── Brand colours ─────────────────────────────────────────────────────────────
TEAL       = colors.HexColor("#0ea5a4")
TEAL_DARK  = colors.HexColor("#0c8f8e")
TEAL_LIGHT = colors.HexColor("#e0f7f7")
RED_ALERT  = colors.HexColor("#dc2626")
RED_LIGHT  = colors.HexColor("#fef2f2")
GREY_TEXT  = colors.HexColor("#6b7280")
GREY_BG    = colors.HexColor("#f9fafb")
BLACK      = colors.HexColor("#111827")


# ── Paragraph styles ──────────────────────────────────────────────────────────
def _make_styles() -> dict:
    return {
        "section_head": ParagraphStyle(
            "section_head", fontName="Helvetica-Bold", fontSize=11,
            textColor=TEAL_DARK, spaceBefore=10, spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "label", fontName="Helvetica-Bold", fontSize=8.5,
            textColor=GREY_TEXT, spaceAfter=1,
        ),
        "value": ParagraphStyle(
            "value", fontName="Helvetica", fontSize=9.5,
            textColor=BLACK, spaceAfter=2,
        ),
        "alert": ParagraphStyle(
            "alert", fontName="Helvetica-Bold", fontSize=9.5, textColor=RED_ALERT,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9, textColor=BLACK, leading=13,
        ),
        "small_grey": ParagraphStyle(
            "small_grey", fontName="Helvetica", fontSize=8, textColor=GREY_TEXT,
        ),
        "doc_title": ParagraphStyle(
            "doc_title", fontName="Helvetica-Bold", fontSize=10, textColor=TEAL_DARK,
            spaceAfter=4,
        ),
        "doc_num": ParagraphStyle(
            "doc_num", fontName="Helvetica-Bold", fontSize=8.5, textColor=GREY_TEXT,
        ),
    }


def _val(v: Any, fallback: str = "—") -> str:
    if v is None or str(v).strip() == "":
        return fallback
    return str(v)


def _section_header(text: str, styles: dict) -> list:
    return [
        Spacer(1, 0.35 * cm),
        HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=4),
        Paragraph(text, styles["section_head"]),
    ]


def _grid_table(rows: list, col_widths: list) -> Table:
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _allergy_table(allergies: list, styles: dict) -> Any:
    if not allergies:
        return Paragraph("No known allergies.", styles["value"])
    header = [
        Paragraph("ALLERGEN",  styles["label"]),
        Paragraph("REACTION",  styles["label"]),
        Paragraph("SEVERITY",  styles["label"]),
    ]
    data = [header]
    for a in allergies:
        sev = _val(a.get("severity"), "Unknown")
        sev_col = RED_ALERT if sev.lower() == "severe" else colors.HexColor("#d97706") if sev.lower() == "moderate" else BLACK
        data.append([
            Paragraph(_val(a.get("allergen")), styles["alert"]),
            Paragraph(_val(a.get("reaction")), styles["body"]),
            Paragraph(sev, ParagraphStyle("sev", fontName="Helvetica-Bold", fontSize=9, textColor=sev_col)),
        ])
    t = Table(data, colWidths=[5.5 * cm, 6.5 * cm, 4 * cm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), TEAL_LIGHT),
        ("BACKGROUND",  (0, 1), (-1, -1), RED_LIGHT),
        ("BOX",         (0, 0), (-1, -1), 0.5, RED_ALERT),
        ("INNERGRID",   (0, 0), (-1, -1), 0.25, colors.HexColor("#fecaca")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def _styled_table(data: list, col_widths: list) -> Table:
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), TEAL_LIGHT),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [GREY_BG, colors.white]),
        ("BOX",           (0, 0), (-1, -1), 0.5, TEAL),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, colors.HexColor("#d1faf9")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def _medications_table(meds: list, styles: dict) -> Any:
    if not meds:
        return Paragraph("No current medications on record.", styles["value"])
    header = [Paragraph(h, styles["label"]) for h in ["MEDICATION", "DOSAGE", "FREQUENCY", "REASON"]]
    rows = [header] + [
        [Paragraph(_val(m.get(k)), styles["body"]) for k in ("name", "dosage", "frequency", "reason")]
        for m in meds
    ]
    return _styled_table(rows, [4.5 * cm, 3.5 * cm, 3.5 * cm, 4.5 * cm])


def _conditions_table(conditions: list, styles: dict) -> Any:
    if not conditions:
        return Paragraph("No chronic conditions on record.", styles["value"])
    header = [Paragraph(h, styles["label"]) for h in ["CONDITION", "SINCE", "STATUS", "NOTES"]]
    rows = [header] + [
        [Paragraph(_val(c.get(k)), styles["body"]) for k in ("name", "diagnosed_year", "status", "notes")]
        for c in conditions
    ]
    return _styled_table(rows, [5 * cm, 2.5 * cm, 3 * cm, 5.5 * cm])


def _surgeries_table(surgeries: list, styles: dict) -> Any:
    if not surgeries:
        return Paragraph("No surgical history on record.", styles["value"])
    header = [Paragraph(h, styles["label"]) for h in ["PROCEDURE", "HOSPITAL", "DATE", "NOTES"]]
    rows = [header] + [
        [Paragraph(_val(s.get(k)), styles["body"]) for k in ("procedure", "hospital", "date", "notes")]
        for s in surgeries
    ]
    return _styled_table(rows, [5 * cm, 5 * cm, 2.5 * cm, 3.5 * cm])


# ── Image embedding helpers ───────────────────────────────────────────────────

def _rl_image_from_bytes(img_bytes: bytes, max_width: float) -> RLImage | None:
    """
    Create a ReportLab Image flowable from raw image bytes.
    Scales the image to fit *max_width* while preserving aspect ratio.
    """
    try:
        pil = PILImage.open(BytesIO(img_bytes))
        orig_w, orig_h = pil.size
        if orig_w == 0:
            return None
        scale = min(max_width / orig_w, 1.0)    # never upscale
        w = orig_w * scale
        h = orig_h * scale
        return RLImage(BytesIO(img_bytes), width=w, height=h)
    except Exception:
        return None


def _pages_from_pdf_bytes(pdf_bytes: bytes, max_pages: int = 6) -> list[bytes]:
    """
    Render up to *max_pages* pages of a PDF as PNG byte strings using PyMuPDF.
    """
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            mat = fitz.Matrix(1.5, 1.5)          # 1.5× zoom → decent resolution
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("png"))
        doc.close()
    except Exception as exc:
        print(f"[pdf_gen] PDF render error: {exc}")
    return images


def _embed_document_file(
    doc: dict,
    file_bytes: bytes | None,
    styles: dict,
) -> list:
    """
    Produce a list of ReportLab flowables for one selected document.
    Embeds the actual file visually (images or rendered PDF pages).
    Falls back to metadata-only if no file bytes are provided.
    """
    items = []
    folder_label = "Prescription" if doc.get("folder") == "prescriptions" else "Report"
    title = f"{folder_label}: {doc.get('original_filename', 'Unnamed')}"
    items.append(Paragraph(title, styles["doc_title"]))

    meta_rows = [
        [Paragraph("Hospital",  styles["label"]), Paragraph(_val(doc.get("hospital_name")), styles["value"]),
         Paragraph("Uploaded",  styles["label"]), Paragraph(
            str(doc.get("upload_date", ""))[:10] if doc.get("upload_date") else "—",
            styles["value"],
        )],
    ]
    items.append(_grid_table(meta_rows, [2.5 * cm, 8 * cm, 2.5 * cm, 3.5 * cm]))
    items.append(Spacer(1, 0.2 * cm))

    if not file_bytes:
        items.append(Paragraph("(File preview unavailable)", styles["small_grey"]))
        return items

    mime = doc.get("mime_type", "")

    if mime.startswith("image/"):
        img = _rl_image_from_bytes(file_bytes, AVAIL_W)
        if img:
            img.hAlign = "LEFT"
            items.append(img)
        else:
            items.append(Paragraph("(Could not render image)", styles["small_grey"]))

    elif mime == "application/pdf":
        pages = _pages_from_pdf_bytes(file_bytes)
        if pages:
            for idx, page_png in enumerate(pages):
                img = _rl_image_from_bytes(page_png, AVAIL_W)
                if img:
                    img.hAlign = "LEFT"
                    items.append(img)
                    if idx < len(pages) - 1:
                        items.append(Spacer(1, 0.2 * cm))
        else:
            items.append(Paragraph("(Could not render PDF pages)", styles["small_grey"]))

    else:
        items.append(Paragraph("(Preview not supported for this file type)", styles["small_grey"]))

    items.append(Spacer(1, 0.2 * cm))
    return items


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_portfolio_pdf(
    profile: dict,
    documents: list[tuple[dict, bytes | None]],
    expires_label: str = "",
) -> bytes:
    """
    Build and return the portfolio PDF bytes.

    Args:
        profile:    Full profile dict from MongoDB (ProfileUpdate shape).
        documents:  List of (document_meta, file_bytes) tuples.
                    Pass file_bytes=None to include metadata only.
        expires_label: Human-readable expiry string shown on the cover.
    """
    buffer = BytesIO()
    doc_template = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="JeevaKosha Medical Portfolio",
        author="JeevaKosha",
    )

    styles = _make_styles()
    personal = profile.get("personal") or {}
    emergency = profile.get("emergency_contact") or {}
    story = []

    # ── Cover header ──────────────────────────────────────────────────────────
    patient_name = _val(personal.get("full_name"), "Patient")
    blood_group  = _val(personal.get("blood_group"), "Unknown")
    now_str      = datetime.utcnow().strftime("%d %B %Y, %H:%M UTC")

    header_data = [
        [
            Paragraph("JeevaKosha", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=13, textColor=colors.white)),
            Paragraph("MEDICAL PORTFOLIO", ParagraphStyle("brand2", fontName="Helvetica-Bold", fontSize=13, textColor=colors.white, alignment=2)),
        ],
        [
            Paragraph(patient_name, ParagraphStyle("pt_name", fontName="Helvetica-Bold", fontSize=18, textColor=colors.white)),
            Paragraph(f"Blood Group: <b>{blood_group}</b>", ParagraphStyle("bg", fontName="Helvetica", fontSize=13, textColor=colors.HexColor("#ccfbf1"), alignment=2)),
        ],
        [
            Paragraph(f"Generated: {now_str}", ParagraphStyle("gen", fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#a7f3f0"))),
            Paragraph(
                f"Access expires: {expires_label}" if expires_label else "Confidential Medical Record",
                ParagraphStyle("exp", fontName="Helvetica-Oblique", fontSize=8.5, textColor=colors.HexColor("#fde68a"), alignment=2),
            ),
        ],
    ]
    header_tbl = Table(header_data, colWidths=[9.5 * cm, 7.5 * cm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (0, -1), 14),
        ("RIGHTPADDING",  (-1, 0), (-1, -1), 14),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── Personal Information ──────────────────────────────────────────────────
    story.extend(_section_header("PERSONAL INFORMATION", styles))
    info_rows = [
        [Paragraph("Full Name",  styles["label"]), Paragraph(_val(personal.get("full_name")),  styles["value"]),
         Paragraph("DOB",        styles["label"]), Paragraph(_val(personal.get("date_of_birth")), styles["value"])],
        [Paragraph("Gender",     styles["label"]), Paragraph(_val(personal.get("gender")),     styles["value"]),
         Paragraph("Blood Group",styles["label"]), Paragraph(_val(personal.get("blood_group")), styles["value"])],
        [Paragraph("Height",     styles["label"]), Paragraph(f"{_val(personal.get('height_cm'))} cm", styles["value"]),
         Paragraph("Weight",     styles["label"]), Paragraph(f"{_val(personal.get('weight_kg'))} kg", styles["value"])],
        [Paragraph("Phone",      styles["label"]), Paragraph(_val(personal.get("phone")),      styles["value"]),
         Paragraph("",           styles["label"]), Paragraph("", styles["value"])],
        [Paragraph("Address",    styles["label"]),
         Paragraph(", ".join(filter(None, [personal.get("address"), personal.get("city"), personal.get("state"), personal.get("pincode")])) or "—", styles["value"]),
         Paragraph("", styles["label"]), Paragraph("", styles["value"])],
    ]
    story.append(_grid_table(info_rows, [3.5 * cm, 7.5 * cm, 3.5 * cm, 2.5 * cm]))

    # ── Emergency Contact ─────────────────────────────────────────────────────
    story.extend(_section_header("EMERGENCY CONTACT", styles))
    ec_rows = [[
        Paragraph("Name",     styles["label"]), Paragraph(_val(emergency.get("name")),     styles["value"]),
        Paragraph("Relation", styles["label"]), Paragraph(_val(emergency.get("relation")), styles["value"]),
        Paragraph("Phone",    styles["label"]), Paragraph(_val(emergency.get("phone")),    styles["value"]),
    ]]
    story.append(_grid_table(ec_rows, [2.5 * cm, 5 * cm, 2.5 * cm, 3.5 * cm, 2 * cm, 3 * cm]))

    # ── Allergies ─────────────────────────────────────────────────────────────
    story.extend(_section_header("ALLERGIES", styles))
    story.append(_allergy_table(profile.get("allergies") or [], styles))

    # ── Chronic Conditions ────────────────────────────────────────────────────
    story.extend(_section_header("CHRONIC CONDITIONS", styles))
    story.append(_conditions_table(profile.get("chronic_conditions") or [], styles))

    # ── Current Medications ───────────────────────────────────────────────────
    story.extend(_section_header("CURRENT MEDICATIONS", styles))
    story.append(_medications_table(profile.get("current_medications") or [], styles))

    # ── Surgical History ──────────────────────────────────────────────────────
    story.extend(_section_header("SURGICAL HISTORY", styles))
    story.append(_surgeries_table(profile.get("surgeries") or [], styles))

    # ── Doctor Notes ──────────────────────────────────────────────────────────
    notes = (profile.get("doctor_notes") or "").strip()
    if notes:
        story.extend(_section_header("DOCTOR'S NOTES", styles))
        story.append(Paragraph(notes, styles["body"]))

    # ── Selected Medical Documents ────────────────────────────────────────────
    if documents:
        story.extend(_section_header("INCLUDED MEDICAL DOCUMENTS", styles))
        for idx, (doc_meta, file_bytes) in enumerate(documents, start=1):
            story.append(Paragraph(f"Document {idx} of {len(documents)}", styles["doc_num"]))
            story.extend(_embed_document_file(doc_meta, file_bytes, styles))
            if idx < len(documents):
                story.append(HRFlowable(
                    width="100%", thickness=0.5,
                    color=colors.HexColor("#e5e7eb"), spaceAfter=4,
                ))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREY_TEXT))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "This document was generated by JeevaKosha — a secure medical data management platform. "
        "It is intended solely for the named patient and authorised medical professionals. "
        "Unauthorised distribution is prohibited.",
        ParagraphStyle("footer", fontName="Helvetica", fontSize=8, textColor=GREY_TEXT),
    ))

    doc_template.build(story)
    return buffer.getvalue()
