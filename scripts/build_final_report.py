"""
build_final_report.py — Generate deliverables/07_final_report.docx

Writes a professional Word document for the Correlation One Week 12
final deliverable. All numbers sourced from real Amazon LMRC 2021 data.

Run from project root: python scripts/build_final_report.py
"""

import pickle
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE       = Path(__file__).parent.parent
OUT_PATH   = BASE / "deliverables" / "07_final_report.docx"
FIGURES    = BASE / "reports" / "figures"
ML_DIR     = BASE / "ml"

# ── Load model metrics (populated by train_and_save.py) ──────────────────────
pkl_path = ML_DIR / "random_forest_model.pkl"
if pkl_path.exists():
    with open(pkl_path, "rb") as f:
        artifact = pickle.load(f)
    M = artifact["metrics"]
    AUC          = f"{M['auc_roc']:.4f}"
    AVG_PREC     = f"{M['avg_precision']:.4f}"
    RECALL_OPT   = f"{M['recall_optimized']:.4f}"
    BEST_THRESH  = f"{artifact['best_threshold']:.2f}"
    MODEL_NAME   = artifact["model_name"]
else:
    AUC = AVG_PREC = RECALL_OPT = BEST_THRESH = "—"
    MODEL_NAME = "RandomForest"

# ── Document setup ────────────────────────────────────────────────────────────
doc = Document()

# Page margins: 1" all around
sections = doc.sections
for section in sections:
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.25)
    section.right_margin  = Inches(1.25)

# ── Style helpers ──────────────────────────────────────────────────────────────
NAVY  = RGBColor(0x2C, 0x3E, 0x50)
DARK  = RGBColor(0x1A, 0x1A, 0x1A)
GREY  = RGBColor(0x55, 0x55, 0x55)


def set_heading(para, text, level=1):
    """Apply heading style without bold-for-every-paragraph pattern."""
    run = para.add_run(text)
    run.bold = True
    if level == 1:
        run.font.size = Pt(16)
        run.font.color.rgb = NAVY
    elif level == 2:
        run.font.size = Pt(13)
        run.font.color.rgb = NAVY
    else:
        run.font.size = Pt(11)
        run.font.color.rgb = DARK


def add_heading(doc, text, level=1):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(18 if level == 1 else 12)
    para.paragraph_format.space_after  = Pt(6)
    set_heading(para, text, level)
    return para


def add_body(doc, text, space_after=8):
    para = doc.add_paragraph(text)
    para.paragraph_format.space_after = Pt(space_after)
    for run in para.runs:
        run.font.size = Pt(11)
        run.font.color.rgb = DARK
    return para


def add_bullet(doc, text, level=0):
    para = doc.add_paragraph(style="List Bullet")
    para.paragraph_format.left_indent = Inches(0.3 * (level + 1))
    para.paragraph_format.space_after = Pt(4)
    run = para.add_run(text)
    run.font.size = Pt(11)
    run.font.color.rgb = DARK
    return para


def add_figure(doc, img_path, width_in=5.5, caption=None):
    if Path(img_path).exists():
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        run.add_picture(str(img_path), width=Inches(width_in))
    if caption:
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(12)
        for run in cap.runs:
            run.font.size = Pt(9)
            run.font.color.rgb = GREY
            run.font.italic = True


# ════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ════════════════════════════════════════════════════════════════════════════
title_para = doc.add_paragraph()
title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_para.paragraph_format.space_before = Pt(48)
t_run = title_para.add_run(
    "Predicting Last-Mile Delivery Failure Before the Truck Leaves"
)
t_run.bold      = True
t_run.font.size = Pt(20)
t_run.font.color.rgb = NAVY

sub_para = doc.add_paragraph()
sub_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub_run = sub_para.add_run(
    "Evidence from 3,559 Real Amazon Packages — Los Angeles, July 2018"
)
sub_run.font.size = Pt(14)
sub_run.font.color.rgb = GREY
sub_run.font.italic = True

