import os
import io
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas
from PIL import Image as PILImage

logger = logging.getLogger("dentalai.pdf")

# Primary clinical disclaimers
PRIMARY_SAFETY_NOTICE = (
    "AI-generated results are preliminary and may be inaccurate. This system does not provide a confirmed diagnosis. "
    "Consult a qualified dental professional for clinical evaluation."
)

MULTI_VIEW_NOTICE = (
    "This combined report provides an algorithmic compilation of independent single-image ResNet-50 model inferences "
    "across the three photographic views. The underlying model was trained on individual images and has NOT been "
    "independently validated as a cohesive multi-view diagnostic system. Clinicians must evaluate each view's visual findings independently."
)

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and draw
    consistent professional running headers and footers with 'Page X of Y'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Top Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 842 - 25, "DentalAI Clinical Screening Platform — Preliminary Intraoral Report")
            self.drawRightString(595 - 36, 842 - 25, f"Report Ref: {getattr(self, '_report_id', 'N/A')}")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 842 - 28, 595 - 36, 842 - 28)

        # Running Bottom Footer (all pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 32, 595 - 36, 32)

        self.drawString(36, 20, "CONFIDENTIAL & PROPRIETARY — PRELIMINARY DENTAL SCREENING PROTOTYPE")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(595 - 36, 20, page_str)
        self.restoreState()


def _format_image_for_pdf(image_path: Optional[str], target_width: float, target_height: float) -> Optional[RLImage]:
    """Safely loads and scales an image for ReportLab Platypus tables."""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with PILImage.open(image_path) as im:
            orig_w, orig_h = im.size
            if orig_w == 0 or orig_h == 0:
                return None
            ratio = min(target_width / orig_w, target_height / orig_h)
            new_w = orig_w * ratio
            new_h = orig_h * ratio
        return RLImage(image_path, width=new_w, height=new_h)
    except Exception as e:
        logger.warning("Could not load image %s for PDF: %s", image_path, e)
        return None


