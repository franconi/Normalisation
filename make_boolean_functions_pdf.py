#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "binary_boolean_functions.pdf"
FONT_ROOT = Path(
    "/Users/franconi/.cache/codex-runtimes/codex-primary-runtime/dependencies/"
    "native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/"
    "Resources/fonts/truetype"
)


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("DejaVuSans", str(FONT_ROOT / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(
        TTFont("DejaVuSans-Bold", str(FONT_ROOT / "DejaVuSans-Bold.ttf"))
    )


def truth_cell(value: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(f"<b>{value}</b>", style)


def formula(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def main() -> None:
    register_fonts()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="DejaVuSans-Bold",
        fontSize=19,
        leading=23,
        textColor=colors.HexColor("#16212b"),
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["BodyText"],
        fontName="DejaVuSans",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#4f5f6d"),
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    header_style = ParagraphStyle(
        "Header",
        parent=styles["BodyText"],
        fontName="DejaVuSans-Bold",
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    body_center = ParagraphStyle(
        "BodyCenter",
        parent=styles["BodyText"],
        fontName="DejaVuSans",
        fontSize=8.6,
        leading=10,
        alignment=TA_CENTER,
    )
    body_formula = ParagraphStyle(
        "BodyFormula",
        parent=styles["BodyText"],
        fontName="DejaVuSans",
        fontSize=8.8,
        leading=10.8,
        alignment=TA_LEFT,
    )
    note_style = ParagraphStyle(
        "Note",
        parent=styles["BodyText"],
        fontName="DejaVuSans",
        fontSize=8.4,
        leading=11,
        textColor=colors.HexColor("#52606d"),
        alignment=TA_LEFT,
    )

    rows = [
        ("1", "F", "F", "F", "F", "false"),
        ("2", "F", "F", "F", "T", "x ∧ y"),
        ("3", "F", "F", "T", "F", "x ∧ ¬y = ¬(x → y)"),
        ("4", "F", "F", "T", "T", "x"),
        ("5", "F", "T", "F", "F", "¬x ∧ y = ¬(x ← y)"),
        ("6", "F", "T", "F", "T", "y"),
        ("7", "F", "T", "T", "F", "x ⊕ y = ¬(x ↔ y)"),
        ("8", "F", "T", "T", "T", "x ∨ y = ¬x → y"),
        ("9", "T", "F", "F", "F", "¬(x ∨ y) = ¬(¬x → y)"),
        ("10", "T", "F", "F", "T", "x ↔ y"),
        ("11", "T", "F", "T", "F", "¬y"),
        ("12", "T", "F", "T", "T", "x ← y"),
        ("13", "T", "T", "F", "F", "¬x"),
        ("14", "T", "T", "F", "T", "x → y"),
        ("15", "T", "T", "T", "F", "¬(x ∧ y) = x → ¬y"),
        ("16", "T", "T", "T", "T", "true"),
    ]

    table_data = [
        [
            Paragraph("#", header_style),
            Paragraph("f(F,F)", header_style),
            Paragraph("f(F,T)", header_style),
            Paragraph("f(T,F)", header_style),
            Paragraph("f(T,T)", header_style),
            Paragraph("Expression", header_style),
        ]
    ]
    for row in rows:
        table_data.append(
            [
                Paragraph(row[0], body_center),
                truth_cell(row[1], body_center),
                truth_cell(row[2], body_center),
                truth_cell(row[3], body_center),
                truth_cell(row[4], body_center),
                formula(row[5], body_formula),
            ]
        )

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=landscape(A4),
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=14 * mm,
        title="Binary Boolean Functions",
        author="Codex",
        subject="Truth tables for the 16 binary Boolean functions",
    )

    story = [
        Paragraph("The 16 Binary Boolean Functions", title_style),
        Paragraph(
            "Each function f: {F,T} × {F,T} → {F,T} is determined by four "
            "truth values, so there are 2<sup>4</sup> = 16 functions. "
            "Here x ← y means y → x.",
            subtitle_style,
        ),
        Spacer(1, 4),
    ]

    table = Table(
        table_data,
        colWidths=[12 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm, 145 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#233746")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (0, 0), (4, -1), "CENTER"),
            ("ALIGN", (5, 0), (5, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d2da")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
            ("LINEBELOW", (0, 0), (-1, 0), 1.1, colors.HexColor("#1b2a35")),
        ]
    )

    true_bg = colors.HexColor("#dff3e7")
    false_bg = colors.HexColor("#f8e4df")
    for row_index, row in enumerate(rows, start=1):
        for col_index in range(1, 5):
            style.add(
                "BACKGROUND",
                (col_index, row_index),
                (col_index, row_index),
                true_bg if row[col_index] == "T" else false_bg,
            )

    table.setStyle(style)
    story.append(table)
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Rows are ordered as (F,F), (F,T), (T,F), (T,T). "
            "The arrow forms highlight implication, reverse implication, "
            "and equivalence where those names are most informative.",
            note_style,
        )
    )

    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