doc.add_paragraph()

for line in [
    "Correlation One Data Analytics (DANA) — Week 12 Final Portfolio Project",
    "Dataset: Amazon Last Mile Routing Research Challenge (LMRC 2021)",
    "April 2026",
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(line)
    r.font.size = Pt(11)
    r.font.color.rgb = GREY

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════
# 1. INTRODUCTION
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "1. Introduction", level=1)

add_body(doc,
    "Every failed last-mile delivery attempt has a cost that goes well beyond the obvious "
    "inconvenience. When a driver cannot complete a delivery — because no one is home, "
    "an address is inaccessible, or a package is rejected on arrival — the downstream "
    "consequences stack up quickly: a redelivery attempt that burns fuel and driver time, "
    "a customer service interaction that may or may not resolve the situation, and a "
    "negative hit to the customer's perception of the service. Industry estimates put the "
    "all-in cost at roughly $17 per failed attempt once all three categories are accounted "
    "for. At any meaningful scale, even a sub-1% failure rate translates to material "
    "operational waste."
)

add_body(doc,
    "The conventional response to delivery failures is reactive: operations teams analyze "
    "DPMO (Defects Per Million Opportunities) reports after failures occur, identify "
    "patterns in the prior week's data, and adjust routing or carrier assignments for the "
    "following week. This lag matters. A driver assigned to a high-risk route on a Monday "
    "morning will attempt those deliveries regardless of what the Friday report later "
    "reveals about that route's historical failure profile."
)

add_body(doc,
    "This project addresses that gap directly. Using real operational data from the Amazon "
    "Last Mile Routing Research Challenge (LMRC 2021) — 3,559 packages across 15 routes "
    "in Los Angeles, July 2018 — we built a pre-dispatch failure prediction model: one that "
    "scores packages before the truck leaves the station, using only features available at "
    "that moment. The goal is to move failure prevention upstream, from post-hoc analysis "
    "to dispatch-time intervention."
)

add_heading(doc, "Business Case", level=2)

add_body(doc,
    "The dataset covers 15 Los Angeles routes in July 2018. Of 3,559 packages tracked, "
    "25 resulted in a DELIVERY_ATTEMPTED outcome — a failure rate of 0.70%. At first "
    "glance this seems low, but across a full-scale delivery network operating thousands "
    "of routes daily, that rate compounds. More importantly, the failures are not uniformly "
    "distributed: certain carriers, certain shifts, and certain route types fail at rates "
    "two to three times the overall average — and those patterns are knowable before dispatch."
)

add_body(doc,
    "This project differs from existing routing optimization work in one important way: "
    "we are not optimizing the sequence of stops on a route (Amazon's own routing "
    "challenge). We are asking a different question — given the carrier, the shift, the "
    "route geography, and the package type, what is the probability that this specific "
    "delivery will fail? — and answering it before the truck is loaded."
)

# ════════════════════════════════════════════════════════════════════════════
# 2. DATA ANALYSIS & COMPUTATION
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "2. Data Analysis and Computation", level=1)

add_heading(doc, "2.1 Dataset Description", level=2)

add_body(doc,
    "The Amazon Last Mile Routing Research Challenge (LMRC) dataset is publicly available "
    "at s3://amazon-last-mile-challenges. It contains real operational data from Amazon "
    "delivery routes across several U.S. cities. For this project, we extracted the first "
    "15 routes from the Los Angeles subset of the July 2018 training data, yielding 3,559 "
    "package-level records."
)

add_body(doc,
    "Each package record captures twelve features available at dispatch time:"
)

