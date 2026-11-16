"""Build the final report (.docx) in the BSFS report format.

Run from the repository root, after report/make_figures.py:
    python report/build_report.py
Inputs:  report/bsfs_template.docx (BSFS header, logos and styles; empty body),
         report/figures/*.png, results/final_comparison/*.csv
Output:  report/Graph_ML_Money_Laundering_Report.docx

Text marked with [TODO ...] is highlighted yellow and must be filled in or deleted before submission.
"""
from copy import deepcopy
from pathlib import Path
import re

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
INK = RGBColor(0x18, 0x18, 0x18)
SECTION_NUMBERING = "2"   # the template's "1. HEADING" list

doc = docx.Document(REPORT / "bsfs_template.docx")
body = doc.element.body
for el in list(body):
    if el.tag != qn("w:sectPr"):
        body.remove(el)


def _run(p, text, bold=False, italic=False, size=12, font="Calibri", color=INK, underline=False):
    r = p.add_run(text)
    r.bold, r.italic, r.underline = bold, italic, underline
    r.font.size, r.font.name, r.font.color.rgb = Pt(size), font, color
    r._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    if "[TODO" in text:
        r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return r


def _rich(p, text, size=12, italic=False):
    """**bold**, *italic* and `code` inline markup."""
    for part in re.split(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)", text):
        if part.startswith("**"):
            _run(p, part[2:-2], bold=True, size=size, italic=italic)
        elif part.startswith("`"):
            _run(p, part[1:-1], size=size - 1, font="Consolas", italic=italic)
        elif part.startswith("*"):
            _run(p, part[1:-1], italic=True, size=size)
        elif part:
            _run(p, part, size=size, italic=italic)


def _para(before=0, after=180, align=WD_ALIGN_PARAGRAPH.JUSTIFY, keep_next=False):
    p = doc.add_paragraph()
    f = p.paragraph_format
    f.space_before, f.space_after, f.alignment, f.keep_with_next = Pt(before / 20), Pt(after / 20), align, keep_next
    return p


def title(*lines):
    for line in lines:
        p = _para(after=180, align=WD_ALIGN_PARAGRAPH.CENTER)
        p.style = doc.styles["Title"]
        _run(p, line, bold=True, size=17, font="Libre Baskerville")


def meta(label, value):
    p = _para(after=0, align=WD_ALIGN_PARAGRAPH.LEFT)
    _run(p, label + ":", bold=True)
    text, _, todo = value.partition(" [TODO")
    _run(p, " " + text, italic=True)
    if todo:
        _run(p, " [TODO" + todo, italic=True)


def heading(text, numbered=True):
    p = _para(before=360, after=180, keep_next=True)
    if numbered:
        pPr = p._p.get_or_add_pPr()
        num = OxmlElement("w:numPr")
        for tag, val in (("w:ilvl", "0"), ("w:numId", SECTION_NUMBERING)):
            el = OxmlElement(tag); el.set(qn("w:val"), val); num.append(el)
        pPr.insert(0, num)
        p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Cm(1.27), Cm(-0.63)
    _run(p, text.upper(), bold=True)


def sub(text):
    p = _para(before=240, after=60, keep_next=True)
    _run(p, text, bold=True)


def para(text):
    _rich(_para(after=180), text)


def bullets(items):
    for item in items:
        p = _para(after=80)
        p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Cm(0.9), Cm(-0.45)
        _run(p, "–  ")
        _rich(p, item)


FIGURES = 0


def figure(name, caption, width=16.0):
    global FIGURES
    FIGURES += 1
    p = _para(before=120, after=40, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
    p.add_run().add_picture(str(REPORT / "figures" / f"{name}.png"), width=Cm(width))
    c = _para(after=200, align=WD_ALIGN_PARAGRAPH.CENTER)
    _run(c, f"Figure {FIGURES}. ", bold=True, size=10, color=RGBColor(0x40, 0x40, 0x40))
    _rich(c, caption, size=10)


TABLES = 0


def _borders(cell, top=None, bottom=None):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for side, sz in (("top", top), ("bottom", bottom)):
        if sz:
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), "181818")
            b.append(e)
    tcPr.append(b)


