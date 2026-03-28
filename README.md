# Trump Oil Market Manipulation Forensics

### See our interactive app: https://market-manipulation.streamlit.app

### Checkout our slide deck: https://docs.google.com/presentation/d/14i7_N7HxKQb0LUROpODcAIZuqEXpwV9vBxTNoyTFmZo

## Introduction

On March 23, 2026, Donald Trump posted on Truth Social claiming "productive conversations" with Iran were underway during the Iran crisis. Oil prices dropped over 13% as markets anticipated de-escalation. Hours later, Iran's Foreign Ministry explicitly denied any talks had taken place, accusing Trump of using "fake news to manipulate the financial and oil markets."

This project investigates whether Trump's Truth Social posts systematically manipulate oil prices. Rather than searching for broad correlations, we build a **forensic case** — analyzing specific posts, proving temporal causation, documenting fabricated claims, and quantifying manipulation through a composite scoring system.

Our central thesis: Trump uses an **oscillation strategy** — posting escalation threats to spike oil prices, then posting de-escalation claims (often fabricated) to crash them, generating volatility that benefits informed traders.

## Research Questions

1. **Oscillation Pattern**: Do oil prices show abnormal pump-and-dump reversal patterns following sequences of Trump posts with alternating directions (escalation → de-escalation)?
2. **Fabrication Detection**: Are there documented cases where Trump made provably false claims that moved oil markets, with official denials from counterparties?
3. **Temporal Causality**: Do Trump's posts precede price movements (proving intent) or follow them (suggesting reactive behavior)?
4. **AI-Detected Intent**: What does nuanced AI analysis (Google Gemini) reveal about the manipulation intent of specific posts, beyond crude keyword matching?
5. **Beneficiary Analysis**: Who profits from these price movements? Does DJT stock move abnormally on oil-post days, and do insiders sell before market-moving announcements?

## Data Sources