for feat, desc in [
    ("package_id", "Unique identifier — excluded from modeling"),
    ("package_type", "Standard vs. high_value (derived from package dimensions)"),
    ("shift", "Departure time window — morning (06:00–14:00) or afternoon (14:00–22:00)"),
    ("carrier", "Carrier code: A, B, C, or D — derived from station code prefix"),
    ("route_distance_km", "Total haversine route distance across all stops"),
    ("packages_in_route", "Total packages on the same route"),
    ("weather_risk", "Month-derived risk: July = low (zero variance — all 'low')"),
    ("days_in_fc", "Days since time-window start — all zero (zero variance)"),
    ("double_scan", "Package recorded at more than one stop in the route"),
    ("short_service_time", "Planned service time < 25s — locker/dense-urban indicator (dispatch-time signal)"),
    ("delivery_failed", "IS the target variable — excluded as a feature"),
    ("cr_number_missing", "No time window on file — 91% positive in this dataset"),
]:
    add_bullet(doc, f"{feat}: {desc}")

add_heading(doc, "2.2 Data Wrangling Decisions", level=2)

add_body(doc,
    "Three wrangling decisions shaped the entire analysis, and each deserves explicit "
    "justification rather than a quiet mention in a footnotes section."
)

add_body(doc,
    "The first decision was renaming the target column from damaged_on_arrival to delivery_failed "
    "for semantic clarity, and excluding it as a feature. This column is the delivery failure — "
    "not a predictor of it. In the LMRC source data, build_dataset.py sets delivery_failed = 1 "
    "when the package's scan_status is 'DELIVERY_ATTEMPTED'. Using this as an input feature would "
    "make the model appear accurate while predicting the exact thing it was already given. It is "
    "excluded entirely and serves only as the target."
)

add_body(doc,
    "The second decision was excluding days_in_fc and weather_risk. Both columns have zero "
    "variance across all 3,559 rows. Every package has days_in_fc = 0 (all dispatched on "
    "the same day their time window began), and every package has weather_risk = 'low' "
    "(July in Los Angeles). Columns with zero variance carry no signal — including them "
    "as features would silently waste model capacity and confuse any feature importance "
    "interpretation."
)

add_body(doc,
    "The third decision was the distance bucketing. Route distance in kilometers is a "
    "continuous variable, but delivery operations think in discrete zones: dense urban "
    "(short), suburban, and exurban (long). Three buckets — below 40 km, 40 to 60 km, "
    "and above 60 km — map to these operational zones and proved to reveal a pattern "
    "invisible in the raw continuous variable."
)

add_heading(doc, "2.3 EDA Findings", level=2)

add_body(doc,
    "The exploratory analysis produced four findings that meaningfully shaped the modeling "
    "decisions. Three were expected; one was not."
)

add_heading(doc, "Carrier", level=3)
add_body(doc,
    "carrier_D has the highest failure rate at 1.39% — nearly double the 0.70% overall "
    "average. carrier_B, by contrast, had zero failures across 412 packages. carrier_A "
    "sits at 0.74% and carrier_C at 0.34%. Carrier identity is the strongest structural "
    "predictor in the dataset: it captures driver experience, technology maturity, SLA "
    "standards, and geographic specialization simultaneously."
)
add_figure(doc, FIGURES / "failure_rate_by_carrier.png", width_in=5.0,
           caption="Figure 1. Delivery failure rate by carrier. carrier_D has nearly 2× the average failure rate; carrier_B has zero failures.")

add_heading(doc, "Shift", level=3)
add_body(doc,
    "Morning shift routes fail at 1.37% versus 0.55% for afternoon routes. Only two shifts "
    "are represented in these 15 LA routes — there are no night routes in this dataset. "
    "The morning gap is consistent with a simple occupancy effect: in dense Los Angeles "
    "neighborhoods, morning deliveries land when residents have left for work, reducing "
    "the likelihood of someone available to accept packages that require access codes, "
    "signatures, or building entry."
)
add_figure(doc, FIGURES / "failure_rate_by_shift.png", width_in=5.0,
           caption="Figure 2. Morning shift failure rate (1.37%) is 2.5× higher than afternoon (0.55%).")