def generate_screening_pdf(report_data: Dict[str, Any], uploads_dir: str) -> bytes:
    """
    Generates a high-quality clinical screening PDF report matching Section 5 requirements.
    A4 page format, clean typography, patient info, three-view side-by-side images, Grad-CAM overlays,
    model scores, examination protocol, and verbatim clinical disclaimers.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )

    report_id = report_data.get("report_id", "RPT-00000000")

    # Typography and Styles
    styles = getSampleStyleSheet()

    # Custom Palettes
    primary_color = colors.HexColor("#0369A1")    # Sky-700
    dark_text = colors.HexColor("#0F172A")        # Slate-900
    muted_text = colors.HexColor("#475569")       # Slate-600
    border_color = colors.HexColor("#E2E8F0")     # Slate-200
    bg_light = colors.HexColor("#F8FAFC")         # Slate-50
    alert_border = colors.HexColor("#F59E0B")     # Amber-500
    alert_bg = colors.HexColor("#FEF3C7")         # Amber-100

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=muted_text
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=dark_text
    )
    body_bold = ParagraphStyle(
        "Body_Bold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=dark_text
    )
    alert_text = ParagraphStyle(
        "AlertText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#92400E")
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=dark_text
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=dark_text
    )
    table_cell_header = ParagraphStyle(
        "TableCellHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []

    # -------------------------------------------------------------
    # 1. Header Banner
    # -------------------------------------------------------------
    header_table_data = [
        [
            Paragraph("<b>DentalAI</b> Clinical Screening", title_style),
            Paragraph(f"<b>REPORT ID:</b> {report_id}<br/><b>Scan Date:</b> {report_data.get('scan_date', 'N/A')}", ParagraphStyle(
                "HeaderMeta",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=12,
                textColor=muted_text,
                alignment=2
            ))
        ]
    ]
    header_table = Table(header_table_data, colWidths=[320, 203])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Paragraph("AI-Assisted Multi-Angle Dental Disease Pre-Screening • ResNet-50 (6 Oral Disease Classes)", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=2, spaceAfter=8))

    # -------------------------------------------------------------
    # 2. Mandatory Clinical Safety Notice Box
    # -------------------------------------------------------------
    safety_box_data = [
        [
            Paragraph(
                f"<b>PRELIMINARY PRE-SCREENING NOTICE:</b> {PRIMARY_SAFETY_NOTICE}",
                alert_text
            )
        ]
    ]
    safety_box = Table(safety_box_data, colWidths=[523])
    safety_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), alert_bg),
        ("BOX", (0, 0), (-1, -1), 1.5, alert_border),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(safety_box)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 3. Patient Information Card
    # -------------------------------------------------------------
    patient = report_data.get("patient", {})
    age_str = f"{patient.get('age')} years" if patient.get("age") is not None else "Not specified"
    dob_str = patient.get("date_of_birth") or "Not recorded"
    gender_str = patient.get("gender") or "Not Specified"
    contact_str = patient.get("contact_number") or "Not recorded"
    email_str = patient.get("email") or "Not recorded"

    pat_rows = [
        [
            Paragraph("<b>Patient Name:</b>", body_style),
            Paragraph(str(patient.get("name", "N/A")), body_bold),
            Paragraph("<b>Medical ID:</b>", body_style),
            Paragraph(str(patient.get("patient_id", "N/A")), body_bold)
        ],
        [
            Paragraph("<b>Age / DOB:</b>", body_style),
            Paragraph(f"{age_str} ({dob_str})", body_style),
            Paragraph("<b>Gender:</b>", body_style),
            Paragraph(gender_str, body_style)
        ],
        [
            Paragraph("<b>Contact No:</b>", body_style),
            Paragraph(contact_str, body_style),
            Paragraph("<b>Email:</b>", body_style),
            Paragraph(email_str, body_style)
        ]
    ]

    med_hist = patient.get("medical_history")
    dent_hist = patient.get("dental_history")
    notes = patient.get("notes")

    if med_hist or dent_hist or notes:
        hist_text = []
        if med_hist:
            hist_text.append(f"<b>Medical:</b> {med_hist}")
        if dent_hist:
            hist_text.append(f"<b>Dental:</b> {dent_hist}")
        if notes:
            hist_text.append(f"<b>Notes:</b> {notes}")
        pat_rows.append([
            Paragraph("<b>Clinical History:</b>", body_style),
            Paragraph(" | ".join(hist_text), body_style),
            "", ""
        ])

    pat_table = Table(pat_rows, colWidths=[85, 175, 85, 178])
    pat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_light),
        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("SPAN", (1, 3), (3, 3)) if len(pat_rows) > 3 else ("ALIGN", (0, 0), (0, 0), "LEFT"),
    ]))
    story.append(pat_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 4. Screening Summary Card
    # -------------------------------------------------------------
    summary = report_data.get("screening_summary", {})
    triage = summary.get("triage_recommendation") or summary.get("urgency_level") or "Routine Evaluation"
    overall_status = summary.get("overall_status", "Screening Complete")
    narrative = summary.get("narrative", "")
    abstained = summary.get("abstained_views", [])

    summary_rows = [
        [
            Paragraph("<b>Overall Screening Status:</b>", body_bold),
            Paragraph(f"<b>{overall_status}</b>", ParagraphStyle("StatusTxt", parent=body_bold, textColor=primary_color)),
            Paragraph("<b>Triage Urgency:</b>", body_bold),
            Paragraph(f"<b>{triage}</b>", ParagraphStyle("TriageTxt", parent=body_bold, textColor=colors.HexColor("#0284C7")))
        ],
        [
            Paragraph("<b>AI Narrative:</b>", body_style),
            Paragraph(narrative, body_style),
            "", ""
        ]
    ]

    if abstained:
        summary_rows.append([
            Paragraph("<b>Abstained Views:</b>", alert_text),
            Paragraph(f"The following photographic views did not meet the confidence threshold: {', '.join(abstained)}. Chairside inspection required.", alert_text),
            "", ""
        ])

    summary_table = Table(summary_rows, colWidths=[120, 160, 90, 153])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F9FF")),
        ("BOX", (0, 0), (-1, -1), 1, primary_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BAE6FD")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("SPAN", (1, 1), (3, 1)),
        ("SPAN", (1, 2), (3, 2)) if len(summary_rows) > 2 else ("ALIGN", (0, 0), (0, 0), "LEFT"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # -------------------------------------------------------------
    # 5. Three-View Image & Grad-CAM Analysis Section
    # -------------------------------------------------------------
    story.append(Paragraph("Three-View Intraoral Photographic Analysis & Grad-CAM Visual Salience", h2_style))
    story.append(Paragraph(
        "Each intraoral view is shown side-by-side with its convolutional feature salience overlay (Grad-CAM on layer <i>conv5_block3_out</i>). "
        "Heatmaps highlight spatial regions that influenced the model classification and do not represent verified diagnostic lesion boundaries.",
        subtitle_style
    ))
    story.append(Spacer(1, 6))

    images_analyzed = report_data.get("images_analyzed", [])
    img_box_width = 115
    img_box_height = 86

    for img_view in images_analyzed:
        view_label = img_view.get("label", img_view.get("view", "").capitalize() + " View")
        pred_class = img_view.get("predicted_class", "Undetermined")
        conf_pct = img_view.get("confidence_percentage", 0.0)
        inf_latency = img_view.get("inference_time_ms", 0.0)
        is_abstaining = img_view.get("is_abstaining", False)

        orig_filename = img_view.get("original_image")
        heat_filename = img_view.get("heatmap_image")

        orig_full_path = os.path.join(uploads_dir, orig_filename) if orig_filename else None
        heat_full_path = os.path.join(uploads_dir, heat_filename) if heat_filename else None

        rl_orig = _format_image_for_pdf(orig_full_path, img_box_width, img_box_height)
        rl_heat = _format_image_for_pdf(heat_full_path, img_box_width, img_box_height)

        orig_cell = rl_orig if rl_orig else Paragraph("<i>[Original Photograph Unavailable]</i>", subtitle_style)
        heat_cell = rl_heat if rl_heat else Paragraph("<i>[Grad-CAM Salience Unavailable]</i>", subtitle_style)

        # Top-3 predictions formatted
        top3 = img_view.get("top_three_predictions", [])
        top3_lines = []
        for item in top3:
            rank = item.get("rank", 1)
            name = item.get("display_name", item.get("class_name", ""))
            pct = item.get("percentage", 0.0)
            top3_lines.append(f"<b>#{rank}</b> {name}: <b>{pct:.1f}%</b>")
        top3_text = "<br/>".join(top3_lines) if top3_lines else "None recorded"

        status_badge = "<font color='#D97706'><b>LOW CONFIDENCE / ABSTAINED</b></font>" if is_abstaining else "<font color='#0D9488'><b>EVALUATED</b></font>"

        view_detail_text = (
            f"<b>Primary Finding:</b> {pred_class}<br/>"
            f"<b>Top-1 Output Score:</b> {conf_pct:.1f}%<br/>"
            f"<b>Model Latency:</b> {inf_latency:.1f}ms<br/>"
            f"<b>Status:</b> {status_badge}<br/><br/>"
            f"<b>Top-3 Model Scores:</b><br/>{top3_text}"
        )

        view_row_data = [
            [
                Paragraph(f"<b>{view_label} — Original Photo</b>", table_cell_header),
                Paragraph(f"<b>{view_label} — Grad-CAM Salience</b>", table_cell_header),
                Paragraph(f"<b>Model Prediction & Scores</b>", table_cell_header)
            ],
            [
                orig_cell,
                heat_cell,
                Paragraph(view_detail_text, table_cell)
            ]
        ]

        view_table = Table(view_row_data, colWidths=[130, 130, 263])
        view_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("BACKGROUND", (0, 1), (-1, 1), bg_light),
            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("ALIGN", (0, 1), (1, 1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))

        story.append(KeepTogether([
            view_table,
            Spacer(1, 6)
        ]))

    story.append(Spacer(1, 6))

    # -------------------------------------------------------------
    # 6. Combined Findings & Dentist Protocol Section
    # -------------------------------------------------------------
    conditions = report_data.get("conditions_detected", [])
    if conditions:
        cond_rows = [
            [
                Paragraph("<b>Flagged Oral Condition</b>", table_cell_header),
                Paragraph("<b>Affected View(s)</b>", table_cell_header),
                Paragraph("<b>Peak Model Score</b>", table_cell_header),
                Paragraph("<b>Clinical Signatures</b>", table_cell_header)
            ]
        ]
        for c in conditions:
            views_str = ", ".join(c.get("affected_views", []))
            peak_pct = f"{c.get('peak_score', 0.0) * 100:.1f}%"
            signs_str = "; ".join(c.get("clinical_signs", [])[:2])
            cond_rows.append([
                Paragraph(f"<b>{c.get('disease_name')}</b>", table_cell),
                Paragraph(views_str, table_cell),
                Paragraph(peak_pct, table_cell_bold),
                Paragraph(signs_str, table_cell)
            ])

        cond_table = Table(cond_rows, colWidths=[130, 90, 80, 223])
        cond_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("BACKGROUND", (0, 1), (-1, -1), bg_light),
            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(KeepTogether([
            Paragraph("Combined Model Findings Across Intraoral Views", h2_style),
            cond_table,
            Spacer(1, 8)
        ]))

    # Examination Steps (Strictly procedural, NO drug prescriptions)
    exam_steps = report_data.get("recommended_examination_steps", [])
    if exam_steps:
        exam_paragraphs = [
            Paragraph(f"• {step}", body_style) for step in exam_steps
        ]
        story.append(KeepTogether([
            Paragraph("Recommended Clinical Follow-Up Protocol (For Qualified Dentist)", h2_style),
            *exam_paragraphs,
            Spacer(1, 8)
        ]))

    # -------------------------------------------------------------
    # 7. Mandatory Multi-View Notice Box
    # -------------------------------------------------------------
    mv_notice_data = [
        [
            Paragraph(
                f"<b>MULTI-VIEW LIMITATION NOTICE:</b> {MULTI_VIEW_NOTICE}",
                ParagraphStyle("MVNoticeText", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=muted_text)
            )
        ]
    ]
    mv_notice_table = Table(mv_notice_data, colWidths=[523])
    mv_notice_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_light),
        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(KeepTogether([
        mv_notice_table,
        Spacer(1, 4)
    ]))

    # Custom canvas with dynamic page numbering
    def make_canvas(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c._report_id = report_id
        return c

    doc.build(story, canvasmaker=make_canvas)
    buffer.seek(0)
    return buffer.getvalue()

