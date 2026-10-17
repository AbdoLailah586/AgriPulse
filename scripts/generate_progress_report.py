"""Generate a short, supervisor-facing PDF progress report for AgriPulse.

Run: ../.venv/Scripts/python generate_progress_report.py
Output: ../reports/AgriPulse_Progress_Report_v2.pdf
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
OUT_PATH = ROOT / "reports" / "AgriPulse_Progress_Report_v2.pdf"

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
            "covers progress on the first two workstreams: WS1 (data pipeline) and WS2 "
            "(model training &amp; evaluation)."
        )
    )

    # 2. Work completed — WS1
    story.append(section_title("2. Work Completed — WS1 (Data Pipeline)"))
    story.append(
        p(
            "Tasks T08–T13 of the plan: implemented and run end to end against the real "
            "220,320-row sensor dataset — not just designed, but working, tested code "
            "producing real output."
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        status_table(
            [
                ["Task", "Deliverable", "Status"],
                ["T08 — Ingest &amp; profile dataset", "profile_report.json", "Done — verified"],
                ["T09 — Clean data &amp; sensor handling", "sensor_handling.md", "Done — policy corrected (see §4)"],
                ["T10 — Labeling (WARNING / RUL targets)", "labeling.py, 3 horizons (6h/8h/12h)", "Done"],
                ["T11 — Leave-one-failure-out validation", "validation.py, 7 folds", "Done"],
                ["T12 — Feature engineering library", "features.py (rolling/EWM/FFT/cross-sensor)", "Done"],
                ["T13 — Versioned feature table", "features_v1.parquet, 1,053 columns", "Done"],
            ],
            col_widths=[6.3 * cm, 6.7 * cm, 3.5 * cm],
        )
    )
    story.append(Spacer(1, 4))
    story.append(p("Repository is organized by workstream (ml/, rag/, backend/, frontend/, iot/) and under git version control.", "Caption"))

    # 2b. Work completed — WS2
    story.append(section_title("3. Work Completed — WS2 (Model Training &amp; Evaluation)"))
    story.append(
        p(
            "Tasks T14–T20: every model is trained and evaluated leave-one-failure-out "
            "(7 folds — one real failure event held out per fold, never seen in that "
            "fold's training data). All numbers below are real, reproducible results, "
            "not placeholders or projections."
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        status_table(
            [
                ["Task", "Headline result", "Status"],
                ["T14 — Anomaly baselines (IsoForest/PCA/Mahalanobis)", "1–2 / 7 events detected", "Done"],
                ["T15 — LSTM-Autoencoder", "1 / 7 detected (first pass, 4 epochs)", "Done"],
                ["T16 — Supervised risk (XGBoost/LightGBM)", "3 / 7 detected — see bug note (§4)", "Done"],
                ["T17 — Calibration + Green/Yellow/Orange/Red levels", "isotonic calibration", "Done"],
                ["T18 — Persistence/hysteresis alert logic", "self-tested, no false flicker", "Done"],
                ["T19 — RUL regressor", "MAE ~194 min on a 720-min horizon", "Done"],
                ["T20 — Model registry &amp; model card", "ml/models/v1/model_card.json", "Done"],
            ],
            col_widths=[7.3 * cm, 6.2 * cm, 3 * cm],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        p(
            "Detection rates look modest (best model: 3/7) — this is honest, not a weak "
            "result: with only 7 failure events total, a leave-one-failure-out fold tests "
            "genuine generalization to an event the model never saw, which is a much "
            "harder and more meaningful bar than in-sample accuracy.",
            "Caption",
        )
    )

    # 4. Key findings
    story.append(section_title("4. Key Findings During Engineering"))
    story.append(
        highlight_box(
            "Finding 1 — two sensors had multi-day data gaps directly overlapping two failure events",
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
                "actual gap-length distribution in the data). Documented in ml/reports/sensor_handling.md.",
            ],
        )
    )
    story.append(Spacer(1, 10))
    story.append(
        highlight_box(
            "Finding 2 — a calibration bug made the first model results falsely look perfect",
            [
                "The first T16/T17 run reported a suspicious \"perfect\" result: every one of the 7 "
                "held-out failures detected, every single one at the very first minute of its "
                "12-hour warning window. That pattern — not gradual, not varying per event — was the "
                "tell that something was wrong rather than something to celebrate.",
                "Root cause: isotonic probability calibration collapsed the near-perfectly-separated "
                "NORMAL class to a calibrated probability of exactly 0.0, which made the 99th-"
                "percentile alert threshold also exactly 0.0 — and since a probability can never be "
                "negative, literally every row in the dataset trivially satisfied \"score &gt;= 0\". "
                "Fixed by computing the alert threshold from the raw, uncalibrated probability "
                "instead. The honest, real result after the fix is 3/7 (§3). See "
                "ml/src/supervised_risk.py for the full writeup.",
            ],
        )
    )

    # 5. Validated facts
    story.append(section_title("5. Validated Dataset Facts"))
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

    story.append(section_title("6. Open Items Needing Supervisor / Team Input"))
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

    story.append(section_title("7. Next Steps"))
    story.append(
        p(
            "WS3 (T21–T25): SHAP-based explainability on the risk model, per-sensor reconstruction "
            "error from the autoencoder, and formal event-level evaluation reporting with ablations. "
            "Then WS4 (T26–T33): build the knowledge base (ISO 10816-3, FMEA, O&amp;M manuals) and the "
            "RAG engine — this is where the LLM API key noted in §6 becomes necessary.",
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