add_heading(doc, "Route Distance — The Urban Density Paradox", level=3)
add_body(doc,
    "Routes under 40 km fail at 1.89% — the highest of any distance bucket. Routes between "
    "40 and 60 km fail at 0.28%. Routes above 60 km fail at 0.00%. This is the most "
    "counterintuitive finding in the dataset, and it required a second look before we "
    "accepted it."
)
add_body(doc,
    "The instinct is that longer, more complex routes should fail more: more stops, more "
    "distance, more opportunity for things to go wrong. The data says the opposite. The "
    "likely explanation is geographic: short routes in Los Angeles run through dense "
    "multi-family residential areas where access barriers — locked lobbies, key-fob "
    "entry, Amazon Locker congestion — prevent delivery completion. Longer routes reach "
    "lower-density areas where single-family homes with driveways and ground-level "
    "delivery points are the norm. The barrier is access, not distance."
)
add_figure(doc, FIGURES / "failure_rate_by_distance.png", width_in=5.0,
           caption="Figure 3. Urban Density Paradox: routes under 40 km fail more than routes twice their length.")

add_heading(doc, "Class Imbalance", level=3)
add_body(doc,
    "25 failures out of 3,559 packages produces a ~140:1 class ratio. This makes standard "
    "accuracy meaningless as a metric: a model that always predicts 'delivered' would "
    "score 99.3% accuracy while catching zero failures. All modeling decisions — metric "
    "choice, class weighting, oversampling, and threshold tuning — flow from this "
    "imbalance."
)
add_figure(doc, FIGURES / "class_imbalance.png", width_in=5.5,
           caption="Figure 4. 25 failures vs 3,534 deliveries — a ~140:1 class ratio requiring recall-focused evaluation.")

add_heading(doc, "2.4 Modeling Methodology", level=2)

add_body(doc,
    "We used a Random Forest classifier for three practical reasons: it handles mixed "
    "feature types without extensive preprocessing, it natively supports class weighting "
    "for imbalanced targets, and its feature importance output is interpretable to "
    "non-technical operations stakeholders."
)

add_body(doc,
    "With class_weight='balanced', the RandomForest reweights each failure observation "
    "by approximately 140 times the weight of a successful delivery. This prevents the "
    "model from defaulting to the majority class and forces it to learn the minority "
    "signal even with very few positive examples."
)

add_body(doc,
    "We also compared a SMOTE (Synthetic Minority Oversampling) variant, which generates "
    "synthetic failure records in feature space to balance the training set before fitting "
    "the model. The SMOTE model was trained without class weighting but on a resampled "
    "training set."
)

add_body(doc,
    "Threshold optimization was applied to the winning model. The default 0.5 probability "
    "threshold is calibrated for balanced classes. At 0.7% failure rate, it will "
    "underclassify failures. We swept thresholds from 0.05 to 0.95 and selected the "
    "cutoff that maximized recall while maintaining non-zero precision."
)

add_heading(doc, "2.5 Model Results", level=2)

add_body(doc,
    f"The {MODEL_NAME} model achieved the following performance on the held-out test set "
    f"(712 packages, 5 failures):"
)

# Results table
table = doc.add_table(rows=5, cols=2)
table.style = "Table Grid"
headers = ["Metric", "Value"]
rows_data = [
    ("AUC-ROC", AUC),
    ("Average Precision", AVG_PREC),
    (f"Recall at threshold {BEST_THRESH}", RECALL_OPT),
    ("Model", MODEL_NAME),
]
for i, (k, v) in enumerate([("Metric", "Value")] + rows_data):
    row = table.rows[i]
    row.cells[0].text = k
    row.cells[1].text = v
    if i == 0:
        for cell in row.cells:
            for run in cell.paragraphs[0].runs:
                run.bold = True

doc.add_paragraph()

