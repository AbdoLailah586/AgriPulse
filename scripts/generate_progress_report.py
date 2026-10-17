"""Generate a short, supervisor-facing PDF progress report for AgriPulse.

Run: ../.venv/Scripts/python generate_progress_report.py
Output: ../reports/AgriPulse_Progress_Report.pdf
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "reports" / "AgriPulse_Progress_Report.pdf"

NAVY = colors.HexColor("#1B3A5C")
TEAL = colors.HexColor("#1F7A6C")
AMBER_BG = colors.HexColor("#FFF4D6")
AMBER_BORDER = colors.HexColor("#D9A441")
LIGHT_GREY = colors.HexColor("#F2F4F6")
TEXT_GREY = colors.HexColor("#333333")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=NAVY, spaceAfter=6))
styles.add(ParagraphStyle(name="SubTitle", fontName="Helvetica", fontSize=11, leading=15, textColor=TEXT_GREY, spaceAfter=14))
styles.add(ParagraphStyle(name="H2", fontName="Helvetica-Bold", fontSize=13.5, leading=17, textColor=NAVY, spaceBefore=16, spaceAfter=8))
styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=10, textColor=TEXT_GREY, leading=15, spaceAfter=6))
styles.add(ParagraphStyle(name="BodyBold", parent=styles["Body"], fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="BulletItem", parent=styles["Body"], leftIndent=14, bulletIndent=2, spaceAfter=4))
styles.add(ParagraphStyle(name="TableHead", fontName="Helvetica-Bold", fontSize=9, textColor=colors.white))
styles.add(ParagraphStyle(name="TableCell", fontName="Helvetica", fontSize=9, textColor=TEXT_GREY, leading=12))
styles.add(ParagraphStyle(name="Caption", fontName="Helvetica-Oblique", fontSize=8.5, textColor=colors.HexColor("#666666")))


def p(text, style="Body"):
    return Paragraph(text, styles[style])


def section_title(text):
    return p(text, "H2")


def highlight_box(title, body_lines):
    inner = [p(f"<b>{title}</b>", "BodyBold")]
    for line in body_lines:
        inner.append(p(line, "Body"))
    t = Table([[inner]], colWidths=[16.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), AMBER_BG),
                ("BOX", (0, 0), (-1, -1), 1, AMBER_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def status_table(rows, col_widths):
    header = rows[0]
    data = [[Paragraph(h, styles["TableHead"]) for h in header]] + [
        [Paragraph(str(c), styles["TableCell"]) for c in row] for row in rows[1:]
    ]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def build():
    doc = SimpleDocTemplate(
        str(OUT_PATH),
        pagesize=A4,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        title="AgriPulse Progress Report",
    )

    story = []

    story.append(p("AgriPulse — Engineering Progress Report", "ReportTitle"))
    story.append(
        p(
            "AI Predictive Maintenance for Irrigation Pumps — Graduation Project, "
            "AI Engineering Program, Faculty of Engineering, Mansoura University",
            "SubTitle",
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=14))

    # 1. Overview
    story.append(section_title("1. Project Overview"))
    story.append(
        p(
            "AgriPulse is a predictive-maintenance AI platform for centrifugal irrigation "
            "pumps: it learns normal pump behaviour from multi-sensor telemetry, detects "
            "early deviations, converts them into a calibrated failure-risk score with a "
            "6-to-12-hour warning horizon, and generates a standards-grounded maintenance "
            "work order through a Retrieval-Augmented Generation (RAG) engine. The full "
            "scope and 67-task execution plan are documented in <i>docs/</i>; this report "
            "covers progress on the first workstream only (WS1 — data pipeline)."
        )
    )

    # 2. Work completed
    story.append(section_title("2. Work Completed — WS1 (Data Pipeline)"))
    story.append(
        p(
            "The data pipeline (tasks T08–T13 of the plan) has been implemented and run "
            "end to end against the real 220,320-row sensor dataset — not just designed, "
            "but working, tested code producing real output."
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        status_table(
            [
                ["Task", "Deliverable", "Status"],
                ["T08 — Ingest &amp; profile dataset", "profile_report.json", "Done — verified"],
                ["T09 — Clean data &amp; sensor handling", "sensor_handling.md", "Done — policy corrected (see §3)"],
                ["T10 — Labeling (WARNING / RUL targets)", "labeling.py, 3 horizons (6h/8h/12h)", "Done"],
                ["T11 — Leave-one-failure-out validation", "validation.py, 7 folds", "Done"],
                ["T12 — Feature engineering library", "features.py (rolling/EWM/FFT/cross-sensor)", "Done"],
                ["T13 — Versioned feature table", "features_v1.parquet, 1,053 columns", "Done"],
                ["T14–T20 — Model training (anomaly, risk, RUL)", "—", "In progress"],
            ],
            col_widths=[6.3 * cm, 6.7 * cm, 3.5 * cm],
        )
    )
    story.append(Spacer(1, 4))
    story.append(p("Repository is organized by workstream (ml/, rag/, backend/, frontend/, iot/) and under git version control.", "Caption"))

    # 3. Key finding
    story.append(section_title("3. Key Finding During Data Cleaning"))
    story.append(
        highlight_box(
            "Two sensors had multi-day data gaps directly overlapping two failure events",
            [
                "The original plan called for forward-fill / linear interpolation on sensor_50 and "
                "sensor_51. Profiling the actual data showed this would have been a mistake: "
                "sensor_50 has a single ~77,000-minute (53-day) gap that swallows breakdown event #7 "
                "entirely, and sensor_51 has a ~15,356-minute (10.6-day) gap covering the full "
                "pre-failure warning window of event #5 — the largest failure in the dataset "
                "(140.5 hours of downtime).",
                "Filling gaps that size would have fabricated weeks of fake sensor readings through "
                "the exact events the model is supposed to learn from. The pipeline now leaves long "
                "gaps as missing and adds a `_was_missing` indicator column instead, and only "
                "interpolates genuinely short gaps (recalibrated threshold: 30 minutes, based on the "
                "actual gap-length distribution in the data). This is documented in "
                "ml/reports/sensor_handling.md.",
            ],
        )
    )

    # 4. Validated facts
    story.append(section_title("4. Validated Dataset Facts"))
    story.append(p("All headline numbers quoted in the planning documents were checked against the real CSV and confirmed accurate:", "Body"))
    story.append(Spacer(1, 4))
    story.append(
        status_table(
            [
                ["Claim", "Verified value"],
                ["Total rows", "220,320 (Apr 1 – Aug 31, 2018, 1-minute intervals, no gaps/duplicates)"],
                ["Sensor channels", "52 (sensor_00 .. sensor_51)"],
                ["Target distribution", "NORMAL 93.43% / RECOVERING 6.57% / BROKEN 0.003% (7 rows)"],
                ["Breakdown events", "7, timestamps match exactly to the minute"],
                ["sensor_15", "100% missing — dropped"],
            ],
            col_widths=[5.5 * cm, 11 * cm],
        )
    )

    story.append(section_title("5. Open Items Needing Supervisor / Team Input"))
    for line in [
        "<b>Dataset provenance:</b> the data's structure (perfectly regular, zero gaps/duplicates, "
        "anonymized sensor_00..51 naming) matches a known public predictive-maintenance pump "
        "dataset rather than original Egyptian field telemetry. Should be cited properly in the "
        "thesis rather than implied as proprietary field data.",
        "<b>Team &amp; supervisor fields:</b> the official university template still has placeholder "
        "names, credit hours, and GPA — needs to be filled before submission.",
        "<b>External accounts:</b> LLM API key (OpenAI/Gemini), a cloud database (TimescaleDB/Neon), "
        "and a Vercel account are needed once work reaches the RAG engine and backend/deployment "
        "stages (WS4, WS6, WS9) — not required yet.",
        "<b>Budget:</b> the ~$33 allocated for cloud/LLM tokens looks tight if development involves "
        "many iterations plus a live demo.",
    ]:
        story.append(p(f"•&nbsp;&nbsp;{line}", "BulletItem"))

    story.append(section_title("6. Next Steps"))
    story.append(
        p(
            "Proceed with T14–T20: train the baseline anomaly detectors (Isolation Forest, "
            "LSTM-Autoencoder), the supervised risk classifier (XGBoost/LightGBM), probability "
            "calibration and Green-to-Red risk levels, the persistence/hysteresis alert logic, and "
            "the RUL regressor — evaluated per failure event via the leave-one-failure-out folds "
            "already built, given only 7 total failure events are available.",
            "Body",
        )
    )

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999")))
    story.append(Spacer(1, 4))
    story.append(p("Generated from the project repository's committed code and reports — every figure above is reproducible by re-running the referenced scripts.", "Caption"))

    doc.build(story)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