def table(caption, header, rows, widths_cm):
    global TABLES
    TABLES += 1
    c = _para(before=120, after=60, align=WD_ALIGN_PARAGRAPH.LEFT, keep_next=True)
    _run(c, f"Table {TABLES}. ", bold=True, size=10, color=RGBColor(0x40, 0x40, 0x40))
    _rich(c, caption, size=10)
    t = doc.add_table(rows=len(rows) + 1, cols=len(header))
    t.alignment, t.autofit = WD_TABLE_ALIGNMENT.CENTER, False
    layout = OxmlElement("w:tblLayout"); layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    for col, w in zip(t.columns, widths_cm):
        col.width = Cm(w)
    for r_i, values in enumerate([header] + rows):
        for c_i, v in enumerate(values):
            cell = t.cell(r_i, c_i)
            cell.width = Cm(widths_cm[c_i])
            p = cell.paragraphs[0]
            f = p.paragraph_format
            f.space_before, f.space_after, f.line_spacing, f.keep_with_next = Pt(1), Pt(1), 1.0, r_i < len(rows)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_i == 0 else WD_ALIGN_PARAGRAPH.CENTER
            _rich(p, f"**{v}**" if r_i == 0 else str(v), size=9)
            _borders(cell, top=8 if r_i == 0 else None,
                     bottom=6 if r_i == 0 else (8 if r_i == len(rows) else None))
    _para(after=120)


def source(text):
    p = _para(after=120)
    p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Cm(0.6), Cm(-0.6)
    _rich(p, text, size=11)


# ----------------------------------------------------------------------------- data for tables
RES = ROOT / "results" / "final_comparison"
NAMES = {"RandomForest_Role2": "Random Forest (R2)", "RandomForest_Role3": "Random Forest (R3)",
         "GCN": "GCN", "GraphSAGE": "GraphSAGE", "GAT": "GAT", "MLP": "MLP (no graph)"}
summary = pd.read_csv(RES / "summary.csv").set_index("model").loc[list(NAMES)]
counts = pd.read_csv(RES / "runs.csv").groupby("model")[["tp", "fp", "fn"]].mean().loc[list(NAMES)]
topk = pd.read_csv(RES / "precision_at_k_runs.csv").groupby("model").mean().loc[list(NAMES)]
main_rows = [[NAMES[m], f"{s.average_precision_mean:.3f} ± {s.average_precision_std:.3f}",
              f"{s.f1_illicit_mean:.3f} ± {s.f1_illicit_std:.3f}", f"{s.precision_illicit_mean:.2f}",
              f"{s.recall_illicit_mean:.2f}", f"{counts.loc[m, 'tp'] + counts.loc[m, 'fp']:,.0f}",
              f"{counts.loc[m, 'fp']:,.0f}", f"{counts.loc[m, 'fn']:,.0f}",
              f"{s.f1_before_shift_mean:.2f}", f"{s.f1_after_shift_mean:.2f}"] for m, s in summary.iterrows()]
topk_rows = [[NAMES[m]] + [f"{topk.loc[m, f'precision_at_{k}']:.0%}" for k in (100, 250, 500, 1000)] for m in NAMES]

# ----------------------------------------------------------------------------- document
title("Graph Machine Learning for Finding Money Laundering:", "Does the Transaction Graph Help?")
meta("Academic Year", "2026-2027")
meta("Association", "Bocconi Students Fintech Society × Bocconi Students Machine Learning")
meta("Team Leader", "Loukas Iatrou [TODO degree programme]")
meta("Authors", "Ahaan Dhawan, Jessica Zainea Pop, Gioia Cancian, Giulio D'Aversa [TODO degree programmes]")
meta("Code and data", "github.com/LoukasIatrou/ML-project")

p = _para(before=360, after=180); _run(p, "ABSTRACT", bold=True)
para("Money laundering disguises the criminal origin of funds. Public blockchains such as Bitcoin make every payment visible but pseudonymous, which makes them a natural test bed for machine learning on transaction networks. This report asks whether learning on the **Bitcoin transaction graph** detects illicit activity better than models that look at each transaction on its own.")
para("We use the public **Elliptic dataset** (203,769 transactions over 49 time steps) and a strict temporal split. Models learn from time steps 1–34 and are tested on 35–49. Classical baselines and three graph neural networks (GCN, GraphSAGE, GAT) were trained with five random seeds each. All 30 runs were scored by one shared evaluation program on the same 16,670 labelled test transactions.")
para("**Random Forests on the transaction features are clearly the best models**, with an average precision of 0.79 and an illicit-class F1 of up to 0.82. The best graph neural network reaches 0.53 and 0.55. Training on the graph does help a neural network (average precision 0.53 against 0.33 without the graph), but a trained network no longer needs the edges when it makes predictions. **Every model fails after a dark market is shut down at time step 43**: F1 falls from up to 0.91 to at most 0.03. SHAP explanations show that the features which signalled illicit activity before the shutdown point towards licit activity afterwards.")
para("For anti-money-laundering practice, the results suggest that monitoring for changes in criminal behaviour and setting alert thresholds from investigators' capacity matter more than the choice between the models we tested. The best model's 500 highest-risk alerts were all correct.")