| Source | Data | Method | Rows |
|--------|------|--------|------|
| [trumpstruth.org](https://trumpstruth.org) | Trump Truth Social posts | Web scraping (BeautifulSoup) | ~5,000+ posts |
| [FRED](https://fred.stlouisfed.org) | Brent & WTI crude oil daily prices | CSV download (requests) | ~310 trading days |
| [Yahoo Finance](https://finance.yahoo.com) | DJT stock price & USO ETF intraday | yfinance library | ~310 trading days |
| [Google Gemini](https://aistudio.google.com) | AI post classification | API (google-genai) | Per oil-related post |
| [EODHD](https://eodhd.com) | Intraday crude oil prices | REST API | Key dates only |

The master dataset contains **450+ rows** (one per calendar day, Jan 2025 – Mar 2026) with **15+ features** of mixed numeric and categorical types.

## Methodology: Five Detection Vectors

We score each trading day on five independent dimensions (0-100), combined into a weighted **Composite Manipulation Score**.

### Vector 1: Oscillation Pattern Detection (20%)
Identifies pump-and-dump cycles where post direction reverses within 48 hours. An escalation post followed by a de-escalation post (or vice versa) with a >2% price swing scores highest. This captures the systematic volatility-creation pattern.

### Vector 2: Fabrication Detection (25%)
Documents cases where Trump's claims were explicitly denied by official sources. The March 23 "productive conversations" claim — denied by Iran's Foreign Ministry as market manipulation — is the strongest single piece of evidence. Each fabrication is scored by the magnitude of price movement before the denial.

### Vector 3: Intraday Causality (25%)
The most critical vector. Using intraday price data (USO ETF 5-minute bars, EODHD crude futures), we measure the time gap between post timestamps and first significant price movements. A post that precedes a price move by minutes provides strong evidence of causation; a post that follows a move suggests reactive behavior.

### Vector 4: Intent Classification via Gemini (15%)
Google's Gemini AI classifies each oil-related post across five dimensions: direction intent, verifiability, fabrication risk, oscillation risk, and market impact intent. This overcomes the limitations of keyword matching — Gemini can distinguish between a post about "Iran's economy" and a post threatening to "bomb Iran," which carry very different market implications.

### Vector 5: Beneficiary Analysis (15%)
Examines whether Trump and associates benefit from post-induced price movements by tracking DJT (Trump Media) stock behavior on oil-post days versus baseline, and documenting known insider sales (e.g., Bondi and Scavino selling DJT shares before Liberation Day tariff announcements).

### Composite Score Formula

```
MANIPULATION_SCORE = (
    Oscillation × 0.20 +
    Fabrication × 0.25 +
    Causality   × 0.25 +
    Intent      × 0.15 +
    Beneficiary × 0.15
)

Verdict: >70 = HIGH | 50-70 = ELEVATED | <50 = LOW
```

## Key Findings

### The Smoking Gun: March 23, 2026
Trump claimed "productive conversations" with Iran → oil dropped 13%+ → Iran denied any talks and explicitly accused Trump of market manipulation. This single event scores near-maximum on fabrication, causality, and intent vectors.

### The $38 Day: March 9, 2026
Trump oscillated between "war is very complete" and threatening to "hit Iran twenty times harder" within hours of each other. Oil swung $38 in a single day — the largest intraday range in crude oil history. This scores maximum on the oscillation vector.

### Systematic Volatility Creation
Oil-post days show significantly higher price volatility compared to non-post days. The oscillation pattern — escalation → spike → de-escalation → crash → repeat — is consistent across the Iran crisis period and suggests deliberate volatility creation rather than reactive commentary.

### Directional Accuracy
Escalation posts tend to precede price increases; de-escalation posts tend to precede price decreases. The directional accuracy exceeds what random posting would produce, suggesting awareness of how posts will move markets.

## Visualizations

The project includes 8+ publication-quality figures:
- **Hero chart**: Full-period oil price with post markers and manipulation score
- **March crisis annotated timeline**: Post-by-post annotations showing the oscillation pattern
- **Volatility comparison**: Box plots and histograms comparing post-day vs. non-post-day returns
- **Fabrication timeline**: Annotated chart showing false claims and their price impacts
- **Score decomposition**: Stacked bar chart breaking down the five vectors for top suspicious days
- **Correlation heatmap**: Feature correlations across all 15+ variables
- **DJT vs. oil scatter**: Relationship between Trump Media stock and crude oil movements
- **Manipulation score time series**: Rolling average with threshold markers

## Interactive Dashboard

An interactive Streamlit dashboard (`app.py`) allows exploration of the data:
- Filter by date range and minimum manipulation score
- Explore individual dates with full score breakdowns
- View AI classification reasoning for each post
- Examine fabrication evidence and the oscillation pattern

Run with: `streamlit run app.py`

## How to Reproduce

```bash
# Clone the repository
git clone <repo-url>
cd SternSecondAttempt

# Install dependencies
pip install -r requirements.txt

# Set API keys (optional but recommended)
# Edit notebooks/04_gemini_classification.ipynb and set GEMINI_API_KEY
# Edit notebooks/01_data_collection.ipynb and set EODHD_API_KEY

# Run notebooks in order
# Execute notebooks/01_data_collection.ipynb through notebooks/07_visualizations.ipynb

# Launch dashboard
streamlit run app.py
```

**Note**: Notebooks 04 (Gemini) and the EODHD section of 01 require API keys. Both have free tiers. The project works without them using keyword-based fallback classifiers and daily-only price data.

## Limitations

- **Correlation vs. causation**: While intraday timing strengthens the causal argument, we cannot definitively prove Trump's intent without insider information or communications.
- **Keyword classification fallback**: Without Gemini API access, the keyword-based classifier is less nuanced and may misclassify ambiguous posts.
- **Intraday data coverage**: USO ETF is a proxy for crude oil, not the exact Brent/WTI futures contract. Tracking error exists.
- **Fabrication evidence**: Our fabrication database is manually curated for the most prominent cases. Additional false claims may exist that we did not document.
- **Political framing**: This analysis focuses on market impact of specific false claims, not broader political judgments. The methodology would apply equally to any public figure making market-moving statements.

## Project Structure

```
SternSecondAttempt/
├── README.md
├── requirements.txt
├── app.py                              # Streamlit dashboard
├── data/
│   ├── raw/                            # Downloaded/scraped data
│   └── processed/                      # Cleaned, scored datasets + figures
├── notebooks/
│   ├── 01_data_collection.ipynb        # Scraping & API downloads
│   ├── 02_cleaning_merging.ipynb       # Master dataset creation
│   ├── 03_price_patterns.ipynb         # Oscillation detection
│   ├── 04_gemini_classification.ipynb  # AI post classification
│   ├── 05_fabrication_causality.ipynb  # False claims & timing proof
│   ├── 06_composite_score.ipynb        # Final manipulation scores
│   └── 07_visualizations.ipynb         # Publication figures
└── evidence/
    └── iran_denial_march23.md          # Documented fabrication evidence
```

## Ethical Considerations

Market manipulation is a serious allegation. Our analysis identifies statistical patterns consistent with manipulation but cannot prove intent without access to private communications or trading records. The composite score should be interpreted as a measure of suspicion, not a legal determination. We note that the SEC has historically used similar temporal and pattern-based analysis in enforcement actions, though typically supplemented with trading records and communications evidence that we do not have access to.

## References

- FRED Economic Data: https://fred.stlouisfed.org
- Trump's Truth Archive: https://trumpstruth.org
- Google Gemini API: https://aistudio.google.com
- EODHD Financial API: https://eodhd.com
- SEC Market Manipulation Enforcement: https://www.sec.gov/enforce/market-manipulation
- Academic basis: Kamps & Kleinberg, "To the Moon: Defining and Detecting Cryptocurrency Pump-and-Dumps" (adapted for commodity markets)