add_body(doc,
    f"An AUC-ROC of {AUC} indicates meaningful discrimination — the model is substantially "
    "better than random at distinguishing packages that will fail from those that will not. "
    f"At the optimized threshold of {BEST_THRESH}, the model correctly identifies "
    f"{float(RECALL_OPT)*100:.0f}% of failures in the test set. The precision is low "
    "(as expected with 140:1 imbalance), meaning many flagged packages will not actually "
    "fail — but the cost of a false alarm (a quick manual review) is far lower than the "
    "cost of a missed failure ($17 per incident)."
)

add_figure(doc, FIGURES / "feature_importance_final.png", width_in=5.5,
           caption="Figure 5. Model-based feature importance (mean decrease in Gini impurity). carrier_enc and dist_bucket are the dominant predictors.")

# ════════════════════════════════════════════════════════════════════════════
# 3. GENAI USAGE
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "3. Generative AI Usage", level=1)

add_body(doc,
    "This project used two categories of generative AI tools, and this section documents "
    "both transparently per Correlation One program guidelines."
)

add_heading(doc, "Claude (Anthropic)", level=2)
add_body(doc,
    "Claude was used throughout the project in the following capacities:"
)
for use in [
    "Drafting and iterating on all written deliverables (project description, scoping document, data curation report, EDA report, and this final report)",
    "Code review: reviewing Python scripts for bugs, data leakage, and logical errors before execution",
    "Analytical reasoning: working through the interpretation of counterintuitive findings such as the urban density paradox",
    "Documentation: writing docstrings, inline comments, and README content",
]:
    add_bullet(doc, use)

add_body(doc,
    "All analytical conclusions — numbers, findings, and interpretations — were validated "
    "against the actual data outputs before being incorporated into any deliverable. Claude "
    "was used as a writing and reasoning partner, not as a substitute for running the "
    "analysis. Every finding cited in this report is traceable to a specific output from "
    "notebooks/04_eda_validation.ipynb or the model training script."
)

add_heading(doc, "CrewAI Agents", level=2)
add_body(doc,
    "The agents_crew.py module implements a CrewAI-based agent that generates per-package "
    "executive risk reports. Given a package's feature values and the trained model's "
    "predicted failure probability, the agent produces a natural-language risk assessment "
    "formatted for a dispatch supervisor: the risk tier, the primary contributing factors, "
    "and an actionable recommendation (hold for review, proceed normally, or reassign to "
    "a different carrier)."
)
add_body(doc,
    "The CrewAI integration represents the operational deployment layer of the model. "
    "Rather than requiring dispatchers to read probability scores, the agent translates "
    "model outputs into plain-language briefings suitable for the morning S&OP workflow."
)

# ════════════════════════════════════════════════════════════════════════════
# 4. CHALLENGES AND SOLUTIONS
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "4. Challenges and Solutions", level=1)

add_heading(doc, "4.1 Zero-Variance Variables", level=2)
add_body(doc,
    "Two features that were designed to carry meaningful signal — days_in_fc and "
    "weather_risk — turned out to be completely uninformative in this dataset. days_in_fc "
    "is zero for every package (all dispatched on the day their time window began), and "
    "weather_risk is 'low' for every package (July in Los Angeles)."
)
add_body(doc,
    "This is a dataset limitation rather than a feature engineering failure. A broader "
    "dataset covering multiple months or multiple geographies would restore variance to "
    "both columns and potentially reveal meaningful signal. For this project, both columns "
    "were identified in the EDA profiling step and explicitly excluded before modeling, "
    "with the exclusion documented and justified rather than silently dropped."
)

add_heading(doc, "4.2 Class Imbalance (140:1)", level=2)
add_body(doc,
    "25 failures in 3,559 packages is an extreme class imbalance for a classification "
    "problem. Standard accuracy becomes meaningless, standard train/test splits risk "
    "putting all failures in one partition, and standard probability thresholds will "
    "systematically underclassify the minority class."
)
add_body(doc,
    "Three solutions were applied sequentially. Stratified splitting preserved the 0.7% "
    "failure rate in both the training and test partitions. class_weight='balanced' "
    "re-weighted each failure observation during model training. SMOTE oversampling "
    "provided a comparison point that generates synthetic failures in feature space. "
    "Finally, threshold optimization decoupled the prediction threshold from its "
    "imbalance-driven default of 0.5."
)