heading("Introduction and AML context")
para("Money laundering is the process of hiding the illegal origin of funds so that they appear legitimate (UNODC). It typically moves money through many intermediate transactions to break the trail between source and destination. With cryptocurrencies, every payment is recorded on a public ledger, so investigators can follow the whole flow of funds even though the people behind the addresses are unknown.")
para("A transaction network records how payments connect as well as what each payment looks like. **Graph neural networks (GNNs)** learn from both by passing information along the edges of the network. Weber et al. (2019) released the Elliptic dataset to test this idea. They found that a Random Forest on the transaction features outperformed graph convolutional networks, and that every model failed after a large dark market closed.")
para("We revisit their question with a shared, reproducible protocol: **does learning on the transaction graph beat models that look at each transaction in isolation?** Throughout, a model's output is treated as a **triage signal**: a ranked list of transactions for a human investigator to review, rather than an accusation or an automated decision. We therefore report how well models rank transactions and how many alerts they raise, in addition to F1.")
para("[TODO optional: one paragraph on AML typologies (placement, layering, integration) and on why layering through chains of transactions suits graph methods, citing Altman et al. (2023).]")

heading("Data")
para("*Role 1 – Ahaan Dhawan. The full data card is in the project repository.*")
sub("2.1 The Elliptic dataset")
para("Each node of the graph is a Bitcoin transaction and each directed edge a flow of bitcoin from one transaction to another. There are **203,769 transactions** and **234,355 edges**. Every transaction belongs to one of 49 time steps, about two weeks each, and has **165 anonymised features**. The first 93 describe the transaction itself (*local* features). The other 72 summarise its one-hop neighbourhood (*aggregated* features). Every edge connects two transactions in the same time step, so splitting the data by time removes no edges.")
sub("2.2 Labels and class imbalance")
para("Only 4,545 transactions (2.2%) are labelled **illicit** and 42,019 (20.6%) **licit**. The remaining 157,205 (77.1%) are unknown. Among labelled transactions, 9.8% are illicit, so accuracy says little about a model: always answering \"licit\" would be 90% accurate. Unknown transactions stay in the graph so that information can flow through them, but they are never used for training or scoring. Illicit transactions are also less connected than licit ones, with an average of 2.01 connections against 3.10.")
sub("2.3 Temporal split")
para("Following Weber et al., every model trains on time steps 1–34 (29,894 labelled, 11.6% illicit) and is tested on 35–49 (16,670 labelled, 6.5% illicit). Splitting by time rather than at random means models are always tested on the future, as they would be in practice. Figure 1 shows why the test period is hard. Illicit activity arrives in bursts, and after the dark-market shutdown at step 43 it almost disappears before slowly returning.")
figure("fig1_illicit_over_time", "Illicit transactions per time step (left) and as a share of labelled transactions (right). The dashed line marks the start of the test period; the dotted line marks the dark-market shutdown at step 43.")

