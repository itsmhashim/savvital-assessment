# AI Systems & Automation Strategist — Technical Assessment

## Repository Structure

| Folder / File | Description |
|---|---|
| [`Task 1/`](<Task 1/>) | n8n workflow, sample output, evidence log |
| [`Task 2/`](<Task 2/>) | Dashboard script, HTML export, dataset |

---

# Task 1 — AI-Powered Intake Triage (n8n Workflow)

## Overview

This automation manages the intake triage for an estate planning firm. It ingests client profiles from Google Sheets, uses a Google Gemini LLM to analyze the data, and returns structured legal instrument recommendations with urgency flags.

## How to Run

1. Open your n8n instance and go to **Workflows → Import from File**
2. Import [`intake_triage.json`](<Task 1/intake_triage.json>)
3. Add your **Google Gemini API key** under the **Google Gemini Chat Model** sub-node (not the AI Agent node itself) — get this from [Google AI Studio](https://aistudio.google.com/app/apikey)
4. Add your **Google Sheets API credentials** (OAuth2 or Service Account) under the Google Sheets trigger node — set these up via the [Google Cloud Console](https://console.cloud.google.com/)
5. Click **Execute Workflow** — results appear in the AI Agent node output
6. See the [Video Walkthrough](#video-walkthrough) below for a full demonstration

## Technical Design Choices

### Model Choice: Google Gemini

I chose **Google Gemini** (via n8n's LangChain nodes) for its high reasoning capabilities and speed. In an automation context, Gemini handles structured JSON output exceptionally well, ensuring that the final data is ready for downstream database insertion without formatting errors. Gemini also offers a generous free API tier, making it immediately practical for prototyping and production-grade automations without upfront cost.

### Prompt Design Strategy

The prompt utilizes **Role-Based Instruction** and **Negative Constraints**:

- **Persona:** Defined the model as an "expert estate planning advisor."
- **Vocabulary Control:** Provided a strict list of 10 available legal instruments to prevent the AI from "inventing" document types.
- **Urgency Logic:** Hardcoded business rules into the prompt (e.g., age 65+ or business owners = High Urgency) to ensure the triage remains objective and consistent.

### Two-Trigger System

To ensure 100% reliability, the workflow uses two triggers:

1. **Google Sheets Trigger:** Provides near-instant processing whenever a new row is added.
2. **Schedule Trigger:** Acts as a fail-safe poll (e.g., every hour) to capture any records missed due to API sync issues or bulk uploads that might bypass the standard trigger.

### Data Validation (JavaScript Node)

I included a JavaScript node to handle "dirty data." It converts empty strings from Google Sheets into proper boolean `false` values and ensures the `age` field is an integer. This pre-processing prevents LLM logic errors.

## Production & Human-in-the-Loop

### Production Changes

- **RAG (Retrieval-Augmented Generation):** For a real firm, I would connect a Vector Store containing state-specific legal codes to ensure the advice is legally compliant with local jurisdictions.
- **Database Persistence:** Instead of just outputting JSON, I would connect a PostgreSQL node to create a permanent audit trail of all triaged leads.

### Human Review & Communication (WhatsApp Integration)

To ensure safety and professional oversight, I'd have designed a **Pre-Approval step** using a communication sub-node:

- **WhatsApp Integration:** A WhatsApp sub-node is added to the AI Agent node.
- **Workflow:** The AI's recommendation and rationale are sent to a lawyer's mobile device via WhatsApp. The lawyer must reply with "Approved" or provide edits. The automation "waits" for this response before finalizing the record. This ensures a human expert always validates the AI's output before it reaches the client or the CRM.

## Video Walkthrough

[![Workflow Walkthrough — click to watch](https://cdn.loom.com/sessions/thumbnails/03b0d98aac28420b89bc0d55aef3f5b1-with-play.gif)](https://www.loom.com/share/03b0d98aac28420b89bc0d55aef3f5b1)

## Task 1 Files

| File | Description |
|---|---|
| [`intake_triage.json`](<Task 1/intake_triage.json>) | Exported n8n workflow — import directly into n8n |
| [`sample_output.json`](<Task 1/sample_output.json>) | Structured LLM output for all 4 client profiles |
| [`evidence_log.pdf`](<Task 1/evidence_log.pdf>) | Input data → prompt → raw LLM response → parsed output per client |

---

# Task 2 — Operations KPI Dashboard

## Overview

A self-contained interactive dashboard built with **Python + Plotly** using the [CRM Sales Opportunities](https://www.kaggle.com/datasets/innocentmfa/crm-sales-opportunities) dataset. The dashboard visualises five operational metrics across a B2B sales pipeline covering October 2016 to March 2017.

## How to Run

```bash
# Install dependencies
conda install plotly pandas
conda install -c plotly kaleido   # optional — for PDF export

# Generate dashboard
cd "Task 2"
python dashboard.py

# Output: dashboard.html (open in any browser) + dashboard.pdf
```

## Metrics & Design Choices

The five metrics were selected to tell a complete operational story — from pipeline health to financial impact to regional performance.

| # | Metric | Chart Type | Why |
|---|---|---|---|
| 1 | Volume by Pipeline Stage | Bar | Shows overall pipeline distribution and where deals accumulate |
| 2 | Monthly Win Rate (%) | Area line | Tracks conversion efficiency over time with average reference line |
| 3 | Won Deals by Sales Region | Donut | Shows proportional contribution of each territory to closed revenue |
| 4 | Monthly Revenue — Won Deals | Area line | Financial pulse — separates volume growth from revenue growth |
| 5 | Avg Days to Close by Product | Horizontal bar | Identifies which products have longer sales cycles — a capacity signal |

**Data story:**

**Metric 1 — Pipeline Volume:** The stage distribution is inverted compared to a live funnel — Won deals outnumber Prospecting deals. This is expected because the dataset is a completed historical snapshot (Oct 2016 – Mar 2017): most opportunities have already resolved. In a live pipeline the Prospecting bar would dominate. This chart is most useful as a retrospective breakdown of how the cycle ended.

**Metric 2 — Monthly Win Rate:** Win rate remains relatively stable month-to-month, hovering around the average reference line. The consistency suggests the sales team applied a reliable qualification process throughout the cycle rather than experiencing significant dips from bad batches of leads.

**Metric 3 — Won Deals by Region:** The donut shows how closed revenue is distributed across the three sales territories (Central, East, West). No single region has a monopoly — each contributes a meaningful share, indicating a geographically balanced team. This can guide headcount and quota decisions per region.

**Metric 4 — Monthly Revenue:** Revenue peaks in the later months of the cycle (February–March 2017) as deals that were engaged in October–November 2016 reach their close dates. The ramp-up shape is typical of a pipeline that was seeded at a similar time — useful for forecasting close timing on a new cohort.

**Metric 5 — Avg Days to Close:** There is a clear and direct relationship between product price and sales cycle length. GTK 500 (priced at $26,768) takes significantly longer to close than any other product — high-value deals require more stakeholders, negotiation rounds, and procurement steps. At the other end, MG Special ($55) closes fastest. This correlation means the product mix in a pipeline directly predicts how long it will take to realise revenue.

**Dataset limitation:** The dataset records only `engage_date` (when active selling began) — there is no Prospecting start date. Deal velocity in Metric 5 is therefore measured from first contact to close, not from initial lead identification, meaning true pipeline age would be longer. The dataset also covers a single sales cycle (late 2016 to early 2017), so monthly trend charts reflect a narrow window rather than multi-year seasonality patterns.

## Screenshots

![Metric 2 — Monthly Win Rate](<Task 2/screenshots/01_monthly_winrate.png>)

![Metric 3 — Won Deals by Sales Region](<Task 2/screenshots/02_regional_revenue.png>)

![Metric 5 — Avg Days to Close by Product](<Task 2/screenshots/03_avg_days.png>)

## Task 2 Files

| File | Description |
|---|---|
| [`dashboard.py`](<Task 2/dashboard.py>) | Python script — run to regenerate HTML and PDF |
| [`dashboard.html`](<Task 2/dashboard.html>) | Self-contained interactive dashboard (open in browser) |
| [`dataset/`](<Task 2/dataset/>) | CRM Sales Opportunities dataset (Kaggle) |