add_heading(doc, "4.3 Data Leakage — Removed in This Version", level=2)
add_body(doc,
    "Two features in earlier versions of the dataset were conditioned on the outcome "
    "(failed delivery) and therefore constituted data leakage. The first, locker_issue, "
    "was defined as svc_sec < 25 AND failed — meaning it could only ever equal 1 when "
    "a failure occurred, so the model was learning from the failure itself. The second, "
    "damaged_on_arrival, was a direct alias of the target variable."
)
add_body(doc,
    "Both were removed in the current version. locker_issue was replaced by "
    "short_service_time (= 1 if planned service time < 25 seconds, regardless of outcome) "
    "— a clean dispatch-time signal for locker/dense-urban stops. damaged_on_arrival was "
    "renamed delivery_failed to clarify its role as the target variable and prevent "
    "accidental inclusion as a feature. All model artifacts were retrained on the clean dataset."
)

add_heading(doc, "4.4 Small Sample Size for 0.7% Event", level=2)
add_body(doc,
    "Training a binary classifier on 25 positive examples is genuinely difficult. With "
    "an 80/20 stratified split, the training set contains only 20 failures. SMOTE "
    "addresses this by generating synthetic minority-class examples, but the underlying "
    "issue — that 15 routes in one month is a small observation window for a rare event "
    "— remains. The model results should be interpreted as directionally correct rather "
    "than precisely calibrated, and the analysis explicitly notes where scaling to the "
    "full LMRC dataset would improve confidence."
)

# ════════════════════════════════════════════════════════════════════════════
# 5. DASHBOARD DESCRIPTION
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "5. Dashboard Description", level=1)

add_body(doc,
    "The Streamlit dashboard (dashboard/dashboard.py) provides an operational interface "
    "for dispatch supervisors. It is designed for the morning S&OP workflow — the "
    "pre-dispatch review window when intervention is still possible."
)

add_heading(doc, "Use Case", level=2)
add_body(doc,
    "A dispatch supervisor opens the dashboard at 07:00 before routes are loaded. The "
    "Operations Overview page shows today's KPI summary: how many packages are flagged "
    "as high-risk, which carriers have elevated predicted failure rates, and which "
    "routes have the highest concentration of risk factors. The supervisor can drill into "
    "the Package Risk Scoring page, enter a package ID, and receive a risk tier (Low / "
    "Medium / High) with the contributing factors explained in plain language."
)

add_heading(doc, "Dashboard Pages", level=2)
for page, desc in [
    ("Operations Overview",
     "KPI cards showing total packages, predicted failures, and average risk probability. "
     "Bar charts for failure rate by carrier and shift. Carrier-by-weather-risk heatmap."),
    ("Package Risk Scoring",
     "Real-time single-package scoring tool. Enter carrier, shift, package type, route "
     "distance, and other features to get an instant risk tier and probability score."),
    ("Route Analysis",
     "Distance vs. failure rate scatter plot, route bucket analysis, carrier comparison. "
     "Helps route planners identify geographic concentrations of high-risk packages."),
]:
    add_bullet(doc, f"{page}: {desc}")

add_body(doc,
    "Tableau Public link: [placeholder — dashboard to be published after final submission]"
)

# ════════════════════════════════════════════════════════════════════════════
# 6. CONCLUSIONS AND FUTURE WORK
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "6. Conclusions and Future Work", level=1)

add_heading(doc, "6.1 Top Three Actionable Findings", level=2)

add_body(doc,
    "Three findings from this analysis are immediately actionable by an Amazon LA "
    "operations team, in order of operational tractability:"
)