heading("Methodology")
sub("3.1 Shared evaluation protocol")
para("*Role 4 – Giulio D'Aversa.* A single evaluation program scores every model. Each model exports an illicit-class score for exactly the 16,670 labelled test transactions, and the program rejects missing, extra or duplicated transactions. It reports, for the illicit class, **precision** (the share of alerts that are truly illicit), **recall** (the share of illicit transactions found), their combination **F1**, and **average precision (AP)**. AP summarises the whole precision–recall curve without needing a threshold. Confusion counts and every metric are also reported per time step. Each run records a fingerprint of the test set, and the comparison tool refuses to combine runs scored on different transactions. All 30 runs in this report share one fingerprint.")
para("Thresholds were always fixed **before** looking at test labels: 0.50 for the Random Forests, and for the neural networks the value that maximised F1 on the validation steps. Because thresholds differ between models, **AP is the headline comparison**. Every model was trained with seeds 0–4, and we report the mean and standard deviation.")
sub("3.2 Baseline models")
para("*Role 2 – Jessica Zainea Pop.* Logistic regression, Random Forest and XGBoost were compared on the 165 features. Model selection trained on steps 1–29 and validated on 30–34. The **Random Forest** won clearly on validation (F1 0.96, AP 0.99). It was then retrained on all of 1–34 with 100 trees, depth 12 and class weights that balance licit and illicit examples. A simple graph feature, the number of same-period connections (degree), did not help, because the aggregated features already describe the neighbourhood.")
sub("3.3 Graph neural networks")
para("*Role 3 – Gioia Cancian.* All neural models share one design: two hidden layers of 64 units, ReLU activations, dropout of 0.3 and a linear output layer. Only the layer type changes, so differences come from how each model uses the graph:")
bullets(["**MLP:** ignores the edges entirely. It is the control model, measuring what the graph adds.",
         "**GCN** (Kipf & Welling, 2017): averages each transaction's features with those of its neighbours.",
         "**GraphSAGE** (Hamilton et al., 2017): keeps a transaction's own signal separate from the average of its neighbours.",
         "**GAT** (Veličković et al., 2018): learns how much attention to pay to each neighbour."])
para("Each time period is a separate subgraph, so models never see test transactions during training. Features are standardised with training statistics only. Training uses a loss weighted about eight to one in favour of the illicit class, and early stopping on validation AP (steps 30–34). A second Random Forest (100 trees, 50 features per split, as in Weber et al.) was trained on steps 1–34, with and without the GCN's learned representations added as features. The neural networks were re-run on a GPU of the **Bocconi HPC cluster**, where all 25 runs took about three minutes.")

heading("Results")
sub("4.1 Model comparison")
table("Test results (time steps 35–49), mean over 5 seeds (± one standard deviation). Alerts, false alarms (FP) and missed illicit transactions (FN) are mean counts per run, out of 1,083 illicit and 15,587 licit test transactions. The last two columns give F1 before and after the shutdown. R2 and R3 denote the Random Forests of Roles 2 and 3.",
      ["Model", "AP", "F1", "Prec.", "Recall", "Alerts", "FP", "FN", "F1 35–42", "F1 43–49"],
      main_rows, [3.0, 2.3, 2.3, 1.3, 1.3, 1.2, 0.9, 0.9, 1.3, 1.3])
para("**The Random Forests are the strongest models.** Both reach an AP of about 0.79, far above every neural network (Table 1, Figure 2), with almost no variation between seeds. This agrees with Weber et al., whose Random Forest reached an F1 of 0.788 (ours: 0.817 and 0.752) and whose GCN reached 0.628 (ours: 0.547).")
figure("fig2_model_comparison", "Average precision (left) and illicit F1 (right), mean ± standard deviation over 5 seeds.")
para("**The two Random Forests rank transactions equally well but raise different numbers of alerts.** Their AP is almost the same (0.788 and 0.783) and they catch about the same number of illicit transactions. At the shared 0.50 threshold, however, the Role 2 model raises 230 false alarms per run and the Role 3 model only 50, because the Role 2 model's class weighting pushes its scores upwards. In other words, the models are calibrated differently.")
para("**Among the neural networks, the graph helps.** Every GNN beats the identical MLP on AP: GCN by 0.20, GraphSAGE by 0.14 and GAT by 0.12. GCN gives the most precise alerts, GraphSAGE has the highest recall among the GNNs, and GAT is the least stable across seeds. Adding the GCN's learned representations to the Random Forest made it **worse** (F1 0.760 against 0.817). These representations were fitted on the same training labels, so they look more reliable on training data than they are on new data.")
sub("4.2 Performance over time")
para("Every model **collapses at time step 43** (Figure 3). Before the shutdown, F1 ranges from 0.55 to 0.91; from step 43 onwards it is between 0.01 and 0.03, with one partial recovery at step 46. The overall scores in Table 1 therefore average a period in which the models work with one in which none of them does.")
figure("fig3_f1_per_time_step", "Illicit F1 per test time step, mean over 5 seeds.")
sub("4.3 Ranking quality and investigators' capacity")
para("An investigation team cannot review every alert, so what matters is how many of the highest-risk alerts are correct. By this measure the gap between the models is even larger (Figure 4, Table 2). **The 500 highest-scored transactions of either Random Forest were all illicit**, in every seed. For the best GNN, 76% of its top 500 were illicit, and for the MLP only 37%.")
figure("fig4_pr_curves", "Precision–recall curves (seed 0). The dotted line is the 6.5% share of illicit transactions in the test set, the precision of random guessing.")
table("Share of truly illicit transactions among each model's k highest-scored test transactions (mean of 5 seeds), i.e. the hit rate for a team able to review k cases.",
      ["Model", "k = 100", "k = 250", "k = 500", "k = 1,000"], topk_rows, [4.4, 2.2, 2.2, 2.2, 2.2])

heading("Explainability")
para("*Role 4. The features are anonymised, so explanations refer to feature numbers rather than economic quantities.*")
sub("5.1 What drives the Random Forest")
para("We used **SHAP** (Lundberg & Lee, 2017), which splits each prediction into contributions from individual features. It was applied to all 1,083 illicit test transactions and an equal random sample of licit ones. **Local features carry 75% of the total importance**, although they are only 93 of the 165 features (Figure 5). The model relies mainly on the characteristics of the transaction itself.")
figure("fig5_shap_importance", "Random Forest (Role 2, seed 0): the 15 most important features by mean absolute SHAP value.", width=11)
sub("5.2 Why every model fails after the shutdown")
para("Before the shutdown, illicit transactions receive a mean score of 0.81 and 86% of them are flagged. After it, the mean score is 0.10 and only 1.8% are flagged. Figure 6 shows the mechanism. **Each of the eight most important features pushes illicit transactions towards \"illicit\" before the shutdown and towards \"licit\" after it.** This is *concept drift*: the illicit activity that continues after the market closed has a different profile from the activity the model learned from, so the model scores it as licit. A model trained only on earlier periods cannot correct this by itself; it needs newly labelled cases, or monitoring that detects the change.")
figure("fig6_shap_drift", "Mean SHAP contribution of the eight most important features for illicit test transactions, before (blue) and after (orange) the shutdown. Positive values push towards \"illicit\".", width=11)
sub("5.3 How the graph neural networks use the graph")
para("We scored the test graph twice with the same trained networks, the second time with **every edge removed** (Figure 7). Removing the edges did not reduce performance: GCN's AP went from 0.477 to 0.509 and GraphSAGE's from 0.506 to 0.564, improving for every GraphSAGE seed. **GNNExplainer** (Ying et al., 2019) gives a similar picture. For the five most confidently flagged illicit transactions, it keeps at most 8 edges, out of up to 1,190 in each neighbourhood.")
figure("fig7_graph_ablation", "Test AP of the same trained model with and without the edges of the test graph. Thin lines are individual seeds; the black line is the mean.", width=9)
para("Our interpretation is that the graph helps mainly **during training**, where averaging over neighbours appears to act as a regulariser. At prediction time, the trained network relies on each transaction's own features, which already contain 72 neighbourhood summaries. That would also account for the strength of the tree models, which use the same summaries. Weber et al. observed something similar: only architectures that add structure beyond a plain GCN came close to their Random Forest. (These networks were trained on CPU and score slightly below the HPC runs; the comparison within each model is what matters.)")

heading("Implications for anti-money laundering")
bullets(["**The best models rank well but still miss many cases.** A team reviewing 500 cases would find only true positives with either Random Forest. Even so, the best model misses about 300 of the 1,083 illicit test transactions, more than half of them after the shutdown.",
         "**Alert volume depends on calibration.** Two models with the same AP produced 833 and 1,020 alerts at the same threshold. Thresholds should be set from investigators' capacity on recent data and reviewed as behaviour changes.",
         "**Changing criminal behaviour is the main operational risk.** One market closure made every model useless for the rest of the period, and nothing in the scores warned of it. A deployed system needs monitoring of score distributions and hit rates, and regular retraining on newly confirmed cases.",
         "**Plain GNNs did not justify their extra cost here.** When neighbourhood summaries are already among the features, they are slower to train and tune than trees and performed worse. They are more promising on raw transaction data or with architectures that model time.",
         "**A label is not proof of laundering.** In Elliptic, \"illicit\" means a link to known illicit categories such as scams, malware, ransomware, Ponzi schemes and terrorist organisations. Most transactions are unlabelled, and a high score is a reason to investigate rather than a finding."])