add_bullet(doc,
    "1. Flag carrier_D + morning + route under 40 km as the highest-risk combination. "
    "All three top risk factors coincide in this segment. A pre-dispatch supervisor review "
    "for packages meeting all three criteria would catch the highest-density cluster of "
    "predicted failures at the lowest false-alarm rate.")

add_bullet(doc,
    "2. Redistribute carrier_D's densest urban routes to carrier_B or carrier_A where "
    "capacity allows. carrier_B ran 412 packages with zero failures in this dataset. "
    "Even a partial reallocation of carrier_D's sub-40 km morning routes would reduce "
    "the failure count.")

add_bullet(doc,
    "3. Implement a morning-shift access-verification protocol for dense routes. "
    "Confirm delivery access codes, intercom availability, and Amazon Locker status "
    "before route loading for packages on routes under 40 km. The barrier is access, "
    "not driver performance, and access information is resolvable before dispatch.")

add_heading(doc, "6.2 Model Implications", level=2)
add_body(doc,
    f"The {MODEL_NAME} model achieves AUC-ROC = {AUC} — meaningful discrimination "
    "for a 0.7% event with only 25 training failures. At the optimized threshold of "
    f"{BEST_THRESH}, recall reaches {float(RECALL_OPT)*100:.0f}%, meaning the model "
    "correctly identifies the majority of real failures. Precision is low (expected at "
    "this class ratio), but the asymmetric cost structure justifies this: the cost of "
    "a missed failure ($17) is far greater than the cost of a false alarm (supervisor "
    "review taking under two minutes)."
)
add_body(doc,
    "Scaling to the full LMRC dataset — approximately 6,000 routes covering multiple "
    "U.S. cities — would provide sufficient failure examples to train a more robust "
    "model without relying on SMOTE synthetic oversampling. The current model's results "
    "should be treated as directionally correct and directionally consistent with the "
    "EDA findings, but not as a calibrated production scoring system."
)

add_heading(doc, "6.3 Future Work", level=2)

for item in [
    "Scale to full LMRC dataset: The full Amazon LMRC 2021 dataset covers ~6,000 routes. "
    "Scaling from 15 routes to the full dataset would provide statistically robust failure "
    "counts without synthetic oversampling.",

    "Barcelona Open Data validation layer: A planned extension would test whether the "
    "urban-density failure pattern generalizes to other delivery markets using Barcelona "
    "Open Data (accident risk by neighborhood, traffic congestion by shift). This "
    "cross-geography validation would strengthen the finding that access barriers — "
    "not route complexity — drive short-route failures.",

    "CrewAI agent full deployment: Integrate the trained model output as a tool input to "
    "the CrewAI agent in agents_crew.py, enabling fully automated per-package executive "
    "reports formatted for the dispatch supervisor's morning briefing.",

    "Feature expansion: Add real-time traffic signals (if available at dispatch time), "
    "building type (single-family vs. multi-family), and historical carrier performance "
    "on specific route segments as additional features.",

    "Production retraining loop: Collect 3 months of production prediction-and-outcome "
    "data and retrain the model with the feedback loop, tracking whether the model's "
    "identified risk factors remain stable over time.",
]:
    add_bullet(doc, item)

# ── Footer ─────────────────────────────────────────────────────────────────────
doc.add_paragraph()
footer_para = doc.add_paragraph(
    "Amazon Last Mile Routing Research Challenge (LMRC 2021) — public dataset, "
    "s3://amazon-last-mile-challenges  |  "
    "Correlation One Data Analytics (DANA) — Week 12  |  April 2026"
)
footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in footer_para.runs:
    run.font.size = Pt(9)
    run.font.color.rgb = GREY
    run.font.italic = True

# ── Save ───────────────────────────────────────────────────────────────────────
doc.save(str(OUT_PATH))
print(f"\n  Final report saved -> {OUT_PATH}")
print(f"  File size: {OUT_PATH.stat().st_size / 1024:.1f} KB")