para("[TODO optional: link these points to real AML practice, e.g. suspicious activity reporting and the risk-based approach, with one or two sources.]")

heading("Limitations and future work")
para("**Limitations.** The results come from one public dataset with anonymised features. Only 23% of transactions are labelled, and just 169 illicit test transactions fall after the shutdown. The Random Forests trained on steps 1–34 but the neural networks on 1–29, and little tuning was done. Message passing and the degree feature assume each period's graph is complete at prediction time, a batch rather than real-time setting. The GNNExplainer analysis covers one seed and five transactions.")
para("**Future work**, in order of expected value: retrain the GNNs on all of 1–34; train them on local features only, where the graph should matter more; test temporal GNNs such as EvolveGCN (Pareja et al., 2020); use representations computed on held-out data for the Random Forest; and simulate retraining after every time step to measure how quickly models recover from drift.")

p = _para(before=360, after=180); _run(p, "CONCLUSIONS", bold=True)
para("On the Elliptic dataset, learning on the transaction graph helps neural networks but does not beat a Random Forest on the transaction features, which already summarise each transaction's neighbourhood. For a real anti-money-laundering system, the larger risk lies outside the model architecture: every model failed when criminal behaviour changed after a dark-market shutdown, and SHAP explanations made that change visible. Monitoring, regular retraining and alert thresholds set from investigators' capacity address that risk directly.")

p = _para(before=360, after=180); _run(p, "TEAM CONTRIBUTIONS", bold=True)
bullets(["**Loukas Iatrou** (project leader): objectives, roles, repository and workflow; integration of the four roles, HPC experiments and report preparation.",
         "**Ahaan Dhawan** (Role 1): data preparation, exploratory analysis, temporal split and data card.",
         "**Jessica Zainea Pop** (Role 2): classical baselines (logistic regression, Random Forest, XGBoost) and graph features.",
         "**Gioia Cancian** (Role 3): graph neural networks (GCN, GraphSAGE, GAT), training protocol and the embedding experiment.",
         "**Giulio D'Aversa** (Role 4): shared evaluation program and tests, explainability, AML context and the write-up."])

p = _para(before=360, after=180); _run(p, "DATA SOURCES", bold=True)
sub("Data and code")
source("Elliptic Co. (2019). *The Elliptic Data Set*. Kaggle. kaggle.com/datasets/ellipticco/elliptic-data-set")
source("Project repository (code, shared split, result tables and figures): github.com/LoukasIatrou/ML-project")
sub("Written Sources")
source("Altman, E. et al. (2023). Realistic Synthetic Financial Transactions for Anti-Money Laundering Models. *NeurIPS Datasets and Benchmarks Track*.")
source("Hamilton, W. L., Ying, R., & Leskovec, J. (2017). Inductive Representation Learning on Large Graphs. *NeurIPS*.")
source("Kipf, T. N., & Welling, M. (2017). Semi-Supervised Classification with Graph Convolutional Networks. *ICLR*.")
source("Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions. *NeurIPS*.")
source("Pareja, A. et al. (2020). EvolveGCN: Evolving Graph Convolutional Networks for Dynamic Graphs. *AAAI*.")
source("UNODC. Money Laundering. *Education for Justice, Organized Crime Module 4*. unodc.org/e4j/en/organized-crime/module-4/key-issues/money-laundering.html")
source("Veličković, P., Cucurull, G., Casanova, A., Romero, A., Liò, P., & Bengio, Y. (2018). Graph Attention Networks. *ICLR*.")
source("Weber, M., Domeniconi, G., Chen, J., Weidele, D. K. I., Bellei, C., Robinson, T., & Leiserson, C. E. (2019). Anti-Money Laundering in Bitcoin: Experimenting with Graph Convolutional Networks for Financial Forensics. *KDD Workshop on Anomaly Detection in Finance*. arXiv:1908.02591")
source("Ying, R., Bourgeois, D., You, J., Zitnik, M., & Leskovec, J. (2019). GNNExplainer: Generating Explanations for Graph Neural Networks. *NeurIPS*.")

out = REPORT / "Graph_ML_Money_Laundering_Report.docx"
doc.save(out)
print("saved", out.relative_to(ROOT), f"({FIGURES} figures, {TABLES} tables)")
